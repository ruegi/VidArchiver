# -*- coding: utf-8 -*-
'''
Created on 2018-06-01
@author: rg
Vidarchiver.py mit pyqt5
ermöglicht es, die Videos in den Prep-Verzeichnissen _in1..._in10
in die passenden VideoArchivOrdner einzusortieren
'''

# import PyQt5.QtWidgets # Import the PyQt5 module we'll need
from PyQt5.QtWidgets import (QMainWindow, 
                             QLabel,
                             QTableWidgetItem,
                             QAbstractItemView,
                             QHeaderView,
                             QLineEdit, 
                             QPushButton,
                             QWidget,
                             QHBoxLayout, 
                             QVBoxLayout, 
                             QApplication,
                             QMessageBox,
                             QFileSystemModel)

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QThread, Qt, QDir, QModelIndex
from PyQt5.QtGui import QIcon

from math import log as logarit
from datetime import datetime
import sys
import os
import time

# das fenster wurde mit dem qtdesigner entworfen und per pyuic5 konvertiert
import VidArchiverUI

stopFlag = False

# --------------------------------------------------------------------------------
# ??? class
# --------------------------------------------------------------------------------
# --------------------------------------------------------------------------------
# VidArchiverApp class
# --------------------------------------------------------------------------------
class VidArchiverApp(QMainWindow, VidArchiverUI.Ui_MainWindow):
    # suchAnfrage = pyqtSignal(str, str, str)

    def __init__(self, app):
        super(self.__class__, self).__init__()
        
        self.setupUi(self)  # This is defined in VidArchiverUI.py file automatically
                            # It sets up layout and widgets that are defined
        # Instanz-Variablen
        self.vpath   = "Y:\\video"
        self.app = app
        self.worker = None

        # Icon versorgen
        scriptDir = os.path.dirname(os.path.realpath(__file__))
        self.setWindowIcon(QIcon(scriptDir + os.path.sep + 'VidArchiver.ico'))

        self.le_vidArchPfad.setText("Y:\\video")
        # self.btn_playVideo.setEnabled(False)
        # self.btn_linkVideo.setEnabled(False)
        # self.btn_unlinkVideo.setEnabled(False)
        # self.le_vidArchPfad.textChanged.connect(self.suchBtnAktivieren)

        #self.lst_erg.setTextBackgroundColor(QColor("lightyellow"))
        self.tbl_film.setStyleSheet("background-color: lightyellow;")
        # self.tre_vidPfad.setHorizontalHeaderLabels(('Video', 'Länge', 'Datum'))
        self.tbl_film.setAlternatingRowColors(True)
        header = self.tbl_film.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tbl_film.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl_film.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.tbl_vorhFilm.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl_vorhFilm.setEditTriggers(QAbstractItemView.NoEditTriggers)
        header = self.tbl_vorhFilm.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)

        self.cb_quelle.addItems(self.prepPfadeLaden(self.le_vidArchPfad.text()))        
        if self.cb_quelle.count() > 0:
            self.filmliste = self.filmeLaden(self.le_vidArchPfad.text() + os.path.sep + str(self.cb_quelle.currentText()))
            self.tbl_film.setCurrentCell(0,0)
        else:
            self.filmliste = []

        self.lst_vidPfad.addItems(self.zielPfadeLaden(self.le_vidArchPfad.text()))
        self.lst_vidPfad.setCurrentRow(0)

        self.filme_aus_Archiv_laden(str(self.lst_vidPfad.currentItem().text()))

        self.statusMeldung("Ready")

        # connects
        self.tbl_film.cellActivated.connect(self.videoPrepStart)
        self.cb_quelle.currentIndexChanged.connect(self.quelleLaden)
        self.btn_playVideo.clicked.connect(lambda: self.videoStart(self.tbl_film.currentRow(), 0))
        self.lst_vidPfad.currentRowChanged.connect(lambda: self.filme_aus_Archiv_laden(str(self.lst_vidPfad.currentItem().text())))
        self.tbl_vorhFilm.cellDoubleClicked.connect(self.videoArchStart)
        self.tbl_vorhFilm.cellClicked.connect(self.videoArchInfo)

    @pyqtSlot(int)
    def quelleLaden(self, quellIndex):
        if self.cb_quelle.count() > 0:
            self.filmliste = self.filmeLaden(self.le_vidArchPfad.text() + os.path.sep + str(self.cb_quelle.currentText()))
        else:
            self.filmliste = []

    # def buttonflip(self, txt):
    #     self.btn_suchen.setText(txt)
    #
    # def suchBtnAktivieren(self):
    #     self.btn_suchen.setEnabled(self.le_such1.text().strip() > "")

    # emuliert den default-key
    # def keyPressEvent(self, event):
    #     if event.key() == Qt.Key_Return:
    #         w = self.focusWidget()
    #         if w == self.le_such1 or w == self.le_such2:
    #             self.suchen()
    #     return

  # @pyqtSlot(list)
    # def ergebnis_ausgeben(self, liste):
    #     self.refreshTable(liste)
    #     self.warten(False)
    #     self.statusMeldung("Suche beendet! Es wurden {} Filme gefunden.".format(len(liste)))
    #     self.buttonflip("&Suchen")

    def prepPfadeLaden(self, vdir):
        preppfad = []
        for root, dirs, files in os.walk(vdir):
            for dir in dirs:
                if dir.startswith("_in"):
                    preppfad.append(dir)    # Pfad merken
            break   # nur oberste Ebene zählt
        return preppfad

    def filmeLaden(self, prepdir):
        '''
        lädt die Filme aus dem gewählten prep-Pfad in die Tabelle self.tbl_film
        '''     
        filmliste = []   
        self.tbl_film.clearContents()
        self.tbl_film.setRowCount(0)
        nr = 0
        for root, dirs, files in os.walk(prepdir):
            for fil in files:                
                vid = prepdir + os.path.sep + fil
                vlen = format_size(os.stat(vid).st_size)
                vdat = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(os.stat(vid).st_ctime))
                self.tbl_film.insertRow(nr)
                self.tbl_film.setItem(nr, 0, QTableWidgetItem(str(fil)))
                self.tbl_film.setItem(nr, 1, QTableWidgetItem(str(vlen)))
                self.tbl_film.setItem(nr, 2, QTableWidgetItem(str(vdat)))
                filmliste.append(vid)
                nr += 1
            break   # nur oberste Ebene zählt
        if nr > 0:
            self.tbl_film.setCurrentCell(0,0)
        return filmliste

    @pyqtSlot()
    def filme_aus_Archiv_laden(self, adir):
        '''
        lädt die Filme aus dem gewählten Archiv-Pfad in die Tabelle self.tbl_vorhFilm
        '''
        self.tbl_vorhFilm.clearContents()
        self.tbl_vorhFilm.setRowCount(0)
        nr = 0
        for root, dirs, files in os.walk(adir):
            for fil in files:
                vid = adir + os.path.sep + fil
                vlen = format_size(os.stat(vid).st_size)
                vdat = time.strftime('%Y-%m-%d', time.localtime(os.stat(vid).st_ctime))
                self.tbl_vorhFilm.insertRow(nr)
                self.tbl_vorhFilm.setItem(nr, 0, QTableWidgetItem(str(fil)))
                self.tbl_vorhFilm.setItem(nr, 1, QTableWidgetItem(str(vlen)))
                self.tbl_vorhFilm.setItem(nr, 2, QTableWidgetItem(str(vdat)))
                nr += 1
            break   # nur oberste Ebene zählt
        if nr > 0:
            self.tbl_vorhFilm.setCurrentCell(0,0)
        return


    def zielPfadeLaden(self, vdir):
        '''
        lädt die verfügbaren Ordner im Archiv in eine Liste;
        übergeht dabei alle Ordner mit beginnendem "_" auf oberster Ebene
        Param:  vdir    Ordner des Archives
        '''
        zielpfad = []
        lv = len(vdir) + 1
        for root, dirs, files in os.walk(vdir,  topdown=True):
            for dir in dirs:
                tst = root + os.path.sep + dir 
                if tst[lv] == "_":
                    # skip all _in* and _raw and _done paths
                    pass
                else:
                    zielpfad.append(tst)    # Pfad merken        
        return sorted(zielpfad)

    @pyqtSlot(int, int)
    def videoArchInfo(self, row, col):
        vid = self.lst_vidPfad.currentItem().text() + os.path.sep + self.tbl_vorhFilm.item(row, col).text()
        self.statusMeldung(vid)

    @pyqtSlot(str)
    def statusMeldung(self, meldung):
        self.statusbar.showMessage(meldung)

    @pyqtSlot(int, int)
    def videoPrepStart(self, row, col):
        vid = self.vpath + os.path.sep + str(self.cb_quelle.currentText()) + os.path.sep + self.tbl_film.item(row, col).text()
        self.videoStart(vid)

    @pyqtSlot(int, int)
    def videoArchStart(self, row, col):
        vid = self.lst_vidPfad.currentItem().text() + os.path.sep + self.tbl_vorhFilm.item(row, col).text()
        self.videoStart(vid)

    # Funktionen
    def videoStart(self, video):
        '''
        startet ein Video
        :param video: das zu startende Video
        :return:
        '''
        try:
            os.startfile(video)
        except:
            self.statusMeldung("Fehler: Kann das Video [{}] nicht starten!".format(video))
            beepSound(self.app)
        return
#
#   Allg Funktionen
#

def format_size(flen: int):
        """Human friendly file size"""
        unit_list = list(zip(['bytes', 'kB', 'MB', 'GB', 'TB', 'PB'], [0, 3, 3, 3, 3, 3]))
        if flen > 1:
            exponent = min(int(logarit(flen, 1024)), len(unit_list) - 1)
            quotient = float(flen) / 1024 ** exponent
            unit, num_decimals = unit_list[exponent]
            s = '{:{width}.{prec}f} {}'.format(quotient, unit, width=8, prec=num_decimals )
            s = s.replace(".", ",")
            return s
        elif flen == 1:
            return '  1 byte'
        else: # flen == 0
            return ' 0 bytes'

def beepSound(app):
    app.beep()

if __name__ == '__main__':        
    app = QApplication(sys.argv)
    form = VidArchiverApp(app)
    form.show()
    app.exec_()

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
                             QDialog,
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

# die fenster wurden mit dem qtdesigner entworfen und per pyuic5 konvertiert
from VidArchiverUI import Ui_MainWindow
from VidArchiverRenDialogUI import Ui_Dialog as Ui_DialogRename
from VidArchiverPfaDialogUI import Ui_Dialog as Ui_DialogPfadNeu

stopFlag = False

# --------------------------------------------------------------------------------
# Rename Dialog Class
# --------------------------------------------------------------------------------
class renameDialog(QDialog, Ui_DialogRename):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)

# --------------------------------------------------------------------------------
# Pfad neu Dialog Class
# --------------------------------------------------------------------------------
class pfaDialog(QDialog, Ui_DialogPfadNeu):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)

# --------------------------------------------------------------------------------
# VidArchiverApp class
# --------------------------------------------------------------------------------
class VidArchiverApp(QMainWindow, Ui_MainWindow):
    def __init__(self, app):
        super(self.__class__, self).__init__()
        
        self.setupUi(self)  # This is defined in VidArchiverUI.py file automatically
                            # It sets up layout and widgets that are defined
        # Instanz-Variablen
        self.vpath   = "y:\\video"
        self.delBasket = "__del"
        self.app = app
        self.worker = None
        self.ArchivReload = True
        self.updateDialog = None
        self.pfadDialog = None

        # Icon versorgen
        scriptDir = os.path.dirname(os.path.realpath(__file__))
        self.setWindowIcon(QIcon(scriptDir + os.path.sep + 'VidArchiver.ico'))

        self.le_vidArchPfad.setText(self.vpath)

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
        #header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        #header.setSectionResizeMode(2, QHeaderView.ResizeToContents)

        self.cb_quelle.addItems(self.prepPfadeLaden(self.le_vidArchPfad.text()))        
        if self.cb_quelle.count() > 0:
            self.filmliste = self.filmeLaden(self.le_vidArchPfad.text() + os.path.sep + str(self.cb_quelle.currentText()))
            self.tbl_film.setCurrentCell(0,0)
        else:
            self.filmliste = []

        self.ladeVidArchPfade()

        self.statusMeldung("Ready")

        # connects
        # --------------------------------------------------------------------------------------------
        self.tbl_film.cellActivated.connect(self.videoPrepStart)
        self.cb_quelle.currentIndexChanged.connect(self.quelleLaden)
        self.btn_playVideo.clicked.connect(self.videoPrepStart)
        self.lst_vidPfad.currentRowChanged.connect(self.filme_aus_Archiv_laden)
        self.tbl_vorhFilm.itemSelectionChanged.connect(self.videoArchDetail)
        self.tbl_vorhFilm.cellActivated.connect(self.videoArchStart)
        self.tbl_vorhFilm.doubleClicked.connect(self.videoArchStart)
        self.btn_showArchVideo.clicked.connect(self.videoArchStart)
        self.btn_del.clicked.connect(self.videoArchDel)
        self.btn_rename.clicked.connect(lambda: self.videoArchRen(self.le_ArchivFilm.text()))
        self.btn_linkVideo.clicked.connect(self.sortVideoInArch)
        self.lst_vidPfad.doubleClicked.connect(self.sortVideoInArch)
        self.btn_pfadNeu.clicked.connect(self.neuerArchPfad)
        self.videoArchDetail()


    # Key-Press-Events auswerten
    def keyPressEvent(self, event):
        w = self.focusWidget()
        if event.key() == Qt.Key_F5:
            if w == self.lst_vidPfad or w == self.tbl_film:
                self.sortVideoInArch()
        elif event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
            if w == self.tbl_vorhFilm:
                self.videoArchStart()
            elif w == self.tbl_film:
                self.videoPrepStart()
            elif w == self.lst_vidPfad:
                self.sortVideoInArch()            
            elif w == self.le_vidArchPfad:
                self.prepPfadeLaden(w.text())
        return

    def getCurrentArchPath(self):
        if self.lst_vidPfad.currentRow() < 0:   # nix zu tun
            return None                        
        else:
            return(self.vpath + self.lst_vidPfad.currentItem().text())

    def getCurrentPrepPath(self):
        if self.cb_quelle.currentIndex() < 0:
            return(None)
        else:
            return(self.vpath + os.sep + self.cb_quelle.currentText())

    def getCurentArchFilm(self):
        row = self.tbl_vorhFilm.currentRow()
        if row < 0:
            # print("Aktuelle Zeile in ArchFilm ist {}".format(row))
            return (None)
        else:
            return(self.tbl_vorhFilm.item(row, 0).text())

    def getCurentPrepFilm(self):
        # vid = self.vpath + os.path.sep + str(self.cb_quelle.currentText()) + os.path.sep + self.tbl_film.item(row, col).text()
        # self.videoStart(vid)        
        row = self.tbl_film.currentRow()
        if row is None or row < 0:
            return None
        else:
            return(self.tbl_film.item(row, 0).text())

    @pyqtSlot(int)
    def quelleLaden(self, quellIndex):
        if self.cb_quelle.count() > 0:
            self.filmliste = self.filmeLaden(self.le_vidArchPfad.text() + os.path.sep + str(self.cb_quelle.currentText()))
        else:
            self.filmliste = []

    def prepPfadeLaden(self, vdir):
        preppfad = []
        for root, dirs, files in os.walk(vdir):
            for dir in dirs:
                if dir.startswith("_in"):
                    preppfad.append(dir)    # Pfad merken
            break   # nur oberste Ebene zählt
        return preppfad

    def ladeVidArchPfade(self, pos=None):
        self.lst_vidPfad.clear()
        lst = self.zielPfadeLaden(self.vpath)
        l = len(self.vpath)
        for pfd in lst:
            kurzpfd = pfd[l:]
            self.lst_vidPfad.addItem(kurzpfd)
        if pos is None:
            self.lst_vidPfad.setCurrentRow(0)
        else:
            try:
                i = lst.index(pos)
                self.lst_vidPfad.setCurrentRow(i)
                print(pos, i)
            except:
                self.lst_vidPfad.setCurrentRow(0)
                print(pos , "not found!")
        self.filme_aus_Archiv_laden()
        return

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
    def filme_aus_Archiv_laden(self, pos=None):
        '''
        lädt die Filme aus dem gewählten Archiv-Pfad in die Tabelle self.tbl_vorhFilm
        :parameter
        adir:   str     Archiv-Directory, dessen Inhalt gelistet werden soll
        pos=None  [None / str]  ggf. Name eines Videos, auf das positioniert werden soll
        '''

        self.ArchivReload = True
        self.tbl_vorhFilm.clearContents()
        self.tbl_vorhFilm.setRowCount(0)

        adir = self.getCurrentArchPath()
        if adir is None:
            return

        nr = 0

        for root, dirs, files in os.walk(adir):
            for fil in files:
                vid = adir + os.path.sep + fil
                self.tbl_vorhFilm.insertRow(nr)
                self.tbl_vorhFilm.setItem(nr, 0, QTableWidgetItem(str(fil)))
                nr += 1
            break   # nur oberste Ebene zählt
        self.ArchivReload = False
        if nr > 0:
            if pos is None:
                self.tbl_vorhFilm.setCurrentCell(0,0)
            else:   # versuchen zu positionieren
                lst = self.tbl_vorhFilm.findItems(pos, Qt.MatchExactly)
                if len(lst) > 0:
                    self.tbl_vorhFilm.setCurrentItem(lst[0])
                else:
                    self.tbl_vorhFilm.setCurrentCell(0, 0)
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
    def videoArchInfo(self):
        adir = self.getCurrentArchPath()
        film = self.getCurentArchFilm()        

        if adir is None or film is None:
            vid = ""
        else:
            vid = adir + os.path.sep + film
        self.statusMeldung(vid)

    @pyqtSlot(str)
    def statusMeldung(self, meldung):
        self.statusbar.showMessage(meldung)

    @pyqtSlot()
    def videoPrepStart(self):
        pdir = self.getCurrentPrepPath()
        film = self.getCurentPrepFilm()
        if pdir is None or film is None:
            return
        else:
            vid = pdir + os.sep + film
            self.videoStart(vid)

    @pyqtSlot()
    def videoArchStart(self):
        vpfad = self.getCurrentArchPath()
        film = self.getCurentArchFilm()
        if vpfad is None or film is None:
            return
        else:
            vid = vpfad + os.path.sep + film
            self.videoStart(vid)

    @pyqtSlot()
    def videoArchDetail(self):
        if self.ArchivReload or self.tbl_vorhFilm.rowCount() == 0:
            self.tbl_vorhFilm.clearContents()
            self.le_ArchivFilm.setText("")
            self.le_ArchivFilmGr.setText("")
            self.le_ArchivFilmDat.setText("")
            return
        else:
            adir = self.getCurrentArchPath()
            afilm = self.getCurentArchFilm()
            if adir is None or afilm is None:
                self.le_ArchivFilm.setText("")
                self.le_ArchivFilmGr.setText("")
                self.le_ArchivFilmDat.setText("")
            else:
                # print(self.lst_vidPfad.currentItem().text())
                # fil = self.tbl_vorhFilm.item(self.tbl_vorhFilm.currentRow(), 0).text()
                vid = adir + os.path.sep + afilm
                vlen = format_size(os.stat(vid).st_size)
                vdat = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.stat(vid).st_ctime))
                self.le_ArchivFilm.setText(afilm)
                self.le_ArchivFilmGr.setText(vlen)
                self.le_ArchivFilmDat.setText(vdat)
        self.le_ArchivFilm.setReadOnly(True)
        self.le_ArchivFilmGr.setReadOnly(True)
        self.le_ArchivFilmDat.setReadOnly(True)

    @pyqtSlot(str)
    def videoArchRen(self, fname):
        # startet einen Dialog zur Erfassung des neuen VideoNamens
        self.alterName = fname
        self.updateDialog = renameDialog()
        self.updateDialog.le_rename.setText(self.alterName)
        self.updateDialog.accepted.connect(lambda: self.renameDialogOK())
        self.updateDialog.rejected.connect(lambda: self.renameDialogCancel())
        self.updateDialog.le_rename.setFocus()
        self.updateDialog.exec_()
        return

    @pyqtSlot()
    def renameDialogOK(self):
        # pfad = self.lst_vidPfad.currentItem().text()
        pfad = self.getCurrentArchPath()
        neuerName = self.updateDialog.le_rename.text()
        neuerFullName = pfad + os.sep + neuerName
        alterFullName = pfad + os.sep + self.alterName
        try:
            os.rename(alterFullName, neuerFullName)
        except OSError as err:
            self.statusMeldung("Fehler! ({})".format(err.strerror))
        finally:
            self.statusbar.showMessage("Video umbenannt in: {}".format(neuerName))
            # print(neuerName)
            self.filme_aus_Archiv_laden(pos=neuerName)
        return

    @pyqtSlot()
    def renameDialogCancel(self):
        self.statusbar.showMessage("renameDialog Cancel: {}".format(self.updateDialog.le_rename.text()))


    @pyqtSlot()
    def videoArchDel(self):
        fname = self.getCurentArchFilm()
        if fname is None:
            return
        reply = QMessageBox.question(self, "Wirklich?",
                                    "Film [{0}] aus dem Archiv löschen?\n\nKeine Panik!\n".format(fname) +
                                     "Der Film wird nur in dem Mülleimer [{}] verschoben!".format(self.vpath + os.sep + self.delBasket),
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:            
            adir = self.getCurrentArchPath()
            delVideo = adir + os.sep + fname            
            delTarget = self.vpath + os.sep + self.delBasket + os.sep + fname
            try:
                os.rename(delVideo, delTarget)
            except OSError as err:
                self.statusMeldung("Fehler! ({})".format(err.strerror))
            finally:
                self.filme_aus_Archiv_laden(pos=None)
                self.statusMeldung("Der Film [{0}] wurde aus dem Archiv nach [{1}] verschoben!".format(fname, delTarget))
        else:
            self.statusMeldung("Löschen abgebrochen!".format(fname))
        return

    @pyqtSlot()
    def sortVideoInArch(self):
        '''
        nimmt den aktuellen Film aus dem prepOrdner und sortiert ihn in den aktuellen Pfad des Archivs
        :return: ---
        '''
        pos = None
        lstItems = self.tbl_film.selectedItems()
        if lstItems:
            # print(len(lstItems))
            pdir = self.getCurrentPrepPath()
            adir = self.getCurrentArchPath()
            pos = lstItems[0].text()
            i = 0
            moved = 0
            for itm in lstItems:
                i += 1
#                if (i % 3) == 1:    # nur Item 1, 4, 7 usw sind Dateinamen
                if itm.column() == 0:  # nur Dateinamen                    
                    qVideoName = itm.text()
                    qVideoFull = pdir + os.sep + qVideoName
                    zVideoTarget = adir
                    zVideoFull = zVideoTarget + os.sep + qVideoName
                    # print(i, ": ", qVideoFull, " --> ", end="")
                    # print(zVideoFull)
                    try:
                        os.rename(qVideoFull, zVideoFull)
                    except OSError as err:
                        QMessageBox.warning(self, "Achtung / Fehler",
                                            "Konnte die Datei [{}] nicht nach [{}] bewegen!".format(qVideoName, zVideoTarget) +
                                            "Fehlermedlung: {0}".format(err.strerror),
                                            QMessageBox.Ok)
                        # self.statusMeldung("Fehler! ({})".format(err.strerror))
                        break
                    finally:
                        time.sleep(0.2)
                        moved += 1
                        i += 1
                else:
                    continue

            self.quelleLaden(0)
            self.filme_aus_Archiv_laden(pos=pos)

        if moved == 1:
            self.statusMeldung("Es wurde ein Film in das Archiv nach [{0}] verschoben!".format(zVideoFull))
        else:
            self.statusMeldung("Es wurden {0} Filme in das Archiv nach [{1}] verschoben!".format(moved, zVideoTarget))
        return

    @pyqtSlot()
    def neuerArchPfad(self):
        '''
        erzeugt einen Dialog für einen neuen UnterOrdner zum aktuellen ArchPfad
        :return: ---
        '''
        aktPfad = self.getCurrentArchPath()
        if aktPfad is None:
            self.statusMeldung("Kein aktueller ArchivPfad -  nichts zu tun!")
            return
        self.alterName = aktPfad + os.sep
        self.pfadDialog = pfaDialog()
        self.pfadDialog.le_pfad.setText("")
        self.pfadDialog.groupBox.setTitle("UnterOrdner anlegen unter: {}".format(self.alterName))
        self.pfadDialog.accepted.connect(lambda: self.pfadDialogOK())
        self.pfadDialog.rejected.connect(lambda: self.pfadDialogCancel())
        self.pfadDialog.le_pfad.setFocus()
        self.pfadDialog.exec_()
        return

    @pyqtSlot()
    def pfadDialogOK(self):
        pfad = self.getCurrentArchPath()
        if pfad is None:
            self.statusMeldung("Kein aktueller ArchivPfad ?? -  nichts zu tun!")
            return
        neuerPfad = pfad + os.sep + self.pfadDialog.le_pfad.text()
        # print(pfad, " --> ", neuerPfad)
        try:
            os.makedirs(neuerPfad, exist_ok=True)
        except OSError as err:
            self.statusMeldung("Fehler! Kann den Ordner nicht anlegen! ({})".format(err.strerror))
            QMessageBox.alert(self, "Fehler",
                                    "Der Ordner [{}} konnte nicht angelegt werden\n\n".format(neuerPfad) +
                                     "FehlerMeldung: [{}]".format(err.strerror), QMessageBox.Close)
        finally:
            time.sleep(0.300)
            self.statusbar.showMessage("Neuen Pfad angelegt: {}".format(neuerPfad))
            self.ladeVidArchPfade(pos=neuerPfad)
        return

    @pyqtSlot()
    def pfadDialogCancel(self):
        self.statusbar.showMessage("Pfad-Dialog Cancel: {}".format(self.pfadDialog.le_pfad.text()))
        return

    # ----------------------------------------------------------------------------------------------------------------
    # Funktionen
    # ----------------------------------------------------------------------------------------------------------------
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

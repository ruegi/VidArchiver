# -*- coding: utf-8 -*-
'''
Created on 2018-06-01
@author: rg
Vidarchiver.py mit pyqt6

ermöglicht es, die Videos in den Prep-Verzeichnissen _in1..._in10
in die passenden VideoArchivOrdner einzusortieren

die Bezeichnungen der 3 ordnerEbenen der Mitte des Fensters sind:
oben:   'Main'  (enthält Musik, Sachfilm, Schule, Unterhaltung)
mittig: 'Sub'   (enthält je Main-ordner UnterOrdner)
unten:  'Base'  (enthält evtl. UnterOrdner zu Sub-Ordnern)
                Um keine weiteren Fenster zu öffnen, war es nötig, in 'Base' auch
                weitere Unterordner mit '/' getrennt einzuführen, z.B.

Anderungen:
    Version Datum       Inhalt
    ------- ----------  ------------------------------------------
    1.00    2022-11-27  Umstellung auf PyQt6; 
                        Öffnung dahingehend, dass alle Video-Ordner QuellOrdner sein können
    1.10    2023-01-09  Löschen Dateien der Eingangsseite angepasst:
                            - es werden jetzt mehrere Dateien auf einmal verarbeitet
                            - wird löschen im DelBasket durchgeführt, wird nach der Nachfrage
                                wirklich physisch aus DB und Ordner geköscht
    1.20    2023-02-12  Rename & Delete von Ordnern eingebaut, Buttons F2 tech.Info eingebaut;
                        Fehler beim Rename von Groß/Klein-Schreibung behoben
'''

import os
import sys
import time
from datetime import datetime
from math import log as logarit
from pathlib import Path
from subprocess import Popen

# import sqlalchemy
import sqlalchemy.sql.default_comparator  # das braucht pyinstaller zum Finden der Module

from PyQt6.QtCore import (QDir, QModelIndex, QObject, Qt, QThread, pyqtSignal, pyqtSlot, QUrl)
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (QAbstractItemView, QApplication, QDialog,
                             QHBoxLayout, QHeaderView,
                             QInputDialog, QLabel, QLineEdit, QMainWindow,
                             QMessageBox, QPushButton, QTableWidgetItem,
                             QVBoxLayout, QWidget)
# from PyQt6.QtMultimedia import QSoundEffect
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer

import vidarchdb
from privat import DBZugang

from VidArchiverPfaDialogUI import Ui_Dialog as Ui_DialogPfadNeu
from VidArchiverRenDialogUI import Ui_Dialog as Ui_DialogRename
# die fenster wurden mit dem qtdesigner entworfen und per pyuic6 konvertiert
from VidArchiverUI import Ui_MainWindow

# Handle high resolution displays (thx 2 https://stackoverflow.com/questions/43904594/pyqt-adjusting-for-different-screen-resolution):
# In PyQt6 nicht mehr erforderlich!
if hasattr(Qt, 'AA_EnableHighDpiScaling'):
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

stopFlag = False
# --------------------------------------------------------------------------------
# Konstanten des Programms
# --------------------------------------------------------------------------------
class Konstanten():
    VideoDir = "y:\\video"
    LoeschOrdner = "__del"
    ProgrammIcon = 'VidArchiver.ico'
    VersionString = "V1.2 rg 12.02.2023"
    PrepPfadBeginn = "_"    
    DBNAME = DBZugang.DBTitel
    FilmInfo = 'c:\\Program Files\\FilmDetails\\FilmDetails.exe'
    # bellSound = "Windows_Error.wav"
    bellSound = "warning.mp3"

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
        self.vpath   = Konstanten.VideoDir
        self.delBasket = Konstanten.LoeschOrdner
        self.app = app
        self.worker = None
        self.ArchivReload = True
        self.PrepReload = True
        self.updateDialog = None
        self.pfadDialog = None
        self.archivListe = []   # enthält eine Liste von Tupeln mit den ZielPfaden
        self.aktMain = ""
        self.aktSub = ""
        self.aktBase = ""

        # Icon versorgen
        scriptDir = os.path.dirname(os.path.realpath(__file__))
        self.setWindowIcon(QIcon(scriptDir + os.path.sep + Konstanten.ProgrammIcon))

        self.le_vidArchPfad.setText(self.vpath) # --------------------------------
        self.le_vidArchPfad.setDisabled(True)

        self.lbl_version.setText(Konstanten.VersionString)
        self.lbl_db.setText(Konstanten.DBNAME)

        header = self.tbl_film.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        # header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        # header.setSectionResizeMode(2, QHeaderView.ResizeToContents)

        self.tbl_film.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl_film.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        self.tbl_vorhFilm.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl_vorhFilm.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        header = self.tbl_vorhFilm.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)

        header = self.tbl_film.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        #header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        #header.setSectionResizeMode(2, QHeaderView.ResizeToContents)

        self.cb_quelle.addItems(self.prepPfadeLaden(self.le_vidArchPfad.text()))        
        if self.cb_quelle.count() > 0:
            self.prepFilmeLaden()
        else:
            self.filmliste = []

        self.ladeVidArchPfade()

        self.statusMeldung("Ready")

        # connects
        # --------------------------------------------------------------------------------------------
        self.cb_quelle.currentIndexChanged.connect(self.quelleLaden)
        self.btn_showPrepVideo.clicked.connect(self.videoPrepStart)
        self.lst_vidPfad_Main.currentRowChanged.connect(self.setPath_Main)
        self.lst_vidPfad_Main.doubleClicked.connect(self.sortVideoInArch)        
        self.lst_vidPfad_Sub.doubleClicked.connect(self.sortVideoInArch)
        self.lst_vidPfad_Sub.clicked.connect(self.setPath_Sub)
        self.lst_vidPfad_Sub.currentRowChanged.connect(self.setPath_Sub)
        self.lst_vidPfad_Base.currentRowChanged.connect(self.setPath_Base)
        self.lst_vidPfad_Base.doubleClicked.connect(self.sortVideoInArch)
        self.tbl_film.itemSelectionChanged.connect(self.videoPrepDetail)
        self.tbl_film.cellActivated.connect(self.videoPrepStart)
        self.btn_renamePrep.clicked.connect(lambda: self.videoPrepRen(self.le_PrepFilm.text()))
        self.btn_delPrep.clicked.connect(self.videoPrepDel)
        self.tbl_vorhFilm.itemSelectionChanged.connect(self.videoArchDetail)
        self.tbl_vorhFilm.cellActivated.connect(self.videoArchStart)        
        self.btn_showArchVideo.clicked.connect(self.videoArchStart)
        self.btn_del.clicked.connect(self.videoArchDel)
        self.btn_rename.clicked.connect(lambda: self.videoArchRen(self.le_ArchivFilm.text()))
        self.btn_linkVideo.clicked.connect(self.sortVideoInArch)
        self.btn_unlinkVideo.clicked.connect(self.unsortVideoInArch)
        ### self.lst_vidPfad.doubleClicked.connect(self.sortVideoInArch)
        self.btn_pfadNeu.clicked.connect(self.neuerArchPfad)
        self.btn_pfadRen.clicked.connect(self.renArchPfad)
        self.btn_pfadDel.clicked.connect(self.delArchPfad)
        self.btn_QInfo.clicked.connect(self.QTechInfo)
        self.btn_ZInfo.clicked.connect(self.ZTechInfo)
        self.videoPrepDetail()
        self.videoArchDetail()


    # Key-Press-Events auswerten
    def keyPressEvent(self, event):
        w = self.focusWidget()
        filmname = self.le_PrepFilm.text()
        
        # self.statusMeldung("filmName = {}".format(filmname))
        if event.key() == Qt.Key.Key_F5:
            if (event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
                shift = True
                if w == self.tbl_vorhFilm:
                    self.unsortVideoInArch()
            else:
                shift = False
                if w == self.lst_vidPfad_Base or w == self.lst_vidPfad_Sub or w == self.lst_vidPfad_Main or w == self.tbl_film:
                    self.sortVideoInArch()
        elif event.key() == Qt.Key.Key_Enter or event.key() == Qt.Key.Key_Return:
            if w == self.tbl_vorhFilm:
                self.videoArchStart()
            elif w == self.tbl_film:
                self.videoPrepStart()
            # elif w == self.lst_vidPfad:
            #     self.sortVideoInArch()            
            elif w == self.le_vidArchPfad:
                self.prepPfadeLaden(w.text())
        elif event.key() == Qt.Key.Key_F3:
            if filmname > "":
                self.videoPrepStart()
        elif event.key() == Qt.Key.Key_F6:            
            if filmname > "":
                self.videoPrepRen(filmname)
        elif event.key() == Qt.Key.Key_F8:            
            if filmname > "":
                self.videoPrepDel()
        elif event.key() == Qt.Key.Key_F2:
            self.videoTechInfo()
        
        return

    # Verwaltung der linken seite
    # --------------------------------------------------------------------------------------------
    def getCurrentPrepPath(self):
        if self.cb_quelle.currentIndex() < 0:
            return(None)
        else:
            return(self.vpath + os.sep + self.cb_quelle.currentText())

    def getCurrentRelPrepPath(self):
        if self.cb_quelle.currentIndex() < 0:
            return(None)
        else:
            return(self.cb_quelle.currentText())



    def getCurentPrepFilm(self):
        # vid = self.vpath + os.path.sep + str(self.cb_quelle.currentText()) + os.path.sep + self.tbl_film.item(row, col).text()
        # self.videoStart(vid)        
        aktrow = self.tbl_film.currentRow()
        # print("row=", row)
        if aktrow is None or aktrow < 0:
            return None
        else:
            if self.tbl_film.item(aktrow, 0) is None:
                return None
            else:
                # print(type(self.tbl_film.item(row, 0)))
                return(self.tbl_film.item(aktrow, 0).text())

    @pyqtSlot(int)
    def quelleLaden(self, quellIndex):
        if self.cb_quelle.count() > 0:
            self.filmliste = self.filmeLaden(self.le_vidArchPfad.text() + os.path.sep + str(self.cb_quelle.currentText()))
        else:
            self.filmliste = []


    def prepPfadeLaden(self, vdir):
        preppfad = leseUV(vdir)
        # preppfad.sort()
        return preppfad

    @pyqtSlot()
    def prepFilmeLaden(self):
        self.filmliste = self.filmeLaden(self.le_vidArchPfad.text() + os.path.sep + str(self.cb_quelle.currentText()))
        if len(self.filmliste) > 0:
            self.tbl_film.setCurrentCell(0, 0)

    def filmeLaden(self, prepdir, pos=None):
        '''
        lädt die Filme aus dem gewählten prep-Pfad in die Tabelle self.tbl_film
        '''
        filmliste = []
        self.PrepReload = True
        self.tbl_film.clearContents()
        self.tbl_film.setRowCount(0)
        self.tbl_film.setColumnCount(1)
        nr = 0
        for root, dirs, files in os.walk(prepdir):
            for fil in files:
                vid = prepdir + os.path.sep + fil
                self.tbl_film.insertRow(nr)
                self.tbl_film.setItem(nr, 0, QTableWidgetItem(str(fil)))
                # print(self.tbl_film.item(nr, 0).text())
                filmliste.append(vid)
                # print(fil)
                # print(nr, self.tbl_film.rowCount())
                nr += 1
            break   # nur oberste Ebene zählt

        self.PrepReload = False
        if nr > 0:
            self.tbl_film.setSortingEnabled(True)
            self.tbl_film.sortByColumn(0, Qt.SortOrder.AscendingOrder)

            if pos is None:
                self.tbl_film.setCurrentCell(0,0)
            else:   # versuchen zu positionieren
                lst = self.tbl_film.findItems(pos, Qt.MatchFlag.MatchExactly)
                if len(lst) > 0:
                    self.tbl_film.setCurrentItem(lst[0])
                else:
                    self.tbl_film.setCurrentCell(0, 0)
            self.videoPrepDetail()

        # print(filmliste)
        return filmliste

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
    def videoPrepDetail(self):
        # print("videoPrepDetail: self.PrepReloaded=", self.PrepReload, "; self.tbl_film.rowCount()=", self.tbl_film.rowCount())
        if self.PrepReload or (self.tbl_film.rowCount() == 0):
            # self.tbl_film.clearContents()
            self.le_PrepFilm.setText("")
            self.le_PrepFilmGr.setText("")
            self.le_PrepFilmDat.setText("")
            return
        else:
            pdir = self.getCurrentPrepPath()
            pfilm = self.getCurentPrepFilm()
            if pdir is None or pfilm is None:
                self.le_PrepFilm.setText("")
                self.le_PrepFilmGr.setText("")
                self.le_PrepFilmDat.setText("")
            else:
                # print(self.lst_vidPfad.currentItem().text())
                # fil = self.tbl_vorhFilm.item(self.tbl_vorhFilm.currentRow(), 0).text()
                vid = pdir + os.path.sep + pfilm
                try:
                    oss = os.stat(vid)
                    vlen = format_size(oss.st_size)                
                    vdat = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(oss.st_ctime))
                except:
                    vlen = "???"
                    vdat = "DB is async!"            
                self.le_PrepFilm.setText(pfilm)
                self.le_PrepFilmGr.setText(vlen)
                self.le_PrepFilmDat.setText(vdat)
        self.le_PrepFilm.setReadOnly(True)
        self.le_PrepFilmGr.setReadOnly(True)
        self.le_PrepFilmDat.setReadOnly(True)

    @pyqtSlot()
    def videoPrepDel(self):
        prepO = self.getCurrentPrepPath()
        prepOR = self.getCurrentRelPrepPath()
        
        pos = None
        lstItems = self.tbl_film.selectedItems()
        pos = lstItems[0].text()
        i = 0
        moved = 0

        filmListe = []
        anzFilme = 0 
        for itm in lstItems:
            anzFilme += 1
            #                if (i % 3) == 1:    # nur Item 1, 4, 7 usw sind Dateinamen
            if itm.column() == 0:  # nur Dateinamen
                filmListe.append(itm.text())
                       
        # fname = self.getCurentPrepFilm()
        if anzFilme is None:
            return
        
        if prepOR == self.delBasket:
            reply = QMessageBox.question(self, "Wirklich?",
                                        f"{anzFilme} Filme aus der DB und dem Archiv löschen?\n\nAchtung!\n" +
                                        "Es wird wirklich gelöscht!",
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes.value:
                for fname in filmListe:
                    #  pysisches Löschen aus dem delBasket
                        delVideo = prepO + os.sep + fname
                        # delTarget = self.vpath + os.sep + self.delBasket + os.sep + fname
                        try:
                            if vidarchdb.film_loeschen(delVideo):
                                # das macht vidarchdb.film
                                pass
                            else:
                                self.statusMeldung("Fehler! Konnte den Film nicht löschen!")
                        except OSError as err:
                            self.statusMeldung("Fehler! ({})".format(err.strerror))
                        finally:
                            nr = self.tbl_film.currentRow() + 1
                            rc = self.tbl_film.rowCount()
                            if rc == 1:     # letzter Film wird gelöscht
                                nextFilm = None
                            else:
                                if nr >= rc:
                                    nr = 0
                                try:
                                    nextFilm = self.tbl_film.item(nr, 0).text()
                                except:
                                    nextFilm = None
                            self.filmeLaden(prepO, pos=nextFilm)
                            # self.filme_aus_Archiv_laden(pos=self.getNextTableText(self.tbl_vorhFilm, frow))
                            self.statusMeldung(
                                "Der Film [{0}] wurde aus dem Archiv gelöscht!".format(fname))
                else:
                    self.statusMeldung("Löschen abgebrochen!")
        else:
            reply = QMessageBox.question(self, "Wirklich?",
                                        f"{anzFilme} Filme aus dem Archiv löschen?\n\nHinweis!\n" 
                                        "Es wird nur in dem Mülleimer [{}] verschoben!".format(
                                            self.vpath + os.sep + self.delBasket),
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes.value:
                for fname in filmListe:
                    # in den delBasket verschieben        
                    delVideo = prepO + os.sep + fname
                    delTarget = self.vpath + os.sep + self.delBasket + os.sep + fname
                    nr = self.tbl_film.currentRow() + 1
                    rc = self.tbl_film.rowCount()
                    if rc == 1:     # letzter Film wird gelöscht
                        nextFilm = None
                    else:
                        if nr >= rc:
                            nr = 0
                        try:
                            nextFilm = self.tbl_film.item(nr, 0).text()
                        except:
                            nextFilm = None
                    try:
                        if vidarchdb.film_umbenennen(delVideo, delTarget):
                            os.rename(delVideo, delTarget)
                        else:
                            self.statusMeldung("Fehler! Konnte die DB nicht ändern!")
                    except OSError as err:
                        self.statusMeldung("Fehler! ({})".format(err.strerror))
                    finally:
                        # hier mus noch etwas gezaubert werden, um nicht auf 0 zu repositionieren
                        self.filmeLaden(prepO, pos=nextFilm)
                        self.statusMeldung(
                            "Der Film [{0}] wurde aus dem Archiv nach [{1}] verschoben!".format(fname, delTarget))
                else:
                    self.statusMeldung("Löschen abgebrochen!".format(fname))
        return

    @pyqtSlot(str)
    def videoPrepRen(self, fname):
        # startet einen Dialog zur Erfassung des neuen VideoNamens
        alterName = fname
        pfad = self.getCurrentPrepPath()
        neuerName, ok = QInputDialog.getText(self, 'Fim im Prep-Ordner umbenennen', 'Neuer Name:',
                                        QLineEdit.EchoMode.Normal, alterName)        
        if ok:
            neuerFullName = pfad + os.sep + neuerName
            alterFullName = pfad + os.sep + alterName
            try:
                if vidarchdb.film_umbenennen(alterFullName, neuerFullName):
                    os.rename(alterFullName, neuerFullName)
                else:
                    self.statusMeldung("Fehler! Konnte die DB nicht ändern!")
            except OSError as err:
                self.statusMeldung("Fehler! ({})".format(err.strerror))
            finally:
                self.statusbar.showMessage("Video umbenannt in: {}".format(neuerName))
                # print(neuerName)
                self.filmeLaden(pfad, pos=neuerName)
        return


    # Verwaltung der rechten seite
    # --------------------------------------------------------------------------------------------
    def getCurrentArchPath(self):
        ''' 
        ermittelt den aktuellen Archiv-Pfad
        '''
        pfad = self.vpath + os.sep
        if self.aktBase > "":
            pfad += self.aktMain + os.sep + self.aktSub + os.sep + self.aktBase
        elif self.aktSub > "":
            pfad += self.aktMain + os.sep + self.aktSub
        elif self.aktMain > "":
            pfad += self.aktMain + os.sep
        else:
            pfad = None
        # print(f'Analysiert: {pfad}')
        self.lbl_ArchivFilm.setText("Archiv: " + pfad)
        return pfad


    def getCurentArchFilm(self):
        row = self.tbl_vorhFilm.currentRow()
        if row < 0:
            # print("Aktuelle Zeile in ArchFilm ist {}".format(row))
            return (None)
        else:
            return(self.tbl_vorhFilm.item(row, 0).text())


    def setCurrentArchPath(self, pos):
        ''' 
        setzt den aktuell eingestellten Pfad der Archiv-Listen auf 'pos'
        '''
        tpl = Path(pos).parts
        base = ""
        sub = ""
        main = ""
        if len(tpl) > 4:    # 4 & mehr
            base = os.sep.join(tpl[4:])
            sub = tpl[3]
            main = tpl[2]
        elif len(tpl) == 3:
            sub = tpl[3]
            main = tpl[2]
        elif len(tpl) == 2:
            main = tpl[2]
        else:
            pass

        # print(f"({main}), ({sub}), ({base})")
        self.listeAnpassen(self.lst_vidPfad_Main, main)
        self.listeAnpassen(self.lst_vidPfad_Sub, sub)
        self.listeAnpassen(self.lst_vidPfad_Base, base)
        # QApplication.processEvents()
        return

    def listeAnpassen(self, listenObjekt, wert):
        # stellt die Auswahl eines ListenObjekts auf die gewünschte Auswahl
        fnd = -1
        for i in range(listenObjekt.count()):
            if listenObjekt.item(i).text() == wert:
                fnd = i
                break
        if fnd > -1:
            listenObjekt.setCurrentItem(listenObjekt.item(fnd))
            # print(listenObjekt.item(fnd).text())
        return

    @pyqtSlot()
    def setPath_Main(self):
        itm = self.lst_vidPfad_Main.currentItem()
        if itm is None:
            return
        aMain = str(itm.text())
        # aMain = str(self.lst_vidPfad_Main.item(newrow).text())
        # if self.aktMain == aMain:   # nothing 2 do
        #     return
        # else:                        
        self.aktMain = aMain            
        self.vidSub_fuellen()
        self.vidBase_fuellen()
        self.filme_aus_Archiv_laden()
        # print(self.aktMain, self.aktSub, self.aktBase)
        return

    def setPath_Sub(self):
        itm = self.lst_vidPfad_Sub.currentItem()
        if itm is None:   
            self.aktSub = ""
            self.aktBase = ""            
        else:
            aSub = str(itm.text())
            self.aktSub = aSub
            # print(aSub)
            # if self.aktSub == aSub:   # nothing 2 do
            #     return
            # else:        
            self.vidBase_fuellen()
            self.filme_aus_Archiv_laden()
            # print(self.aktMain, self.aktSub, self.aktBase)
        return

    def setPath_Base(self):
        itm = self.lst_vidPfad_Base.currentItem()
        if itm is None:
            self.aktBase = ""
            return
        else:
            aBase = itm.text()        
        if self.aktBase == aBase:   # nothing 2 do
            return
        else:
            self.aktBase = aBase
            self.filme_aus_Archiv_laden()
        # print(self.aktMain, self.aktSub, self.aktBase)
        return

    def ladeVidArchPfade(self, pos=None):
        ''' 
        lädt alle ZielPfade im Archiv neu ein
        opt. Parm pos: Zielpfad, auf den positioniert werden soll (z.B. ein neuer Unterordner)
        '''
        self.lst_vidPfad_Main.clear()
        lst = self.zielPfadeLaden(self.vpath)   # alle Pfad als string-Liste und als Liste von Tupeln einlesen
        # Main füllen
        main_word = ""
        # if not pos is None:
        #     print("pos=", pos)

        for liste in self.archivListe:  # ein Tupel nach dem anderen auf den Hauptbegriff prüfen und diesen merken
            # alles durchlesen die Ornder [1] unique sammeln
            main = str(liste[1])                        
            # print(main, liste)
            if main_word == main:    # bekannten Eintrag gefunden
                continue             # überlesen
            else:
                if self.aktMain == "":  # ggf. neuen pos-eintrag festlegen
                    self.aktMain = main
                main_word = main    # neue Main-Sequenz                
                self.lst_vidPfad_Main.addItem(main)
            
        self.vidSub_fuellen()        
        # print(f"ladeVidArchPfade: ({self.aktMain}), ({self.aktSub}), ({self.aktBase})")
        if not pos is None:
            self.setCurrentArchPath(pos)
        return

    def vidSub_fuellen(self, pos=None):
        ''' Füllt die Liste vidSub mit Einträgen
        '''
        self.lst_vidPfad_Sub.clear()
        self.aktSub = ""
        # subListe = list(l[2] for l in self.archivListe if l[1] == self.aktMain)
        # self.lst_vidPfad_Sub.addItems(subListe)
        sub_word = ""
        for liste in self.archivListe:
            if len(liste) > 2 and liste[1] == self.aktMain:
                sub = liste[2]
                # print(sub, liste)
                if sub == sub_word:
                    continue
                else:
                    sub_word = sub
                    # if self.aktSub == "":
                    #     self.aktSub = sub
                    self.lst_vidPfad_Sub.addItem(sub)
        self.vidBase_fuellen()
        return

    def vidBase_fuellen(self):
        ''' Füllt die Liste vidBase mit Einträgen
        '''
        self.lst_vidPfad_Base.clear()
        self.aktBase = ""
        for lst in self.archivListe:
            if len(lst) > 3 and lst[1] == self.aktMain and lst[2] == self.aktSub:
                baseDir = "/".join(x for x in lst[3:])
                self.lst_vidPfad_Base.addItem(baseDir)
        return

    @pyqtSlot()
    def filme_aus_Archiv_laden(self, pos=None):
        '''
        lädt die Filme aus dem gewählten Archiv-Pfad in die Tabelle self.tbl_vorhFilm
        :parameter
        adir:   str     Archiv-Directory, dessen Inhalt gelistet werden soll
        pos=None  [None / str]  ggf. Name eines Videos, auf das positioniert werden soll
        '''

        adir = self.getCurrentArchPath()
        if adir is None:
            return

        self.ArchivReload = True
        self.tbl_vorhFilm.clearContents()
        self.tbl_vorhFilm.setRowCount(0)
        self.tbl_vorhFilm.setSortingEnabled(True)

        nr = 0
        for root, dirs, files in os.walk(adir):
            for fil in files:
                # vid = adir + os.path.sep + fil
                self.tbl_vorhFilm.insertRow(nr)
                self.tbl_vorhFilm.setItem(nr, 0, QTableWidgetItem(str(fil)))
                nr += 1
            break   # nur oberste Ebene zählt
        # Einträge sortieren
        self.tbl_vorhFilm.sortItems(0, Qt.SortOrder.AscendingOrder)
        self.ArchivReload = False        
        if nr > 0:
            if pos is None:
                self.tbl_vorhFilm.setCurrentCell(0,0)
            else:   # versuchen zu positionieren
                lst = self.tbl_vorhFilm.findItems(pos, Qt.MatchFlag.MatchExactly)
                if len(lst) > 0:
                    self.tbl_vorhFilm.setCurrentItem(lst[0])
                else:
                    self.tbl_vorhFilm.setCurrentCell(0, 0)
        return

    @pyqtSlot()
    def videoArchDetail(self):
        if self.ArchivReload or self.tbl_vorhFilm.rowCount() == 0:
            # self.tbl_vorhFilm.clearContents()
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

    @pyqtSlot()
    def videoArchStart(self):
        vpfad = self.getCurrentArchPath()
        film = self.getCurentArchFilm()
        if vpfad is None or film is None:
            return
        else:
            vid = vpfad + os.path.sep + film
            self.videoStart(vid)

    @pyqtSlot(str)
    def videoArchRen(self, fname):
        # startet einen Dialog zur Erfassung des neuen VideoNamens
        self.alterName = fname
        self.updateDialog = renameDialog()
        self.updateDialog.le_rename.setText(self.alterName)
        self.updateDialog.accepted.connect(lambda: self.renameArchivDialogOK())
        self.updateDialog.rejected.connect(lambda: self.renameArchivDialogCancel())
        self.updateDialog.le_rename.setFocus()
        self.updateDialog.exec()
        return

    @pyqtSlot()
    def renameArchivDialogOK(self):        
        pfad = self.getCurrentArchPath()
        neuerName = self.updateDialog.le_rename.text()
        neuerFullName = pfad + os.sep + neuerName
        alterFullName = pfad + os.sep + self.alterName
        # print(f"{neuerFullName =}, \n{alterFullName =}")
        # prüfen, ob es das Ziel schon gibt
        #Achtung! Windows unterscheidet Groß/Kleischreibung nicht!
        if not neuerFullName.lower() == alterFullName.lower():
            if os.path.exists(neuerFullName):
                self.statusMeldung(f"Fehler! Die Datei [{neuerFullName}] existiert bereits!")
                return
        try:
            if vidarchdb.film_umbenennen(alterFullName, neuerFullName):
                os.rename(alterFullName, neuerFullName)
                self.statusbar.showMessage("Video umbenannt in: {}".format(neuerName))
            else:
                self.statusMeldung("Fehler! Konnte die DB nicht ändern!")            
        except OSError as err:
            self.statusMeldung("Fehler! ({})".format(err.strerror))
        finally:
            self.filme_aus_Archiv_laden(pos=neuerName)
        return


    @pyqtSlot()
    def renameArchivDialogCancel(self):
        self.statusbar.showMessage("renameDialog Cancel: {}".format(self.updateDialog.le_rename.text()))


    @pyqtSlot()
    def videoArchDel(self):
        '''
        verschiebt einen Film in den DelBasket oder löscht sogar physisch aus dem DelBasket heraus
        '''
        fname = self.getCurentArchFilm()
        frow = self.tbl_vorhFilm.currentRow()
        if fname is None:
            return

        adir = self.getCurrentArchPath()


        # in den delBasket verschieben        
        reply = QMessageBox.question(self, "Wirklich?",
                                    "Film [{0}] aus dem Archiv löschen?\n\nKeine Panik!\n".format(fname) +
                                    "Der Film wird nur in dem Mülleimer [{}] verschoben!".format(
                                        self.vpath + os.sep + self.delBasket),
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes.value:
            delVideo = adir + os.sep + fname
            delTarget = self.vpath + os.sep + self.delBasket + os.sep + fname
            try:
                if vidarchdb.film_umbenennen(delVideo, delTarget):
                    os.rename(delVideo, delTarget)
                else:
                    self.statusMeldung("Fehler! Konnte die DB nicht ändern!")
            except OSError as err:
                self.statusMeldung("Fehler! ({})".format(err.strerror))
            finally:

                self.filme_aus_Archiv_laden(pos=self.getNextTableText(self.tbl_vorhFilm, frow))
                self.statusMeldung(
                    "Der Film [{0}] wurde aus dem Archiv nach [{1}] verschoben!".format(fname, delTarget))
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
                        if vidarchdb.film_umbenennen(qVideoFull, zVideoFull):
                            os.rename(qVideoFull, zVideoFull)
                        else:
                            self.statusMeldung("Fehler! Konnte die DB nicht ändern!")
                    except OSError as err:
                        QMessageBox.warning(self, "Achtung / Fehler",
                                            "Konnte die Datei [{}] nicht nach [{}] bewegen!".format(qVideoName,
                                                                                                    zVideoTarget) +
                                            "Fehlermedlung: {0}".format(err.strerror),
                                            QMessageBox.StandardButton.Ok)
                        self.statusMeldung("Fehler! ({})".format(err.strerror))
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
            self.statusMeldung(
                "Es wurden {0} Filme in das Archiv nach [{1}] verschoben!".format(moved, zVideoTarget))
        return

    @pyqtSlot()
    def unsortVideoInArch(self):
        '''
        nimmt den aktuellen Film aus dem ArchivOrdner und sortiert ihn in den aktuellen PrepOrdner ein
        :return: ---
        '''
        pos = None
        lstItems = self.tbl_vorhFilm.selectedItems()
        if lstItems:
            # print(len(lstItems))
            pdir = self.getCurrentPrepPath()
            adir = self.getCurrentArchPath()
            pos = lstItems[0].text()
            npos = self.getNextTableText(self.tbl_vorhFilm, self.tbl_vorhFilm.currentRow())
            i = 0
            moved = 0
            for itm in lstItems:
                i += 1
                #                if (i % 3) == 1:    # nur Item 1, 4, 7 usw sind Dateinamen
                if itm.column() == 0:  # nur Dateinamen
                    qVideoName = itm.text()
                    qVideoFull = adir + os.sep + qVideoName
                    zVideoTarget = pdir
                    zVideoFull = zVideoTarget + os.sep + qVideoName
                    # print(i, ": ", qVideoFull, " --> ", end="")
                    # print(zVideoFull)
                    try:
                        if vidarchdb.film_umbenennen(qVideoFull, zVideoFull):
                            os.rename(qVideoFull, zVideoFull)
                    except OSError as err:
                        QMessageBox.warning(self, "Achtung / Fehler",
                                            "Konnte die Datei [{}] nicht nach [{}] bewegen!".format(qVideoName,
                                                                                                    zVideoTarget) +
                                            "Fehlermedlung: {0}".format(err.strerror),
                                            QMessageBox.StandardButton.Ok)
                        self.statusMeldung("Fehler! ({})".format(err.strerror))
                        break
                    finally:
                        time.sleep(0.2)
                        moved += 1
                        i += 1
                else:

                    continue

            self.filmeLaden(pdir, pos=pos)
            self.filme_aus_Archiv_laden(pos=npos)

        if moved == 1:
            self.statusMeldung("Es wurde ein Film aus dem Archiv nach [{0}] verschoben!".format(zVideoFull))
        else:
            self.statusMeldung(
                "Es wurden {0} Filme aus dem Archiv nach [{1}] verschoben!".format(moved, zVideoTarget))
        return

    # Verwaltung der Mitte
    # --------------------------------------------------------------------------------------------
    def zielPfadeLaden(self, vdir):
        '''
        lädt die verfügbaren Ordner im Archiv in eine Liste;
        übergeht dabei alle Ordner mit beginnendem "_" auf oberster Ebene
        Param:  vdir    Ordner des Archives
        setzt als side-effekt die Liste self.archivListe: jedes Element ist ein Tupel der Ordner
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
        zpfade = sorted(zielpfad)
        self.archivListe = []
        for s in zpfade:  # alle Teilpfade in eine Liste aufsplitten und als Liste von Listen speichern
            p = Path(s).parts
            self.archivListe.append(p[1:])  # erstellt ein Tupel der Ordner ohne das Laufwerk Y:\\
        # print(f'zielPfadeLaden: ({self.archivListe})')
        return zpfade

    @pyqtSlot(int, int)
    def videoArchInfo(self):
        adir = self.getCurrentArchPath()
        film = self.getCurentArchFilm()        

        if adir is None or film is None:
            vid = ""
        else:
            vid = adir + os.path.sep + film
        self.statusMeldung(vid)

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
        self.pfadDialog.exec()
        return

    @pyqtSlot()
    def pfadDialogOK(self):
        pfad = self.getCurrentArchPath()
        if pfad is None:
            self.statusMeldung("Kein aktueller ArchivPfad ?? -  nichts zu tun!")
            return
        neuerPfad = pfad + os.sep + self.pfadDialog.le_pfad.text()
        if neuerPfad.startswith(Konstanten.VideoDir):
            relPfad = neuerPfad[len(Konstanten.VideoDir)+1:]
        else:
            relPfad = neuerPfad
        # print(pfad, " --> ", neuerPfad)
        # ergänzung 2022-11-25: Backslash verhindern
        if relPfad.index("\\") >= 0:
            relPfad = relPfad.replace("\\", "/")
        try:
            os.makedirs(neuerPfad, exist_ok=False)  # gibt sonst eine Exception, wenn der Ordner schon da ist
            if not vidarchdb.anlage_relpath(None, relPfad):
                self.statusbar.showMessage("DB-Fehler bei der NeuAnlage des Pfades [{}]".format(relPfad))
        except OSError as err:
            self.statusMeldung("Fehler! Kann den Ordner nicht anlegen! ({})".format(err.strerror))
            QMessageBox.Warning(self, "Fehler",
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


    @pyqtSlot()
    def renArchPfad(self):
        '''
        erzeugt einen Dialog für das Umbenennen des aktuellen Archiv-UnterOrdners
        :return: ---
        '''
        self.renEbene = "Base"
        self.pfad2chg = ""
        self.aktPfad = ""
        # zunächst die Ebene bestimmen
        if self.aktBase:
            self.aktPfad = self.aktMain + os.sep + self.aktSub + os.sep + self.aktBase
            self.pfad2chg = self.aktBase
            self.renEbene = "Base"
        elif self.aktSub:
            self.aktPfad = self.aktMain + os.sep + self.aktSub
            self.pfad2chg = self.aktSub
            self.renEbene = "Sub"
        else:
            self.aktPfad = self.aktMain
            self.pfad2chg = self.aktMain
            self.renEbene = "Main"
                
        # print(f"{self.renEbene}, {self.aktPfad =}, {self.pfad2chg =}")

        self.alterName = self.pfad2chg
        self.pfadDialog = pfaDialog()
        self.pfadDialog.le_pfad.setText(self.alterName)
        self.pfadDialog.setWindowTitle("UnterOrdner umbenennen")
        self.pfadDialog.groupBox.setTitle(f"[{self.aktPfad}] umbenennen!")
        self.pfadDialog.accepted.connect(lambda: self.pfadRenDialogOK())
        self.pfadDialog.rejected.connect(lambda: self.pfadRenDialogCancel())
        self.pfadDialog.le_pfad.setFocus()
        self.pfadDialog.show()

    @pyqtSlot()
    def pfadRenDialogOK(self):
        '''
        benennt den Base-Ordner um
        '''
        newPfad = self.pfadDialog.le_pfad.text()
        oldPfad = self.aktBase
        if newPfad == oldPfad:
            self.statusbar.showMessage("Keine Änderung, kein umbenennen!")
            return

        relPfad = self.aktMain + os.sep + self.aktSub
        pfad = Konstanten.VideoDir + os.sep + relPfad
        alterPfad = pfad + os.sep + oldPfad
        neuerPfad = pfad + os.sep + newPfad

        relAltPfad = relPfad + os.sep + oldPfad
        relNeuPfad = relPfad + os.sep + newPfad

        # ergänzung 2022-11-25: Backslash verhindern
        if relPfad.index("\\") >= 0:
            relPfad = relPfad.replace("\\", "/")
        # es könne mehrere Einträge der Tabelle vapfad betroffen sein,
        # obwohl nur ein Pfad verändert wird!
        try:
            os.rename(alterPfad, neuerPfad)
            if not vidarchdb.rename_relpath(relAltPfad, relNeuPfad):
                self.statusbar.showMessage("DB-Fehler bei der NeuAnlage des Pfades [{}]".format(relPfad))
                os.rename(neuerPfad, alterPfad) # reparieren!
                # time.sleep(0.300)
                self.ladeVidArchPfade(pos=alterPfad)
                QMessageBox.Warning(self, "Fehler",
                        "Der Ordner [{neuerPfad}} konnte nicht angelegt werden\n" +
                            f"FehlerMeldung:\nDB-Fehler: [{vidarchdb.DBError}]", QMessageBox.Close)            
                return
            else:
                self.ladeVidArchPfade(pos=neuerPfad)
                self.statusbar.showMessage("Neuen Pfad angelegt: {}".format(neuerPfad))
        except OSError as err:
            self.statusMeldung("Fehler! Kann den Ordner nicht anlegen! ({})".format(err.strerror))
            QMessageBox.Warning(self, "Fehler",
                                    "Der Ordner [{}} konnte nicht angelegt werden\n\n".format(neuerPfad) +
                                     "FehlerMeldung: [{}]".format(err.strerror), QMessageBox.Close)            
        return

    @pyqtSlot()
    def pfadRenDialogCancel(self):
        self.statusbar.showMessage("Pfad umbenennen - Cancel: {}".format(self.pfadDialog.le_pfad.text()))
        return

    @pyqtSlot()
    def delArchPfad(self):
        # löscht einen Archiv Ordner nur. wenn er leer ist
        relPfad = self.aktMain
        if self.aktSub:
            relPfad += os.sep + self.aktSub
            if self.aktBase:
                relPfad += os.sep + self.aktBase
        pfad = Konstanten.VideoDir + os.sep + relPfad
        
        if vidarchdb.delete_relpath(relPfad, Test=True):
            try:
                err = ""
                os.rmdir(pfad)
            except FileNotFoundError:
                err = f"Konnte den Ordner {pfad} nicht löschen - os.FileNotFound"
            except OSError:
                err = f"Konnte den Ordner {pfad} nicht löschen - nicht leer(os.OSError)"
            finally:
                if err:
                    QMessageBox.Warning(self, "Fehler",\
                                    "Der Ordner [{pfad}} konnte nicht gelöscht werden\n\n" +\
                                     f"FehlerMeldung: [{err}]", QMessageBox.Close)
                else:
                    ok = vidarchdb.delete_relpath(relPfad, Test=False)
                    if not ok:
                        os.mkdir(pfad) # Pfad wieder in OS erzeugen
                        QMessageBox.Warning(self, "Fehler",\
                                        "Der Ordner [{pfad}} konnte nicht gelöscht werden\n\n" +\
                                        f"FehlerMeldung: [{vidarchdb.DBError}]", QMessageBox.Close)
                return
      



    @pyqtSlot()
    def ZTechInfo(self):
        '''
        zeigt die tech Info des ZielFilms
        '''
        # w = self.focusWidget()
        # if not w == self.tbl_vorhFilm:
        #     self.tbl_vorhFilm
        pfad = self.getCurrentArchPath()
        fname = self.getCurentArchFilm()
        fname = pfad + os.path.sep + fname
        self.showTechInfo(fname)
        return

    @pyqtSlot()
    def QTechInfo(self):
        '''
        zeigt die tech Info des QuellFilms
        '''
        # w = self.focusWidget()
        # if not w == self.tbl_vorhFilm:
        #     self.tbl_vorhFilm
        pfad = self.getCurrentPrepPath()
        fname = self.getCurentPrepFilm()
        fname = pfad + os.path.sep + fname
        self.showTechInfo(fname)
        return



    @pyqtSlot()
    def videoTechInfo(self):
        # wird vom Button F2 angesteuert
        # zeigt die technischen Video-Daten eines Films im Focus, benutzt dazu ffmpeg
        # ergänzt 2021-02-03 rg
        #         
        self.statusMeldung(" TechInfo ... ")
        w = self.focusWidget()
        if w == self.tbl_vorhFilm:
            self.ZTechInfo()
            # pfad = self.getCurrentArchPath()
            # fname = self.getCurentArchFilm()
            # fname = pfad + os.path.sep + fname
        elif w == self.tbl_film:
            self.QTechInfo()
            # pfad = self.getCurrentPrepPath()
            # fname = self.getCurentPrepFilm()
            # fname = pfad + os.path.sep + fname
        else:
            return
    

    def showTechInfo(self, fname):
        '''
        show the text Info in a separate process
        Parameter:
        fname: full path to the film
        '''
        self.statusMeldung(f"Lade FilmDetails für {fname} . . .")
        QApplication.processEvents()
        proc = Popen([Konstanten.FilmInfo, fname] )
        proc.wait()
        self.statusMeldung("")
        return

    # ----------------------------------------------------------------------------------------------------------------
    # Funktionen
    # ----------------------------------------------------------------------------------------------------------------
    def getNextTableText(self, tbl, row, gollum=0):
        '''
        Such den Text in der Nachfolgezeile der angegebenen Zeile in Spalte gollum (default: Spalte 0)
        :param tbl: QTableWidget, auf die sich die such bezieht
        :param itm: aktuelles Item, dessen Nachfolger gesucht wird
        :return: Text des nachfolgenden Items oder None
        '''
        row = tbl.currentRow()
        col = gollum
        anz = tbl.rowCount()
        try:
            ctxt = tbl.item(row, col).text()
        except:
            ctxt = None
        if anz == 0:
            return None
        elif anz == 1:
            return ctxt
        else:
            # es gibt mehrere Einträge, den nächsten suchen
            nrow = (row + 1) % anz
            try:
                txt = tbl.item(nrow, col).text()
            except:
                txt = None
            return txt


    @pyqtSlot(str)
    def statusMeldung(self, meldung):
        self.statusbar.showMessage(meldung)


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
            bell()
        return


    def popupNachricht(self, txt: str):        
        bell()
        QMessageBox.warning(self, "Achtung", txt, QMessageBox.StandardButton.Ok)
        
        return

#
#   Allg Funktionen
#
def leseUV(ordner):
    '''
    liest alle Unterordner eines Ordners ein
    gibt sie als Liste relativer Ordnernamen zum Videodir zurück
    '''
    uvs = []
    for root, dirs, _ in os.walk(ordner):
        for dir in dirs:
            if dir.startswith(Konstanten.PrepPfadBeginn):
                # preppfad.append(dir)    # Pfad merken
                if "__pycache__" in dir:
                    continue
                pfad = root + "/" + dir
                pfad = pfad[len(Konstanten.VideoDir)+1:]
                pfad = pfad.replace("\\", "/")
                uvs.append(pfad)    # Pfad merken
        break   # nur eine Ebene zählt
    return uvs

def bell():    
    # effect = QSoundEffect()
    # effect.setSource(QUrl.fromLocalFile(Konstanten.bellSound))
    # effect.setVolume(0.25)
    # effect.setLoopCount(2)
    # effect.play()
    return
    # player = QMediaPlayer()
    # audio_output = QAudioOutput()
    # player.setAudioOutput(audio_output)
    # player.setSource(QUrl.fromLocalFile(Konstanten.bellSound))
    # audio_output.setVolume(50)
    # player.play()


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


if __name__ == '__main__':        
    app = QApplication(sys.argv)
    form = VidArchiverApp(app)    
    vidarchdb.defineAlert(form.popupNachricht)
    form.show()    
    app.exec()

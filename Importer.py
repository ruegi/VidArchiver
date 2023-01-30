# -*- coding: utf-8 -*-
'''
Importer.py
.
Kopiert Film aus dem lokalen Ordner E:\Filme\schnitt in einen Prep-Ordner, 
z.B. nach Y:\video\_in,
ermittelt dabei den Fingerprint (md5-Summe der ersten 64 KB) und die komplette 
MD5-Summe des Films und legt den Film in der vidarch-db ab
rg, 2023-01-30
Änderungen:

'''
from PyQt6.QtWidgets import (
    QMainWindow, QApplication, QFileDialog,
    QHeaderView,
    QLabel, QCheckBox, QComboBox, QMessageBox, 
    QTableWidget, QTableWidgetItem,
    QLineEdit, QProgressBar
)

from PyQt6.QtCore import Qt

from frm_ImporterUI import Ui_frm_Importer

# import sys
import os
from pathlib import Path, PurePath
from humanBytes import HumanBytes
import hashlib
import vidarchdb

# die Alert-Logik der vidaArchDB abschalten
def stummerAlert(txt):
    pass

vidarchdb.defineAlert(vidarchdb.stummerAlarm)


class KONSTANTEN():
    default_Quelle = r"E:\filme\schnitt"
    default_Ziel = r"Y:\video"
    ZielOrdnerAnfang = "_in"
    verschiebeOrdner = r"E:\filme\schnitt.alt"


# Namen der Quell- und ZielPfade
QuellPfad = KONSTANTEN.default_Quelle
ZielPfad = os.path.join(KONSTANTEN.default_Ziel, KONSTANTEN.ZielOrdnerAnfang)
zielPfadId = 0     #  wird von Frm_kopieren.zielOrdnerAnpassen versorgt


class FilmEintrag():
    def __init__(self, filmName: str) -> None:
        self.filmName = filmName                            # nur der FilmName mit Ext.
        self.fullName = os.path.join(QuellPfad, self.filmName)    # Voller Pfad & Name
        self.filmExt = PurePath(self.filmName).suffix
        if os.path.exists(self.fullName):
            self.filmBytes = os.path.getsize(self.fullName)
            self.filmBytesAnz = HumanBytes.format(self.filmBytes, True, 3)
            self.filmStatus = "bereit"
        else:
            self.filmBytes = "-"
            self.filmStatus = "NOT FOUND"
            self.filmBytesAnz = ""
        self.filmFP = ""
        self.filmMD5 = ""

filmListe = list[FilmEintrag]

stopFlag = False

# Klasse für das Fenster, um Filme ins Archiv zu kopieren
class Frm_Kopieren(QMainWindow, Ui_frm_Importer):
    def __init__(self) -> None:
        super().__init__()
        self.setupUi(self)
        self.filmAnz = 0    # Anzahl der Filme in der FilmListe
        self.filmPos = 0    # nr des aktuell bearbeiteten Films in der filmListe

        self.le_quellOrdner.setText(KONSTANTEN.default_Quelle)
        self.btn_quelleSuchen.clicked.connect(self.quelleSuchen)
        self.ladeZielOrdner()
        self.zielOrdnerAnpassen()
        self.ladeFilme(KONSTANTEN.default_Quelle)
        self.cb_zielOrdner.currentTextChanged.connect(self.zielOrdnerAnpassen )
        self.btn_abbruch.clicked.connect(self.abbruch)
        self.btn_start.clicked.connect(self.start)

        self.tbl_filme.setShowGrid(False)
        header = self.tbl_filme.horizontalHeader()
        # header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        # header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)

        # self.tbl_filme.setColumnWidth(0, 30)        # Summe 1000        
        self.tbl_filme.setColumnWidth(0, 600)       # FilmName
        self.tbl_filme.setColumnWidth(1, 100)       # Größe
        self.tbl_filme.setColumnWidth(2, 75)        # FingerPrint
        self.tbl_filme.setColumnWidth(3, 75)        # MD5
        self.tbl_filme.setColumnWidth(4, 50)        # Status

        self.tbl_filme.currentCellChanged.connect(self.filmLangNameAnzeigen)


    def quelleSuchen(self):
        global QuellPfad

        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setViewMode(QFileDialog.ViewMode.Detail)
        dialog.setOption(QFileDialog.Option.ShowDirsOnly)
        dir = QFileDialog.getExistingDirectory(
            self,
            "Einen QuellOrdner suchen", 
            "E:\\Filme\\"
        )
        if dir:
            path = str(Path(dir))
            self.le_quellOrdner.setText(path)
            QuellPfad = path
            self.ladeFilme(QuellPfad)


    def ladeZielOrdner(self):
        global ZielPfad
        # bestimmt die ZielOrdner der Operation
        # das sind alle Ordner des Ziels, die mit "_in" beginnen
        ordner = []
        for root, dirs, _ in os.walk(KONSTANTEN.default_Ziel):
            for d in dirs:
                if d.startswith(KONSTANTEN.ZielOrdnerAnfang):
                    ordner.append(os.path.join(KONSTANTEN.default_Ziel, d))
            break   # nur eine Ebene zählt
        self.cb_zielOrdner.addItems(ordner)
        Ziel = ordner[0]


    def zielOrdnerAnpassen(self):
        # setzt den ZielPfad und seine Id neu bei Wechsel der ComboBox
        # 
        global ZielPfad, zielPfadId
        # pZiel = PurePath(ZielPfad)
        # ordner = pZiel.name
        # print(f"Alter ZielPfad: {ordner} mit id {zielPfadId}")
        ordner = self.cb_zielOrdner.currentText()
        pZiel = PurePath(ordner)
        ordner = pZiel.name        
        zielPfadId = vidarchdb._get_pfad_id(ordner, neuAnlage=False, verbose=False)
        # print(f"Neuer ZielPfad: {ordner} mit id {zielPfadId}")


    def abbruch(self):
        global stopFlag

        if self.btn_start.isEnabled():   
            vidarchdb.dbClose()     
            self.close()
        else:
            stopFlag = True
    
    
    def ladeFilme(self, quellOrdner):
        '''
        lädt alle Filme aus dem QuellOrdner in die filmListe
        '''
        global filmListe
        filmListe = []        
        for root, _, files in os.walk(quellOrdner):
            for film in files:
                if film.lower().endswith(('.mpg', '.mkv', '.mp4')):
                    x = FilmEintrag(film)
                    filmListe.append(x)
            break   # nur eine Ebene zählt
    
        self.filmeAnzeigen()
        self.filmAnz = len(filmListe)
        self.filmPos = 0        
        self.fortschrittAnzeigen(0, setGesamt=True)
        return

    def filmLangNameAnzeigen(self): 
        global filmListe
        row = self.tbl_filme.currentRow()
        self.lbl_filmName.setText(filmListe[row].filmName)


    def filmeAnzeigen(self):
        # die Filme der filmListe im TabelView anzeigen
        global filmListe

        self.tbl_filme.clearContents()
        self.tbl_filme.setRowCount(0)
        nr = 0
        for filmObj in filmListe:
            self.tbl_filme.insertRow(nr)
            
            self.tbl_filme.setItem(nr, 0, QTableWidgetItem(filmObj.filmName))
            
            itm = QTableWidgetItem(QTableWidgetItem(filmObj.filmBytesAnz))
            itm.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tbl_filme.setItem(nr, 1, itm)
                        
            self.tbl_filme.setItem(nr, 2, QTableWidgetItem(filmObj.filmFP))
            self.tbl_filme.setItem(nr, 3, QTableWidgetItem(filmObj.filmMD5))
            
            itm = QTableWidgetItem(QTableWidgetItem(filmObj.filmStatus))
            itm.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tbl_filme.setItem(nr, 4, itm)

            # self.tbl_filme.setItem(nr, 4, QTableWidgetItem(filmObj.filmStatus))
            nr += 1
        
        self.filmAnz = nr
        self.pb_filmGesamt.setRange(0, nr)
        self.pb_filmDetail.setRange(0, 100)


    def fortschrittAnzeigen(self, detailPos, setGesamt=False):
        global filmListe
        
        self.pb_filmGesamt.setValue(self.filmPos)
        self.pb_filmDetail.setValue(detailPos)
        QApplication.processEvents()
        

    def start(self):
        '''
        Rahmenprogramm für die Kopier-Aktion
        ''' 
        global filmListe, stopFlag

        # zuerst fast alle Widgets abschalten
        self.le_quellOrdner.setEnabled(False)
        self.cb_zielOrdner.setEnabled(False)
        self.cb_verschiebeFilm.setEnabled(False)
        self.btn_start.setEnabled(False)

        # ggf. Vorbereitung für verschiebe Film
        if self.cb_verschiebeFilm:
            if not os.path.exists(KONSTANTEN.verschiebeOrdner):
                os.mkdir(KONSTANTEN.verschiebeOrdner)

        row = 0
        fobj : FilmEintrag
        for fobj in filmListe:
            if not fobj.filmStatus == "bereit":
                row += 1
                continue
            self.tbl_filme.selectRow(row)
            fobj.filmStatus = "in Arbeit..."
            self.tbl_filme.setItem(row, 4, QTableWidgetItem(fobj.filmStatus))
            self.tbl_filme.setFocus()
            self.tbl_filme.selectRow(row)
            itm = self.tbl_filme.item(row,0)
            self.tbl_filme.scrollToItem(itm)
            self.tbl_filme.setCurrentItem(itm)
            itm.setSelected(True)
            # self.filmLangNameAnzeigen()
            QApplication.processEvents()
            
            if stopFlag:
                fobj.filmStatus = "Abbruch"
                self.tbl_filme.setItem(row, 4, QTableWidgetItem(fobj.filmStatus))
                break
            self.filmPos = row + 1
            self.fortschrittAnzeigen(0)

            zName = os.path.join(ZielPfad, fobj.filmName)

            fp, md5, ret = self.do_the_copy(row)

            # print(f"{fp =}, {md5 =}, {ret =}")
            fobj.filmFP = fp
            fobj.filmMD5 = md5
            if ret:     # ein FehlerText ist enthalten
                # irgend ein Fehler ist passiert
                if os.path.exists(zName):
                    os.remove(zName)
                fobj.filmStatus = ret
                self.tbl_filme.setItem(row, 4, QTableWidgetItem(fobj.filmStatus))
                break
            else:
                # den Film in der DB hinterlegen . . .
                ret = vidarchdb.film_merken(zielPfadId, fobj.filmName, fobj.filmExt, fobj.filmMD5, verbose=False)
                # ggf fehler in der Anlage verarbeiten
                if ret.startswith("Err"):
                    if os.path.exists(zName):
                        os.remove(zName)
                    fobj.filmStatus = ret
                    self.tbl_filme.setItem(row, 4, QTableWidgetItem(fobj.filmStatus))
                    break
                # end if ret.startswith   
                                 
                fobj.filmFP = fp
                fobj.filmMD5 = md5
                fobj.filmStatus = "OK"
                self.tbl_filme.setItem(row, 2, QTableWidgetItem(fobj.filmFP))
                self.tbl_filme.setItem(row, 3, QTableWidgetItem(fobj.filmMD5))
                self.tbl_filme.setItem(row, 4, QTableWidgetItem(fobj.filmStatus))

            self.tbl_filme.item(row,0).setSelected(False)
            row += 1
            
            QApplication.processEvents()
            
            # AbschlussArbeit: 
            if self.cb_verschiebeFilm:
                qname = fobj.fullName
                zname = os.path.join(KONSTANTEN.verschiebeOrdner, fobj.filmName)                
                # erst prüfen, ob die Laufwerke gelich sind...
                if PurePath(qname).drive.lower() == PurePath(zname).drive.lower():
                    if not os.path.exists(zname):
                        os.rename(qname, zname)
            if os.path.exists(qname):
                # alternativ die Quelle umbenennen
                os.rename(fobj.fullName, fobj.fullName + ".done")                

        # end for ...

        if stopFlag:
            stopFlag = False
        self.le_quellOrdner.setEnabled(True)
        self.cb_zielOrdner.setEnabled(True)
        self.cb_verschiebeFilm.setEnabled(True)
        self.btn_start.setEnabled(True)
        self.filmeAnzeigen()
        self.fortschrittAnzeigen(0) 
        return

    
    def do_the_copy(self, filmNr):
        '''
        führt die eigentliche Kopieroperation für eine Datei durch
        Parameter:
            die laufende Nr des Films in der filmListe
        Returns:
            3 Par4ameter:
                - FP:   den Fingerprint der ersten 64 KB
                - MD5:  die MD5 Wert des gesamten Films
                - RetVal:   "" oder der ErrorText   ("" heißt: OK)
        '''
        global filmListe, QuellPfad, Ziel
        
        fobj: FilmEintrag
        fobj = filmListe[filmNr]

        chunkSize1 = 64*1024
        chunkSize2 = 1*1024*1024
        qlen = 0
        qName = os.path.join(QuellPfad, fobj.filmName)
        zName = os.path.join(ZielPfad, fobj.filmName)
        copy_file = True
        fp = ""
        md5 = ""

        # Prüfung, ob quelle existiert
        if os.path.exists(qName):
            qlen = os.path.getsize(qName)
        else:
            fobj.filmStatus = "Fehler - Quelle fehlt"
            self.tbl_filme.setItem(filmNr, 4, QTableWidgetItem(fobj.filmStatus))
            return (None, None, "Fehler - Quelle fehlt")

        # Prüfung, ob ziel existiert
        if os.path.exists(zName):
            if vidarchdb.filmIstInDerDB(zielPfadId, fobj.filmName):
                # Film ist schon da, Größe prüfen
                zlen = os.path.getsize(zName)
                if qlen == zlen:
                    fobj.filmStatus = "OK - Ziel da"
                    copy_file = False
                    self.fortschrittAnzeigen(100)
                    copiedLen = qlen
                else:
                    fobj.filmStatus = "Fehler - Ziel exist."                    
                    self.tbl_filme.setItem(filmNr, 4, QTableWidgetItem(fobj.filmStatus))    
                    return (None, None, "Fehler - Ziel exist.")
            else:   # film ist noch nicht in der DB; das Ziel wird überschrieben
                pass
            # print(f"Quelle: {qName}")
            # print(f"Ziel: {zName}")
        else:   # vorsorglich anlegen / reservieren / bzw. überschreiben
            f = open(zName, "wb")
            f.close()
        
        anfang = True
        if copy_file:
            with open(qName, "rb") as q, open(zName,"wb") as z:
                file_hash = hashlib.md5()            
                fp_hash = hashlib.md5()            
                copiedLen = 0
                chunkSize = chunkSize1
                while chunk := q.read(chunkSize):
                    copiedLen += len(chunk)
                    if anfang:
                        fp_hash.update(chunk)
                        chunkSize = chunkSize2
                        anfang = False
                    else:
                        file_hash.update(chunk)
                    z.write(chunk)

                    self.fortschrittAnzeigen(int(copiedLen/qlen*100))
                    
                    # ggf. auf Abbruch prüfen...
                    if stopFlag:
                        reply = QMessageBox.question(self, "Wirklich?",
                                            f"Den aktuellen Kopier-Vorgang von\n [{fobj.filmName}]\n abbrechen?",
                                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
                        if reply == QMessageBox.StandardButton.Yes.value:
                            # die Schleife beenden
                                fobj.filmStatus = "gestoppt"
                                return (None, None, "gestoppt")
                # end while chunk...            
            # end with open           
            fp  = str(fp_hash.hexdigest())
            md5 = str(file_hash.hexdigest())
        # end if copy_file

        # vergleich der kopierten mit der gespeicherten Länge
        if copiedLen == qlen:
            # print("OK! Kopierte Länge und QuellDateiLänge sind identisch!")
            return (fp, md5, "")
        else:
            fobj.filmStatus = "Dateilänge falsch"
            return (None, None, "Dateilänge falsch")



StyleSheet = '''
    QMainWindow {
        background-color: SlateGray;
    }
    QPushButton {
        background-color: lightGrey;
        border-style: outset;
        border-width: 1px;
        border-radius: 5px;
        border-color: blue;        
        padding: 3px;
        color: darkBlue;        
    }

    QPushButton:disabled {
        color: lightGray;
    }
    QPushButton:disabled:checked {
        background-color: #ffaaaa;
    }
    QPushButton:disabled:!checked {
        background-color: dimGray;
    }

    #btn_quelleSuchen {
        border-width: 1px;
        border-radius: 5px;
        border-color: black;        
        background-color: lightGrey;
        color: darkBlue;
    }
    
    QLineEdit {
        border-width: 1px;
        border-radius: 5px;
        border-color: black;        
        background-color: lightGrey;
        color: darkBlue;
    }
    
    #lbl_filmName {
        border-width: 1px;
        border-radius: 5px;
        border-color: darkBlue;
        background-color: lightSlateGray;
        color: darkBlue;
    }

    #lbl_filmeKopieren {
        border-style: outset;
        border-width: 1px;
        border-radius: 5px;
        border-color: darkBlue;
        background-color: lightSlateGray;
        color: darkBlue;
    }

    QComboBox {
        border-width: 1px;
        border-radius: 5px;
        border-color: black;        
        background-color: lightGrey;
        color: darkBlue;
    }

    QCheckBox {
        border-width: 1px;
        border-radius: 5px;
        border-color: black;        
        background-color: slateGrey;
        color: darkBlue;
    }


    QTableWidget {  
        background-color: Beige;
        alternate-background-color: lightGrey;
        border-width: 1px;
        border-radius: 5px;
        border-color: blue;
        color: darkBlue;
        selection-background-color: Peru;
    }
    
    QHeaderView::Section {
        background-color: LightSlateGray;
    }

    QTableCornerButton::section {     
        border-width: 1px;     
        border-color: lightSlateGray;     
        border-style: solid; 
        background-color: LightSlateGray;
    } 

    QProgressBar {
        border: 1px solid darkBlue;
        border-radius: 5px;
        background-color: lightGray;
        text-align: center;
    }
    QProgressBar::chunk {
        background-color: Peru;
        width: 8px; 
        margin: 0.5px;
    }
'''

if __name__ == "__main__":
    app = QApplication([])
    app.setStyleSheet(StyleSheet)
    frm_main = Frm_Kopieren()
    frm_main.show()
    app.exec()



# -*- coding: utf-8 -*-
"""
Created on 2020-02-14

@author: rg

FilmDetails.py mit pyqt5

Gibt die technischen eines Films in einem Fenster an
technische Basis: c:\ffmpeg\bin\ffprobe.exe

"""
from PyQt5.QtWidgets import (QMainWindow, 
                             QDialog,
                             QLabel, 
                             QLineEdit, 
                             QPushButton,
                             QFileDialog,
                             QWidget,
                             QApplication,
                             QMessageBox)
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtCore import Qt

import sys
import os
import subprocess

# Hauptfenster; mit pyuic aus der UI-Datei konvertiert
import FilmDetailsUI as FilmDetailsUI
# import FilmDetailsUI as FilmDetailsUI

# einige statische Konstanten
class Konstanten():
    ffprobe = r'c:\ffmpeg\bin\ffprobe.exe'
    icon = 'FilmDetails.ico'

fname = None        # Name des zu begutachtenden Films

class mainApp(QDialog, FilmDetailsUI.Ui_FilmDetailsDialog):  # QMainWindow
    def __init__(self, fname):               
        super(self.__class__, self).__init__()
        
        self.setupUi(self)  # This is defined in ...UI.py file automatically
                            # It sets up layout and widgets that are defined
        # Instanz-Variablen
        self.fname = fname
        # Icon versorgen
        scriptDir = os.path.dirname(os.path.realpath(__file__))
        self.setWindowIcon(QIcon(scriptDir + os.path.sep + Konstanten.icon))

        # Feintuning der Widgets
        if self.fname is None:
            self.fname = self.openFileNameDialog()
        # gibt es diesen Film tatsächlich?
        if self.fname is None:            
            self.teFilmDetails.setTextColor(QColor('red'))
            self.teFilmDetails.setPlainText('Fatal!\nDiesem Programm muss der Name mit Pfad zu einer Filmdatei übergeben werden!')
        else:
            self.leFilmName.setText(self.fname) 
            if os.path.isfile(self.fname):
                self.teFilmDetails.setTextColor(QColor('lightyellow'))
                x = getFilmDetails(self.fname)
                # self.mess(x)
                self.teFilmDetails.setPlainText(x)
            else:
                self.teFilmDetails.setTextColor(QColor('red'))
                self.teFilmDetails.setPlainText(f'Fatal!\nKonnte den Film \n({self.fname})\n nicht finden!')

        # connects
        self.pbDone.clicked.connect(self.progende)
        # self.leName.installEventFilter(self)
        self.pbDone.setFocus()

    def openFileNameDialog(self)->str:
        options = QFileDialog.Options()
        # options |= QFileDialog.DontUseNativeDialog
        # fileName, _ = QFileDialog.getOpenFileName(self, "einen Film aussuchen", os.getcwd(), "All Files (*);;Filme (*.mkv *.mpg *.mp4 *.ts *.avi)", options=options)
        fileName, _ = QFileDialog.getOpenFileName(self, "einen Film aussuchen", "E:\\Filme\\", "All Files (*);;Filme (*.mkv *.mpg *.mp4 *.ts *.avi)", options=options)
        if fileName:
            return fileName
        else:
            return None

    def mess(self, txt):
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Information)
        msgBox.setText(txt)
        msgBox.setWindowTitle("Film Details")
        msgBox.setStandardButtons(QMessageBox.Ok)
        msgBox.exec()
        
    # Slots
    def keyPressEvent(self, event):
        # w = self.focusWidget()
        if event.key() == Qt.Key_Escape or event.key == Qt.Key_Enter or event.key == Qt.Key_Return:            
            self.progende()
        
    # def eventFilter(self, source, event):
    #     if (event.type() == QEvent.FocusOut an
    #         source is self.leName):
    #         # print('eventFilter: focus out')
    #         if self.grpLaden(self.leName.text()) > 0:
    #             self.leName.setFocus()
    #             return True
    #     return super(QMainWindow, self).eventFilter(source, event)

    # Funktionen
    def progende(self):     # Ende Proc mit Nachfrage
        self.close()
   
    def Hinweis(self, nachricht ):        
        self.statusbar.showMessage(nachricht)        

def _runit(cmd):
    try:
        pobj = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, encoding="utf-8")
    except:
        print("Unbekannter Fehler beim run-Aufruf!")
        print("Unexpected error:{0}".format(sys.exc_info()[0]))

    return pobj

def getFilmDetails(filmname):
    cmd = r'C:\ffmpeg\\bin\ffprobe -hide_banner ' + '"' + filmname + '"'
    pobj = _runit(cmd)
    ausg = pobj.stderr
    if pobj.returncode > 0:
        ausg = f'Fehler {pobj.returncode}\n' + ausg
    ausg = FilmInfosLesen(ausg)
    return ausg

def FilmInfosLesen(txt: str) -> str: 
    # liest die Ausgabe von ffprobe ein und gibt einen kurzen Abstrakt daraus aus
    # rg 2021-01-09
    ausgabe = ""    #txt + "\n\n"
    l_txt = txt.split("\n")
    # lastStream = ""
    duration = None
    for zle in l_txt:
        zle = zle.strip()
        if duration is None:
            if zle.startswith("Duration:"):
                ausgabe = ausgabe + "\n" + zle + "\n"
                duration = True
        else:
            if zle.startswith("Stream"):    # nur weitere Stream Zeilen einlesen
                l1 = zle.split(",")
                l2 = l1[0].split(": ")
                l0 = l2[0].split(" ")
                if l2[1].strip() == "Video":
                    # Video stream beschreiben
                    vcodec = l2[2].split(" ")
                    ausgabe = ausgabe + "\nVideo\n" + " "*6 + l0[1] + " " + vcodec[0] + " " + vcodec[1] + l1[1] + ", " + l1[2] + ", " + l1[3] + "\n\n"
                elif l2[1].strip() == "Audio":
                    # Audio stream beschreiben
                    p = l2[0].find("(")
                    if p > 0:
                        p_lang = l2[0][p+1 : p+4]
                    else:
                        p_lang = "???"
                    acodec = l2[2].split(" ")                                   #  " (" + p_lang + ")  " +
                    if len(l1) > 4:
                        ausgabe = ausgabe + "\nAudio\n" + " "*6 + l0[1] + " " + acodec[0] + " " + ", " + l1[1] + ", " + l1[2] + ", " + l1[4] + "\n"
                    else:
                        ausgabe = ausgabe + "\nAudio\n" + " "*6 + l0[1] + " " + acodec[0] + " " + ", " + l1[1] + ", " + l1[2]  + "\n"
                elif l2[1].strip() == "Subtitle":
                    ausgabe = ausgabe + "\nSubtitle\n" + " "*6 + l2[2] + "\n"
                elif l2[1].strip() == "Data":
                    ausgabe = ausgabe + "\nData\n" + " "*6 + l2[2] + "\n"
                else:
                    ausgabe = ausgabe + zle + "\n"
                
                # if zle.find("Video"):
                #     if lastStream == "Video":
                #         ausgabe = ausgabe + zle + "\n"
                #     else:
                #         ausgabe = ausgabe + "\n" + zle + "\n"
                #     lastStream = "Video"
                # elif zle.find("Audio"):
                #     if lastStream == "Audio":
                #         ausgabe = ausgabe + zle + "\n"
                #     else:
                #         ausgabe = ausgabe + "\n" + zle + "\n"
                #     lastStream = "Audio"
                # elif zle.find("Subtitle"):
                #     if lastStream == "Subtitle":
                #         ausgabe = ausgabe + zle + "\n"
                #     else:
                #         ausgabe = ausgabe + "\n" + zle + "\n"
                #     lastStream = "Subtitle"                    
    return ausgabe

# nötig, um als subdialog laufen zu können
def DlgMain(fname):
    dialog = mainApp(fname)    
    dialog.show()           
    dialog.exec_()


def main(fname):        
    app = QApplication(sys.argv)  # A new instance of QApplication
    form = mainApp(fname)              # We set the form to be our App (design)
    form.show()                   # Show the form
    app.exec_()                   # and execute the app


if __name__ == '__main__':        # if we're running file directly and not importing it
    if len(sys.argv) == 2:        
        fname = sys.argv[1]       
    else:
        fname = None
    main(fname)                        # run the main function
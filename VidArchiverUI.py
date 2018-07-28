# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'VidArchiverUI.ui'
#
# Created by: PyQt5 UI code generator 5.11.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1363, 767)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("VidArchiver.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        MainWindow.setWindowIcon(icon)
        MainWindow.setStyleSheet("")
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setStyleSheet("QLabel: {\n"
"    font: 75 10pt \"MS Shell Dlg 2\";\n"
"    background-color: rgb(208, 199, 255);\n"
"};\n"
"")
        self.centralwidget.setObjectName("centralwidget")
        self.formLayoutWidget = QtWidgets.QWidget(self.centralwidget)
        self.formLayoutWidget.setGeometry(QtCore.QRect(10, 0, 511, 61))
        self.formLayoutWidget.setObjectName("formLayoutWidget")
        self.formLayout_4 = QtWidgets.QFormLayout(self.formLayoutWidget)
        self.formLayout_4.setContentsMargins(0, 0, 0, 0)
        self.formLayout_4.setObjectName("formLayout_4")
        self.lbl_vidArchPfad = QtWidgets.QLabel(self.formLayoutWidget)
        self.lbl_vidArchPfad.setObjectName("lbl_vidArchPfad")
        self.formLayout_4.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.lbl_vidArchPfad)
        self.le_vidArchPfad = QtWidgets.QLineEdit(self.formLayoutWidget)
        self.le_vidArchPfad.setObjectName("le_vidArchPfad")
        self.formLayout_4.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.le_vidArchPfad)
        self.lbl_quelle = QtWidgets.QLabel(self.formLayoutWidget)
        self.lbl_quelle.setObjectName("lbl_quelle")
        self.formLayout_4.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.lbl_quelle)
        self.cb_quelle = QtWidgets.QComboBox(self.formLayoutWidget)
        self.cb_quelle.setObjectName("cb_quelle")
        self.formLayout_4.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.cb_quelle)
        self.horizontalLayoutWidget = QtWidgets.QWidget(self.centralwidget)
        self.horizontalLayoutWidget.setGeometry(QtCore.QRect(10, 80, 1351, 591))
        self.horizontalLayoutWidget.setObjectName("horizontalLayoutWidget")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.horizontalLayoutWidget)
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.lbl_filmeQuelle = QtWidgets.QLabel(self.horizontalLayoutWidget)
        self.lbl_filmeQuelle.setStyleSheet("font: 75 10pt \"MS Shell Dlg 2\";\n"
"background-color: rgb(184, 191, 255);")
        self.lbl_filmeQuelle.setAlignment(QtCore.Qt.AlignCenter)
        self.lbl_filmeQuelle.setObjectName("lbl_filmeQuelle")
        self.verticalLayout_2.addWidget(self.lbl_filmeQuelle)
        self.tbl_film = QtWidgets.QTableWidget(self.horizontalLayoutWidget)
        self.tbl_film.setMaximumSize(QtCore.QSize(505, 16777215))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.tbl_film.setFont(font)
        self.tbl_film.setStyleSheet("background-color: rgb(255, 255, 203);\n"
"alternate-background-color: rgb(170, 255, 127);")
        self.tbl_film.setEditTriggers(QtWidgets.QAbstractItemView.DoubleClicked|QtWidgets.QAbstractItemView.EditKeyPressed)
        self.tbl_film.setAlternatingRowColors(True)
        self.tbl_film.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.tbl_film.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.tbl_film.setRowCount(3)
        self.tbl_film.setObjectName("tbl_film")
        self.tbl_film.setColumnCount(3)
        item = QtWidgets.QTableWidgetItem()
        self.tbl_film.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.tbl_film.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.tbl_film.setHorizontalHeaderItem(2, item)
        self.tbl_film.verticalHeader().setDefaultSectionSize(50)
        self.verticalLayout_2.addWidget(self.tbl_film)
        self.horizontalLayout_2.addLayout(self.verticalLayout_2)
        self.verticalLayout_3 = QtWidgets.QVBoxLayout()
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.lbl_filmOrdner = QtWidgets.QLabel(self.horizontalLayoutWidget)
        self.lbl_filmOrdner.setStyleSheet("font: 75 10pt \"MS Shell Dlg 2\";\n"
"background-color: rgb(184, 191, 255);")
        self.lbl_filmOrdner.setAlignment(QtCore.Qt.AlignCenter)
        self.lbl_filmOrdner.setObjectName("lbl_filmOrdner")
        self.verticalLayout_3.addWidget(self.lbl_filmOrdner)
        self.lst_vidPfad = QtWidgets.QListWidget(self.horizontalLayoutWidget)
        font = QtGui.QFont()
        font.setPointSize(11)
        self.lst_vidPfad.setFont(font)
        self.lst_vidPfad.setStyleSheet("background-color: rgb(115, 170, 170);")
        self.lst_vidPfad.setObjectName("lst_vidPfad")
        self.verticalLayout_3.addWidget(self.lst_vidPfad)
        self.horizontalLayout_2.addLayout(self.verticalLayout_3)
        self.verticalLayout_9 = QtWidgets.QVBoxLayout()
        self.verticalLayout_9.setObjectName("verticalLayout_9")
        self.label = QtWidgets.QLabel(self.horizontalLayoutWidget)
        self.label.setStyleSheet("font: 75 10pt \"MS Shell Dlg 2\";\n"
"background-color: rgb(184, 191, 255);\n"
"")
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setObjectName("label")
        self.verticalLayout_9.addWidget(self.label, 0, QtCore.Qt.AlignTop)
        self.tbl_vorhFilm = QtWidgets.QTableWidget(self.horizontalLayoutWidget)
        self.tbl_vorhFilm.setMinimumSize(QtCore.QSize(300, 0))
        font = QtGui.QFont()
        font.setPointSize(11)
        self.tbl_vorhFilm.setFont(font)
        self.tbl_vorhFilm.setStyleSheet("background-color: rgb(154, 255, 152);\n"
"alternate-background-color: rgb(255, 226, 176);")
        self.tbl_vorhFilm.setEditTriggers(QtWidgets.QAbstractItemView.DoubleClicked)
        self.tbl_vorhFilm.setAlternatingRowColors(True)
        self.tbl_vorhFilm.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.tbl_vorhFilm.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.tbl_vorhFilm.setRowCount(5)
        self.tbl_vorhFilm.setObjectName("tbl_vorhFilm")
        self.tbl_vorhFilm.setColumnCount(1)
        item = QtWidgets.QTableWidgetItem()
        self.tbl_vorhFilm.setHorizontalHeaderItem(0, item)
        self.tbl_vorhFilm.verticalHeader().setDefaultSectionSize(25)
        self.verticalLayout_9.addWidget(self.tbl_vorhFilm)
        self.groupBox_2 = QtWidgets.QGroupBox(self.horizontalLayoutWidget)
        self.groupBox_2.setMinimumSize(QtCore.QSize(0, 50))
        self.groupBox_2.setStyleSheet("background-color: rgb(200, 200, 200);")
        self.groupBox_2.setObjectName("groupBox_2")
        self.btn_del = QtWidgets.QPushButton(self.groupBox_2)
        self.btn_del.setGeometry(QtCore.QRect(11, 21, 130, 23))
        self.btn_del.setMinimumSize(QtCore.QSize(130, 0))
        self.btn_del.setObjectName("btn_del")
        self.btn_rename = QtWidgets.QPushButton(self.groupBox_2)
        self.btn_rename.setGeometry(QtCore.QRect(150, 20, 130, 23))
        self.btn_rename.setObjectName("btn_rename")
        self.btn_showArchVideo = QtWidgets.QPushButton(self.groupBox_2)
        self.btn_showArchVideo.setGeometry(QtCore.QRect(288, 21, 130, 23))
        self.btn_showArchVideo.setObjectName("btn_showArchVideo")
        self.verticalLayout_9.addWidget(self.groupBox_2)
        self.formLayout = QtWidgets.QFormLayout()
        self.formLayout.setObjectName("formLayout")
        self.label_3 = QtWidgets.QLabel(self.horizontalLayoutWidget)
        self.label_3.setObjectName("label_3")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label_3)
        self.le_ArchivFilm = QtWidgets.QLineEdit(self.horizontalLayoutWidget)
        self.le_ArchivFilm.setObjectName("le_ArchivFilm")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.le_ArchivFilm)
        self.label_4 = QtWidgets.QLabel(self.horizontalLayoutWidget)
        self.label_4.setObjectName("label_4")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.label_4)
        self.le_ArchivFilmGr = QtWidgets.QLineEdit(self.horizontalLayoutWidget)
        self.le_ArchivFilmGr.setObjectName("le_ArchivFilmGr")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.le_ArchivFilmGr)
        self.label_5 = QtWidgets.QLabel(self.horizontalLayoutWidget)
        self.label_5.setObjectName("label_5")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.label_5)
        self.le_ArchivFilmDat = QtWidgets.QLineEdit(self.horizontalLayoutWidget)
        self.le_ArchivFilmDat.setObjectName("le_ArchivFilmDat")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.le_ArchivFilmDat)
        self.verticalLayout_9.addLayout(self.formLayout)
        self.horizontalLayout_2.addLayout(self.verticalLayout_9)
        self.horizontalGroupBox_2 = QtWidgets.QGroupBox(self.centralwidget)
        self.horizontalGroupBox_2.setGeometry(QtCore.QRect(10, 680, 1341, 41))
        self.horizontalGroupBox_2.setObjectName("horizontalGroupBox_2")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout(self.horizontalGroupBox_2)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.btn_playVideo = QtWidgets.QPushButton(self.horizontalGroupBox_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btn_playVideo.sizePolicy().hasHeightForWidth())
        self.btn_playVideo.setSizePolicy(sizePolicy)
        self.btn_playVideo.setDefault(True)
        self.btn_playVideo.setObjectName("btn_playVideo")
        self.horizontalLayout_3.addWidget(self.btn_playVideo)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem)
        self.btn_linkVideo = QtWidgets.QPushButton(self.horizontalGroupBox_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btn_linkVideo.sizePolicy().hasHeightForWidth())
        self.btn_linkVideo.setSizePolicy(sizePolicy)
        self.btn_linkVideo.setObjectName("btn_linkVideo")
        self.horizontalLayout_3.addWidget(self.btn_linkVideo)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem1)
        self.btn_pfadNeu = QtWidgets.QPushButton(self.horizontalGroupBox_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btn_pfadNeu.sizePolicy().hasHeightForWidth())
        self.btn_pfadNeu.setSizePolicy(sizePolicy)
        self.btn_pfadNeu.setMinimumSize(QtCore.QSize(200, 0))
        self.btn_pfadNeu.setObjectName("btn_pfadNeu")
        self.horizontalLayout_3.addWidget(self.btn_pfadNeu)
        spacerItem2 = QtWidgets.QSpacerItem(500, 20, QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem2)
        self.btn_ende = QtWidgets.QPushButton(self.horizontalGroupBox_2)
        self.btn_ende.setObjectName("btn_ende")
        self.horizontalLayout_3.addWidget(self.btn_ende)
        self.label_2 = QtWidgets.QLabel(self.centralwidget)
        self.label_2.setGeometry(QtCore.QRect(950, 0, 261, 41))
        self.label_2.setStyleSheet("font: 87 24pt \"Arial Black\";")
        self.label_2.setObjectName("label_2")
        self.lbl_version = QtWidgets.QLabel(self.centralwidget)
        self.lbl_version.setGeometry(QtCore.QRect(1210, 40, 81, 16))
        self.lbl_version.setObjectName("lbl_version")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1363, 21))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        self.btn_ende.clicked['bool'].connect(MainWindow.close)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "VideoArchiver"))
        self.lbl_vidArchPfad.setText(_translate("MainWindow", "Pfad zum Video-Archiv"))
        self.lbl_quelle.setText(_translate("MainWindow", "Quelle (Prep-Ordner)"))
        self.lbl_filmeQuelle.setText(_translate("MainWindow", "Filme in der Quelle"))
        item = self.tbl_film.horizontalHeaderItem(0)
        item.setText(_translate("MainWindow", "Film"))
        item = self.tbl_film.horizontalHeaderItem(1)
        item.setText(_translate("MainWindow", "Größe"))
        item = self.tbl_film.horizontalHeaderItem(2)
        item.setText(_translate("MainWindow", "Datum"))
        self.lbl_filmOrdner.setText(_translate("MainWindow", "Verfügbare Archiv-Ordner"))
        self.label.setText(_translate("MainWindow", "Filme im Archiv-Ordner"))
        item = self.tbl_vorhFilm.horizontalHeaderItem(0)
        item.setText(_translate("MainWindow", "Film"))
        self.groupBox_2.setTitle(_translate("MainWindow", "Video im Archiv ..."))
        self.btn_del.setText(_translate("MainWindow", "&löschen"))
        self.btn_rename.setText(_translate("MainWindow", "&umbenennen"))
        self.btn_showArchVideo.setText(_translate("MainWindow", "&zeigen"))
        self.label_3.setText(_translate("MainWindow", "Film"))
        self.label_4.setText(_translate("MainWindow", "Größe"))
        self.label_5.setText(_translate("MainWindow", "Datum"))
        self.btn_playVideo.setText(_translate("MainWindow", "Film ab&spielen"))
        self.btn_linkVideo.setText(_translate("MainWindow", "Video &in den  Pfad einsortieren (F5)"))
        self.btn_pfadNeu.setText(_translate("MainWindow", "neuer Unterordner"))
        self.btn_ende.setText(_translate("MainWindow", "Ende"))
        self.label_2.setText(_translate("MainWindow", "Video-Archiver"))
        self.lbl_version.setText(_translate("MainWindow", "V0.2 rg 06.2018"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())


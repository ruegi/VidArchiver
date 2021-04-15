# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'FilmDetailsUI.ui'
#
# Created by: PyQt5 UI code generator 5.13.2
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_FilmDetailsDialog(object):
    def setupUi(self, FilmDetailsDialog):
        FilmDetailsDialog.setObjectName("FilmDetailsDialog")
        FilmDetailsDialog.resize(920, 697)
        self.teFilmDetails = QtWidgets.QTextEdit(FilmDetailsDialog)
        self.teFilmDetails.setEnabled(False)
        self.teFilmDetails.setGeometry(QtCore.QRect(30, 40, 871, 621))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.teFilmDetails.sizePolicy().hasHeightForWidth())
        self.teFilmDetails.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.teFilmDetails.setFont(font)
        self.teFilmDetails.setStyleSheet("background-color: rgb(60, 60, 60);\n"
"color: green;\n"
"\n"
"")
        self.teFilmDetails.setFrameShape(QtWidgets.QFrame.WinPanel)
        self.teFilmDetails.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.teFilmDetails.setObjectName("teFilmDetails")
        self.leFilmName = QtWidgets.QLineEdit(FilmDetailsDialog)
        self.leFilmName.setEnabled(False)
        self.leFilmName.setGeometry(QtCore.QRect(30, 10, 871, 20))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.leFilmName.setFont(font)
        self.leFilmName.setObjectName("leFilmName")
        self.pbDone = QtWidgets.QPushButton(FilmDetailsDialog)
        self.pbDone.setGeometry(QtCore.QRect(390, 662, 111, 31))
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setItalic(False)
        font.setUnderline(False)
        font.setWeight(75)
        font.setStrikeOut(False)
        font.setKerning(True)
        self.pbDone.setFont(font)
        self.pbDone.setCheckable(False)
        self.pbDone.setDefault(True)
        self.pbDone.setFlat(False)
        self.pbDone.setObjectName("pbDone")

        self.retranslateUi(FilmDetailsDialog)
        QtCore.QMetaObject.connectSlotsByName(FilmDetailsDialog)

    def retranslateUi(self, FilmDetailsDialog):
        _translate = QtCore.QCoreApplication.translate
        FilmDetailsDialog.setWindowTitle(_translate("FilmDetailsDialog", "FilmDetails nach ffprobe"))
        self.pbDone.setText(_translate("FilmDetailsDialog", "Fertig"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    FilmDetailsDialog = QtWidgets.QDialog()
    ui = Ui_FilmDetailsDialog()
    ui.setupUi(FilmDetailsDialog)
    FilmDetailsDialog.show()
    sys.exit(app.exec_())

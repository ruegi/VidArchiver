# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'VidArchiverRenDialogUI.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets
# from PyQt5.QtCore import PyQtSlot

class Ui_Dialog(object):		# gändert
    def __init__(self, alterName):
        self.alterName = alterName
        super(Ui_Dialog, self).__init__()

    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(657, 174)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("VidArchiver.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        Dialog.setWindowIcon(icon)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setGeometry(QtCore.QRect(50, 120, 571, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.groupBox = QtWidgets.QGroupBox(Dialog)
        self.groupBox.setGeometry(QtCore.QRect(40, 60, 581, 51))
        self.groupBox.setObjectName("groupBox")
        self.le_rename = QtWidgets.QLineEdit(self.groupBox)
        self.le_rename.setGeometry(QtCore.QRect(10, 20, 561, 20))
        self.le_rename.setObjectName("le_rename")
        self.le_rename.setText(self.alterName)

        # bindings
        # connect the two functions

        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)
        Dialog.accepted.connect(lambda: self.return_accept())
        Dialog.rejected.connect(lambda: self.return_cancel())
        # QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Umbenennen eines Videos aus dem Archiv"))
        self.groupBox.setTitle(_translate("Dialog", "Bitte einen neuen Namen eingeben:"))

    @QtCore.pyqtSlot()
    def return_accept(self):
        print("yes")

    @QtCore.pyqtSlot()
    def return_cancel(self):
        print("no")

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Dialog = QtWidgets.QDialog()
    ui = Ui_Dialog("alter Name des Videos")
    ui.setupUi(Dialog)
    Dialog.show()
    sys.exit(app.exec_())

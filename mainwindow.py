
import sys
from PyQt5.uic import loadUi
from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QApplication, QDialog
import resource_rc
# from model import Model
from out_window import Ui_OutputDialog


class Ui_Dialog(QDialog):
    def __init__(self):
        super(Ui_Dialog, self).__init__()
        loadUi("mainwindow.ui", self)       #Se carga la interfaz principal

        self.runButton.clicked.connect(self.runSlot)

        self._new_window = None
        self.Videocapture_ = None

    def refreshAll(self):
        print("La persona que llama detecta el número de cámara (0 es la cámara integrada del portátil, 1 es la cámara externa USB）：")
        self.Videocapture_ = "0"

    @pyqtSlot()
    def runSlot(self):
        print("El sistema de registro de reconocimiento facial INFRAVENZ se está ejecutando...")
        self.refreshAll()
        print(self.Videocapture_)
        ui.hide()  # Ocultar interfaz de usuario
        self.outputWindow_()  # crear nuevo formulario

    def outputWindow_(self):
        """
       Cree un formulario para el área de reconocimiento facial en la GUI
        """
        self._new_window = Ui_OutputDialog()
        self._new_window.show()
        self._new_window.startVideo(self.Videocapture_)
        print("La función de reconocimiento facial se está inicializando....")
        print("La función de reconocimiento facial se inicializa！")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = Ui_Dialog()
    ui.show()
    sys.exit(app.exec_())

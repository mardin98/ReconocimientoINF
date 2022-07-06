
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.uic import loadUi
from PyQt5.QtCore import pyqtSlot, QTimer, QDate, Qt
from PyQt5.QtWidgets import QDialog,QMessageBox
import cv2
import face_recognition
import numpy as np
import datetime
import os
import csv
import pymysql

class Ui_OutputDialog(QDialog):
    def __init__(self):
        super(Ui_OutputDialog, self).__init__()
        loadUi("./outputwindow.ui", self)   #Cargar interfaz de usuario del formulario de salida

        #datetime
        now = QDate.currentDate()
        current_date = now.toString('ddd dd MMMM yyyy') #Formato de tiempo
        current_time = datetime.datetime.now().strftime("%I:%M %p")
        self.Date_Label.setText(current_date)
        self.Time_Label.setText(current_time)

        self.image = None

    @pyqtSlot()
    def startVideo(self, camera_name):
        """
        :param camera_name: enlace a cámara web o cámara web usb
        :return:
        """
        if len(camera_name) == 1:
        	self.capture = cv2.VideoCapture(int(camera_name))
        else:
        	self.capture = cv2.VideoCapture(camera_name)
        self.timer = QTimer(self)  # crear
        path = 'Images'     #Lea la ruta de la imagen de reconocimiento facial-donde estan las imagenes del personal
        if not os.path.exists(path):
            os.mkdir(path)
        # Lista de códigos de rostros y nombres de rostros debajo de la ruta
        images = []
        self.class_names = []
        self.encode_list = []
        self.TimeList1 = []
        self.TimeList2 = []
        attendance_list = os.listdir(path)

        for cl in attendance_list:
            cur_img = cv2.imread(f'{path}/{cl}')
            images.append(cur_img)
            self.class_names.append(os.path.splitext(cl)[0])
        for img in images:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            boxes = face_recognition.face_locations(img)
            encodes_cur_frame = face_recognition.face_encodings(img, boxes)[0]
            self.encode_list.append(encodes_cur_frame)
        self.timer.timeout.connect(self.update_frame)  # salida de conexión de tiempo de espera
        self.timer.start(10)

    def face_rec_(self, frame, encode_list_known, class_names):
        """
        :param frame: captura de cámara
        :param encode_list_known: Código facial codificado
        :param class_names: El nombre de la cara registrada
        :return:
        """

        # tabla csv para guardar datos
        def mark_attendance(name):
            """
            :param name: parte de reconocimiento facial
            :return:
            """
            if self.ClockInButton.isChecked():
                self.ClockInButton.setEnabled(False)
                with open('Attendance.csv', 'a') as f:
                        if (name != 'Desconocido'):        #Valoración de entrada: si se ha reconocido el rostro
                            buttonReply = QMessageBox.question(self, 'Hola! ' + name, 'empezar a iniciar sesión',
                                                               QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                            if buttonReply == QMessageBox.Yes:

                                date_time_string = datetime.datetime.now().strftime("%y/%m/%d %H:%M:%S")
                                f.writelines(f'\n{name},{date_time_string},Ingreso')
                                con = pymysql.connect(db='datainf', user='root', passwd='', host='localhost', port=3306, autocommit=True)
                                cur = con.cursor()
                                sql = f"INSERT INTO registro(usuario, ingreso) VALUES('{name}', '{date_time_string}')"
                                cur.execute(sql)


                                self.ClockInButton.setChecked(False)

                                self.NameLabel.setText(name)
                                self.StatusLabel.setText('Ingreso')
                                self.HoursLabel.setText('Hora Actual')
                                self.MinLabel.setText('')

                                self.Time1 = datetime.datetime.now()
                                self.ClockInButton.setEnabled(True)
                            else:
                                print('La operación de inicio de sesión falló')
                                self.ClockInButton.setEnabled(True)
            elif self.ClockOutButton.isChecked():
                self.ClockOutButton.setEnabled(False)
                with open('Attendance.csv', 'a') as f:
                        if (name != 'Desconocido'):
                            buttonReply = QMessageBox.question(self, 'Hola' + name, '¿Confirmar para cerrar sesión?',
                                                              QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                            if buttonReply == QMessageBox.Yes:
                                date_time_string = datetime.datetime.now().strftime("%y/%m/%d %H:%M:%S")
                                f.writelines(f'\n{name},{date_time_string},Salio')
                                con = pymysql.connect(db='datainf', user='root', passwd='', host='localhost', port=3306, autocommit=True)
                                cur = con.cursor()
                                sql = f"INSERT INTO registro(salio ) VALUES('{name}', '{date_time_string}')"
                                cur.execute(sql)
                                self.ClockOutButton.setChecked(False)

                                self.NameLabel.setText(name)
                                self.StatusLabel.setText('Salio')
                                self.Time2 = datetime.datetime.now()

                                self.ElapseList(name)
                                self.TimeList2.append(datetime.datetime.now())
                                CheckInTime = self.TimeList1[-1]
                                CheckOutTime = self.TimeList2[-1]
                                self.ElapseHours = (CheckOutTime - CheckInTime)
                                self.MinLabel.setText("{:.0f}".format(abs(self.ElapseHours.total_seconds() / 60)%60) + 'm')
                                self.HoursLabel.setText("{:.0f}".format(abs(self.ElapseHours.total_seconds() / 60**2)) + 'h')
                                self.ClockOutButton.setEnabled(True)
                            else:
                                print('La operación de pago falló')
                                self.ClockOutButton.setEnabled(True)

        # parte de reconocimiento facial
        faces_cur_frame = face_recognition.face_locations(frame)
        encodes_cur_frame = face_recognition.face_encodings(frame, faces_cur_frame)

        for encodeFace, faceLoc in zip(encodes_cur_frame, faces_cur_frame):
            match = face_recognition.compare_faces(encode_list_known, encodeFace, tolerance=0.50)
            face_dis = face_recognition.face_distance(encode_list_known, encodeFace)
            name = "Desconocido"    #Unknown el reconocimiento facial es desconocido
            best_match_index = np.argmin(face_dis)
            if match[best_match_index]:
                name = class_names[best_match_index].upper()
                y1, x2, y2, x1 = faceLoc
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.rectangle(frame, (x1, y2 - 20), (x2, y2), (0, 255, 0), cv2.FILLED)
                cv2.putText(frame, name, (x1 + 6, y2 - 6), cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)
            mark_attendance(name)

        return frame

    def showdialog(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)

        msg.setText("insinuación")
        msg.setInformativeText("agregar mensaje")
        msg.setWindowTitle("notificación")
        msg.setDetailedText("El contenido es el siguiente:")
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)


    def ElapseList(self,name):
        with open('Attendance.csv', "r") as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 2

            Time1 = datetime.datetime.now()
            Time2 = datetime.datetime.now()
            for row in csv_reader:
                for field in row:
                    if field in row:
                        if field == 'Ingreso':
                            if row[0] == name:
                                Time1 = (datetime.datetime.strptime(row[1], '%y/%m/%d %H:%M:%S'))
                                self.TimeList1.append(Time1)
                        if field == 'Salio':
                            if row[0] == name:
                                Time2 = (datetime.datetime.strptime(row[1], '%y/%m/%d %H:%M:%S'))
                                self.TimeList2.append(Time2)

    def update_frame(self):
        ret, self.image = self.capture.read()
        self.displayImage(self.image, self.encode_list, self.class_names, 1)

    def displayImage(self, image, encode_list, class_names, window=1):
        """
        :param image: Imagen capturada de la cámara
        :param encode_list: Código de reconocimiento facial reconocido
        :param class_names: El nombre de la persona cuyo rostro ha sido reconocido.
        :param window: forma
        :return:
        """
        image = cv2.resize(image, (640, 480))  #Definir el tamaño del área de reconocimiento
        try:
            image = self.face_rec_(image, encode_list, class_names)
        except Exception as e:
            print(e)
        qformat = QImage.Format_Indexed8
        if len(image.shape) == 3:
            if image.shape[2] == 4:
                qformat = QImage.Format_RGBA8888
            else:
                qformat = QImage.Format_RGB888
        outImage = QImage(image, image.shape[1], image.shape[0], image.strides[0], qformat)
        outImage = outImage.rgbSwapped()

        if window == 1:
            self.imgLabel.setPixmap(QPixmap.fromImage(outImage))
            self.imgLabel.setScaledContents(True)

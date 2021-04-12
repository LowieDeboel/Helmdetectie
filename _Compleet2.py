# source: https://gist.github.com/docPhil99/ca4da12c9d6f29b9cea137b617c7b8b1
# documentatie: http://index-of.es/Python/Rapid.GUI.Programming.with.Python.and.Qt.Mark.Summerfield.2007.pdf

import sys
from time import time

import cv2
import numpy as np
from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread, QMutex
from PyQt5.QtGui import QPixmap, QCursor
from PyQt5.QtWidgets import QMessageBox, QWidget, QApplication, QLabel, QGridLayout, QPushButton, QRadioButton, QMenuBar, QMenu, QComboBox


class VideoThread(QThread):
   change_pixmap_signal = pyqtSignal(np.ndarray)

   def __init__(self, tiny, poort):
      super().__init__()
      self._run_flag = 1 # True
      self.t = tiny
      self.p = poort
      #print("detectie: ", self.t)

   def run(self): # capture from web cam
      cap = cv2.VideoCapture(self.p, cv2.CAP_DSHOW) # self.p = 0 of 1

      # TODO: kleur van 'hoed' veranderen naar dezelfde kleur als hoofd
      # constanten
      CONFIDENCE_THRESHOLD, NMS_THRESHOLD, COLORS = 0.2, 0.6, [(0, 255, 0), (255, 255, 0), (0, 0, 255)]  # BGR ipv RGB

      if self.t:  # parameters van yolov4-tiny toepassen
         shiftregister_length = 10
         shiftregister_threshold = 7
         max_counter = 100
         weightsPath, configPath = 'training1mrt/yolov4-tiny_training_best.weights', \
                                   'training1mrt/yolov4-tiny_testing.cfg'
      else:  # parameters van gewone yolov4 toepassen
         shiftregister_length = 7
         shiftregister_threshold = 5
         max_counter = 10
         weightsPath, configPath = 'training1mrt/yolov4_training_best.weights', \
                                   'training1mrt/yolov4_testing.cfg'
      class_names = ['helm', 'hoed', 'hoofd']
      net = cv2.dnn.readNet(weightsPath, configPath)
      model = cv2.dnn_DetectionModel(net)  # dnn = deep neural network
      model.setInputParams(size=(416, 416), scale=1 / 255)

      # initialisatie
      shiftregister = []
      wait_counter = 0
      openpoort = False

      while self._run_flag:
         ret, frame = cap.read()

         # fps van de detectie berekenen
         start = time()
         classes, scores, boxes = model.detect(frame, CONFIDENCE_THRESHOLD, NMS_THRESHOLD)
         end = time()

         helm = 1 # negatieve detectie initialiseren
         for (classid, score, box) in zip(classes, scores, boxes):
            color = COLORS[int(classid) % len(COLORS)]  # juiste kleur kiezen voor de bounding box
            label = '%s: %.2f' % (class_names[classid[0]], score)  # percentage van confidence
            cv2.rectangle(frame, box, color, 2)  # bounding box
            cv2.rectangle(frame, (box[0], box[1]), (box[0] + 100, box[1] + 15), color, cv2.FILLED)  # achtergrondkleur voor benaming
            cv2.putText(frame, label, (box[0] + 1, box[1] + 13), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)  # benaming van de bounding box

            helm = classid[0] # helm is index van gedecteerde object

         # 1 = positieve detectie, 0 = negatieve detectie
         decision = 1 if class_names[helm] == "helm" else 0

         # shiftregister beslissingsstructuur
         if openpoort == False: # poort is gesloten en blijven detecteren
            lampkleur = (0, 0, 255) # rood (BGR)
            shiftregister.append(decision) # shifregister van 0'en en 1'en
            if len(shiftregister) > shiftregister_length:  # max lengte behouden
               shiftregister.pop(0)
            print(shiftregister)
         else: # poort is open en bepaalde tijd wachten
            lampkleur = (0, 255, 0) # groen (BGR)
            wait_counter += 1
            if wait_counter >= max_counter:  # 5sec poort geopend laten
               print("POORT SLUIT")
               # reset van alle waarden
               openpoort = False
               shiftregister = []
               wait_counter = 0

         if shiftregister.count(1) >= shiftregister_threshold and openpoort == False: # poort openen als er 7 of meer positieve detecties zijn
            print("OKEEE\nPOORT OPENT")
            openpoort = True

         # lampje label
         cv2.circle(frame, (590,50), 40, (0,0,0), cv2.FILLED) # zwarte rand
         cv2.circle(frame, (590,50), 33, (255,255,255), cv2.FILLED) # witte rand
         cv2.circle(frame, (590,50), 32, lampkleur, cv2.FILLED) # ingekleurd

         # fps label
         cv2.rectangle(frame, (0, 0), (100, 20), (0, 0, 0), cv2.FILLED)  # zwarte achtergrond aanmaken
         fps_label = 'FPS: %.2f' % (1 / (end - start))  # fps label aanmaken
         cv2.putText(frame, fps_label, (0, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)  # fps label plotten

         if ret:
            self.change_pixmap_signal.emit(frame)
      # shut down capture system
      cap.release()
      cv2.destroyAllWindows()

   def stop(self): # Sets run flag to False and waits for thread to finish
      self._run_flag = 0 # False
      self.wait()



# TODO: logo toevoegen, layout aanpassen, cursor actie veranderen
class App(QWidget):
   def __init__(self):
      super().__init__()
      self.setWindowTitle("Helm Detectie GUI")
      self.setGeometry(400, 150, 670, 640)  # positie van window
      self.display_width, self.display_height =  720, 650# 640, 480
      self.grid = QGridLayout()
      self.setLayout(self.grid)
      self.widgets = {"text_label": [],
                      "webcam": [],
                      "button": [],
                      "radio_button1": [],
                      "radio_button2": [],
                      "combobox": []}
      self.colour = "red"
      self.startframe()

   #https://stackoverflow.com/questions/4528347/clear-all-widgets-in-a-layout-in-pyqt
   def clear_widgets(self): # clear alle widgets als in window een nieuw frame wordt geopend
      for widget in self.widgets:
         if self.widgets[widget] != []:
            self.widgets[widget][-1].hide()
         for i in range(0, len(self.widgets[widget])):
            self.widgets[widget].pop()

   def startframe(self):
      self.clear_widgets()
      self.tiny = True
      self.poort = 0

      # create a text label
      self.text_label = QLabel("Klik op onderstaande knop om de webcam te openen.\n"
                               "Na enige tijd zal de webcam tevoorschijn komen.\n"
                               "Druk vervolgens terug op de knop om de webcam te sluiten.")
      self.text_label.setAlignment(QtCore.Qt.AlignCenter)
      #self.text_label.setWordWrap(True)  # verandert te lange strings naar meerdere lijnen
      self.widgets["text_label"].append(self.text_label)
      #self.text_label.setFixedHeight(300)
      #self.text_label.setStyleSheet("background: '#64A314';")

      # create combo box
      self.combobox = QComboBox()
      self.combobox.addItems(["Poort 0", "Poort 1"])
      self.combobox.currentIndexChanged.connect(self.selectionchange)
      self.widgets["combobox"].append(self.combobox)
      #self.combobox.setMaximumWidth(80)
      #self.combobox.setSizeAdjustPolicy(QComboBox.AdjustToContentsOnFirstShow)
      #elf.combobox.resize(self.combobox.sizeHint())
      #print(self.combobox.sizeHint())
      self.combobox.setFixedWidth(71)

      # create radio buttons
      self.radiobutton1 = QRadioButton("Tiny")
      #self.radiobutton1.setChecked(False)
      self.radiobutton1.setChecked(True)
      self.radiobutton1.tiny = True
      self.radiobutton1.toggled.connect(self.onClicked)
      self.widgets["radio_button1"].append(self.radiobutton1)

      self.radiobutton2 = QRadioButton("Normal")
      self.radiobutton2.tiny = False
      self.radiobutton2.toggled.connect(self.onClicked)
      self.widgets["radio_button2"].append(self.radiobutton2)

      # create open webcam button
      self.webcam_button = QPushButton("Open Webcam")
      self.webcam_button.clicked.connect(self.webcamframe)
      self.widgets["button"].append(self.webcam_button)

      # widgets op grid plaatsen
      self.grid.addWidget(self.text_label, 0, 0)
      self.grid.addWidget(self.radiobutton1, 1, 0)
      self.grid.addWidget(self.radiobutton2, 2, 0)
      self.grid.addWidget(self.combobox, 3, 0)
      self.grid.addWidget(self.webcam_button, 4, 0)

   def selectionchange(self, i):
      self.poort = i
      #print("\nItems in the list are :")
      #for count in range(self.combobox.count()):
      #   print(self.combobox.itemText(count))
      print("Current index", i, ", selection changed:", self.combobox.currentText())

   def onClicked(self):
      self.radiobutton = self.sender()
      if self.radiobutton1.isChecked() and self.radiobutton2.isChecked():
         self.radiobutton1.setChecked(False) # radiobutton1 staat soms foutief aangevinkt
      if self.radiobutton.isChecked():
         self.tiny = self.radiobutton.tiny
         #print("onclicked: ", self.tiny)


   def webcamframe(self):
      self.clear_widgets()
      # create the label that holds the image
      self.webcam_label = QLabel(self)
      self.webcam_label.resize(self.display_width, self.display_height)
      self.widgets["webcam"].append(self.webcam_label)

      # create close webcam button
      self.close_button = QPushButton("Close Webcam")
      self.close_button.clicked.connect(self.close_webcam)
      self.widgets["button"].append(self.close_button)

      # widgets op grid plaatsen
      self.grid.addWidget(self.webcam_label, 0, 0)
      self.grid.addWidget(self.close_button, 1, 0)

      # threading
      self.videothread = VideoThread(self.tiny, self.poort) # create the video capture thread
      self.videothread.change_pixmap_signal.connect(self.update_image) # connect its signal to the update_image slot
      self.videothread.start() # start the thread

   def close_webcam(self):
      self.videothread.stop()
      self.startframe()


   # update the image_label with a new opencv image
   @pyqtSlot(np.ndarray) # decorator, https://stackoverflow.com/questions/45841843/function-of-pyqtslot
   def update_image(self, cv_img):
      qt_img = self.convert_cv_qt(cv_img)
      self.webcam_label.setPixmap(qt_img)

   # convert from an opencv image to QPixmap
   def convert_cv_qt(self, cv_img):
      rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
      h, w, ch = rgb_image.shape
      bytes_per_line = ch * w
      convert_to_Qt_format = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
      p = convert_to_Qt_format.scaled(self.display_width, self.display_height, Qt.KeepAspectRatio)
      return QPixmap.fromImage(p)


def window():
   app = QApplication(sys.argv)
   win = App()
   win.show()
   sys.exit(app.exec_())


window()
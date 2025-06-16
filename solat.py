from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import QTimer, QTime, QDate
import requests
import datetime
import os
import sys
import json

PATH = os.path.dirname(__file__)
BASE_URL = "https://api.waktusolat.app/v2/solat/"
ZONE = "JHR01"
ZONE_CODE = []
ZONE_CODE_DESCRIPTION = []
SUCCESSFUL_LOAD = True

class settings(QtCore.QObject):
    onClosed = QtCore.pyqtSignal(str)
    
    def __init__(self, parent=None):
        super(settings, self).__init__(parent) 
    
    def setupUi(self, Form):
        try:
            with open(os.path.join(PATH, "src", "current.dat"), "r") as current_zone:
                ZONE = current_zone.readline()
        except FileNotFoundError:
            QtWidgets.QMessageBox.warning(
                MainWindow,
                "Warning",
                "Current zone saves not found! Reverting to default value. Refer documentation for more information",
                )
        
        self.Form = Form
        Form.setObjectName("Form")
        Form.resize(400, 300)
        self.verticalLayout = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtWidgets.QLabel(parent=Form)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.zon_dropdown = QtWidgets.QComboBox(parent=Form)
        self.zon_dropdown.setObjectName("zon_dropdown")
        self.verticalLayout.addWidget(self.zon_dropdown)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.saveButton = QtWidgets.QPushButton(parent=Form)
        self.saveButton.setObjectName("saveButton")
        self.horizontalLayout.addWidget(self.saveButton)
        self.cancelButton = QtWidgets.QPushButton(parent=Form)
        self.cancelButton.setObjectName("cancelButton")
        self.horizontalLayout.addWidget(self.cancelButton)
        self.verticalLayout.addLayout(self.horizontalLayout)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.verticalLayout.addItem(spacerItem)

        self.zon_dropdown.addItems(ZONE_CODE_DESCRIPTION)
        self.zon_dropdown.setCurrentIndex(ZONE_CODE.index(ZONE))
        self.saveButton.clicked.connect(self.saveSettings)
        self.cancelButton.clicked.connect(self.exitSettings)
        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Settings"))
        self.label.setText(_translate("Form", "Zon Waktu Solat"))
        self.saveButton.setText(_translate("Form", "Simpan"))
        self.cancelButton.setText(_translate("Form", "Keluar"))
    
    def saveSettings(self):
        ZONE = ZONE_CODE[self.zon_dropdown.currentIndex()]
        with open(os.path.join(PATH, "src", "current.dat"), "w") as current_zone:
            current_zone.write(ZONE)
        self.onClosed.emit("1") # Setting modification was made
        self.Form.close()

    def exitSettings(self):
        self.Form.close()

class Ui_MainWindow(object):
    ERR_CODE = 0
    def setupUi(self, MainWindow):
        try:
            with open(os.path.join(PATH, "src", "zon.dat"), "r") as zone_file:
                for code in zone_file:
                    ZONE_CODE.append(code.strip())
        except FileNotFoundError:
            QtWidgets.QMessageBox.critical(
                MainWindow,
                "Error",
                "File 'zone' not found. Refer documentation for more information (01)",
                )
            sys.exit(-1)
            
        try:
            with open(os.path.join(PATH, "src", "zon_description.dat"), "r") as zone_description_file:
                for description in zone_description_file:
                    ZONE_CODE_DESCRIPTION.append(description.strip())
        except FileNotFoundError:
            QtWidgets.QMessageBox.critical(
                MainWindow,
                "Error",
                "File 'zon_description' not found. Refer documentation for more information (02)",
                )
            sys.exit(-1)
            
        try:
            with open(os.path.join(PATH, "src", "current.dat"), "r") as current_zone:
                ZONE = current_zone.readline()
        except FileNotFoundError:
            QtWidgets.QMessageBox.warning(
                MainWindow,
                "Warning",
                "Current zone saves not found! Reverting to default value. Refer documentation for more information",
                )
            ZONE = "JHR01"
            with open (os.path.join(PATH, "src", "current.dat"), "w") as current_zone:
                current_zone.write(ZONE)
        # -- begin qt designer
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(960, 540)
        self.centralwidget = QtWidgets.QWidget(parent=MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.label_tarikh = QtWidgets.QLabel(parent=self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.label_tarikh.setFont(font)
        self.label_tarikh.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_tarikh.setObjectName("label_tarikh")
        self.horizontalLayout_3.addWidget(self.label_tarikh)
        self.layout_tarikh_masa = QtWidgets.QHBoxLayout()
        self.layout_tarikh_masa.setObjectName("layout_tarikh_masa")
        self.tarikh = QtWidgets.QLabel(parent=self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(13)
        self.tarikh.setFont(font)
        self.tarikh.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight|QtCore.Qt.AlignmentFlag.AlignTrailing|QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.tarikh.setObjectName("tarikh")
        self.layout_tarikh_masa.addWidget(self.tarikh)
        self.masa = QtWidgets.QLabel(parent=self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(13)
        self.masa.setFont(font)
        self.masa.setObjectName("masa")
        self.layout_tarikh_masa.addWidget(self.masa)
        self.horizontalLayout_3.addLayout(self.layout_tarikh_masa)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label = QtWidgets.QLabel(parent=self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.label.setFont(font)
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label.setObjectName("label")
        self.horizontalLayout_2.addWidget(self.label)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.label_waktu_solat_next = QtWidgets.QLabel(parent=self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.label_waktu_solat_next.setFont(font)
        self.label_waktu_solat_next.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_waktu_solat_next.setObjectName("label_waktu_solat_next")
        self.verticalLayout_2.addWidget(self.label_waktu_solat_next)
        self.time_waktu_solat_next = QtWidgets.QLabel(parent=self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(13)
        self.time_waktu_solat_next.setFont(font)
        self.time_waktu_solat_next.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.time_waktu_solat_next.setObjectName("time_waktu_solat_next")
        self.verticalLayout_2.addWidget(self.time_waktu_solat_next)
        self.horizontalLayout_2.addLayout(self.verticalLayout_2)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.frame_subuh = QtWidgets.QVBoxLayout()
        self.frame_subuh.setObjectName("frame_subuh")
        self.label_subuh = QtWidgets.QLabel(parent=self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.label_subuh.setFont(font)
        self.label_subuh.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_subuh.setObjectName("label_subuh")
        self.frame_subuh.addWidget(self.label_subuh)
        self.time_subuh = QtWidgets.QLabel(parent=self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(13)
        self.time_subuh.setFont(font)
        self.time_subuh.setMouseTracking(False)
        self.time_subuh.setLayoutDirection(QtCore.Qt.LayoutDirection.LeftToRight)
        self.time_subuh.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.time_subuh.setObjectName("time_subuh")
        self.frame_subuh.addWidget(self.time_subuh)
        self.horizontalLayout.addLayout(self.frame_subuh)
        self.frame_syuruk = QtWidgets.QVBoxLayout()
        self.frame_syuruk.setObjectName("frame_syuruk")
        self.label_syuruk = QtWidgets.QLabel(parent=self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.label_syuruk.setFont(font)
        self.label_syuruk.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_syuruk.setObjectName("label_syuruk")
        self.frame_syuruk.addWidget(self.label_syuruk)
        self.time_syuruk = QtWidgets.QLabel(parent=self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(13)
        self.time_syuruk.setFont(font)
        self.time_syuruk.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.time_syuruk.setObjectName("time_syuruk")
        self.frame_syuruk.addWidget(self.time_syuruk)
        self.horizontalLayout.addLayout(self.frame_syuruk)
        self.frame_zohor = QtWidgets.QVBoxLayout()
        self.frame_zohor.setObjectName("frame_zohor")
        self.label_zohor = QtWidgets.QLabel(parent=self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.label_zohor.setFont(font)
        self.label_zohor.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_zohor.setObjectName("label_zohor")
        self.frame_zohor.addWidget(self.label_zohor)
        self.time_zohor = QtWidgets.QLabel(parent=self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(13)
        self.time_zohor.setFont(font)
        self.time_zohor.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.time_zohor.setObjectName("time_zohor")
        self.frame_zohor.addWidget(self.time_zohor)
        self.horizontalLayout.addLayout(self.frame_zohor)
        self.frame_asar = QtWidgets.QVBoxLayout()
        self.frame_asar.setObjectName("frame_asar")
        self.label_asar = QtWidgets.QLabel(parent=self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setKerning(True)
        self.label_asar.setFont(font)
        self.label_asar.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_asar.setObjectName("label_asar")
        self.frame_asar.addWidget(self.label_asar)
        self.time_asar = QtWidgets.QLabel(parent=self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(13)
        self.time_asar.setFont(font)
        self.time_asar.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.time_asar.setObjectName("time_asar")
        self.frame_asar.addWidget(self.time_asar)
        self.horizontalLayout.addLayout(self.frame_asar)
        self.frame_maghrib = QtWidgets.QVBoxLayout()
        self.frame_maghrib.setObjectName("frame_maghrib")
        self.label_maghrib = QtWidgets.QLabel(parent=self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.label_maghrib.setFont(font)
        self.label_maghrib.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_maghrib.setObjectName("label_maghrib")
        self.frame_maghrib.addWidget(self.label_maghrib)
        self.time_maghrib = QtWidgets.QLabel(parent=self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(13)
        self.time_maghrib.setFont(font)
        self.time_maghrib.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.time_maghrib.setObjectName("time_maghrib")
        self.frame_maghrib.addWidget(self.time_maghrib)
        self.horizontalLayout.addLayout(self.frame_maghrib)
        self.frame_isyak = QtWidgets.QVBoxLayout()
        self.frame_isyak.setObjectName("frame_isyak")
        self.label_isyak = QtWidgets.QLabel(parent=self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.label_isyak.setFont(font)
        self.label_isyak.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_isyak.setObjectName("label_isyak")
        self.frame_isyak.addWidget(self.label_isyak)
        self.time_isyak = QtWidgets.QLabel(parent=self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(13)
        self.time_isyak.setFont(font)
        self.time_isyak.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.time_isyak.setObjectName("time_isyak")
        self.frame_isyak.addWidget(self.time_isyak)
        self.horizontalLayout.addLayout(self.frame_isyak)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.verticalLayout_3.addLayout(self.verticalLayout)
        self.current_zone_description = QtWidgets.QLabel(parent=self.centralwidget)
        self.current_zone_description.setMaximumSize(QtCore.QSize(16777215, 24))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.current_zone_description.setFont(font)
        self.current_zone_description.setObjectName("current_zone_description")
        self.verticalLayout_3.addWidget(self.current_zone_description)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(parent=MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 960, 26))
        self.menubar.setObjectName("menubar")
        self.menuMenu = QtWidgets.QMenu(parent=self.menubar)
        self.menuMenu.setObjectName("menuMenu")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(parent=MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.actionSettings = QtGui.QAction(parent=MainWindow)
        self.actionSettings.setObjectName("actionSettings")
        self.actionQuit = QtGui.QAction(parent=MainWindow)
        self.actionQuit.setObjectName("actionQuit")
        self.menuMenu.addAction(self.actionSettings)
        self.menuMenu.addAction(self.actionQuit)
        self.menubar.addAction(self.menuMenu.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
        # -- end qt designer

        self.actionSettings.triggered.connect(self.launchSettings)
        self.actionQuit.triggered.connect(self.quitApp)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000) # Update every 1000 ms (1 second)
        self.update_date()

        msg = ''
        if not self.get_waktu(ZONE):
            if self.ERR_CODE == 3:
                msg = "Service return unexpected data. (03)"
            elif self.ERR_CODE == 4:
                msg = "Unable to connect to service. Ensure internet connectivity remains present"
            QtWidgets.QMessageBox.critical(
                MainWindow,
                "Error",
                msg
                )
            sys.exit(-1)
            

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Waktu Solat"))
        self.label_tarikh.setText(_translate("MainWindow", "Tarikh Masa"))
        self.tarikh.setText(_translate("MainWindow", "DD/MM/YYYY"))
        self.masa.setText(_translate("MainWindow", "hh:mm:ss"))
        self.label.setText(_translate("MainWindow", "Waktu solat seterusnya:"))
        self.label_waktu_solat_next.setText(_translate("MainWindow", "waktu_solat"))
        self.time_waktu_solat_next.setText(_translate("MainWindow", "00:00"))
        self.label_subuh.setText(_translate("MainWindow", "Subuh"))
        self.time_subuh.setText(_translate("MainWindow", "00:00"))
        self.label_syuruk.setText(_translate("MainWindow", "Syuruk"))
        self.time_syuruk.setText(_translate("MainWindow", "00:00"))
        self.label_zohor.setText(_translate("MainWindow", "Zohor"))
        self.time_zohor.setText(_translate("MainWindow", "00:00"))
        self.label_asar.setText(_translate("MainWindow", "Asar"))
        self.time_asar.setText(_translate("MainWindow", "00:00"))
        self.label_maghrib.setText(_translate("MainWindow", "Maghrib"))
        self.time_maghrib.setText(_translate("MainWindow", "00:00"))
        self.label_isyak.setText(_translate("MainWindow", "Isyak"))
        self.time_isyak.setText(_translate("MainWindow", "00:00"))
        self.current_zone_description.setText(_translate("MainWindow", "TextLabel"))
        self.menuMenu.setTitle(_translate("MainWindow", "Menu"))
        self.actionSettings.setText(_translate("MainWindow", "Settings"))
        self.actionQuit.setText(_translate("MainWindow", "Quit"))

    def update_time(self):
        current_time = QTime.currentTime()
        formatted_time = current_time.toString("hh:mm:ss")
        if formatted_time == "00:00:00":
            self.update_date()
            print("Updating date")
        self.masa.setText(formatted_time)

    def update_date(self):
        current_date = QDate.currentDate()
        formatted_date = current_date.toString("dd/MM/yyyy")
        self.tarikh.setText(formatted_date)

    def get_waktu(self, zone):
        cache = True
        today = datetime.datetime.today()
        month = today.month
        year = today.year
        prayer_index = today.day - 1
        try:
            with open (os.path.join(PATH,"src", "cache_zon.dat"), "r") as cache_file:
                response_dict = json.loads(cache_file.read())
                if response_dict['zone'] != zone or response_dict["month_number"] != month or response_dict["year"] != year:
                    print("Current month, year or zone in file mismatch.")
                    cache = False
        except FileNotFoundError:
            with open(os.path.join(PATH,"src", "cache_zon.dat"), "x") as cache_file:
                cache = False
        except json.decoder.JSONDecodeError: #cache file is empty
            cache = False
        if not cache:
            try:
                response = requests.get(f'{BASE_URL}{zone}')
                if response.status_code != 200:
                    self.ERR_CODE = 3
                    return False
            except requests.exceptions.ConnectionError:
                self.ERR_CODE = 4
                return False
            response_dict = response.json()
            with open(os.path.join(PATH, "src", "cache_zon.dat"), "w") as cache_file:
                cache_file.write(json.dumps(response_dict))
        self.current_zone_description.setText(f"Waktu solat bagi kawasan {ZONE_CODE_DESCRIPTION[(ZONE_CODE.index(zone))]}")
        self.time_subuh.setText(str(datetime.datetime.fromtimestamp(response_dict['prayers'][prayer_index]['fajr']).strftime("%H:%M")))
        self.time_syuruk.setText(str(datetime.datetime.fromtimestamp(response_dict['prayers'][prayer_index]['syuruk']).strftime("%H:%M")))
        self.time_zohor.setText(str(datetime.datetime.fromtimestamp(response_dict['prayers'][prayer_index]['dhuhr']).strftime("%H:%M")))
        self.time_asar.setText(str(datetime.datetime.fromtimestamp(response_dict['prayers'][prayer_index]['asr']).strftime("%H:%M")))
        self.time_maghrib.setText(str(datetime.datetime.fromtimestamp(response_dict['prayers'][prayer_index]['maghrib']).strftime("%H:%M")))
        self.time_isyak.setText(str(datetime.datetime.fromtimestamp(response_dict['prayers'][prayer_index]['isha']).strftime("%H:%M")))
        if int(today.timestamp()) < response_dict['prayers'][prayer_index]['fajr']:
            self.label_waktu_solat_next.setText("Subuh")
            self.time_waktu_solat_next.setText(str(datetime.datetime.fromtimestamp(response_dict['prayers'][prayer_index]['fajr']).strftime("%H:%M")))
        elif int(today.timestamp()) < response_dict['prayers'][prayer_index]['syuruk']:
            self.label_waktu_solat_next.setText("Syuruk")
            self.time_waktu_solat_next.setText(str(datetime.datetime.fromtimestamp(response_dict['prayers'][prayer_index]['syuruk']).strftime("%H:%M")))
        elif int(today.timestamp()) < response_dict['prayers'][prayer_index]['dhuhr']:
            self.label_waktu_solat_next.setText("Zohor")
            self.time_waktu_solat_next.setText(str(datetime.datetime.fromtimestamp(response_dict['prayers'][prayer_index]['dhuhr']).strftime("%H:%M")))
        elif int(today.timestamp()) < response_dict['prayers'][prayer_index]['asr']:
            self.label_waktu_solat_next.setText("Asar")
            self.time_waktu_solat_next.setText(str(datetime.datetime.fromtimestamp(response_dict['prayers'][prayer_index]['asr']).strftime("%H:%M")))
        elif int(today.timestamp()) < response_dict['prayers'][prayer_index]['maghrib']:
            self.label_waktu_solat_next.setText("Maghrib")
            self.time_waktu_solat_next.setText(str(datetime.datetime.fromtimestamp(response_dict['prayers'][prayer_index]['maghrib']).strftime("%H:%M")))
        elif int(today.timestamp()) < response_dict['prayers'][prayer_index]['isha']:
            self.label_waktu_solat_next.setText("Isyak")
            self.time_waktu_solat_next.setText(str(datetime.datetime.fromtimestamp(response_dict['prayers'][prayer_index]['isha']).strftime("%H:%M")))
        else:
            prayer_index += 1
            if prayer_index == len(response_dict['prayers']):
                prayer_index = 0
                month += 1
                if month == 13:
                    month = 1
                    year += 1
                next_month_url = f"https://api.waktusolat.app/v2/solat/{zone}?year={year}&month={month}"
                response = requests.get(next_month_url)
                if response.status_code != 200:
                    self.ERR_CODE = 3
                    return False
                response_dict = response.json()
            self.label_waktu_solat_next.setText("Subuh")
            self.time_waktu_solat_next.setText(str(datetime.datetime.fromtimestamp(response_dict['prayers'][prayer_index]['fajr']).strftime("%H:%M")))   
        return True

    def launchSettings(self):
        self.form = QtWidgets.QWidget()
        self.settings = settings()
        self.settings.setupUi(self.form)
        self.settings.onClosed.connect(self.closeSettings)
        self.form.show()

    def closeSettings(self, event):
        if event == "1":
            with open(os.path.join(PATH, "src","current.dat"), "r") as current_zone:
                ZONE = current_zone.readline()
            self.get_waktu(ZONE)
    
    def quitApp(self):
        sys.exit(0)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec())
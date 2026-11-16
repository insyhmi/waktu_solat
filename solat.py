from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import QTimer, QTime, QDate, QUrl
from zoneinfo import ZoneInfo
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
import requests
import datetime
import os
import sys
import json

BASE_URL_MALAYSIA = "https://api.waktusolat.app/v2/solat/"
BASE_URL_AUS = "https://api.aladhan.com/v1/timings/"  
ZONE = "JHR01"
ZONE_CODE = []
ZONE_CODE_DESCRIPTION = []
SUCCESSFUL_LOAD = True

COUNTRIES = {"Malaysia": "MY", "Australia": "AU"}
COUNTRY_NAMES = {v: k for k, v in COUNTRIES.items()}

# For Australia cities
# city: (latitude, longitude, timezone) 
AU_CITIES = {
    "Sydney":    (-33.8688, 151.2093, "Australia/Sydney"),
    "Melbourne": (-37.8136, 144.9631, "Australia/Melbourne"),
    "Brisbane":  (-27.4698, 153.0251, "Australia/Brisbane"),
    "Perth":     (-31.9505, 115.8605, "Australia/Perth"),
    "Adelaide":  (-34.9285, 138.6007, "Australia/Adelaide"),
    "Canberra":  (-35.2809, 149.1300, "Australia/Sydney"),
    "Hobart":    (-42.8821, 147.3272, "Australia/Hobart"),
    "Darwin":    (-12.4634, 130.8456, "Australia/Darwin"),
}
AU_METHOD = 3  # Muslim World League

PRAYER_ORDER = [("fajr", "Subuh"), ("syuruk", "Syuruk"), ("dhuhr", "Zohor"),
                ("asr", "Asar"), ("maghrib", "Maghrib"), ("isha", "Isyak")]

ALERT_KEYS = {"fajr", "dhuhr", "asr", "maghrib", "isha"}
ALERT_WINDOW = datetime.timedelta(minutes=2) 
RETRY_DELAY = datetime.timedelta(seconds=60) 

def resource_path(*parts):
    """Read-only files bundled with the app."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, *parts)


def data_dir():
    """Writable per-user folder for settings and cache."""
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
    path = os.path.join(base, "WaktuSolat")
    os.makedirs(path, exist_ok=True)
    return path

AZAN_DIR = os.path.join(data_dir(), "azan")          # empty by default
os.makedirs(AZAN_DIR, exist_ok=True)
AZAN_SETTINGS_FILE = os.path.join(data_dir(), "azan.json")
AZAN_EXTS = (".mp3", ".wav", ".ogg")
AZAN_PRAYERS = [(k, l) for k, l in PRAYER_ORDER if k in ALERT_KEYS]

AZAN_CATALOG = {
    "Dai Syazwan.mp3": "https://drive.google.com/uc?id=1jvEXGaagRhTx0_vCnJLSLPDd-KBajbaR",
    "Ustaz Asri.mp3": "https://drive.google.com/uc?id=1QF68X3WOwkzB2MDE1xhhjk9M-a2d3xHm",
}

AZAN_CATALOG_FAJR = {
    "Fajr Syeikh Mansur Al-Zahrani.mp3": "https://drive.google.com/uc?id=17Y7Ju6W3z6Ur_WNGGkCwq93S1Wf5PLru",
    "Fajr Mishary Rashid.mp3": "https://drive.google.com/uc?id=1G2naFBKl3HYvefj1YSUmBciFxzSBTfrY"
}

def load_azan_settings():
    cfg = {"enabled": False,
           "prayers": {k: True for k, _ in AZAN_PRAYERS},
           "file": "",
           "file_fajr": ""}
    try:
        with open(AZAN_SETTINGS_FILE) as f:
            saved = json.load(f)
        cfg["enabled"] = bool(saved.get("enabled", False))
        cfg["file"] = saved.get("file", "")
        cfg["file_fajr"] = saved.get("file_fajr", "")
        cfg["prayers"].update(saved.get("prayers", {}))
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return cfg


def save_azan_settings(cfg):
    with open(AZAN_SETTINGS_FILE, "w") as f:
        json.dump(cfg, f)


def ensure_azan(filename):
    """Returns the local path, downloading the file first if it isn't on disk."""
    path = os.path.join(AZAN_DIR, filename)
    if os.path.exists(path):
        return path
    url = {**AZAN_CATALOG, **AZAN_CATALOG_FAJR}.get(filename)
    if not url:
        raise FileNotFoundError(filename)
    r = requests.get(url, timeout=30, stream=True)
    r.raise_for_status()
    tmp = path + ".part"
    with open(tmp, "wb") as f:
        for chunk in r.iter_content(65536):
            f.write(chunk)
    os.replace(tmp, path)   # so a half-finished download is never mistaken for a real file
    return path

CACHE_FILE = os.path.join(data_dir(), "cache_zon.dat")
SELECTION_FILE = os.path.join(data_dir(), "current.dat")
"""
Returns (country_code, zone). 
Old files holding just 'JHR01' still work.
"""
def load_selection():
    try:
        with open(SELECTION_FILE) as f:
            raw = f.readline().strip()
    except FileNotFoundError:
        return "MY", "JHR01"
    if ":" in raw:
        country, zone = raw.split(":", 1)
        return country, zone
    return "MY", raw or "JHR01"

def save_selection(country, zone):
    with open(SELECTION_FILE, "w") as f:
        f.write(f"{country}:{zone}")

def zone_tz(country, zone):
    if country == "AU":
        return ZoneInfo(AU_CITIES[zone][2])
    return ZoneInfo("Asia/Kuala_Lumpur")

def _parse_time(value, day, tz):
    value = value.strip()
    try:
        return datetime.datetime.fromisoformat(value).astimezone(tz)
    except ValueError:
        hh, mm = value.split(" ")[0].split(":")
        return datetime.datetime.combine(day, datetime.time(int(hh), int(mm)), tzinfo=tz)

def _fetch_my(zone, day):
    tz = zone_tz("MY", zone)
    r = requests.get(f"{BASE_URL_MALAYSIA}{zone}",
                     params={"year": day.year, "month": day.month}, timeout=10)
    r.raise_for_status()
    entry = r.json()["prayers"][day.day - 1]
    return {k: datetime.datetime.fromtimestamp(entry[k], tz) for k, _ in PRAYER_ORDER}

def _fetch_au(city, day):
    lat, lon, tzname = AU_CITIES[city]
    tz = ZoneInfo(tzname)
    r = requests.get(f"{BASE_URL_AUS}{day:%d-%m-%Y}",
                     params={"latitude": lat, "longitude": lon,
                             "method": AU_METHOD, "timezonestring": tzname},
                     timeout=10)
    r.raise_for_status()
    t = r.json()["data"]["timings"]
    mapping = {"fajr": "Fajr", "syuruk": "Sunrise", "dhuhr": "Dhuhr",
               "asr": "Asr", "maghrib": "Maghrib", "isha": "Isha"}
    return {k: _parse_time(t[v], day, tz) for k, v in mapping.items()}

"""Normalised {'fajr': aware datetime, ...} for one day, with a small file cache."""
def get_times(country, zone, day):
    key = f"{country}:{zone}:{day.isoformat()}"
    try:
        with open(CACHE_FILE) as f:
            cache = json.load(f)
        cache = {k: v for k, v in cache.items() if isinstance(v, dict) and ":" in k}
    except (FileNotFoundError, json.JSONDecodeError):
        cache = {}

    if key in cache:
        return {k: datetime.datetime.fromisoformat(v) for k, v in cache[key].items()}

    times = _fetch_au(zone, day) if country == "AU" else _fetch_my(zone, day)

    cache = {k: v for k, v in cache.items() if k.rsplit(":", 1)[1] >= day.isoformat()}
    cache[key] = {k: v.isoformat() for k, v in times.items()}
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f)
    return times

class settings(QtCore.QObject):
    onClosed = QtCore.pyqtSignal(str)
    
    def __init__(self, parent=None):
        super(settings, self).__init__(parent) 
    
    def setupUi(self, Form):
        self.Form = Form
        Form.setObjectName("Form")
        Form.resize(400, 300)
        self.verticalLayout = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtWidgets.QLabel(parent=Form)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.country_dropdown = QtWidgets.QComboBox(parent=Form)
        self.country_dropdown.setObjectName("country_dropdown")
        self.verticalLayout.addWidget(self.country_dropdown)
        self.zon_dropdown = QtWidgets.QComboBox(parent=Form)
        self.zon_dropdown.setObjectName("zon_dropdown")
        self.verticalLayout.addWidget(self.zon_dropdown)
        self.azan_enable = QtWidgets.QCheckBox(parent=Form)
        self.azan_enable.setObjectName("azan_enable")
        self.verticalLayout.addWidget(self.azan_enable)
        self.prayer_row = QtWidgets.QHBoxLayout()
        self.prayer_checks = {}
        for key, label in AZAN_PRAYERS:
            cb = QtWidgets.QCheckBox(label, parent=Form)
            self.prayer_checks[key] = cb
            self.prayer_row.addWidget(cb)
        self.verticalLayout.addLayout(self.prayer_row)
        self.azan_label = QtWidgets.QLabel(parent=Form)
        self.verticalLayout.addWidget(self.azan_label)
        self.azan_dropdown = QtWidgets.QComboBox(parent=Form)
        self.azan_dropdown.setObjectName("azan_dropdown")
        self.verticalLayout.addWidget(self.azan_dropdown)
        self.azan_fajr_label = QtWidgets.QLabel(parent=Form)
        self.verticalLayout.addWidget(self.azan_fajr_label)
        self.azan_fajr_dropdown = QtWidgets.QComboBox(parent=Form)
        self.azan_fajr_dropdown.setObjectName("azan_fajr_dropdown")
        self.verticalLayout.addWidget(self.azan_fajr_dropdown)
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

        self.zones = []
        country, zone = load_selection()
        self.country_dropdown.addItems(list(COUNTRIES))
        self.country_dropdown.setCurrentText(COUNTRY_NAMES.get(country, "Malaysia"))
        self.populate_zones()
        for i, (code, _) in enumerate(self.zones):
            if code == zone:
                self.zon_dropdown.setCurrentIndex(i)
        cfg = load_azan_settings()
        self.azan_enable.setChecked(cfg["enabled"])
        for key, cb in self.prayer_checks.items():
            cb.setChecked(cfg["prayers"].get(key, True))
        self.populate_azan_files(self.azan_dropdown, AZAN_CATALOG, cfg["file"])
        self.populate_azan_files(self.azan_fajr_dropdown, AZAN_CATALOG_FAJR, cfg["file_fajr"])
        self.azan_enable.toggled.connect(self.toggle_azan_controls)
        self.toggle_azan_controls(cfg["enabled"])
        self.country_dropdown.currentIndexChanged.connect(self.populate_zones)
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
        self.azan_enable.setText(_translate("Form", "Aktifkan panggilan azan"))
        self.azan_label.setText(_translate("Form", "Azan"))
        self.azan_fajr_label.setText(_translate("Form", "Azan Subuh"))

    def populate_zones(self):
        code = COUNTRIES[self.country_dropdown.currentText()]
        if code == "AU":
            self.zones = [(c, c) for c in AU_CITIES]
        else:
            self.zones = list(zip(ZONE_CODE, ZONE_CODE_DESCRIPTION))
        self.zon_dropdown.clear()
        self.zon_dropdown.addItems([desc for _, desc in self.zones])

    def toggle_azan_controls(self, enabled):
        for cb in self.prayer_checks.values():
            cb.setEnabled(enabled)
        for w in (self.azan_label, self.azan_dropdown,
                  self.azan_fajr_label, self.azan_fajr_dropdown):
            w.setEnabled(enabled)

    def populate_azan_files(self, combo, catalog, selected=""):
        local = {f for f in os.listdir(AZAN_DIR) if f.lower().endswith(AZAN_EXTS)}
        combo.clear()
        for name in sorted(local | set(catalog)):
            text = name if name in local else f"{name} (dimuat turun semasa simpan)"
            combo.addItem(text, name)
        idx = combo.findData(selected)
        if idx >= 0:
            combo.setCurrentIndex(idx)

    def saveSettings(self):
        enabled = self.azan_enable.isChecked()
        filename = self.azan_dropdown.currentData() or ""
        filename_fajr = self.azan_fajr_dropdown.currentData() or ""

        if enabled:
            QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.CursorShape.WaitCursor)
            try:
                for fn in (filename, filename_fajr):
                    if fn:
                        ensure_azan(fn)
            except (requests.exceptions.RequestException, OSError) as e:
                QtWidgets.QApplication.restoreOverrideCursor()
                QtWidgets.QMessageBox.warning(
                    self.Form, "Warning", f"Gagal memuat turun fail azan:\n{e}")
                return
            QtWidgets.QApplication.restoreOverrideCursor()

        save_azan_settings({
            "enabled": enabled,
            "prayers": {k: cb.isChecked() for k, cb in self.prayer_checks.items()},
            "file": filename,
            "file_fajr": filename_fajr,
        })

        country = COUNTRIES[self.country_dropdown.currentText()]
        zone = self.zones[self.zon_dropdown.currentIndex()][0]
        save_selection(country, zone)
        self.onClosed.emit("1")
        self.Form.close()

    def exitSettings(self):
        self.Form.close()

class Ui_MainWindow(object):
    ERR_CODE = 0
    tray = None
    current_times = None
    notified = set()
    next_retry = None
    def setupUi(self, MainWindow):
        try:
            with open(resource_path("src", "zon.dat"), "r") as zone_file:
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
            with open(resource_path("src", "zon_description.dat"), "r") as zone_description_file:
                for description in zone_description_file:
                    ZONE_CODE_DESCRIPTION.append(description.strip())
        except FileNotFoundError:
            QtWidgets.QMessageBox.critical(
                MainWindow,
                "Error",
                "File 'zon_description' not found. Refer documentation for more information (02)",
                )
            sys.exit(-1)
        
        self.main_window = MainWindow
        country, ZONE = load_selection()
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
        self.audio_output = QAudioOutput()
        self.player = QMediaPlayer()
        self.player.setAudioOutput(self.audio_output)
        self.update_date()

        msg = ''
        if not self.get_waktu(country, ZONE):
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
        self.check_alerts()

    def check_alerts(self):
        if not self.current_times:
            return
        now = datetime.datetime.now(self.current_tz)
        for key, label in PRAYER_ORDER:
            t = self.current_times[key]
            marker = (self.current_date, key)
            if key in ALERT_KEYS and marker not in self.notified and t <= now < t + ALERT_WINDOW:
                self.notified.add(marker)
                self.play_azan(key)
                if self.tray:
                    self.tray.showMessage(
                        "Waktu Solat",
                        f"Masuk waktu {label} bagi kawasan {self.current_zone} ({t.strftime('%H:%M')})",
                        QtWidgets.QSystemTrayIcon.MessageIcon.Information,
                        10000)
                self.notified = {m for m in self.notified if m[0] >= self.current_date}

        if now.date() != self.current_date or now >= self.next_time:
            if self.next_retry is None or now >= self.next_retry:
                if not self.get_waktu(self.current_country, self.current_zone):
                    self.next_retry = now + RETRY_DELAY   # retry in a minute, not every second
                else:
                    self.next_retry = None

    def update_date(self):
        current_date = QDate.currentDate()
        formatted_date = current_date.toString("dd/MM/yyyy")
        self.tarikh.setText(formatted_date)

    def get_waktu(self, country, zone):
        try:
            tz = zone_tz(country, zone)
            today = datetime.datetime.now(tz).date()
            times = get_times(country, zone, today)
            now = datetime.datetime.now(tz)

            widgets = {"fajr": self.time_subuh, "syuruk": self.time_syuruk,
                       "dhuhr": self.time_zohor, "asr": self.time_asar,
                       "maghrib": self.time_maghrib, "isha": self.time_isyak}
            for key, widget in widgets.items():
                widget.setText(times[key].strftime("%H:%M"))

            if country == "AU":
                desc = f"{zone}, Australia"
            else:
                desc = ZONE_CODE_DESCRIPTION[ZONE_CODE.index(zone)]
            self.current_zone_description.setText(f"Waktu solat bagi kawasan {desc}")

            for key, label in PRAYER_ORDER:
                if now < times[key]:
                    next_label, next_time = label, times[key]
                    break
            else:  # all of today's prayers have passed -> tomorrow's Subuh
                tomorrow = get_times(country, zone, today + datetime.timedelta(days=1))
                next_label, next_time = "Subuh", tomorrow["fajr"]

            self.label_waktu_solat_next.setText(next_label)
            self.time_waktu_solat_next.setText(next_time.strftime("%H:%M"))
            self.current_country, self.current_zone, self.current_tz = country, zone, tz
            self.current_times, self.current_date, self.next_time = times, today, next_time
            return True

        except requests.exceptions.RequestException:
            import traceback; traceback.print_exc()
            self.ERR_CODE = 4
        except (KeyError, IndexError, ValueError):
            import traceback; traceback.print_exc()
            self.ERR_CODE = 3
        return False

    def launchSettings(self):
        self.form = QtWidgets.QWidget()
        self.settings = settings()
        self.settings.setupUi(self.form)
        self.settings.onClosed.connect(self.closeSettings)
        self.form.show()

    def closeSettings(self, event):
        if event == "1":
            country, zone = load_selection()
            if not self.get_waktu(country, zone):
                QtWidgets.QMessageBox.warning(
                    self.form, "Warning", "Unable to load prayer times for the selected location.")
    
    def quitApp(self):
        self.main_window.confirm_quit = True
        QtWidgets.QApplication.quit()

    def play_azan(self, key):
        cfg = load_azan_settings()
        if not cfg["enabled"] or not cfg["prayers"].get(key):
            return False
        filename = (cfg["file_fajr"] or cfg["file"]) if key == "fajr" else cfg["file"]
        if not filename:
            return False
        path = os.path.join(AZAN_DIR, filename)
        if not os.path.exists(path):
            return False
        self.player.setSource(QUrl.fromLocalFile(path))
        self.audio_output.setVolume(1.0)
        self.player.play()
        return True
    
class AppWindow(QtWidgets.QMainWindow):

    confirm_quit = False
    def closeEvent(self, event):
        if self.confirm_quit:
            event.accept()
        else:
            event.ignore()
            self.hide()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    MainWindow = AppWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    icon_path = resource_path("src", "icon.png")
    if os.path.exists(icon_path):
        icon = QtGui.QIcon(icon_path)
    else:
        icon = app.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_ComputerIcon)
    MainWindow.setWindowIcon(icon)
    tray = QtWidgets.QSystemTrayIcon(icon, MainWindow)
    tray.messageClicked.connect(ui.player.stop)
    ui.tray = tray
    tray.setToolTip("Lanx's Waktu Solat")

    def show_window():
        MainWindow.show()
        MainWindow.setWindowState(MainWindow.windowState() & ~QtCore.Qt.WindowState.WindowMinimized)
        MainWindow.raise_()
        MainWindow.activateWindow()

    tray_menu = QtWidgets.QMenu()
    show_action = tray_menu.addAction("Show")
    show_action.triggered.connect(show_window)
    quit_action = tray_menu.addAction("Quit")
    quit_action.triggered.connect(ui.quitApp)
    stop_action = tray_menu.addAction("Stop azan")
    stop_action.triggered.connect(ui.player.stop)
    tray.setContextMenu(tray_menu)
    tray.activated.connect(
        lambda reason: show_window()
        if reason in (QtWidgets.QSystemTrayIcon.ActivationReason.Trigger, QtWidgets.QSystemTrayIcon.ActivationReason.DoubleClick)
        else None)
    tray.show()

    MainWindow.show()
    sys.exit(app.exec())
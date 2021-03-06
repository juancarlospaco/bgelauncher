#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PEP8:OK, LINT:OK, PY3:OK


# metadata
"""BGElauncher."""
__package__ = "bgelauncher"
__version__ = ' 0.0.1 '
__license__ = ' GPLv3+ LGPLv3+ '
__author__ = ' JuanCarlos '
__email__ = ' juancarlospaco@gmail.com '
__url__ = 'https://github.com/juancarlospaco/bgelauncher#bgelauncher'
__source__ = ('https://raw.githubusercontent.com/juancarlospaco/'
              'bgelauncher/master/bgelauncher.py')


# imports
import codecs
import logging as log
import os
import signal
import sys
import tarfile
import time
import zipfile
from copy import copy
from ctypes import byref, cdll, create_string_buffer
from datetime import datetime
from getopt import getopt
from subprocess import call, check_output
from tempfile import gettempdir
from urllib import request
from webbrowser import open_new_tab
from zipfile import ZipFile

from PyQt5.QtCore import (QDir, QFile, QFileInfo, QIODevice, QProcess, QSize,
                          Qt, QTimer, QUrl)
from PyQt5.QtGui import QIcon
from PyQt5.QtNetwork import (QNetworkAccessManager, QNetworkProxyFactory,
                             QNetworkRequest)
from PyQt5.QtWidgets import (QApplication, QCheckBox, QComboBox, QDialog,
                             QDialogButtonBox, QFileDialog, QFontDialog,
                             QGridLayout, QGroupBox, QHBoxLayout, QInputDialog,
                             QLabel, QMainWindow, QMessageBox, QProgressBar,
                             QProgressDialog, QShortcut, QSpinBox, QVBoxLayout,
                             QWidget)


HELP = """<h3>BGElauncher</h3><b>Blender Game Engine Launcher App !</b><br>
Version {}, licence {}<ul><li>Python3 + Qt5, single-file, No Dependencies</ul>
DEV: <a href=https://github.com/juancarlospaco>JuanCarlos</a>
""".format(__version__, __license__)
GAME_FILE = "game.blend"
PASSWORD = ""


###############################################################################


class Downloader(QProgressDialog):

    """Downloader Dialog with complete informations and progress bar."""

    def __init__(self, parent=None):
        """Init class."""
        super(Downloader, self).__init__(parent)
        self.setWindowTitle(__doc__)
        if not os.path.isfile(__file__) or not __source__:
            self.close()
        self._time, self._date = time.time(), datetime.now().isoformat()[:-7]
        self._url, self._dst = __source__, __file__
        log.debug("Downloading from {} to {}.".format(self._url, self._dst))
        if not self._url.lower().startswith("https:"):
            log.warning("Unsecure Download over plain text without SSL.")
        self.template = """<h3>Downloading</h3><hr><table>
        <tr><td><b>From:</b></td>      <td>{}</td>
        <tr><td><b>To:  </b></td>      <td>{}</td> <tr>
        <tr><td><b>Started:</b></td>   <td>{}</td>
        <tr><td><b>Actual:</b></td>    <td>{}</td> <tr>
        <tr><td><b>Elapsed:</b></td>   <td>{}</td>
        <tr><td><b>Remaining:</b></td> <td>{}</td> <tr>
        <tr><td><b>Received:</b></td>  <td>{} MegaBytes</td>
        <tr><td><b>Total:</b></td>     <td>{} MegaBytes</td> <tr>
        <tr><td><b>Speed:</b></td>     <td>{}</td>
        <tr><td><b>Percent:</b></td>     <td>{}%</td></table><hr>"""
        self.manager = QNetworkAccessManager(self)
        self.manager.finished.connect(self.save_downloaded_data)
        self.manager.sslErrors.connect(self.download_failed)
        self.progreso = self.manager.get(QNetworkRequest(QUrl(self._url)))
        self.progreso.downloadProgress.connect(self.update_download_progress)
        self.show()
        self.exec_()

    def save_downloaded_data(self, data):
        """Save all downloaded data to the disk and quit."""
        log.debug("Download done. Update Done.")
        with open(os.path.join(self._dst), "wb") as output_file:
            output_file.write(data.readAll())
        data.close()
        QMessageBox.information(self, __doc__.title(),
                                "<b>You got the latest version of this App!")
        del self.manager, data
        return self.close()

    def download_failed(self, download_error):
        """Handle a download error, probable SSL errors."""
        log.error(download_error)
        QMessageBox.error(self, __doc__.title(), str(download_error))

    def seconds_time_to_human_string(self, time_on_seconds=0):
        """Calculate time, with precision from seconds to days."""
        minutes, seconds = divmod(int(time_on_seconds), 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)
        human_time_string = ""
        if days:
            human_time_string += "%02d Days " % days
        if hours:
            human_time_string += "%02d Hours " % hours
        if minutes:
            human_time_string += "%02d Minutes " % minutes
        human_time_string += "%02d Seconds" % seconds
        return human_time_string

    def update_download_progress(self, bytesReceived, bytesTotal):
        """Calculate statistics and update the UI with them."""
        downloaded_MB = round(((bytesReceived / 1024) / 1024), 2)
        total_data_MB = round(((bytesTotal / 1024) / 1024), 2)
        downloaded_KB, total_data_KB = bytesReceived / 1024, bytesTotal / 1024
        # Calculate download speed values, with precision from Kb/s to Gb/s
        elapsed = time.clock()
        if elapsed > 0:
            speed = round((downloaded_KB / elapsed), 2)
            if speed > 1024000:  # Gigabyte speeds
                download_speed = "{} GigaByte/Second".format(speed // 1024000)
            if speed > 1024:  # MegaByte speeds
                download_speed = "{} MegaBytes/Second".format(speed // 1024)
            else:  # KiloByte speeds
                download_speed = "{} KiloBytes/Second".format(int(speed))
        if speed > 0:
            missing = abs((total_data_KB - downloaded_KB) // speed)
        percentage = int(100.0 * bytesReceived // bytesTotal)
        self.setLabelText(self.template.format(
            self._url.lower()[:99], self._dst.lower()[:99],
            self._date, datetime.now().isoformat()[:-7],
            self.seconds_time_to_human_string(time.time() - self._time),
            self.seconds_time_to_human_string(missing),
            downloaded_MB, total_data_MB, download_speed, percentage))
        self.setValue(percentage)


###############################################################################


def get_blender_version():
    """
    Try to return Blender version if fails return the default docstring.

    >>> isinstance(get_blender_version(), str)
    True
    """
    try:
        ver = check_output("blender --version", shell=True).splitlines()[0]
        ver = str(ver[:-7]).strip().lower()
    except:
        ver = __doc__.strip().lower()
    finally:
        log.info(ver)
        return ver


class MainWindow(QMainWindow):

    """Main window of the BGE Launcher."""

    def __init__(self, parent=None):
        """Init class."""
        super(MainWindow, self).__init__()
        QNetworkProxyFactory.setUseSystemConfiguration(True)
        self.statusBar().showMessage(get_blender_version())
        self.setWindowTitle(__doc__.strip().capitalize())
        self.setMinimumSize(400, 200)
        self.setMaximumSize(1024, 800)
        self.resize(self.minimumSize())
        self.setWindowIcon(QIcon.fromTheme("blender"))
        self.center()
        QShortcut("Ctrl+q", self, activated=lambda: self.close())
        self.menuBar().addMenu("&File").addAction("Exit", exit)
        windowMenu = self.menuBar().addMenu("&Window")
        windowMenu.addAction("Minimize", lambda: self.showMinimized())
        windowMenu.addAction("Maximize", lambda: self.showMaximized())
        windowMenu.addAction("Restore", lambda: self.showNormal())
        windowMenu.addAction("FullScreen", lambda: self.showFullScreen())
        windowMenu.addAction("Center", lambda: self.center())
        windowMenu.addAction("Top-Left", lambda: self.move(0, 0))
        windowMenu.addAction("To Mouse", lambda: self.move_to_mouse_position())
        windowMenu.addSeparator()
        windowMenu.addAction(
            "Increase size", lambda:
            self.resize(self.size().width() * 1.4, self.size().height() * 1.4))
        windowMenu.addAction("Decrease size", lambda: self.resize(
            self.size().width() // 1.4, self.size().height() // 1.4))
        windowMenu.addAction("Minimum size", lambda:
                             self.resize(self.minimumSize()))
        windowMenu.addAction("Maximum size", lambda:
                             self.resize(self.maximumSize()))
        windowMenu.addAction("Horizontal Wide", lambda: self.resize(
            self.maximumSize().width(), self.minimumSize().height()))
        windowMenu.addAction("Vertical Tall", lambda: self.resize(
            self.minimumSize().width(), self.maximumSize().height()))
        windowMenu.addSeparator()
        windowMenu.addAction("Disable Resize", lambda:
                             self.setFixedSize(self.size()))
        windowMenu.addAction("Set Interface Font...", lambda:
                             self.setFont(QFontDialog.getFont()[0]))
        windowMenu.addAction(
            "Load .qss Skin", lambda: self.setStyleSheet(self.skin()))
        helpMenu = self.menuBar().addMenu("&Help")
        helpMenu.addAction("About Qt 5", lambda: QMessageBox.aboutQt(self))
        helpMenu.addAction("About Python 3",
                           lambda: open_new_tab('https://www.python.org'))
        helpMenu.addAction("About" + __doc__,
                           lambda: QMessageBox.about(self, __doc__, HELP))
        helpMenu.addSeparator()
        helpMenu.addAction(
            "Keyboard Shortcut",
            lambda: QMessageBox.information(self, __doc__, "<b>Quit = CTRL+Q"))
        if sys.platform.startswith('linux'):
            helpMenu.addAction(
                "View Source Code",
                lambda: call('xdg-open ' + __file__, shell=True))
        helpMenu.addAction("View GitHub Repo", lambda: open_new_tab(__url__))
        helpMenu.addAction("Report Bugs", lambda: open_new_tab(
            'https://github.com/juancarlospaco/bgelauncher/issues?state=open'))
        helpMenu.addAction("Check Updates", lambda: Downloader(self))
        # process
        self.process = QProcess()
        self.process.readyReadStandardOutput.connect(self._read_output)
        self.process.readyReadStandardError.connect(self._read_errors)
        self.process.finished.connect(self._process_finished)
        self.process.error.connect(self._process_failed)

        # widgets
        self.group0, self.group1 = QGroupBox("BGE"), QGroupBox("Resolutions")
        self.group2, self.group3 = QGroupBox("AntiAlias"), QGroupBox("3DViews")
        self.group4, self.group5 = QGroupBox("Dome mode"), QGroupBox("Misc")
        g0grid, g1vlay = QGridLayout(self.group0), QVBoxLayout(self.group1)
        g5vlay, g4vlay = QVBoxLayout(self.group5), QVBoxLayout(self.group4)
        g2vlay, g3vlay = QVBoxLayout(self.group2), QVBoxLayout(self.group3)

        # group 0 the game engine options
        self.fixedti = QCheckBox("Force frames")
        self.mipmaps = QCheckBox("No MipMaps")
        self.showfps = QCheckBox("Show F.P.S.")
        self.propert = QCheckBox("Debug properties")
        self.profile = QCheckBox("Debug profilings")
        self.materia = QCheckBox("OpenGL Materials")
        self.depreca = QCheckBox("Debug Deprecations")
        self.nosound = QCheckBox("No Audio")
        g0grid.addWidget(self.showfps, 0, 0)
        g0grid.addWidget(self.fixedti, 0, 1)
        g0grid.addWidget(self.propert, 0, 2)
        g0grid.addWidget(self.mipmaps, 0, 3)
        g0grid.addWidget(self.profile, 1, 0)
        g0grid.addWidget(self.materia, 1, 1)
        g0grid.addWidget(self.depreca, 1, 2)
        g0grid.addWidget(self.nosound, 1, 3)

        # group 1 screen resolutions
        self.fullscreen = QCheckBox("FullScreen")
        self.autodetect = QCheckBox("AutoDetect")
        self.width, self.heigt = QComboBox(), QComboBox()
        self.bpp = QComboBox()
        resols = [
            "240", "600", "640", "400", "480", "600", "640", "768", "800",
            "840", "1024", "1080", "1150", "1280", "1680", "1920", "2048"]
        self.width.addItems([str(self.get_half_of_resolution()[0])] + resols)
        self.heigt.addItems([str(self.get_half_of_resolution()[1])] + resols)
        self.bpp.addItems(["32", "16", "8"])
        _container1, _container2 = QWidget(), QWidget()
        _res_lay, _mis_lay = QHBoxLayout(_container1), QHBoxLayout(_container2)
        _res_lay.addWidget(self.width)
        _res_lay.addWidget(QLabel("Pixels Width"))
        _res_lay.addWidget(self.heigt)
        _res_lay.addWidget(QLabel("Pixels Heigth"))
        _mis_lay.addWidget(self.fullscreen)
        _mis_lay.addWidget(self.autodetect)
        _mis_lay.addWidget(self.bpp)
        _mis_lay.addWidget(QLabel("Bits per Pixel"))
        g1vlay.addWidget(_container1)
        g1vlay.addWidget(_container2)

        # group 2 antialiasing
        self.aaa, self.aas = QCheckBox("AntiAliasing"), QSpinBox()
        self.aas.setToolTip("Maximum anti-aliasing samples")
        self.aaa.setChecked(True)
        self.aas.setRange(2, 16)
        self.aas.setValue(16)
        self.aas.setSingleStep(2)
        g2vlay.addWidget(self.aaa)
        g2vlay.addWidget(QLabel("Maximum Samples"))
        g2vlay.addWidget(self.aas)

        # group 3 the 3d stereo view mode
        self.stereos, self.smode = QCheckBox("3D View"), QComboBox()
        self.smode.addItems([
            "NoStereo", "Anaglyph", "SideBySide", "SyncDoubling",
            "3DTVTopBottom", "Interlace", "VInterlace", "HWPageFlip"])
        g3vlay.addWidget(self.stereos)
        g3vlay.addWidget(QLabel("Stereoscopy"))
        g3vlay.addWidget(self.smode)
        g3vlay.addWidget(QLabel("<small><i>Requires 3D<br>capable hardware!"))

        # group 4 the dome view mode
        self.dome, self.dmode = QCheckBox("Dome View"), QComboBox()
        self.dmode.addItems(["Fisheye", "TruncatedFront", "TruncatedRear",
                             "CubeMap", "SphericalPanoramic"])
        self.dangle, self.dtilt = QSpinBox(), QSpinBox()
        self.dangle.setToolTip("Field of view in degrees")
        self.dtilt.setToolTip("Tilt angle in degrees")
        self.dangle.setRange(10, 360)
        self.dangle.setValue(10)
        self.dtilt.setRange(10, 360)
        self.dtilt.setValue(10)
        g4vlay.addWidget(self.dome)
        g4vlay.addWidget(QLabel("Field of view"))
        g4vlay.addWidget(self.dangle)
        g4vlay.addWidget(QLabel("Tilt angle"))
        g4vlay.addWidget(self.dtilt)

        # group 5 miscelaneous stuff
        self.debug, self.log = QCheckBox("Use Debug"), QCheckBox("Save Logs")
        self.chrt, self.ionice = QCheckBox("Slow CPU"), QCheckBox("Slow HDD")
        self.minimi = QCheckBox("Auto Minimize")
        self.embeds = QCheckBox("Wallpaper mode")
        self.chrt.setToolTip("Use Low CPU speed priority (Linux only)")
        self.ionice.setToolTip("Use Low HDD speed priority (Linux only)")
        self.debug.setToolTip("Use BGE Verbose logs,ideal for Troubleshooting")
        self.minimi.setToolTip("Automatically Minimize Launcher after launch")
        self.embeds.setToolTip("Embed Game as interactive Desktop Wallpaper")
        self.minimi.setChecked(True)
        if not sys.platform.startswith('linux'):
            self.chrt.setDisabled(True)
            self.ionice.setDisabled(True)
        g5vlay.addWidget(self.debug)
        g5vlay.addWidget(self.log)
        g5vlay.addWidget(self.chrt)
        g5vlay.addWidget(self.ionice)
        g5vlay.addWidget(self.embeds)
        g5vlay.addWidget(self.minimi)

        # option to show or hide some widgets on the gui
        self.guimode = QComboBox()
        self.guimode.addItems(('Full UX / UI', 'Simple UX / UI'))
        self.guimode.setCurrentIndex(1)
        self._set_guimode()
        self.guimode.setStyleSheet(
            """QComboBox{background:transparent;border:0;
            margin-left:25px;color:gray;text-decoration:underline}""")
        self.guimode.currentIndexChanged.connect(self._set_guimode)

        # buttons from bottom to close or proceed
        self.bt = QDialogButtonBox(self)
        self.bt.setStandardButtons(QDialogButtonBox.Ok |
                                   QDialogButtonBox.Close)
        self.bt.rejected.connect(self.close)
        self.bt.accepted.connect(self.run)

        # container for all groups of widgets
        container = QWidget()
        container_layout = QGridLayout(container)  # Y, X
        container_layout.addWidget(self.guimode, 0, 1)
        container_layout.addWidget(self.group2, 1, 0)
        container_layout.addWidget(self.group3, 2, 0)
        container_layout.addWidget(self.group0, 1, 1)
        container_layout.addWidget(self.group1, 2, 1)
        container_layout.addWidget(self.group4, 1, 2)
        container_layout.addWidget(self.group5, 2, 2)
        container_layout.addWidget(self.bt, 3, 1)
        self.setCentralWidget(container)

    def run(self):
        """Run the main method and run BlenderPlayer."""
        condition = self.autodetect.isChecked() and self.fullscreen.isChecked()
        dome_mode = str(self.dmode.currentText()).lower().strip()
        ster_mode = str(self.smode.currentText()).lower().strip()
        dome_angl, dome_tilt = int(self.dangle.value()), self.dtilt.value()
        show_deprecated = self.depreca.isChecked()
        desktop_win_ids = int(QApplication.desktop().winId())
        command_to_run_blenderplayer = " ".join((
            "ionice --ignore --class 3" if self.ionice.isChecked() else "",
            "chrt --verbose --idle 0" if self.chrt.isChecked() else "",
            "blenderplayer",
            "-d" if self.debug.isChecked() else "",
            "-m {}".format(self.aas.value()) if self.aaa.isChecked() else "",
            "-D mode {}".format(dome_mode) if self.dome.isChecked() else "",
            "-D angle {}".format(dome_angl) if self.dome.isChecked() else "",
            "-D tilt {}".format(dome_tilt) if self.dome.isChecked() else "",
            "-s {}".format(ster_mode) if self.stereos.isChecked() else "",
            "-g noaudio" if self.nosound.isChecked() else "",
            "-g fixedtime=1" if self.fixedti.isChecked() else "",
            "-g nomipmap=1" if self.mipmaps.isChecked() else "",
            "-g show_framerate=1" if self.showfps.isChecked() else "",
            "-g show_properties=1" if self.propert.isChecked() else "",
            "-g show_profile=1" if self.profile.isChecked() else "",
            "-g blender_material=1" if self.materia.isChecked() else "",
            "-g ignore_deprecation_warnings=0" if show_deprecated else "",
            "-f" if self.fullscreen.isChecked() else "-w",
            "0" if condition else str(self.width.currentText()),
            "0" if condition else str(self.heigt.currentText()),
            str(self.bpp.currentText()) if self.fullscreen.isChecked() else "",
            "-i {}".format(desktop_win_ids) if self.embeds.isChecked() else "",
            self.open_game_file(GAME_FILE))).strip()
        log.debug(command_to_run_blenderplayer)
        if self.minimi.isChecked():
            self.showMinimized()
        self.process.start(command_to_run_blenderplayer)

    def open_game_file(self, game_file):
        """Open a Game file."""
        if not os.path.isfile(game_file):
            game_file = str(QFileDialog.getOpenFileName(
                self, __doc__ + "- Open Blender Game", os.path.expanduser("~"),
                "Blender Game Engine file (*.blend)")[0]).strip()
            if game_file and os.path.isfile(game_file):
                return game_file
            else:
                return
        elif game_file.lower().endswith(".blend"):
            return game_file
        elif game_file.lower().endswith(".zip"):
            if not len(PASSWORD):
                pwd = QInputDialog.getText(self, __doc__, "Game SerialKey")[0]
            else:
                pwd = codecs.decode(PASSWORD, "rot13")
            try:
                with ZipFile(game_file, "r") as zipy:
                    zipy.setpassword(str(pwd))
                    # zipy.setpassword(PASSWORD)
                    if zipy.testzip():
                        zipy.extractall()
                        zipy.close()
                        return game_file.replace(".zip", ".blend")
            except Exception as e:
                log.warning(e)

    def _process_finished(self):
        """Finished sucessfully."""
        self.showNormal()
        if self.log.isChecked():
            try:
                with open(GAME_FILE.replace(".blend", ".log"), "w") as _log:
                    _log.write(self._read_output())
                    _log.write(self._read_errors())
            except Exception as e:
                log.warning(e)

    def _read_output(self):
        """Read and return output."""
        return str(self.process.readAllStandardOutput()).strip()

    def _read_errors(self):
        """Read and return errors."""
        return str(self.process.readAllStandardError()).strip()

    def _process_failed(self):
        """Read and return errors."""
        self.showNormal()
        self.statusBar().showMessage(" ERROR: BlenderPlayer Failed ! ")
        return str(self.process.readAllStandardError()).strip().lower()

    def _set_guimode(self):
        """Switch between simple and full UX."""
        for widget in (self.group0, self.group2, self.group3, self.group4,
                       self.group5, self.statusBar(), self.menuBar()):
            widget.hide() if self.guimode.currentIndex() else widget.show()
        self.resize(self.minimumSize()
                    if self.guimode.currentIndex() else self.maximumSize())
        self.center()

    def skin(self, filename=None):
        """Open QSS from filename,if no QSS return None,if no filename ask."""
        if not filename:
            filename = str(QFileDialog.getOpenFileName(
                self, __doc__ + "- Open QSS Skin", os.path.expanduser("~"),
                "CSS Cascading Style Sheet for Qt 5 (*.qss);;All (*.*)")[0])
        if filename and os.path.isfile(filename):
            with open(filename, 'r') as file_to_read:
                text = file_to_read.read().strip()
        if text:
            return text

    def center(self):
        """
        Center the Window on the Current Screen,with Multi-Monitor support.

        >>> MainWindow().center()
        True
        """
        window_geometry = self.frameGeometry()
        mousepointer_position = QApplication.desktop().cursor().pos()
        screen = QApplication.desktop().screenNumber(mousepointer_position)
        centerPoint = QApplication.desktop().screenGeometry(screen).center()
        window_geometry.moveCenter(centerPoint)
        return bool(not self.move(window_geometry.topLeft()))

    def move_to_mouse_position(self):
        """
        Center the Window on the Current Mouse position.

        >>> MainWindow().move_to_mouse_position()
        True
        """
        window_geometry = self.frameGeometry()
        window_geometry.moveCenter(QApplication.desktop().cursor().pos())
        return bool(not self.move(window_geometry.topLeft()))

    def get_half_of_resolution(self):
        """
        Get half of the screen resolution.

        >>> isinstance(MainWindow().get_half_of_resolution(), tuple)
        True
        """
        mouse_pointer_position = QApplication.desktop().cursor().pos()
        screen = QApplication.desktop().screenNumber(mouse_pointer_position)
        widt = QApplication.desktop().screenGeometry(screen).size().width() / 2
        hei = QApplication.desktop().screenGeometry(screen).size().height() / 2
        return (int(widt), int(hei))

    def closeEvent(self, event):
        """Ask to Quit."""
        the_conditional_is_true = QMessageBox.question(
            self, __doc__.title(), 'Quit ?.', QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No) == QMessageBox.Yes
        event.accept() if the_conditional_is_true else event.ignore()


###############################################################################


def main():
    """Main Loop."""
    APPNAME = str(__package__ or __doc__)[:99].lower().strip().replace(" ", "")
    if not sys.platform.startswith("win") and sys.stderr.isatty():
        def add_color_emit_ansi(fn):
            """Add methods we need to the class."""
            def new(*args):
                """Method overload."""
                if len(args) == 2:
                    new_args = (args[0], copy(args[1]))
                else:
                    new_args = (args[0], copy(args[1]), args[2:])
                if hasattr(args[0], 'baseFilename'):
                    return fn(*args)
                levelno = new_args[1].levelno
                if levelno >= 50:
                    color = '\x1b[31m'  # red
                elif levelno >= 40:
                    color = '\x1b[31m'  # red
                elif levelno >= 30:
                    color = '\x1b[33m'  # yellow
                elif levelno >= 20:
                    color = '\x1b[32m'  # green
                elif levelno >= 10:
                    color = '\x1b[35m'  # pink
                else:
                    color = '\x1b[0m'  # normal
                try:
                    new_args[1].msg = color + str(new_args[1].msg) + '\x1b[0m'
                except Exception as reason:
                    print(reason)  # Do not use log here.
                return fn(*new_args)
            return new
        # all non-Windows platforms support ANSI Colors so we use them
        log.StreamHandler.emit = add_color_emit_ansi(log.StreamHandler.emit)
    log.basicConfig(
        level=-1, format="%(levelname)s:%(asctime)s %(message)s", filemode="w",
        filename=os.path.join(gettempdir(), "bge-launcher.log"))
    log.getLogger().addHandler(log.StreamHandler(sys.stderr))
    try:
        os.nice(19)  # smooth cpu priority
        libc = cdll.LoadLibrary('libc.so.6')  # set process name
        buff = create_string_buffer(len(APPNAME) + 1)
        buff.value = bytes(APPNAME.encode("utf-8"))
        libc.prctl(15, byref(buff), 0, 0, 0)
    except Exception as reason:
        log.warning(reason)
    signal.signal(signal.SIGINT, signal.SIG_DFL)  # CTRL+C work to quit app
    application = QApplication(sys.argv)
    application.setApplicationName(__doc__.strip().lower())
    application.setOrganizationName(__doc__.strip().lower())
    application.setOrganizationDomain(__doc__.strip())
    application.setWindowIcon(QIcon.fromTheme("blender"))
    try:
        opts, args = getopt(sys.argv[1:], 'hvt', ('version', 'help', 'tests'))
    except:
        pass
    for o, v in opts:
        if o in ('-h', '--help'):
            print(APPNAME + ''' Usage:
                  -h, --help        Show help informations and exit.
                  -v, --version     Show version information and exit.
                  -t, --tests       Run Unit Tests on DocTests if any.''')
            return sys.exit(0)
        elif o in ('-v', '--version'):
            print(__version__)
            return sys.exit(0)
        elif o in ('-t', '--tests'):
            from doctest import testmod
            testmod(verbose=True, report=True, exclude_empty=True)
            exit(0)
    mainwindow = MainWindow()
    mainwindow.show()
    sys.exit(application.exec_())


if __name__ in '__main__':
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PEP8:OK, LINT:OK, PY3:OK


# metadata
""" BGElauncher """
__version__ = ' 0.0.1 '
__license__ = ' GPLv3+ '
__author__ = ' juancarlos '
__email__ = ' juancarlospaco@gmail.com '
__url__ = 'https://github.com/juancarlospaco/bgelauncher#bgelauncher'


# imports
import codecs
import sys
from getopt import getopt
from os import path
from subprocess import call, check_output
from webbrowser import open_new_tab
from zipfile import ZipFile

from PyQt5.QtCore import QProcess
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QApplication, QCheckBox, QComboBox,
                             QDialogButtonBox, QFileDialog, QGridLayout,
                             QGroupBox, QHBoxLayout, QInputDialog, QLabel,
                             QMainWindow, QMessageBox, QShortcut, QSpinBox,
                             QVBoxLayout, QWidget)

HELP = """<h3>BGElauncher</h3><b>Blender Game Engine Launcher App !</b><br>
Version {}, licence {}<ul><li>Python 3 + Qt 5, single-file, No Dependencies</ul>
DEV: <a href=https://github.com/juancarlospaco>JuanCarlos</a>
""".format(__version__, __license__)
GAME_FILE = "game.blend"
PASSWORD = ""


###############################################################################


def get_blender_version():
    """Try to return Blender version if fails return the default docstring."""
    try:
        ver = str(check_output("blender --version", shell=True).splitlines()[0])
        ver = ver[2:-1].strip().lower()
    except:
        ver = __doc__.strip().lower()
    finally:
        return ver


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__()
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
        windowMenu.addAction("Center", lambda: self.center())
        windowMenu.addAction("To Mouse", lambda: self.move_to_mouse_position())
        helpMenu = self.menuBar().addMenu("&Help")
        helpMenu.addAction("About Qt 5", lambda: QMessageBox.aboutQt(self))
        helpMenu.addAction("About Python 3",
                           lambda: open_new_tab('https://www.python.org'))
        helpMenu.addAction("About" + __doc__,
                           lambda: QMessageBox.about(self, __doc__, HELP))
        helpMenu.addSeparator()
        helpMenu.addAction("Keyboard Shortcut", lambda: QMessageBox.information(
            self, __doc__, "Quit = CTRL+Q"))
        if sys.platform.startswith('linux'):
            helpMenu.addAction("View Source Code",
                               lambda: call('xdg-open ' + __file__, shell=True))
        helpMenu.addAction("View GitHub Repo", lambda: open_new_tab(__url__))

        # process
        self.process = QProcess()
        self.process.readyReadStandardOutput.connect(self._read_output)
        self.process.readyReadStandardError.connect(self._read_errors)
        self.process.finished.connect(self._process_finished)
        self.process.error.connect(self._process_failed)

        # widgets
        self.group0, self.group1 = QGroupBox("B.G.E."), QGroupBox("Resolutions")
        self.group2, self.group3 = QGroupBox("AntiAlias"), QGroupBox("3D Views")
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
        self.width, self.heigt, self.bpp = QComboBox(), QComboBox(), QComboBox()
        resols = ["240", "600", "640", "400", "480", "600", "640", "768", "800",
                  "840", "1024", "1080", "1150", "1280", "1680", "1920", "2048"]
        self.width.addItems(resols)
        self.heigt.addItems(resols)
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
        self.chrt.setToolTip("Use Low CPU speed priority (Linux only)")
        self.ionice.setToolTip("Use Low HDD speed priority (Linux only)")
        self.debug.setToolTip("Use BGE Verbose logs, ideal for Troubleshooting")
        self.minimi.setToolTip("Automatically Minimize Launcher after launch")
        self.minimi.setChecked(True)
        if not sys.platform.startswith('linux'):
            self.chrt.setDisabled(True)
            self.ionice.setDisabled(True)
        g5vlay.addWidget(self.debug)
        g5vlay.addWidget(self.log)
        g5vlay.addWidget(self.chrt)
        g5vlay.addWidget(self.ionice)
        g5vlay.addWidget(self.minimi)

        # option to show or hide some widgets on the gui
        self.guimode = QComboBox()
        self.guimode.addItems(('Full UX / UI', 'Simple UX / UI'))
        self.guimode.setCurrentIndex(1)
        self._set_guimode()
        self.guimode.setStyleSheet("""QComboBox{background:transparent;border:0;
            margin-left:25px;color:gray;text-decoration:underline}""")
        self.guimode.currentIndexChanged.connect(self._set_guimode)

        # buttons from bottom to close or proceed
        self.bt = QDialogButtonBox(self)
        self.bt.setStandardButtons(QDialogButtonBox.Ok | QDialogButtonBox.Close)
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
        dome_angl, dome_tilt = int(self.dangle.value()), int(self.dtilt.value())
        show_deprecated = self.depreca.isChecked()
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
            self.open_game_file(GAME_FILE))).strip()
        print(command_to_run_blenderplayer)
        if self.minimi.isChecked():
            self.showMinimized()
        self.process.start(command_to_run_blenderplayer)

    def open_game_file(self, game_file):
        if not path.isfile(game_file):
            game_file = str(QFileDialog.getOpenFileName(
                self, __doc__ + " - Open Blender Game ! ", path.expanduser("~"),
                "Blender Game Engine file (*.blend)")[0]).strip()
            if game_file and path.isfile(game_file):
                return game_file
            else:
                return
        elif game_file.lower().endswith(".blend"):
            return game_file
        elif game_file.lower().endswith(".zip"):
            if not len(PASSWORD):
                pwd = QInputDialog.getText(self, __doc__, "Game Serial Key")[0]
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
                print(e)

    def _process_finished(self):
        """finished sucessfully"""
        self.showNormal()
        if self.log.isChecked():
            try:
                with open(GAME_FILE.replace(".blend", ".log"), "w") as _log:
                    _log.write(self._read_output())
                    _log.write(self._read_errors())
            except Exception as e:
                print(e)

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
        """Switch between simple and full UX"""
        for widget in (self.group0, self.group2, self.group3, self.group4,
                       self.group5, self.statusBar(), self.menuBar()):
            widget.hide() if self.guimode.currentIndex() else widget.show()
        self.resize(self.minimumSize()
                    if self.guimode.currentIndex() else self.maximumSize())
        self.center()

    def center(self):
        """Center the Window on the Current Screen,with Multi-Monitor support"""
        window_geometry = self.frameGeometry()
        mousepointer_position = QApplication.desktop().cursor().pos()
        screen = QApplication.desktop().screenNumber(mousepointer_position)
        centerPoint = QApplication.desktop().screenGeometry(screen).center()
        window_geometry.moveCenter(centerPoint)
        self.move(window_geometry.topLeft())

    def move_to_mouse_position(self):
        """Center the Window on the Current Mouse position"""
        window_geometry = self.frameGeometry()
        window_geometry.moveCenter(QApplication.desktop().cursor().pos())
        self.move(window_geometry.topLeft())

    def closeEvent(self, event):
        ' Ask to Quit '
        the_conditional_is_true = QMessageBox.question(
            self, __doc__.title(), 'Quit ?.', QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No) == QMessageBox.Yes
        event.accept() if the_conditional_is_true else event.ignore()


###############################################################################


def main():
    ' Main Loop '
    application = QApplication(sys.argv)
    application.setApplicationName(__doc__.strip().lower())
    application.setOrganizationName(__doc__.strip().lower())
    application.setOrganizationDomain(__doc__.strip())
    application.setWindowIcon(QIcon.fromTheme("blender"))
    try:
        opts, args = getopt(sys.argv[1:], 'hv', ('version', 'help'))
    except:
        pass
    for o, v in opts:
        if o in ('-h', '--help'):
            print(''' Usage:
                  -h, --help        Show help informations and exit.
                  -v, --version     Show version information and exit.''')
            return sys.exit(1)
        elif o in ('-v', '--version'):
            print(__version__)
            return sys.exit(1)
    mainwindow = MainWindow()
    mainwindow.show()
    sys.exit(application.exec_())


if __name__ in '__main__':
    main()

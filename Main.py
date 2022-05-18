#!/usr/bin/env python
'''
Copyright © 2022 Echedey Luis
This work is free. You can redistribute it and/or modify it under the
terms of the Do What The Fuck You Want To Public License, Version 2,
as published by Sam Hocevar. See the COPYING file for more details.

Small graphical solution to make QR codes easily with logos embedded
'''
__author__ = "Echedey Luis Álvaerz"
__copyright__ = "Copyright 2022, Echedey Luis Álvarez"
__credits__ = ["Echedey Luis Álvarez"]
__license__ = "WTFPL"
__version__ = "0.1.0"
__status__ = "Prototype"

import sys
import errno
import tomli, tomli_w
import qrcode

from PIL import Image

from os.path import exists

from datetime import datetime

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtWidgets import QApplication, QWidget, QGridLayout, QHBoxLayout, QVBoxLayout, QLineEdit, QButtonGroup, QPushButton, QToolButton, QLabel
from PyQt6.QtGui import QPixmap, QIcon, QImage, QCloseEvent

class customQR_widgetApp(QWidget):
    paths = {
        'usedLogos': 'saved',
        'config': 'qrGenConfig.toml'
    }
    usedLogos = []

    def __init__(self):
        super().__init__()
        self.cf = QRApp_config(self.paths['config'])
        self.initEnv()
        self.initUI()
        return

    def initEnv(self):
        self.usedLogos = self.cf.getConf()['logo-history']
        return

    
    def initUI(self):
        self.setWindowTitle("QR with logos generator")

        # Main layout of app
        parentLayout = QVBoxLayout()

        title = QLabel()
        title.setText('# QR Code Generator with centered logo')
        title.setTextFormat(Qt.TextFormat.MarkdownText)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Where almost all widgets are
        lowerSegment = QHBoxLayout()

        # Left column, for QR input data
        leftColumn = QGridLayout()

        uriLabel = QLabel()
        uriLabel.setTextFormat(Qt.TextFormat.PlainText)
        uriLabel.setAlignment(Qt.AlignmentFlag.AlignRight)
        uriLabel.setText('Content')
        self.qrContent = QLineEdit()

        logoLabel = QLabel()
        logoLabel.setTextFormat(Qt.TextFormat.PlainText)
        logoLabel.setAlignment(Qt.AlignmentFlag.AlignRight)
        logoLabel.setText('Logo path')
        self.logoInput = QLineEdit()

        # Used logos grid
        logosGrid = QGridLayout()
        self.logosButtons = QButtonGroup()
        for logoEntry in self.usedLogos:
            button = QToolButton()
            button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
            button.setIcon(QIcon(logoEntry))
            button.setIconSize(QSize(32,32))
            button.setMinimumSize(QSize(32,32))
            button.setCheckable(True)
            button.clicked.connect(lambda _,staticEntry=logoEntry: self.logoClicked(staticEntry) )
            self.logosButtons.addButton(button)
            logosGrid.addWidget(button)
        self.logosButtons.setExclusive(True)
        # !Used logos grid

        leftColumn.addWidget(uriLabel,0,0)
        leftColumn.addWidget(self.qrContent,0,1)
        leftColumn.addWidget(logoLabel,1,0)
        leftColumn.addWidget(self.logoInput,1,1)
        leftColumn.addLayout(logosGrid,2,0,1,-1)
        leftColumn.setAlignment(Qt.AlignmentFlag.AlignTop)
        # !Left column, for QR input data

        # Right column, for QR output
        rightColumn= QGridLayout()

        self.outputImg = QLabel()
        self.outputImg.setFixedSize(QSize(300,300))
        self.doQRPixmap() # Initialize outputImg

        self.generateButton = QPushButton('Make QR')
        self.generateButton.clicked.connect(self.doQRPixmap)

        self.saveButton = QPushButton('Save QR')
        self.saveButton.clicked.connect(self.saveQR)

        rightColumn.addWidget(self.generateButton,1,0)
        rightColumn.addWidget(self.saveButton,1,1)
        rightColumn.addWidget(self.outputImg,0,0,1,-1)
        rightColumn.addWidget(QLabel('Paths are automatically added to used logos'),2,0,1,-1)
        # !Right column, for QR output

        lowerSegment.addLayout(leftColumn)
        lowerSegment.addLayout(rightColumn)
        # !Where almost all widgets are

        parentLayout.addWidget(title)
        parentLayout.addLayout(lowerSegment)
        self.setLayout(parentLayout)
        # !Main layout of app 
        return

    def logoClicked(self, entry):
        self.logoInput.setText(entry)
        self.doQRPixmap()
        return

    def doQRPixmap(self):
        qrContent= self.qrContent.text()
        logoPath = self.logoInput.text()
        if  qrContent == '':
            self.qr = QImage(QSize(1000,1000), QImage.Format.Format_ARGB32)
            self.qr.fill(Qt.GlobalColor.gray)
        elif exists(logoPath) or logoPath == '':
            # This workaround is thanks to Win10
            # See https://stackoverflow.com/questions/34697559/pil-image-to-qpixmap-conversion-issue
            im = makeCustomQR(data=qrContent, imagePath=logoPath)
            im2 = im.convert("RGBA")
            data = im2.tobytes("raw", "BGRA")
            self.qr = QImage(data, im.width, im.height, QImage.Format.Format_ARGB32)
            self.cf.addToHistory(logoPath)
        self.outputImg.setPixmap(QPixmap.fromImage(self.qr.scaled(QSize( 300, 300))))
        return
    
    def saveQR(self):
        timestamp = datetime.now().replace(microsecond=0).isoformat()+'.png'
        self.qr.save(timestamp.replace(':','-')) # Replace ':' so it can be a valid filename
    
    def closeEvent(self, a0: QCloseEvent) -> None:
        self.cf.saveConfig()
        return super().closeEvent(a0)

class QRApp_config:
    def __init__(self, path: str) -> None:
        self._path = path
        if exists(self._path):
            self.readConfig()
            self._cf['logo-history'] = self.sanitizeHistory()
        else:
            self.createVoidConfig()
    def createVoidConfig(self) -> None: # Creates a default configuration file
        self._cf = {'logo-history': []}
        self.saveConfig()
    def saveConfig(self) -> None: # Saves current config to the TOML config file
        self._cf['logo-history'] = self.sanitizeHistory()
        with open(self._path, 'wb') as cfFile:
            tomli_w.dump(self._cf, cfFile)
    def readConfig(self) -> None: # Gets config dict from TOML file. If not valid, new config is created
        with open(self._path, 'rb') as cfFile:
            self._cf = tomli.load(cfFile)
        if 'logo-history' not in self._cf.keys():
            self.createVoidConfig()
    def sanitizeHistory(self) -> list: # Checks all paths do exist, else they are deleted
        # Might be considered unwanted behaviour, but how do I put the icons then?
        return [logoPath for logoPath in self._cf['logo-history'] if exists(logoPath)] 
    def addToHistory(self, path: str) -> None: # When we add a path, it is the last one used so insert at index 0
        history = self._cf['logo-history']
        if path in history:
            history.remove(path)
        history.insert(0, path)
        self._cf['logo-history'] = history
    def getConf(self) -> dict: # Accessor for the config dict
        return self._cf

# Wrapper to a function that makes the QR with the logo
# Copied and modified without shame from https://www.geeksforgeeks.org/how-to-generate-qr-codes-with-a-custom-logo-using-python/
# Credits to pavanpatel3684 @ https://auth.geeksforgeeks.org/user/pavanpatel3684/articles
def makeCustomQR(data: str, imagePath: str, fgColor='black', bkColor='white', baseWidth=5000, logoPercent=0.3):
    QRcode = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        border=0,
        image_factory=None,
        mask_pattern=None
    )

    QRcode.add_data(data)
    QRcode.make()

    QRimg = QRcode.make_image(fill_color=fgColor, back_color=bkColor).convert('RGBA').resize((baseWidth,baseWidth), Image.Resampling.NEAREST)

    if imagePath:
        logo = Image.open(imagePath)
        # set size of logo
        logo = logo.resize(
            (int(QRimg.size[0]*logoPercent),
            int(QRimg.size[1]*logoPercent)),
            Image.Resampling.NEAREST
        ).convert('RGBA')
        # set size of QR code
        pos = (
            (QRimg.size[0] - logo.size[0]) // 2,
            (QRimg.size[1] - logo.size[1]) // 2
        )
        QRimg.alpha_composite(logo, pos)

    return QRimg

# UNUSED Wrapper to a function that makes the QR with the logo. Just for reference, also is a WIP
# Copied and modified without shame from https://medium.com/@insecurecoders/how-to-generate-qr-codes-with-a-custom-logo-for-a-1000-links-in-less-than-a-minute-python-32fef17a8b3e
def makeCustomQR2(data: str, imagePath: str, fgColor='black', bkColor='white', basewidth=100):
    Logo = Image.open(imagePath)

    qr = qrcode.QRCode(
        version=12,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=1
    )

    qr.add_data(data)
    qr.make()
    # You need to convert the image into RGB in order to use it
    img_qr_big = qr.make_image(fill_color=fgColor, back_color=bkColor).convert('RGB')

    # Where to place the logo within the QR Code
    pos = ((img_qr_big.size[0] - Logo.size[0]) // 2, (img_qr_big.size[1] - Logo.size[1]) // 2)
    img_qr_big.paste(Logo, pos)

    return img_qr_big

if __name__ == "__main__":
    app = QApplication(sys.argv)
    customQR_widgetApp = customQR_widgetApp()
    customQR_widgetApp.show()
    sys.exit(app.exec())

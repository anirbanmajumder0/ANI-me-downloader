# coding:utf-8
import json,time
from PyQt5.QtCore import Qt, QRect, QRectF, QUrl, pyqtSignal
from PyQt5.QtGui import  QPainter, QColor, QPainterPath,  QDesktopServices, QFont,QPalette
from PyQt5.QtWidgets import (QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame,
                             QWidget, QVBoxLayout, QLabel, QSizePolicy, QWidget, QFrame)
from qfluentwidgets import (FluentIcon, FlowLayout, PushButton,
                            PrimaryToolButton)
from .base_interface import BaseInterface, ScrollArea

from ..common.style_sheet import StyleSheet
from ..common.utils import get_img
from ..common.config import cfg

class ImageLabel(QLabel):
    delete_signal = pyqtSignal(int)

    def __init__(self, anime, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.anime = anime
        self.setMouseTracking(True)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

    def paintEvent(self, event):
        #TODO make the rect slyanted
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw the image with rounded corners
        rect = QRect(0, 0, self.width(), self.height())
        rectf = QRectF(0, 0, self.width(), self.height())
        path = QPainterPath()
        path.addRoundedRect(rectf, 10, 10)
        painter.setClipPath(path)
        if self.pixmap():
            painter.drawPixmap(rect, self.pixmap())

        # Draw a black rectangle at the bottom of the image
        bottom_rect_height = int(self.height() * 0.08)
        bottom_rect = QRect(0, self.height() - bottom_rect_height, self.width(), bottom_rect_height)
        painter.fillRect(bottom_rect, QColor('black'))

        # Set the font and pen for drawing text
        font = painter.font()
        font.setPixelSize(10)
        painter.setFont(font)
        painter.setPen(QColor('white'))

        # Draw the current airing episode (if anime is airing)
        if self.anime['airing']:
            current_episode_text = f"A{self.anime['last_aired_episode']}"
            current_episode_rect = QRect(0, self.height() - bottom_rect_height + 2, 25, bottom_rect_height - 4)
            painter.fillRect(current_episode_rect, QColor('green'))
            painter.drawText(current_episode_rect, Qt.AlignCenter, current_episode_text)

        # Draw the number of downloaded episodes
        downloaded_episodes_text = f"D{len(self.anime['episodes_downloaded'])}"
        downloaded_episodes_rect = QRect(self.width()-50, self.height() - bottom_rect_height + 2, 25, bottom_rect_height - 4)
        painter.fillRect(downloaded_episodes_rect, QColor('blue'))
        painter.drawText(downloaded_episodes_rect, Qt.AlignCenter, downloaded_episodes_text)

        # Draw the total number of episodes
        total_episodes_text = f"T{self.anime['total_episodes']}"
        total_episodes_rect = QRect(self.width()-25, self.height() - bottom_rect_height + 2, 25, bottom_rect_height - 4)
        painter.fillRect(total_episodes_rect, QColor('grey'))
        painter.drawText(total_episodes_rect, Qt.AlignCenter, total_episodes_text)

    def enterEvent(self, event):
        style = """
            QLabel {
                color: white;
                qproperty-alignment: 'AlignCenter';
                border-radius: 10px;
            };
        """
        style2=f"background-color: {cfg.themeColor.value.name()};"
        delete_button = PrimaryToolButton(FluentIcon.DELETE)
        delete_button.clicked.connect(self.on_delete_button_clicked)
        if self.anime['airing']:
            current_time = int(time.time())
            time_difference = self.anime['next_eta'] - current_time
            days = time_difference // (24 * 3600)
            time_difference = time_difference % (24 * 3600)
            hours = time_difference // 3600
            time_difference %= 3600
            minutes = time_difference // 60
            next_air= QLabel(f"Next Airing episode: {self.anime['last_aired_episode']+1}")
            time_left = QLabel(f"Time Left: {days} days {hours} hrs" if days else f"Time Left: {hours} hrs {minutes} mins")
        ep_downloaded = QLabel(f"Episodes Downloaded: {len(self.anime['episodes_downloaded'])}")
        total_ep = QLabel(f"Total Episodes: {self.anime['total_episodes']}")

        self.layout.addWidget(delete_button, alignment=Qt.AlignTop | Qt.AlignRight)
        labels=[next_air,time_left,ep_downloaded,total_ep] if self.anime['airing'] else [ep_downloaded,total_ep]
        for label in labels:
            label.setMinimumHeight(30)
            label.setMaximumHeight(30)
            self.layout.addWidget(label, alignment=Qt.AlignTop)

        self.layout.setSpacing(5)
        self.setStyleSheet(style+style2)


    def leaveEvent(self, event):
        self.setStyleSheet("background-color: transparent;")

        #remove all labels
        labels = self.findChildren(QLabel)
        for label in labels:
            label.deleteLater()

        # Remove delete button
        delete_button = self.findChild(PrimaryToolButton)
        if delete_button:
            delete_button.deleteLater()

    def on_delete_button_clicked(self):
        self.delete_signal.emit(self.anime['id'])


class LibraryInterface(BaseInterface):
    """ Library interface """

    deleteSignal = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        scroll_area = ScrollArea()
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.vBoxLayout.addWidget(scroll_area)
        grid_widget = QFrame()
        self.grid_layout = FlowLayout(self, needAni=True)
        grid_widget.setLayout(self.grid_layout)
        scroll_area.setWidget(grid_widget)
        scroll_area.setWidgetResizable(True)

        self.vBoxLayout.setAlignment(Qt.AlignTop)
        self.vBoxLayout.setContentsMargins(2, 2, 0, 0)

        StyleSheet.LIBRARY_INTERFACE.apply(self)

        with open('data/anime_file.json', 'r') as f:
            self.anime_data = json.load(f)

        self.img_size = (164, 240)
        self.update_grid()

    def update_grid(self):
        """ Update the grid layout """

        while self.grid_layout.count():
            widget = self.grid_layout.takeAt(0)
            if widget:
                widget.setParent(None)
                widget.deleteLater()

        if not self.anime_data:
            title_label = QLabel("Add Anime from Search to see here")
            title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #fff; font-style: italic;")
            title_label.setAlignment(Qt.AlignCenter)
            self.grid_layout.addWidget(title_label)

        for anime in self.anime_data:
            # Create a vertical layout for each grid cell
            cell_widget = QWidget()
            cell_layout = QVBoxLayout()
            cell_widget.setLayout(cell_layout)
            cell_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            self.grid_layout.addWidget(cell_widget)

            # Create a label for the image
            image_label = ImageLabel(anime)
            image_label.setFixedSize(self.img_size[0], self.img_size[1])
            image_label.setStyleSheet("background-color: transparent;")
            image_label.delete_signal.connect(self.on_delete_signal)
            cell_layout.addWidget(image_label, alignment=Qt.AlignCenter)
            # Load the image from the URL
            url = anime['img']
            self.load_img(url, image_label)

            # Create a label for the title
            name = anime['name'] if len(anime['name']) <= 28 else anime['name'][:28] + '...'
            title_label = QLabel(name)
            title_label.setStyleSheet("font-size: 10px; font-weight: bold; color: #fff;")
            title_label.setAlignment(Qt.AlignCenter)
            cell_layout.addWidget(title_label)


            # Create a horizontal layout for the buttons
            button_layout = QHBoxLayout()
            cell_layout.addLayout(button_layout)

            # Create a button for watching online
            font = QFont()
            font.setPointSize(8)
            watch_online_button = PushButton('Watch Online')
            watch_online_button.setFont(font)
            watch_online_button.clicked.connect(lambda checked, url=anime['watch_url']: self.on_watch_online_button_clicked(url))
            button_layout.addWidget(watch_online_button)

            # Create a button for watching locally
            watch_local_button = PushButton('Watch Local')
            watch_local_button.setFont(font)
            watch_local_button.clicked.connect(lambda checked, path=anime['output_dir']: self.on_watch_local_button_clicked(path))
            button_layout.addWidget(watch_local_button)

    def load_img(self, url, label):
        pixmap = get_img(url)
        scaled_pixmap = pixmap.scaled(self.img_size[0], self.img_size[1])
        label.setPixmap(scaled_pixmap)

    def on_watch_online_button_clicked(self, url):
        QDesktopServices.openUrl(QUrl(url))

    def on_watch_local_button_clicked(self, path):
        QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def add_anime(self, anime):
        self.anime_data.insert(0, anime)
        self.update_grid()


    def on_delete_signal(self, id):
        self.anime_data = [anime for anime in self.anime_data if anime['id'] != id]
        self.update_grid()
        self.deleteSignal.emit(id)
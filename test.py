import os
import sys
import random
import ctypes
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QPointF, QEasingCurve, QRectF # type: ignore
from PyQt5.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QGraphicsTextItem, QGraphicsObject, QSystemTrayIcon, QMenu, QAction # type: ignore
from PyQt5.QtGui import QFont, QColor, QBrush, QPainter, QIcon # type: ignore
import pygame # type: ignore

def resource_path(relative_path):
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
pygame.mixer.init()
pygame.mixer.music.load(resource_path("music.mp3"))
pygame.mixer.music.play(loops=-1)

GWL_EXSTYLE = -20
WS_EX_TRANSPARENT = 0x00000020
WS_EX_LAYERED = 0x00080000
def make_window_click_through(hwnd):
    exStyle = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    exStyle |= WS_EX_LAYERED | WS_EX_TRANSPARENT
    ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, exStyle)

class HeartItem(QGraphicsTextItem):
    def __init__(self, text, font_size=30):
        super().__init__(text)
        font = QFont("Arial", font_size)
        self.setFont(font)
        self.setDefaultTextColor(QColor("red"))
        self.setOpacity(1.0)

class ParticleItem(QGraphicsObject):
    def __init__(self, size, color, parent=None):
        super().__init__(parent)
        self._size = size
        self._color = color
        self.setOpacity(1.0)
    
    def boundingRect(self):
        return QRectF(0, 0, self._size, self._size)
    
    def paint(self, painter, option, widget):
        painter.setBrush(QBrush(self._color))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(0, 0, self._size, self._size)

class FloatingHeartsView(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setStyleSheet("background: transparent;")
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scene = QGraphicsScene(self)
        self.scene.setBackgroundBrush(Qt.transparent)
        self.setScene(self.scene)
        self.showFullScreen()
        self.scene.setSceneRect(0, 0, self.width(), self.height())
    
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.add_heart)
        self.timer.start(500)
        self.fireworks_timer = QTimer(self)
        self.fireworks_timer.timeout.connect(self.random_fireworks)
        self.fireworks_timer.start(2000) 
    
    def add_heart(self):
        rect = self.scene.sceneRect()
        x = random.uniform(0, rect.width() - 30)
        y = rect.height()
        font_size = random.randint(20, 40)
        heart = HeartItem("❤", font_size)
        heart.setPos(x, y)
        self.scene.addItem(heart)
        
        duration = 5000
        anim = QPropertyAnimation(heart, b'pos')
        anim.setDuration(duration)
        anim.setStartValue(QPointF(x, y))
        anim.setEndValue(QPointF(x, -50))
        anim.setEasingCurve(QEasingCurve.Linear)
        anim.start()
        heart.anim = anim
        
        opacity_anim = QPropertyAnimation(heart, b'opacity')
        opacity_anim.setDuration(duration)
        opacity_anim.setStartValue(1.0)
        opacity_anim.setEndValue(0.0)
        opacity_anim.start()
        heart.opacity_anim = opacity_anim
        opacity_anim.finished.connect(lambda: self.scene.removeItem(heart))
    
    def add_fireworks(self, x, y):
        num_particles = 50 
        for _ in range(num_particles):
            size = random.randint(4, 10)
            color = QColor(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            particle = ParticleItem(size, color)
            particle.setPos(x, y)
            self.scene.addItem(particle)
            dx = random.uniform(-120, 120)
            dy = random.uniform(-120, 120)
            pos_anim = QPropertyAnimation(particle, b'pos')
            pos_anim.setDuration(1500)
            pos_anim.setStartValue(QPointF(x, y))
            pos_anim.setEndValue(QPointF(x + dx, y + dy))
            pos_anim.setEasingCurve(QEasingCurve.OutQuad)
            pos_anim.start()
            particle.pos_anim = pos_anim
            
            opacity_anim = QPropertyAnimation(particle, b'opacity')
            opacity_anim.setDuration(1500)
            opacity_anim.setStartValue(1.0)
            opacity_anim.setEndValue(0.0)
            opacity_anim.start()
            particle.opacity_anim = opacity_anim
            opacity_anim.finished.connect(lambda p=particle: self.scene.removeItem(p))
    
    def random_fireworks(self):
        rect = self.scene.sceneRect()
        x = random.uniform(0, rect.width())
        y = random.uniform(0, rect.height())
        self.add_fireworks(x, y)

class FloatingHeartsApp(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self.view = FloatingHeartsView()
        self.setup_tray_icon()
    
    def setup_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(QIcon(resource_path("icon.ico")), self)
        self.tray_icon.setToolTip("App")
        tray_menu = QMenu()
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.exit_app)
        tray_menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
    
    def exit_app(self):
        self.tray_icon.hide()
        self.quit()

if __name__ == "__main__":
    app = FloatingHeartsApp(sys.argv)
    hwnd = int(app.view.winId())
    try:
        make_window_click_through(hwnd)
    except Exception as e:
        print("Error setting click-through:", e)
    sys.exit(app.exec_())

import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

###对话
from deepseekclient import ChatApp, myFont

class DesktopPet(QWidget):
    def __init__(self):
        super().__init__()
        # 显示初始化
        self.scale_factor = 1.0
        self.original_size = QSize()
        self.curpath = "./doroimg/dorolay.gif"
        self.initUI()

        #chat
        self.ai_window = None
        
    def initUI(self):
        # 窗口设置
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 创建主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 创建标签显示GIF
        self.label = QLabel(self)
        self.label.setScaledContents(True)
        self.movie = QMovie("./doroimg/dorolay.gif") 
        self.label.setMovie(self.movie)
        layout.addWidget(self.label)
        
        # 启动动画
        self.movie.start()
        
        # 设置窗口大小与GIF匹配
        self.resize(self.movie.scaledSize())
        
        # 初始化拖动变量
        self.dragging = False
        self.offset = QPoint()

        # 使用 QPixmap 获取 GIF 的原始尺寸
        pixmap = QPixmap(self.movie.fileName())
        if not pixmap.isNull():
            self.original_size = pixmap.size()
        else:
            # 如果无法加载 QPixmap，则使用第一帧的尺寸
            self.movie.jumpToFrame(0)  # 跳到第一帧
            self.original_size = self.movie.currentImage().size()

        self.resize(int(self.original_size.width() * self.scale_factor),
                    int(self.original_size.height() * self.scale_factor))
        
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.offset = event.pos()
            self.changeGIF("./doroimg/dorodagun.gif")
            
    def mouseMoveEvent(self, event: QMouseEvent):
        if self.dragging:
            self.move(event.globalPos() - self.offset)
            
    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.changeGIF(self.curpath)

    def wheelEvent(self, event):
        # if event.modifiers() & Qt.ControlModifier:
        # if event.modifiers():
            delta = event.angleDelta().y()
            if delta > 0:
                self.zoom_in()
            else:
                self.zoom_out()
            event.accept()
        # else:
        #     event.ignore()

    def zoom_in(self):
        self.scale_factor *= 1.05
        self.scale_factor = min(self.scale_factor, 5.0)
        self.update_size()

    def zoom_out(self):
        self.scale_factor *= 0.95
        self.scale_factor = max(self.scale_factor, 0.2)
        self.update_size()

    def zoom_def(self):
        self.scale_factor = 1.0
        self.update_size()

    def update_size(self):
        new_width = int(self.original_size.width() * self.scale_factor)
        new_height = int(self.original_size.height() * self.scale_factor)
        self.resize(new_width, new_height)
        self.label.setFixedSize(new_width, new_height)
        self.label.update()  # ✅ 强制更新 QLabel  
        
            
    def contextMenuEvent(self, event):
        # 创建右键菜单
        menu = QMenu(self)

        zoom_in_action = QAction("放大", self)
        zoom_in_action.triggered.connect(self.zoom_in)

        zoom_out_action = QAction("缩小", self)
        zoom_out_action.triggered.connect(self.zoom_out)

        zoom_def_action = QAction("默认", self)
        zoom_def_action.triggered.connect(self.zoom_def)

        show_ai = QAction("聊天", self)
        show_ai.triggered.connect(self.show_deepseek_window)

        change_gif = QAction("更换动画", self)
        change_gif.triggered.connect(self.OnclickchangeGIF)

        exit_action = QAction("退出", self)
        exit_action.triggered.connect(lambda: sys.exit())


        menu.addAction(zoom_in_action)
        menu.addAction(zoom_out_action)
        menu.addAction(zoom_def_action)
        menu.addSeparator()
        menu.addAction(show_ai)
        menu.addAction(change_gif)
        menu.addSeparator()
        menu.addAction(exit_action)
        
        # 在鼠标位置显示菜单
        menu.exec_(QCursor.pos())
        
    def OnclickchangeGIF(self):
        # 弹出文件对话框，让用户选择新的GIF文件
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "选择GIF文件",
            "./doroimg",
            "GIF Files (*.gif)"
        )
        self.curpath = filename
        self.changeGIF(filename)
        
    def changeGIF(self, filename):
        if filename:
            try:
                # 停止当前动画
                self.movie.stop()
                # 创建新的QMovie实例
                self.movie = QMovie(filename)
                # 使用 QPixmap 获取新 GIF 的原始尺寸
                pixmap = QPixmap(filename)
                if not pixmap.isNull():
                    self.original_size = pixmap.size()
                else:
                    self.movie.jumpToFrame(0)
                    self.original_size = self.movie.currentImage().size()

                # 设置新的动画到标签上
                self.label.setMovie(self.movie)
                self.movie.start()

                # 调整窗口大小以匹配新 GIF 的尺寸
                self.resize(int(self.original_size.width() * self.scale_factor),
                            int(self.original_size.height() * self.scale_factor))

            except Exception as e:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.critical(self, "错误", f"无法加载GIF文件：{str(e)}")

    def show_deepseek_window(self):
        if not self.ai_window:
            self.ai_window = ChatApp()
        self.ai_window.show()
    

if __name__ == '__main__':
    app = QApplication(sys.argv)
    font = QFont(myFont().getFont(), 13)
    app.setFont(font)
    pet = DesktopPet()
    pet.show()
    sys.exit(app.exec_())
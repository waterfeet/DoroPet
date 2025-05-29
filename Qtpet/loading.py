from math import sin, cos, pi
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import sys

class LoadingWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.initUI()

    def initUI(self):
        # 创建主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 创建标签显示GIF
        self.label = QLabel(self)
        self.label.setScaledContents(True)
        self.movie = QMovie("./doroimg/load.gif") 
        self.label.setMovie(self.movie)
        layout.addWidget(self.label)
        
        # 启动动画
        self.movie.start()
        
        # 设置窗口大小与GIF匹配
        self.resize(self.movie.scaledSize())

        self.setFixedSize(100, 100)

        #   QVariantAnimation实现加载动画
        # self.animation = QVariantAnimation(
        #     self,
        #     startValue=0,
        #     endValue=100,
        #     duration=1200,
        #     valueChanged=self.update
        # )
        # self.animation.setLoopCount(-1)
        # self.animation.start()

    def paintEvent(self, event):
        pass
        # painter = QPainter(self)
        # painter.setRenderHint(QPainter.Antialiasing)
        
        # # 获取动画进度
        # progress = self.animation.currentValue() / 100
        
        # # 定义爪子的基本参数
        # paw_center = QPointF(self.width()/2, self.height()*0.7)
        # base_size = min(self.width(), self.height()) * 0.3
        
        # # 绘制爪垫
        # self.drawPawPad(painter, paw_center, base_size, progress)
        
        # # 绘制脚趾
        # self.drawToes(painter, paw_center, base_size, progress)
        
        # # 添加光效
        # self.drawHighlights(painter, paw_center, base_size, progress)

    def drawPawPad(self, painter, center, size, progress):
        # 创建渐变色背景
        gradient = QRadialGradient(center, size*1.5)
        gradient.setColorAt(0, QColor("#FFD6E8"))
        gradient.setColorAt(1, QColor("#FFA4C7"))
        painter.setBrush(gradient)
        
        # 绘制主爪垫
        paw_rect = QRectF(
            center.x() - size*0.8,
            center.y() - size*0.6,
            size*1.6,
            size*1.2
        )
        painter.drawRoundedRect(paw_rect, 30, 30, Qt.RelativeSize)
        
        # 绘制肉垫高光
        highlight = QPainterPath()
        highlight.addEllipse(
            center.x() - size*0.3,
            center.y() - size*0.3,
            size*0.6,
            size*0.6
        )
        painter.setOpacity(0.3 * (1 + sin(progress * 2 * pi)) / 2)
        painter.fillPath(highlight, Qt.white)
        painter.setOpacity(1)

    def drawToes(self, painter, center, size, progress):
        # 脚趾位置参数
        toe_positions = [
            (-0.6, -0.8), (0, -1), (0.6, -0.8),
            (-0.4, -0.3), (0.4, -0.3)
        ]
        
        for i, (dx, dy) in enumerate(toe_positions):
            # 计算脚趾位置
            offset_x = center.x() + dx * size
            offset_y = center.y() + dy * size
            
            # 计算动画效果
            phase = (i * 0.3 + progress) % 1
            scale = 0.8 + 0.2 * (1 - abs(sin(phase * pi)))
            
            # 设置笔触
            painter.setPen(QPen(QColor("#FF69B4"), 2))
            
            # 创建脚趾渐变
            gradient = QRadialGradient(offset_x, offset_y, size*0.3)
            gradient.setColorAt(0, QColor("#FFFFFF"))
            gradient.setColorAt(1, QColor("#FFB6C1"))
            
            painter.setBrush(gradient)
            
            # 绘制脚趾
            painter.save()
            painter.translate(offset_x, offset_y)
            painter.scale(scale, scale)
            ellipse_rect = QRectF(-size*0.2, -size*0.2, size*0.4, size*0.4)
            painter.drawEllipse(ellipse_rect)
            painter.restore()

    def drawHighlights(self, painter, center, size, progress):
        # 添加动态光点效果
        painter.setPen(Qt.NoPen)
        painter.setBrush(Qt.white)
        
        # 光点位置计算
        highlight_x = center.x() + size * 0.4 * cos(progress * 2 * pi)
        highlight_y = center.y() - size * 0.5 + size * 0.2 * sin(progress * 3 * pi)
        
        # 绘制闪烁光点
        painter.setOpacity(0.5 + 0.5 * sin(progress * 4 * pi))
        painter.drawEllipse(
            QPointF(highlight_x, highlight_y),
            size*0.05, size*0.05
        )
        painter.setOpacity(1)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = LoadingWidget()
    window.show()
    sys.exit(app.exec_())        
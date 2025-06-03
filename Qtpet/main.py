import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import random
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
        self.ai_window = ChatApp()
        self.ai_window.global_finished_response_received.connect(self.onReceivedLLM)
        self.bottom_chat = False

        # 随机行为
        self.interaction_timer = QTimer(self)
        self.interaction_timer.timeout.connect(self.random_behavior)
        self.AutoChange = False
        self.OnclickAutobehavier() # 默认开启自动事件
        
        # 气泡淡出
        self.bubble_timer = QTimer()
        self.bubble_timer.timeout.connect(self.hide_bubble)
        
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
        
        #思考气泡
        self.thought_bubble = QLabel(self)
        self.thought_bubble.hide()
        self.thought_bubble.setStyleSheet("""
            QLabel {
                background-color: rgba(255, 255, 255, 220);
                border: 2px solid #8E8E8E;
                border-radius: 15px;
                padding: 8px;
                color: #333;
                font-weight: bold;
                font-size: 15px;
                height: 30px
            }
        """)

        self.sendwidget = QWidget(self)
        layout.addWidget(self.sendwidget)

        sendwidget_HLayout = QHBoxLayout(self.sendwidget)
        self.inputLineEdit = QLineEdit(self.sendwidget)
        self.sendBtn = QPushButton("发送")
        self.sendBtn.setObjectName("Tool_button")
        sendwidget_HLayout.addWidget(self.inputLineEdit)
        sendwidget_HLayout.addWidget(self.sendBtn)

        self.inputLineEdit.setPlaceholderText("输入消息...")
        self.inputLineEdit.returnPressed.connect(self.send_message)  # 回车键绑定
        self.sendBtn.clicked.connect(self.send_message)
        self.inputLineEdit.hide()
        self.sendBtn.hide()

        # 右键菜单
        self.menu = QMenu(self)

        zoom_in_action = QAction("放大", self)
        zoom_in_action.triggered.connect(self.zoom_in)

        zoom_out_action = QAction("缩小", self)
        zoom_out_action.triggered.connect(self.zoom_out)

        zoom_def_action = QAction("默认", self)
        zoom_def_action.triggered.connect(self.zoom_def)

        show_ai = QAction("聊天", self)
        show_ai.triggered.connect(self.show_deepseek_window)

        self.show_bottom_chat = QAction("快捷聊天", self)
        self.show_bottom_chat.setCheckable(True)
        self.show_bottom_chat.triggered.connect(self.on_show_bottom_chat)

        change_gif = QAction("更换动画", self)
        change_gif.triggered.connect(self.OnclickchangeGIF)

        self.auto_change_gif = QAction("自动更换", self)
        self.auto_change_gif.setCheckable(True)
        self.auto_change_gif.setChecked(True)
        self.auto_change_gif.toggled.connect(self.OnclickAutobehavier)

        exit_action = QAction("退出", self)
        exit_action.triggered.connect(lambda: sys.exit())


        self.menu.addAction(zoom_in_action)
        self.menu.addAction(zoom_out_action)
        self.menu.addAction(zoom_def_action)
        self.menu.addSeparator()
        self.menu.addAction(show_ai)
        self.menu.addAction(self.show_bottom_chat)
        self.menu.addAction(change_gif)
        self.menu.addAction(self.auto_change_gif)
        self.menu.addSeparator()
        self.menu.addAction(exit_action)
        
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
        self.scale_factor = min(self.scale_factor, 3.0)
        self.update_size()

    def zoom_out(self):
        self.scale_factor *= 0.95
        self.scale_factor = max(self.scale_factor, 0.5)
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
        # 在鼠标位置显示菜单
        self.menu.exec_(QCursor.pos())
        
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

    def OnclickAutobehavier(self):
        self.AutoChange = not self.AutoChange
        if self.AutoChange:
            self.auto_change_gif.setChecked(True)
            # self.random_behavior()  # 立即触发一次
            self.jump_animation() # 立即触发一次跳
            self.interaction_timer.start(30000)  # 每xx秒触发一次随机行为

            if self.bottom_chat:
                self.on_show_bottom_chat()
                self.show_bottom_chat.setChecked(False)
        else:
            self.auto_change_gif.setChecked(False)
            self.interaction_timer.stop()

    def random_behavior(self):
        behaviors = [
            lambda: self.random_ChangeGif(),
            lambda: self.jump_animation(),
            lambda: self.random_thought_bubble()
        ]
        weights = [5, 1, 4]  # 权重比例为 5:3:2，即 50%, 30%, 20%
    
        selected_behavior = random.choices(behaviors, weights=weights, k=1)[0]
        selected_behavior()  # 触发行为
        # random.choice(behaviors)()


    def random_ChangeGif(self):
        GifList =[
        "./doroimg/doroatention.gif",
        "./doroimg/dorobutton.gif",
        "./doroimg/dorocake.gif",
        "./doroimg/dorocool.gif",
        "./doroimg/dorodagun.gif",
        "./doroimg/dorodianzan.gif",
        "./doroimg/dorodrive.gif",
        "./doroimg/doroeat.gif",
        "./doroimg/dorogun.gif",
        "./doroimg/dorohappy.gif",
        "./doroimg/doroheiehei.gif",
        "./doroimg/dorohello.gif",
        "./doroimg/dorojugong.gif",
        "./doroimg/dorolaugh.gif",
        "./doroimg/dorolay.gif",
        "./doroimg/dorolinghun.gif",
        "./doroimg/doronowork.gif",
        "./doroimg/doroscare.gif",
        "./doroimg/doroshihua.gif",
        "./doroimg/dorosleep.gif",
        "./doroimg/dorotukoushui.gif",
        "./doroimg/dorowuyu.gif",
        "./doroimg/dorozhuairen.gif",
        ]
        filename = random.choice(GifList)
        self.curpath = filename
        self.changeGIF(filename)


    def jump_animation(self):
        # 跳跃动画效果
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(500)
        start_rect = self.geometry()
        jump_rect = QRect(start_rect.x(), int(start_rect.y()-start_rect.height()/2), 
                         start_rect.width(), start_rect.height())
        self.animation.setKeyValueAt(0.5, jump_rect)
        self.animation.setEndValue(start_rect)
        self.animation.start()    

    def random_thought_bubble(self):
        thinktext_List = [
            "欧润吉！好多好多欧润吉！人也要一起吃！",  # 开心到飞起
            "哼！不理人了！Doro要藏起人所有的袜子！",  # 超生气
            "呜呜...人不要丢下Doro...Doro会乖乖的...",  # 害怕得发抖
            "咕噜咕噜...Doro要吃掉一头牛！还有十个欧润吉！",  # 超级饿
            "Zzz...欧润吉...Zzz...人...",  # 困成一团
            "人什么时候回来呀...Doro要拆家了！...才不是！",  # 无聊到爆炸
            "Doro今天捡了好多瓶子！人会夸Doro能干的！",  # 得意洋洋
            "呜...Doro是不是做错事了...人会不喜欢Doro吗...",  # 难过想哭
            "那个会发光的长方形是什么呀？人为什么一直看它？",  # 好奇宝宝
            "Doro要努力挣钱！给人买最大的欧润吉！",  # 决心满满
            "人...人夸Doro可爱...Doro...Doro才不是最可爱的呢！",  # 害羞脸红
            "Doro是人最棒的家人！Doro会保护人的！",  # 自豪挺胸
            "Doro只是想玩一下...不是故意弄坏的...",  # 委屈巴巴
            "Doro想到一个挣钱的好办法！...是什么来着？",  # 灵光一闪
            "人...人对Doro真好...Doro也要对人好！",  # 感动到哭
            "为什么人要上班呢？上班是什么？能吃吗？",  # 疑惑不解
            "明天一定能捡到更多的瓶子！买更多的欧润吉！",  # 充满希望
            "Doro不要收拾房间！Doro要玩！",  # 厌烦至极
            "嘿嘿嘿...人是Doro的！",  # 傻乐傻乐
            "Doro以后再也不乱翻东西了！...大概吧..."  # 下定决心
        ]
        thinktext = random.choice(thinktext_List)
        self.show_thought_bubble(thinktext)

    def show_thought_bubble(self, text, delay=5000):
        self.thought_bubble.setText(text)
        self.thought_bubble.setWordWrap(True)  # 启用自动换行
        available_width = self.width() - 20
        self.thought_bubble.setFixedWidth(available_width)
        self.thought_bubble.adjustSize()
        
        self.thought_bubble.move(0, 0)
        # 显示动画
        self.thought_bubble.show()
        self.bubble_timer.start(delay)
    
    def hide_bubble(self):
        """隐藏气泡的动画效果"""
        self.bubble_timer.stop()
        if self.thought_bubble:
            self.thought_bubble.hide()


    def show_deepseek_window(self):
        if not self.ai_window:
            return
        self.ai_window.show()

    def on_show_bottom_chat(self): 
        self.bottom_chat = not self.bottom_chat
        if self.bottom_chat:
            self.show_bottom_chat.setChecked(True)
            self.inputLineEdit.show()
            self.sendBtn.show()
            if self.AutoChange:
                self.auto_change_gif.setChecked(False)
                self.interaction_timer.stop()
        else:
            self.inputLineEdit.hide()
            self.show_bottom_chat.setChecked(False)
            self.sendBtn.hide()

    def send_message(self):
        user_input = self.inputLineEdit.text().strip()
        if not user_input:
            return
        if self.AutoChange:
            self.auto_change_gif.setChecked(False)
            self.interaction_timer.stop()
        self.inputLineEdit.clear()
        self.ai_window.send_message(user_input) # 调用聊天窗口的功能，这样记录会留在聊天窗口

    def onReceivedLLM(self,content):
        self.show_thought_bubble(content)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    font = QFont(myFont().getFont(), 13)
    app.setFont(font)
    pet = DesktopPet()
    pet.show()
    sys.exit(app.exec_())
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from option import OptionWidget
from loading import LoadingWidget
from LLMprovider import ChatThread_gemini,ChatThread_Deepseek,ChatThread_maas,ChatThread_Qwen


class myFont():
    def __init__(self):
        super().__init__()
        self.font_id = QFontDatabase.addApplicationFont("./cfg/zxf.ttf")
        if self.font_id == -1:
            print("Failed to load font.")
        else:
            families = QFontDatabase.applicationFontFamilies(self.font_id)
            if families:
                self.font_family = families[0]

    def getFont(self):
        return self.font_family



class ChatMessage(QWidget):
    def __init__(self, content, is_user=True, parent=None):
        super().__init__(parent)
        self.is_user = is_user
        self.setProperty("isUser", self.is_user)  # 用于QSS样式选择
        self.font_family = myFont().getFont()
        self.init_ui(content)

    def init_ui(self, content):
        # 设置尺寸策略为Preferred以获得更好的布局适应性
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        
        # 主布局：水平布局，用于消息对齐
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 4, 0, 4)  # 添加上下边距
        main_layout.setSpacing(0)

        # 创建气泡容器
        self.bubble = QWidget()
        self.bubble.setObjectName("bubble")  # 用于QSS选择器
        
        # 创建内容显示组件
        self.content_label = QTextEdit()
        self.content_label.setReadOnly(True)
        self.content_label.setObjectName("content_label")
        self.content_label.setFont(QFont(self.font_family, 12))
        # 禁用滚动条，通过动态调整高度实现自适应
        self.content_label.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.content_label.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # 气泡内部布局
        bubble_layout = QHBoxLayout(self.bubble)
        bubble_layout.addWidget(self.content_label)
        bubble_layout.setContentsMargins(12, 6, 12, 6) 

        # 用户消息右对齐
        if self.is_user:
            main_layout.addStretch()
        
        main_layout.addWidget(self.bubble)
        if not self.is_user:
            main_layout.addStretch()
        self.set_content(content)

    def set_content(self, content):
        """设置初始内容"""
        self.full_content = content
        if self.is_user:
            self.content_label.setPlainText(content)
        else:
            self.content_label.setMarkdown(content)
        self.adjust_size()

    def append_content(self, content):
        """流式追加内容（用于生成式回复）"""
        self.full_content += content
        self.content_label.setMarkdown(self.full_content)
        self.adjust_size()

    def adjust_size(self):
        """动态调整消息气泡尺寸"""
        doc = self.content_label.document()
        
        # 计算内边距（从布局获取或硬编码）
        padding = 24   # 左右内边距（12*2）
        v_padding = 12 # 垂直内边距（6*2）
        
        # 获取父容器宽度（考虑父级不存在时的默认值）
        parent_width = self.parent().width() if self.parent() else 400

        # 根据消息类型确定最大宽度约束
        if self.is_user:
            max_bubble_width = int(parent_width * 0.7)  # 用户消息最大70%
        else:
            max_bubble_width = int(parent_width * 0.9)  # AI消息最大88%

        # 计算文本可用宽度并设置到文档
        available_text_width = max(max_bubble_width - padding, 1)
        doc.setTextWidth(available_text_width)

        # 计算实际所需宽度
        text_width = doc.idealWidth()
        bubble_width = text_width + padding
        bubble_width = min(bubble_width, max_bubble_width)
        bubble_width = max(bubble_width, 60 if self.is_user else 100)  # 最小宽度限制

        # 设置气泡宽度
        self.bubble.setFixedWidth(int(bubble_width))

        # 计算高度（包含文档边距）
        ideal_height = doc.size().height() + v_padding * 2
        self.setFixedHeight(int(ideal_height))
        self.updateGeometry()

    def resizeEvent(self, event):
        """父窗口尺寸变化时重新调整"""
        super().resizeEvent(event)
        self.adjust_size()


class StyleLoader:
    _instance = None
    
    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._cache = {}
        return cls._instance
    
    def load_theme(self, theme_name):
        if theme_name not in self._cache:
            try:
                with open(f"themes/{theme_name}.qss", "r",  encoding='utf-8') as f:
                    self._cache[theme_name] = f.read()
            except FileNotFoundError:
                return ""
        return self._cache[theme_name]


def get_windows_theme():
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        winreg.CloseKey(key)
        return 'light' if value == 1 else 'dark'
    except Exception:
        return 'unknown'

class ChatApp(QMainWindow):
    global_finished_response_received = pyqtSignal(str)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Tool)
        self.initUI()
        self.messages = []
        self.current_ai_message = None
        self.system_message = ""
        self.loading_widget = None
        self.preset = 0
        self.style_loader = StyleLoader()
        # 获取系统颜色方案

        self.current_theme = "light"

        self.current_theme = get_windows_theme()
        self.apply_theme()
        # self.loadcfg()
        self.preset_options = self.options_widget.getpreset()
        self.update_system_message("Doro")
        # self.setWindowFlags(Qt.FramelessWindowHint)
        self.on_alpha_changed(0.9)

        # 修改窗口大小
        self.margin = 5  # 边缘检测区域宽度
        self.dragging = False
        self.resize_dir = None
        self.drag_start_pos = None
        self.window_start_size = None
        self.drag_position= None


    def apply_theme(self):
        qss = self.style_loader.load_theme(self.current_theme)
        app = QApplication.instance()
        if app:
            app.setStyleSheet(qss)  # 确保qss字符串无语法错误
            self.update()  # 触发重绘

        
    def update_children_theme(self, widget):
        for child in widget.children():
            if isinstance(child, QWidget):
                if hasattr(child, "update_theme"):
                    child.update_theme(self.current_theme)
                self.update_children_theme(child)
                
    def toggle_theme(self):
        self.current_theme = "dark" if self.current_theme == "light" else "light"
        self.theme_button.setIcon(QIcon("./icons/light.ico") if self.current_theme == "light" else QIcon("./icons/dark.ico"))
        self.preset_button.setIcon(QIcon("./icons/personl.ico")if self.current_theme == "light" else QIcon("./icons/persond.ico"))
        self.exit_button.setIcon(QIcon("./icons/exitl.ico")if self.current_theme == "light" else QIcon("./icons/exitd.ico"))
        # self.general_button.setIcon(QIcon("./icons/settingl.ico")if self.current_theme == "light" else QIcon("./icons/settingd.ico"))
        if self.stack_widget.currentIndex() == 0:
            self.general_button.setIcon(QIcon("./icons/settingl.ico")if self.current_theme == "light" else QIcon("./icons/settingd.ico"))
        else:
            self.general_button.setIcon(QIcon("./icons/returnl.ico")if self.current_theme == "light" else QIcon("./icons/returnd.ico"))
        self.apply_theme()
        
    def hide(self):
        self.close()

    def initUI(self):
        self.setWindowTitle("聊天")
        self.setWindowIcon(QIcon("./icons/app.ico"))
        # self.setGeometry(100, 100, 1000, 800)
        self.setMinimumSize(800, 600)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        main_widget = QWidget() # 聊天页面
        self.setCentralWidget(main_widget)
        
        # 主页面
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 顶部工具栏
        toolbar = QWidget()
        toolbar.setFixedHeight(50)
        toolbar.setObjectName("toolbar")
        layout.addWidget(toolbar)

        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(20, 0, 20, 0)
        
        # 这里改成人格名字
        self.title_label = QLabel("Doro")
        self.title_label.setObjectName("title_label")
        toolbar_layout.addWidget(self.title_label)
        toolbar_layout.addStretch()
        

        # 通用设置
        self.general_button = QPushButton() # 通用设置
        self.general_button.setIcon(QIcon("./icons/settingl.ico"))
        self.general_button.setObjectName("Tool_button")
        self.general_button.clicked.connect(self.set_Promptwidget)
        toolbar_layout.addWidget(self.general_button)

        self.preset_button = QPushButton() # 人格设置
        self.preset_button.setIcon(QIcon("./icons/personl.ico"))
        self.preset_button.setObjectName("Tool_button")
        self.preset_button.clicked.connect(self.set_personality)
        toolbar_layout.addWidget(self.preset_button)

        self.theme_button = QPushButton()   # 切换浅色深色主题
        self.theme_button.setIcon(QIcon("./icons/light.ico"))
        self.theme_button.setObjectName("Tool_button")
        self.theme_button.clicked.connect(self.toggle_theme)
        toolbar_layout.addWidget(self.theme_button)

        self.exit_button = QPushButton() # 退出
        self.exit_button.setIcon(QIcon("./icons/exitl.ico"))
        self.exit_button.setObjectName("Tool_button")
        self.exit_button.clicked.connect(self.hide)
        toolbar_layout.addWidget(self.exit_button)


        # 创建堆叠窗口控件
        self.stack_widget = QStackedWidget()
        self.stack_widget.setObjectName("stackwidget")
        layout.addWidget(self.stack_widget)
        chat_widget = QWidget()
        self.options_widget = OptionWidget() # 设置
        self.options_widget.GeneratorOptPage.alphaChanged.connect(self.on_alpha_changed)
        self.options_widget.GeneratorOptPage.windowSizeChanged.connect(self.on_size_changed)
        chatlayout = QVBoxLayout(chat_widget)

        self.stack_widget.addWidget(chat_widget)
        self.stack_widget.addWidget(self.options_widget)
        self.stack_widget.setCurrentIndex(0)

        # 聊天区域
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setObjectName("chat_scroll")
        
        self.chat_container = QWidget(self)
        self.chat_container.setObjectName("chat_scroll")

        
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setAlignment(Qt.AlignTop)
        self.chat_layout.setContentsMargins(40, 20, 20, 20)
        self.chat_layout.setSpacing(0)
        
        self.chat_scroll.setWidget(self.chat_container)
        chatlayout.addWidget(self.chat_scroll, 1)

        # 输入区域
        input_widget = QWidget(self)
        # input_widget.setStyleSheet("background-color: #FFFFFF; border-top: 1px solid #E5E5E5;")
        input_widget.setFixedHeight(210)
        input_layout = QVBoxLayout(input_widget)
        input_layout.setContentsMargins(0, 0, 0, 0)
        
        self.input_box = QTextEdit()
        self.input_box.setPlaceholderText("输入消息...")
        self.input_box.setObjectName("inputbox")
        self.input_box.setAcceptRichText(False)
        self.input_box.setFixedHeight(210)
        self.input_box.setFont(QFont(myFont().getFont(), 12))
        
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.addStretch()
        
        self.send_button = QPushButton("发送")
        self.send_button.setFixedSize(80, 32)
        self.send_button.setObjectName("SendBtn")

        self.send_button.clicked.connect(self.on_clicked_send_message)
        
        button_layout.addWidget(self.send_button)
        input_layout.addWidget(self.input_box)
        input_layout.addLayout(button_layout)
        chatlayout.addWidget(input_widget)

        self.chat_scroll.verticalScrollBar().setObjectName("verticalScrollBar")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        for i in range(self.chat_container.layout().count()):
            if self.layout().itemAt(i):
                widget = self.layout().itemAt(i).widget()
                if isinstance(widget, ChatMessage):
                    widget.adjust_size()

    # 槽函数 响应透明度变化
    def on_alpha_changed(self, alpha):
        self.setWindowOpacity(alpha)

    # 槽函数 响应尺寸变化
    def on_size_changed(self, size):
        self.setFixedSize(size)

    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            # 记录鼠标按下时的全局坐标
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if event.buttons() == Qt.LeftButton and self.drag_position:
            # 计算新的窗口位置并移动
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.LeftButton:
            self.drag_position = None  # 重置拖动位置
            event.accept()


    # def read_ini(self, file_path):
    #     config = configparser.RawConfigParser()
    #     read_files = config.read(file_path)

    #     if not read_files:
    #         self.show_error(f"配置文件不存在: {file_path}")
    #         return {}

    #     return {
    #         section: dict(config.items(section))
    #         for section in config.sections()
    #     }

    def show_error(self, message):
        """使用 PyQt 的 QMessageBox 显示错误信息"""
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle("Error")
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec_()


    def on_clicked_send_message(self):
        user_input = self.input_box.toPlainText().strip()
        if not user_input:
            return
        self.input_box.clear()
        self.send_message(user_input)

    def send_message(self, content):
        # 添加用户消息
        user_message = ChatMessage(content, is_user=True, parent=self.chat_container)
        self.chat_layout.addWidget(user_message)
        self.messages.append({"role": "user", "content": content})

        # 添加加载状态
        self.loading_widget = LoadingWidget()
        self.chat_layout.addWidget(self.loading_widget, 0, Qt.AlignLeft)
        self.scroll_to_bottom()

        # 创建AI消息占位符
        self.current_ai_message = ChatMessage("", is_user=False,parent=self.chat_container)
        self.chat_layout.addWidget(self.current_ai_message)

        # 启动线程
        provider = self.options_widget.getProvider()
        if provider.get("baseurl") == '':
            self.update_chat_display_stream(f"模型：{provider.get('provider')}，baseurl未配置")
            return
        if provider.get("apikey") == '':
            self.update_chat_display_stream(f"模型：{provider.get('provider')}，apikey未配置")
            return
        if provider.get("model") == '':
            self.update_chat_display_stream(f"模型：{provider.get('provider')}，model未配置")
            return


        self.chat_thread = QThread()
        if(provider.get("provider") == "maas"):
            self.chat_thread = ChatThread_maas(self.messages, 
                                            stream= True, 
                                            base_url= provider.get("baseurl"),
                                            api_key= provider.get("apikey"), 
                                            model= provider.get("model")) 
        if(provider.get("provider") == "qwen"):
            self.chat_thread = ChatThread_Qwen(self.messages, 
                                            stream= True, 
                                            base_url= provider.get("baseurl"),
                                            api_key= provider.get("apikey"), 
                                            model= provider.get("model")) 
        if(provider.get("provider") == "deepseek"):
            self.chat_thread = ChatThread_Deepseek(self.messages, 
                                            stream= True, 
                                            base_url= provider.get("baseurl"),
                                            api_key= provider.get("apikey"), 
                                            model= provider.get("model"))     
        if(provider.get("provider") == "gemini"):
            self.chat_thread = ChatThread_Deepseek(self.messages, 
                                            stream= True, 
                                            base_url= provider.get("baseurl"),
                                            api_key= provider.get("apikey"), 
                                            model= provider.get("model"))  
        
        self.chat_thread.stream_response_received.connect(self.update_chat_display_stream)
        self.chat_thread.finished.connect(self.on_chat_thread_finished)
        self.chat_thread.start()

    # 流式输出
    def update_chat_display_stream(self, content):
        if self.loading_widget:
            self.chat_layout.removeWidget(self.loading_widget)
            self.loading_widget.deleteLater()
            self.loading_widget = None
        
        if self.current_ai_message:
            self.current_ai_message.append_content(content)
            self.scroll_to_bottom()
            # print(content)

    # 返回结果
    def on_chat_thread_finished(self):
        if self.loading_widget:
            self.chat_layout.removeWidget(self.loading_widget)
            self.loading_widget.deleteLater()
            self.loading_widget = None
        
        ai_content = self.current_ai_message.full_content
        self.messages.append({"role": "assistant", "content": ai_content})
        self.global_finished_response_received.emit(ai_content)
        print(f"api调用结束：{ai_content}")

    def scroll_to_bottom(self):
        QTimer.singleShot(50, lambda: self.chat_scroll.verticalScrollBar().setValue(
            self.chat_scroll.verticalScrollBar().maximum()
        ))

   
    def set_personality(self):
        # 创建人格菜单
        personality_menu = QMenu("选择人格", self)
        personality_menu.setObjectName("personality_menu")
        personality_menu.setAttribute(Qt.WA_TranslucentBackground)
        # 添加预设项
        for name in self.preset_options:
            action = personality_menu.addAction(name)
            action.triggered.connect(lambda checked, n=name: 
                self.update_system_message(n))
        
        # 获取触发菜单的控件位置
        btn = self.sender()  # 假设通过按钮触发
        pos = btn.mapToGlobal(QPoint(0, btn.height()))
        
        # 显示菜单（模态）
        personality_menu.exec_(pos)

    def set_Promptwidget(self):
        """更新系统消息并重置对话"""
        if self.stack_widget.currentIndex() == 0:
            self.general_button.setIcon(QIcon("./icons/returnl.ico")if self.current_theme == "light" else QIcon("./icons/returnd.ico"))
            self.stack_widget.setCurrentIndex(1)
        else:
            self.general_button.setIcon(QIcon("./icons/settingl.ico")if self.current_theme == "light" else QIcon("./icons/settingd.ico"))
            self.stack_widget.setCurrentIndex(0)
            

    def update_system_message(self, selected):
    # 这里使用 selected 和 preset_options 设置人格预设
        self.system_message = self.preset_options[selected]
        self.reset_messages()
        self.title_label.setText(selected)

    def reset_messages(self):
        """重置对话历史"""
        self.messages = [{"role": "system", "content": self.system_message}]
        # 清空聊天界面
        for i in reversed(range(self.chat_layout.count())): 
            self.chat_layout.itemAt(i).widget().setParent(None)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    font = QFont(myFont().getFont(), 13)
    app.setFont(font)
    window = ChatApp()
    window.show()
    sys.exit(app.exec_())
from PyQt5.QtCore import *
from openai import OpenAI

# OpenAI接口实现
class ChatThread_Deepseek(QThread):
    response_received = pyqtSignal(str)
    stream_response_received = pyqtSignal(str)
    def __init__(self, messages, stream=False, base_url="https://api.deepseek.com", api_key="", model = "deepseek-chat"):
        super().__init__()
        self.messages = messages
        self.stream = stream
        self.baseurl = base_url
        self.apikey = api_key
        self.dmodel = model
        self.client = OpenAI(api_key=self.apikey, base_url=self.baseurl)

    def run(self):
        try:
            # 创建 OpenAI 客户端实例
            response = self.client.chat.completions.create(
                model=self.dmodel,
                messages=self.messages,
                stream=self.stream
            )

            if self.stream:
                full_content = ""
                for chunk in response:
                    if chunk.choices and len(chunk.choices) > 0:
                        content = chunk.choices[0].delta.content
                        if content:
                            full_content += content
                            self.stream_response_received.emit(content)
                self.response_received.emit(full_content)
            else:
                if response.choices and len(response.choices) > 0:
                    content = response.choices[0].message.content
                    self.response_received.emit(content)

        except Exception as e:
            # 处理异常情况
            error_msg = f"API Error: {str(e)}"
            self.response_received.emit(error_msg)


# qwen3
class ChatThread_Qwen(QThread):
    # 定义两个信号：完整响应和流式响应
    response_received = pyqtSignal(str)       # 非流式或流式结束后发送完整内容
    stream_response_received = pyqtSignal(str) # 流式响应时逐步发送

    def __init__(self, messages, stream=False, base_url=None, api_key=None, model="qwen-plus"):
        super().__init__()
        self.messages = messages
        self.stream = stream
        self.base_url = base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1"
        self.api_key = api_key
        self.model = model
        self.enable_search = True
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def run(self):
        try:
            # 创建 OpenAI 客户端并发送请求
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                extra_body={
                    "enable_search": self.enable_search
                },
                stream=self.stream
            )

            if self.stream:
                full_content = ""
                for chunk in response:
                    if chunk.choices and len(chunk.choices) > 0:
                        content = chunk.choices[0].delta.content
                        if content:
                            full_content += content
                            self.stream_response_received.emit(content)
                # 发送完整响应
                self.response_received.emit(full_content)
            else:
                if response.choices and len(response.choices) > 0:
                    content = response.choices[0].message.content
                    self.response_received.emit(content)

        except Exception as e:
            # 发生异常时发送错误信息
            error_msg = f"API Error: {str(e)}"
            self.response_received.emit(error_msg)


#maas
class ChatThread_maas(QThread):
     # 定义两个信号：完整响应和流式响应
    response_received = pyqtSignal(str)       # 非流式或流式结束后发送完整内容
    stream_response_received = pyqtSignal(str) # 流式响应时逐步发送

    def __init__(self, messages, stream=False, base_url= "http://maas-api.cn-huabei-1.xf-yun.com/v1", api_key=None, model="xdeepseekv32"):
        super().__init__()
        self.messages = messages
        self.stream = stream
        self.baseurl = base_url
        self.apikey = api_key
        self.model = model
        self.enable_search = True
        self.client = OpenAI(api_key=self.apikey, base_url=self.baseurl)

    def run(self):
        try:
            # 创建 OpenAI 客户端并发送请求
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                stream=self.stream,
                temperature=0.7,
                max_tokens=4096,
                extra_headers={"lora_id": "0"},  # 调用微调大模型时,对应替换为模型服务卡片上的resourceId
                stream_options={"include_usage": True},
                extra_body={"search_disable": False, "show_ref_label": False} 
            )

            if self.stream:
                full_content = ""
                for chunk in response:
                    if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content is not None:
                        content = chunk.choices[0].delta.content
                        self.stream_response_received.emit(content)
                        full_content += content
                # 发送完整响应
                self.response_received.emit(full_content)
            else:
                if response.choices and len(response.choices) > 0:
                    content = response.choices[0].message.content
                    self.response_received.emit(content)

        except Exception as e:
            # 发生异常时发送错误信息
            error_msg = f"API Error: {str(e)}"
            self.response_received.emit(error_msg)


#哈基米Gemini
class ChatThread_gemini(QThread):
     # 定义两个信号：完整响应和流式响应
    response_received = pyqtSignal(str)       # 非流式或流式结束后发送完整内容
    stream_response_received = pyqtSignal(str) # 流式响应时逐步发送

    def __init__(self, messages, stream=False, base_url= "https://generativelanguage.googleapis.com/v1beta/openai/", api_key=None, model="gemini-2.0-flash"):
        super().__init__()
        self.messages = messages
        self.stream = stream
        self.baseurl = base_url
        self.apikey = api_key
        self.model = model
        self.enable_search = True
        self.client = OpenAI(api_key=self.apikey, base_url=self.baseurl)

    def run(self):
        try:
            # 创建 OpenAI 客户端并发送请求
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                stream=self.stream,
                stream_options={"include_usage": True},
                reasoning_effort="low",
            )

            if self.stream:
                full_content = ""
                for chunk in response:
                    if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content is not None:
                        content = chunk.choices[0].delta.content
                        self.stream_response_received.emit(content)
                        full_content += content
                # 发送完整响应
                self.response_received.emit(full_content)
            else:
                if response.choices and len(response.choices) > 0:
                    content = response.choices[0].message.content
                    self.response_received.emit(content)

        except Exception as e:
            # 发生异常时发送错误信息
            error_msg = f"API Error: {str(e)}"
            self.response_received.emit(error_msg)

#////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////// 
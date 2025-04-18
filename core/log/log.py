import os
import logging
import unicodedata
from datetime import datetime
from typing import Literal
from .coloredformatter import ColoredFormatter
from .colorcodefilter import ColorCodeFilter


class Log:
    MAX_LOG_ENTRIES = 500  # 最大日志存储条数
    _instance = None  # 单例实例

    def __new__(cls, level: str = "INFO"):
        """单例模式实现：确保全局只有一个实例"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, level: str = "INFO"):
        """初始化日志器"""
        if self._initialized:
            return
        self._level = getattr(logging, level.upper(), logging.INFO)  # 将字符串转换为日志级别常量
        self._initialized = True
        self.logs = []  # 用于存储日志消息
        self._init_log()

    def add_log(self, message: str):
        """将日志消息添加到存储列表中，超过最大条数时移除最早的消息"""
        if len(self.logs) >= self.MAX_LOG_ENTRIES:
            self.logs.pop(0)
        self.logs.append(message)

    def _init_log(self):
        """初始化日志器及其配置"""
        self._ensure_log_directory_exists()
        self._create_log()
        self._create_log_title()

    def _current_datetime(self) -> str:
        """获取当前日期，格式为 YYYY-MM-DD"""
        return datetime.now().strftime("%Y-%m-%d")

    def _create_log(self):
        """创建并配置日志器，包括控制台和文件输出"""
        self.log = logging.getLogger('StarRailAuto')
        self.log.propagate = False
        self.log.setLevel(logging.DEBUG)  # 允许所有级别的日志传递给处理器

        # 控制台日志
        console_handler = logging.StreamHandler()
        console_formatter = ColoredFormatter('%(asctime)s | %(levelname)s | %(message)s')
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(self._level)  # 使用用户传入的级别
        self.log.addHandler(console_handler)

        # 文件日志（按天创建）
        file_handler = logging.FileHandler(f"./logs/{self._current_datetime()}.log", encoding="utf-8")
        file_formatter = ColorCodeFilter('%(asctime)s | %(levelname)s | %(message)s')
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.DEBUG)  # 文件记录所有级别
        self.log.addHandler(file_handler)

        # 添加自定义处理器来捕获日志消息
        log_handler = LogHandler(self)
        self.log.addHandler(log_handler)

    def _create_log_title(self):
        """创建专用于标题日志的日志器"""
        self.log_title = logging.getLogger('StarRailAuto_title')
        self.log_title.propagate = False
        self.log_title.setLevel(self._level)

        # 控制台日志
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter('%(message)s')
        console_handler.setFormatter(console_formatter)
        self.log_title.addHandler(console_handler)

        # 文件日志
        file_handler = logging.FileHandler(f"./logs/{self._current_datetime()}.log", encoding="utf-8")
        file_formatter = logging.Formatter('%(message)s')
        file_handler.setFormatter(file_formatter)
        self.log_title.addHandler(file_handler)

        # 添加自定义处理器来捕获日志消息
        log_handler = LogHandler(self)
        self.log_title.addHandler(log_handler)

    def _ensure_log_directory_exists(self):
        """确保日志目录存在，不存在则创建"""
        try:
            if not os.path.exists("logs"):
                os.makedirs("logs")
        except Exception as e:
            print(f"无法创建日志目录: {e}")  # 在日志系统未初始化时，直接打印错误信息

    def info(self, format_str: str, *args):
        """正确透传参数化日志"""
        self.log.info(format_str, *args)  # 参数直接传递

    def debug(self, format_str: str, *args):
        self.log.debug(format_str, *args)

    def warning(self, format_str: str, *args):
        self.log.warning(format_str, *args)

    def error(self, format_str: str, *args):
        self.log.error(format_str, *args)

    def critical(self, format_str: str, *args):
        self.log.critical(format_str, *args)

    def hr(self, title: str, level: Literal[0, 1, 2] = 0, write: bool = True):
        """
        格式化标题并打印或写入文件

        level: 0
        +--------------------------+
        |       这是一个标题        |
        +--------------------------+

        level: 1
        ======= 这是一个标题 =======

        level: 2
        ------- 这是一个标题 -------
        """
        if not title:
            return  # 如果标题为空，直接返回

        try:
            title_lines = title.split('\n')
            max_title_length = max(self._custom_len(line) for line in title_lines)
            separator_length = max_title_length + 4

            if level == 0:
                separator = '+' + '-' * separator_length + '+'
                formatted_title_lines = []

                for line in title_lines:
                    title_length = self._custom_len(line)
                    padding_left = (separator_length - title_length) // 2
                    padding_right = separator_length - title_length - padding_left

                    formatted_title_line = '|' + ' ' * padding_left + line + ' ' * padding_right + '|'
                    formatted_title_lines.append(formatted_title_line)

                formatted_title = f"{separator}\n" + "\n".join(formatted_title_lines) + f"\n{separator}"
            elif level == 1:
                padding = (separator_length - self._custom_len(title)) // 2
                formatted_title = '=' * padding + ' ' + title + ' ' + '=' * padding
            elif level == 2:
                padding = (separator_length - self._custom_len(title)) // 2
                formatted_title = '-' * padding + ' ' + title + ' ' + '-' * padding

            self._print_title(formatted_title, write)
        except Exception as e:
            self.error(f"格式化标题时出错: {e}")

    def _custom_len(self, text: str) -> int:
        """
        计算字符串的自定义长度，考虑到某些字符可能占用更多的显示宽度
        """
        if text is None:
            return 0
        return sum(2 if unicodedata.east_asian_width(c) in 'WF' else 1 for c in text)

    def _print_title(self, title: str, write: bool):
        """打印标题"""
        if title is None:
            return
        if write:
            self.log_title.info(title)
        else:
            print(title)


class LogHandler(logging.Handler):
    """自定义日志处理器将日志存储在内存中"""

    def __init__(self, log_instance):
        super().__init__()
        self.log_instance = log_instance

    def emit(self, record):
        try:
            # 只有当日志级别是 INFO 时，才存储日志消息
            if record.levelno == logging.INFO:
                msg = record.getMessage()  # 直接获取日志消息
                self.log_instance.add_log(msg)
        except Exception as e:
            self.log_instance.error(f"记录日志时出错: {e}")

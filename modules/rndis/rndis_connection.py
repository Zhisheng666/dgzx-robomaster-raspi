import time
import socket
import threading

from ..utils.logger import logger as LOGGER
from ..utils.logger import LOGGER_PREFIX as _p
from ..utils.logger import PREFIX_GENERATOR
_gen = PREFIX_GENERATOR(_p["RNDIS_CONNECTION"])

CONN_STATUS_ING     = 0x00
CONN_STATUS_SUCCESS = 0x01

# 明文SDK通信连接类
class RndisConnection:
    
    def __init__(
        self,
        # 指令处理函数
        handler,
        host: str = "192.168.42.2",
        port: int = 40923,
        timeout  = 5 # 单位: seconds
    ):
        self.handler = handler

        self.conn_status = CONN_STATUS_ING
        self.conn_status_lock = threading.Lock()

        self.address = (host, port)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(timeout)

    def start(self):
        self.loop_thread = threading.Thread(target=self.loop, args=tuple())
        self.loop_thread.start()

    def writeline(self, content: str) -> bool:
        try:
            self.socket.send(content.encode("utf-8"))
        except:
            LOGGER.error(_gen("Failed to write data."))
            return False
        return True

    def readline(self) -> str:
        try:
            response = self.socket.recv(1024).decode("utf-8")
            response = response.strip()
        except:
            LOGGER.error(_gen("Failed to get data."))
            return False

        LOGGER.info(_gen(f"Received data: <{response}>"))
        return True

    # 初始化
    def initialize(self) -> bool:
        # 连接
        try:
            self.socket.connect(self.address)
        except Exception as e:
            LOGGER.error(_gen("Failed to connect to the socket."))
            return False

        # 连接成功
        self.writeline("game_msg on")
        self.set_status(CONN_STATUS_SUCCESS)
        return True

    # 获取当前连接状态
    def get_status(self) -> str:
        with self.conn_status_lock:
            return self.conn_status

    # 设置当前连接状态
    def set_status(self, status: str) -> bool:
        with self.conn_status_lock:
            if status not in (CONN_STATUS_ING, CONN_STATUS_SUCCESS):
                LOGGER.warning(_gen(f"设置连接状态为未定义值，具体值为：{status}"))
                return False
            self.conn_status = CONN_STATUS_SUCCESS
            LOGGER.info(_gen(f"设置连接状态为 {status}"))
            return True

    def loop(self):
        while True:
            if self.get_status() == CONN_STATUS_ING:
                self.initialize()
            elif self.get_status() == CONN_STATUS_SUCCESS:
                resp = self.readline()

                if "game msg push" in resp:
                    data = resp.split("[")[1].split("]")[0]
                    pressed_key = data[7]
                    pressed_key = int(pressed_key)

                    LOGGER.info(f"选手端 键盘按下：{pressed_key}")

                    self.handler("KEYBOARD", pressed_key)
            else:
                LOGGER.error(_gen("状态值异常，请检查代码。"))
                time.sleep(1)
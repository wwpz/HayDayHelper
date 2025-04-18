import io
import cv2
import math
import traceback
import subprocess
import numpy as np
from io import BytesIO
from core.log import log
from PIL import Image, ImageDraw, ImageEnhance
from utils.image_utils import ImageUtils


class SimulatorController:
    def __init__(self, port):
        self.port = port
        self.img_cache = {}
        self.connected = False

    def connect(self):
        """
        连接到 MuMu 模拟器
        :return: 连接成功返回 True，否则返回 False
        """
        try:
            # 断开所有已连接的设备
            subprocess.run(["adb", "disconnect"], capture_output=True)
            log.debug("启动前先断开所有已连接的设备。将重新连接端口")

            # 尝试连接到指定端口的模拟器
            result = subprocess.run(["adb", "connect", f"127.0.0.1:{self.port}"], capture_output=True, text=True)
            log.debug(result.stdout)  # 打印连接结果

            if "connected" in result.stdout:
                log.info(f"成功连接到 MuMu 模拟器——端口：{self.port}")
                self.connected = True
                return True
            else:
                log.info("连接失败，请检查 MuMu 模拟器是否已启动。")
                self.connected = False
                return False
        except Exception as e:
            log.debug(f"连接模拟器发生错误: {e}")
            self.connected = False
            return False

    def disconnect(self):
        """
        断开与 MuMu 模拟器的连接
        :return: 断开成功返回 True，否则返回 False
        """
        try:
            result = subprocess.run(["adb", "disconnect", f"127.0.0.1:{self.port}"], capture_output=True, text=True)
            log.debug(result.stdout)  # 打印断开连接结果
            if "disconnected" in result.stdout:
                log.debug("成功断开与 MuMu 模拟器的连接！")
                self.connected = False
                return True
            else:
                log.debug("断开连接失败。")
                return False
        except Exception as e:
            log.debug(f"发生错误: {e}")
            return False

    def click(self, x, y):
        """
        模拟点击屏幕上的指定坐标
        :param x: 横坐标
        :param y: 纵坐标
        """
        if not self.connected:
            log.debug("未连接到模拟器，请先调用 connect() 方法。")
            return False

        try:
            # 使用 adb shell input tap 命令模拟点击
            subprocess.run(["adb", "shell", "input", "tap", str(x), str(y)])
            log.debug(f"模拟点击成功，坐标: ({x}, {y})")
            return True
        except Exception as e:
            log.debug(f"模拟点击失败: {e}")
        return False

    def swipe(self, x1, y1, x2, y2, duration=900):
        """
        模拟从 (x1, y1) 滑动到 (x2, y2)
        :param x1: 起点横坐标
        :param y1: 起点纵坐标
        :param x2: 终点横坐标
        :param y2: 终点纵坐标
        :param duration: 滑动持续时间（毫秒，默认 100ms）
        """
        if not self.connected:
            log.debug("未连接到模拟器，请先调用 connect() 方法。")
            return

        try:
            # 使用 adb shell input swipe 命令模拟滑动
            subprocess.run(["adb", "shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2), str(duration)])
            log.debug(f"模拟滑动成功，从 ({x1}, {y1}) 到 ({x2}, {y2}),持续时间: {duration}ms")
        except Exception as e:
            log.debug(f"模拟滑动失败: {e}")

    def take_screenshot(self, enhance=False):
        """
        截取屏幕，选择性处理图片，转字节
        :return: 返回修改后的字节图像对象
        """
        if not self.connected:
            log.debug("未连接到模拟器，请先调用 connect() 方法。")
            return

        try:
            # 使用 adb shell screencap 命令截取屏幕
            result = subprocess.run(["adb", "shell", "screencap", "-p"], capture_output=True)

            # 清理输出数据：去除多余的换行符
            screenshot_data = result.stdout.replace(b"\r\n", b"\n")

            # 将二进制数据转换为图像
            image = Image.open(io.BytesIO(screenshot_data))

            # 获取图像的分辨率
            width, height = image.size
            # print(f"截图的分辨率: {width}x{height}")

            if enhance:
                # 在内存中修改图像：控制涂白的高度
                draw = ImageDraw.Draw(image)
                draw.rectangle([(0, 0), (width, 100)], fill="white")
                draw.rectangle([(0, 145), (width, 420)], fill="white")
                draw.rectangle([(0, 460), (width, 730)], fill="white")
                draw.rectangle([(0, 780), (width, height)], fill="white")

                draw.rectangle([(0, 0), (300, height)], fill="white")
                draw.rectangle([(530, 0), (650, height)], fill="white")
                draw.rectangle([(900, 0), (1070, height)], fill="white")
                draw.rectangle([(1280, 0), (1420, height)], fill="white")
                draw.rectangle([(1600, 0), (width, height)], fill="white")
                # 增强对比度
                enhancer = ImageEnhance.Contrast(image)
                image = enhancer.enhance(2)

                # 增强亮度
                enhancer = ImageEnhance.Brightness(image)
                image = enhancer.enhance(3)
                # 转为灰度图（替代OpenCV预处理）
                image = image.convert('L')
                # 放大倍率
                # scale_percent = 100  # 放大200%
                #
                # # 计算新的宽度和高度
                # width = int(image.width * scale_percent / 100)
                # height = int(image.height * scale_percent / 100)
                #
                # # 调整图像大小
                # image = image.resize((width, height), Image.BICUBIC)

            # 调试时显示图像
            # image.show()

            with BytesIO() as byte_stream:
                image.save(byte_stream, format='PNG')
                byte_data = byte_stream.getvalue()  # 在流关闭前获取数据
            return byte_data
        except Exception as e:
            log.debug(f"截图失败: {e}")
            return None

    def is_connected(self):
        """
        检查是否已连接到模拟器
        :return: 已连接返回 True，否则返回 False
        """
        return self.connected

    def find_element(self, target, threshold=0.9,enable_scaling=False):
        now_image_name = target.replace('./res/', '')
        log.debug(f"本次查找的图片路径为------：" + now_image_name)

        # 捕获游戏窗口，判断是否在游戏窗口内进行截图
        screenshot_result = self.take_screenshot()
        if not screenshot_result:
            log.debug("截图失败")
            return None

        try:
            if target in self.img_cache:
                mask = self.img_cache[target]['mask']
                template = self.img_cache[target]['template']
            else:
                mask = ImageUtils.read_template_with_mask(target)  # 读取模板图片掩码
                template = cv2.imread(target)  # 读取模板图片
                self.img_cache[target] = {'mask': mask, 'template': template}

            # 将二进制数据转换为 OpenCV 图像（BGR 格式）
            screenshot = cv2.imdecode(np.frombuffer(screenshot_result, np.uint8), cv2.IMREAD_COLOR)

            if mask is not None:
                # 执行匹配模板
                if enable_scaling:
                    matchVal, matchLoc = ImageUtils.scale_and_match_template(screenshot, template, threshold, mask)
                else:
                    matchVal, matchLoc = ImageUtils.match_template(screenshot, template, threshold, mask)
            else:
                if enable_scaling:
                    matchVal, matchLoc = ImageUtils.scale_and_match_template(screenshot, template, threshold, mask)
                # 执行匹配模板
                else:
                    matchVal, matchLoc = ImageUtils.match_template(screenshot, template, threshold, None)

            # # 获取模板图像的宽度和高度
            # template_width = template.shape[1]
            # template_height = template.shape[0]
            #
            # # 在输入图像上绘制矩形框
            # top_left = matchLoc
            # bottom_right = (top_left[0] + template_width, top_left[1] + template_height)
            # cv2.rectangle(screenshot, top_left, bottom_right, (0, 255, 0), 2)
            #
            # # 显示标记了匹配位置的图像
            # resized_img = cv2.resize(screenshot, (640, 480))
            # cv2.imshow('Matched Image', resized_img)
            # cv2.waitKey(0)
            # cv2.destroyAllWindows()

            if matchVal > 0 and matchLoc != (-1, -1):
                log.debug(f"目标图片：{target.replace('./res/', '')} 相似度：{matchVal:.2f}")
                if mask is not None:
                    if not math.isinf(matchVal) and (threshold is None or matchVal <= threshold):
                        top_left, bottom_right = ImageUtils.calculate_center_position(template, matchLoc)
                        return top_left, bottom_right, matchVal
                else:
                    if not math.isinf(matchVal) and (threshold is None or matchVal >= threshold):
                        top_left, bottom_right = ImageUtils.calculate_center_position(template, matchLoc)
                        return top_left, bottom_right, matchVal

        except Exception as e:
            log.debug(f"目标图片路径未找到------：{target.replace('./res/', '')}")
            log.debug(f"寻找图片出错：{e}")
            traceback.print_exc()
        return None

    def click_element(self, target, threshold=0.9,enable_scaling=False):
        """
        查找并点击屏幕上的元素。

        参数:
        :param enable_scaling: 是否启用缩放功能
        :param target: 图片路径
        :param threshold: 查找阈值，用于图像查找时的相似度匹配。

        返回:
        如果找到元素并点击成功，则返回True；否则返回False。
        """
        coordinates = self.find_element(target, threshold,enable_scaling)
        if coordinates:
            top_left, bottom_right, _ = coordinates
            return self.click(top_left, bottom_right)
        return False


from pathlib import Path
import os
from core.ocr.PPOCR_api import GetOcrApi
from utils.ocr_analysis import OcrAnalysis



# 示例用法
if __name__ == "__main__":
    os.chdir('F:\\me\\HayDayHelper')
    orc_path = 'core/ocr/PaddleOCR/PaddleOCR-json.exe'
    ocr = GetOcrApi(orc_path)

    simulator = SimulatorController(16384)
    if simulator.connect():
        screenshot = simulator.take_screenshot(enhance=True)
        ocr_res = ocr.runBytes(screenshot)
        current_corner_texts = OcrAnalysis.get_corner_texts(ocr_res)
        print(f"当前获取的{current_corner_texts}")
        print(ocr_res)
        # print(simulator.find_element("./res/image/more1.png"))



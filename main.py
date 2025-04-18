import time
import keyboard
import threading
from core.log import log
from core.console import console
from core.ocr.PPOCR_api import GetOcrApi
from utils.ocr_analysis import OcrAnalysis
from core.simulator import simulator_controller as simulator

orc_path = 'core/ocr/PaddleOCR/PaddleOCR-json.exe'

# 全局停止标志
stop_flag = True
# 初始化计数器
counter = 1
# 存储报纸每页的数据
corner_texts_storage = {}
lock = threading.Lock()  # 线程锁
# 统计计数器
refresh_counter = 0


def keyboard_listener():
    global stop_flag
    log.info("键盘检测线程已启动 (按 q 停止)")

    def on_press(event):
        global stop_flag
        if event.name == 'q':
            with lock:
                log.info("检测到 q 键按下，停止程序...")
                stop_flag = False

    keyboard.on_press(on_press)

    while True:
        with lock:
            if not stop_flag:
                break
        time.sleep(0.1)

    # 停止键盘监听
    keyboard.unhook_all()


def main():
    global stop_flag, counter, corner_texts_storage, refresh_counter

    print("程序启动...")
    key, label = console.run()
    log.info(f"当前选择商品：{key}")

    if not simulator.connect():
        return

    ocr = GetOcrApi(orc_path)

    # 启动键盘监听线程
    keyboard_thread = threading.Thread(target=keyboard_listener, daemon=True)
    keyboard_thread.start()

    try:
        while True:
            with lock:
                if not stop_flag:
                    log.info("收到停止信号,即将退出主循环")
                    break

            log.debug(f"当前计数: {counter}")
            screenshot = simulator.take_screenshot(enhance=True)
            ocr_res = ocr.runBytes(screenshot)

            if counter <= 5:
                # 存储左页角标文本
                current_corner_texts = OcrAnalysis.get_corner_texts(ocr_res)
                current_corner_texts_all = OcrAnalysis.get_corner_texts(ocr_res, False)
                corner_texts_storage[counter] = current_corner_texts
                log.info(f"当前所在 {counter} 页,内容为：{current_corner_texts_all}")

                # 前4页处理逻辑
                locations = OcrAnalysis.find_trading_location(ocr_res, label)

                if len(locations) > 0:
                    for loc in locations:
                        center_x, center_y = loc
                        simulator.click(center_x, center_y)
                        time.sleep(1)

                        target = f"./res/image/{key}.png"
                        found = False
                        for _ in range(3):
                            if simulator.click_element(target, enable_scaling=True):
                                found = True
                                break

                            if simulator.find_element("./res/image/more1.png") or simulator.find_element(
                                    "./res/image/more2.png"):
                                simulator.swipe(1670.0, 450.0, 150.0, 450.0, 800)
                            else:
                                break

                        if found:
                            return
                        else:
                            log.info(f"未在小店中找到想要购买的 {label},将重新返回报纸进行刷新")
                            simulator.click_element("./res/image/return.png")
                            time.sleep(1)

                    log.info("遍历完所有位置都未找到目标，继续刷新报纸")
                    refresh_counter += 1
                    log.info(f"报纸已刷新 {refresh_counter} 次")
                    break
                else:
                    simulator.swipe(1670.0, 1030.0, 870.0, 1030.0)
                    time.sleep(1)
            else:
                screenshot = simulator.take_screenshot(enhance=True)
                ocr_res = ocr.runBytes(screenshot)

                # 获取当前页的 get_corner_texts
                current_corner_texts = OcrAnalysis.get_corner_texts(ocr_res)

                # 判断当前页属于哪一页
                current_page = None
                for stored_counter, stored_corner_texts in corner_texts_storage.items():
                    # 比较两个列表是否相同
                    if set(current_corner_texts) == set(stored_corner_texts):
                        current_page = stored_counter
                        break

                if current_page is not None:
                    log.info(f"当前页属于第 {current_page} 页,内容为：{current_corner_texts}")
                else:
                    log.info("页面已刷新,将再次查找")
                    refresh_counter += 1
                    log.info(f"报纸已刷新 {refresh_counter} 次")
                    corner_texts_storage = {counter: current_corner_texts}

                # 后4次遍历所有识别结果
                for result in ocr_res['data']:
                    # 每次循环时再次获取当前页的 get_corner_texts
                    screenshot = simulator.take_screenshot(enhance=True)
                    ocr_res = ocr.runBytes(screenshot)
                    current_corner_texts = OcrAnalysis.get_corner_texts(ocr_res)

                    # 判断当前页的 get_corner_texts 是否属于 corner_texts_storage
                    is_page_refreshed = True
                    for stored_corner_texts in corner_texts_storage.values():
                        if current_corner_texts == stored_corner_texts:
                            is_page_refreshed = False
                            break

                    if is_page_refreshed:
                        log.info("页面已刷新，停止当前循环并重置")
                        refresh_counter += 1
                        log.info(f"报纸已刷新 {refresh_counter} 次")
                        corner_texts_storage = {}
                        counter = 0
                        break  # 停止当前循环

                    box = result['box']
                    center_x = sum(p[0] for p in box) / 4
                    center_y = sum(p[1] for p in box) / 4

                    simulator.click(center_x, center_y)
                    time.sleep(1)

                    target = f"./res/image/{key}.png"
                    found = False
                    for _ in range(3):
                        with lock:
                            if not stop_flag:
                                return
                        if simulator.click_element(target):
                            found = True
                            break

                        if simulator.find_element("./res/image/more1.png") or simulator.find_element(
                                "./res/image/more2.png"):
                            simulator.swipe(1670.0, 450.0, 150.0, 450.0, 800)
                        else:
                            break

                    if found:
                        return
                    else:
                        log.info(f"未在小店中找到想要购买的 {label},将重新返回报纸进行刷新")
                        simulator.click_element("./res/image/return.png")
                        time.sleep(1.5)
                if counter < 1:
                    time.sleep(1)
                elif current_page >= 2:
                    simulator.swipe(200.0, 1030.0, 1670.0, 1030.0, 800)

            counter += 1
            with lock:
                if not stop_flag:
                    break

    finally:
        with lock:
            stop_flag = False
        keyboard_thread.join()
        log.info("程序已停止")
        log.info(f"报纸总共刷新了 {refresh_counter} 次")


if __name__ == '__main__':
    main()

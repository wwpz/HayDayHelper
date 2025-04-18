import time
import keyboard
import threading
from core.console import console
from core.ocr.PPOCR_api import GetOcrApi
from utils.ocr_analysis import OcrAnalysis
from core.simulator import simulator_controller as simulator

orc_path = 'core/ocr/PaddleOCR/PaddleOCR-json.exe'

# 全局停止标志
stop_flag = True
# 初始化计数器
counter = 0
# 存储报纸每页的数据
corner_texts_storage = {}
lock = threading.Lock()  # 线程锁


def keyboard_listener():
    global stop_flag
    print("键盘检测线程已启动 (按Q停止)")

    def on_press(event):
        global stop_flag
        if event.name == 'q':
            with lock:
                print("\n检测到Q键按下，停止程序...")
                stop_flag = False

    keyboard.on_press(on_press)

    while True:
        with lock:
            if not stop_flag:
                break
        time.sleep(0.1)

    keyboard.unhook_all()
    print("键盘监听已停止")


def main():
    global stop_flag, counter, corner_texts_storage

    print("程序启动...")
    key, label = console.run()

    if not simulator.connect():
        print("模拟器连接失败")
        return

    print("模拟器连接成功")
    ocr = GetOcrApi(orc_path)

    # 启动键盘监听线程
    keyboard_thread = threading.Thread(target=keyboard_listener, daemon=True)
    keyboard_thread.start()

    try:
        while True:
            with lock:
                if not stop_flag:
                    print("收到停止信号，退出主循环")
                    break

            print(f"\n当前计数: {counter}")
            screenshot = simulator.take_screenshot(enhance=True)
            ocr_res = ocr.runBytes(screenshot)

            # 存储左页角标文本
            current_corner_texts = OcrAnalysis.get_corner_texts(ocr_res)
            corner_texts_storage[counter] = current_corner_texts

            if counter < 4:
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
                            print(f"未在小店中找到想要购买的 {label},将重新返回报纸进行刷新")
                            simulator.click_element("./res/image/return.png")
                            time.sleep(1)

                    print("遍历完所有位置都未找到目标，继续刷新报纸")
                    break
                else:
                    simulator.swipe(1670.0, 1030.0, 870.0, 1030.0)
                    time.sleep(1)
            else:
                print("往回")
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
                    print(f"当前页属于第 {current_page} 页")
                else:
                    print("页面已刷新，重置存储的 corner_texts_storage")
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
                        print("页面已刷新，停止当前循环并重置")
                        corner_texts_storage = {}
                        counter = -1
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
                                break
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
                        print(f"未在小店中找到想要购买的 {label},将重新返回报纸进行刷新")
                        simulator.click_element("./res/image/return.png")
                        time.sleep(1.5)
                if counter < 0:
                    time.sleep(1)
                elif current_page >= 1:
                    simulator.swipe(200.0, 1030.0, 1670.0, 1030.0, 800)

            counter += 1
            with lock:
                if not stop_flag:
                    break

    finally:
        with lock:
            stop_flag = False
        keyboard_thread.join()
        print("程序已停止")


if __name__ == '__main__':
    main()

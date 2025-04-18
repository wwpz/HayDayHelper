import time
import keyboard
import threading
from core.console import console
from core.ocr.PPOCR_api import GetOcrApi
from utils.image_utils import ImageUtils
from utils.ocr_analysis import OcrAnalysis
from core.simulator import simulator_controller as simulator

orc_path = 'core/ocr/PaddleOCR/PaddleOCR-json.exe'

# 全局停止标志
stop_flag = True
# 初始化计数器
counter = 0
# 存储报纸每页的数据
corner_texts_storage = {}


def keyboard_listener():
    global stop_flag
    """键盘检测线程"""
    print("键盘检测线程已启动")

    def on_press(event):
        global stop_flag
        if event.name == 'q':  # 检测 q 键是否被按下
            print("q 键被按下，停止运行")
            stop_flag = False

    keyboard.on_press(on_press)  # 注册事件监听器

    while not stop_flag:
        time.sleep(0.1)  # 主循环延迟，减少 CPU 占用

    keyboard.unhook_all()  # 取消事件监听
    print("键盘检测线程已停止")


# 主逻辑
def main():
    global counter, corner_texts_storage
    print("Running main logic...")
    key, label = console.run()
    if simulator.connect():
        print("模拟器连接成功...")
        ocr = GetOcrApi(orc_path)
        # 启动键盘检测线程
        keyboard_thread = threading.Thread(target=keyboard_listener, daemon=True)
        keyboard_thread.start()
        # 翻页报纸
        while stop_flag:
            print(counter)
            screenshot = simulator.take_screenshot(enhance=True)
            ocr_res = ocr.runBytes(screenshot)
            print(ocr_res)
            # 获取当前页的 get_corner_texts 并存储
            current_corner_texts = ImageUtils.get_corner_texts(ocr_res)
            corner_texts_storage[counter] = current_corner_texts

            if counter < 4:
                # 前4次执行查找指定文本位置
                locations = OcrAnalysis.find_trading_location(ocr_res, label)
                # print(locations)

                if len(locations) > 0:
                    for loc in locations:
                        center_x, center_y = loc
                        simulator.click(center_x, center_y)
                        time.sleep(1)

                        target = f"./res/image/{key}.png"
                        found = False
                        for j in range(3):
                            if simulator.click_element(target,enable_scaling=True):
                                found = True
                                break
                            else:
                                if simulator.find_element("./res/image/more1.png") is not None or simulator.find_element("./res/image/more2.png") is not None:
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
                current_corner_texts = ImageUtils.get_corner_texts(ocr_res)

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
                    print(f"当前获取的{ocr_res}")
                    current_corner_texts = ImageUtils.get_corner_texts(ocr_res)

                    # 判断当前页的 get_corner_texts 是否属于 corner_texts_storage
                    is_page_refreshed = True
                    for stored_corner_texts in corner_texts_storage.values():
                        print(stored_corner_texts)
                        if current_corner_texts == stored_corner_texts:
                            is_page_refreshed = False
                            break

                    if is_page_refreshed:
                        print("页面已刷新，停止当前循环并重置")
                        corner_texts_storage = {}
                        counter = -1
                        break  # 停止当前循环

                    box = result['box']
                    x_coords = [point[0] for point in box]
                    y_coords = [point[1] for point in box]
                    center_x = sum(x_coords) / len(box)
                    center_y = sum(y_coords) / len(box)

                    simulator.click(center_x, center_y)
                    time.sleep(1)

                    target = f"./res/image/{key}.png"
                    found = False
                    for j in range(3):
                        if simulator.click_element(target):
                            found = True
                            break
                        else:
                            if simulator.find_element("./res/image/more1.png",enable_scaling=False) is not None or simulator.find_element("./res/image/more2.png",enable_scaling=False) is not None :
                                simulator.swipe(1670.0, 450.0, 150.0, 450.0, 800)
                            else:
                                break
                    if found:
                        return
                    else:
                        print(f"未在小店中找到想要购买的 {label},将重新返回报纸进行刷新")
                        simulator.click_element("./res/image/return.png",enable_scaling=False)
                        time.sleep(1.5)
                if counter < 0 :
                    time.sleep(1)
                elif current_page >= 1:
                    simulator.swipe(200.0, 1030.0, 1670.0, 1030.0, 800)

            counter += 1
        # 等待键盘检测线程结束
        keyboard_thread.join()
        print("任务已手动停止")
    else:
        print("Simulator disconnected.")


if __name__ == '__main__':
    main()

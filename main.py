import time
from core.console import console
from utils.ocr_analysis import OcrAnalysis
from core.ocr.PPOCR_api import GetOcrApi
from core.simulator import simulator_controller as simulator

orc_path = 'core/ocr/PaddleOCR/PaddleOCR-json.exe'


# 主逻辑
def main():
    print("Running main logic...")
    key, label = console.run()
    if simulator.connect():
        print("模拟器连接成功...")
        ocr = GetOcrApi(orc_path)
        # 翻页报纸
        for i in range(4):
            screenshot = simulator.take_screenshot(enhance=True)
            ocr_res = ocr.runBytes(screenshot)
            print(ocr_res)
            locations = OcrAnalysis.find_trading_location(ocr_res, label)
            print(locations)
            if len(locations) > 0:
                # 一页内找到了,并且只有一个
                if len(locations) == 1:
                    center_x, center_y = locations[0]
                    # 进入售卖的商店
                    simulator.click(center_x, center_y)
                    time.sleep(2)
                    # 找对应的图片/滑动售卖栏,循环3次
                    target = f"./res/image/{key}.png"
                    for j in range(3):
                        if not simulator.click_element(target):
                            simulator.swipe(1670.0, 450.0, 150.0, 450.0, 800)
                        else:
                            return
                    print(f"未在小店中找到想要购买的 {label},将重新返回报纸进行刷新")
                    simulator.click_element("./res/image/return.png")
                    time.sleep(2)



                else:
                    print("多个")

                    break
            else:
                simulator.swipe(1670.0, 1030.0, 870.0, 1030.0)
                time.sleep(2)

    else:
        print("Simulator disconnected.")


if __name__ == '__main__':
    main()

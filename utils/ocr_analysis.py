class OcrAnalysis:

    @staticmethod
    def find_trading_location(ocr_results, text, x_offset=0, y_offset=0):
        """
        从OCR结果中找到指定识别文本的中心点位置
        :param ocr_results: OCR识别结果，格式为 {'code': 100, 'data': [{'box': [[x1, y1], [x2, y2], ...], 'text': '...', ...}, ...]}
        :param text: 需要查找的文本，如 "小麦"
        :param x_offset: X 坐标偏移量（默认 0）
        :param y_offset: Y 坐标偏移量（默认 0）
        :return: 中心点坐标列表 [(center_x1, center_y1), (center_x2, center_y2), ...]，如果未找到则返回空列表 []
        """
        print(f"提取当前识别中心点位置: {text}")
        centers = []  # 用于存储找到的中心点坐标

        if ocr_results.get('code') != 100:
            print(f"OCR结果无效: {ocr_results}")
            return centers

        for result in ocr_results['data']:
            if result['text'] == text:
                box = result['box']
                x_coords = [point[0] for point in box]
                y_coords = [point[1] for point in box]
                center_x = sum(x_coords) / len(box) + x_offset
                center_y = sum(y_coords) / len(box) + y_offset
                print(f"找到文本 '{text}' 的中心点: ({center_x}, {center_y})")
                centers.append((center_x, center_y))

        if not centers:
            print(f"未找到文本: {text}")
        return centers

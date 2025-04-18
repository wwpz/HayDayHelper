from collections import defaultdict


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
        return centers

    @staticmethod
    def get_corner_texts(ocr_res, left_only=True):
        """
        根据 OCR 识别结果，获取文本值并按固定顺序排列。

        参数:
            ocr_res: OCR识别结果
            left_only: 布尔值，True表示只获取左侧文本，False表示获取所有文本
        """
        # 定义屏幕的中心 x 坐标
        center_x = 1920 / 2

        # 初始化结果列表
        filtered_texts = []

        # 遍历 OCR 识别结果，根据 box 坐标判断文本位置
        for result in ocr_res['data']:
            # 过滤掉置信度（score）低于 0.7 的识别结果
            if 'score' in result and result['score'] < 0.7:
                continue

            # 获取 box 的 x 和 y 坐标
            box = result['box']
            x_coords = [point[0] for point in box]
            y_coords = [point[1] for point in box]

            # 根据 left_only 参数决定是否过滤右侧文本
            if left_only and not all(x < center_x for x in x_coords):
                continue

            # 提取最小的 y 和 x 坐标（文本区域的最上方和最左侧）
            y_coord = min(y_coords)
            x_coord = min(x_coords)
            filtered_texts.append({
                'text': result['text'],
                'y': y_coord,
                'x': x_coord
            })

        # 按 y 坐标分组（将相近的 y 坐标视为同一行）
        y_threshold = 20  # 定义 y 坐标的阈值
        grouped_texts = defaultdict(list)
        for item in filtered_texts:
            # 找到最接近的 y 坐标组
            matched_y = None
            for y in grouped_texts.keys():
                if abs(y - item['y']) <= y_threshold:
                    matched_y = y
                    break
            if matched_y is None:
                matched_y = item['y']
            grouped_texts[matched_y].append(item)

        # 按 y 坐标从小到大排序，然后对每行内的文本按 x 坐标排序
        sorted_texts = []
        for y in sorted(grouped_texts.keys()):
            row_texts = sorted(grouped_texts[y], key=lambda item: item['x'])
            sorted_texts.extend([item['text'] for item in row_texts])

        return sorted_texts

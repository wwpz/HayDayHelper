import cv2
import numpy as np
from collections import defaultdict

class ImageUtils:
    @staticmethod
    def get_image_info(image_path):
        """
        获取图片的信息，如尺寸。
        :param image_path: 图片路径。
        :return: 图片的宽度和高度。
        """
        template = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        return template.shape[::-1]

    @staticmethod
    def match_template(screenshot, template, threshold=None, mask=None):
        """
        :param screenshot: 截图。
        :param template: 模板图片。
        :param threshold: 匹配阈值，小于此值的匹配将被忽略。
        :param mask: 模板的掩码，用于匹配透明区域。
        :return: 最大匹配值和最佳匹配位置。
        """
        if mask is not None:
            result = cv2.matchTemplate(screenshot, template, cv2.TM_SQDIFF, mask=mask)
            min_val, _, min_loc, _ = cv2.minMaxLoc(result)
            return min_val, min_loc
        else:
            result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        print(f"本次识图的结果为：max_val={max_val}, max_loc={max_loc}")
        # 检查最大匹配值是否满足阈值要求
        if threshold is not None and max_val < threshold:
            return 0.0, (-1, -1)  # 返回默认值

        return max_val, max_loc

    @staticmethod
    def scale_and_match_template(screenshot, template, threshold=None, mask=None, scale_range=(0.8, 1.1),
                                 scale_step=0.1, enable_scaling=True):
        """
        :param screenshot: 截图。
        :param template: 模板图片。
        :param threshold: 匹配阈值，小于此值的匹配将被忽略。
        :param mask: 模板的掩码，用于匹配透明区域。
        :param scale_range: 缩放比例范围，元组形式 (min_scale, max_scale)。
        :param scale_step: 缩放步长。
        :param enable_scaling: 是否启用缩放功能。
        :return: 最大匹配值、最佳匹配位置和最佳缩放比例。
        """
        best_max_val = 0.0
        best_max_loc = (-1, -1)

        if enable_scaling:
            min_scale, max_scale = scale_range
            current_scale = min_scale
        else:
            # 如果不启用缩放，则只使用原始比例（1.0）
            min_scale, max_scale = 1.0, 1.0
            current_scale = 1.0

        while current_scale <= max_scale:
            # 缩放模板图
            scaled_template = cv2.resize(template, None, fx=current_scale, fy=current_scale,
                                         interpolation=cv2.INTER_AREA)

            try:
                if mask is not None:
                    # 缩放掩码
                    scaled_mask = cv2.resize(mask, None, fx=current_scale, fy=current_scale,
                                             interpolation=cv2.INTER_AREA)
                    result = cv2.matchTemplate(screenshot, scaled_template, cv2.TM_SQDIFF, mask=scaled_mask)
                    min_val, _, min_loc, _ = cv2.minMaxLoc(result)
                    current_max_val = 1 - min_val  # 对于 TM_SQDIFF，取反以统一比较
                    current_max_loc = min_loc
                else:
                    result = cv2.matchTemplate(screenshot, scaled_template, cv2.TM_CCOEFF_NORMED)
                    _, current_max_val, _, current_max_loc = cv2.minMaxLoc(result)

                # print(f"缩放比例: {current_scale}, 匹配值: {current_max_val}, 匹配位置: {current_max_loc}")

                # 更新最佳匹配结果
                if current_max_val > best_max_val:
                    best_max_val = current_max_val
                    best_max_loc = current_max_loc

            except cv2.error as e:
                print(f"模板匹配出错（缩放比例 {current_scale}）: {e}")

            current_scale += scale_step

        # 检查最大匹配值是否满足阈值要求
        if threshold is not None and best_max_val < threshold:
            return 0.0, (-1, -1)  # 返回默认值

        return best_max_val, best_max_loc

    @staticmethod
    def scale_and_match_template_with_multiple_targets(screenshot, template, threshold=None, scale=None):
        """
        对模板进行缩放并匹配至截图，找出最佳匹配位置。
        :param screenshot: 截图。
        :param template: 模板图片。
        :param threshold: 匹配阈值，小于此值的匹配将被忽略。
        :param scale: 缩放值。
        :return: 匹配位置。
        """
        if scale is not None:
            template = cv2.resize(template, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        locations = np.where(result >= threshold)
        matches = ImageUtils.filter_overlapping_matches(locations, template.shape[::-1])
        return ImageUtils.convert_np_int64_to_int(matches)

    @staticmethod
    def read_template_with_mask(target):
        """
        读取模板图片，并根据需要生成掩码。
        :param target: 目标图片路径。
        :return: 掩码（如果有透明通道）。
        """
        template = cv2.imread(target, cv2.IMREAD_UNCHANGED)  # 保留图片的透明通道
        if template is None:
            raise ValueError(f"读取图片失败：{target}")
        mask = None
        if template.shape[-1] == 4:  # 检查通道数是否为4（含有透明通道）
            alpha_channel = template[:, :, 3]
            if np.any(alpha_channel < 255):  # 检查是否存在非完全透明的像素
                mask = alpha_channel
        return mask

    @staticmethod
    def intersected(top_left1, botton_right1, top_left2, botton_right2):
        """判断两个矩形是否相交。

        参数:
        - top_left1: 第一个矩形的左上角坐标 (x, y)。
        - botton_right1: 第一个矩形的右下角坐标 (x, y)。
        - top_left2: 第二个矩形的左上角坐标 (x, y)。
        - botton_right2: 第二个矩形的右下角坐标 (x, y)。

        返回:
        - bool: 如果矩形相交返回True，否则返回False。

        逻辑说明:
        - 如果一个矩形在另一个矩形的右侧或左侧，它们不相交。
        - 如果一个矩形在另一个矩形的上方或下方，它们也不相交。
        - 否则，矩形相交。
        """
        # 检查矩形1是否在矩形2的右侧或矩形2是否在矩形1的右侧
        if top_left1[0] > botton_right2[0] or top_left2[0] > botton_right1[0]:
            return False
        # 检查矩形1是否在矩形2的下方或矩形2是否在矩形1的下方
        if top_left1[1] > botton_right2[1] or top_left2[1] > botton_right1[1]:
            return False
        # 上述条件都不成立，则矩形相交
        return True

    @staticmethod
    def is_match_non_overlapping(top_left, matches, width, height):
        """检查给定的匹配位置是否与已有的匹配重叠。

        参数:
        - top_left: 当前匹配的左上角坐标。
        - matches: 已有的匹配位置列表。
        - width: 模板宽度。
        - height: 模板高度。

        返回:
        - bool: 是否不重叠。
        """
        botton_right = (top_left[0] + width, top_left[1] + height)
        for match_top_left in matches:
            match_botton_right = (match_top_left[0] + width, match_top_left[1] + height)
            if ImageUtils.intersected(top_left, botton_right, match_top_left, match_botton_right):
                return False
        return True

    @staticmethod
    def filter_overlapping_matches(locations, template_size):
        """过滤掉重叠的匹配。

        参数:
        - locations: 匹配的位置数组。
        - template_size: 模板图片的大小 (宽度, 高度)。

        返回:
        - matches: 不重叠的匹配位置列表。
        """
        matches = []
        width, height = template_size
        for top_left in zip(*locations[::-1]):
            if ImageUtils.is_match_non_overlapping(top_left, matches, width, height):
                matches.append(top_left)
        return matches

    @staticmethod
    def count_template_matches(target, template, threshold):
        """使用模板匹配计算目标图片中的匹配数。

        参数:
        - target: 目标图片数组。
        - template: 模板图片数组。
        - threshold: 匹配阈值，用于决定哪些结果被认为是匹配。

        返回:
        - match_count: 匹配的数量。
        """
        # 执行模板匹配
        result = cv2.matchTemplate(target, template, cv2.TM_CCOEFF_NORMED)
        locations = np.where(result >= threshold)

        matches = ImageUtils.filter_overlapping_matches(locations, template.shape[::-1])

        # 返回匹配数量
        return len(matches)

    @staticmethod
    def calculate_center_position(template, max_loc):
        """
        计算匹配位置的中心坐标。
        :param template: 模板图片。
        :param max_loc: 最佳匹配位置。
        :return: 匹配位置的中心坐标。
        """
        # 获取模板的宽度和高度
        width, height = template.shape[1], template.shape[0]

        # 计算中心坐标
        center_x = max_loc[0] + width // 2
        center_y = max_loc[1] + height // 2
        return center_x, center_y

    @staticmethod
    def get_corner_texts(ocr_res):
        """
        根据 OCR 识别结果，获取某一侧（左侧）的文本值，并按固定顺序排列。
        """
        # 定义屏幕的中心 x 坐标
        center_x = 1920 / 2

        # 初始化结果列表
        left_side_texts = []

        # 遍历 OCR 识别结果，根据 box 坐标判断文本位置
        for result in ocr_res['data']:
            # 过滤掉置信度（score）低于 0.7 的识别结果
            if 'score' in result and result['score'] < 0.7:
                continue

            # 获取 box 的 x 和 y 坐标
            box = result['box']
            x_coords = [point[0] for point in box]
            y_coords = [point[1] for point in box]

            # 判断文本是否在左侧（x 坐标小于中心点）
            if all(x < center_x for x in x_coords):
                # 提取最小的 y 和 x 坐标（文本区域的最上方和最左侧）
                y_coord = min(y_coords)
                x_coord = min(x_coords)
                left_side_texts.append({
                    'text': result['text'],
                    'y': y_coord,
                    'x': x_coord
                })
                # print(f"Added text: {result['text']}, y: {y_coord}, x: {x_coord}")

        # 按 y 坐标分组（将相近的 y 坐标视为同一行）
        y_threshold = 20  # 定义 y 坐标的阈值
        grouped_texts = defaultdict(list)
        for item in left_side_texts:
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

        print(f"sorted_texts: {sorted_texts}")
        return sorted_texts


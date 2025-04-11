# import json
# from collections import defaultdict
#
#
# class ConsoleInput:
#     _instance = None
#
#     def __new__(cls, config_file=None):
#         if cls._instance is None:
#             cls._instance = super().__new__(cls)
#             cls._instance._initialized = False
#         return cls._instance
#
#     def __init__(self, config_file):
#         if not self._initialized:
#             self.config = self.load_config(config_file)
#             self.menu_stack = ["main"]
#             self.selection_states = defaultdict(dict)
#             self.shopping_cart = defaultdict(set)
#             self.init_states()
#             self.current_operation = None
#             self._initialized = True
#
#     def init_states(self):
#         for menu_name, menu_data in self.config.items():
#             self.selection_states[menu_name] = {
#                 'options': [item.copy() for item in menu_data['options']],
#                 'selected': set()
#             }
#
#     @staticmethod
#     def load_config(config_file):
#         with open(config_file, 'r', encoding='utf-8') as f:
#             return json.load(f)['menus']
#
#     def show_current_menu(self):
#         current_menu = self.menu_stack[-1]
#         menu_config = self.config[current_menu]
#         state = self.selection_states[current_menu]
#
#         print(f"\n=== {menu_config['title']} ===")
#         self.show_current_selections()  # 显示当前选择
#
#         for item in state['options']:
#             prefix = "[✓] " if item['label'] in state['selected'] else "[ ] "
#             action_desc = self.get_action_description(item)
#             print(f"{item['key']:>2}. {prefix if menu_config['multi_select'] else ''}{item['label']}{action_desc}")
#
#     def show_current_selections(self):
#         """实时显示当前选择状态"""
#         # 显示全局购物车内容
#         all_items = [item for sublist in self.shopping_cart.values() for item in sublist]
#         if all_items:
#             print(f"当前已选择: {', '.join(all_items)}")
#         else:
#             print("当前未选择")
#
#     def get_action_description(self, item):
#         if 'action' not in item:
#             return ""
#         action_type = item['action']['type']
#         descriptors = {
#
#         }
#         return descriptors.get(action_type, "")
#
#     def process_selection(self):
#         current_menu = self.menu_stack[-1]
#         menu_config = self.config[current_menu]
#
#         while True:
#             try:
#                 prompt = "请选择商品（多选用逗号分隔）: " if menu_config['multi_select'] else "请选择操作: "
#                 raw = input(prompt).strip()
#
#                 if not raw:
#                     raise ValueError("输入不能为空")
#
#                 # 处理用户输入
#                 selections = set()
#                 for input_item in raw.split(','):
#                     input_item = input_item.strip()
#                     if input_item.isdigit():
#                         # 如果是数字，按编号处理
#                         selections.add(int(input_item))
#                     else:
#                         # 如果是名称，按名称处理
#                         for item in self.selection_states[current_menu]['options']:
#                             if item['label'] == input_item:
#                                 selections.add(item['key'])
#                                 break
#                         else:
#                             raise ValueError(f"未找到商品: {input_item}")
#
#                 valid_keys = {item['key'] for item in self.selection_states[current_menu]['options']}
#
#                 if not selections.issubset(valid_keys):
#                     raise ValueError("包含无效选项")
#
#                 return self.handle_choices(current_menu, selections)
#             except ValueError as e:
#                 print(f"输入错误: {str(e)}")
#
#     def handle_choices(self, menu_name, choices):
#         menu_config = self.config[menu_name]
#         state = self.selection_states[menu_name]
#
#         # 优先处理功能操作
#         for key in list(choices):
#             item = next(i for i in state['options'] if i['key'] == key)
#             if 'action' in item:
#                 # 调用 handle_action 并捕获返回值
#                 should_exit = self.handle_action(item['action'], menu_name)
#                 if should_exit:
#                     return True  # 返回标志，表示需要结束循环
#                 choices.discard(key)
#
#         # 处理普通选择
#         if menu_config['multi_select']:
#             for item in state['options']:
#                 if item['key'] in choices and 'action' not in item:
#                     # 直接切换选择状态
#                     if item['label'] in state['selected']:
#                         state['selected'].remove(item['label'])
#                         self.shopping_cart[menu_name].discard(item['label'])  # 从购物车中移除
#                     else:
#                         state['selected'].add(item['label'])
#                         self.shopping_cart[menu_name].add(item['label'])  # 添加到购物车中
#         return False  # 默认返回 False，表示不需要结束循环
#
#     def handle_action(self, action, current_menu):
#         action_type = action['type']
#
#         if action_type == 'confirm':
#             self.commit_selections(current_menu)
#             print("已返回主菜单")
#
#         elif action_type == 'execute':
#             self.show_receipt()
#             return True  # 返回标志，表示需要结束循环
#
#         elif action_type == 'exit':
#             exit()
#
#         elif action_type == 'switch_menu':
#             self.menu_stack.append(action['target'])
#
#         return False  # 默认返回 False，表示不需要结束循环
#
#     def commit_selections(self, menu_name):
#         """提交当前菜单选择到购物车"""
#         current_selections = self.selection_states[menu_name]['selected']
#         if current_selections:
#             self.shopping_cart[menu_name] = current_selections.copy()
#             print(f"已保存【{self.config[menu_name]['title']}】选择")
#         self.menu_stack = ["main"]
#
#     def show_receipt(self):
#         """增强的购物清单显示"""
#         print("\n=== 购买明细 ===")
#         total = 0
#         for menu_name, items in self.shopping_cart.items():
#             if items:
#                 menu_title = self.config[menu_name]['title']
#                 print(f"{menu_title}:")
#                 for item in sorted(items):
#                     print(f"  - {item}")
#                 total += len(items)
#         print(f"\n总计 {total} 项商品")
#         print("=" * 30)
#
#     def run(self):
#         while True:
#             self.show_current_menu()
#             should_exit = self.process_selection()
#             all_items = []  # 用于存储所有元素的列表
#             for items in self.shopping_cart.values():
#                 if items:  # 如果集合不为空
#                     all_items.extend(items)  # 将集合中的元素添加到列表中
#             if should_exit:
#                 break  # 结束循环
#         return all_items
#
# from pathlib import Path
#
# if __name__ == "__main__":
#     config_path = Path(__file__).parent / 'F:\\me\\HayDayHelper\\res\\menu_config.json'
#     system = ConsoleInput(config_path)
#     system.run()
#     print("ok")

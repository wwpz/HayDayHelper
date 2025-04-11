import json
from collections import defaultdict


class ConsoleInput:
    _instance = None

    def __new__(cls, config_file=None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config_file):
        if not self._initialized:
            self.config = self.load_config(config_file)
            self.menu_stack = ["main"]
            self.selection_states = defaultdict(dict)
            self.shopping_cart = {}  # 改为字典存储单选结果
            self.init_states()
            self.current_operation = None
            self._initialized = True

    def init_states(self):
        for menu_name, menu_data in self.config.items():
            self.selection_states[menu_name] = {
                'options': [item.copy() for item in menu_data['options']],
                'selected': None  # 单选使用None或字符串
            }

    @staticmethod
    def load_config(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)['menus']
        # 强制所有菜单为单选
        for menu in config.values():
            menu['multi_select'] = False
        return config

    def show_current_menu(self):
        current_menu = self.menu_stack[-1]
        menu_config = self.config[current_menu]
        state = self.selection_states[current_menu]

        print(f"\n=== {menu_config['title']} ===")
        self.show_current_selections()

        for item in state['options']:
            prefix = "[✓] " if item['label'] == state['selected'] else "[ ] "
            action_desc = self.get_action_description(item)
            print(f"{item['key']:>2}. {prefix}{item['label']}{action_desc}")

    def show_current_selections(self):
        """显示已提交到购物车的内容"""
        if self.shopping_cart:
            items = [f"{self.config[menu]['title']}: {label}" for menu, label in self.shopping_cart.items()]
            print("当前已选择: " + "; ".join(items))
        else:
            print("当前未选择")

    def get_action_description(self, item):
        if 'action' not in item:
            return ""
        action_type = item['action']['type']
        descriptors = {

        }
        return descriptors.get(action_type, "")

    def process_selection(self):
        current_menu = self.menu_stack[-1]

        while True:
            try:
                prompt = "请选择操作: "
                raw = input(prompt).strip()

                if not raw:
                    raise ValueError("输入不能为空")

                # 处理单选输入
                input_item = raw.strip()
                key = None
                if input_item.isdigit():
                    key = int(input_item)
                else:
                    for item in self.selection_states[current_menu]['options']:
                        if item['label'] == input_item:
                            key = item['key']
                            break
                    if key is None:
                        raise ValueError(f"无效选项: {input_item}")

                valid_keys = {item['key'] for item in self.selection_states[current_menu]['options']}
                if key not in valid_keys:
                    raise ValueError("无效选项")

                return self.handle_choices(current_menu, {key})
            except ValueError as e:
                print(f"输入错误: {str(e)}")

    def handle_choices(self, menu_name, choices):
        state = self.selection_states[menu_name]

        # 处理功能操作
        for key in list(choices):
            item = next(i for i in state['options'] if i['key'] == key)
            if 'action' in item:
                should_exit = self.handle_action(item['action'], menu_name)
                if should_exit:
                    return True
                choices.discard(key)

        # 处理单选逻辑
        if choices:
            selected_key = choices.pop()
            selected_item = next(item for item in state['options'] if item['key'] == selected_key)
            if 'action' not in selected_item:
                state['selected'] = selected_item['label'] if state['selected'] != selected_item['label'] else None

        # 新增：自动保存有效选择到购物车
        if state['selected']:
            self.shopping_cart[menu_name] = state['selected']

        return False

    def handle_action(self, action, current_menu):
        action_type = action['type']

        if action_type == 'confirm':
            self.commit_selections(current_menu)
            print("已返回主菜单")
        elif action_type == 'execute':
            self.show_receipt()
            return True
        elif action_type == 'exit':
            exit()
        elif action_type == 'switch_menu':
            self.menu_stack.append(action['target'])

        return False

    def commit_selections(self, menu_name):
        """提交当前选择到购物车"""
        current_selection = self.selection_states[menu_name]['selected']
        if current_selection is not None:
            self.shopping_cart[menu_name] = current_selection
            print(f"【{self.config[menu_name]['title']}】选择已保存: {current_selection}")
        self.menu_stack = ["main"]

    def show_receipt(self):
        print("\n=== 购买明细 ===")
        total = 0
        for menu_name, item in self.shopping_cart.items():
            menu_title = self.config[menu_name]['title']
            print(f"{menu_title}: {item}")
            total += 1
        print(f"\n总计 {total} 项商品")
        print("=" * 30)

    def run(self):
        while True:
            self.show_current_menu()
            should_exit = self.process_selection()
            if should_exit:
                break
        # 返回购物车中的 label 和对应的 key
        if self.shopping_cart:
            menu_name = next(iter(self.shopping_cart))  # 获取菜单名称
            label = self.shopping_cart[menu_name]  # 获取 label
            key = next(
                item['key'] for item in self.selection_states[menu_name]['options']
                if item['label'] == label
            )  # 根据 label 找到对应的 key
            return key, label
        return None, None


from pathlib import Path

if __name__ == "__main__":
    config_path = Path(__file__).parent / 'F:\\me\\HayDayHelper\\res\\menu_config.json'
    system = ConsoleInput(config_path)
    item = system.run()
    print(item)

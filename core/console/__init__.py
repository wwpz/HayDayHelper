import os
from .console_input import ConsoleInput

config_path = './res/menu_config.json'
if not os.path.exists(config_path):
    raise print(f"orc_path file not found: {config_path}")

console = ConsoleInput(config_path)

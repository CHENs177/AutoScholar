import os
from pathlib import Path

# 获取项目根目录的绝对路径
BASE_DIR = Path(__file__).resolve().parent.parent

# 目录定义
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"
CONFIG_DIR = BASE_DIR / "config"

# 提纲路径 
OUTLINE_PATH = CONFIG_DIR / "outline.txt"

# API 配置 (这里可以手动填，或者之后教你用 python-dotenv 库)
API_KEY = "你的Key" 
BASE_URL = "你的中转地址/v1"

# 确保基础目录存在
for d in [INPUT_DIR, OUTPUT_DIR, CONFIG_DIR]:
    d.mkdir(exist_ok=True)
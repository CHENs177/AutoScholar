import os
from pathlib import Path
from dotenv import load_dotenv

# 获取项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent

# 加载 .env 文件 (它会自动寻找根目录下的 .env)
load_dotenv(BASE_DIR / ".env")

# 目录定义
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"
CONFIG_DIR = BASE_DIR / "config"
OUTLINE_PATH = CONFIG_DIR / "outline.txt"

# 动态读取 API 配置
API_KEY = os.getenv("OPENAI_API_KEY")
BASE_URL = os.getenv("OPENAI_BASE_URL")

# 确保基础目录存在
for d in [INPUT_DIR, OUTPUT_DIR, CONFIG_DIR]:
    d.mkdir(exist_ok=True)
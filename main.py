from core.config import OUTLINE_PATH
from core.folder_manager import create_structure_from_outline

def init_project():
    if not OUTLINE_PATH.exists():
        print(f"错误：找不到提纲文件 {OUTLINE_PATH}")
        return

    with open(OUTLINE_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    create_structure_from_outline(content)

if __name__ == "__main__":
    init_project()
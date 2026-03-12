import openai
import sys
from core.config import API_KEY, BASE_URL

# 强制设置输出编码，防止终端显示乱码
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


def test_connection():
    # 检查是否还是占位符
    if "你的" in BASE_URL or "你的" in API_KEY:
        print("错误：检测到 .env 文件中仍包含中文占位符，请先替换为真实的 API 信息。")
        return

    print(f"正在尝试连接至: {BASE_URL}")
    client = openai.OpenAI(api_key=API_KEY, base_url=BASE_URL)

    try:
        response = client.chat.completions.create(
            model="gpt-4o",  # 确保这个模型在你的中转套餐内
            messages=[{"role": "user", "content": "Hello, confirm connection."}]
        )
        print("✅ API 连接成功！")
        print("回复内容：", response.choices[0].message.content)
    except Exception as e:
        print(f"❌ API 连接失败")
        print(f"具体错误信息: {str(e)}")


if __name__ == "__main__":
    test_connection()
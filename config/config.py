# 配置文件 - 使用 python-dotenv 加载环境变量
import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# DeepSeek API 配置
API_KEY = os.getenv('DEEPSEEK_API_KEY', 'your-api-key-here')
API_URL = os.getenv('DEEPSEEK_API_URL', 'https://api.deepseek.com/v1/chat/completions')
MODEL = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')

# API 参数配置
TEMPERATURE = float(os.getenv('API_TEMPERATURE', '0.7'))
MAX_TOKENS = int(os.getenv('API_MAX_TOKENS', '150'))

# 验证必要配置
if API_KEY == 'your-api-key-here':
    print("⚠️  警告：未设置 DEEPSEEK_API_KEY，请在 .env 文件中配置")

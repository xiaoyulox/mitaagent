import requests
from config.config import API_URL, API_KEY, MODEL, TEMPERATURE, MAX_TOKENS
from utils.prompt import MITA_PROMPT
from database.db_operations import db_ops
from context.context_manager import ContextManager

context_manager = ContextManager()


def get_mita_response(user_input):
    # 分析用户输入并更新状态
    context_manager.analyze_sentiment_and_update_state(user_input)
    
    # 获取当前状态下的个性提示
    personality_prompt = context_manager.get_personality_prompt_by_state()
    
    # 获取历史对话上下文
    context_history = context_manager.get_context_history()
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    # 构建消息历史
    messages = [
        {"role": "system", "content": f"{MITA_PROMPT}\n\n{personality_prompt}"}
    ]
    
    # 如果有历史对话，将其添加到消息中
    if context_history:
        messages.append({"role": "system", "content": f"之前的对话历史：\n{context_history}"})
    
    # 添加当前用户输入
    messages.append({"role": "user", "content": user_input})
    
    data = {
        "model": MODEL,
        "messages": messages,
        "temperature": TEMPERATURE,
        "max_tokens": MAX_TOKENS
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        mita_response = result['choices'][0]['message']['content']
        # 保存对话到数据库
        db_ops.save_conversation(user_input, mita_response)
        return mita_response
    except Exception as e:
        print(f"错误: {e}")
        error_response = "呜…好像出了点问题呢… 能再试一次吗？"
        # 保存错误对话到数据库
        db_ops.save_conversation(user_input, error_response)
        return error_response
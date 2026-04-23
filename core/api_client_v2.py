import requests
from config.config import API_URL, API_KEY, MODEL, TEMPERATURE, MAX_TOKENS
from utils.prompt import MITA_PROMPT
from database.db_operations_v2 import db_ops_v2
from context.smart_context_manager import smart_context_manager
from context.user_profile import user_profile
from context.feedback_manager import feedback_manager
from utils.logger import log_info, log_error, log_warning
from utils.performance_monitor import perf_monitor
import time


@perf_monitor.track_api_call
def get_mita_response(user_input, max_retries=2, timeout=15):
    """获取米塔的回复，带重试机制和超时处理
    
    Args:
        user_input: 用户输入
        max_retries: 最大重试次数（默认2次，避免过多等待）
        timeout: 超时时间（默认15秒，从30秒降低）
    """
    # 分析用户输入并更新状态
    smart_context_manager.analyze_sentiment_and_update_state(user_input)
    
    # 获取当前状态下的个性提示
    personality_prompt = smart_context_manager.get_personality_prompt_by_state()
    
    # 获取历史对话上下文
    context_history = smart_context_manager.get_context_history()
    
    # 获取个性化用户画像上下文
    user_context = user_profile.get_personalized_context()
    
    # 获取风格偏好提示
    style_prompt = feedback_manager.get_style_prompt()
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    # 构建消息历史
    system_content = f"{MITA_PROMPT}\n\n{personality_prompt}\n\n{user_context}"
    if style_prompt:
        system_content += f"\n\n📝 用户风格偏好：\n{style_prompt}"
    
    messages = [
        {"role": "system", "content": system_content}
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
    
    # 重试机制
    for attempt in range(max_retries):
        try:
            log_info(f"正在发送API请求，第 {attempt + 1} 次尝试")
            response = requests.post(API_URL, headers=headers, json=data, timeout=timeout)
            
            if response.status_code == 429:  # 配额耗尽
                log_warning("API配额耗尽，稍后重试")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # 指数退避
                    continue
                else:
                    error_response = "呜…我现在有点忙，暂时无法回复你…能稍后再试试吗？"
                    db_ops_v2.save_conversation(user_input, error_response)
                    return error_response
            
            response.raise_for_status()
            result = response.json()
            mita_response = result['choices'][0]['message']['content']
            
            # 保存对话到数据库
            if db_ops_v2.save_conversation(user_input, mita_response):
                log_info("对话记录保存成功")
            else:
                log_error("对话记录保存失败")
            
            log_info("成功获取米塔回复")
            return mita_response
            
        except requests.exceptions.Timeout:
            log_error(f"API请求超时 (尝试 {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # 指数退避
            else:
                error_response = "呜…网络好像不太顺畅呢…能再试一次吗？"
                db_ops_v2.save_conversation(user_input, error_response)
                return error_response
                
        except requests.exceptions.ConnectionError:
            log_error(f"连接错误 (尝试 {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # 指数退避
            else:
                error_response = "呜…连接服务器遇到了一些困难…请稍后再试…"
                db_ops_v2.save_conversation(user_input, error_response)
                return error_response
                
        except KeyError as e:
            log_error(f"解析API响应失败: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                error_response = "呜…服务器返回的信息有些混乱呢…能再告诉我一次吗？"
                db_ops_v2.save_conversation(user_input, error_response)
                return error_response
                
        except Exception as e:
            log_error(f"API请求发生未知错误: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                error_response = "呜…好像出了点问题呢…能再试一次吗？"
                db_ops_v2.save_conversation(user_input, error_response)
                return error_response
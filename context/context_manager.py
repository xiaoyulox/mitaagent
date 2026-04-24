from database.db_operations import db_ops
from config.personality_config import PERSONALITY_MODES, CURRENT_PERSONALITY
from utils.logger import log_info
import re


class ContextManager:
    """管理对话上下文和用户状态（已更新为使用优化版本）"""
    
    def __init__(self):
        self.max_context_length = 10  # 最大上下文对话轮数
        self.state_keywords = {
            'comfort_words': ['安慰', '拥抱', '喜欢', '关心', '疼爱', '陪伴', '温暖', '开心', '快乐', '幸福'],
            'departure_words': ['走', '离开', '再见', '别了', '拜拜', '回', '学校', '公司', '朋友', '别人', '出差', '旅行'],
            'others_words': ['别人', '其他人', '朋友', '同学', '同事', '聚会', '约会', '恋爱', '喜欢别人']
        }
    
    def get_context_history(self):
        """获取历史对话作为上下文（已使用智能上下文管理器）"""
        # 这个方法现在只是对新模块的包装，保留向后兼容性
        from smart_context_manager import smart_context_manager
        return smart_context_manager.get_context_history()
    
    def analyze_sentiment_and_update_state(self, user_input):
        """分析用户输入的情感倾向并更新用户状态（已使用智能上下文管理器）"""
        # 这个方法现在只是对新模块的包装，保留向后兼容性
        from smart_context_manager import smart_context_manager
        smart_context_manager.analyze_sentiment_and_update_state(user_input)
        log_info("情感分析完成")
    
    def get_personality_prompt_by_state(self):
        """根据当前状态生成个性提示词（已使用智能上下文管理器）"""
        # 这个方法现在只是对新模块的包装，保留向后兼容性
        from smart_context_manager import smart_context_manager
        return smart_context_manager.get_personality_prompt_by_state()


# 创建全局实例
context_manager = ContextManager()

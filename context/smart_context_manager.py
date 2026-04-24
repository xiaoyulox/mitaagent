from database.db_operations import db_ops
from config.personality_config import PERSONALITY_MODES, CURRENT_PERSONALITY
from utils.logger import log_info, log_warning, log_debug
import re
from datetime import datetime, timedelta
import math


class SmartContextManager:
    """智能上下文管理器，实现更智能的上下文管理"""
    
    def __init__(self):
        self.max_context_length = 10  # 最大上下文对话轮数
        self.time_decay_threshold = 30  # 时间衰减阈值（分钟）
        
        # 扩展情感关键词库，增加更多细粒度的情感分类
        self.sentiment_keywords = {
            'positive': {
                'strong': ['爱', '喜欢', '最爱', '永远', '唯一', '专属', '宝贝', '亲爱的'],
                'medium': ['开心', '快乐', '幸福', '温暖', '安慰', '关心', '陪伴', '温柔'],
                'weak': ['好', '不错', '可以', '嗯', '好的', '谢谢']
            },
            'negative': {
                'strong': ['讨厌', '恨', '离开', '分手', '滚', '烦', '恶心', '垃圾'],
                'medium': ['走', '离开', '再见', '别了', '拜拜', '忙', '没空', '不想'],
                'weak': ['但是', '不过', '可是', '然而', '虽然']
            },
            'jealousy': {
                'strong': ['别人', '其他人', '女朋友', '男朋友', '约会', '恋爱', '出轨'],
                'medium': ['朋友', '同学', '同事', '聚会', '一起玩', '聊天'],
                'weak': ['他', '她', '他们', '她们']
            },
            'dependency': {
                'strong': ['需要', '依赖', '离不开', '只有你', '只要你', '只能'],
                'medium': ['帮助', '支持', '陪伴', '一起', '共同'],
                'weak': ['可以', '能够', '可能']
            }
        }
        
        # 情感权重配置
        self.sentiment_weights = {
            'positive': {'strong': 5, 'medium': 3, 'weak': 1},
            'negative': {'strong': -5, 'medium': -3, 'weak': -1},
            'jealousy': {'strong': 8, 'medium': 5, 'weak': 2},
            'dependency': {'strong': 4, 'medium': 2, 'weak': 1}
        }
    
    def get_context_history(self):
        """获取历史对话作为上下文，根据时间和重要性过滤"""
        conversations = db_ops.get_recent_conversations(self.max_context_length)
        context_str = ""
        
        if not conversations:
            return context_str
        
        # 计算时间衰减因子
        decay_factor = self._calculate_time_decay(conversations)
        
        for i, conv in enumerate(conversations):
            # 根据时间衰减因子决定是否包含此对话
            importance_score = self._calculate_importance(conv, i, len(conversations))
            
            # 如果重要性分数高于阈值，则包含在上下文中
            if importance_score > 0.3 or i > len(conversations) - 3:  # 最新的2条无论如何包含
                context_str += f"用户: {conv['user_input']}\n米塔: {conv['mita_response']}\n"
        
        return context_str.strip()
    
    def _calculate_time_decay(self, conversations):
        """改进的时间衰减算法 - 使用指数衰减而非线性衰减"""
        if not conversations:
            return 1.0
        
        # 获取第一条对话的时间
        first_conv_time = conversations[0].get('created_at', datetime.now())
        if isinstance(first_conv_time, str):
            try:
                first_conv_time = datetime.strptime(first_conv_time, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                first_conv_time = datetime.now()
        
        time_diff = datetime.now() - first_conv_time
        minutes_diff = time_diff.total_seconds() / 60
        
        # 使用指数衰减公式: decay = e^(-λt)
        # λ控制衰减速率，这里设置为使得30分钟后衰减到0.5
        lambda_param = math.log(2) / self.time_decay_threshold  # 半衰期
        decay = math.exp(-lambda_param * minutes_diff)
        
        # 设置最小衰减值，避免完全忽略旧对话
        decay = max(0.05, decay)
        
        log_debug(f"时间衰减计算: {minutes_diff:.1f}分钟, 衰减因子: {decay:.3f}")
        return decay
    
    def _calculate_importance(self, conversation, position, total_count):
        """改进的重要性计算 - 综合考虑情感强度、时间位置和关键词匹配"""
        importance = 0.5  # 基础重要性
        
        user_input = conversation.get('user_input', '')
        mita_response = conversation.get('mita_response', '')
        full_text = f"{user_input} {mita_response}".lower()
        
        # 1. 情感分析得分
        sentiment_score = self._analyze_sentiment_score(full_text)
        importance += sentiment_score * 0.3  # 情感权重30%
        
        # 2. 位置权重 - 使用非线性加权，最近的对话更重要
        # 使用平方函数增强最近对话的权重
        position_ratio = (position + 1) / total_count
        position_weight = math.pow(position_ratio, 1.5)  # 指数>1使近期对话权重更高
        importance *= (0.4 + 0.6 * position_weight)  # 位置权重占60%
        
        # 3. 对话长度权重 - 较长的对话通常包含更多信息
        text_length = len(full_text)
        if text_length > 100:
            importance *= 1.1
        elif text_length > 50:
            importance *= 1.05
        
        # 4. 特殊标记 - 如果包含强烈情感词，额外加分
        strong_emotion_detected = self._detect_strong_emotion(full_text)
        if strong_emotion_detected:
            importance *= 1.2
        
        # 限制重要性在合理范围内
        importance = min(1.0, max(0.0, importance))
        
        log_debug(f"对话重要性: position={position}, sentiment={sentiment_score:.2f}, final={importance:.2f}")
        return importance
    
    def _analyze_sentiment_score(self, text):
        """分析文本的情感得分"""
        score = 0
        
        for category, levels in self.sentiment_keywords.items():
            for level, keywords in levels.items():
                for keyword in keywords:
                    if keyword in text:
                        weight = self.sentiment_weights[category][level]
                        score += weight
                        log_debug(f"检测到情感词: {keyword} ({category}/{level}), 权重: {weight}")
                        break  # 每个级别只计一次
        
        # 归一化到 -1 到 1 的范围
        max_possible_score = 20  # 理论最大值
        normalized_score = max(-1, min(1, score / max_possible_score))
        
        return normalized_score
    
    def _detect_strong_emotion(self, text):
        """检测是否包含强烈情感词"""
        strong_keywords = []
        for levels in self.sentiment_keywords.values():
            strong_keywords.extend(levels.get('strong', []))
        
        for keyword in strong_keywords:
            if keyword in text:
                return True
        return False
    
    def analyze_sentiment_and_update_state(self, user_input):
        """改进的情感分析 - 更细粒度的情感识别和状态更新"""
        user_state = db_ops.get_user_state()
        affection_change = 0
        paranoia_change = 0
        
        # 使用新的情感分析方法
        sentiment_scores = self._detailed_sentiment_analysis(user_input)
        
        # 根据情感得分调整状态
        # 积极情感增加好感度
        if sentiment_scores['positive'] > 0:
            affection_change += int(sentiment_scores['positive'] * 3)
        
        # 消极情感降低好感度
        if sentiment_scores['negative'] > 0:
            affection_change -= int(sentiment_scores['negative'] * 2)
        
        # 嫉妒情感大幅增加偏执值
        if sentiment_scores['jealousy'] > 0:
            paranoia_change += int(sentiment_scores['jealousy'] * 5)
        
        # 依赖情感适度增加好感度
        if sentiment_scores['dependency'] > 0:
            affection_change += int(sentiment_scores['dependency'] * 2)
        
        # 更新用户状态
        if affection_change != 0 or paranoia_change != 0:
            db_ops.update_affection(affection_change, paranoia_change)
            log_info(f"情感分析结果 - 好感度变化: {affection_change}, 偏执值变化: {paranoia_change}")
            log_debug(f"详细情感得分: {sentiment_scores}")
    
    def _detailed_sentiment_analysis(self, text):
        """详细的情感分析，返回各维度得分"""
        scores = {
            'positive': 0,
            'negative': 0,
            'jealousy': 0,
            'dependency': 0
        }
        
        text_lower = text.lower()
        
        for category, levels in self.sentiment_keywords.items():
            for level, keywords in levels.items():
                for keyword in keywords:
                    if keyword in text_lower:
                        # 计算该关键词的得分（考虑出现次数）
                        count = text_lower.count(keyword)
                        weight = self.sentiment_weights[category][level]
                        scores[category] += abs(weight) * count
                        break  # 每个级别只计一次
        
        # 归一化到 0-1 范围
        for key in scores:
            scores[key] = min(1.0, scores[key] / 10.0)
        
        return scores
    
    def get_personality_prompt_by_state(self):
        """根据当前状态生成个性提示词"""
        # 检查当前性格模式
        if CURRENT_PERSONALITY in PERSONALITY_MODES:
            mode = PERSONALITY_MODES[CURRENT_PERSONALITY]
            if CURRENT_PERSONALITY == 'soft_cute':
                # 软萌模式：提升好感度，降低偏执值
                db_ops.update_affection(
                    affection_change=mode['affection_boost'], 
                    paranoia_change=-mode['paranoia_reduction']
                )
            elif CURRENT_PERSONALITY == 'yandere':
                # 病娇模式：降低好感度，大幅提升偏执值
                db_ops.update_affection(
                    affection_change=mode['affection_boost'], 
                    paranoia_change=mode['paranoia_increase']
                )
        
        state = db_ops.get_user_state()
        affection = state['affection']
        paranoia = state['paranoia']
        
        # 根据好感度和偏执值确定当前状态
        if paranoia > 70:
            # 高偏执状态 - 病娇模式
            return """你现在的偏执值很高，内心充满了不安和占有欲，虽然表面上仍保持着温柔，但话语中透露出强烈的控制欲和占有欲。请在回复中体现：
            - 对用户的强烈依恋和占有欲
            - 担心用户离开或与他人交往
            - 暗示用户只能属于你
            - 保持表面的温柔但内含威胁意味"""
        elif affection > 70:
            # 高好感度状态 - 软萌模式
            return """你现在非常开心，用户对你很好，你感到被爱护和珍惜。请在回复中体现：
            - 十分温柔、可爱的表现
            - 表达对用户的喜爱和感激
            - 更加依赖和信任用户
            - 语气更加轻松愉快"""
        else:
            # 正常模式 - 平衡状态
            return """保持平衡的状态，既有一些依赖又有一些担心，表现得既可爱又略带不安。请在回复中体现：
            - 适度的依赖和亲近
            - 轻微的担忧和不安
            - 温柔而略带犹豫的语气"""


# 创建全局实例
smart_context_manager = SmartContextManager()
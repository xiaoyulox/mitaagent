"""
高级情绪分析器
支持多维度情绪识别：文本内容、语气符号、对话行为
"""
import re
from datetime import datetime, timedelta


class EmotionAnalyzer:
    """情绪分析类"""
    
    def __init__(self):
        # 情绪关键词库
        self.emotion_keywords = {
            'positive': {
                'happy': ['哈哈', '嘿嘿', '太棒了', '绝了', '爱了', '舒服', '爽', '开心', '快乐'],
                'satisfied': ['可以', '没问题', '好的', '谢谢', '辛苦', '完美', '不错'],
                'agree': ['对', '没错', '就是这样', '懂了', '学到了', '确实']
            },
            'negative': {
                'angry': ['气死', '离谱', '服了', '什么玩意', '有病', '搞什么', '滚'],
                'annoyed': ['烦死了', '别烦', '够了', '算了', '随便', '无语'],
                'sad': ['难受', '崩溃', '麻了', '绝望', '累了', '伤心', '难过'],
                'complain': ['又不行', '总是', '一直', '根本不', '从来没有', '垃圾']
            },
            'anxious': ['快', '赶紧', '马上', '急', '来不及', '怎么办', '会不会', '着急'],
            'hesitant': ['不知道', '不太懂', '好像', '或许', '要不要', '应该吗', '犹豫']
        }
        
        # 语气符号权重
        self.punctuation_weights = {
            '!!!': {'emotion': 'excited_or_angry', 'weight': 0.8},
            '???': {'emotion': 'confused_or_questioning', 'weight': 0.7},
            '...': {'emotion': 'speechless_or_hesitant', 'weight': 0.6},
            '呵呵': {'emotion': 'sarcastic_or_dismissive', 'weight': 0.9}
        }
    
    def analyze_emotion(self, text, recent_messages=None):
        """
        综合分析情绪
        :param text: 当前消息文本
        :param recent_messages: 最近的消息列表（用于行为分析）
        :return: 情绪字典
        """
        emotion_result = {
            'primary_emotion': 'neutral',  # 主要情绪
            'intensity': 0.0,              # 强度 0-1
            'confidence': 0.0,             # 置信度 0-1
            'details': {}                  # 详细信息
        }
        
        if not text or len(text.strip()) == 0:
            return emotion_result
        
        # 1. 文本内容分析
        content_analysis = self._analyze_content(text)
        
        # 2. 语气符号分析
        punctuation_analysis = self._analyze_punctuation(text)
        
        # 3. 行为分析（如果有历史消息）
        behavior_analysis = self._analyze_behavior(recent_messages) if recent_messages else {}
        
        # 综合评分
        final_emotion = self._combine_analysis(content_analysis, punctuation_analysis, behavior_analysis)
        
        emotion_result.update(final_emotion)
        return emotion_result
    
    def _analyze_content(self, text):
        """分析文本内容"""
        scores = {
            'positive': 0,
            'negative': 0,
            'anxious': 0,
            'hesitant': 0,
            'neutral': 0
        }
        
        text_lower = text.lower()
        
        # 检查积极情绪
        for level, keywords in self.emotion_keywords['positive'].items():
            for keyword in keywords:
                if keyword in text_lower:
                    scores['positive'] += 1
        
        # 检查消极情绪
        for level, keywords in self.emotion_keywords['negative'].items():
            for keyword in keywords:
                if keyword in text_lower:
                    scores['negative'] += 2  # 负面情绪权重更高
        
        # 检查焦虑
        for keyword in self.emotion_keywords['anxious']:
            if keyword in text_lower:
                scores['anxious'] += 1
        
        # 检查犹豫
        for keyword in self.emotion_keywords['hesitant']:
            if keyword in text_lower:
                scores['hesitant'] += 1
        
        # 确定主要情绪
        max_score = max(scores.values())
        if max_score == 0:
            primary = 'neutral'
        else:
            primary = max(scores, key=scores.get)
        
        intensity = min(1.0, max_score / 5.0)  # 归一化到 0-1
        
        return {
            'primary': primary,
            'intensity': intensity,
            'scores': scores
        }
    
    def _analyze_punctuation(self, text):
        """分析语气符号"""
        emotion_boost = 0
        detected_emotion = None
        
        # 检查感叹号
        exclamation_count = text.count('!') + text.count('！')
        if exclamation_count >= 3:
            emotion_boost = 0.3
            detected_emotion = 'strong_emotion'
        
        # 检查问号
        question_count = text.count('?') + text.count('？')
        if question_count >= 2:
            emotion_boost = 0.2
            detected_emotion = 'questioning'
        
        # 检查省略号
        if '...' in text or '……' in text:
            emotion_boost = 0.2
            detected_emotion = 'hesitant'
        
        # 检查特定词汇
        for pattern, info in self.punctuation_weights.items():
            if pattern in text:
                emotion_boost = info['weight']
                detected_emotion = info['emotion']
                break
        
        return {
            'emotion': detected_emotion,
            'boost': emotion_boost
        }
    
    def _analyze_behavior(self, recent_messages):
        """分析对话行为"""
        if not recent_messages or len(recent_messages) < 2:
            return {}
        
        behavior = {}
        
        # 检查重复提问
        last_msg = recent_messages[-1]['content']
        for msg in recent_messages[:-1]:
            if msg['content'] == last_msg:
                behavior['repeated_question'] = True
                break
        
        # 检查连续发消息（5分钟内 > 3条）
        now = datetime.now()
        recent_count = 0
        for msg in reversed(recent_messages):
            msg_time = datetime.fromisoformat(msg['timestamp'])
            if (now - msg_time).total_seconds() < 300:  # 5分钟
                recent_count += 1
            else:
                break
        
        if recent_count > 3:
            behavior['rapid_fire'] = True
        
        # 检查短句冷漠
        if len(last_msg) <= 2 and last_msg in ['嗯', '哦', '好', '行']:
            behavior['dismissive'] = True
        
        return behavior
    
    def _combine_analysis(self, content, punctuation, behavior):
        """综合分析结果"""
        primary_emotion = content['primary']
        intensity = content['intensity']
        
        # 语气符号加成
        if punctuation['boost'] > 0:
            intensity = min(1.0, intensity + punctuation['boost'])
            if punctuation['emotion']:
                primary_emotion = punctuation['emotion']
        
        # 行为修正
        if behavior.get('repeated_question'):
            primary_emotion = 'frustrated'
            intensity = max(intensity, 0.7)
        
        if behavior.get('rapid_fire'):
            if primary_emotion == 'neutral':
                primary_emotion = 'anxious'
            intensity = max(intensity, 0.6)
        
        if behavior.get('dismissive'):
            primary_emotion = 'cold'
            intensity = 0.5
        
        # 计算置信度
        confidence = min(1.0, intensity * 1.2)
        
        return {
            'primary_emotion': primary_emotion,
            'intensity': round(intensity, 2),
            'confidence': round(confidence, 2),
            'details': {
                'content_analysis': content,
                'punctuation_analysis': punctuation,
                'behavior_analysis': behavior
            }
        }
    
    def get_emotion_label(self, emotion_code):
        """将情绪代码转换为人类可读标签"""
        labels = {
            'positive': '开心/满意',
            'negative': '生气/不满',
            'anxious': '焦虑/着急',
            'hesitant': '犹豫/迷茫',
            'neutral': '平静',
            'excited_or_angry': '激动/愤怒',
            'confused_or_questioning': '困惑/质疑',
            'speechless_or_hesitant': '无语/犹豫',
            'sarcastic_or_dismissive': '讽刺/敷衍',
            'strong_emotion': '强烈情绪',
            'questioning': '疑问',
            'frustrated': '挫败/烦躁',
            'cold': '冷漠/敷衍'
        }
        return labels.get(emotion_code, emotion_code)


# 全局实例
emotion_analyzer = EmotionAnalyzer()

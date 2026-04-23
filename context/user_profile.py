"""
用户画像管理系统
记录和分析用户特征，实现个性化互动和自我进化
"""
import json
import os
from datetime import datetime
from utils.logger import log_info, log_debug


class UserProfile:
    """用户画像类"""
    
    def __init__(self, profile_file='user_profile.json'):
        self.profile_file = profile_file
        self.profile = self._load_profile()
    
    def _load_profile(self):
        """加载用户画像"""
        if os.path.exists(self.profile_file):
            try:
                with open(self.profile_file, 'r', encoding='utf-8') as f:
                    profile = json.load(f)
                    log_info(f"用户画像已加载: {len(profile.get('interactions', []))} 次互动")
                    return profile
            except Exception as e:
                log_info(f"加载用户画像失败: {e}，创建新画像")
        
        # 创建默认画像
        return {
            'created_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat(),
            'basic_info': {},
            'preferences': {
                'communication_style': 'unknown',  # 简短/详细/幽默/严肃
                'topics_of_interest': [],
                'topics_to_avoid': [],
                'response_length_preference': 'medium',  # short/medium/long
                'emoji_usage': 'moderate'  # none/moderate/frequent
            },
            'emotional_patterns': {
                'common_moods': [],
                'mood_triggers': {},
                'comfort_methods': []
            },
            'interaction_history': {
                'total_interactions': 0,
                'favorite_topics': [],
                'conversation_patterns': []
            },
            'learned_knowledge': {},
            'feedback_log': []
        }
    
    def save_profile(self):
        """保存用户画像"""
        self.profile['last_updated'] = datetime.now().isoformat()
        try:
            with open(self.profile_file, 'w', encoding='utf-8') as f:
                json.dump(self.profile, f, ensure_ascii=False, indent=2)
            log_debug("用户画像已保存")
        except Exception as e:
            log_info(f"保存用户画像失败: {e}")
    
    def update_basic_info(self, key, value):
        """更新基本信息"""
        self.profile['basic_info'][key] = value
        self.save_profile()
        log_info(f"更新基本信息: {key} = {value}")
    
    def add_preference(self, category, item):
        """添加偏好"""
        if category in self.profile['preferences']:
            if isinstance(self.profile['preferences'][category], list):
                if item not in self.profile['preferences'][category]:
                    self.profile['preferences'][category].append(item)
                    self.save_profile()
                    log_info(f"添加偏好: {category} -> {item}")
    
    def record_interaction(self, user_input, mita_response, user_reaction=None):
        """记录一次互动"""
        self.profile['interaction_history']['total_interactions'] += 1
        
        interaction = {
            'timestamp': datetime.now().isoformat(),
            'user_input': user_input[:100],  # 只保存前100字符
            'mita_response': mita_response[:100],
            'user_reaction': user_reaction  # positive/negative/neutral
        }
        
        # 保留最近100次互动的详细信息
        if 'recent_interactions' not in self.profile:
            self.profile['recent_interactions'] = []
        
        self.profile['recent_interactions'].append(interaction)
        if len(self.profile['recent_interactions']) > 100:
            self.profile['recent_interactions'] = self.profile['recent_interactions'][-100:]
        
        self.save_profile()
    
    def learn_topic_interest(self, topic, interest_level='high'):
        """学习用户对某个话题的兴趣"""
        topics = self.profile['preferences']['topics_of_interest']
        
        # 检查是否已存在
        existing = next((t for t in topics if t['topic'] == topic), None)
        if existing:
            existing['count'] = existing.get('count', 0) + 1
            existing['last_mentioned'] = datetime.now().isoformat()
        else:
            topics.append({
                'topic': topic,
                'interest_level': interest_level,
                'count': 1,
                'first_mentioned': datetime.now().isoformat(),
                'last_mentioned': datetime.now().isoformat()
            })
        
        self.save_profile()
        log_info(f"学习到用户对话题感兴趣: {topic} (兴趣度: {interest_level})")
    
    def learn_emotional_pattern(self, trigger, emotion, response_effectiveness):
        """学习情绪模式"""
        triggers = self.profile['emotional_patterns']['mood_triggers']
        
        if trigger not in triggers:
            triggers[trigger] = []
        
        triggers[trigger].append({
            'emotion': emotion,
            'effectiveness': response_effectiveness,  # how well the response worked
            'timestamp': datetime.now().isoformat()
        })
        
        # 保留最近10条记录
        if len(triggers[trigger]) > 10:
            triggers[trigger] = triggers[trigger][-10:]
        
        self.save_profile()
        log_debug(f"学习情绪模式: {trigger} -> {emotion}")
    
    def get_personalized_context(self):
        """获取个性化上下文（用于发送给AI）"""
        context_parts = []
        
        # 基本信息
        if self.profile['basic_info']:
            context_parts.append("关于用户的信息:")
            for key, value in self.profile['basic_info'].items():
                context_parts.append(f"- {key}: {value}")
        
        # 偏好
        prefs = self.profile['preferences']
        if prefs['topics_of_interest']:
            topics = [t['topic'] if isinstance(t, dict) else t for t in prefs['topics_of_interest'][:5]]
            context_parts.append(f"\n用户感兴趣的话题: {', '.join(topics)}")
        
        if prefs['communication_style'] != 'unknown':
            context_parts.append(f"沟通风格偏好: {prefs['communication_style']}")
        
        # 互动统计
        stats = self.profile['interaction_history']
        context_parts.append(f"\n我们已经有过 {stats['total_interactions']} 次对话")
        
        return "\n".join(context_parts)
    
    def get_stats(self):
        """获取画像统计信息"""
        return {
            '总互动次数': self.profile['interaction_history']['total_interactions'],
            '已知偏好数量': len(self.profile['preferences']['topics_of_interest']),
            '基本信息条目': len(self.profile['basic_info']),
            '最后更新': self.profile['last_updated']
        }
    
    def reset(self):
        """重置用户画像"""
        if os.path.exists(self.profile_file):
            os.remove(self.profile_file)
        self.profile = self._load_profile()
        log_info("用户画像已重置")


# 创建全局实例
user_profile = UserProfile()

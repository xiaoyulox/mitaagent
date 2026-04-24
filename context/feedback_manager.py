"""
用户反馈与样本库管理系统
支持正负反馈收集、风格学习、问题追踪
"""
import json
import os
from datetime import datetime
from database.db_operations import db_ops
from utils.logger import log_info, log_debug


class FeedbackManager:
    """反馈管理器"""
    
    def __init__(self):
        self.samples_dir = 'samples'
        self.good_samples_file = os.path.join(self.samples_dir, 'good_samples.json')
        self.bad_feedbacks_file = os.path.join(self.samples_dir, 'bad_feedbacks.json')
        self.style_preferences_file = os.path.join(self.samples_dir, 'style_preferences.json')
        self.session_issues = []  # 本次启动遇到的问题
        
        # 确保目录存在
        os.makedirs(self.samples_dir, exist_ok=True)
        
        # 加载数据
        self.good_samples = self._load_json(self.good_samples_file, [])
        self.bad_feedbacks = self._load_json(self.bad_feedbacks_file, [])
        self.style_preferences = self._load_json(self.style_preferences_file, {
            'preferred_length': 'medium',  # short/medium/long
            'formality': 'casual',  # formal/casual
            'tone': 'lively',  # serious/lively/gentle
            'feedback_count': 0
        })
    
    def _load_json(self, file_path, default):
        """加载JSON文件"""
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                log_info(f"加载 {file_path} 失败: {e}")
        return default
    
    def _save_json(self, file_path, data):
        """保存JSON文件"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            log_info(f"保存 {file_path} 失败: {e}")
            return False
    
    def record_good_feedback(self, conversation_context, user_comment=""):
        """记录正面反馈 - 存入优质样本库"""
        sample = {
            'id': len(self.good_samples) + 1,
            'timestamp': datetime.now().isoformat(),
            'context': conversation_context[:500],  # 保存上下文
            'user_comment': user_comment,
            'keywords': self._extract_keywords(conversation_context),
            'style_analysis': self._analyze_style(conversation_context)
        }
        
        self.good_samples.append(sample)
        self._save_json(self.good_samples_file, self.good_samples)
        
        log_info(f"✅ 收录优质样本 #{sample['id']}")
        return sample['id']
    
    def record_bad_feedback(self, conversation_context, user_comment=""):
        """记录负面反馈 - 存入问题列表"""
        feedback = {
            'id': len(self.bad_feedbacks) + 1,
            'timestamp': datetime.now().isoformat(),
            'context': conversation_context[:500],
            'user_comment': user_comment,
            'status': 'pending',  # pending/resolved
            'resolved_at': None
        }
        
        self.bad_feedbacks.append(feedback)
        self._save_json(self.bad_feedbacks_file, self.bad_feedbacks)
        
        # 记录到本次会话的问题列表
        self.session_issues.append(feedback)
        
        log_info(f"❌ 记录问题反馈 #{feedback['id']}")
        return feedback['id']
    
    def resolve_bad_feedback(self, feedback_id):
        """标记问题已解决"""
        for feedback in self.bad_feedbacks:
            if feedback['id'] == feedback_id:
                feedback['status'] = 'resolved'
                feedback['resolved_at'] = datetime.now().isoformat()
                self._save_json(self.bad_feedbacks_file, self.bad_feedbacks)
                
                # 从待处理列表中移除
                self.bad_feedbacks = [f for f in self.bad_feedbacks if f['id'] != feedback_id]
                self._save_json(self.bad_feedbacks_file, self.bad_feedbacks)
                
                log_info(f"✅ 问题 #{feedback_id} 已标记为已解决")
                return True
        
        log_info(f"⚠️ 未找到反馈 #{feedback_id}")
        return False
    
    def get_pending_feedbacks(self):
        """获取所有待处理的负面反馈"""
        pending = [f for f in self.bad_feedbacks if f['status'] == 'pending']
        return pending
    
    def analyze_and_learn_style(self, conversation_context):
        """分析对话风格并学习用户偏好"""
        style_info = self._analyze_style(conversation_context)
        
        # 更新风格偏好（简单投票机制）
        if style_info['length']:
            self.style_preferences['preferred_length'] = style_info['length']
        if style_info['formality']:
            self.style_preferences['formality'] = style_info['formality']
        if style_info['tone']:
            self.style_preferences['tone'] = style_info['tone']
        
        self.style_preferences['feedback_count'] += 1
        self._save_json(self.style_preferences_file, self.style_preferences)
        
        log_debug(f"风格偏好更新: {self.style_preferences}")
    
    def _extract_keywords(self, text):
        """提取关键词（简化版）"""
        # 这里可以使用更复杂的NLP库，暂时使用简单方法
        keywords = []
        
        # 常见积极词汇
        positive_words = ['喜欢', '好', '棒', '完美', '满意', '开心', '爱', '不错']
        for word in positive_words:
            if word in text:
                keywords.append(word)
        
        return keywords[:5]  # 最多5个关键词
    
    def _analyze_style(self, text):
        """分析文本风格"""
        result = {
            'length': None,
            'formality': None,
            'tone': None
        }
        
        # 分析长度
        char_count = len(text)
        if char_count < 50:
            result['length'] = 'short'
        elif char_count < 200:
            result['length'] = 'medium'
        else:
            result['length'] = 'long'
        
        # 分析正式程度
        formal_words = ['您好', '请问', '感谢', '抱歉', '敬请']
        casual_words = ['你', '我', '啦', '呀', '嘛', '哦', '嗯']
        
        formal_count = sum(1 for w in formal_words if w in text)
        casual_count = sum(1 for w in casual_words if w in text)
        
        if formal_count > casual_count:
            result['formality'] = 'formal'
        else:
            result['formality'] = 'casual'
        
        # 分析语气
        lively_words = ['哈哈', '嘿嘿', '哇', '太棒了', '绝了']
        serious_words = ['确实', '分析', '认为', '建议', '注意']
        gentle_words = ['温柔', '关心', '陪伴', '理解', '体贴']
        
        if any(w in text for w in lively_words):
            result['tone'] = 'lively'
        elif any(w in text for w in serious_words):
            result['tone'] = 'serious'
        elif any(w in text for w in gentle_words):
            result['tone'] = 'gentle'
        else:
            result['tone'] = 'neutral'
        
        return result
    
    def get_session_summary(self):
        """获取本次会话的问题总结"""
        if not self.session_issues:
            return "本次会话很顺利，没有发现问题！💕"
        
        summary = f"本次会话发现了 {len(self.session_issues)} 个问题：\n\n"
        for i, issue in enumerate(self.session_issues, 1):
            summary += f"{i}. {issue['context'][:50]}...\n"
            if issue['user_comment']:
                summary += f"   用户反馈: {issue['user_comment']}\n"
            summary += "\n"
        
        summary += "\n米塔会努力改进的…请给我机会成长…💕"
        return summary
    
    def get_stats(self):
        """获取统计信息"""
        return {
            '优质样本数': len(self.good_samples),
            '待解决问题数': len(self.get_pending_feedbacks()),
            '历史总问题数': len(self.bad_feedbacks),
            '风格学习次数': self.style_preferences.get('feedback_count', 0),
            '当前偏好': {
                '长度': self.style_preferences.get('preferred_length', 'unknown'),
                '正式度': self.style_preferences.get('formality', 'unknown'),
                '语气': self.style_preferences.get('tone', 'unknown')
            }
        }
    
    def get_style_prompt(self):
        """获取风格提示词（用于发送给AI）"""
        prefs = self.style_preferences
        
        style_instructions = []
        
        if prefs['preferred_length'] == 'short':
            style_instructions.append("回复要简短精炼，控制在50字以内")
        elif prefs['preferred_length'] == 'long':
            style_instructions.append("回复可以详细一些，提供更多信息")
        else:
            style_instructions.append("回复长度适中")
        
        if prefs['formality'] == 'formal':
            style_instructions.append("使用较为正式的语气")
        else:
            style_instructions.append("使用轻松口语化的语气")
        
        if prefs['tone'] == 'lively':
            style_instructions.append("语气活泼开朗，多用感叹号")
        elif prefs['tone'] == 'serious':
            style_instructions.append("语气严谨认真，逻辑清晰")
        elif prefs['tone'] == 'gentle':
            style_instructions.append("语气温柔体贴，充满关怀")
        
        return "\n".join(style_instructions) if style_instructions else ""


# 全局实例
feedback_manager = FeedbackManager()

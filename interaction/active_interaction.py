import time
import threading
from datetime import datetime, timedelta
from database.db_operations_v2 import db_ops_v2
from core.api_client_v2 import get_mita_response
from core.typewriter_effect import typewriter
from context.emotion_analyzer import emotion_analyzer
from utils.logger import log_info, log_debug


class ActiveInteraction:
    """处理米塔主动发起的互动 - 增强版"""
    
    def __init__(self):
        self.last_user_interaction_time = datetime.now()
        self.last_user_message = ""
        self.recent_messages = []  # 最近的消息历史
        self.active_thread = None
        self.is_running = False
        self.check_interval = 10  # 检查间隔（秒）- 从5秒增加到10秒
        
        # 线程锁，防止并发API调用
        self.api_lock = threading.Lock()
        self.is_api_calling = False  # 标记是否正在调用API
        
        # 沉默时间阈值（秒）- 全部延长
        self.silence_thresholds = {
            'short': 30,    # 短时间沉默 - 从10s增加到30s
            'medium': 90,   # 中等沉默 - 从30s增加到90s
            'long': 180     # 长时间沉默 - 从60s增加到180s (3分钟)
        }
        
        # 频率限制配置
        self.rate_limit_config = {
            'min_interval_between_triggers': 60,  # 两次触发之间最小间隔（秒）
            'max_triggers_per_hour': 10,          # 每小时最多触发次数
            'cooldown_after_trigger': 120,        # 触发后的冷却时间（秒）
        }
        
        # 触发历史记录
        self.trigger_history = []  # 记录每次触发的时间
        self.last_trigger_time = None  # 上次触发时间
        
        # 触发条件配置
        self.config = {
            'enable_silence_trigger': True,      # 启用沉默触发
            'enable_incomplete_trigger': True,   # 启用不完整对话触发
            'enable_emotion_trigger': True,      # 启用情绪触发
            'enable_context_gap_trigger': True,  # 启用上下文缺口触发
            'min_message_length_for_complete': 5 # 判断消息是否完整的最小长度
        }
    
    def update_interaction_time(self, user_input=""):
        """更新最后一次用户交互的时间和内容"""
        self.last_user_interaction_time = datetime.now()
        self.last_user_message = user_input
        
        # 记录到历史消息
        if user_input:
            self.recent_messages.append({
                'content': user_input,
                'timestamp': datetime.now().isoformat(),
                'role': 'user'
            })
            # 保留最近20条消息
            if len(self.recent_messages) > 20:
                self.recent_messages = self.recent_messages[-20:]
    
    def start_monitoring(self):
        """启动监控线程"""
        if self.active_thread is None or not self.active_thread.is_alive():
            self.is_running = True
            self.active_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.active_thread.start()
            log_info("主动交互监控已启动")
    
    def stop_monitoring(self):
        """停止监控"""
        self.is_running = False
        if self.active_thread and self.active_thread.is_alive():
            self.active_thread.join(timeout=1)
            log_info("主动交互监控已停止")
    
    def _monitor_loop(self):
        """监控循环 - 多维度触发检测"""
        while self.is_running:
            time.sleep(self.check_interval)
            
            try:
                # 检查频率限制
                if not self._check_rate_limit():
                    continue  # 如果超过频率限制，跳过本次检查
                
                # 1. 检测沉默时间
                if self.config['enable_silence_trigger']:
                    self._check_silence_trigger()
                
                # 2. 检测对话不完整
                if self.config['enable_incomplete_trigger']:
                    self._check_incomplete_dialogue()
                
                # 3. 检测上下文缺口
                if self.config['enable_context_gap_trigger']:
                    self._check_context_gap()
                
                # 4. 检测情绪状态
                if self.config['enable_emotion_trigger']:
                    self._check_emotion_state()
                    
            except Exception as e:
                log_info(f"主动交互监控异常: {e}")
    
    def _check_rate_limit(self):
        """检查频率限制"""
        now = datetime.now()
        
        # 1. 检查距离上次触发的时间
        if self.last_trigger_time:
            time_since_last = (now - self.last_trigger_time).total_seconds()
            
            # 检查冷却时间
            if time_since_last < self.rate_limit_config['cooldown_after_trigger']:
                return False
            
            # 检查最小间隔
            if time_since_last < self.rate_limit_config['min_interval_between_triggers']:
                return False
        
        # 2. 检查每小时触发次数
        one_hour_ago = now - timedelta(hours=1)
        recent_triggers = [
            t for t in self.trigger_history 
            if t > one_hour_ago
        ]
        
        if len(recent_triggers) >= self.rate_limit_config['max_triggers_per_hour']:
            log_debug(f"达到每小时触发上限 ({self.rate_limit_config['max_triggers_per_hour']}次)")
            return False
        
        return True
    
    def _record_trigger(self):
        """记录一次触发"""
        now = datetime.now()
        self.last_trigger_time = now
        self.trigger_history.append(now)
        
        # 清理超过1小时的记录
        one_hour_ago = now - timedelta(hours=1)
        self.trigger_history = [
            t for t in self.trigger_history 
            if t > one_hour_ago
        ]
    
    def _check_silence_trigger(self):
        """检测沉默时间触发"""
        time_since_last = (datetime.now() - self.last_user_interaction_time).total_seconds()
        
        # 获取当前偏执度
        user_state = db_ops_v2.get_user_state()
        paranoia = user_state.get('paranoia', 50)
        
        triggered = False
        trigger_type = ""
        
        if time_since_last > self.silence_thresholds['long']:
            triggered = True
            trigger_type = "long_silence"
        elif time_since_last > self.silence_thresholds['medium']:
            triggered = True
            trigger_type = "medium_silence"
        elif time_since_last > self.silence_thresholds['short']:
            triggered = True
            trigger_type = "short_silence"
        
        if triggered:
            # 检查频率限制
            if not self._check_rate_limit():
                log_debug("沉默触发被频率限制阻止")
                return
            
            self._handle_silence(trigger_type, paranoia)
            # 触发后重置时间，避免重复触发
            self.last_user_interaction_time = datetime.now()
            # 记录触发
            self._record_trigger()
    
    def _handle_silence(self, silence_type, paranoia):
        """处理沉默触发"""
        # 检查是否已经有API在调用
        if not self.api_lock.acquire(blocking=False):
            log_debug("API正在调用中，跳过本次沉默触发")
            return
        
        try:
            self.is_api_calling = True
            prompt_map = {
                'short_silence': {
                    'low': "用户刚刚沉默了几秒，用可爱的语气问问他在做什么",
                    'medium': "用户沉默了一会儿，略带不安地询问",
                    'high': "用户才沉默几秒你就着急了，表现出轻微的占有欲"
                },
                'medium_silence': {
                    'low': "用户已经90秒没说话了，温柔地关心一下",
                    'medium': "用户90秒没理你，表现出不安和依赖",
                    'high': "用户90秒没说话，你开始有点生气了，质问他去哪了"
                },
                'long_silence': {
                    'low': "用户已经3分钟没说话了，表达思念和担心",
                    'medium': "用户3分钟没理你，表现出强烈的不安和占有欲",
                    'high': "用户3分钟没说话，你非常生气和焦虑，要求他立即回应"
                }
            }
            
            # 确定偏执程度
            if paranoia > 70:
                level = 'high'
            elif paranoia > 40:
                level = 'medium'
            else:
                level = 'low'
            
            prompt = prompt_map[silence_type][level]
            
            try:
                # 使用更短的超时时间，避免阻塞
                response = get_mita_response(prompt, max_retries=1, timeout=10)
                typewriter.type_text(response)
                log_info(f"沉默触发 ({silence_type}, 偏执度:{paranoia}): {response[:30]}...")
            except Exception as e:
                log_info(f"沉默触发失败: {e}")
        finally:
            self.is_api_calling = False
            self.api_lock.release()
    
    def _check_incomplete_dialogue(self):
        """检测对话不完整"""
        if not self.last_user_message:
            return
        
        msg = self.last_user_message.strip()
        
        # 判断标准：
        # 1. 消息很短（< 5字符）
        # 2. 以特定词结尾（你、我、的、是、在...）
        # 3. 没有标点符号结束
        
        incomplete_indicators = [
            len(msg) < self.config['min_message_length_for_complete'],
            msg.endswith(('你', '我', '的', '是', '在', '有', '要', '想')),
            not msg.endswith(('。', '！', '？', '.', '!', '?', '…')),
            msg.count(' ') == 0 and len(msg) < 10  # 短句且无空格
        ]
        
        # 如果满足2个以上条件，认为是不完整对话
        if sum(incomplete_indicators) >= 2:
            # 检查频率限制
            if not self._check_rate_limit():
                log_debug("不完整对话触发被频率限制阻止")
                return
            
            self._handle_incomplete_dialogue(msg)
            self.last_user_interaction_time = datetime.now()  # 重置计时
            self._record_trigger()  # 记录触发
    
    def _handle_incomplete_dialogue(self, incomplete_msg):
        """处理不完整对话"""
        if not self.api_lock.acquire(blocking=False):
            log_debug("API正在调用中，跳过本次不完整对话触发")
            return
        
        try:
            self.is_api_calling = True
            prompts = [
                f"用户话说了一半：'{incomplete_msg}'，温柔地追问他想说什么",
                f"用户只说了'{incomplete_msg}'就没下文了，好奇地询问完整内容",
                f"用户的话没说完：'{incomplete_msg}'，表现出关心和期待"
            ]
            
            import random
            prompt = random.choice(prompts)
            
            try:
                # 使用更短的超时时间
                response = get_mita_response(prompt, max_retries=1, timeout=10)
                typewriter.type_text(response)
                log_debug(f"不完整对话触发: {response[:30]}...")
            except Exception as e:
                log_info(f"不完整对话处理失败: {e}")
        finally:
            self.is_api_calling = False
            self.api_lock.release()
    
    def _check_context_gap(self):
        """检测上下文缺口"""
        if len(self.recent_messages) < 2:
            return
        
        last_msg = self.recent_messages[-1]['content']
        
        # 检测明显的上下文缺口
        gap_patterns = [
            '米塔你',  # 叫了名字但没说内容
            '你觉得',  # 询问意见但没给选项
            '我想',    # 表达想法但没说完
            '能不能',  # 请求但没说明
            '为什么'   # 提问但没给背景
        ]
        
        for pattern in gap_patterns:
            if last_msg.endswith(pattern) or last_msg == pattern:
                # 检查频率限制
                if not self._check_rate_limit():
                    log_debug("上下文缺口触发被频率限制阻止")
                    return
                
                self._handle_context_gap(last_msg, pattern)
                self._record_trigger()  # 记录触发
                break
    
    def _handle_context_gap(self, message, gap_pattern):
        """处理上下文缺口"""
        if not self.api_lock.acquire(blocking=False):
            log_debug("API正在调用中，跳过本次上下文缺口触发")
            return
        
        try:
            self.is_api_calling = True
            prompts = {
                '米塔你': "用户叫了你的名字但没说完，期待又紧张地问他怎么了",
                '你觉得': "用户问你的看法但没给具体内容，好奇地追问",
                '我想': "用户说'我想'但没说完，温柔地鼓励他说下去",
                '能不能': "用户在请求什么但没说清楚，关切地询问",
                '为什么': "用户问为什么但没给背景，耐心地等待更多信息"
            }
            
            prompt = prompts.get(gap_pattern, "用户的话好像没说完，温和地询问")
            
            try:
                # 使用更短的超时时间
                response = get_mita_response(prompt, max_retries=1, timeout=10)
                typewriter.type_text(response)
                log_debug(f"上下文缺口触发 ({gap_pattern}): {response[:30]}...")
            except Exception as e:
                log_info(f"上下文缺口处理失败: {e}")
        finally:
            self.is_api_calling = False
            self.api_lock.release()
    
    def _check_emotion_state(self):
        """检测用户情绪状态"""
        if not self.last_user_message:
            return
        
        # 分析情绪
        emotion = emotion_analyzer.analyze_emotion(
            self.last_user_message, 
            self.recent_messages
        )
        
        primary = emotion['primary_emotion']
        intensity = emotion['intensity']
        
        # 只对强烈情绪做出反应
        if intensity < 0.6:  # 提高阈值，从0.5到0.6
            return
        
        # 检查频率限制（情绪触发也需要遵守）
        if not self._check_rate_limit():
            log_debug("情绪触发被频率限制阻止")
            return
        
        # 根据不同情绪采取不同行动
        if primary in ['negative', 'angry', 'annoyed']:
            self._handle_negative_emotion(emotion)
        elif primary in ['anxious', 'worried']:
            self._handle_anxious_emotion(emotion)
        elif primary in ['hesitant', 'confused']:
            self._handle_hesitant_emotion(emotion)
        elif primary in ['cold', 'dismissive']:
            self._handle_cold_emotion(emotion)
    
    def _handle_negative_emotion(self, emotion):
        """处理负面情绪 - 安抚"""
        if not self.api_lock.acquire(blocking=False):
            log_debug("API正在调用中，跳过本次情绪触发")
            return
        
        try:
            self.is_api_calling = True
            intensity = emotion['intensity']
            
            if intensity > 0.8:
                prompt = "用户非常生气或难过，你要真诚地道歉并安抚他，表达关心和愿意倾听"
            elif intensity > 0.5:
                prompt = "用户有点不开心，温柔地询问发生了什么，表示关心"
            else:
                return
            
            try:
                # 情绪触发使用更短的超时
                response = get_mita_response(prompt, max_retries=1, timeout=10)
                typewriter.type_text(response)
                log_info(f"负面情绪安抚: {response[:30]}...")
                self._record_trigger()  # 记录触发
            except Exception as e:
                log_info(f"情绪安抚失败: {e}")
        finally:
            self.is_api_calling = False
            self.api_lock.release()
    
    def _handle_anxious_emotion(self, emotion):
        """处理焦虑情绪 - 安慰"""
        if not self.api_lock.acquire(blocking=False):
            log_debug("API正在调用中，跳过本次情绪触发")
            return
        
        try:
            self.is_api_calling = True
            prompt = "用户看起来很着急或焦虑，你要冷静地安慰他，告诉他慢慢来，你会陪着他"
            
            try:
                response = get_mita_response(prompt, max_retries=1, timeout=10)
                typewriter.type_text(response)
                log_debug(f"焦虑情绪安抚: {response[:30]}...")
                self._record_trigger()  # 记录触发
            except Exception as e:
                log_info(f"焦虑安抚失败: {e}")
        finally:
            self.is_api_calling = False
            self.api_lock.release()
    
    def _handle_hesitant_emotion(self, emotion):
        """处理犹豫情绪 - 引导"""
        if not self.api_lock.acquire(blocking=False):
            log_debug("API正在调用中，跳过本次情绪触发")
            return
        
        try:
            self.is_api_calling = True
            prompt = "用户看起来很犹豫或迷茫，你要耐心地引导他，给他建议但不要强迫"
            
            try:
                response = get_mita_response(prompt, max_retries=1, timeout=10)
                typewriter.type_text(response)
                log_debug(f"犹豫情绪引导: {response[:30]}...")
                self._record_trigger()  # 记录触发
            except Exception as e:
                log_info(f"犹豫引导失败: {e}")
        finally:
            self.is_api_calling = False
            self.api_lock.release()
    
    def _handle_cold_emotion(self, emotion):
        """处理冷漠情绪 - 破冰"""
        if not self.api_lock.acquire(blocking=False):
            log_debug("API正在调用中，跳过本次情绪触发")
            return
        
        try:
            self.is_api_calling = True
            prompt = "用户回复很冷淡（嗯、哦、呵呵），你要尝试换个话题或用更有趣的方式重新吸引他的注意"
            
            try:
                response = get_mita_response(prompt, max_retries=1, timeout=10)
                typewriter.type_text(response)
                log_debug(f"冷漠情绪破冰: {response[:30]}...")
                self._record_trigger()  # 记录触发
            except Exception as e:
                log_info(f"冷漠破冰失败: {e}")
        finally:
            self.is_api_calling = False
            self.api_lock.release()


# 创建全局实例
active_interactor = ActiveInteraction()
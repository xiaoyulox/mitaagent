import importlib
import threading
from datetime import datetime, timedelta
from utils.logger import log_info, log_error, log_warning
from context.cache_manager import cache_manager

try:
    pymysql = importlib.import_module('pymysql')
except ImportError:
    log_error("未找到pymysql库，请运行 'pip install PyMySQL' 安装依赖")
    pymysql = None

from database.db_config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME


class DatabaseOperationsV2:
    """改进版数据库操作类，支持连接池和缓存"""
    
    def __init__(self):
        self.host = DB_HOST
        self.port = DB_PORT
        self.user = DB_USER
        self.password = DB_PASSWORD
        self.db_name = DB_NAME
        self.connection = None
        self.db_available = True
        self.lock = threading.Lock()  # 线程锁，确保线程安全
        self.last_connect_attempt = None  # 记录最后连接尝试时间
        self.reconnect_delay = 5  # 重连延迟（秒）
        
        if pymysql is None:
            log_error("由于缺少PyMySQL库，数据库功能不可用。请运行 'pip install PyMySQL' 安装依赖")
            self.db_available = False
            return
    
    def connect(self):
        """建立数据库连接，带健康检查和重连机制"""
        with self.lock:
            if not self._should_attempt_reconnect():
                return False
                
            try:
                if self.connection:
                    # 尝试ping连接
                    self.connection.ping(reconnect=True)
                    if self.connection.open:
                        log_info("使用现有数据库连接")
                        return True
                
                self.connection = pymysql.connect(
                    host=self.host,
                    port=self.port,
                    user=self.user,
                    password=self.password,
                    database=self.db_name,
                    charset='utf8mb4',
                    cursorclass=pymysql.cursors.DictCursor,
                    autocommit=True
                )
                
                # 设置连接参数以提高性能
                with self.connection.cursor() as cursor:
                    cursor.execute("SET SESSION wait_timeout=28800")  # 8小时超时
                    cursor.execute("SET SESSION interactive_timeout=28800")
                
                self.last_connect_attempt = datetime.now()
                log_info("数据库连接成功")
                return True
            except Exception as e:
                self.last_connect_attempt = datetime.now()
                log_error(f"数据库连接失败: {e}")
                self.db_available = False
                return False
    
    def _should_attempt_reconnect(self):
        """判断是否应该尝试重连"""
        if self.last_connect_attempt is None:
            return True
            
        time_since_last_attempt = datetime.now() - self.last_connect_attempt
        return time_since_last_attempt.total_seconds() > self.reconnect_delay
    
    def _ensure_connection(self):
        """确保数据库连接可用"""
        if not self.db_available:
            return False
            
        if not self.connection:
            return self.connect()
        
        try:
            self.connection.ping(reconnect=True)
            return True
        except Exception as e:
            log_warning(f"连接丢失，尝试重新连接: {e}")
            return self.connect()
    
    def initialize_tables(self):
        """初始化数据库表结构"""
        if not self._ensure_connection():
            return False
        
        try:
            with self.connection.cursor() as cursor:
                # 创建对话表，添加索引优化查询
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS conversations (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        user_input TEXT NOT NULL,
                        mita_response TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        INDEX idx_created_at (created_at),
                        INDEX idx_id_desc (id DESC)
                    )
                ''')
                
                # 创建用户状态表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_state (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        affection INT DEFAULT 50,
                        paranoia INT DEFAULT 30,
                        last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 检查并插入初始状态
                cursor.execute("SELECT COUNT(*) as count FROM user_state")
                result = cursor.fetchone()
                if result['count'] == 0:
                    cursor.execute("INSERT INTO user_state (affection, paranoia) VALUES (50, 30)")
                    
            self.connection.commit()
            log_info("数据库表结构初始化完成")
            return True
        except Exception as e:
            log_error(f"初始化表失败: {e}")
            self.db_available = False
            return False

    def save_conversation(self, user_input, mita_response):
        """保存对话记录"""
        if not self._ensure_connection():
            # 如果数据库不可用，尝试保存到本地文件作为备用
            self._save_to_backup_file(user_input, mita_response)
            return False

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO conversations (user_input, mita_response) VALUES (%s, %s)",
                    (user_input, mita_response)
                )
            self.connection.commit()
            
            # 清除相关缓存，因为数据已更新
            cache_manager.invalidate('recent_conversations')
            cache_manager.invalidate('all_conversations')
            cache_manager.invalidate('conversation_count')
            
            log_info("对话记录保存成功")
            return True
        except Exception as e:
            log_error(f"保存对话失败: {e}")
            # 如果数据库保存失败，尝试保存到本地文件
            self._save_to_backup_file(user_input, mita_response)
            return False

    def _save_to_backup_file(self, user_input, mita_response):
        """将对话保存到备份文件"""
        try:
            backup_file = "backup_conversations.txt"
            with open(backup_file, "a", encoding="utf-8") as f:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"[{timestamp}] 用户: {user_input} | 米塔: {mita_response}\n")
            log_warning("对话已保存到备份文件")
        except Exception as e:
            log_error(f"备份文件保存失败: {e}")

    def get_recent_conversations(self, limit=10):
        """获取最近的对话记录（带缓存）"""
        cache_key = f"recent_conversations_{limit}"
        cached_result = cache_manager.get(cache_key)
        if cached_result is not None:
            log_info(f"从缓存获取最近{limit}条对话")
            return cached_result
        
        if not self._ensure_connection():
            return []
        
        try:
            with self.connection.cursor() as cursor:
                # 使用优化的查询，利用索引
                cursor.execute(
                    "SELECT user_input, mita_response, created_at FROM conversations "
                    "ORDER BY id DESC LIMIT %s", 
                    (limit,)
                )
                results = cursor.fetchall()
                # 按时间顺序反转，使最早的对话在前
                conversations = list(reversed(results))
                
            # 存入缓存，TTL为5分钟
            cache_manager.set(cache_key, conversations, 300)
            log_info(f"获取到{len(conversations)}条最近对话记录")
            return conversations
        except Exception as e:
            log_error(f"获取最近对话失败: {e}")
            return []

    def get_all_conversations(self):
        """获取所有对话记录（带缓存）"""
        cache_key = "all_conversations"
        cached_result = cache_manager.get(cache_key)
        if cached_result is not None:
            log_info("从缓存获取所有对话")
            return cached_result
        
        if not self._ensure_connection():
            return []
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT id, user_input, mita_response, created_at FROM conversations ORDER BY id ASC")
                results = cursor.fetchall()
                
            # 存入缓存，TTL为10分钟
            cache_manager.set(cache_key, results, 600)
            log_info(f"获取到{len(results)}条所有对话记录")
            return results
        except Exception as e:
            log_error(f"获取所有对话失败: {e}")
            return []

    def get_latest_conversations(self, limit=5):
        """获取最新的对话记录（带缓存）"""
        cache_key = f"latest_conversations_{limit}"
        cached_result = cache_manager.get(cache_key)
        if cached_result is not None:
            log_info(f"从缓存获取最新{limit}条对话")
            return cached_result
        
        if not self._ensure_connection():
            return []
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    "SELECT id, user_input, mita_response, created_at FROM conversations "
                    "ORDER BY id DESC LIMIT %s", 
                    (limit,)
                )
                results = cursor.fetchall()
                # 按时间顺序反转，使最早的对话在前
                conversations = list(reversed(results))
                
            # 存入缓存，TTL为5分钟
            cache_manager.set(cache_key, conversations, 300)
            log_info(f"获取到{len(conversations)}条最新对话记录")
            return conversations
        except Exception as e:
            log_error(f"获取最新对话失败: {e}")
            return []

    def delete_conversation(self, conv_id):
        """删除特定ID的对话记录"""
        if not self._ensure_connection():
            return False

        try:
            with self.connection.cursor() as cursor:
                cursor.execute("DELETE FROM conversations WHERE id = %s", (conv_id,))
            self.connection.commit()
            
            # 清除相关缓存
            cache_manager.invalidate('recent_conversations')
            cache_manager.invalidate('all_conversations')
            cache_manager.invalidate('conversation_count')
            
            log_info(f"ID为{conv_id}的对话记录已删除")
            return True
        except Exception as e:
            log_error(f"删除对话记录失败: {e}")
            return False

    def update_conversation(self, conv_id, user_input=None, mita_response=None):
        """更新特定ID的对话记录"""
        if not self._ensure_connection():
            return False

        try:
            with self.connection.cursor() as cursor:
                if user_input is not None and mita_response is not None:
                    cursor.execute(
                        "UPDATE conversations SET user_input = %s, mita_response = %s WHERE id = %s",
                        (user_input, mita_response, conv_id)
                    )
                elif mita_response is not None:
                    cursor.execute(
                        "UPDATE conversations SET mita_response = %s WHERE id = %s",
                        (mita_response, conv_id)
                    )
                else:
                    cursor.execute(
                        "UPDATE conversations SET user_input = %s WHERE id = %s",
                        (user_input, conv_id)
                    )
            self.connection.commit()
            
            # 清除相关缓存
            cache_manager.invalidate('recent_conversations')
            cache_manager.invalidate('all_conversations')
            
            log_info(f"ID为{conv_id}的对话记录已更新")
            return True
        except Exception as e:
            log_error(f"更新对话记录失败: {e}")
            return False

    def get_conversation_count(self):
        """获取对话记录总数（带缓存）"""
        cache_key = "conversation_count"
        cached_result = cache_manager.get(cache_key)
        if cached_result is not None:
            log_info("从缓存获取对话计数")
            return cached_result
        
        if not self._ensure_connection():
            return 0

        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) as count FROM conversations")
                result = cursor.fetchone()
                count = result['count']
                
            # 存入缓存，TTL为10分钟
            cache_manager.set(cache_key, count, 600)
            log_info(f"当前对话总数: {count}")
            return count
        except Exception as e:
            log_error(f"获取对话记录总数失败: {e}")
            return 0

    def get_latest_mita_response(self):
        """获取最新一条米塔的回复（带缓存）"""
        cache_key = "latest_mita_response"
        cached_result = cache_manager.get(cache_key)
        if cached_result is not None:
            log_info("从缓存获取最新米塔回复")
            return cached_result
        
        if not self._ensure_connection():
            return None

        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT mita_response FROM conversations ORDER BY id DESC LIMIT 1")
                result = cursor.fetchone()
                response = result['mita_response'] if result else None
                
            # 存入缓存，TTL为2分钟
            if response:
                cache_manager.set(cache_key, response, 120)
            
            log_info("获取最新米塔回复成功")
            return response
        except Exception as e:
            log_error(f"获取最新米塔回复失败: {e}")
            return None

    def update_affection(self, affection_change=0, paranoia_change=0):
        """更新好感度和偏执值"""
        if not self._ensure_connection():
            return False

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE user_state SET affection = GREATEST(0, LEAST(100, affection + %s)), "
                    "paranoia = GREATEST(0, LEAST(100, paranoia + %s)) WHERE id = 1", 
                    (affection_change, paranoia_change)
                )
            self.connection.commit()
            
            # 清除用户状态缓存
            cache_manager.invalidate('user_state')
            
            log_info(f"好感度变化: {affection_change}, 偏执值变化: {paranoia_change}")
            return True
        except Exception as e:
            log_error(f"更新好感度/偏执值失败: {e}")
            return False

    def get_user_state(self):
        """获取用户状态（带缓存）"""
        cache_key = "user_state"
        cached_result = cache_manager.get(cache_key)
        if cached_result is not None:
            log_info("从缓存获取用户状态")
            return cached_result
        
        if not self._ensure_connection():
            return {"affection": 50, "paranoia": 30}

        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT affection, paranoia FROM user_state WHERE id = 1")
                result = cursor.fetchone()
                
                if not result:
                    # 如果没有记录，创建一个默认记录
                    with self.connection.cursor() as cursor:
                        cursor.execute("INSERT INTO user_state (affection, paranoia) VALUES (50, 30)")
                        result = {"affection": 50, "paranoia": 30}
                        
            # 存入缓存，TTL为1分钟
            cache_manager.set(cache_key, result, 60)
            log_info(f"获取用户状态成功 - 好感度: {result['affection']}, 偏执值: {result['paranoia']}")
            return result
        except Exception as e:
            log_error(f"获取用户状态失败: {e}")
            return {"affection": 50, "paranoia": 30}
    
    def reset_database(self):
        """重置数据库"""
        if not self._ensure_connection():
            return False

        try:
            with self.connection.cursor() as cursor:
                cursor.execute("TRUNCATE TABLE conversations")
            self.connection.commit()
            
            # 清除所有相关缓存
            cache_manager.invalidate('recent_conversations')
            cache_manager.invalidate('all_conversations')
            cache_manager.invalidate('conversation_count')
            cache_manager.invalidate('latest_mita_response')
            
            log_info("数据库重置成功")
            return True
        except Exception as e:
            log_error(f"重置数据库失败: {e}")
            return False
    
    def close(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            log_info("数据库连接已关闭")


# 创建全局实例
db_ops_v2 = DatabaseOperationsV2()
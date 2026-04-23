import importlib

try:
    pymysql = importlib.import_module('pymysql')
except ImportError:
    print("警告: 未找到pymysql库，请运行 'pip install PyMySQL' 安装依赖")
    pymysql = None

from database.db_config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME

class DatabaseOperations:
    def __init__(self):
        self.host = None
        self.port = None
        self.user = None
        self.password = None
        self.db_name = None
        self.connection = None
        self.db_available = True
        
        if pymysql is None:
            print("错误: 由于缺少PyMySQL库，数据库功能不可用。请运行 'pip install PyMySQL' 安装依赖")
            self.db_available = False
            return
            
        self.host = DB_HOST
        self.port = DB_PORT
        self.user = DB_USER
        self.password = DB_PASSWORD
        self.db_name = DB_NAME
        self.connection = None
    
    def connect(self):
        if pymysql is None:
            print("错误: 由于缺少PyMySQL库，无法连接数据库")
            self.db_available = False
            return False
            
        try:
            self.connection = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.db_name,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            return True
        except Exception as e:
            print(f"数据库连接失败: {e}")
            self.db_available = False
            return False
    
    def initialize_tables(self):
        if not self.db_available:
            return False
        
        if not self.connection:
            if not self.connect():
                return False
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS conversations (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        user_input TEXT NOT NULL,
                        mita_response TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_state (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        affection INT DEFAULT 50,
                        paranoia INT DEFAULT 30,
                        last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                cursor.execute("SELECT COUNT(*) as count FROM user_state")
                result = cursor.fetchone()
                if result['count'] == 0:
                    cursor.execute("INSERT INTO user_state (affection, paranoia) VALUES (50, 30)")
                    
            self.connection.commit()
            return True
        except Exception as e:
            print(f"初始化表失败: {e}")
            self.db_available = False
            return False

    # ------------------ 下面是你缺失的核心方法 ------------------
    def save_conversation(self, user_input, mita_response):
        if not self.db_available:
            return False
        if not self.connection:
            self.connect()

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO conversations (user_input, mita_response) VALUES (%s, %s)",
                    (user_input, mita_response)
                )
            self.connection.commit()
            return True
        except Exception as e:
            print(f"保存对话失败: {e}")
            return False

    def reset_database(self):
        if not self.db_available:
            return False
        if not self.connection:
            self.connect()

        try:
            with self.connection.cursor() as cursor:
                cursor.execute("TRUNCATE TABLE conversations")
            self.connection.commit()
            return True
        except Exception as e:
            print(f"重置数据库失败: {e}")
            return False

    def get_chat_history(self, limit=10):
        if not self.db_available:
            return []
        if not self.connection:
            self.connect()

        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT user_input, mita_response FROM conversations ORDER BY id ASC LIMIT %s", (limit,))
                return cursor.fetchall()
        except Exception as e:
            print(f"获取历史记录失败: {e}")
            return []

    def get_recent_conversations(self, limit=10):
        """获取最近的对话记录"""
        if not self.db_available:
            return []
        if not self.connection:
            self.connect()

        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT user_input, mita_response, created_at FROM conversations ORDER BY id DESC LIMIT %s", (limit,))
                results = cursor.fetchall()
                # 因为按ID倒序排列，需要反转结果以获得正确的时间顺序
                return list(reversed(results))
        except Exception as e:
            print(f"获取最近对话失败: {e}")
            return []

    def get_all_conversations(self):
        """获取所有对话记录"""
        if not self.db_available:
            return []
        if not self.connection:
            self.connect()

        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT id, user_input, mita_response, created_at FROM conversations ORDER BY id ASC")
                return cursor.fetchall()
        except Exception as e:
            print(f"获取所有对话失败: {e}")
            return []

    def get_latest_conversations(self, limit=5):
        """获取最新的对话记录"""
        if not self.db_available:
            return []
        if not self.connection:
            self.connect()

        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT id, user_input, mita_response, created_at FROM conversations ORDER BY id DESC LIMIT %s", (limit,))
                results = cursor.fetchall()
                # 按时间顺序反转，使最早的对话在前
                return list(reversed(results))
        except Exception as e:
            print(f"获取最新对话失败: {e}")
            return []

    def delete_conversation(self, conv_id):
        """删除特定ID的对话记录"""
        if not self.db_available:
            return False
        if not self.connection:
            self.connect()

        try:
            with self.connection.cursor() as cursor:
                cursor.execute("DELETE FROM conversations WHERE id = %s", (conv_id,))
            self.connection.commit()
            return True
        except Exception as e:
            print(f"删除对话记录失败: {e}")
            return False

    def update_conversation(self, conv_id, user_input=None, mita_response=None):
        """更新特定ID的对话记录"""
        if not self.db_available:
            return False
        if not self.connection:
            self.connect()

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
            return True
        except Exception as e:
            print(f"更新对话记录失败: {e}")
            return False

    def get_conversation_count(self):
        """获取对话记录总数"""
        if not self.db_available:
            return 0
        if not self.connection:
            self.connect()

        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) as count FROM conversations")
                result = cursor.fetchone()
                return result['count']
        except Exception as e:
            print(f"获取对话记录总数失败: {e}")
            return 0

    def get_latest_mita_response(self):
        """获取最新一条米塔的回复"""
        if not self.db_available:
            return None
        if not self.connection:
            self.connect()

        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT mita_response FROM conversations ORDER BY id DESC LIMIT 1")
                result = cursor.fetchone()
                return result['mita_response'] if result else None
        except Exception as e:
            print(f"获取最新米塔回复失败: {e}")
            return None

    def update_affection(self, affection_change=0, paranoia_change=0):
        if not self.db_available:
            return False
        if not self.connection:
            self.connect()

        try:
            with self.connection.cursor() as cursor:
                cursor.execute("UPDATE user_state SET affection = affection + %s, paranoia = paranoia + %s WHERE id = 1", (affection_change, paranoia_change))
                cursor.execute("UPDATE user_state SET affection = 0 WHERE affection < 0")
                cursor.execute("UPDATE user_state SET affection = 100 WHERE affection > 100")
                cursor.execute("UPDATE user_state SET paranoia = 0 WHERE paranoia < 0")
                cursor.execute("UPDATE user_state SET paranoia = 100 WHERE paranoia > 100")
            self.connection.commit()
            return True
        except Exception as e:
            print(f"更新好感度/偏执值失败: {e}")
            return False

    def get_user_state(self):
        if not self.db_available:
            return {"affection": 50, "paranoia": 30}
        if not self.connection:
            self.connect()

        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT affection, paranoia FROM user_state WHERE id = 1")
                return cursor.fetchone()
        except Exception as e:
            print(f"获取用户状态失败: {e}")
            return {"affection": 50, "paranoia": 30}
    
    def close(self):
        if self.connection:
            self.connection.close()

# ------------------ 测试函数 ------------------
def test_database_connection():
    print("开始测试数据库连接...")
    
    db_test = DatabaseOperations()
    
    if db_test.connect():
        print("✅ 数据库连接成功！")
    else:
        print("❌ 数据库连接失败！")
        return False
    
    if db_test.initialize_tables():
        print("✅ 表结构初始化成功！")
    else:
        print("❌ 表结构初始化失败！")
        return False

    # 测试保存对话
    test_input = "你好呀米塔"
    test_response = "呜…你终于来找我了…"
    if db_test.save_conversation(test_input, test_response):
        print("✅ 保存对话成功！")
    else:
        print("❌ 保存对话失败！")

    # 测试获取历史
    history = db_test.get_chat_history(5)
    print(f"✅ 获取到 {len(history)} 条历史记录")

    # 测试重置
    if db_test.reset_database():
        print("✅ 重置数据库成功！")

    print("✅ 所有数据库测试通过！")
    db_test.close()

# 全局实例
db_ops = DatabaseOperations()

if __name__ == "__main__":
    test_database_connection()
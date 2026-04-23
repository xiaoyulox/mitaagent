"""
统一配置管理类
支持从.env、JSON、YAML等多种格式加载配置
提供配置验证和默认值管理
"""
import os
import json
from typing import Any, Dict, Optional
from dotenv import load_dotenv


class ConfigManager:
    """统一配置管理器"""
    
    def __init__(self, config_file: Optional[str] = None):
        self._config: Dict[str, Any] = {}
        self._validators: Dict[str, callable] = {}
        
        # 加载 .env 文件
        load_dotenv()
        
        # 如果提供了配置文件，尝试加载
        if config_file and os.path.exists(config_file):
            self.load_from_file(config_file)
        else:
            self.load_from_env()
        
        # 注册验证器
        self._register_validators()
    
    def _register_validators(self):
        """注册配置验证器"""
        self._validators = {
            'API_TEMPERATURE': lambda v: 0.0 <= float(v) <= 1.0,
            'API_MAX_TOKENS': lambda v: int(v) > 0,
            'DB_PORT': lambda v: 1 <= int(v) <= 65535,
            'LOG_LEVEL': lambda v: v.upper() in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
            'MAX_LOG_SIZE': lambda v: int(v) > 0,
            'BACKUP_COUNT': lambda v: int(v) >= 0,
        }
    
    def load_from_env(self):
        """从环境变量加载配置"""
        # API配置
        self._config['DEEPSEEK_API_KEY'] = os.getenv('DEEPSEEK_API_KEY', '')
        self._config['DEEPSEEK_API_URL'] = os.getenv('DEEPSEEK_API_URL', 'https://api.deepseek.com/v1/chat/completions')
        self._config['DEEPSEEK_MODEL'] = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')
        
        # API参数
        self._config['API_TEMPERATURE'] = float(os.getenv('API_TEMPERATURE', '0.7'))
        self._config['API_MAX_TOKENS'] = int(os.getenv('API_MAX_TOKENS', '150'))
        
        # 数据库配置
        self._config['DB_HOST'] = os.getenv('DB_HOST', 'localhost')
        self._config['DB_PORT'] = int(os.getenv('DB_PORT', '3306'))
        self._config['DB_USER'] = os.getenv('DB_USER', 'root')
        self._config['DB_PASSWORD'] = os.getenv('DB_PASSWORD', '')
        self._config['DB_NAME'] = os.getenv('DB_NAME', 'miside_agent')
        
        # 日志配置
        self._config['LOG_LEVEL'] = os.getenv('LOG_LEVEL', 'INFO')
        self._config['LOG_ENABLED'] = os.getenv('LOG_ENABLED', 'True').lower() == 'true'
        self._config['CONSOLE_OUTPUT'] = os.getenv('CONSOLE_OUTPUT', 'True').lower() == 'true'
        self._config['MAX_LOG_SIZE'] = int(os.getenv('MAX_LOG_SIZE', '5242880'))
        self._config['BACKUP_COUNT'] = int(os.getenv('BACKUP_COUNT', '3'))
        
        # 缓存配置
        self._config['CACHE_ENABLED'] = os.getenv('CACHE_ENABLED', 'True').lower() == 'true'
        self._config['CACHE_PERSISTENCE'] = os.getenv('CACHE_PERSISTENCE', 'False').lower() == 'true'
    
    def load_from_json(self, file_path: str):
        """从JSON文件加载配置"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json_config = json.load(f)
                self._config.update(json_config)
            print(f"✅ 已从 JSON 文件加载配置: {file_path}")
        except Exception as e:
            print(f"❌ 加载 JSON 配置失败: {e}")
    
    def load_from_yaml(self, file_path: str):
        """从YAML文件加载配置（需要pyyaml库）"""
        try:
            import yaml
            with open(file_path, 'r', encoding='utf-8') as f:
                yaml_config = yaml.safe_load(f)
                if yaml_config:
                    self._config.update(yaml_config)
            print(f"✅ 已从 YAML 文件加载配置: {file_path}")
        except ImportError:
            print("⚠️  未安装 pyyaml 库，无法加载 YAML 配置")
            print("   安装命令: pip install pyyaml")
        except Exception as e:
            print(f"❌ 加载 YAML 配置失败: {e}")
    
    def load_from_file(self, file_path: str):
        """根据文件扩展名自动选择加载方式"""
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.json':
            self.load_from_json(file_path)
        elif ext in ['.yaml', '.yml']:
            self.load_from_yaml(file_path)
        else:
            print(f"⚠️  不支持的配置文件格式: {ext}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any):
        """设置配置值（带验证）"""
        if key in self._validators:
            try:
                if not self._validators[key](value):
                    raise ValueError(f"配置值无效: {key} = {value}")
            except Exception as e:
                print(f"❌ 配置验证失败: {e}")
                return False
        
        self._config[key] = True
        return True
    
    def validate_all(self) -> bool:
        """验证所有配置"""
        errors = []
        
        for key, validator in self._validators.items():
            if key in self._config:
                try:
                    if not validator(self._config[key]):
                        errors.append(f"{key}: 值无效 - {self._config[key]}")
                except Exception as e:
                    errors.append(f"{key}: 验证错误 - {str(e)}")
        
        if errors:
            print("❌ 配置验证失败:")
            for error in errors:
                print(f"   - {error}")
            return False
        
        print("✅ 配置验证通过")
        return True
    
    def get_api_config(self) -> dict:
        """获取API相关配置"""
        return {
            'api_key': self._config.get('DEEPSEEK_API_KEY', ''),
            'api_url': self._config.get('DEEPSEEK_API_URL', ''),
            'model': self._config.get('DEEPSEEK_MODEL', ''),
            'temperature': self._config.get('API_TEMPERATURE', 0.7),
            'max_tokens': self._config.get('API_MAX_TOKENS', 150),
        }
    
    def get_db_config(self) -> dict:
        """获取数据库相关配置"""
        return {
            'host': self._config.get('DB_HOST', 'localhost'),
            'port': self._config.get('DB_PORT', 3306),
            'user': self._config.get('DB_USER', 'root'),
            'password': self._config.get('DB_PASSWORD', ''),
            'database': self._config.get('DB_NAME', 'miside_agent'),
        }
    
    def get_log_config(self) -> dict:
        """获取日志相关配置"""
        return {
            'level': self._config.get('LOG_LEVEL', 'INFO'),
            'enabled': self._config.get('LOG_ENABLED', True),
            'console_output': self._config.get('CONSOLE_OUTPUT', True),
            'max_size': self._config.get('MAX_LOG_SIZE', 5242880),
            'backup_count': self._config.get('BACKUP_COUNT', 3),
        }
    
    def get_cache_config(self) -> dict:
        """获取缓存相关配置"""
        return {
            'enabled': self._config.get('CACHE_ENABLED', True),
            'persistence': self._config.get('CACHE_PERSISTENCE', False),
        }
    
    def to_dict(self) -> dict:
        """导出所有配置为字典"""
        return self._config.copy()
    
    def __repr__(self):
        return f"ConfigManager(keys={list(self._config.keys())})"


# 创建全局配置实例
config_manager = ConfigManager()

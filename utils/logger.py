import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 创建logs目录（如果不存在）
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# 日志配置
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
LOG_ENABLED = os.getenv('LOG_ENABLED', 'True').lower() == 'true'
CONSOLE_OUTPUT = os.getenv('CONSOLE_OUTPUT', 'True').lower() == 'true'  # 控制台输出开关
MAX_LOG_SIZE = int(os.getenv('MAX_LOG_SIZE', '5242880'))  # 单个日志文件最大大小（默认5MB）
BACKUP_COUNT = int(os.getenv('BACKUP_COUNT', '3'))  # 保留的备份文件数量

# 日志级别映射
LEVEL_MAP = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}

# 设置日志配置
def setup_logger(name, log_file, level=None):
    """创建并配置一个日志记录器，支持日志轮转和控制台开关"""
    if level is None:
        level = LEVEL_MAP.get(LOG_LEVEL, logging.INFO)
    
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 避免重复添加handler
    if logger.handlers:
        return logger
    
    # 文件处理器 - 使用日志轮转
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, log_file),
        maxBytes=MAX_LOG_SIZE,
        backupCount=BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)
    logger.addHandler(file_handler)
    
    # 控制台处理器 - 可开关
    if CONSOLE_OUTPUT:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(level)
        logger.addHandler(console_handler)
    
    return logger

# 日志开关状态
log_enabled = LOG_ENABLED
console_output_enabled = CONSOLE_OUTPUT

def enable_logging():
    """启用日志记录"""
    global log_enabled
    log_enabled = True
    app_logger.info("日志记录已启用")
    return "唉？又要记录我们的对话了呢..."

def disable_logging():
    """禁用日志记录"""
    global log_enabled
    log_enabled = False
    app_logger.info("日志记录已禁用")
    return "唉？不记录我们的对话了呢..."

def enable_console_output():
    """启用控制台输出"""
    global console_output_enabled
    console_output_enabled = True
    # 为所有logger添加控制台handler
    for logger_name in ['app_logger', 'db_logger', 'api_logger']:
        logger = logging.getLogger(logger_name)
        if not any(isinstance(h, logging.StreamHandler) and not isinstance(h, RotatingFileHandler) 
                   for h in logger.handlers):
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter(
                '%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            ))
            console_handler.setLevel(logger.level)
            logger.addHandler(console_handler)
    return "控制台输出已启用"

def disable_console_output():
    """禁用控制台输出"""
    global console_output_enabled
    console_output_enabled = False
    # 移除所有logger的控制台handler
    for logger_name in ['app_logger', 'db_logger', 'api_logger']:
        logger = logging.getLogger(logger_name)
        handlers_to_remove = [
            h for h in logger.handlers 
            if isinstance(h, logging.StreamHandler) and not isinstance(h, RotatingFileHandler)
        ]
        for handler in handlers_to_remove:
            logger.removeHandler(handler)
            handler.close()
    return "控制台输出已禁用"

def set_log_level(level_str):
    """设置日志级别"""
    level = LEVEL_MAP.get(level_str.upper())
    if level is None:
        return f"无效的日志级别: {level_str}，支持: DEBUG/INFO/WARNING/ERROR/CRITICAL"
    
    for logger_name in ['app_logger', 'db_logger', 'api_logger']:
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)
        for handler in logger.handlers:
            handler.setLevel(level)
    
    return f"日志级别已设置为: {level_str.upper()}"

def is_logging_enabled():
    """检查日志是否启用"""
    return log_enabled

def get_log_stats():
    """获取日志统计信息"""
    stats = {
        'enabled': log_enabled,
        'console_output': console_output_enabled,
        'log_level': LOG_LEVEL,
        'max_file_size': f"{MAX_LOG_SIZE / 1024 / 1024:.1f}MB",
        'backup_count': BACKUP_COUNT
    }
    
    # 检查日志文件大小
    for log_file in ['app.log', 'database.log', 'api.log']:
        log_path = os.path.join(log_dir, log_file)
        if os.path.exists(log_path):
            size_mb = os.path.getsize(log_path) / 1024 / 1024
            stats[log_file] = f"{size_mb:.2f}MB"
    
    return stats

# 创建不同的日志记录器
app_logger = setup_logger('app_logger', 'app.log')
db_logger = setup_logger('db_logger', 'database.log')
api_logger = setup_logger('api_logger', 'api.log')

def log_error(error_msg, logger_name='app'):
    """记录错误信息"""
    if not log_enabled:
        return
    
    if logger_name == 'db':
        db_logger.error(error_msg)
    elif logger_name == 'api':
        api_logger.error(error_msg)
    else:
        app_logger.error(error_msg)

def log_warning(warning_msg, logger_name='app'):
    """记录警告信息"""
    if not log_enabled:
        return
    
    if logger_name == 'db':
        db_logger.warning(warning_msg)
    elif logger_name == 'api':
        api_logger.warning(warning_msg)
    else:
        app_logger.warning(warning_msg)

def log_info(info_msg, logger_name='app'):
    """记录一般信息"""
    if not log_enabled:
        return
    
    if logger_name == 'db':
        db_logger.info(info_msg)
    elif logger_name == 'api':
        api_logger.info(info_msg)
    else:
        app_logger.info(info_msg)

def log_debug(debug_msg, logger_name='app'):
    """记录调试信息"""
    if not log_enabled:
        return
    
    if logger_name == 'db':
        db_logger.debug(debug_msg)
    elif logger_name == 'api':
        api_logger.debug(debug_msg)
    else:
        app_logger.debug(debug_msg)
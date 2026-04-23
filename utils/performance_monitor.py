"""
性能监控模块
统计API响应时间、调用次数、数据库查询性能等
"""
import time
from datetime import datetime
from collections import defaultdict
from utils.logger import log_info, log_debug


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        # API统计
        self.api_call_count = 0
        self.api_total_time = 0
        self.api_times = []
        
        # 数据库统计
        self.db_query_count = 0
        self.db_total_time = 0
        self.db_times = []
        
        # 缓存统计
        self.cache_hit_count = 0
        self.cache_miss_count = 0
        
        # 对话统计
        self.conversation_count = 0
        self.start_time = datetime.now()
        
        # 错误统计
        self.error_count = 0
        self.errors = []
    
    def track_api_call(self, func):
        """装饰器：追踪API调用性能"""
        def wrapper(*args, **kwargs):
            start_time = time.time()
            self.api_call_count += 1
            
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time
                self.api_total_time += elapsed
                self.api_times.append(elapsed)
                
                log_debug(f"API调用 #{self.api_call_count} 耗时: {elapsed:.3f}秒")
                return result
            except Exception as e:
                self.error_count += 1
                self.errors.append({
                    'type': 'api',
                    'error': str(e),
                    'time': datetime.now().isoformat()
                })
                raise
        
        return wrapper
    
    def track_db_query(self, func):
        """装饰器：追踪数据库查询性能"""
        def wrapper(*args, **kwargs):
            start_time = time.time()
            self.db_query_count += 1
            
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time
                self.db_total_time += elapsed
                self.db_times.append(elapsed)
                
                log_debug(f"数据库查询 #{self.db_query_count} 耗时: {elapsed:.3f}秒")
                return result
            except Exception as e:
                self.error_count += 1
                self.errors.append({
                    'type': 'database',
                    'error': str(e),
                    'time': datetime.now().isoformat()
                })
                raise
        
        return wrapper
    
    def record_cache_hit(self):
        """记录缓存命中"""
        self.cache_hit_count += 1
    
    def record_cache_miss(self):
        """记录缓存未命中"""
        self.cache_miss_count += 1
    
    def record_conversation(self):
        """记录一次对话"""
        self.conversation_count += 1
    
    def get_api_stats(self) -> dict:
        """获取API统计信息"""
        if self.api_call_count == 0:
            return {
                'total_calls': 0,
                'avg_time': 0,
                'min_time': 0,
                'max_time': 0,
                'total_time': 0
            }
        
        return {
            'total_calls': self.api_call_count,
            'avg_time': f"{self.api_total_time / self.api_call_count:.3f}秒",
            'min_time': f"{min(self.api_times):.3f}秒" if self.api_times else 0,
            'max_time': f"{max(self.api_times):.3f}秒" if self.api_times else 0,
            'total_time': f"{self.api_total_time:.3f}秒"
        }
    
    def get_db_stats(self) -> dict:
        """获取数据库统计信息"""
        if self.db_query_count == 0:
            return {
                'total_queries': 0,
                'avg_time': 0,
                'min_time': 0,
                'max_time': 0,
                'total_time': 0
            }
        
        return {
            'total_queries': self.db_query_count,
            'avg_time': f"{self.db_total_time / self.db_query_count:.3f}秒",
            'min_time': f"{min(self.db_times):.3f}秒" if self.db_times else 0,
            'max_time': f"{max(self.db_times):.3f}秒" if self.db_times else 0,
            'total_time': f"{self.db_total_time:.3f}秒"
        }
    
    def get_cache_stats(self) -> dict:
        """获取缓存统计信息"""
        total = self.cache_hit_count + self.cache_miss_count
        hit_rate = (self.cache_hit_count / total * 100) if total > 0 else 0
        
        return {
            'hit_count': self.cache_hit_count,
            'miss_count': self.cache_miss_count,
            'hit_rate': f"{hit_rate:.1f}%"
        }
    
    def get_overall_stats(self) -> dict:
        """获取整体统计信息"""
        uptime = datetime.now() - self.start_time
        hours = uptime.total_seconds() / 3600
        
        return {
            'uptime': f"{hours:.2f}小时",
            'total_conversations': self.conversation_count,
            'conversations_per_hour': f"{self.conversation_count / hours:.1f}" if hours > 0 else 0,
            'total_errors': self.error_count,
            'api_stats': self.get_api_stats(),
            'db_stats': self.get_db_stats(),
            'cache_stats': self.get_cache_stats()
        }
    
    def print_report(self):
        """打印性能报告"""
        stats = self.get_overall_stats()
        
        print("\n" + "="*60)
        print("📊 性能监控报告")
        print("="*60)
        print(f"运行时间: {stats['uptime']}")
        print(f"对话总数: {stats['total_conversations']}")
        print(f"对话频率: {stats['conversations_per_hour']} 次/小时")
        print(f"错误总数: {stats['total_errors']}")
        
        print("\n🔌 API 统计:")
        api = stats['api_stats']
        print(f"  - 调用次数: {api['total_calls']}")
        print(f"  - 平均耗时: {api['avg_time']}")
        print(f"  - 最快: {api['min_time']}")
        print(f"  - 最慢: {api['max_time']}")
        print(f"  - 总耗时: {api['total_time']}")
        
        print("\n💾 数据库统计:")
        db = stats['db_stats']
        print(f"  - 查询次数: {db['total_queries']}")
        print(f"  - 平均耗时: {db['avg_time']}")
        print(f"  - 最快: {db['min_time']}")
        print(f"  - 最慢: {db['max_time']}")
        print(f"  - 总耗时: {db['total_time']}")
        
        print("\n💿 缓存统计:")
        cache = stats['cache_stats']
        print(f"  - 命中次数: {cache['hit_count']}")
        print(f"  - 未命中次数: {cache['miss_count']}")
        print(f"  - 命中率: {cache['hit_rate']}")
        
        print("="*60 + "\n")
    
    def reset(self):
        """重置所有统计"""
        self.__init__()
        log_info("性能统计已重置")


# 创建全局性能监控实例
perf_monitor = PerformanceMonitor()

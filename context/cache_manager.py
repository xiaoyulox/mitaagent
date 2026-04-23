from datetime import datetime, timedelta
import json
import os
import pickle
from utils.logger import log_info, log_warning, log_debug

class CacheManager:
    """增强版缓存管理器，支持持久化、智能失效和性能监控"""
    
    def __init__(self, cache_dir='cache', enable_persistence=False):
        self.cache = {}
        self.timestamps = {}  # 记录缓存时间
        self.ttl = {}         # 记录过期时间（秒）
        self.access_count = {}  # 访问次数统计
        self.last_access = {}   # 最后访问时间
        self.hit_count = 0      # 缓存命中次数
        self.miss_count = 0     # 缓存未命中次数
        
        # 持久化配置
        self.enable_persistence = enable_persistence
        self.cache_dir = cache_dir
        self.cache_file = os.path.join(cache_dir, 'cache_data.pkl')
        
        if enable_persistence:
            self._ensure_cache_dir()
            self._load_cache()  # 启动时加载缓存
    
    def _ensure_cache_dir(self):
        """确保缓存目录存在"""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def _load_cache(self):
        """从文件加载缓存"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'rb') as f:
                    data = pickle.load(f)
                    self.cache = data.get('cache', {})
                    self.timestamps = data.get('timestamps', {})
                    self.ttl = data.get('ttl', {})
                    # 清理已过期的缓存
                    self._cleanup_expired()
                    log_info(f"缓存已从文件加载: {len(self.cache)} 项")
        except Exception as e:
            log_warning(f"加载缓存失败: {e}")
    
    def _save_cache(self):
        """保存缓存到文件"""
        if not self.enable_persistence:
            return
        
        try:
            data = {
                'cache': self.cache,
                'timestamps': self.timestamps,
                'ttl': self.ttl
            }
            with open(self.cache_file, 'wb') as f:
                pickle.dump(data, f)
            log_debug("缓存已保存到文件")
        except Exception as e:
            log_warning(f"保存缓存失败: {e}")
    
    def _cleanup_expired(self):
        """清理所有过期的缓存项"""
        expired_keys = [
            key for key in self.cache 
            if self._is_expired(key)
        ]
        for key in expired_keys:
            del self.cache[key]
            del self.timestamps[key]
            del self.ttl[key]
            if key in self.access_count:
                del self.access_count[key]
            if key in self.last_access:
                del self.last_access[key]
        
        if expired_keys:
            log_info(f"清理了 {len(expired_keys)} 个过期缓存项")
    
    def set(self, key, value, ttl_seconds=300, priority='normal'):
        """设置缓存项
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl_seconds: 过期时间（秒）
            priority: 优先级 ('high', 'normal', 'low')
        """
        self.cache[key] = value
        self.timestamps[key] = datetime.now()
        self.ttl[key] = ttl_seconds
        self.access_count[key] = self.access_count.get(key, 0)
        self.last_access[key] = datetime.now()
        
        # 根据优先级调整TTL
        if priority == 'high':
            self.ttl[key] = ttl_seconds * 2  # 高优先级缓存时间翻倍
        elif priority == 'low':
            self.ttl[key] = ttl_seconds // 2  # 低优先级缓存时间减半
        
        log_debug(f"缓存已设置: {key}, TTL: {self.ttl[key]}秒, 优先级: {priority}")
        
        # 定期保存缓存（每10次设置操作保存一次）
        if len(self.cache) % 10 == 0:
            self._save_cache()
    
    def get(self, key, default=None):
        """获取缓存项，如果过期则返回None或默认值
        
        Args:
            key: 缓存键
            default: 缓存不存在时的默认值
            
        Returns:
            缓存值或默认值
        """
        if key not in self.cache:
            self.miss_count += 1
            log_debug(f"缓存未命中: {key}")
            return default
            
        if self._is_expired(key):
            self.invalidate(key)
            self.miss_count += 1
            log_debug(f"缓存已过期: {key}")
            return default
        
        # 更新访问统计
        self.hit_count += 1
        self.access_count[key] = self.access_count.get(key, 0) + 1
        self.last_access[key] = datetime.now()
        
        log_debug(f"缓存命中: {key} (访问次数: {self.access_count[key]})")
        return self.cache[key]
    
    def _is_expired(self, key):
        """检查缓存是否过期"""
        if key not in self.timestamps or key not in self.ttl:
            return True
            
        elapsed = (datetime.now() - self.timestamps[key]).total_seconds()
        return elapsed > self.ttl[key]
    
    def invalidate(self, key):
        """清除指定缓存"""
        if key in self.cache:
            del self.cache[key]
            del self.timestamps[key]
            del self.ttl[key]
            if key in self.access_count:
                del self.access_count[key]
            if key in self.last_access:
                del self.last_access[key]
            log_debug(f"缓存已清除: {key}")
            self._save_cache()  # 清除后立即保存
    
    def invalidate_pattern(self, pattern):
        """批量清除匹配模式的缓存
        
        Args:
            pattern: 缓存键的模式（如 'recent_*' 清除所有以 recent_ 开头的缓存）
        """
        import fnmatch
        keys_to_remove = [
            key for key in self.cache 
            if fnmatch.fnmatch(key, pattern)
        ]
        for key in keys_to_remove:
            self.invalidate(key)
        log_info(f"批量清除缓存: {pattern}, 共 {len(keys_to_remove)} 项")
    
    def clear_all(self):
        """清除所有缓存"""
        self.cache.clear()
        self.timestamps.clear()
        self.ttl.clear()
        self.access_count.clear()
        self.last_access.clear()
        self.hit_count = 0
        self.miss_count = 0
        log_info("所有缓存已清除")
        if self.enable_persistence:
            if os.path.exists(self.cache_file):
                os.remove(self.cache_file)
    
    def size(self):
        """获取缓存大小"""
        return len(self.cache)
    
    def get_stats(self):
        """获取缓存统计信息"""
        total_requests = self.hit_count + self.miss_count
        hit_rate = (self.hit_count / total_requests * 100) if total_requests > 0 else 0
        
        # 计算平均访问次数
        avg_access = 0
        if self.access_count:
            avg_access = sum(self.access_count.values()) / len(self.access_count)
        
        stats = {
            'total_items': len(self.cache),
            'hit_count': self.hit_count,
            'miss_count': self.miss_count,
            'hit_rate': f"{hit_rate:.1f}%",
            'avg_access_per_item': f"{avg_access:.1f}",
            'persistence_enabled': self.enable_persistence
        }
        
        # 按优先级分类统计
        high_priority = sum(1 for k in self.cache if self.ttl.get(k, 0) > 600)
        low_priority = sum(1 for k in self.cache if self.ttl.get(k, 0) < 150)
        normal_priority = len(self.cache) - high_priority - low_priority
        
        stats['by_priority'] = {
            'high': high_priority,
            'normal': normal_priority,
            'low': low_priority
        }
        
        return stats
    
    def get_most_accessed(self, top_n=5):
        """获取访问最频繁的缓存项"""
        if not self.access_count:
            return []
        
        sorted_items = sorted(
            self.access_count.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:top_n]
        
        return [
            {'key': key, 'access_count': count}
            for key, count in sorted_items
        ]
    
    def cleanup_low_priority(self):
        """清理低优先级且长时间未访问的缓存"""
        now = datetime.now()
        keys_to_remove = []
        
        for key in self.cache:
            ttl = self.ttl.get(key, 300)
            last_acc = self.last_access.get(key, now)
            access_cnt = self.access_count.get(key, 0)
            
            # 如果TTL短且访问次数少且长时间未访问，则标记为删除
            if ttl < 150 and access_cnt < 3 and (now - last_acc).total_seconds() > 600:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            self.invalidate(key)
        
        if keys_to_remove:
            log_info(f"清理了 {len(keys_to_remove)} 个低优先级缓存项")
        
        return len(keys_to_remove)


# 创建全局缓存实例
cache_manager = CacheManager()
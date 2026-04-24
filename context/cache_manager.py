
from datetime import datetime, timedelta
import json
import os
import pickle
import threading
import time
from collections import OrderedDict
from queue import Queue, Empty
from utils.logger import log_info, log_warning, log_debug, log_error


class CacheManagerV2:
    """增强版缓存管理器，支持线程安全、LRU淘汰、异步持久化"""
    
    def __init__(self, 
                 cache_dir='cache', 
                 enable_persistence=True,
                 max_size=1000,
                 auto_cleanup_interval=300):
        """
        初始化缓存管理器
        
        Args:
            cache_dir: 缓存目录
            enable_persistence: 是否启用持久化
            max_size: 最大缓存项数量
            auto_cleanup_interval: 自动清理间隔（秒）
        """
        # 核心数据结构
        self.cache = OrderedDict()  # 保持插入顺序，支持 LRU
        self.timestamps = {}  # 记录缓存时间
        self.ttl = {}  # 记录过期时间（秒）
        self.priority = {}  # 优先级权重
        self.access_count = {}  # 访问次数统计
        self.last_access = {}  # 最后访问时间
        
        # 统计信息
        self.hit_count = 0
        self.miss_count = 0
        
        # 线程安全
        self.lock = threading.RLock()  # 可重入锁
        
        # 配置
        self.max_size = max_size
        self.enable_persistence = enable_persistence
        self.cache_dir = cache_dir
        self.cache_file = os.path.join(cache_dir, 'cache_data_v2.pkl')
        
        # 异步持久化
        self.save_queue = Queue()
        self.save_thread = None
        self.cleanup_thread = None
        self._running = False
        
        # 初始化
        if enable_persistence:
            self._ensure_cache_dir()
            self._load_cache()
        
        # 启动后台任务
        self._start_background_tasks(auto_cleanup_interval)
    
    def _ensure_cache_dir(self):
        """确保缓存目录存在"""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
            log_info(f"创建缓存目录: {self.cache_dir}")
    
    def _start_background_tasks(self, cleanup_interval):
        """启动后台任务线程"""
        self._running = True
        
        # 启动持久化工作线程
        self.save_thread = threading.Thread(
            target=self._save_worker, 
            daemon=True,
            name="CacheSaveWorker"
        )
        self.save_thread.start()
        log_debug("缓存保存工作线程已启动")
        
        # 启动定期清理线程
        if cleanup_interval > 0:
            self.cleanup_thread = threading.Thread(
                target=self._cleanup_worker,
                args=(cleanup_interval,),
                daemon=True,
                name="CacheCleanupWorker"
            )
            self.cleanup_thread.start()
            log_debug(f"缓存清理工作线程已启动 (间隔: {cleanup_interval}秒)")
    
    def _save_worker(self):
        """后台保存工作线程"""
        while self._running:
            try:
                # 等待保存信号，最多等待 30 秒
                self.save_queue.get(timeout=30)
                
                # 批量保存（等待更多请求）
                time.sleep(1)
                
                # 清空队列中的重复请求
                while not self.save_queue.empty():
                    try:
                        self.save_queue.get_nowait()
                    except Empty:
                        break
                
                # 执行保存
                self._save_cache()
                self.save_queue.task_done()
                
            except Empty:
                # 超时，继续循环
                continue
            except Exception as e:
                log_error(f"缓存保存工作线程错误: {e}")
    
    def _cleanup_worker(self, interval):
        """定期清理工作线程"""
        while self._running:
            try:
                time.sleep(interval)
                
                with self.lock:
                    expired_count = self._cleanup_expired_internal()
                    low_priority_count = self._cleanup_low_priority_internal()
                
                if expired_count > 0 or low_priority_count > 0:
                    log_info(
                        f"定期清理完成: "
                        f"过期={expired_count}, 低优先级={low_priority_count}"
                    )
                    
            except Exception as e:
                log_error(f"缓存清理工作线程错误: {e}")
    
    def _load_cache(self):
        """从文件加载缓存"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'rb') as f:
                    data = pickle.load(f)
                    
                    with self.lock:
                        self.cache = OrderedDict(data.get('cache', {}))
                        self.timestamps = data.get('timestamps', {})
                        self.ttl = data.get('ttl', {})
                        self.priority = data.get('priority', {})
                        
                        # 清理已过期的缓存
                        self._cleanup_expired_internal()
                        
                    log_info(f"缓存已从文件加载: {len(self.cache)} 项")
            else:
                log_debug("缓存文件不存在，使用空缓存")
        except Exception as e:
            log_warning(f"加载缓存失败: {e}，使用空缓存")
            # 重置所有状态
            with self.lock:
                self.cache = OrderedDict()
                self.timestamps = {}
                self.ttl = {}
                self.priority = {}
    
    def _save_cache(self):
        """保存缓存到文件"""
        if not self.enable_persistence:
            return
        
        try:
            with self.lock:
                data = {
                    'cache': dict(self.cache),
                    'timestamps': self.timestamps,
                    'ttl': self.ttl,
                    'priority': self.priority
                }
            
            # 临时文件原子写入
            temp_file = self.cache_file + '.tmp'
            with open(temp_file, 'wb') as f:
                pickle.dump(data, f)
            
            # 原子替换
            if os.path.exists(self.cache_file):
                os.remove(self.cache_file)
            os.rename(temp_file, self.cache_file)
            
            log_debug(f"缓存已保存到文件 ({len(self.cache)} 项)")
        except Exception as e:
            log_error(f"保存缓存失败: {e}")
            # 清理临时文件
            if os.path.exists(self.cache_file + '.tmp'):
                try:
                    os.remove(self.cache_file + '.tmp')
                except:
                    pass
    
    def _cleanup_expired_internal(self):
        """内部方法：清理所有过期的缓存项（需要在锁内调用）"""
        expired_keys = [
            key for key in list(self.cache.keys())
            if self._is_expired_internal(key)
        ]
        
        for key in expired_keys:
            self._invalidate_internal(key)
        
        return len(expired_keys)
    
    def _cleanup_low_priority_internal(self):
        """内部方法：清理低优先级缓存（需要在锁内调用）"""
        now = datetime.now()
        keys_to_remove = []
        
        for key in list(self.cache.keys()):
            ttl = self.ttl.get(key, 300)
            last_acc = self.last_access.get(key, now)
            access_cnt = self.access_count.get(key, 0)
            priority_weight = self.priority.get(key, 2)
            
            # 如果TTL短、访问次数少、长时间未访问、且优先级低
            if (ttl < 150 and 
                access_cnt < 3 and 
                (now - last_acc).total_seconds() > 600 and
                priority_weight <= 1):
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            self._invalidate_internal(key)
        
        return len(keys_to_remove)
    
    def set(self, key, value, ttl_seconds=300, priority='normal'):
        """设置缓存项
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl_seconds: 过期时间（秒）
            priority: 优先级 ('high', 'normal', 'low')
        """
        with self.lock:
            # 优先级映射到权重
            priority_weights = {
                'high': 3,
                'normal': 2,
                'low': 1
            }
            weight = priority_weights.get(priority, 2)
            
            # 如果已存在，先删除（会触发 LRU 更新）
            if key in self.cache:
                del self.cache[key]
            
            # 检查是否需要淘汰
            while len(self.cache) >= self.max_size:
                self._evict_lru_internal()
            
            # 设置缓存
            self.cache[key] = value
            self.cache.move_to_end(key)  # 移到末尾（最近使用）
            
            self.timestamps[key] = datetime.now()
            self.ttl[key] = ttl_seconds
            self.priority[key] = weight
            self.access_count[key] = self.access_count.get(key, 0)
            self.last_access[key] = datetime.now()
            
            # 根据优先级调整TTL
            if priority == 'high':
                self.ttl[key] = ttl_seconds * 2  # 高优先级缓存时间翻倍
            elif priority == 'low':
                self.ttl[key] = ttl_seconds // 2  # 低优先级缓存时间减半
            
            log_debug(
                f"缓存已设置: {key}, "
                f"TTL: {self.ttl[key]}秒, "
                f"优先级: {priority}, "
                f"当前大小: {len(self.cache)}/{self.max_size}"
            )
            
            # 触发异步保存
            if len(self.cache) % 10 == 0:
                try:
                    self.save_queue.put_nowait('save')
                except:
                    pass
    
    def get(self, key, default=None):
        """获取缓存项，如果过期则返回None或默认值
        
        Args:
            key: 缓存键
            default: 缓存不存在时的默认值
            
        Returns:
            缓存值或默认值
        """
        with self.lock:
            if key not in self.cache:
                self.miss_count += 1
                log_debug(f"缓存未命中: {key}")
                return default
                
            if self._is_expired_internal(key):
                self._invalidate_internal(key)
                self.miss_count += 1
                log_debug(f"缓存已过期: {key}")
                return default
            
            # 更新访问统计
            self.hit_count += 1
            self.access_count[key] = self.access_count.get(key, 0) + 1
            self.last_access[key] = datetime.now()
            
            # 移动到末尾（标记为最近使用）
            self.cache.move_to_end(key)
            
            log_debug(
                f"缓存命中: {key} "
                f"(访问次数: {self.access_count[key]})"
            )
            return self.cache[key]
    
    def _is_expired_internal(self, key):
        """内部方法：检查缓存是否过期（需要在锁内调用）"""
        if key not in self.timestamps or key not in self.ttl:
            return True
            
        elapsed = (datetime.now() - self.timestamps[key]).total_seconds()
        return elapsed > self.ttl[key]
    
    def invalidate(self, key):
        """清除指定缓存"""
        with self.lock:
            self._invalidate_internal(key)
        
        # 触发异步保存
        try:
            self.save_queue.put_nowait('save')
        except:
            pass
    
    def _invalidate_internal(self, key):
        """内部方法：清除指定缓存（需要在锁内调用）"""
        if key in self.cache:
            del self.cache[key]
            del self.timestamps[key]
            del self.ttl[key]
            if key in self.priority:
                del self.priority[key]
            if key in self.access_count:
                del self.access_count[key]
            if key in self.last_access:
                del self.last_access[key]
            log_debug(f"缓存已清除: {key}")
    
    def invalidate_pattern(self, pattern):
        """批量清除匹配模式的缓存
        
        Args:
            pattern: 缓存键的模式（如 'recent_*' 清除所有以 recent_ 开头的缓存）
        """
        import fnmatch
        
        with self.lock:
            keys_to_remove = [
                key for key in list(self.cache.keys())
                if fnmatch.fnmatch(key, pattern)
            ]
            
            for key in keys_to_remove:
                self._invalidate_internal(key)
        
        if keys_to_remove:
            log_info(f"批量清除缓存: {pattern}, 共 {len(keys_to_remove)} 项")
            
            # 触发异步保存
            try:
                self.save_queue.put_nowait('save')
            except:
                pass
    
    def clear_all(self):
        """清除所有缓存"""
        with self.lock:
            self.cache.clear()
            self.timestamps.clear()
            self.ttl.clear()
            self.priority.clear()
            self.access_count.clear()
            self.last_access.clear()
            self.hit_count = 0
            self.miss_count = 0
        
        log_info("所有缓存已清除")
        
        if self.enable_persistence:
            if os.path.exists(self.cache_file):
                try:
                    os.remove(self.cache_file)
                    log_debug("缓存文件已删除")
                except Exception as e:
                    log_warning(f"删除缓存文件失败: {e}")
    
    def _evict_lru_internal(self):
        """内部方法：LRU 淘汰（需要在锁内调用）"""
        if not self.cache:
            return
        
        # 计算每个键的淘汰分数（分数越高越应该被淘汰）
        scores = {}
        now = datetime.now()
        
        for key in self.cache:
            priority_weight = self.priority.get(key, 2)
            access_count = self.access_count.get(key, 0)
            last_access = self.last_access.get(key, now)
            age = (now - last_access).total_seconds()
            
            # 淘汰分数 = 年龄 / (优先级 * 访问次数)
            score = age / (priority_weight * max(access_count, 1))
            scores[key] = score
        
        # 淘汰分数最高的
        victim = max(scores, key=scores.get)
        self._invalidate_internal(victim)
        log_debug(f"LRU 淘汰: {victim} (分数: {scores[victim]:.2f})")
    
    def size(self):
        """获取缓存大小"""
        with self.lock:
            return len(self.cache)
    
    def get_stats(self):
        """获取缓存统计信息"""
        with self.lock:
            total_requests = self.hit_count + self.miss_count
            hit_rate = (self.hit_count / total_requests * 100) if total_requests > 0 else 0
            
            # 计算平均访问次数
            avg_access = 0
            if self.access_count:
                avg_access = sum(self.access_count.values()) / len(self.access_count)
            
            # 内存使用估算
            estimated_size = sum(len(str(v)) for v in self.cache.values())
            
            stats = {
                'total_items': len(self.cache),
                'max_capacity': self.max_size,
                'capacity_usage': f"{len(self.cache)/self.max_size*100:.1f}%",
                'estimated_memory_kb': round(estimated_size / 1024, 2),
                'hit_count': self.hit_count,
                'miss_count': self.miss_count,
                'hit_rate': f"{hit_rate:.1f}%",
                'avg_access_per_item': f"{avg_access:.1f}",
                'persistence_enabled': self.enable_persistence,
                'queue_size': self.save_queue.qsize()
            }
            
            # 按优先级分类统计
            high_priority = sum(1 for w in self.priority.values() if w >= 3)
            low_priority = sum(1 for w in self.priority.values() if w <= 1)
            normal_priority = len(self.cache) - high_priority - low_priority
            
            stats['by_priority'] = {
                'high': high_priority,
                'normal': normal_priority,
                'low': low_priority
            }
            
            # 告警检查
            if total_requests > 100 and hit_rate < 30:
                log_warning(f"⚠️ 缓存命中率过低: {hit_rate:.1f}%")
            
            if len(self.cache) > self.max_size * 0.9:
                log_warning(
                    f"⚠️ 缓存容量即将耗尽: "
                    f"{len(self.cache)}/{self.max_size}"
                )
            
            return stats
    
    def get_most_accessed(self, top_n=5):
        """获取访问最频繁的缓存项"""
        with self.lock:
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
    
    def shutdown(self):
        """优雅关闭缓存管理器"""
        log_info("正在关闭缓存管理器...")
        self._running = False
        
        # 等待保存线程完成
        if self.save_thread and self.save_thread.is_alive():
            # 强制保存一次
            try:
                self.save_queue.put_nowait('save')
            except:
                pass
            self.save_thread.join(timeout=5)
        
        # 最后一次保存
        if self.enable_persistence:
            self._save_cache()
        
        log_info("缓存管理器已关闭")


# 创建全局缓存实例
cache_manager = CacheManagerV2()

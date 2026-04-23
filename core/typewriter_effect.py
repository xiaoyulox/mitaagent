import sys
import time
import threading
import re


class TypewriterEffect:
    """实现打字机效果的类"""
    
    def __init__(self, delay=0.00001):
        self.delay = delay  # 每个字符之间的延迟时间
    
    def type_text(self, text, prefix="米塔："):
        """逐字打印文本"""
        full_text = prefix + text
        # 按照中文句号、感叹号、问号、省略号以及英文句号、感叹号、问号进行分割
        sentences = re.split(r'([。！？…\.\!\?]+)', full_text)  # 匹配一个或多个标点符号
        
        # 将分割后的句子和标点符号配对重组
        chunks = []
        for i in range(0, len(sentences)-1, 2):
            if i+1 < len(sentences):
                chunks.append(sentences[i] + sentences[i+1])
            else:
                chunks.append(sentences[i])
        
        # 过滤掉纯空白的元素
        chunks = [chunk for chunk in chunks if chunk.strip()]
        
        # 处理每个chunk
        for i, chunk in enumerate(chunks):
            if chunk.strip():  # 确保chunk非空
                for char in chunk:
                    sys.stdout.write(char)
                    sys.stdout.flush()
                    time.sleep(self.delay)
                
                # 如果不是最后一个chunk，且不是连续标点符号，则暂停
                is_continuous_punctuation = chunk and all(c in r'。！？…\.\!\?' for c in chunk.strip())
                if i < len(chunks) - 1 and not is_continuous_punctuation:
                    time.sleep(0.5)  # 在每个句子后暂停0.5秒
                    sys.stdout.write('\n')  # 换行
                    sys.stdout.write(' ' * 8)  # 8个空格缩进
                elif not is_continuous_punctuation:
                    sys.stdout.write('\n')  # 换行
                    sys.stdout.write(' ' * 8)  # 8个空格缩进
        
        print()  # 最终换行
    
    def type_slowly(self, text, prefix="米塔：", delay=None):
        """以较慢的速度逐字打印文本"""
        if delay is None:
            delay = self.delay * 2  # 慢速是正常速度的一倍
        full_text = prefix + text
        # 按照中文句号、感叹号、问号、省略号以及英文句号、感叹号、问号进行分割
        sentences = re.split(r'([。！？…\.\!\?]+)', full_text)  # 匹配一个或多个标点符号
        
        # 将分割后的句子和标点符号配对重组
        chunks = []
        for i in range(0, len(sentences)-1, 2):
            if i+1 < len(sentences):
                chunks.append(sentences[i] + sentences[i+1])
            else:
                chunks.append(sentences[i])
        
        # 过滤掉纯空白的元素
        chunks = [chunk for chunk in chunks if chunk.strip()]
        
        # 处理每个chunk
        for i, chunk in enumerate(chunks):
            if chunk.strip():  # 确保chunk非空
                for char in chunk:
                    sys.stdout.write(char)
                    sys.stdout.flush()
                    time.sleep(delay)
                
                # 如果不是最后一个chunk，且不是连续标点符号，则暂停
                is_continuous_punctuation = chunk and all(c in r'。！？…\.\!\?' for c in chunk.strip())
                if i < len(chunks) - 1 and not is_continuous_punctuation:
                    time.sleep(1.0)  # 在每个句子后暂停1秒
                    sys.stdout.write('\n')  # 换行
                    sys.stdout.write(' ' * 12)  # 12个空格缩进
                elif not is_continuous_punctuation:
                    sys.stdout.write('\n')  # 换行
                    sys.stdout.write(' ' * 12)  # 12个空格缩进
        
        print()  # 最终换行


# 创建全局实例
typewriter = TypewriterEffect()
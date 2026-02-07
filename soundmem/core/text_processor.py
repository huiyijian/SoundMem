"""
文本处理模块
对ASR输出的文本进行分段和清洗
"""

import re
from typing import List, Dict, Any
from datetime import datetime
from soundmem.utils.logger import log

class TextProcessor:
    """文本处理器"""
    
    def __init__(self, max_chunk_size: int = 500, min_chunk_size: int = 50):
        """
        初始化文本处理器
        
        Args:
            max_chunk_size: 最大分块大小（字符数）
            min_chunk_size: 最小分块大小（字符数）
        """
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        
        # 句子结束标点
        self.sentence_endings = ['。', '！', '？', '.', '!', '?', '\n']
        
        log.info(f"文本处理器初始化: max_chunk={max_chunk_size}, min_chunk={min_chunk_size}")
    
    def clean_text(self, text: str) -> str:
        """
        清洗文本
        
        Args:
            text: 原始文本
            
        Returns:
            清洗后的文本
        """
        if not text:
            return ""
        
        # 去除多余空格
        text = re.sub(r'\s+', ' ', text)
        
        # 去除首尾空格
        text = text.strip()
        
        return text
    
    def split_into_sentences(self, text: str) -> List[str]:
        """
        将文本分割成句子
        
        Args:
            text: 输入文本
            
        Returns:
            句子列表
        """
        if not text:
            return []
        
        sentences = []
        current_sentence = ""
        
        for char in text:
            current_sentence += char
            if char in self.sentence_endings:
                if current_sentence.strip():
                    sentences.append(current_sentence.strip())
                current_sentence = ""
        
        # 添加最后一个句子
        if current_sentence.strip():
            sentences.append(current_sentence.strip())
        
        return sentences
    
    def chunk_text(self, text: str, timestamp: str = None) -> List[Dict[str, Any]]:
        """
        将文本分块
        
        Args:
            text: 输入文本
            timestamp: 时间戳
            
        Returns:
            文本块列表
        """
        if not text:
            return []
        
        # 清洗文本
        text = self.clean_text(text)
        
        # 如果文本长度小于最大块大小，直接返回
        if len(text) <= self.max_chunk_size:
            return [{
                "text": text,
                "timestamp": timestamp or datetime.now().isoformat(),
                "length": len(text)
            }]
        
        # 分割成句子
        sentences = self.split_into_sentences(text)
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # 如果当前块加上新句子不超过最大大小
            if len(current_chunk) + len(sentence) <= self.max_chunk_size:
                current_chunk += sentence
            else:
                # 保存当前块
                if len(current_chunk) >= self.min_chunk_size:
                    chunks.append({
                        "text": current_chunk,
                        "timestamp": timestamp or datetime.now().isoformat(),
                        "length": len(current_chunk)
                    })
                
                # 开始新块
                current_chunk = sentence
        
        # 添加最后一个块
        if current_chunk and len(current_chunk) >= self.min_chunk_size:
            chunks.append({
                "text": current_chunk,
                "timestamp": timestamp or datetime.now().isoformat(),
                "length": len(current_chunk)
            })
        
        log.info(f"文本分块完成: 原始长度={len(text)}, 块数={len(chunks)}")
        
        return chunks
    
    def merge_chunks(self, chunks: List[str], separator: str = " ") -> str:
        """
        合并文本块
        
        Args:
            chunks: 文本块列表
            separator: 分隔符
            
        Returns:
            合并后的文本
        """
        return separator.join(chunks)
    
    def extract_keywords(self, text: str, top_k: int = 5) -> List[str]:
        """
        提取关键词（简单实现）
        
        Args:
            text: 输入文本
            top_k: 返回前K个关键词
            
        Returns:
            关键词列表
        """
        # TODO: 实现更复杂的关键词提取算法
        # 这里只是简单的词频统计
        words = re.findall(r'\w+', text)
        word_freq = {}
        
        for word in words:
            if len(word) > 1:  # 过滤单字
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # 按频率排序
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        
        return [word for word, freq in sorted_words[:top_k]]


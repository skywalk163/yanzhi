
# -*- coding: utf-8 -*-
"""
修复版缓存优化分词器
继承原始分词器，只添加缓存和优化常用方法
"""
from typing import List, Dict, Any
from .pre_tokenizer import TokenType, Token, PreTokenizer


class CachedPreTokenizer(PreTokenizer):
    """带缓存的预分词器优化版"""
    
    # 类级缓存：存储常见模式的分词结果
    _cache: Dict[str, List[Token]] = {}
    _cache_hits = 0
    _cache_misses = 0
    _max_cache_size = 1000
    
    def __init__(self, source: str):
        # 调用父类初始化
        super().__init__(source)
        # 预计算长度
        self.source_len = len(source)
    
    def tokenize(self) -> List[Token]:
        """带缓存的分词"""
        # 检查缓存
        cache_key = self.source
        if cache_key in self._cache:
            CachedPreTokenizer._cache_hits += 1
            # 返回缓存的副本（避免修改）
            return [Token(t.type, t.value, t.line, t.column) for t in self._cache[cache_key]]
        
        CachedPreTokenizer._cache_misses += 1
        
        # 调用父类的分词逻辑
        tokens = super().tokenize()
        
        # 缓存结果（如果缓存未满）
        if len(self._cache) < self._max_cache_size:
            self._cache[cache_key] = tokens.copy()
        
        return tokens
    
    # 优化高频方法，减少方法调用开销
    def peek(self) -> str:
        """优化版peek，直接访问属性"""
        if self.pos >= self.source_len:
            return '\0'
        return self.source[self.pos]
    
    def at_end(self) -> bool:
        """优化版at_end，直接比较"""
        return self.pos >= self.source_len
    
    def advance(self) -> str:
        """优化版advance，减少方法调用"""
        if self.pos >= self.source_len:
            return '\0'
        
        char = self.source[self.pos]
        self.pos += 1
        
        if char == '\n':
            self.line += 1
            self.column = 0
        else:
            self.column += 1
        
        return char
    
    def scan_chinese(self):
        """优化版中文扫描"""
        # 预计算最大匹配长度
        max_len = min(4, self.source_len - self.pos)
        
        # 尝试贪心匹配最长的关键字/动词/副词
        for length in range(max_len, 0, -1):
            text = self.source[self.pos:self.pos+length]

            # 合并集合查找逻辑
            if text in self.VERBS:
                for _ in range(length):
                    self.advance()
                self.add_token(TokenType.VERB, text)
                return

            if text in self.KEYWORDS:
                for _ in range(length):
                    self.advance()
                self.add_token(TokenType.KEYWORD, text)
                return

            if text in self.ADVERBS:
                for _ in range(length):
                    self.advance()
                self.add_token(TokenType.ADVERB, text)
                return
        
        # 如果不是关键字/动词/副词，则作为标识符
        start = self.pos
        self.advance()  # 至少前进一个字符
        
        # 继续扫描，直到遇到关键字/动词/副词或非中文字符
        while self.pos < self.source_len:
            char = self.source[self.pos]
            if not ('\u4e00' <= char <= '\u9fff'):
                break
            
            # 检查后续2+字符是否形成完整的动词/关键字
            found_multi = False
            remaining = self.source_len - self.pos
            for length in range(min(4, remaining), 1, -1):
                text = self.source[self.pos:self.pos+length]
                if text in self.VERBS or text in self.KEYWORDS or text in self.ADVERBS:
                    found_multi = True
                    break
            if found_multi:
                break
            
            self.advance()
        
        text = self.source[start:self.pos]
        
        # 检查是否为中文数字
        if self.is_chinese_number(text):
            value = self.parse_chinese_number(text)
            self.add_token(TokenType.NUM, value)
        else:
            self.add_token(TokenType.IDENT, text)
    
    @classmethod
    def get_cache_stats(cls) -> Dict[str, Any]:
        """获取缓存统计信息"""
        return {
            'hits': cls._cache_hits,
            'misses': cls._cache_misses,
            'hit_rate': cls._cache_hits / max(cls._cache_hits + cls._cache_misses, 1),
            'size': len(cls._cache),
            'max_size': cls._max_cache_size
        }
    
    @classmethod
    def clear_cache(cls):
        """清空缓存"""
        cls._cache.clear()
        cls._cache_hits = 0
        cls._cache_misses = 0


def tokenize_cached(source: str) -> List[Token]:
    """带缓存的分词函数"""
    tokenizer = CachedPreTokenizer(source)
    return tokenizer.tokenize()


if __name__ == '__main__':
    # 测试代码
    test_cases = [
        "定义x=5相加3。",
        "列表1 2 3，映射相乘2。",
        "如果x大于y那么x否则y。",
        "张三=18。",
    ]
    
    for source in test_cases:
        print(f"\n源码: {source}")
        tokens = tokenize_cached(source)
        for token in tokens:
            if token.type != TokenType.EOF:
                print(f"  {token}")
    
    # 测试缓存
    stats = CachedPreTokenizer.get_cache_stats()
    print(f"\n缓存统计: 命中{stats['hits']}次, 未命中{stats['misses']}次, 命中率{stats['hit_rate']:.1%}")

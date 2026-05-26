




# -*- coding: utf-8 -*-
"""
带缓存的分词器优化版
减少方法调用开销，添加简单缓存
"""
from typing import List, Dict, Any
import functools
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
        
        # 预计算长度以减少len()调用
        self.source_len = len(source)
        
        # 优化：内联常用方法
        self._peek = self._inline_peek
        self._at_end = self._inline_at_end
        self._advance = self._advance_inline
    
    def _inline_peek(self) -> str:
        """内联版peek，减少方法调用开销"""
        if self.pos >= self.source_len:
            return '\0'
        return self.source[self.pos]
    
    def _inline_at_end(self) -> bool:
        """内联版at_end"""
        return self.pos >= self.source_len
    
    def tokenize(self) -> List[Token]:
        """带缓存的分词"""
        # 检查缓存
        cache_key = self.source
        if cache_key in self._cache:
            CachedPreTokenizer._cache_hits += 1
            # 返回缓存的副本（避免修改）
            return [Token(t.type, t.value, t.line, t.column) for t in self._cache[cache_key]]
        
        CachedPreTokenizer._cache_misses += 1
        
        # 调用父类的分词逻辑（但使用优化后的方法）
        tokens = super().tokenize()
        
        # 缓存结果（如果缓存未满）
        if len(self._cache) < self._max_cache_size:
            self._cache[cache_key] = tokens.copy()
        
        return tokens
    
    # 重写关键方法以使用内联版本
    def peek(self) -> str:
        """优化版peek，减少方法调用开销"""
        if self.pos >= self.source_len:
            return '\0'
        return self.source[self.pos]
    
    def at_end(self) -> bool:
        """优化版at_end"""
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
        """重写中文扫描以使用优化版本"""
        self.scan_chinese_optimized()
    
    def scan_token_optimized(self):
        """优化版scan_token，减少方法调用"""
        # 内联peek和at_end
        if self.pos >= self.source_len:
            return
        
        # 跳过空白符（内联逻辑）
        char = self.source[self.pos]
        if char.isspace():
            self._advance_inline()
            return
        
        # 1. 结构锚点优先
        if self._match_inline('$('):
            self.scan_math_expr()
            return
        
        if self._match_inline('{{'):
            self.scan_python_block()
            return
        
        # 2. 字符串
        if char == '"':
            self.scan_string()
            return
        
        # 3. 注释处理
        if char == '#':
            self.scan_hash_comment()
            return
        
        if self._match_inline('--'):
            # 检查是否是注释
            if self.pos >= self.source_len or self.source[self.pos].isspace():
                self.scan_comment()
                return
            else:
                # 不是注释，回退
                self.pos -= 2
                self.column -= 2
        
        # 4. 数字（内联检查）
        if char.isdigit() or char == '.':
            self.scan_number()
            return

        # 5. 标点符号（包含中文标点）
        punctuation_map = {'.': TokenType.DOT, ',': TokenType.COMMA, ':': TokenType.COLON, 
                          '=': TokenType.EQUALS, "'": TokenType.QUOTE,
                          '。': TokenType.DOT, '，': TokenType.COMMA, '：': TokenType.COLON,
                          '【': TokenType.CLBRACKET, '】': TokenType.CRBRACKET}
        if char in punctuation_map:
            self._advance_inline()
            self.add_token(punctuation_map[char], char)
            return

        # 6. 内联数学运算符
        if char in '+-*/%^()[]<>!=':
            self.scan_math_operator()
            return

        # 7. 中文关键字/动词/标识符（优化版本）
        if '\u4e00' <= char <= '\u9fff':
            self.scan_chinese_optimized()
            return

        # 8. 英文标识符
        if char.isalpha() or char == '_':
            self.scan_identifier()
            return

        # 无法识别的字符
        raise SyntaxError(f"无法识别的字符: {char} (行{self.line}, 列{self.column})")
    
    def scan_chinese_optimized(self):
        """优化版中文扫描，减少集合查找次数"""
        # 优化：预计算最大匹配长度
        max_len = min(4, self.source_len - self.pos)
        
        # 尝试贪心匹配最长的关键字/动词/副词
        for length in range(max_len, 0, -1):
            text = self.source[self.pos:self.pos+length]

            # 优化：合并集合查找逻辑
            if text in self.VERBS:
                for _ in range(length):
                    self._advance_inline()
                self.add_token(TokenType.VERB, text)
                return

            if text in self.KEYWORDS:
                for _ in range(length):
                    self._advance_inline()
                self.add_token(TokenType.KEYWORD, text)
                return

            if text in self.ADVERBS:
                for _ in range(length):
                    self._advance_inline()
                self.add_token(TokenType.ADVERB, text)
                return
        
        # 如果不是关键字/动词/副词，则作为标识符的一个字符
        start = self.pos
        self._advance_inline()  # 至少前进一个字符
        
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
            
            self._advance_inline()
        
        text = self.source[start:self.pos]
        
        # 检查是否为中文数字
        if self.is_chinese_number(text):
            value = self.parse_chinese_number(text)
            self.add_token(TokenType.NUM, value)
        else:
            self.add_token(TokenType.IDENT, text)
    
    def _advance_inline(self):
        """内联版advance，减少方法调用"""
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
    
    def _match_inline(self, expected: str) -> bool:
        """内联版match"""
        exp_len = len(expected)
        if self.pos + exp_len > self.source_len:
            return False
        
        actual = self.source[self.pos:self.pos+exp_len]
        if actual == expected:
            for _ in range(exp_len):
                self._advance_inline()
            return True
        
        return False
    
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
    ]
    
    for source in test_cases:
        print(f"\n源码: {source}")
        tokens = tokenize_cached(source)
        for token in tokens:
            if token.type != TokenType.EOF:
                print(f"  {token}")
    
    # 测试缓存
    print(f"\n缓存统计: {CachedPreTokenizer.get_cache_stats()}")
    
    # 再次运行相同代码测试缓存命中
    for source in test_cases:
        tokens = tokenize_cached(source)
    
    print(f"缓存统计(第二次): {CachedPreTokenizer.get_cache_stats()}")





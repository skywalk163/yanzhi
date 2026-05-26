

# -*- coding: utf-8 -*-
"""
优化版预分词器：使用Trie树加速中文分词
"""

from typing import List, Any
from .pre_tokenizer import TokenType, Token
from .trie import get_keyword_trie


class OptimizedPreTokenizer:
    """优化版预分词器：使用Trie树加速中文分词"""
    
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []
        self.trie = get_keyword_trie()  # 使用全局Trie实例
        
        # 常用标点符号
        self.punctuation_map = {
            '。': TokenType.DOT,
            '，': TokenType.COMMA,
            '：': TokenType.COLON,
            '=': TokenType.EQUALS,
            '\'': TokenType.QUOTE,
            '【': TokenType.CLBRACKET,
            '】': TokenType.CRBRACKET,
        }
        
        # 数学运算符映射
        self.math_operator_map = {
            '+': (TokenType.PLUS, '+'),
            '-': (TokenType.MINUS, '-'),
            '*': (TokenType.STAR, '*'),
            '/': (TokenType.SLASH, '/'),
            '%': (TokenType.PERCENT, '%'),
            '^': (TokenType.CARET, '^'),
            '(': (TokenType.LPAREN, '('),
            ')': (TokenType.RPAREN, ')'),
            '[': (TokenType.LBRACKET, '['),
            ']': (TokenType.RBRACKET, ']'),
            '<': (TokenType.LT, '<'),
            '>': (TokenType.GT, '>'),
            '=': (TokenType.EQUALS, '='),
        }
    
    def tokenize(self) -> List[Token]:
        """执行分词"""
        while not self.at_end():
            self.scan_token()
        
        # 添加EOF
        self.tokens.append(Token(TokenType.EOF, None, self.line, self.column))
        return self.tokens
    
    def scan_token(self):
        """扫描下一个Token"""
        # 跳过空白符
        if self.peek().isspace():
            self.advance()
            return
        
        # 1. 结构锚点优先
        if self.match('$('):
            self.scan_math_expr()
            return
        
        if self.match('{{'):
            self.scan_python_block()
            return
        
        # 2. 字符串
        if self.peek() == '"':
            self.scan_string()
            return
        
        # 3. 注释处理
        if self.peek() == '#':
            self.scan_hash_comment()
            return
        
        if self.match('--'):
            # 检查是否是注释
            if self.at_end() or self.peek().isspace():
                self.scan_comment()
                return
            else:
                # 不是注释，回退
                self.pos -= 2
                self.column -= 2
        
        # 4. 数字
        if self.peek().isdigit() or self.peek() == '.':
            self.scan_number()
            return

        # 5. 标点符号
        char = self.peek()
        if char in self.punctuation_map:
            self.advance()
            self.add_token(self.punctuation_map[char], char)
            return

        # 6. 内联数学运算符（包含<=, >=, ==, !=等）
        if char in '+-*/%^()[]<>!=':
            self.scan_math_operator_optimized()
            return

        # 7. 中文关键字/动词/标识符
        if self.is_chinese_char(char):
            self.scan_chinese_optimized()
            return

        # 8. 英文标识符
        if char.isalpha() or char == '_':
            self.scan_identifier()
            return

        # 无法识别的字符
        raise SyntaxError(f"无法识别的字符: {char} (行{self.line}, 列{self.column})")
    
    def scan_chinese_optimized(self):
        """优化版中文扫描：使用Trie树进行最长匹配"""
        # 使用Trie树查找最长匹配
        match = self.trie.find_longest_match(self.source, self.pos)
        
        if match:
            length, token_type_str, value = match
            
            # 只处理VERB、KEYWORD、ADVERB
            if token_type_str == 'VERB':
                token_type = TokenType.VERB
            elif token_type_str == 'KEYWORD':
                token_type = TokenType.KEYWORD
            elif token_type_str == 'ADVERB':
                token_type = TokenType.ADVERB
            else:
                # 其他情况不视为匹配，继续处理为标识符
                match = None
        
        if match:
            # 前进匹配的长度
            for _ in range(length):
                self.advance()
            
            self.add_token(token_type, value)
            return
            
            # 前进匹配的长度
            for _ in range(length):
                self.advance()
            
            self.add_token(token_type, value)
            return
        
        # 如果没有匹配的关键词，处理为普通标识符
        start = self.pos
        self.advance()  # 至少前进一个字符
        
        # 继续扫描中文字符，直到遇到以下情况：
        # 1. 遇到非中文字符
        # 2. 下一个位置匹配到多字符关键词/动词
        while not self.at_end() and self.is_chinese_char(self.peek()):
            # 检查后续字符是否形成完整的动词/关键字
            found_multi = False
            for length in [4, 3, 2]:
                if self.pos + length <= len(self.source):
                    text = self.source[self.pos:self.pos+length]
                    match = self.trie.find_longest_match(self.source, self.pos)
                    if match and match[0] >= 2:  # 只考虑2个字符以上的匹配
                        found_multi = True
                        break
            if found_multi:
                break
            self.advance()
        
        text = self.source[start:self.pos]
        
        # 检查是否为中文数字（必须整个token都是中文数字）
        if self.is_chinese_number(text):
            value = self.parse_chinese_number(text)
            self.add_token(TokenType.NUM, value)
        else:
            self.add_token(TokenType.IDENT, text)
    
    def scan_math_operator_optimized(self):
        """优化版数学运算符扫描"""
        char = self.peek()
        
        # 处理双字符运算符
        if char == '<' and self.peek_next() == '=':
            self.advance()  # <
            self.advance()  # =
            self.add_token(TokenType.LE, '<=')
        elif char == '>' and self.peek_next() == '=':
            self.advance()  # >
            self.advance()  # =
            self.add_token(TokenType.GE, '>=')
        elif char == '=' and self.peek_next() == '=':
            self.advance()  # =
            self.advance()  # =
            self.add_token(TokenType.EQ, '==')
        elif char == '!' and self.peek_next() == '=':
            self.advance()  # !
            self.advance()  # =
            self.add_token(TokenType.NE, '!=')
        elif char == '*' and self.peek_next() == '*':
            self.advance()  # *
            self.advance()  # *
            self.add_token(TokenType.STAR, '**')
        else:
            # 单字符运算符
            if char in self.math_operator_map:
                token_type, value = self.math_operator_map[char]
                self.advance()
                self.add_token(token_type, value)
            else:
                raise SyntaxError(f"无法识别的运算符: {char} (行{self.line}, 列{self.column})")
    
    def scan_math_expr(self):
        """扫描数学表达式 $(...)"""
        # match已经前进了$和(，所以当前位置是表达式的开始
        expr_start = self.pos
        
        depth = 1
        while not self.at_end() and depth > 0:
            if self.peek() == '(':
                depth += 1
            elif self.peek() == ')':
                depth -= 1
            self.advance()
        
        # 提取表达式内容（不包括最后的)）
        expr = self.source[expr_start:self.pos-1]
        self.add_token(TokenType.MATH, expr)
    
    def scan_python_block(self):
        """扫描Python代码块 {{...}}"""
        # match已经前进了两个{，所以当前位置是代码的开始
        start = self.pos

        depth = 1
        while not self.at_end() and depth > 0:
            if self.match('{{'):
                depth += 1
            elif self.match('}}'):
                depth -= 1
            else:
                self.advance()

        # 提取代码内容（不包括最后的}}）
        code = self.source[start:self.pos-2]
        self.add_token(TokenType.PYTHON, code)
    
    def scan_string(self):
        """扫描字符串"""
        self.advance()  # "
        start = self.pos
        
        while not self.at_end() and self.peek() != '"':
            if self.peek() == '\n':
                self.line += 1
                self.column = 0
            self.advance()
        
        if self.at_end():
            raise SyntaxError(f"未闭合的字符串 (行{self.line})")
        
        value = self.source[start:self.pos]
        self.advance()  # "
        self.add_token(TokenType.STR, value)
    
    def scan_comment(self):
        """扫描注释 -- ..."""
        while not self.at_end() and self.peek() != '\n':
            self.advance()

    def scan_hash_comment(self):
        """扫描 # 注释"""
        self.advance()  # 消费 #
        while not self.at_end() and self.peek() != '\n':
            self.advance()

    def scan_number(self):
        """扫描数字"""
        start = self.pos
        
        # 整数部分
        while not self.at_end() and self.peek().isdigit():
            self.advance()
        
        # 小数部分
        if not self.at_end() and self.peek() == '.':
            self.advance()
            while not self.at_end() and self.peek().isdigit():
                self.advance()
        
        value = self.source[start:self.pos]
        if '.' in value:
            self.add_token(TokenType.NUM, float(value))
        else:
            self.add_token(TokenType.NUM, int(value))
    
    def scan_identifier(self):
        """扫描英文标识符"""
        start = self.pos
        
        # 只扫描ASCII字母、数字和下划线
        while not self.at_end():
            char = self.peek()
            if char.isascii() and (char.isalnum() or char == '_'):
                self.advance()
            else:
                break
        
        text = self.source[start:self.pos]
        self.add_token(TokenType.IDENT, text)
    
    def is_chinese_char(self, char: str) -> bool:
        """判断是否为中文字符"""
        return '\u4e00' <= char <= '\u9fff'
    
    def is_chinese_number(self, text: str) -> bool:
        """判断是否为中文数字"""
        # 简单判断：所有字符都是中文数字
        from .pre_tokenizer import PreTokenizer
        chinese_numbers = PreTokenizer.CHINESE_NUMBERS
        return all(char in chinese_numbers for char in text)
    
    def parse_chinese_number(self, text: str) -> int:
        """解析中文数字"""
        from .pre_tokenizer import PreTokenizer
        chinese_numbers = PreTokenizer.CHINESE_NUMBERS
        
        # 简单实现，只处理基本数字
        if text in chinese_numbers:
            return chinese_numbers[text]
        
        # 复杂数字需要更复杂的解析
        # 这里简化处理
        result = 0
        for char in text:
            if char in chinese_numbers:
                result += chinese_numbers[char]
        return result
    
    def peek(self) -> str:
        """查看当前字符"""
        if self.at_end():
            return '\0'
        return self.source[self.pos]
    
    def peek_next(self) -> str:
        """查看下一个字符"""
        if self.pos + 1 >= len(self.source):
            return '\0'
        return self.source[self.pos + 1]
    
    def advance(self) -> str:
        """前进一个字符"""
        char = self.source[self.pos]
        self.pos += 1
        
        if char == '\n':
            self.line += 1
            self.column = 0
        else:
            self.column += 1
        
        return char
    
    def match(self, expected: str) -> bool:
        """匹配字符串"""
        if self.pos + len(expected) > len(self.source):
            return False
        
        actual = self.source[self.pos:self.pos+len(expected)]
        if actual == expected:
            for _ in range(len(expected)):
                self.advance()
            return True
        
        return False
    
    def at_end(self) -> bool:
        """是否到达末尾"""
        return self.pos >= len(self.source)
    
    def add_token(self, type: TokenType, value: Any):
        """添加Token"""
        self.tokens.append(Token(type, value, self.line, self.column))


def tokenize_optimized(source: str) -> List[Token]:
    """优化版分词函数"""
    tokenizer = OptimizedPreTokenizer(source)
    return tokenizer.tokenize()


if __name__ == '__main__':
    # 测试代码
    test_cases = [
        "定义x=5相加3。",
        "列表1 2 3，映射相乘2。",
        "如果x大于y那么x否则y。",
        "张三=18。",
        "定义阶乘=函数n如果n等于1那么1否则n相乘阶乘n相减1。",
    ]
    
    for source in test_cases:
        print(f"\n源码: {source}")
        tokens = tokenize_optimized(source)
        for token in tokens:
            print(f"  {token}")


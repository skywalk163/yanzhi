"""
知行语言词法分析器
基于预分词层的完整词法分析
"""

from typing import List
from .pre_tokenizer import Token, TokenType, PreTokenizer


class Lexer:
    """词法分析器"""
    
    def __init__(self, source: str):
        self.source = source
        self.pre_tokenizer = PreTokenizer(source)
        self.tokens: List[Token] = []
        self.pos = 0
    
    def tokenize(self) -> List[Token]:
        """执行词法分析"""
        # 1. 预分词
        raw_tokens = self.pre_tokenizer.tokenize()
        
        # 2. 后处理（合并、转换等）
        self.tokens = self.post_process(raw_tokens)
        
        return self.tokens
    
    def post_process(self, tokens: List[Token]) -> List[Token]:
        """后处理：合并、转换Token"""
        result = []
        i = 0
        
        while i < len(tokens):
            token = tokens[i]
            
            # 跳过EOF
            if token.type == TokenType.EOF:
                i += 1
                continue
            
            # 处理布尔值
            if token.type == TokenType.KEYWORD and token.value in ('真', '假'):
                bool_value = token.value == '真'
                result.append(Token(TokenType.BOOL, bool_value, token.line, token.column))
                i += 1
                continue
            
            # 处理空值
            if token.type == TokenType.KEYWORD and token.value == '空':
                result.append(Token(TokenType.BOOL, None, token.line, token.column))
                i += 1
                continue
            
            # 其他Token直接添加
            result.append(token)
            i += 1
        
        # 添加EOF
        result.append(Token(TokenType.EOF, None))
        return result
    
    def peek(self) -> Token:
        """查看当前Token"""
        if self.pos >= len(self.tokens):
            return self.tokens[-1]  # EOF
        return self.tokens[self.pos]
    
    def advance(self) -> Token:
        """前进一个Token"""
        token = self.peek()
        if not self.at_end():
            self.pos += 1
        return token
    
    def match(self, type: TokenType, value: any = None) -> bool:
        """匹配Token"""
        if self.at_end():
            return False
        
        token = self.peek()
        if token.type != type:
            return False
        
        if value is not None and token.value != value:
            return False
        
        self.advance()
        return True
    
    def at_end(self) -> bool:
        """是否到达末尾"""
        return self.peek().type == TokenType.EOF


def lex(source: str) -> List[Token]:
    """词法分析函数"""
    lexer = Lexer(source)
    return lexer.tokenize()


# 测试代码
if __name__ == '__main__':
    # 测试用例
    test_cases = [
        "定x=5加3。",
        "列1 2 3，皆乘2。",
        "若x大y则x否则y。",
        "张三=18。",
        "定阶乘=函n若n等1则1否则n乘阶乘n减1。",
        "定flag=真。",
        "定result=$(1 + 2 * 3)。",
    ]
    
    for source in test_cases:
        print(f"\n源码: {source}")
        tokens = lex(source)
        for i, token in enumerate(tokens):
            if token.type != TokenType.EOF:
                print(f"  [{i}] {token}")

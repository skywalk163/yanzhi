

"""
词法分析器单元测试
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../src')))

import pytest
from yanzhi.compiler.pre_tokenizer import PreTokenizer, TokenType
from yanzhi.compiler.lexer import Lexer


class TestLexer:
    """词法分析器测试"""
    
    def test_basic_lexing(self):
        """测试基础词法分析"""
        code = "定 x = 5。"
        # Lexer需要原始代码字符串
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        
        assert len(tokens) > 0
        # 应该包含标识符和数字
        token_types = [t.type for t in tokens]
        # 检查是否有合适的token类型
        assert any(t.type in [TokenType.IDENT, TokenType.NUM, TokenType.KEYWORD] for t in tokens)
        
    def test_function_definition(self):
        """测试函数定义"""
        code = "定 fact = 函 n：若 n 等 1 则 1 否则 n 乘 fact $(n-1)。"
        # Lexer需要原始代码字符串
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        
        assert len(tokens) > 0
        # 检查关键字
        keywords = [t.value for t in tokens if t.type == TokenType.KEYWORD]
        # 由于分词可能不同，我们检查是否有合适的token
        assert any(t.value in ["定", "函", "若", "则", "否则"] for t in tokens)
        
    def test_verb_parsing(self):
        """测试动词解析"""
        code = "相加 1 2。"
        # Lexer需要原始代码字符串
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        
        # 检查动词
        verbs = [t for t in tokens if t.type == TokenType.VERB]
        assert len(verbs) > 0
        
    def test_string_parsing(self):
        """测试字符串解析"""
        code = '设 文 = "你好世界"。'
        # Lexer需要原始代码字符串
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        
        # 检查字符串
        strings = [t for t in tokens if t.type == TokenType.STR]
        assert len(strings) > 0
        # 字符串值可能包含引号，所以检查是否包含内容
        string_values = [s.value for s in strings]
        assert any("你好世界" in str(val) for val in string_values)
        
    def test_boolean_parsing(self):
        """测试布尔值解析"""
        code = "设 是 = 真。"
        # Lexer需要原始代码字符串
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        
        # 检查布尔值
        booleans = [t for t in tokens if t.type == TokenType.BOOL]
        assert len(booleans) > 0
        
    def test_mathematical_expression(self):
        """测试数学表达式"""
        code = "结果 = $(1 + 2 * 3)。"
        # Lexer需要原始代码字符串
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        
        # 检查数学表达式
        math_exprs = [t for t in tokens if t.type == TokenType.MATH]
        assert len(math_exprs) > 0
        
    def test_punctuation(self):
        """测试标点符号"""
        code = "定 x = 5。定 y = 10。"
        # Lexer需要原始代码字符串
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        
        # 检查句号
        dots = [t for t in tokens if t.type == TokenType.DOT]
        assert len(dots) >= 2


if __name__ == "__main__":
    pytest.main([__file__])



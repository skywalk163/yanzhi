
"""
预分词器单元测试
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../src')))

import pytest
from yanzhi.compiler.pre_tokenizer import PreTokenizer, TokenType


class TestPreTokenizer:
    """预分词器测试"""
    
    def test_basic_tokenization(self):
        """测试基础分词"""
        code = "定 x = 5。"
        tokenizer = PreTokenizer(code)
        tokens = tokenizer.tokenize()
        
        assert len(tokens) > 0
        # 检查是否包含关键字
        token_values = [t.value for t in tokens]
        assert "定" in token_values
        
    def test_number_token(self):
        """测试数字分词"""
        code = "设 数 = 123.45。"
        tokenizer = PreTokenizer(code)
        tokens = tokenizer.tokenize()
        
        # 检查是否有数字token
        number_tokens = [t for t in tokens if t.type == TokenType.NUM]
        assert len(number_tokens) > 0
        
    def test_verb_recognition(self):
        """测试动词识别"""
        code = "相加 1 2。"
        tokenizer = PreTokenizer(code)
        tokens = tokenizer.tokenize()
        
        # 检查动词token
        verb_tokens = [t for t in tokens if t.type == TokenType.VERB]
        assert len(verb_tokens) > 0
        assert verb_tokens[0].value == "相加"
        
    def test_string_literal(self):
        """测试字符串字面量"""
        code = '设 文 = "你好世界"。'
        tokenizer = PreTokenizer(code)
        tokens = tokenizer.tokenize()
        
        # 检查字符串token
        str_tokens = [t for t in tokens if t.type == TokenType.STR]
        assert len(str_tokens) > 0
        
    def test_mathematical_expression(self):
        """测试数学表达式"""
        code = "结果 = $(1 + 2 * 3)。"
        tokenizer = PreTokenizer(code)
        tokens = tokenizer.tokenize()
        
        # $(...) 应该被识别为 MATH token
        math_tokens = [t for t in tokens if t.type == TokenType.MATH]
        assert len(math_tokens) > 0
        # 检查MATH token的值包含表达式
        math_value = math_tokens[0].value
        assert "1 + 2 * 3" in math_value
        
    def test_empty_code(self):
        """测试空代码"""
        code = ""
        tokenizer = PreTokenizer(code)
        tokens = tokenizer.tokenize()
        # 空代码应该只返回EOF token
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.EOF
        
    def test_whitespace_handling(self):
        """测试空格处理"""
        code = "定 x = 5 。 定 y = 10 。"
        tokenizer = PreTokenizer(code)
        tokens = tokenizer.tokenize()
        
        # 应该正确处理带空格的代码
        assert len(tokens) > 0


if __name__ == "__main__":
    pytest.main([__file__])


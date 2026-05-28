"""
预分词器单元测试 — 验证 Trie 树优化 + 双字关键字分词
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../src')))

import pytest
from yanzhi.compiler.pre_tokenizer import PreTokenizer, TokenType, tokenize


class TestPreTokenizer:
    """预分词器测试"""

    def test_keyword_define(self):
        """测试 定义 关键字"""
        tokens = tokenize("定义 x = 5。")
        values = [t.value for t in tokens]
        assert "定义" in values
        assert tokens[0].type == TokenType.KEYWORD
        assert tokens[0].value == "定义"

    def test_keyword_function(self):
        """测试 函数 关键字"""
        tokens = tokenize("定义 f = 函数 n：n 相乘 n。。")
        values = [t.value for t in tokens]
        assert "函数" in values
        # 找到 函数 关键字的位置
        func_idx = values.index("函数")
        assert tokens[func_idx].type == TokenType.KEYWORD

    def test_keyword_if_else(self):
        """测试 如果/那么/否则 关键字"""
        tokens = tokenize("如果 x 大于 5 那么 x 否则 0。")
        values = [t.value for t in tokens]
        assert "如果" in values and "那么" in values and "否则" in values
        assert tokens[0].type == TokenType.KEYWORD

    def test_verb_arithmetic(self):
        """测试双字算术动词"""
        tokens = tokenize("相加 5 3。")
        verbs = [t for t in tokens if t.type == TokenType.VERB]
        assert len(verbs) > 0
        assert verbs[0].value == "相加"

        tokens2 = tokenize("相乘 2 4。")
        verbs2 = [t for t in tokens2 if t.type == TokenType.VERB]
        assert verbs2[0].value == "相乘"

    def test_verb_list(self):
        """测试列表动词"""
        tokens = tokenize("列表 1 2 3。")
        verbs = [t for t in tokens if t.type == TokenType.VERB]
        assert verbs[0].value == "列表"

    def test_verb_print(self):
        """测试打印动词"""
        tokens = tokenize('打印 "hello"。')
        verbs = [t for t in tokens if t.type == TokenType.VERB]
        assert verbs[0].value == "打印"

    def test_adverb_map_filter(self):
        """测试副词：映射/过滤"""
        tokens = tokenize("映射相乘2 列表 1 2 3。")
        adverbs = [t for t in tokens if t.type == TokenType.ADVERB]
        assert any(a.value == "映射" for a in adverbs)

        tokens2 = tokenize("过滤大于5 列表 1 2 3。")
        adverbs2 = [t for t in tokens2 if t.type == TokenType.ADVERB]
        assert any(a.value == "过滤" for a in adverbs2)

    def test_identifier_multichar(self):
        """测试多字符标识符（阶乘不应被分割）"""
        tokens = tokenize("阶乘 5。")
        idents = [t for t in tokens if t.type == TokenType.IDENT]
        assert len(idents) > 0
        # 阶乘 应作为整体标识符，不被拆分
        assert idents[0].value == "阶乘"

    def test_identifier_within_keywords(self):
        """测试关键字间的标识符"""
        tokens = tokenize("定义 冒泡排序 = 函数 lst：。")
        values = [t.value for t in tokens]
        assert "冒泡排序" in values
        assert "lst" in values

    def test_chinese_number(self):
        """测试中文数字"""
        tokens = tokenize("一百二十三。")
        nums = [t for t in tokens if t.type == TokenType.NUM]
        assert len(nums) > 0

    def test_string_literal(self):
        """测试字符串"""
        tokens = tokenize('打印 "你好世界"。')
        strs = [t for t in tokens if t.type == TokenType.STR]
        assert len(strs) > 0

    def test_math_expression(self):
        """测试内联数学表达式 $(...)"""
        tokens = tokenize("定义 r = $(1 + 2 * 3)。")
        math_tokens = [t for t in tokens if t.type == TokenType.MATH]
        assert len(math_tokens) > 0
        assert "1 + 2 * 3" in math_tokens[0].value

    def test_python_block(self):
        """测试 Python 代码块 {{...}}"""
        tokens = tokenize("{{ print(1) }}")
        py_tokens = [t for t in tokens if t.type == TokenType.PYTHON]
        assert len(py_tokens) > 0

    def test_pipeline_with_adverb(self):
        """测试管道中的副词"""
        code = "列表 1 2 3，映射相乘2。"
        tokens = tokenize(code)
        adverbs = [t for t in tokens if t.type == TokenType.ADVERB]
        verbs = [t for t in tokens if t.type == TokenType.VERB]
        assert any(a.value == "映射" for a in adverbs)
        assert any(v.value == "相乘" for v in verbs)
        # 确认逗号正常
        commas = [t for t in tokens if t.type == TokenType.COMMA]
        assert len(commas) == 1

    def test_empty_source(self):
        """测试空源码"""
        tokens = tokenize("")
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.EOF

    def test_whitespace_handling(self):
        """测试空格处理"""
        code = "定义 x = 5 。 定义 y = 10 。"
        tokens = tokenize(code)
        assert len(tokens) > 0

    def test_trie_caching(self):
        """测试 Trie 实例是否被正确缓存（模块级单例）"""
        from yanzhi.compiler.trie import get_keyword_trie
        trie1 = get_keyword_trie()
        trie2 = get_keyword_trie()
        assert trie1 is trie2  # 应是同一个实例

    def test_trie_contains_all_keywords(self):
        """测试 Trie 是否包含所有关键字/动词/副词"""
        from yanzhi.compiler.trie import get_keyword_trie
        trie = get_keyword_trie()
        for kw in PreTokenizer.KEYWORDS:
            assert trie.search(kw) is not None, f"Trie 缺少关键字: {kw}"
        for vb in PreTokenizer.VERBS:
            assert trie.search(vb) is not None, f"Trie 缺少动词: {vb}"
        for av in PreTokenizer.ADVERBS:
            assert trie.search(av) is not None, f"Trie 缺少副词: {av}"

    def test_trie_no_false_match(self):
        """测试 Trie 不会误匹配不存在的词"""
        from yanzhi.compiler.trie import get_keyword_trie
        trie = get_keyword_trie()
        assert trie.search("不存在") is None
        assert trie.search("阶乘") is None

    def test_trie_longest_match(self):
        """测试 Trie 最长匹配：'大于等于' 应匹配完整词而非 '大于'"""
        from yanzhi.compiler.trie import get_keyword_trie
        trie = get_keyword_trie()
        match = trie.find_longest_match("大于等于5", 0)
        assert match is not None
        length, token_type, value = match
        assert value == "大于等于"
        assert length == 4  # 4个字符


if __name__ == "__main__":
    pytest.main([__file__])

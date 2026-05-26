
# -*- coding: utf-8 -*-
"""
Trie树（前缀树）用于加速中文分词中的关键词匹配
"""

from typing import Dict, Any, Optional


class TrieNode:
    """Trie树节点"""
    
    __slots__ = ('children', 'is_end', 'token_type', 'value')
    
    def __init__(self):
        self.children: Dict[str, 'TrieNode'] = {}
        self.is_end: bool = False
        self.token_type: Optional[str] = None  # 'VERB', 'KEYWORD', 'ADVERB', 'SURNAME'
        self.value: Any = None


class Trie:
    """Trie树"""
    
    def __init__(self):
        self.root = TrieNode()
        self._word_count = 0
    
    def insert(self, word: str, token_type: str, value: Any = None) -> None:
        """插入一个词"""
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        
        if not node.is_end:
            self._word_count += 1
        node.is_end = True
        node.token_type = token_type
        node.value = value
    
    def search(self, word: str) -> Optional[tuple]:
        """精确查找一个词"""
        node = self._find_node(word)
        if node and node.is_end:
            return (node.token_type, node.value)
        return None
    
    def starts_with(self, prefix: str) -> bool:
        """检查是否有以prefix为前缀的词"""
        node = self._find_node(prefix)
        return node is not None
    
    def find_longest_match(self, text: str, start_pos: int = 0) -> Optional[tuple]:
        """
        从给定位置开始查找最长的匹配词
        
        返回: (匹配长度, token_type, value) 或 None
        """
        node = self.root
        max_match = None
        
        for i in range(start_pos, len(text)):
            char = text[i]
            if char not in node.children:
                break
            node = node.children[char]
            if node.is_end:
                # 记录当前位置的匹配
                match_length = i - start_pos + 1
                max_match = (match_length, node.token_type, node.value)
        
        return max_match
    
    def _find_node(self, word: str) -> Optional[TrieNode]:
        """查找指定词对应的节点"""
        node = self.root
        for char in word:
            if char not in node.children:
                return None
            node = node.children[char]
        return node
    
    @property
    def word_count(self) -> int:
        """返回树中的词数"""
        return self._word_count
    
    def __contains__(self, word: str) -> bool:
        """检查词是否在Trie中"""
        return self.search(word) is not None
    
    def __len__(self) -> int:
        return self._word_count


def build_keyword_trie() -> Trie:
    """构建包含所有关键词、动词、副词、姓氏的Trie树"""
    from .pre_tokenizer import PreTokenizer
    
    trie = Trie()
    
    # 添加关键词
    for keyword in PreTokenizer.KEYWORDS:
        trie.insert(keyword, 'KEYWORD', keyword)
    
    # 添加动词
    for verb in PreTokenizer.VERBS:
        trie.insert(verb, 'VERB', verb)
    
    # 添加副词
    for adverb in PreTokenizer.ADVERBS:
        trie.insert(adverb, 'ADVERB', adverb)
    
    # 注意：姓氏不添加到Trie中，原始算法中不检查SURNAMES集合
    # SURNAMES集合在代码中定义但未在实际分词中使用
    
    # 注意：中文数字不添加到Trie中，因为需要特殊处理
    # 中文数字只有在整个token都是中文数字时才应识别
    # 例如："一"是数字，"一百"是数字，但"张三"中的"三"不是数字
    
    return trie


# 全局Trie实例
_KEYWORD_TRIE = None


def get_keyword_trie() -> Trie:
    """获取或创建全局Trie实例"""
    global _KEYWORD_TRIE
    if _KEYWORD_TRIE is None:
        _KEYWORD_TRIE = build_keyword_trie()
    return _KEYWORD_TRIE


if __name__ == '__main__':
    # 测试代码
    trie = get_keyword_trie()
    
    test_words = ["定义", "相加", "映射", "赵", "一"]
    for word in test_words:
        result = trie.search(word)
        if result:
            token_type, value = result
            print(f"'{word}': {token_type} = {value}")
        else:
            print(f"'{word}': 未找到")
    
    # 测试最长匹配
    text = "定义变量名称"
    match = trie.find_longest_match(text, 0)
    if match:
        length, token_type, value = match
        print(f"最长匹配: '{text[:length]}' ({token_type})")
    
    # 测试前缀
    print(f"'定' 前缀存在: {trie.starts_with('定')}")
    print(f"'定义' 前缀存在: {trie.starts_with('定义')}")

"""
知行语言标准库 - 数据结构模块
提供栈、队列、树等数据结构
"""

from typing import Any, List, Optional


# 1. 栈
class Stack:
    """栈数据结构"""
    
    def __init__(self):
        self.items: List[Any] = []
    
    def push(self, item: Any):
        """入栈"""
        self.items.append(item)
    
    def pop(self) -> Optional[Any]:
        """出栈"""
        if self.is_empty():
            return None
        return self.items.pop()
    
    def peek(self) -> Optional[Any]:
        """查看栈顶"""
        if self.is_empty():
            return None
        return self.items[-1]
    
    def is_empty(self) -> bool:
        """是否为空"""
        return len(self.items) == 0
    
    def size(self) -> int:
        """大小"""
        return len(self.items)
    
    def clear(self):
        """清空"""
        self.items.clear()


# 2. 队列
class Queue:
    """队列数据结构"""
    
    def __init__(self):
        self.items: List[Any] = []
    
    def enqueue(self, item: Any):
        """入队"""
        self.items.append(item)
    
    def dequeue(self) -> Optional[Any]:
        """出队"""
        if self.is_empty():
            return None
        return self.items.pop(0)
    
    def peek(self) -> Optional[Any]:
        """查看队首"""
        if self.is_empty():
            return None
        return self.items[0]
    
    def is_empty(self) -> bool:
        """是否为空"""
        return len(self.items) == 0
    
    def size(self) -> int:
        """大小"""
        return len(self.items)


# 3. 双端队列
class Deque:
    """双端队列"""
    
    def __init__(self):
        self.items: List[Any] = []
    
    def add_front(self, item: Any):
        """前端添加"""
        self.items.insert(0, item)
    
    def add_rear(self, item: Any):
        """后端添加"""
        self.items.append(item)
    
    def remove_front(self) -> Optional[Any]:
        """前端移除"""
        if self.is_empty():
            return None
        return self.items.pop(0)
    
    def remove_rear(self) -> Optional[Any]:
        """后端移除"""
        if self.is_empty():
            return None
        return self.items.pop()
    
    def is_empty(self) -> bool:
        """是否为空"""
        return len(self.items) == 0
    
    def size(self) -> int:
        """大小"""
        return len(self.items)


# 4. 链表节点
class ListNode:
    """链表节点"""
    
    def __init__(self, value: Any):
        self.value = value
        self.next: Optional['ListNode'] = None


# 5. 链表
class LinkedList:
    """链表"""
    
    def __init__(self):
        self.head: Optional[ListNode] = None
        self._size = 0
    
    def append(self, value: Any):
        """追加"""
        new_node = ListNode(value)
        if self.head is None:
            self.head = new_node
        else:
            current = self.head
            while current.next:
                current = current.next
            current.next = new_node
        self._size += 1
    
    def prepend(self, value: Any):
        """前插"""
        new_node = ListNode(value)
        new_node.next = self.head
        self.head = new_node
        self._size += 1
    
    def delete(self, value: Any) -> bool:
        """删除"""
        if self.head is None:
            return False
        
        if self.head.value == value:
            self.head = self.head.next
            self._size -= 1
            return True
        
        current = self.head
        while current.next:
            if current.next.value == value:
                current.next = current.next.next
                self._size -= 1
                return True
            current = current.next
        
        return False
    
    def find(self, value: Any) -> Optional[ListNode]:
        """查找"""
        current = self.head
        while current:
            if current.value == value:
                return current
            current = current.next
        return None
    
    def size(self) -> int:
        """大小"""
        return self._size
    
    def to_list(self) -> List[Any]:
        """转为列表"""
        result = []
        current = self.head
        while current:
            result.append(current.value)
            current = current.next
        return result


# 6. 二叉树节点
class TreeNode:
    """二叉树节点"""
    
    def __init__(self, value: Any):
        self.value = value
        self.left: Optional['TreeNode'] = None
        self.right: Optional['TreeNode'] = None


# 7. 二叉搜索树
class BinarySearchTree:
    """二叉搜索树"""
    
    def __init__(self):
        self.root: Optional[TreeNode] = None
    
    def insert(self, value: Any):
        """插入"""
        if self.root is None:
            self.root = TreeNode(value)
        else:
            self._insert_recursive(self.root, value)
    
    def _insert_recursive(self, node: TreeNode, value: Any):
        if value < node.value:
            if node.left is None:
                node.left = TreeNode(value)
            else:
                self._insert_recursive(node.left, value)
        else:
            if node.right is None:
                node.right = TreeNode(value)
            else:
                self._insert_recursive(node.right, value)
    
    def search(self, value: Any) -> bool:
        """搜索"""
        return self._search_recursive(self.root, value)
    
    def _search_recursive(self, node: Optional[TreeNode], value: Any) -> bool:
        if node is None:
            return False
        if value == node.value:
            return True
        if value < node.value:
            return self._search_recursive(node.left, value)
        return self._search_recursive(node.right, value)
    
    def inorder(self) -> List[Any]:
        """中序遍历"""
        result = []
        self._inorder_recursive(self.root, result)
        return result
    
    def _inorder_recursive(self, node: Optional[TreeNode], result: List):
        if node:
            self._inorder_recursive(node.left, result)
            result.append(node.value)
            self._inorder_recursive(node.right, result)


# 8. 字典树（Trie）
class TrieNode:
    """字典树节点"""
    
    def __init__(self):
        self.children: dict = {}
        self.is_end = False


class Trie:
    """字典树"""
    
    def __init__(self):
        self.root = TrieNode()
    
    def insert(self, word: str):
        """插入单词"""
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end = True
    
    def search(self, word: str) -> bool:
        """搜索单词"""
        node = self.root
        for char in word:
            if char not in node.children:
                return False
            node = node.children[char]
        return node.is_end
    
    def starts_with(self, prefix: str) -> bool:
        """检查前缀"""
        node = self.root
        for char in prefix:
            if char not in node.children:
                return False
            node = node.children[char]
        return True

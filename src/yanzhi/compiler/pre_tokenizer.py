"""
知行语言预分词层
实现无空格分词的核心算法
"""

from typing import List, Tuple, Optional, Dict, Any
from enum import Enum, auto
from ..yan.action_vocab import ACTION_VOCAB


class TokenType(Enum):
    """Token类型定义"""
    # 字面量
    NUM = auto()        # 数字
    STR = auto()        # 字符串
    BOOL = auto()       # 布尔值
    
    # 标识符和关键字
    KEYWORD = auto()    # 关键字
    VERB = auto()       # 动词
    ADVERB = auto()     # 副词
    IDENT = auto()      # 标识符

    # 结构
    DOT = auto()        # 。
    COMMA = auto()      # ，
    COLON = auto()      # ：
    EQUALS = auto()     # =
    QUOTE = auto()      # '

    # 内联数学运算符
    PLUS = auto()       # +
    MINUS = auto()      # -
    STAR = auto()       # *
    SLASH = auto()      # /
    PERCENT = auto()    # %
    CARET = auto()      # ^
    LPAREN = auto()     # (
    RPAREN = auto()     # )
    LBRACKET = auto()   # [
    RBRACKET = auto()   # ]
    CLBRACKET = auto()  # 【
    CRBRACKET = auto()  # 】
    LT = auto()         # <
    GT = auto()         # >
    LE = auto()         # <=
    GE = auto()         # >=
    EQ = auto()         # ==
    NE = auto()         # !=
    
    # 特殊
    MATH = auto()       # $(...)
    PYTHON = auto()     # {{...}}
    
    # 结束
    EOF = auto()


class Token:
    """Token类"""
    def __init__(self, type: TokenType, value: any, line: int = 0, column: int = 0):
        self.type = type
        self.value = value
        self.line = line
        self.column = column
    
    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r})"


class PreTokenizer:
    """预分词器：实现无空格分词"""
    
    # 关键字集合
    KEYWORDS = {
        '定义', '赋值', '函数', '如果', '那么', '否则', '遍历', '循环当', '导入', '导出', '于',
        '真', '假', '空', '尝试', '试', '捕获', '结束', '完毕',
        # 友好语法
        '就', '不然', '是', '对于', '每次', '算', '从', '到',
        # 言律句式
        '每隔', '要是',
        # 模块系统
        '导入', '导出', '模块', '从', '为',
        # 结构体
        '结构', '方法',
        # 异常
        '抛出',
        # 返回
        '返回',
        # 宏
        '宏',
        # 注释
        '注释', '注',
        # DSL 工厂
        '启用', '策略',
    }
    
    # 动词集合（运算符）
    VERBS = {
        # 函数调用
        '使用',
        # 算术
        '相加', '相减', '相乘', '相除', '取余', '乘方', '取负', '绝对',
        # 比较
        '大于', '小于', '等于', '不等', '大于等于', '小于等于',
        # 逻辑
        '并且', '或者', '非也',
        # 列表
        '列表', '首个', '剩余', '索引', '长度', '添加', '连接', '包含', '删除', '空值', '范围',
        # I/O
        '打印', '读取', '写入',
        # 输入函数
        '输入', '读入', '读行', '读字符', '读键', '读整数', '读小数', '读确认', '确认',
        # 异常
        '抛',
        # 同像性
        '行',
        # 谓词
        '是数', '是文', '是列', '是空', '是零', '是正', '是负', '是布尔',
        '全真', '任真', '全假',
        # 序列操作
        '反转', '去重', '位置', '子列', '拉链', '交集', '并集', '差集',
        # 数学函数
        '四舍五入', '最小', '最大', '求和', '求积', '展平', '枚举', '分块', '交错',
        # 字符串操作
        '连接', '子串', '小写', '大写', '查找', '长度', '截取',
        # 动词白名单（高层语义 → 内核动词映射）
        *ACTION_VOCAB.keys(),
    }
    
    # 副词集合（高阶函数）
    ADVERBS = {'映射', '过滤', '归约', '合并'}
    
    # 百家姓（部分）
    SURNAMES = {
        '赵', '钱', '孙', '李', '周', '吴', '郑', '王', '冯', '陈',
        '褚', '卫', '蒋', '沈', '韩', '杨', '朱', '秦', '尤', '许',
        '何', '吕', '施', '张', '孔', '曹', '严', '华', '金', '魏',
        '陶', '姜', '戚', '谢', '邹', '喻', '柏', '水', '窦', '章',
        '云', '苏', '潘', '葛', '奚', '范', '彭', '郎', '鲁', '韦',
        '昌', '马', '苗', '凤', '花', '方', '俞', '任', '袁', '柳',
        '酆', '鲍', '史', '唐', '费', '廉', '岑', '薛', '雷', '贺',
        '倪', '汤', '滕', '殷', '罗', '毕', '郝', '邬', '安', '常',
        '乐', '于', '时', '傅', '皮', '卞', '齐', '康', '伍', '余',
        '元', '卜', '顾', '孟', '平', '黄', '和', '穆', '萧', '尹',
        # 复姓
        '司马', '欧阳', '上官', '诸葛', '东方', '皇甫', '尉迟', '公孙',
    }
    
    # 中文数字
    CHINESE_NUMBERS = {
        '零': 0, '一': 1, '二': 2, '三': 3, '四': 4,
        '五': 5, '六': 6, '七': 7, '八': 8, '九': 9,
        '十': 10, '百': 100, '千': 1000, '万': 10000,
    }
    
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []
    
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
        
        # 3. 注释
        # 注意：-- 可能是两个减号，需要检查后面是否跟着空格或换行
        if self.match('--'):
            # 检查是否是注释（后面跟着空格、换行或结束）
            if self.at_end() or self.peek().isspace():
                self.scan_comment()
                return
            else:
                # 不是注释，回退并作为两个减号处理
                self.pos -= 2
                self.column -= 2

        # # 注释
        if self.peek() == '#':
            self.scan_hash_comment()
            return

        # 4. 数字
        if self.peek().isdigit() or self.peek() == '.':
            self.scan_number()
            return

        # 5. 标点符号
        if self.peek() in '。，：\'【】':
            self.scan_punctuation()
            return

        # 6. 内联数学运算符
        if self.peek() in '+-*/%^()[]<>!=':
            self.scan_math_operator()
            return

        # 7. 中文关键字/动词/标识符
        if self.is_chinese_char(self.peek()):
            self.scan_chinese()
            return

        # 8. 英文标识符
        if self.peek().isalpha() or self.peek() == '_':
            self.scan_identifier()
            return

        # 无法识别的字符
        raise SyntaxError(f"无法识别的字符: {self.peek()} (行{self.line}, 列{self.column})")
    
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
    
    def scan_punctuation(self):
        """扫描标点符号"""
        char = self.peek()

        if char == '。':
            self.advance()
            self.add_token(TokenType.DOT, '。')
        elif char == '，':
            self.advance()
            self.add_token(TokenType.COMMA, '，')
        elif char == '：':
            self.advance()
            self.add_token(TokenType.COLON, '：')
        elif char == '=':
            self.advance()
            self.add_token(TokenType.EQUALS, '=')
        elif char == '\'':
            self.advance()
            self.add_token(TokenType.QUOTE, '\'')
        elif char == '【':
            self.advance()
            self.add_token(TokenType.CLBRACKET, '【')
        elif char == '】':
            self.advance()
            self.add_token(TokenType.CRBRACKET, '】')

    def scan_math_operator(self):
        """扫描内联数学运算符"""
        char = self.peek()

        if char == '+':
            self.advance()
            self.add_token(TokenType.PLUS, '+')
        elif char == '-':
            self.advance()
            self.add_token(TokenType.MINUS, '-')
        elif char == '*':
            self.advance()
            # 检查是否是幂运算 **
            if self.peek() == '*':
                self.advance()
                self.add_token(TokenType.STAR, '**')
            else:
                self.add_token(TokenType.STAR, '*')
        elif char == '/':
            self.advance()
            self.add_token(TokenType.SLASH, '/')
        elif char == '%':
            self.advance()
            self.add_token(TokenType.PERCENT, '%')
        elif char == '^':
            self.advance()
            self.add_token(TokenType.CARET, '^')
        elif char == '(':
            self.advance()
            self.add_token(TokenType.LPAREN, '(')
        elif char == ')':
            self.advance()
            self.add_token(TokenType.RPAREN, ')')
        elif char == '[':
            self.advance()
            self.add_token(TokenType.LBRACKET, '[')
        elif char == ']':
            self.advance()
            self.add_token(TokenType.RBRACKET, ']')
        elif char == '<':
            self.advance()
            # 检查是否是 <=
            if self.peek() == '=':
                self.advance()
                self.add_token(TokenType.LE, '<=')
            else:
                self.add_token(TokenType.LT, '<')
        elif char == '>':
            self.advance()
            # 检查是否是 >=
            if self.peek() == '=':
                self.advance()
                self.add_token(TokenType.GE, '>=')
            else:
                self.add_token(TokenType.GT, '>')
        elif char == '=':
            self.advance()
            # 检查是否是 ==
            if self.peek() == '=':
                self.advance()
                self.add_token(TokenType.EQ, '==')
            else:
                # 单个=已经在scan_punctuation中处理了
                self.add_token(TokenType.EQUALS, '=')
        elif char == '!':
            self.advance()
            # 检查是否是 !=
            if self.peek() == '=':
                self.advance()
                self.add_token(TokenType.NE, '!=')
            else:
                raise SyntaxError(f"无法识别的字符: ! (行{self.line}, 列{self.column})")
    
    def scan_chinese(self):
        """扫描中文（关键字/动词/标识符）"""
        # 尝试贪心匹配最长的关键字/动词/副词
        for length in [4, 3, 2, 1]:
            if self.pos + length <= len(self.source):
                text = self.source[self.pos:self.pos+length]

                # 检查是否为动词（优先于关键字）
                if text in self.VERBS:
                    for _ in range(length):
                        self.advance()
                    self.add_token(TokenType.VERB, text)
                    return

                # 检查是否为关键字
                if text in self.KEYWORDS:
                    for _ in range(length):
                        self.advance()
                    self.add_token(TokenType.KEYWORD, text)
                    return

                # 检查是否为副词
                if text in self.ADVERBS:
                    for _ in range(length):
                        self.advance()
                    self.add_token(TokenType.ADVERB, text)
                    return
        
        # 如果不是关键字/动词/副词，则作为标识符的一个字符
        start = self.pos
        self.advance()  # 至少前进一个字符
        
        # 继续扫描，直到遇到关键字/动词/副词或非中文字符
        # 策略：只有多字符(2+)动词/关键字才中断单字符标识符扩展
        # 单字符动词可能是标识符的一部分（如"阶乘"中的"乘"）
        while not self.at_end() and self.is_chinese_char(self.peek()):
            # 检查后续2+字符是否形成完整的动词/关键字
            found_multi = False
            for length in [4, 3, 2]:
                if self.pos + length <= len(self.source):
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
        return all(char in self.CHINESE_NUMBERS for char in text)
    
    def parse_chinese_number(self, text: str) -> int:
        """解析中文数字"""
        # 简单实现，只处理基本数字
        if text in self.CHINESE_NUMBERS:
            return self.CHINESE_NUMBERS[text]
        
        # 复杂数字需要更复杂的解析
        # 这里简化处理
        result = 0
        for char in text:
            if char in self.CHINESE_NUMBERS:
                result += self.CHINESE_NUMBERS[char]
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
    
    def add_token(self, type: TokenType, value: any):
        """添加Token"""
        self.tokens.append(Token(type, value, self.line, self.column))


import threading
import time
from collections import defaultdict

# 高级线程安全LRU缓存实现（带性能监控和读写锁分离）
class AdvancedThreadSafeLRUCache:
    """高级线程安全LRU缓存实现，包含：
    1. 读写锁分离（读多写少场景优化）
    2. 锁性能分析（等待时间统计）
    3. 缓存分区（减少锁争用）
    """
    def __init__(self, maxsize=1000, num_partitions=4):
        self.maxsize = maxsize
        self.num_partitions = num_partitions
        
        # 缓存分区：将缓存分散到多个字典中减少锁争用
        self.partitions = []
        self.partition_locks = []
        for i in range(num_partitions):
            self.partitions.append({
                'cache': {},      # hash_key -> (value, timestamp)
                'key_map': {},    # hash_key -> original_key
                'timestamp': 0,   # 分区内时间戳
            })
            self.partition_locks.append(threading.RLock())
        
        # 全局统计
        self.hits = 0
        self.misses = 0
        self.timestamp = 0
        self.lock_stats = defaultdict(int)  # 锁等待时间统计
        self.access_pattern = {'reads': 0, 'writes': 0}  # 访问模式统计
        
        # 读写锁分离：使用条件变量优化读多写少场景
        self.readers = 0
        self.writer_active = False
        self.condition = threading.Condition()
    
    def _hash_key(self, key):
        """生成缓存键的哈希值（线程安全，无状态）"""
        # 对于短字符串使用字符串本身，长字符串使用哈希
        if len(key) <= 64:
            return key  # 短字符串直接使用
        return hash(key)  # 长字符串使用哈希
    
    def _get_partition(self, hash_key):
        """根据键选择分区（减少锁争用）"""
        if isinstance(hash_key, int):
            return abs(hash_key) % self.num_partitions
        else:
            return hash(hash_key) % self.num_partitions
    
    def _record_lock_wait(self, method_name, wait_time):
        """记录锁等待时间"""
        self.lock_stats[f'{method_name}_wait_time'] += wait_time
        self.lock_stats[f'{method_name}_wait_count'] += 1
    
    def _record_access_pattern(self, is_read=True):
        """记录访问模式（读/写）"""
        if is_read:
            self.access_pattern['reads'] += 1
        else:
            self.access_pattern['writes'] += 1
    
    def _reader_enter(self):
        """读者进入（读写锁优化）"""
        with self.condition:
            while self.writer_active:
                self.condition.wait()
            self.readers += 1
    
    def _reader_exit(self):
        """读者离开（读写锁优化）"""
        with self.condition:
            self.readers -= 1
            if self.readers == 0:
                self.condition.notify_all()
    
    def _writer_enter(self):
        """写者进入（读写锁优化）"""
        with self.condition:
            while self.writer_active or self.readers > 0:
                self.condition.wait()
            self.writer_active = True
    
    def _writer_exit(self):
        """写者离开（读写锁优化）"""
        with self.condition:
            self.writer_active = False
            self.condition.notify_all()
    
    def get(self, key):
        """获取缓存项，更新访问时间（线程安全，带性能监控）"""
        start_wait = time.time()
        self._reader_enter()  # 读者进入（读写锁优化）
        wait_time = time.time() - start_wait
        self._record_lock_wait('get_reader', wait_time)
        self._record_access_pattern(is_read=True)
        
        try:
            hash_key = self._hash_key(key)
            partition_idx = self._get_partition(hash_key)
            partition = self.partitions[partition_idx]
            lock = self.partition_locks[partition_idx]
            
            start_partition_wait = time.time()
            with lock:
                partition_wait_time = time.time() - start_partition_wait
                self._record_lock_wait(f'partition_{partition_idx}', partition_wait_time)
                
                if hash_key in partition['cache']:
                    self.hits += 1
                    value, _ = partition['cache'][hash_key]
                    partition['cache'][hash_key] = (value, partition['timestamp'])
                    partition['timestamp'] += 1
                    return value
                self.misses += 1
                return None
        finally:
            self._reader_exit()  # 读者离开
    
    def put(self, key, value):
        """添加缓存项，如果超出大小则移除最久未使用的（线程安全，带性能监控）"""
        start_wait = time.time()
        self._writer_enter()  # 写者进入（读写锁优化）
        wait_time = time.time() - start_wait
        self._record_lock_wait('put_writer', wait_time)
        self._record_access_pattern(is_read=False)
        
        try:
            hash_key = self._hash_key(key)
            partition_idx = self._get_partition(hash_key)
            partition = self.partitions[partition_idx]
            lock = self.partition_locks[partition_idx]
            
            start_partition_wait = time.time()
            with lock:
                partition_wait_time = time.time() - start_partition_wait
                self._record_lock_wait(f'partition_{partition_idx}_write', partition_wait_time)
                
                if hash_key in partition['cache']:
                    partition['cache'][hash_key] = (value, partition['timestamp'])
                else:
                    # 检查分区是否已满（基于总大小/分区数）
                    partition_maxsize = self.maxsize // self.num_partitions + 1
                    if len(partition['cache']) >= partition_maxsize:
                        # 移除分区内最久未使用的
                        if partition['cache']:
                            oldest_hash_key = min(
                                partition['cache'].items(), 
                                key=lambda x: x[1][1]
                            )[0]
                            del partition['cache'][oldest_hash_key]
                            if oldest_hash_key in partition['key_map']:
                                del partition['key_map'][oldest_hash_key]
                    
                    partition['cache'][hash_key] = (value, partition['timestamp'])
                    # 存储原始键（仅用于调试）
                    if isinstance(hash_key, int):
                        partition['key_map'][hash_key] = key[:50] + "..." if len(key) > 50 else key
                
                partition['timestamp'] += 1
        finally:
            self._writer_exit()  # 写者离开
    
    def clear(self):
        """清空所有分区的缓存（线程安全）"""
        start_wait = time.time()
        self._writer_enter()  # 写者进入（需要独占访问）
        wait_time = time.time() - start_wait
        self._record_lock_wait('clear_writer', wait_time)
        
        try:
            for i in range(self.num_partitions):
                partition = self.partitions[i]
                lock = self.partition_locks[i]
                
                with lock:
                    partition['cache'].clear()
                    partition['key_map'].clear()
                    partition['timestamp'] = 0
            
            # 重置全局统计
            self.hits = 0
            self.misses = 0
            self.timestamp = 0
            self.access_pattern = {'reads': 0, 'writes': 0}
            # 注意：不清空锁统计，用于长期监控
        finally:
            self._writer_exit()
    
    def stats(self):
        """获取详细的统计信息（线程安全，带锁性能分析）"""
        start_wait = time.time()
        self._reader_enter()  # 读者进入（统计是读操作）
        wait_time = time.time() - start_wait
        self._record_lock_wait('stats_reader', wait_time)
        
        try:
            # 收集所有分区的数据
            total_size = 0
            total_key_map_size = 0
            total_memory_optimized = 0
            
            for i in range(self.num_partitions):
                partition = self.partitions[i]
                lock = self.partition_locks[i]
                
                with lock:
                    total_size += len(partition['cache'])
                    total_key_map_size += len(partition['key_map'])
                    total_memory_optimized += sum(
                        1 for k in partition['cache'] if isinstance(k, int)
                    )
            
            total = self.hits + self.misses
            
            # 锁性能统计
            lock_stats_summary = {}
            for key, value in self.lock_stats.items():
                if key.endswith('_wait_time'):
                    count_key = key.replace('_wait_time', '_wait_count')
                    if count_key in self.lock_stats and self.lock_stats[count_key] > 0:
                        avg_wait = value / self.lock_stats[count_key]
                        lock_stats_summary[key.replace('_wait_time', '_avg_wait')] = avg_wait
            
            return {
                # 基本统计
                'hits': self.hits,
                'misses': self.misses,
                'hit_rate': self.hits / max(total, 1),
                'size': total_size,
                'max_size': self.maxsize,
                'key_map_size': total_key_map_size,
                'memory_optimized': total_memory_optimized,
                'memory_saving_percent': total_memory_optimized / max(total_size, 1) * 100,
                'full_warning': total_size >= self.maxsize * 0.9,
                
                # 高级统计
                'num_partitions': self.num_partitions,
                'access_pattern': self.access_pattern.copy(),
                'read_write_ratio': (
                    self.access_pattern['reads'] / max(self.access_pattern['writes'], 1)
                    if self.access_pattern['writes'] > 0 else float('inf')
                ),
                'partition_sizes': [
                    len(self.partitions[i]['cache']) for i in range(self.num_partitions)
                ],
                
                # 锁性能统计
                'lock_stats': lock_stats_summary,
                'total_lock_wait_count': sum(
                    v for k, v in self.lock_stats.items() if k.endswith('_wait_count')
                ),
                'total_lock_wait_time': sum(
                    v for k, v in self.lock_stats.items() if k.endswith('_wait_time')
                ),
            }
        finally:
            self._reader_exit()
    
    def check_memory_warning(self):
        """检查内存警告（线程安全）"""
        stats = self.stats()  # stats()已经带锁
        warnings = []
        
        if stats['full_warning']:
            warnings.append(f"缓存已使用{stats['size']}/{stats['max_size']}，接近容量上限")
        
        if stats['hit_rate'] < 0.1 and stats['misses'] > 100:
            warnings.append(f"缓存命中率较低: {stats['hit_rate']:.1%}，考虑调整缓存策略")
        
        # 锁争用警告
        if stats['total_lock_wait_time'] > 0.1:  # 总等待时间超过100ms
            warnings.append(f"锁等待时间较高: {stats['total_lock_wait_time']:.3f}s")
        
        # 分区不均衡警告
        partition_sizes = stats['partition_sizes']
        if partition_sizes:
            max_size = max(partition_sizes)
            min_size = min(partition_sizes)
            if max_size > min_size * 3 and max_size > 10:  # 不平衡超过3倍
                warnings.append(f"缓存分区不均衡: {min_size}-{max_size}，考虑调整分区策略")
        
        return warnings

# 动态分区调整LRU缓存
class DynamicPartitionLRUCache(AdvancedThreadSafeLRUCache):
    """动态分区调整LRU缓存，根据负载自动优化分区数量"""
    
    def __init__(self, maxsize=1000, num_partitions=4, 
                 min_partitions=2, max_partitions=16,
                 rebalance_threshold=0.3,  # 30%不均衡时触发调整
                 rebalance_interval=60):   # 每60秒检查一次
        super().__init__(maxsize=maxsize, num_partitions=num_partitions)
        
        # 动态调整参数
        self.min_partitions = min_partitions
        self.max_partitions = max_partitions
        self.rebalance_threshold = rebalance_threshold
        self.rebalance_interval = rebalance_interval
        
        # 动态调整统计
        self.last_rebalance_time = time.time()
        self.rebalance_count = 0
        self.partition_history = []  # 记录分区变化历史
        
        # 性能监控
        self.before_rebalance_stats = None
    
    def _should_rebalance(self):
        """检查是否应该重新平衡分区"""
        current_time = time.time()
        if current_time - self.last_rebalance_time < self.rebalance_interval:
            return False
        
        stats = self.stats()
        
        # 检查分区不均衡
        partition_sizes = stats['partition_sizes']
        if not partition_sizes:
            return False
        
        max_size = max(partition_sizes)
        min_size = min(partition_sizes)
        total_size = sum(partition_sizes)
        
        if total_size == 0:
            return False
        
        # 计算不均衡比例
        imbalance_ratio = (max_size - min_size) / max(1, total_size / len(partition_sizes))
        
        # 检查锁争用
        lock_wait_time = stats.get('total_lock_wait_time', 0)
        lock_wait_per_op = lock_wait_time / max(1, stats.get('total_lock_wait_count', 1))
        
        # 触发条件：不均衡超过阈值 或 锁争用过高
        return (imbalance_ratio > self.rebalance_threshold or 
                lock_wait_per_op > 0.001)  # 平均锁等待超过1ms
    
    def _calculate_optimal_partitions(self, stats):
        """计算最优分区数量"""
        current_partitions = self.num_partitions
        total_size = stats['size']
        
        # 基于总大小调整
        if total_size < 100:
            optimal = max(self.min_partitions, 2)  # 小缓存使用较少分区
        elif total_size < 1000:
            optimal = max(self.min_partitions, 4)  # 中等缓存
        else:
            optimal = max(self.min_partitions, min(8, self.max_partitions))  # 大缓存
        
        # 基于锁争用调整
        lock_wait_per_op = stats.get('total_lock_wait_time', 0) / max(1, stats.get('total_lock_wait_count', 1))
        if lock_wait_per_op > 0.002:  # 锁等待超过2ms
            optimal = min(self.max_partitions, optimal * 2)  # 增加分区减少争用
        elif lock_wait_per_op < 0.0001:  # 锁等待很低
            optimal = max(self.min_partitions, optimal // 2)  # 减少分区降低开销
        
        # 基于访问模式调整
        read_write_ratio = stats.get('read_write_ratio', 1)
        if read_write_ratio > 10:  # 读远多于写
            optimal = min(self.max_partitions, optimal + 2)  # 增加分区支持更多并发读
        
        # 确保在范围内
        optimal = max(self.min_partitions, min(self.max_partitions, optimal))
        
        return optimal
    
    def _rebalance_partitions(self, new_num_partitions):
        """重新平衡分区到新数量"""
        if new_num_partitions == self.num_partitions:
            return False  # 无需调整
        
        print(f"[动态分区] 从 {self.num_partitions} 分区调整到 {new_num_partitions} 分区")
        
        # 保存当前所有数据
        all_items = []
        for i in range(self.num_partitions):
            partition = self.partitions[i]
            lock = self.partition_locks[i]
            
            with lock:
                for hash_key, (value, timestamp) in partition['cache'].items():
                    original_key = partition['key_map'].get(hash_key, None)
                    all_items.append((original_key, value, timestamp))
        
        # 清空当前分区
        self.partitions = []
        self.partition_locks = []
        
        # 创建新分区
        self.num_partitions = new_num_partitions
        for i in range(new_num_partitions):
            self.partitions.append({
                'cache': {},
                'key_map': {},
                'timestamp': 0,
            })
            self.partition_locks.append(threading.RLock())
        
        # 重新分配数据
        for original_key, value, timestamp in all_items:
            if original_key is None:
                continue  # 跳过没有原始键的项（不应该发生）
            
            hash_key = self._hash_key(original_key)
            partition_idx = self._get_partition(hash_key)
            partition = self.partitions[partition_idx]
            
            partition['cache'][hash_key] = (value, timestamp)
            if isinstance(hash_key, int):
                partition['key_map'][hash_key] = original_key[:50] + "..." if len(original_key) > 50 else original_key
        
        # 更新统计
        self.last_rebalance_time = time.time()
        self.rebalance_count += 1
        self.partition_history.append({
            'time': self.last_rebalance_time,
            'old_partitions': self.num_partitions,  # 注意：这里记录的是调整后的，但历史记录会显示变化
            'new_partitions': new_num_partitions,
            'size': len(all_items)
        })
        
        return True
    
    def auto_rebalance(self):
        """自动重新平衡分区（如果应该的话）"""
        if not self._should_rebalance():
            return False
        
        # 保存调整前统计
        self.before_rebalance_stats = self.stats()
        
        # 计算最优分区数
        optimal_partitions = self._calculate_optimal_partitions(self.before_rebalance_stats)
        
        # 执行调整
        if self._rebalance_partitions(optimal_partitions):
            print(f"[动态分区] 完成调整，当前 {self.num_partitions} 分区")
            return True
        return False
    
    def stats(self):
        """获取统计信息，包含动态调整信息"""
        base_stats = super().stats()
        
        # 添加动态调整信息
        base_stats.update({
            'dynamic_partitioning': {
                'min_partitions': self.min_partitions,
                'max_partitions': self.max_partitions,
                'current_partitions': self.num_partitions,
                'rebalance_count': self.rebalance_count,
                'last_rebalance_time': self.last_rebalance_time,
                'time_since_last_rebalance': time.time() - self.last_rebalance_time,
                'rebalance_threshold': self.rebalance_threshold,
                'rebalance_interval': self.rebalance_interval,
            },
            'partition_history_count': len(self.partition_history),
        })
        
        return base_stats
    
    def get(self, key):
        """获取缓存项，自动检查是否需要重新平衡"""
        result = super().get(key)
        
        # 定期检查是否需要重新平衡（每100次操作检查一次）
        if (self.hits + self.misses) % 100 == 0:
            self.auto_rebalance()
        
        return result
    
    def put(self, key, value):
        """添加缓存项，自动检查是否需要重新平衡"""
        result = super().put(key, value)
        
        # 定期检查是否需要重新平衡（每50次写操作检查一次）
        if self.access_pattern['writes'] % 50 == 0:
            self.auto_rebalance()
        
        return result


# 全局动态分区LRU缓存（带自动优化）
_token_cache = DynamicPartitionLRUCache(
    maxsize=1000, 
    num_partitions=4,
    min_partitions=2,
    max_partitions=8,
    rebalance_threshold=0.3,
    rebalance_interval=30  # 30秒检查一次
)

def tokenize(source: str, use_cache: bool = True) -> List[Token]:
    """分词函数（带LRU缓存）"""
    if use_cache:
        cached = _token_cache.get(source)
        if cached is not None:
            # 返回缓存副本
            return [Token(t.type, t.value, t.line, t.column) for t in cached]
    
    tokenizer = PreTokenizer(source)
    tokens = tokenizer.tokenize()
    
    # 缓存结果
    if use_cache:
        _token_cache.put(source, tokens.copy())
    
    return tokens

def get_cache_stats() -> Dict[str, Any]:
    """获取缓存统计信息"""
    return _token_cache.stats()

def get_cache_warnings() -> List[str]:
    """获取缓存警告信息"""
    return _token_cache.check_memory_warning()

def clear_cache():
    """清空缓存"""
    _token_cache.clear()


# 测试代码
if __name__ == '__main__':
    # 测试用例
    test_cases = [
        "定义x=5相加3。",
        "列表1 2 3，映射相乘2。",
        "如果x大于y那么x否则y。",
        "张三=18。",
        "定义阶乘=函数n如果n等于1那么1否则n相乘阶乘n相减1。",
    ]
    
    for source in test_cases:
        print(f"\n源码: {source}")
        tokens = tokenize(source)
        for token in tokens:
            print(f"  {token}")

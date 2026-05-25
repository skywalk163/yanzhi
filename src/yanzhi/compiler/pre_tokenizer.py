"""
知行语言预分词层
实现无空格分词的核心算法
"""

from typing import List, Tuple, Optional
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
        '定', '设', '函', '若', '则', '否则', '遍历', '当', '入', '出', '于',
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
        '用',
        # 算术
        '加', '减', '乘', '除', '模', '幂', '负', '绝对',
        # 比较
        '大', '小', '等', '不等', '大等于', '小等于', '大于等于', '小于等于',
        # 逻辑
        '且', '或', '非',
        # 列表
        '列', '首', '余', '入', '长', '添', '连', '含', '删', '空', '范围',
        # I/O
        '印', '读', '写',
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
    ADVERBS = {'皆', '只', '归', '并'}
    
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


def tokenize(source: str) -> List[Token]:
    """分词函数"""
    tokenizer = PreTokenizer(source)
    return tokenizer.tokenize()


# 测试代码
if __name__ == '__main__':
    # 测试用例
    test_cases = [
        "定x=5加3。",
        "列1 2 3，皆乘2。",
        "若x大y则x否则y。",
        "张三=18。",
        "定阶乘=函n若n等1则1否则n乘阶乘n减1。",
    ]
    
    for source in test_cases:
        print(f"\n源码: {source}")
        tokens = tokenize(source)
        for token in tokens:
            print(f"  {token}")

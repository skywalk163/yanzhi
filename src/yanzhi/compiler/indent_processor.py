# -*- coding: utf-8 -*-
"""知行语言缩进处理器

实现缩进敏感的语法规则：
- 下一段开头空两格（一个全角空格）代表进入代码块
- 下一段开头顶格代表退出代码块

核心逻辑：
- 全角空格（\u3000）作为缩进单位
- 缩进增加 → 生成 INDENT token
- 缩进减少 → 生成 DEDENT token
- 缩进不变 → 不生成缩进相关 token

参考 Python 的缩进机制，但使用全角空格更符合中文书写习惯。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass
class IndentToken:
    """缩进标记"""
    type: str  # 'INDENT' 或 'DEDENT'
    line: int  # 行号
    col: int   # 列号
    
    def __repr__(self):
        return f"IndentToken({self.type}, line={self.line})"


class IndentProcessor:
    """缩进处理器
    
    负责跟踪缩进层级，在缩进变化时生成 INDENT/DEDENT token。
    
    使用方法：
    1. 对每一行代码，调用 process_line_indent() 获取该行开头的缩进 token
    2. 处理完所有行后，调用 finalize() 获取文件末尾的 DEDENT token
    """
    
    # 全角空格（一个汉字宽度）
    FULLWIDTH_SPACE = '\u3000'
    
    def __init__(self):
        # 缩进栈，记录每层的缩进量（以全角空格数计）
        # 栈底始终为 0（顶格）
        self.indent_stack: List[int] = [0]
        
        # 待输出的缩进 token
        self.pending_tokens: List[IndentToken] = []
        
        # 当前行号
        self.current_line = 1
        
        # 是否在第一行（用于处理文件开头的缩进）
        self.is_first_line = True
    
    def _count_indent(self, line: str) -> Tuple[int, int]:
        """计算行首的缩进量
        
        返回：(全角空格数, 半角空格数)
        
        规则：
        - 全角空格（\u3000）计为 1 个缩进单位
        - 半角空格和 Tab 需要转换为全角空格等价量
        - Tab = 2 个全角空格（与中文排版习惯一致）
        - 2 个半角空格 = 1 个全角空格
        """
        fullwidth_count = 0
        halfwidth_count = 0
        tab_count = 0
        
        i = 0
        while i < len(line):
            ch = line[i]
            if ch == self.FULLWIDTH_SPACE:
                fullwidth_count += 1
                i += 1
            elif ch == ' ':
                halfwidth_count += 1
                i += 1
            elif ch == '\t':
                tab_count += 1
                i += 1
            else:
                break
        
        # 转换为全角空格等价量
        # Tab = 2 个全角空格
        # 2 个半角空格 = 1 个全角空格
        indent_units = fullwidth_count + tab_count * 2 + halfwidth_count // 2
        
        return indent_units, halfwidth_count
    
    def process_line_indent(self, line: str, line_num: int) -> List[IndentToken]:
        """处理一行的缩进，返回需要插入的缩进 token
        
        参数：
        - line: 该行的内容（不包含换行符）
        - line_num: 行号（从 1 开始）
        
        返回：
        - 需要在该行开头插入的缩进 token 列表（可能为空）
        
        逻辑：
        1. 计算该行的缩进量
        2. 与栈顶比较：
           - 相等：无变化，返回空列表
           - 大于栈顶：缩进增加，压栈并生成 INDENT
           - 小于栈顶：缩进减少，弹栈并生成 DEDENT（可能多个）
        """
        self.current_line = line_num
        self.pending_tokens = []
        
        # 空行或注释行不处理缩进
        stripped = line.strip()
        if not stripped or stripped.startswith('#') or stripped.startswith('注：'):
            return []
        
        # 计算缩进量
        indent_units, halfwidth_count = self._count_indent(line)
        
        # 第一行不允许有缩进（顶格开始）
        if self.is_first_line:
            if indent_units > 0:
                # 第一行有缩进，报错
                raise IndentationError(
                    f"第 {line_num} 行：文件开头不能有缩进，请顶格书写"
                )
            self.is_first_line = False
            return []
        
        # 获取当前缩进层级
        current_indent = self.indent_stack[-1]
        
        if indent_units > current_indent:
            # 缩进增加：进入新的代码块
            # 检查是否只增加了一层（不允许一次增加多层）
            if indent_units > current_indent + 1:
                raise IndentationError(
                    f"第 {line_num} 行：缩进过深，一次只能增加一层缩进（一个全角空格）\n"
                    f"  当前缩进：{current_indent} 层\n"
                    f"  期望缩进：{current_indent + 1} 层\n"
                    f"  实际缩进：{indent_units} 层"
                )
            
            # 压栈并生成 INDENT
            self.indent_stack.append(indent_units)
            self.pending_tokens.append(IndentToken('INDENT', line_num, 0))
            
        elif indent_units < current_indent:
            # 缩进减少：退出代码块
            # 可能退出多层，需要生成多个 DEDENT
            while self.indent_stack and self.indent_stack[-1] > indent_units:
                # 检查是否匹配栈中的某个层级
                if indent_units not in self.indent_stack:
                    raise IndentationError(
                        f"第 {line_num} 行：缩进不匹配，没有对应的代码块\n"
                        f"  当前缩进栈：{self.indent_stack}\n"
                        f"  期望缩进：{indent_units} 层"
                    )
                
                self.indent_stack.pop()
                self.pending_tokens.append(IndentToken('DEDENT', line_num, 0))
        
        # indent_units == current_indent: 无变化，不生成 token
        
        return self.pending_tokens
    
    def finalize(self) -> List[IndentToken]:
        """处理文件末尾，关闭所有未关闭的代码块
        
        返回：需要在文件末尾插入的 DEDENT token 列表
        """
        tokens = []
        
        # 弹出所有非零缩进层级
        while len(self.indent_stack) > 1:
            self.indent_stack.pop()
            tokens.append(IndentToken('DEDENT', self.current_line + 1, 0))
        
        return tokens
    
    def get_current_indent(self) -> int:
        """获取当前缩进层级"""
        return self.indent_stack[-1]
    
    def reset(self):
        """重置处理器状态"""
        self.indent_stack = [0]
        self.pending_tokens = []
        self.current_line = 1
        self.is_first_line = True


def process_indentation(source: str) -> Tuple[List[str], List[IndentToken]]:
    """处理源码的缩进，返回带缩进 token 标记的行列表
    
    这是一个辅助函数，用于演示缩进处理逻辑。
    
    参数：
    - source: 源码字符串
    
    返回：
    - (lines, all_indent_tokens)
      - lines: 按行分割的源码
      - all_indent_tokens: 所有缩进 token（按出现顺序）
    """
    processor = IndentProcessor()
    lines = source.split('\n')
    all_indent_tokens = []
    
    for i, line in enumerate(lines, start=1):
        indent_tokens = processor.process_line_indent(line, i)
        all_indent_tokens.extend(indent_tokens)
    
    # 文件末尾的 DEDENT
    final_tokens = processor.finalize()
    all_indent_tokens.extend(final_tokens)
    
    return lines, all_indent_tokens


# 示例用法
if __name__ == '__main__':
    # 测试代码
    test_code = """若 条件A：
　执行操作一
　若 条件B：
　　执行操作二
　执行操作三
执行操作四"""
    
    print("测试代码：")
    print(test_code)
    print("\n" + "="*50 + "\n")
    
    try:
        lines, tokens = process_indentation(test_code)
        print("缩进 token：")
        for tok in tokens:
            print(f"  {tok}")
    except IndentationError as e:
        print(f"缩进错误：{e}")

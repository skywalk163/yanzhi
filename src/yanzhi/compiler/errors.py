"""
知行语言错误处理
"""


class YanError(Exception):
    """知行语言错误基类"""
    
    def __init__(self, message: str, line: int = 0, column: int = 0):
        self.message = message
        self.line = line
        self.column = column
        super().__init__(self.format())
    
    def format(self) -> str:
        """格式化错误消息"""
        if self.line > 0:
            return f"行{self.line}列{self.column}: {self.message}"
        return self.message


class LexError(YanError):
    """词法错误"""
    pass


class ParseError(YanError):
    """语法错误"""
    pass


class RuntimeError(YanError):
    """运行时错误"""
    pass


class TypeError(YanError):
    """类型错误"""
    pass


class NameError(YanError):
    """名称错误"""
    pass


class IndexError(YanError):
    """索引错误"""
    pass


class ValueError(YanError):
    """值错误"""
    pass


class FileNotFoundError(YanError):
    """文件未找到错误"""
    pass


def format_error(error: YanError, source: str = None) -> str:
    """格式化错误消息，包含源码位置和友好提示"""
    lines = [
        "=" * 60,
        "❌ 错误信息",
        "=" * 60,
        f"错误类型: {type(error).__name__}",
        f"错误描述: {error.message}",
    ]
    
    if error.line > 0:
        lines.append(f"错误位置: 行{error.line}列{error.column}")
        
        if source:
            # 显示错误行及上下文
            source_lines = source.split('\n')
            start_line = max(1, error.line - 2)
            end_line = min(len(source_lines), error.line + 2)
            
            lines.append("")
            lines.append("源码上下文:")
            lines.append("-" * 60)
            
            for i in range(start_line - 1, end_line):
                line_num = i + 1
                line_content = source_lines[i]
                
                # 标记错误行
                if line_num == error.line:
                    lines.append(f">>> {line_num:4d} | {line_content}")
                    # 显示错误位置指示
                    pointer = ' ' * (error.column - 1) + '^'
                    lines.append(f"         | {pointer}")
                    lines.append(f"         | 这里出现问题！")
                else:
                    lines.append(f"    {line_num:4d} | {line_content}")
            
            lines.append("-" * 60)
    
    # 添加修复建议
    suggestion = get_error_suggestion(error)
    if suggestion:
        lines.append("")
        lines.append("💡 修复建议:")
        lines.append(f"   {suggestion}")
    
    lines.append("=" * 60)
    
    return '\n'.join(lines)


def get_error_suggestion(error: YanError) -> str:
    """根据错误类型提供修复建议"""
    message = error.message.lower()
    
    # 词法错误建议
    if isinstance(error, LexError):
        if '无法识别' in message:
            return "请检查是否使用了不支持的字符或符号"
        elif '字符串' in message:
            return "请确保字符串用引号包裹，并且引号成对出现"
        elif '数字' in message:
            return "请检查数字格式是否正确"
    
    # 语法错误建议
    elif isinstance(error, ParseError):
        if '期望' in message:
            if '。' in message:
                return "每个语句应该以句号'。'结束"
            elif '则' in message:
                return "条件语句需要'则'关键字来分隔条件和结果"
            elif '否则' in message:
                return "条件语句需要'否则'关键字来提供默认值"
            elif '结束' in message:
                return "循环语句需要'结束'关键字来标记结束"
            elif '标识符' in message:
                return "这里需要一个变量名或函数名"
            elif '=' in message:
                return "定义语句需要等号'='来分隔名称和值"
        elif '未定义' in message:
            return "请检查变量名是否正确，或是否需要先定义"
    
    # 运行时错误建议
    elif isinstance(error, RuntimeError):
        if '类型' in message:
            return "请检查操作的数据类型是否正确"
        elif '索引' in message:
            return "请检查索引是否超出范围"
        elif '参数' in message:
            return "请检查函数参数数量和类型是否正确"
    
    # 类型错误建议
    elif isinstance(error, TypeError):
        return "请检查数据类型是否匹配操作要求"
    
    # 名称错误建议
    elif isinstance(error, NameError):
        return "请检查变量或函数名是否已定义，注意区分大小写"
    
    return ""


# 调试工具
class Debugger:
    """调试器"""
    
    def __init__(self, source: str):
        self.source = source
        self.breakpoints = []
        self.trace = []
        self.verbose = False
    
    def add_breakpoint(self, line: int):
        """添加断点"""
        self.breakpoints.append(line)
        if self.verbose:
            print(f"断点已添加: 行{line}")
    
    def remove_breakpoint(self, line: int):
        """移除断点"""
        if line in self.breakpoints:
            self.breakpoints.remove(line)
            if self.verbose:
                print(f"断点已移除: 行{line}")
    
    def is_breakpoint(self, line: int) -> bool:
        """检查是否为断点"""
        return line in self.breakpoints
    
    def add_trace(self, line: int, column: int, message: str):
        """添加跟踪信息"""
        self.trace.append((line, column, message))
        if self.verbose:
            print(f"跟踪: 行{line}列{column} - {message}")
    
    def show_trace(self) -> str:
        """显示跟踪信息"""
        if not self.trace:
            return "跟踪为空"
        
        result = ["执行跟踪:"]
        for i, (line, column, message) in enumerate(self.trace, 1):
            result.append(f"  {i}. 行{line}列{column}: {message}")
        return '\n'.join(result)
    
    def show_context(self, line: int, context: int = 3) -> str:
        """显示上下文"""
        lines = self.source.split('\n')
        start = max(0, line - context - 1)
        end = min(len(lines), line + context)
        
        result = []
        for i in range(start, end):
            prefix = '>' if i == line - 1 else ' '
            result.append(f"{prefix} {i+1:4d} | {lines[i]}")
        
        return '\n'.join(result)
    
    def clear_trace(self):
        """清空跟踪"""
        self.trace = []


# 错误处理装饰器
def catch_errors(func):
    """捕获错误的装饰器"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except YanError as e:
            print(f"错误: {e}")
            return None
        except Exception as e:
            print(f"内部错误: {e}")
            import traceback
            traceback.print_exc()
            return None
    return wrapper


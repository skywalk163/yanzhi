"""
初始化编译器数据结构
注册所有编译器相关的结构体
"""

from yanzhi.runtime.structs import define_struct


def init_compiler_structs():
    """初始化编译器结构体"""
    
    # Token结构体
    define_struct('Token', {
        '类型': '文',
        '值': '任意',
        '行': '数',
        '列': '数'
    })
    
    # AST节点结构体
    
    # 字面量
    define_struct('Num', {'值': '数'})
    define_struct('Str', {'值': '文'})
    define_struct('Bool', {'值': '布尔'})
    define_struct('Nil', {})
    
    # 标识符和调用
    define_struct('Ident', {'名称': '文'})
    define_struct('Call', {'动词': '文', '参数': '列'})
    define_struct('Pipeline', {'左': '任意', '右': '任意'})
    
    # 定义和赋值
    define_struct('Define', {'名称': '文', '值': '任意'})
    define_struct('Assign', {'名称': '文', '值': '任意'})
    
    # Lambda
    define_struct('Lambda', {'参数': '列', '体': '任意'})
    
    # 控制流
    define_struct('If', {'条件': '任意', '则分支': '任意', '否则分支': '任意'})
    define_struct('ForEach', {'变量': '文', '可迭代': '任意', '体': '任意'})
    define_struct('While', {'条件': '任意', '体': '任意'})
    
    # 块和程序
    define_struct('Block', {'语句': '列'})
    define_struct('Program', {'语句': '列'})
    
    # 编译器状态
    
    # 词法分析器状态
    define_struct('LexerState', {
        '源码': '文',
        '位置': '数',
        '行号': '数',
        '列号': '数',
        'tokens': '列'
    })
    
    # 语法分析器状态
    define_struct('ParserState', {
        'tokens': '列',
        '位置': '数'
    })
    
    # 编译器上下文
    define_struct('CompilerContext', {
        '源文件': '文',
        '输出文件': '文',
        '选项': '列',
        '错误': '列'
    })


# 自动初始化
init_compiler_structs()

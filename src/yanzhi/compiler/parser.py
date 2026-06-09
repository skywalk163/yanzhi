"""
知行语言语法分析器
实现递归下降解析
"""

from typing import List, Optional
from .lexer import Lexer, Token, TokenType
from .ast import *
from .errors import ParseError
from ..yan.syntax_templates import try_rewrite


class Parser:
    """语法分析器"""
    
    # 动词元数表
    VERB_ARITY = {
        # 函数调用（可变参数）
        '使用': -1,
        # 算术运算（二元）
        '相加': 2, '相减': 2, '相乘': 2, '相除': 2, '取余': 2, '乘方': 2,
        # 一元运算
        '取负': 1, '绝对': 1, '取整': 1, '开方': 1,
        # 比较运算（二元）
        '大于': 2, '小于': 2, '等于': 2, '不等': 2, '大于等于': 2, '小于等于': 2,
        # 逻辑运算
        '并且': 2, '或者': 2, '非也': 1,
        # 列表操作
        '列表': -1,  # 可变参数
        '首个': 1, '剩余': 1, '长度': 1, '空值': 1,
        '索引': 2, '添加': 2, '连接': 2, '包含': 2, '删除': 2, '计数': 2,
        '范围': 2,
        # VM 内置（保留单字）
        '取': 1, '尾': 1, '排': 1, '反': 1, '合': 1, '字': 1, '整': 1, '类': 1,
        # I/O
        '打印': 1, '读取': 1, '写入': 2, '追加': 2, '存在': 1,
        '删除文件': 1, '列出目录': 1,
        # 谓词
        '是数': 1, '是文': 1, '是列': 1, '是串': 1, '是空': 1, '是零': 1, '是正': 1, '是负': 1, '是布尔': 1,
        '是文件': 1, '是目录': 1,
        '全真': 1, '任真': 1, '全假': 1,
        # 序列操作
        '排序': 1, '反转': 1, '去重': 1, '位置': 2, '子列': 3, '拉链': 2, '交集': 2, '并集': 2, '差集': 2,
        # 数学函数
        '四舍五入': 1, '最小': 1, '最大': 1, '求和': 1, '乘积': 1, '求积': 1,
        '展平': 1, '枚举': 1, '分块': 2, '交错': -1, '范围步': 3, '间隔': 2,
        '正弦': 1, '余弦': 1, '正切': 1, '指数': 1, '对数': 1, '绝对值': 1,
        # 高阶函数
        '映射': 2, '过滤': 2, '归约': 3, '合并': 2,
        # 字符串操作
        '连接': 2, '子串': 3, '小写': 1, '大写': 1, '查找': 2, '长度': 1, '截取': 3,
        '分割': 2, '替换': 3, '格式化': -1,
        # 字典
        '字典': -1, '键': 2, '设键': 3, '键集': 1, '值集': 1, '含键': 2, '删键': 2, '键数': 1,
        # 随机
        '随机': 0, '随机整数': 2, '随机选择': 1, '随机打乱': 1, '随机采样': 2,
        # 重复工具
        '重复': 2,
        # JSON
        '编JSON': 1, '解JSON': 1, '读JSON': 1, '写JSON': 2, '紧JSON': 1,
        # URL
        '编码URL': 1, '解码URL': 1, '解析URL': 1,
        # 正则
        '正则测试': 2, '正则匹配': 2, '正则搜索': 2, '正则全找': 2, '正则替换': 3, '正则分割': 2,
        # Python/C 互操作
        '求值Py': 1, '执行Py': 1, '导入模块': 1, '取模块': 2, '调模块': 3,
        '加载C库': 1, '取C符号': 2, '调C函数': 3, '调C双精': 3,
        # 数据库
        '开库': 1, '关库': 1, '执行SQL': 2, '查询SQL': 2, '执行参数': 3, '表列表': 1, '提交': 2,
        '提交JSON': 2,
        # 输入
        '输入': 0,
        # 代码即数据（同像性）
        '执行': 1,    # 执行 ast节点
        '源码': 1,    # 源码 ast节点  → 字符串
        '语法树': 1,  # 语法树 ast节点 → 调试字符串
        '节点类型': 1,
        '子节点': 1,
        '是语法树': 1,
    }
    
    # 副词（高阶函数）
    ADVERBS = {'映射', '过滤', '归约', '合并'}
    
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        self._in_call = False  # 是否在动词参数解析中
    
    def parse(self) -> Program:
        """解析程序"""
        statements = []
        
        while not self.at_end():
            stmt = self.parse_statement()
            if stmt is not None:
                statements.append(stmt)
        
        return Program(statements)
    
    def parse_statement(self) -> Optional[ASTNode]:
        """解析语句"""
        token = self.peek()
        
        # 跳过EOF
        if token.type == TokenType.EOF:
            return None
        
        # 变量定义（含 定义宏 形式）
        if token.type == TokenType.KEYWORD and token.value == '定义':
            # 向前看：如果下一个 token 是关键字 宏，则走宏定义路径
            if (self.pos + 1 < len(self.tokens) and
                    self.tokens[self.pos + 1].type == TokenType.KEYWORD and
                    self.tokens[self.pos + 1].value == '宏'):
                return self.parse_named_macro()
            return self.parse_define()
        
        # 变量赋值
        if token.type == TokenType.KEYWORD and token.value == '赋值':
            return self.parse_assign()
        
        # 遍历循环
        if token.type == TokenType.KEYWORD and token.value == '遍历':
            return self.parse_foreach()

        # 友好语法：对于循环
        if token.type == TokenType.KEYWORD and token.value == '对于':
            return self.parse_friendly_for()

        # 友好语法：每次循环（作为"每个"的别名）
        if token.type == TokenType.KEYWORD and token.value == '每次':
            return self.parse_foreach_friendly()

        # 言律句式模板（支持当…就…、每隔…等自然语言模式）
        yan_result = try_rewrite(self.tokens, self.pos)
        if yan_result is not None:
            rewritten, consumed = yan_result
            # 用展开后的 token 替换原 token 序列
            self.tokens = (self.tokens[:self.pos] + rewritten +
                           self.tokens[self.pos + consumed:])
            # 递归解析展开后的语句
            return self.parse_statement()

        # 启用成语模式：启用 X 策略
        if token.type == TokenType.KEYWORD and token.value == '启用':
            return self._try_idiom_enable()

        # 当循环
        if token.type == TokenType.KEYWORD and token.value == '循环当':
            return self.parse_while()
        
        # 函数定义（作为表达式）
        if token.type == TokenType.KEYWORD and token.value == '函数':
            return self.parse_lambda()

        # 宏定义
        if token.type == TokenType.KEYWORD and token.value == '宏':
            return self.parse_macro()

        # 引用
        if token.type == TokenType.QUOTE:
            return self.parse_quote()
        
        # 条件表达式（作为独立语句）
        if token.type == TokenType.KEYWORD and token.value == '如果':
            result = self.parse_if()
            # 消费结尾的。
            if self.match(TokenType.DOT):
                pass
            return result
        
        # Try-catch语句
        if token.type == TokenType.KEYWORD and token.value in ('尝试', '试'):
            return self.parse_try()

        # 返回语句
        if token.type == TokenType.KEYWORD and token.value == '返回':
            return self.parse_return()

        # 友好语法：算表达式
        if token.type == TokenType.KEYWORD and token.value == '算':
            return self.parse_math_statement()

        # 注释语句（跳过）
        if token.type == TokenType.KEYWORD and token.value in ('注释', '注'):
            self.advance()  # 消费"注释"或"注"
            # 消费冒号（如果有）
            if self.match(TokenType.COLON):
                pass
            # 消费注释内容，直到遇到下一个语句的开始
            # 下一个语句通常以数字、标识符、关键字（定、设、若等）或动词开始
            while not self.at_end():
                next_token = self.peek()
                # 如果遇到句号，停止
                if next_token.type == TokenType.DOT:
                    break
                # 如果遇到数字，停止（可能是下一个语句的开始）
                if next_token.type == TokenType.NUM:
                    break
                # 如果遇到动词，停止
                if next_token.type == TokenType.VERB:
                    break
                # 如果遇到关键字，停止
                if next_token.type == TokenType.KEYWORD:
                    break
                # 否则继续消费
                self.advance()
            # 消费句号（如果有）
            if self.match(TokenType.DOT):
                pass
            return None  # 返回None，不生成AST节点

        # 作用域块语法：xxx的时候：stmt。stmt。...
        if token.type == TokenType.IDENT and token.value.endswith('的时候'):
            return self.parse_scope_block()

        # 表达式语句
        expr = self.parse_expression()
        
        # 消费结尾的。
        if self.match(TokenType.DOT):
            pass
        
        return expr
    
    def _try_idiom_enable(self) -> ASTNode:
        """解析「启用 X 策略」模式，展开为宏定义语句"""
        start = self.pos
        self.advance()  # 消费 启用

        # 收集成语名（可能被split成多个IDENT/VERB token）
        name_parts = []
        while not self.at_end():
            t = self.peek()
            if t.type in (TokenType.IDENT, TokenType.VERB):
                name_parts.append(self.advance().value)
            else:
                break
        if not name_parts:
            raise ParseError("期望成语名", self.peek().line, self.peek().column)
        idiom_name = ''.join(name_parts)

        # 消费策略关键字
        self.consume(TokenType.KEYWORD, '策略', "期望'策略'")

        # 查找成语模板
        from ..yan.dsl_factory import IDIOM_REGISTRY
        if idiom_name not in IDIOM_REGISTRY:
            raise ParseError(f"未定义的成语: {idiom_name}", self.peek().line, self.peek().column)

        # 对模板进行词法分析
        from .lexer import Lexer
        template = IDIOM_REGISTRY[idiom_name]
        template_tokens = Lexer(template).tokenize()

        consumed = self.pos - start
        # 用模板 token 替换原始 token 序列
        self.tokens = (self.tokens[:start] + template_tokens +
                       self.tokens[self.pos:])
        self.pos = start
        # 递归解析展开后的语句
        return self.parse_statement()

    def parse_define(self) -> Define:
        """解析变量定义"""
        self.consume(TokenType.KEYWORD, '定义', "期望'定义'")

        # 收集变量名（可能被分割成多个Token）
        name_parts = []
        while not self.at_end() and self.peek().type in (TokenType.IDENT, TokenType.VERB):
            name_parts.append(self.advance().value)

        if not name_parts:
            raise ParseError("期望标识符", self.peek().line, self.peek().column)

        name = ''.join(name_parts)

        # 支持"是"和"="两种语法
        if self.match(TokenType.KEYWORD, '是'):
            # "定x是value。"语法
            pass
        else:
            # "定x=value。"语法
            self.consume(TokenType.EQUALS, None, "期望'='或'是'")

        value = self.parse_expression()
        self.consume(TokenType.DOT, None, "期望'。'")

        return Define(name, value)
    
    def parse_assign(self) -> Assign:
        """解析变量赋值"""
        self.consume(TokenType.KEYWORD, '赋值', "期望'赋值'")
        name = self.consume(TokenType.IDENT, None, "期望标识符").value
        
        # 检查是否是索引赋值：lst[j] = expr
        if self.peek().type == TokenType.LBRACKET:
            self.advance()  # 消耗 [
            index = self.parse_expression()
            self.consume(TokenType.RBRACKET, None, "期望']'")
            self.consume(TokenType.EQUALS, None, "期望'='")
            value = self.parse_expression()
            self.consume(TokenType.DOT, None, "期望'。'")
            return Assign(name, value, index)
        
        self.consume(TokenType.EQUALS, None, "期望'='")
        value = self.parse_expression()
        self.consume(TokenType.DOT, None, "期望'。'")
        return Assign(name, value)
    
    def parse_if(self) -> If:
        """解析条件表达式"""
        self.consume(TokenType.KEYWORD, '如果', "期望'如果'")
        condition = self.parse_expression()
        
        # 支持'那么'和'就'两种关键字
        if not self.match(TokenType.KEYWORD, '那么'):
            self.consume(TokenType.KEYWORD, '就', "期望'那么'或'就'")

        # 解析then分支：如果后面是：则解析语句块，否则解析单表达式
        then_branch = self._parse_if_branch()

        # 检查是否有"否则"或"不然"分支
        if self.match(TokenType.KEYWORD, '否则') or self.match(TokenType.KEYWORD, '不然'):
            # 解析else分支
            else_branch = self._parse_if_branch()
        else:
            # 没有否则分支，返回None
            else_branch = Nil()

        # 消费块分支后可选的结束/完毕
        if self.match(TokenType.KEYWORD, '结束') or self.match(TokenType.KEYWORD, '完毕'):
            pass

        # 不消费。，让调用者决定

        return If(condition, then_branch, else_branch)

    def _parse_if_branch(self) -> ASTNode:
        """解析 if 分支：支持 则：块 或 则 expr 两种格式"""
        # 如果是 返回 语句
        if self.peek().type == TokenType.KEYWORD and self.peek().value == '返回':
            return self.parse_return()
        
        # 如果后面是 ：，解析语句块
        if self.peek().type == TokenType.COLON:
            self.advance()  # 消耗 ：
            block = self.parse_block()
            return block
        
        # 否则解析单表达式
        return self.parse_expression()
    
    def parse_foreach(self) -> ForLoop:
        """解析遍历循环"""
        self.consume(TokenType.KEYWORD, '遍历', "期望'遍历'")
        var = self.consume(TokenType.IDENT, None, "期望循环变量").value
        
        # 检查是"于"还是"从"
        if self.match(TokenType.KEYWORD, '于'):
            # 原有语法：遍历i于列表
            iterable = self.parse_expression()
        elif self.match(TokenType.KEYWORD, '从'):
            # 友好语法：遍历i从1到5
            start = self.parse_expression()
            self.consume(TokenType.KEYWORD, '到', "期望'到'")
            end = self.parse_expression()
            # 创建范围迭代：range(start, end+1)
            iterable = Call('范围', [start, Call('相加', [end, Num(1)])])
        else:
            raise ParseError("期望'于'或'从'", self.peek().line, self.peek().column)
        
        self.consume(TokenType.COLON, None, "期望'：'")
        body = self.parse_block()
        # 消费可选的结束/完毕
        if self.match(TokenType.KEYWORD, '结束') or self.match(TokenType.KEYWORD, '完毕'):
            pass
        # 消费可选的。
        if self.match(TokenType.DOT):
            pass
        
        return ForLoop(var, iterable, body)
    
    def parse_friendly_for(self) -> ForLoop:
        """解析友好语法的对于循环：对于i从1到5：...结束"""
        self.consume(TokenType.KEYWORD, '对于', "期望'对于'")
        var = self.consume(TokenType.IDENT, None, "期望循环变量").value
        self.consume(TokenType.KEYWORD, '从', "期望'从'")
        start = self.parse_expression()
        self.consume(TokenType.KEYWORD, '到', "期望'到'")
        end = self.parse_expression()
        self.consume(TokenType.COLON, None, "期望'：'")
        body = self.parse_block()
        # 消费可选的结束/完毕
        if self.match(TokenType.KEYWORD, '结束') or self.match(TokenType.KEYWORD, '完毕'):
            pass

        # 创建范围迭代：range(start, end+1)
        # 使用Call节点表示范围
        range_call = Call('范围', [start, Call('相加', [end, Num(1)])])
        return ForLoop(var, range_call, body)

    def parse_foreach_friendly(self) -> ForLoop:
        """解析友好语法的每次循环：每次i于列表：...结束"""
        self.consume(TokenType.KEYWORD, '每次', "期望'每次'")
        var = self.consume(TokenType.IDENT, None, "期望循环变量").value

        # 检查是"于"还是"从"
        if self.match(TokenType.KEYWORD, '于'):
            # 每次i于列表
            iterable = self.parse_expression()
        elif self.match(TokenType.KEYWORD, '从'):
            # 每次i从1到5
            start = self.parse_expression()
            self.consume(TokenType.KEYWORD, '到', "期望'到'")
            end = self.parse_expression()
            # 创建范围迭代：range(start, end+1)
            iterable = Call('范围', [start, Call('相加', [end, Num(1)])])
        else:
            raise ParseError("期望'于'或'从'", self.peek().line, self.peek().column)

        self.consume(TokenType.COLON, None, "期望'：'")
        body = self.parse_block()
        # 消费可选的结束/完毕
        if self.match(TokenType.KEYWORD, '结束') or self.match(TokenType.KEYWORD, '完毕'):
            pass
        # 消费可选的。
        if self.match(TokenType.DOT):
            pass

        return ForLoop(var, iterable, body)
    
    def parse_while(self) -> While:
        """解析当循环"""
        self.consume(TokenType.KEYWORD, '循环当', "期望'循环当'")
        condition = self.parse_expression()
        self.consume(TokenType.COLON, None, "期望'：'")
        body = self.parse_block()
        # 消费可选的结束/完毕
        if self.match(TokenType.KEYWORD, '结束') or self.match(TokenType.KEYWORD, '完毕'):
            pass
        # 消费可选的。
        if self.match(TokenType.DOT):
            pass

        return While(condition, body)
    
    def parse_lambda(self) -> Lambda:
        """解析匿名函数"""
        self.consume(TokenType.KEYWORD, '函数', "期望'函数'")

        # 收集参数
        params = []
        while not self.at_end() and self.peek().type == TokenType.IDENT:
            params.append(self.advance().value)

        # 函数体
        if self.match(TokenType.COLON):
            # 块体
            body = self.parse_block()
            # 消费结束关键字
            if self.match(TokenType.KEYWORD, '结束') or self.match(TokenType.KEYWORD, '完毕'):
                pass
        else:
            # 单行体
            body = self.parse_expression()

        return Lambda(params, body)

    def parse_macro(self) -> MacroDef:
        """解析匿名宏定义：宏 参数1 参数2 ：body（用于宏作为值赋给变量时）"""
        self.consume(TokenType.KEYWORD, '宏', "期望'宏'")

        # 收集参数名（直到遇到冒号）
        params = []
        while not self.at_end() and self.peek().type in (TokenType.IDENT, TokenType.VERB):
            params.append(self.advance().value)

        # 消费冒号
        self.consume(TokenType.COLON, None, "期望'：'")

        # 解析宏体
        body = self.parse_block()
        # 消费结束关键字
        if self.match(TokenType.KEYWORD, '结束') or self.match(TokenType.KEYWORD, '完毕'):
            pass

        return MacroDef('', params, body)

    def parse_named_macro(self) -> Define:
        """解析具名宏定义：定义宏 宏名 参数1 参数2 ：body。
        
        语法：定义宏 宏名 [参数...] ：单行表达式。
             或
             定义宏 宏名 [参数...] ：
                 多行块
             结束。
        
        等价于：定义 宏名 = 宏 参数1 参数2 ：body
        会把宏名注册到 VERB_ARITY 中，使解析器后续能正确处理宏调用参数数量。
        """
        self.consume(TokenType.KEYWORD, '定义', "期望'定义'")
        self.consume(TokenType.KEYWORD, '宏', "期望'宏'")

        # 读取宏名
        if self.peek().type not in (TokenType.IDENT, TokenType.VERB):
            raise ParseError("期望宏名标识符", self.peek().line, self.peek().column)
        macro_name = self.advance().value

        # 收集参数名（直到冒号）
        params = []
        while not self.at_end() and self.peek().type in (TokenType.IDENT, TokenType.VERB):
            params.append(self.advance().value)

        # 消费冒号
        self.consume(TokenType.COLON, None, "期望'：'")

        # 解析宏体：单个表达式（消费尾部 。），而不用 parse_block
        # 这样后续语句不会被吸入宏体
        body = self.parse_expression()
        self.match(TokenType.DOT)  # 消费可选的 。

        # 将宏名注册到 VERB_ARITY，以便后续调用正确解析参数
        self.VERB_ARITY[macro_name] = len(params)

        macro_node = MacroDef(macro_name, params, body)
        # 包装为 Define 节点，让 evaluator 将宏闭包绑定到环境
        return Define(macro_name, macro_node)
    
    def parse_try(self) -> Try:
        """解析try-catch-finally语句：试：...捕获 e：...最终：..."""
        # 消费'试'或'尝试'
        self.advance()

        # 消费冒号
        self.consume(TokenType.COLON, None, "期望'：'")

        # 解析try块（可能包含嵌套try）
        try_block = self.parse_block()

        # 消费'捕获'
        self.consume(TokenType.KEYWORD, '捕获', "期望'捕获'")

        # 异常变量
        error_var = self.consume(TokenType.IDENT, None, "期望异常变量").value

        # 消费冒号
        self.consume(TokenType.COLON, None, "期望'：'")

        # 解析catch块（可能包含嵌套try）
        catch_block = self.parse_block()

        # 检查是否有finally块
        finally_block = None
        if self.match(TokenType.KEYWORD, '最终'):
            # 消费冒号
            self.consume(TokenType.COLON, None, "期望'：'")
            # 解析finally块
            finally_block = self.parse_block()

        return Try(try_block, error_var, catch_block, finally_block)

    def parse_return(self) -> ReturnStmt:
        """解析返回语句：返回 <expr>。"""
        self.consume(TokenType.KEYWORD, '返回', "期望'返回'")
        value = self.parse_expression()
        # 消费结尾的。
        if self.match(TokenType.DOT):
            pass
        return ReturnStmt(value)

    def parse_math_statement(self) -> ASTNode:
        """解析算语句：算 <expr>。"""
        self.consume(TokenType.KEYWORD, '算', "期望'算'")
        value = self.parse_expression()
        # 消费结尾的。
        if self.match(TokenType.DOT):
            pass
        return value

    def _is_top_level_keyword(self, token: Token) -> bool:
        """检查是否是顶层关键字（新语句的开始）"""
        if token.type == TokenType.KEYWORD:
            return token.value in (
                '定义', '赋值', '如果', '函数', '宏', '循环当', '遍历', '对于', '每次',
                '返回', '导入', '导出', '结构', '尝试', '试', '注释', '注',
                '算',
            )
        return False

    def parse_scope_block(self) -> Call:
        """解析作用域块：xxx的时候：stmt。stmt。..."""
        # 消费 'xxx的时候'
        self.advance()
        # 消费 '：'
        self.consume(TokenType.COLON, None, "期望'：'")

        body_statements = []

        while not self.at_end():
            token = self.peek()

            # 如果遇到顶层关键字，作用域结束
            if self._is_top_level_keyword(token):
                break

            # 遇到EOF直接结束
            if token.type == TokenType.EOF:
                break

            stmt = self.parse_statement()
            if stmt is not None:
                body_statements.append(stmt)
            else:
                break

        body = Block(body_statements)

        # 创建 Lambda([], body) 并通过 用() 立即调用
        lambda_node = Lambda([], body)
        return Call(Ident('使用'), [lambda_node])

    def parse_block(self) -> Block:
        """解析代码块"""
        statements = []

        while not self.at_end():
            token = self.peek()

            # 块结束
            if token.type == TokenType.DOT:
                break
            if token.type == TokenType.KEYWORD and token.value in ('结束', '完毕', '捕获', '最终', '否则', '不然'):
                break

            stmt = self.parse_statement()
            if stmt is not None:
                statements.append(stmt)

        return Block(statements)
    
    def parse_quote(self) -> Quote:
        """解析引用——两种语法：
        1. 单引号前缀：'表达式
        2. 关键字括号：引用（表达式）
        """
        if self.peek().type == TokenType.QUOTE:
            self.consume(TokenType.QUOTE, None, "期望'''")
        else:
            # 关键字 引用 形式：已由 parse_primary 分发，这里只消费到 expr
            pass
        expr = self.parse_expression()
        # 消费结尾的。
        if self.match(TokenType.DOT):
            pass
        return Quote(expr)

    def parse_quasiquote(self) -> 'Quasiquote':
        """解析反引用模板：模板（表达式）"""
        expr = self.parse_expression()
        return Quasiquote(expr)

    def parse_unquote(self) -> 'Unquote':
        """解析插值：嵌入（表达式）"""
        expr = self.parse_expression()
        return Unquote(expr)

    def parse_unquote_splicing(self) -> 'UnquoteSplicing':
        """解析展开插值：展开嵌入（表达式）"""
        expr = self.parse_expression()
        return UnquoteSplicing(expr)
    
    def parse_expression(self) -> ASTNode:
        """解析表达式"""
        # 使用递归下降解析，支持运算符优先级
        # 优先级从低到高：
        #   比较（大/小/等）→ 加减（加/减）→ 乘除（乘/除）→ 幂（幂）→ 原子
        return self.parse_comparison()

    def parse_comparison(self) -> ASTNode:
        """解析比较运算（低优先级）"""
        left = self.parse_additive()

        while not self.at_end() and self.peek().type in (
            TokenType.GT, TokenType.LT,
            TokenType.GE, TokenType.LE,
            TokenType.EQ, TokenType.NE,
        ):
            op_token = self.advance()
            op = op_token.value
            right = self.parse_additive()

            # 将比较符号映射为中文比较动词
            op_to_verb = {
                '>': '大于', '<': '小于',
                '>=': '大于等于', '<=': '小于等于',
                '==': '等于', '!=': '不等',
            }
            verb = op_to_verb.get(op, op)
            left = Call(Ident(verb), [left, right])

        return left

    def parse_additive(self) -> ASTNode:
        """解析加减法（最低优先级）"""
        left = self.parse_multiplicative()

        while not self.at_end() and self.peek().type in (TokenType.PLUS, TokenType.MINUS):
            op_token = self.advance()
            op = op_token.value
            right = self.parse_multiplicative()

            # 将内联运算符转换为对应的中文动词调用
            op_to_verb = {'+': '相加', '-': '相减'}
            verb = op_to_verb.get(op, op)
            left = Call(Ident(verb), [left, right])

        # 检查是否是标识符函数调用（如 dbl 5）
        # 注意：只在非动词参数内部触发，避免误吞
        if isinstance(left, Ident) and not self._in_call and not self.at_end() and not self.is_blocker():
            next_token = self.peek()
            # 如果后面跟着参数，则解析为函数调用
            # 添加MATH类型支持，允许 fact $(n-1) 这样的调用
            if next_token.type in (TokenType.NUM, TokenType.IDENT, TokenType.STR, TokenType.BOOL, TokenType.LPAREN, TokenType.CLBRACKET, TokenType.MATH):
                args = []
                # 智能参数收集策略：
                # 1. 贪婪收集所有参数
                # 2. 遇到动词时停止（动词有明确arity）
                # 3. 遇到管道符号时停止
                # 4. 遇到结束符时停止
                while not self.at_end() and not self.is_blocker():
                    next_token = self.peek()
                    # 遇到动词，停止收集（动词会自己处理参数）
                    if next_token.type == TokenType.VERB:
                        break
                    # 遇到管道符号，停止收集
                    if next_token.type == TokenType.COMMA:
                        break
                    # 收集参数
                    if next_token.type in (TokenType.NUM, TokenType.IDENT, TokenType.STR, TokenType.BOOL, TokenType.LPAREN, TokenType.CLBRACKET, TokenType.MATH):
                        args.append(self.parse_primary())
                    else:
                        break
                left = Call(left, args)

        # 检查后面是否有动词（动词吞噬）
        while not self.at_end() and self.peek().type == TokenType.VERB:
            verb = self.advance().value
            arity = self.VERB_ARITY.get(verb, 1)

            # 收集参数
            args = [left]  # 第一个参数是左边的表达式

            if arity == -1:
                # 可变参数
                while not self.is_blocker() and not self.match(TokenType.COMMA):
                    # 使用parse_additive而不是parse_primary，以支持函数调用
                    arg = self.parse_additive()
                    args.append(arg)
            else:
                # 固定参数（还需要arity-1个参数）
                for _ in range(arity - 1):
                    if self.is_blocker() or self.peek().type == TokenType.COMMA:
                        break
                    # 使用parse_additive而不是parse_primary，以支持函数调用
                    arg = self.parse_additive()
                    args.append(arg)

            left = Call(Ident(verb), args)

        # 处理管道
        while not self._in_call and self.match(TokenType.COMMA):
            right = self.parse_primary()
            left = Pipeline(left, right)

        return left

    def parse_multiplicative(self) -> ASTNode:
        """解析乘除法（中等优先级）"""
        left = self.parse_power()

        while not self.at_end() and self.peek().type in (TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            op_token = self.advance()
            op = op_token.value
            right = self.parse_power()

            # 将内联运算符转换为对应的中文动词调用
            op_to_verb = {'*': '相乘', '/': '相除', '%': '取余'}
            verb = op_to_verb.get(op, op)
            left = Call(Ident(verb), [left, right])

        return left

    def parse_power(self) -> ASTNode:
        """解析幂运算（最高优先级，右结合）"""
        left = self.parse_primary()

        if not self.at_end() and self.peek().type in (TokenType.CARET, TokenType.STAR):
            # 检查是否是 ** 幂运算
            if self.peek().type == TokenType.STAR and self.peek().value == '**':
                op_token = self.advance()
                right = self.parse_power()  # 右结合
                left = Call(Ident('乘方'), [left, right])
            elif self.peek().type == TokenType.CARET:
                op_token = self.advance()
                right = self.parse_power()  # 右结合
                left = Call(Ident('乘方'), [left, right])

        return left
    
    def parse_primary(self) -> ASTNode:
        """解析基本表达式"""
        token = self.peek()

        # 数字
        if token.type == TokenType.NUM:
            self.advance()
            return Num(token.value)

        # 字符串
        if token.type == TokenType.STR:
            self.advance()
            return Str(token.value)

        # 布尔值
        if token.type == TokenType.BOOL:
            self.advance()
            if token.value is None:
                return Nil()
            return Bool(token.value)

        # 数学表达式
        if token.type == TokenType.MATH:
            self.advance()
            return MathExpr(token.value)

        # Python代码块
        if token.type == TokenType.PYTHON:
            self.advance()
            return PythonCode(token.value)

        # 引用（单引号前缀）
        if token.type == TokenType.QUOTE:
            return self.parse_quote()

        # 引用关键字形式：引用（expr）
        if token.type == TokenType.KEYWORD and token.value == '引用':
            self.advance()  # 消费 引用
            # 支持括号包裹：引用（expr）或直接 引用 expr
            if self.peek().type == TokenType.LPAREN:
                self.advance()  # 消费 (
                expr = self.parse_expression()
                self.consume(TokenType.RPAREN, None, "期望')'")
            else:
                expr = self.parse_expression()
            return Quote(expr)

        # 反引用模板：模板（expr）
        if token.type == TokenType.KEYWORD and token.value == '模板':
            self.advance()  # 消费 模板
            if self.peek().type == TokenType.LPAREN:
                self.advance()
                expr = self.parse_expression()
                self.consume(TokenType.RPAREN, None, "期望')'")
            else:
                expr = self.parse_expression()
            return Quasiquote(expr)

        # 插值：嵌入（expr）
        if token.type == TokenType.KEYWORD and token.value == '嵌入':
            self.advance()  # 消费 嵌入
            if self.peek().type == TokenType.LPAREN:
                self.advance()
                expr = self.parse_expression()
                self.consume(TokenType.RPAREN, None, "期望')'")
            else:
                expr = self.parse_expression()
            return Unquote(expr)

        # 展开插值：展开嵌入（expr）
        if token.type == TokenType.KEYWORD and token.value == '展开嵌入':
            self.advance()  # 消费 展开嵌入
            if self.peek().type == TokenType.LPAREN:
                self.advance()
                expr = self.parse_expression()
                self.consume(TokenType.RPAREN, None, "期望')'")
            else:
                expr = self.parse_expression()
            return UnquoteSplicing(expr)

        # 括号表达式
        if token.type == TokenType.LPAREN:
            self.advance()  # 消费 (
            expr = self.parse_expression()  # 递归解析表达式
            self.consume(TokenType.RPAREN, None, "期望')'")  # 消费 )
            return expr

        # 中文方括号列表
        if token.type == TokenType.CLBRACKET:
            self.advance()  # 消费 【
            # 解析列表元素
            elements = []
            while not self.at_end() and self.peek().type != TokenType.CRBRACKET:
                elem = self.parse_primary()  # 使用parse_primary而不是parse_expression
                elements.append(elem)
                # 消费逗号（如果有）
                if self.match(TokenType.COMMA):
                    pass
            self.consume(TokenType.CRBRACKET, None, "期望'】'")  # 消费 】
            return Call('列表', elements)

        # 负号关键字
        if token.type == TokenType.KEYWORD and token.value == '取负':
            self.advance()  # 消费"负"
            operand = self.parse_primary()
            return Call('取负', [operand])

        # 负数（-开头）
        if token.type == TokenType.MINUS:
            self.advance()  # 消费 -
            # 检查后面是否是数字或标识符
            next_token = self.peek()
            if next_token.type == TokenType.NUM:
                num = self.advance()
                return Num(-num.value)
            elif next_token.type == TokenType.IDENT:
                # -x 转换为 取负x
                ident = self.parse_primary()
                return Call('取负', [ident])
            else:
                raise ParseError("期望数字或标识符", token.line, token.column)
            self.advance()
            return PythonCode(token.value)
        
        # 标识符（可能被分割）
        if token.type == TokenType.IDENT:
            # 收集可能被分割的标识符
            name_parts = [self.advance().value]

            # 检查后面是否跟着动词，如果是且不是阻断符，可能是被分割的标识符
            while not self.at_end() and self.peek().type == TokenType.VERB:
                # 检查是否为阻断符
                if self.is_blocker():
                    break

                # 检查下一个Token是否可能是参数
                # 如果动词后面跟着标识符或数字，说明动词是操作符，不是标识符的一部分
                next_pos = self.pos + 1
                if next_pos < len(self.tokens):
                    next_token = self.tokens[next_pos]
                    if next_token.type in (TokenType.IDENT, TokenType.NUM, TokenType.VERB):
                        # 可能是操作符，停止合并
                        break

                # 否则，合并标识符
                name_parts.append(self.advance().value)

            name = ''.join(name_parts)

            # 检查是否为数组索引：Ident[expr]
            if not self.at_end() and self.peek().type == TokenType.LBRACKET:
                self.advance()  # 消耗 [
                index = self.parse_expression()
                self.consume(TokenType.RBRACKET, None, "期望']'")
                return Call(Ident('取'), [Ident(name), index])

            # 检查是否为函数调用：Ident(expr, expr, ...)
            if not self.at_end() and self.peek().type == TokenType.LPAREN:
                self.advance()  # 消耗 (
                call_args = []
                saved_in_call = self._in_call
                self._in_call = True  # 阻止管道吞噬参数分隔符
                while not self.at_end() and self.peek().type != TokenType.RPAREN:
                    if self.peek().type == TokenType.COMMA:
                        self.advance()  # 消耗逗号
                        continue
                    arg = self.parse_expression()
                    call_args.append(arg)
                self._in_call = saved_in_call
                self.consume(TokenType.RPAREN, None, "期望')'")
                return Call(Ident(name), call_args)

            return Ident(name)
        
        # 动词调用
        if token.type == TokenType.VERB:
            return self.parse_call()
        
        # 副词调用
        if token.type == TokenType.ADVERB:
            return self.parse_adverb_call()
        
        # 函数定义
        if token.type == TokenType.KEYWORD and token.value == '函数':
            return self.parse_lambda()

        # 宏定义
        if token.type == TokenType.KEYWORD and token.value == '宏':
            return self.parse_macro()

        # 条件表达式
        if token.type == TokenType.KEYWORD and token.value == '如果':
            return self.parse_if()

        raise ParseError(f"意外的Token: {token}", token.line, token.column)
    
    def parse_call(self) -> Call:
        """解析动词调用"""
        verb_token = self.advance()
        verb = verb_token.value
        
        # 获取元数
        arity = self.VERB_ARITY.get(verb, 1)
        
        # 收集参数
        args = []
        
        if arity == -1:
            # 可变参数，吞噬到阻断符
            while not self.is_blocker():
                arg = self.parse_primary()
                args.append(arg)
        else:
            # 固定参数数量
            saved_in_call = self._in_call
            self._in_call = True
            for _ in range(arity):
                if self.is_blocker():
                    break
                arg = self.parse_expression()
                args.append(arg)
            self._in_call = saved_in_call
        
        # 将verb包装为Ident节点（同像性支持）
        return Call(Ident(verb), args)
    
    def parse_adverb_call(self) -> Call:
        """解析副词调用"""
        adverb_token = self.advance()
        adverb = adverb_token.value
        
        # 副词需要一个动词作为参数
        if self.peek().type == TokenType.VERB:
            verb = self.advance().value
            arity = self.VERB_ARITY.get(verb, 1)
            
            # 收集动词参数
            verb_args = []
            for _ in range(arity):
                if self.is_blocker():
                    break
                arg = self.parse_primary()
                verb_args.append(arg)
            
            # 构建动词调用
            verb_call = Call(Ident(verb), verb_args)
            
            # 副词调用（参数：动词调用）
            return Call(Ident(adverb), [verb_call])
        
        # 如果不是动词，则作为普通调用
        arg = self.parse_primary()
        return Call(Ident(adverb), [arg])
    
    def is_blocker(self) -> bool:
        """检查是否为阻断符"""
        token = self.peek()
        
        # EOF
        if token.type == TokenType.EOF:
            return True
        
        # 标点符号
        if token.type in (TokenType.DOT, TokenType.COMMA, TokenType.COLON):
            return True
        
        # 关键字
        if token.type == TokenType.KEYWORD:
            return token.value in ('那么', '就', '否则', '不然', '结束', '完毕')
        
        return False
    
    def peek(self) -> Token:
        """查看当前Token"""
        if self.pos >= len(self.tokens):
            return self.tokens[-1]  # EOF
        return self.tokens[self.pos]
    
    def advance(self) -> Token:
        """前进一个Token"""
        token = self.peek()
        if not self.at_end():
            self.pos += 1
        return token
    
    def match(self, type: TokenType, value: any = None) -> bool:
        """匹配Token"""
        if self.at_end():
            return False
        
        token = self.peek()
        if token.type != type:
            return False
        
        if value is not None and token.value != value:
            return False
        
        self.advance()
        return True
    
    def consume(self, type: TokenType, value: any, message: str) -> Token:
        """消费Token"""
        if self.match(type, value):
            return self.tokens[self.pos - 1]
        
        token = self.peek()
        raise ParseError(message, token.line, token.column)
    
    def at_end(self) -> bool:
        """是否到达末尾"""
        return self.peek().type == TokenType.EOF


def parse(source) -> Program:
    """解析函数"""
    from .lexer import Lexer
    from .pre_tokenizer import Token
    
    # 如果输入是Token列表，直接使用
    if isinstance(source, list) and all(isinstance(t, Token) for t in source):
        tokens = source
    else:
        # 否则假设是字符串，进行词法分析
        lexer = Lexer(source)
        tokens = lexer.tokenize()
    
    parser = Parser(tokens)
    return parser.parse()


# 测试代码
if __name__ == '__main__':
    test_cases = [
        "定x=5。",
        "定y=5加3。",
        "列1 2 3，皆乘2。",
        "若x大y则x否则y。",
        "定平方=函x乘x x。",
    ]
    
    for source in test_cases:
        print(f"\n源码: {source}")
        try:
            ast = parse(source)
            print(ast_to_string(ast))
        except Exception as e:
            print(f"错误: {e}")

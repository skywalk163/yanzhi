# -*- coding: utf-8 -*-
"""知行语言 LSP 服务器

基于 pygls 框架实现 LSP 协议，提供：
- 诊断（语法错误提示）
- 补全（变量名、动词名）
- 悬停提示（函数签名）
"""
from __future__ import annotations

import sys
import re
from typing import Any

from yanzhi.compiler.parser import parse
from yanzhi.errors import ParseError
from yanzhi.stdlib.loader import get_all_lib_names

# 预编译正则
_CJK_IDENT_RE = re.compile(r'([\u4e00-\u9fff]+|[a-zA-Z_]\w*)$')
_CJK_IDENT_FIND_RE = re.compile(r'([\u4e00-\u9fff]+|[a-zA-Z_]\w*)')
_VAR_DEF_RE = re.compile(r'定([\u4e00-\u9fff\w]+)\s*=')


def diagnose(source: str, uri: str = '') -> list[dict]:
    """诊断源码，返回 LSP Diagnostic 列表"""
    diagnostics = []
    try:
        parse(source)
    except ParseError as e:
        line = getattr(e, 'line', 0) or 0
        col = getattr(e, 'col', 0) or 0
        diag = {
            'range': {
                'start': {'line': max(line - 1, 0), 'character': max(col - 1, 0)},
                'end': {'line': max(line - 1, 0), 'character': max(col, 1)},
            },
            'severity': 1,
            'message': str(e),
            'source': 'zhixing',
        }
        diagnostics.append(diag)
    except Exception as e:
        diag = {
            'range': {
                'start': {'line': 0, 'character': 0},
                'end': {'line': 0, 'character': 1},
            },
            'severity': 1,
            'message': f"内部错误: {e}",
            'source': 'zhixing',
        }
        diagnostics.append(diag)
    return diagnostics


def complete(source: str, line: int, character: int) -> list[dict]:
    """补全建议，返回 LSP CompletionItem 列表"""
    items = []

    lines = source.split('\n')
    if line < len(lines):
        prefix = lines[line][:character]
    else:
        prefix = ''

    # 提取正在输入的标识符
    match = _CJK_IDENT_RE.search(prefix)
    partial = match.group(0) if match else ''

    # 1. 内置动词补全
    lib_names = get_all_lib_names()
    for name in sorted(lib_names):
        if not partial or name.startswith(partial):
            items.append({'label': name, 'kind': 3, 'detail': '内置动词'})

    # 2. 关键字补全
    keywords = ['定义', '如果', '那么', '否则', '函数', '为', '映射', '过滤',
                '循环当', '遍', '试', '捕获', '抛', '终', '返', '宏', '导出']
    for kw in keywords:
        if not partial or kw.startswith(partial):
            items.append({'label': kw, 'kind': 14, 'detail': '关键字'})

    # 3. 变量名补全
    for m in _VAR_DEF_RE.finditer(source):
        var_name = m.group(1)
        if var_name and (not partial or var_name.startswith(partial)):
            items.append({'label': var_name, 'kind': 6, 'detail': '变量'})

    return items


def hover(source: str, line: int, character: int) -> dict | None:
    """悬停提示，返回 LSP Hover"""
    lines = source.split('\n')
    if line >= len(lines):
        return None

    current_line = lines[line]

    # 找到包含 character 位置的标识符
    word = None
    for match in _CJK_IDENT_FIND_RE.finditer(current_line):
        start, end = match.span()
        if start <= character <= end:
            word = match.group(0)
            break

    if word is None:
        return None

    # 查找动词签名
    lib_names = get_all_lib_names()
    if word in lib_names:
        return {
            'contents': {
                'kind': 'markdown',
                'value': f'**{word}** - 内置动词\n\n知行标准库函数',
            }
        }

    # 查找关键字
    keywords_info = {
        '定义': '定义变量/函数: 定义 名=值。',
        '如果': '条件判断: 如果 条件 那么 真分支 否则 假分支。',
        '函数': '函数定义: 函数 参数 函数体。',
        '映射': '映射: 列表 映射 函数。',
        '过滤': '过滤: 列表 过滤 谓词。',
        '试': '异常处理: 试：块。捕获 变量：块。',
        '抛': '抛出异常: 抛 值。',
        '返': '返回: 返 值。',
        '宏': '宏定义: 宏 名 参数 模板。',
    }
    if word in keywords_info:
        return {
            'contents': {
                'kind': 'markdown',
                'value': f'**{word}** - 关键字\n\n{keywords_info[word]}',
            }
        }

    return None


# ==================== LSP 服务器（基于 pygls）====================

def create_server():
    """创建 LSP 服务器（需要 pygls）"""
    try:
        from pygls.server import LanguageServer
        from lsprotocol import types as lsp_types
    except ImportError:
        print("错误: 需要安装 pygls 和 lsprotocol", file=sys.stderr)
        print("  pip install pygls lsprotocol", file=sys.stderr)
        sys.exit(1)

    server = LanguageServer("zhixing-lsp", "v0.1.0")

    @server.feature(lsp_types.TEXT_DOCUMENT_DID_OPEN)
    def did_open(params):
        source = params.text_document.text
        uri = params.text_document.uri
        server.publish_diagnostics(uri, diagnose(source, uri))

    @server.feature(lsp_types.TEXT_DOCUMENT_DID_CHANGE)
    def did_change(params):
        uri = params.text_document.uri
        doc = server.workspace.get_text_document(uri)
        server.publish_diagnostics(uri, diagnose(doc.source, uri))

    @server.feature(
        lsp_types.TEXT_DOCUMENT_COMPLETION,
        lsp_types.CompletionOptions(trigger_characters=['定', '若', '函'])
    )
    def completions(params):
        uri = params.text_document.uri
        doc = server.workspace.get_text_document(uri)
        items = complete(doc.source, params.position.line, params.position.character)
        return lsp_types.CompletionList(
            is_incomplete=False,
            items=[lsp_types.CompletionItem(label=i['label'], kind=i.get('kind'), detail=i.get('detail')) for i in items]
        )

    @server.feature(lsp_types.TEXT_DOCUMENT_HOVER)
    def hover_handler(params):
        uri = params.text_document.uri
        doc = server.workspace.get_text_document(uri)
        result = hover(doc.source, params.position.line, params.position.character)
        if result:
            return lsp_types.Hover(
                contents=lsp_types.MarkupContent(kind=lsp_types.MarkupKind.Markdown, value=result['contents']['value'])
            )
        return None

    return server


def run_lsp():
    """启动 LSP 服务器"""
    server = create_server()
    server.start_io()


if __name__ == '__main__':
    run_lsp()

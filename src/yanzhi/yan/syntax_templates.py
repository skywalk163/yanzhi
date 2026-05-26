"""
言知·言律句式模板引擎
将中文自然句式展开为 yanzhi 标准 token 序列

支持的句式 (Phase 1):
  - 当...就... → 若...则...  (条件触发)
  - 每隔 N 单位，做 X → 当 真: X (定时循环)
  - 要是...就...；否则... → 若...则...否则...  (条件分支)

用法: 外部通过 try_rewrite(tokens, pos) 接口调用,
      返回 (rewritten_tokens, consumed_count) 或 None。
"""
from typing import List, Optional, Tuple, Any
from ..compiler.pre_tokenizer import Token, TokenType


def try_rewrite(tokens: List[Token], pos: int) -> Optional[Tuple[List[Token], int]]:
    """尝试在 tokens[pos:] 位置匹配言律句式模板。

    Args:
        tokens: 完整 token 列表
        pos: 当前解析位置

    Returns:
        (rewritten_tokens, consumed_count) —— consumed_count 表示原 tokens 中被
        模式吞掉的个数（不含句号）；rewritten_tokens 是要替换进去的标准化序列。
        匹配失败返回 None。
    """
    if pos >= len(tokens):
        return None

    token = tokens[pos]
    if token.type != TokenType.KEYWORD:
        return None

    if token.value == '循环当':
        return _try_when_pattern(tokens, pos)
    elif token.value == '每隔':
        return _try_interval_pattern(tokens, pos)
    elif token.value == '要是':
        return _try_ifelse_pattern(tokens, pos)

    return None


# ---------------------------------------------------------------------------
# 当…就… → 若…则…
# ---------------------------------------------------------------------------

def _try_when_pattern(tokens: List[Token], pos: int) -> Optional[Tuple[List[Token], int]]:
    """
    匹配: KEYWORD(循环当) <条件> [COMMA] KEYWORD(就) <动作>
    展开: KEYWORD(如果) <条件> KEYWORD(那么) <动作>
    """
    start = pos
    pos += 1  # skip KEYWORD(循环当)

    # ---- 条件部分 (到 COMMA 或 KEYWORD(就) 为止) ----
    condition_tokens = []
    while pos < len(tokens):
        t = tokens[pos]
        if t.type == TokenType.COMMA:
            pos += 1          # 吞掉逗号
            break
        if t.type == TokenType.KEYWORD and t.value == '就':
            break
        if t.type in (TokenType.DOT, TokenType.EOF):
            return None       # 不应在此结束
        condition_tokens.append(t)
        pos += 1

    # ---- 必须看到 KEYWORD(就) ----
    if pos >= len(tokens):
        return None
    if not (tokens[pos].type == TokenType.KEYWORD and tokens[pos].value == '就'):
        return None
    pos += 1  # 吞掉 '就'

    # ---- 动作部分 (到 DOT / EOF 为止) ----
    action_tokens = []
    while pos < len(tokens):
        t = tokens[pos]
        if t.type in (TokenType.DOT, TokenType.EOF):
            break
        action_tokens.append(t)
        pos += 1

    # 确保后面有 DOT (避免吃掉后续语句)
    if pos >= len(tokens) or tokens[pos].type != TokenType.DOT:
        return None

    consumed = pos - start

    # 展开为 如果 <条件> 那么 <动作>  (不包含句号, 让上层 parser 处理)
    rewritten: List[Token] = [
        Token(TokenType.KEYWORD, '如果'),
        *condition_tokens,
        Token(TokenType.KEYWORD, '那么'),
        *action_tokens,
    ]
    return (rewritten, consumed)


# ---------------------------------------------------------------------------
# 每隔 N 单位 → 循环当 真: (无限循环)
# ---------------------------------------------------------------------------

def _try_interval_pattern(tokens: List[Token], pos: int) -> Optional[Tuple[List[Token], int]]:
    """
    匹配: KEYWORD(每隔) NUM <单位> [COMMA] <动作>
    展开: KEYWORD(当) BOOL(True) COLON <动作>  KEYWORD(结束)
    """
    start = pos
    pos += 1  # skip KEYWORD(每隔)

    # ---- 数字 ----
    if pos >= len(tokens) or tokens[pos].type != TokenType.NUM:
        return None
    # num_value = tokens[pos].value   # 暂时保留, 后续可用于 sleep 时长
    pos += 1

    # ---- 单位 (IDENT) ----
    if pos >= len(tokens) or tokens[pos].type != TokenType.IDENT:
        return None
    pos += 1

    # ---- 可选逗号 ----
    if pos < len(tokens) and tokens[pos].type == TokenType.COMMA:
        pos += 1

    # ---- 动作部分 ----
    action_tokens = []
    while pos < len(tokens):
        t = tokens[pos]
        if t.type in (TokenType.DOT, TokenType.EOF):
            break
        action_tokens.append(t)
        pos += 1

    if pos >= len(tokens) or tokens[pos].type != TokenType.DOT:
        return None

    consumed = pos - start

    # 展开为 循环当 真: <动作> 结束
    rewritten: List[Token] = [
        Token(TokenType.KEYWORD, '循环当'),
        Token(TokenType.BOOL, True),
        Token(TokenType.COLON, '：'),
        *action_tokens,
        Token(TokenType.KEYWORD, '结束'),
    ]
    return (rewritten, consumed)


# ---------------------------------------------------------------------------
# 要是…就…否则… → 若…则…否则…
# ---------------------------------------------------------------------------

def _try_ifelse_pattern(tokens: List[Token], pos: int) -> Optional[Tuple[List[Token], int]]:
    """
    匹配: KEYWORD(要是) <条件> KEYWORD(就) <动作> [KEYWORD(否则) <备选>]
    展开: KEYWORD(若) <条件> KEYWORD(则) <动作> [KEYWORD(否则) <备选>]
    """
    start = pos
    pos += 1  # skip KEYWORD(要是)

    # ---- 条件 ----
    condition_tokens = []
    while pos < len(tokens):
        t = tokens[pos]
        # 跳过可选逗号
        if t.type == TokenType.COMMA:
            pos += 1
            continue
        if t.type == TokenType.KEYWORD and t.value == '就':
            break
        if t.type in (TokenType.DOT, TokenType.EOF):
            return None
        condition_tokens.append(t)
        pos += 1

    if pos >= len(tokens):
        return None
    if not (tokens[pos].type == TokenType.KEYWORD and tokens[pos].value == '就'):
        return None
    pos += 1  # 吞掉 '就'

    # ---- 动作 ----
    action_tokens = []
    while pos < len(tokens):
        t = tokens[pos]
        if t.type == TokenType.KEYWORD and t.value == '否则':
            break
        if t.type in (TokenType.DOT, TokenType.EOF):
            break
        action_tokens.append(t)
        pos += 1

    # ---- 否则 分支 (可选) ----
    else_tokens = []
    if pos < len(tokens) and tokens[pos].type == TokenType.KEYWORD and tokens[pos].value == '否则':
        pos += 1  # 吞掉 '否则'
        while pos < len(tokens):
            t = tokens[pos]
            if t.type in (TokenType.DOT, TokenType.EOF):
                break
            else_tokens.append(t)
            pos += 1

    if pos >= len(tokens) or tokens[pos].type != TokenType.DOT:
        return None

    consumed = pos - start

    rewritten: List[Token] = [
        Token(TokenType.KEYWORD, '如果'),
        *condition_tokens,
        Token(TokenType.KEYWORD, '那么'),
        *action_tokens,
    ]
    if else_tokens:
        rewritten.append(Token(TokenType.KEYWORD, '否则'))
        rewritten.extend(else_tokens)

    return (rewritten, consumed)

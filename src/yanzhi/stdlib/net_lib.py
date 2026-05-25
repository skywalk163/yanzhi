# -*- coding: utf-8 -*-
"""网络库

基于 urllib，提供 HTTP 请求能力：
- GET/POST 请求
- URL 编解码
"""
from __future__ import annotations

import json as _json
import urllib.request
import urllib.parse
import urllib.error
from typing import Any, Callable


def _http_get(url: str, headers: dict | None = None) -> str:
    """HTTP GET 请求"""
    req = urllib.request.Request(url)
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.read().decode('utf-8')
    except urllib.error.URLError as e:
        raise RuntimeError(f"HTTP GET 错误: {e}")


def _http_post(url: str, data: str, headers: dict | None = None) -> str:
    """HTTP POST 请求"""
    body = data.encode('utf-8') if isinstance(data, str) else data
    req = urllib.request.Request(url, data=body, method='POST')
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.read().decode('utf-8')
    except urllib.error.URLError as e:
        raise RuntimeError(f"HTTP POST 错误: {e}")


def _http_post_json(url: str, data: Any) -> str:
    """HTTP POST JSON 请求"""
    body = _json.dumps(data, ensure_ascii=False).encode('utf-8')
    req = urllib.request.Request(url, data=body, method='POST')
    req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.read().decode('utf-8')
    except urllib.error.URLError as e:
        raise RuntimeError(f"HTTP POST JSON 错误: {e}")


def _url_encode(s: str) -> str:
    """URL 编码"""
    return urllib.parse.quote(s)


def _url_decode(s: str) -> str:
    """URL 解码"""
    return urllib.parse.unquote(s)


def _url_parse(url: str) -> dict:
    """解析 URL"""
    result = urllib.parse.urlparse(url)
    return {
        '协议': result.scheme,
        '主机': result.netloc,
        '路径': result.path,
        '参数': result.params,
        '查询': result.query,
        '片段': result.fragment,
    }


# 标准库注册字典
LIBS: dict[str, tuple[int, Callable]] = {
    '取':       (1, _http_get),        # HTTP GET
    '提交':     (2, _http_post),       # HTTP POST
    '提交JSON': (2, _http_post_json),  # HTTP POST JSON
    '编码URL':  (1, _url_encode),      # URL 编码
    '解码URL':  (1, _url_decode),      # URL 解码
    '解析URL':  (1, _url_parse),       # 解析 URL
}

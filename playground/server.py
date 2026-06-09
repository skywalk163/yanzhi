#!/usr/bin/env python3
"""言知 Playground v2 — 本地 Web 服务器

启动：python playground/server.py [port]
访问：http://localhost:3000

参考设计：
  - wenyan-lang Online IDE (ide.wy-lang.org)
  - CodeMirror 6 playgrounds
"""

import sys
import os
import io
import json
import mimetypes
import time
import zlib
import base64

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(PROJECT_ROOT, 'src')
sys.path.insert(0, SRC_DIR)

from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse

from yanzhi.compiler.lexer import lex
from yanzhi.compiler.parser import parse
from yanzhi.runtime.compiler_bc import compile_to_bytecode
from yanzhi.compiler.expander import MacroExpander
from yanzhi.runtime.macro_env import MacroEnvironment
from yanzhi.yan.dsl_factory import register_builtins
from yanzhi.runtime.vm import VM
from yanzhi.compiler.errors import YanError
from yanzhi.compiler.pre_tokenizer import TokenType


class PlaygroundHandler(SimpleHTTPRequestHandler):

    project_root = PROJECT_ROOT
    static_dir = os.path.join(PROJECT_ROOT, 'playground', 'static')
    examples_dir = os.path.join(PROJECT_ROOT, 'examples')

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # --- API: 示例列表 ---
        if path == '/api/examples':
            return self._list_examples()

        # --- API: 单个示例 ---
        if path.startswith('/api/examples/'):
            name = path[len('/api/examples/'):]
            return self._get_example(name)

        # --- API: 词法分析（返回 token 详情用于调试）---
        if path == '/api/tokens':
            query = parsed.query
            code = self._get_query_param(query, 'code')
            if code:
                return self._tokenize(code)
            return self._json_response({'error': 'Missing code param'}, 400)

        # --- 静态文件 ---
        if path == '/' or path == '':
            path = '/static/index.html'
        if path.startswith('/static/'):
            rel = path[len('/static/'):]
            file_path = os.path.normpath(os.path.join(self.static_dir, rel))
            if not file_path.startswith(os.path.normpath(self.static_dir)):
                self.send_error(403)
                return
            if os.path.isfile(file_path):
                return self._serve_file(file_path)

        self.send_error(404, 'Not Found')

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # --- API: 运行代码 ---
        if path == '/api/run':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body)
            code = data.get('code', '')
            return self._run_code(code)

        self.send_error(404, 'Not Found')

    # ---- Helpers ----

    def _get_query_param(self, query, key):
        for part in query.split('&'):
            if '=' in part:
                k, v = part.split('=', 1)
                if k == key:
                    return v
        return None

    def _serve_file(self, file_path):
        content_type, _ = mimetypes.guess_type(file_path)
        if content_type is None:
            content_type = 'application/octet-stream'
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
            self.end_headers()
            self.wfile.write(data)
        except IOError:
            self.send_error(404)

    def _list_examples(self):
        examples = []
        try:
            for fname in sorted(os.listdir(self.examples_dir)):
                if fname.endswith('.yan'):
                    path = os.path.join(self.examples_dir, fname)
                    size = os.path.getsize(path)
                    examples.append({'name': fname, 'size': size})
        except FileNotFoundError:
            pass
        self._json_response({'examples': examples})

    def _get_example(self, name):
        safe_name = os.path.basename(name)
        file_path = os.path.join(self.examples_dir, safe_name)
        if not os.path.isfile(file_path) or not safe_name.endswith('.yan'):
            self.send_error(404, 'Example not found')
            return
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self._json_response({'name': safe_name, 'content': content})
        except IOError as e:
            self._json_response({'error': str(e)}, status=500)

    def _tokenize(self, code):
        """词法分析，返回 token 序列（含行号列号）"""
        try:
            tokens = lex(code)
            token_list = []
            for t in tokens:
                token_list.append({
                    'type': t.type.name,
                    'value': t.value,
                    'line': t.line,
                    'col': t.column,
                })
            self._json_response({'tokens': token_list})
        except Exception as e:
            self._json_response({'error': str(e)}, 400)

    def _run_code(self, code):
        """执行言知代码"""
        stdout_capture = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = stdout_capture

        result = None
        error = None
        exec_time = 0
        token_count = 0
        instr_count = 0

        try:
            start = time.perf_counter()
            tokens = lex(code)
            token_count = len(tokens)
            ast = parse(tokens)

            # 宏展开（支持成语/宏调用）
            macro_env = MacroEnvironment()
            temp_expander = MacroExpander(macro_env)
            register_builtins(temp_expander)
            ast = temp_expander.expand(ast)

            chunk = compile_to_bytecode(ast)
            instr_count = len(chunk.instructions)
            vm = VM()
            result = vm.run(chunk)
            exec_time = (time.perf_counter() - start) * 1000  # ms
        except YanError as e:
            error = str(e)
            exec_time = (time.perf_counter() - start) * 1000
        except SyntaxError as e:
            error = f'语法错误: {e}'
        except Exception as e:
            error = f'{type(e).__name__}: {e}'
        finally:
            sys.stdout = old_stdout

        stdout_text = stdout_capture.getvalue()
        if isinstance(result, type(None)):
            serializable_result = None
        elif isinstance(result, (int, float, str, bool)):
            serializable_result = result
        elif isinstance(result, list):
            serializable_result = result
        else:
            serializable_result = str(result)

        self._json_response({
            'stdout': stdout_text,
            'result': serializable_result,
            'error': error,
            'time': round(exec_time, 2),
            'tokens': token_count,
            'instrs': instr_count,
        })

    def _json_response(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False, default=str).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        msg = format % args
        if '/static/' not in msg and '/api/' not in msg:
            pass
        else:
            print(f"[Playground] {msg}")


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
    server = HTTPServer(('', port), PlaygroundHandler)
    print(f"╔═════════════════════════════════════════╗")
    print(f"║  言知语言 Playground v2                 ║")
    print(f"║                                        ║")
    print(f"║  http://localhost:{port}                 ║")
    print(f"║                                        ║")
    print(f"║  特性: CodeMirror 6 | 语法高亮 | 分享  ║")
    print(f"║        执行计时 | Token 预览 | 示例    ║")
    print(f"║                                        ║")
    print(f"║  Ctrl+C 停止服务                       ║")
    print(f"╚═════════════════════════════════════════╝")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务已停止。")
        server.server_close()


if __name__ == '__main__':
    main()

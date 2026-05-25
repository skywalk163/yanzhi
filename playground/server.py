#!/usr/bin/env python3
"""言知 Playground — 本地 Web 服务器

启动：python playground/server.py
访问：http://localhost:3000
"""

import sys
import os
import io
import json
import mimetypes

# 确保能找到 yanzhi 模块
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(PROJECT_ROOT, 'src')
sys.path.insert(0, SRC_DIR)

from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse

# 延迟导入 yanzhi（确保 sys.path 已设）
from yanzhi.compiler.lexer import lex
from yanzhi.compiler.parser import parse
from yanzhi.runtime.compiler_bc import compile_to_bytecode
from yanzhi.runtime.vm import VM
from yanzhi.compiler.errors import YanError


class PlaygroundHandler(SimpleHTTPRequestHandler):
    """自定义 HTTP 处理器"""

    # 项目根目录（用于定位 static/ 和 examples/）
    project_root = PROJECT_ROOT
    static_dir = os.path.join(PROJECT_ROOT, 'playground', 'static')
    examples_dir = os.path.join(PROJECT_ROOT, 'examples')

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # --- API: 获取示例列表 ---
        if path == '/api/examples':
            return self._list_examples()

        # --- API: 获取单个示例 ---
        if path.startswith('/api/examples/'):
            name = path[len('/api/examples/'):]
            return self._get_example(name)

        # --- 静态文件 ---
        # 根路径 -> index.html
        if path == '/' or path == '':
            path = '/static/index.html'

        # 将 /static/... 映射到 static_dir
        if path.startswith('/static/'):
            rel = path[len('/static/'):]
            file_path = os.path.normpath(os.path.join(self.static_dir, rel))
            # 安全检查：必须在 static_dir 内
            if not file_path.startswith(os.path.normpath(self.static_dir)):
                self.send_error(403)
                return
            if os.path.isfile(file_path):
                return self._serve_file(file_path)

        # 未匹配 -> 404
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

    # ---- Handlers ----

    def _serve_file(self, file_path):
        """提供静态文件"""
        content_type, _ = mimetypes.guess_type(file_path)
        if content_type is None:
            content_type = 'application/octet-stream'

        try:
            with open(file_path, 'rb') as f:
                data = f.read()
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except IOError:
            self.send_error(404)

    def _list_examples(self):
        """获取示例文件列表"""
        examples = []
        try:
            for fname in sorted(os.listdir(self.examples_dir)):
                if fname.endswith('.yan'):
                    examples.append(fname)
        except FileNotFoundError:
            pass

        self._json_response({'examples': examples})

    def _get_example(self, name):
        """获取单个示例文件内容"""
        # 安全检查：防止路径遍历
        safe_name = os.path.basename(name)
        file_path = os.path.join(self.examples_dir, safe_name)
        if not os.path.isfile(file_path) or not safe_name.endswith('.yan'):
            self.send_error(404, '示例不存在')
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self._json_response({
                'name': safe_name,
                'content': content,
            })
        except IOError as e:
            self._json_response({'error': str(e)}, status=500)

    def _run_code(self, code):
        """执行言知代码"""
        stdout_capture = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = stdout_capture

        result = None
        error = None

        try:
            # 词法分析
            tokens = lex(code)
            # 语法分析
            ast = parse(tokens)
            # 编译为字节码
            chunk = compile_to_bytecode(ast)
            # 执行（每次新建 VM，隔离环境）
            vm = VM()
            result = vm.run(chunk)
        except YanError as e:
            error = str(e)
        except SyntaxError as e:
            error = f'语法错误: {e}'
        except Exception as e:
            error = f'{type(e).__name__}: {e}'
        finally:
            sys.stdout = old_stdout

        stdout_text = stdout_capture.getvalue()

        # 将 Python 的 None 转为 JS 可理解的 null
        if isinstance(result, type(None)):
            result = None

        self._json_response({
            'stdout': stdout_text,
            'result': result,
            'error': error,
        })

    def _json_response(self, data, status=200):
        """返回 JSON 响应"""
        body = json.dumps(data, ensure_ascii=False, default=str).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        """减少日志噪音"""
        msg = format % args
        if '/static/' not in msg and '/api/' not in msg:
            pass  # 静默处理
        else:
            print(f"[Playground] {msg}")


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
    server = HTTPServer(('127.0.0.1', port), PlaygroundHandler)
    print(f"╔════════════════════════════════════════╗")
    print(f"║   言知语言 Playground                   ║")
    print(f"║                                       ║")
    print(f"║   http://localhost:{port}                ║")
    print(f"║                                       ║")
    print(f"║  Ctrl+C 停止服务                        ║")
    print(f"╚════════════════════════════════════════╝")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务已停止。")
        server.server_close()


if __name__ == '__main__':
    main()

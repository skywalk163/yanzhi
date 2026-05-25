/* === 言知 Playground — 前端逻辑 === */

// === State ===
const state = {
  sidebarOpen: false,
  sidebarTab: 'examples',
  currentFile: null,
  running: false,
};

// === DOM refs ===
const $ = (s) => document.querySelector(s);
const $$ = (s) => document.querySelectorAll(s);

const editor = $('#editor');
const outputBody = $('#output-body');
const runBtn = $('#run-btn');
const clearBtn = $('#clear-btn');
const statusText = $('#status-text');
const statusDot = $('#status-dot');
const sidebar = $('#sidebar');
const sidebarBody = $('#sidebar-body');
const sidebarTabs = $$('.sidebar-tabs button');

// === API ===
async function api(method, path, body) {
  const opts = { method, headers: {} };
  if (body) {
    opts.headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(body);
  }
  const res = await fetch(path, opts);
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
  return res.json();
}

// === Run Code ===
async function runCode() {
  if (state.running) return;
  const code = editor.value.trim();
  if (!code) return;

  state.running = true;
  runBtn.disabled = true;
  runBtn.textContent = '⏳ 运行中…';
  setStatus('运行中…', 'busy');

  outputBody.innerHTML = '';

  try {
    const data = await api('POST', '/api/run', { code });
    
    if (data.stdout) {
      addOutput(data.stdout, 'output-stdout');
    }
    if (data.result !== null && data.result !== undefined) {
      addOutput(`=> ${data.result}`, 'output-result');
    }
    if (data.error) {
      addOutput(`错误: ${data.error}`, 'output-error');
      setStatus('有错误', 'error');
    } else {
      setStatus('执行完成', '');
    }
  } catch (e) {
    addOutput(`请求失败: ${e.message}`, 'output-error');
    setStatus('请求失败', 'error');
  } finally {
    state.running = false;
    runBtn.disabled = false;
    runBtn.textContent = '▶ 运行';
  }
}

function addOutput(text, cls) {
  const div = document.createElement('div');
  div.className = cls || '';
  div.textContent = text;
  outputBody.appendChild(div);
  outputBody.scrollTop = outputBody.scrollHeight;
}

function clearOutput() {
  outputBody.innerHTML = '<div class="output-placeholder">点击 ▶ 运行 或按 Ctrl+Enter 执行代码</div>';
}

function clearEditor() {
  editor.value = '';
  state.currentFile = null;
  updateFileLabel();
}

function setStatus(text, type) {
  statusText.textContent = text;
  statusDot.className = 'status-indicator' + (type ? ' ' + type : '');
}

function updateFileLabel() {
  const label = $('#file-label');
  label.textContent = state.currentFile ? `📄 ${state.currentFile}` : '未命名';
}

// === Sidebar ===
function toggleSidebar(tab) {
  if (state.sidebarOpen && state.sidebarTab === tab) {
    closeSidebar();
    return;
  }
  state.sidebarOpen = true;
  state.sidebarTab = tab;
  sidebar.classList.add('open');
  
  // Highlight active tab
  sidebarTabs.forEach(b => {
    b.classList.toggle('active', b.dataset.tab === tab);
  });
  
  if (tab === 'examples') renderExamples();
  else if (tab === 'docs') renderDocs();
}

function closeSidebar() {
  state.sidebarOpen = false;
  sidebar.classList.remove('open');
}

// === Examples ===
const EXAMPLE_META = {
  'demo.yan': { desc: '言知语言特性总览 — 数学、条件、管道、Lambda、递归、言律句式' },
  'bubblesort.yan': { desc: '冒泡排序 — 使用 若...则：... 语句块语法' },
  'hanoi.yan': { desc: '汉诺塔 — 递归函数 + 则：分支语句块' },
  'pipeline_demo.yan': { desc: '函数式管道 — 皆(map) / 只(filter) / 归(reduce) 组合演示' },
  'quicksort.yan': { desc: '快速排序 — 分治思想 + 函数式列表操作' },
  'turing.yan': { desc: '图灵机模拟器 — 双轨设计，识别 aⁿbⁿ 语言' },
  'webserver.yan': { desc: 'Web 服务器 — 用 Python http.server 提供 HTTP 服务' },
};

async function renderExamples() {
  sidebarBody.innerHTML = '<p style="color:var(--fg2)">加载示例列表中…</p>';
  try {
    const data = await api('GET', '/api/examples');
    const names = data.examples || [];
    sidebarBody.innerHTML = '';
    names.forEach(name => {
      const meta = EXAMPLE_META[name] || { desc: '言知示例文件' };
      const item = document.createElement('div');
      item.className = 'example-item';
      item.innerHTML = `<div class="ex-name">${name}</div><div class="ex-desc">${meta.desc}</div>`;
      item.onclick = () => loadExample(name);
      sidebarBody.appendChild(item);
    });
    if (names.length === 0) {
      sidebarBody.innerHTML = '<p style="color:var(--fg2)">暂无示例文件</p>';
    }
  } catch (e) {
    sidebarBody.innerHTML = `<p style="color:var(--red)">加载失败: ${e.message}</p>`;
  }
}

async function loadExample(name) {
  try {
    const data = await api('GET', `/api/examples/${encodeURIComponent(name)}`);
    editor.value = data.content || '';
    state.currentFile = name;
    updateFileLabel();
    closeSidebar();
    clearOutput();
    setStatus(`已加载: ${name}`, '');
  } catch (e) {
    setStatus(`加载失败: ${e.message}`, 'error');
  }
}

// === Docs ===
const DOCS_HTML = `
<h2>言知语法速查</h2>

<h3>核心哲学：极简关键字，强大扩展</h3>
<p>言知只有 <strong>7 个关键字</strong>（定、设、函、宏、若、则、否则），其余语法由中文虚词+标点模式构成。新增功能永不增加关键字。</p>

<h3>基本语法</h3>
<pre><code>定 x = 5。           # 定义变量（不可变）
定 lst = 列 1 2 3。  # 列表
设 lst[0] = 10。     # 赋值（可变）
印 "你好，言知！"。    # 打印
</code></pre>

<h3>数学表达式</h3>
<p>使用常规数学符号：</p>
<pre><code>印 1 + 2 * 3。        # 7
印 (1 + 2) * 3。      # 9
印 10 / 3。           # 3.333...
定 n = 2 ** 10。      # 1024
</code></pre>

<h3>条件判断</h3>
<pre><code>若 x > 5 则 "大" 否则 "小"。

# 语句块形式（多个语句）
若 x > 5 则：
  印 "x 大于 5"。
  印 "条件成立"。
否则：
  印 "x 不大于 5"。
。
</code></pre>

<h3>循环</h3>
<pre><code>当 条件：
  印 "循环中"。
  ...

# 相当于 while true
当 真：
  印 "无限循环"。
  若 条件 则 跳出。
。
</code></pre>

<h3>函数定义</h3>
<pre><code>定 平方 = 函 n：n * n。。
印 平方 5。            # 25

# 多参数
定 加 = 函 a b：a + b。。
印 加 3 4。            # 7

# 递归
定 阶乘 = 函 n：
  若 n <= 1 则 1 否则 n * 阶乘(n - 1)。
。
</code></pre>

<h3>列表操作</h3>
<pre><code>定 lst = 列 10 20 30 40 50。
印 首 lst。             # 10（第一个元素）
印 余 lst。             # [20, 30, 40, 50]（除第一个外）
印 长 lst。             # 5（长度）
印 lst[0]。             # 10（索引访问）
印 lst[1:3]。           # [20, 30]（切片）
</code></pre>

<h3>函数式管道（言知标志性特性）</h3>
<pre><code>定 data = 列 1 2 3 4 5 6 7 8 9 10。
印 data，皆乘2。        # 映射：[2, 4, 6, 8, 10, 12, 14, 16, 18, 20]
印 data，只大5。        # 过滤：[6, 7, 8, 9, 10]
印 data，归加0。        # 规约求和：55
印 data，皆乘2，只大5，归加0。  # 链式组合：120

# 中缀风格等价写法
印(皆乘2 data)。
印(只大5 data)。
</code></pre>

<h3>言律句式（自然语法）</h3>
<pre><code>当 真，就印 "条件触发"。     # 类似 if true

要是 温度 > 30，就印 "热" 否则 印 "冷"。

# 作用域块 — 用场景描述限定范围
回家的时候：
  印 "进门了"。
  印 "开灯了"。
。
</code></pre>

<h3>双轨设计 — Python 生态调用</h3>
<pre><code># $(...) 表达式嵌入
定 result = $(abs(-5) + 10)。

# {{...}} 多行 Python 代码块
{{
import random
print("随机数:", random.randint(1, 100))
}}
</code></pre>

<h3>动词一览（内置函数）</h3>
<table>
<tr><th>动词</th><th>功能</th><th>示例</th></tr>
<tr><td>印</td><td>打印输出</td><td>印 "hello"</td></tr>
<tr><td>加 / 减 / 乘 / 除</td><td>算术运算</td><td>加 5 3 → 8</td></tr>
<tr><td>列</td><td>创建列表</td><td>列 1 2 3</td></tr>
<tr><td>首 / 余 / 长</td><td>列表操作</td><td>首 [1,2,3] → 1</td></tr>
<tr><td>连</td><td>拼接列表</td><td>连 [1] [2,3]</td></tr>
<tr><td>皆（map）</td><td>映射</td><td>皆乘2 [1,2,3]</td></tr>
<tr><td>只（filter）</td><td>过滤</td><td>只大5 [3,6,9]</td></tr>
<tr><td>归（reduce）</td><td>规约</td><td>归加0 [1,2,3] → 6</td></tr>
<tr><td>并</td><td>zip 合并</td><td>并 [a,b] [1,2]</td></tr>
<tr><td>空</td><td>判空</td><td>空 [] → true</td></tr>
<tr><td>取</td><td>索引（语法糖）</td><td>lst 取 0</td></tr>
<tr><td>大 / 小 / 等</td><td>比较</td><td>大 5 3 → true</td></tr>
</table>

<h3>语句终止符</h3>
<p><code>。</code>（中文句号）是命令式语句（如 <code>定</code>、<code>设</code>、<code>印</code>）的终止符。表达式（如数学计算、函数调用）可以不带句号作为返回值。</p>
<p><code>。</code>（连续两个句号）终止函数体：<code>函 n：n * n。。</code></p>

<h3>关键字速记</h3>
<table>
<tr><th>关键字</th><th>用法</th></tr>
<tr><td>定</td><td>定义变量（绑定值）</td></tr>
<tr><td>设</td><td>赋值（修改变量）</td></tr>
<tr><td>函</td><td>定义函数</td></tr>
<tr><td>宏</td><td>定义宏（编译期展开）</td></tr>
<tr><td>若</td><td>条件判断开始</td></tr>
<tr><td>则</td><td>条件真值分支</td></tr>
<tr><td>否则</td><td>条件假值分支</td></tr>
</table>

<h3>如何退出 REPL</h3>
<p>在 REPL 中输入 <code>退出</code>、<code>quit</code> 或 <code>exit</code>。</p>

<h3>常见错误</h3>
<ul>
<li><strong>忘记句号</strong>：每条命令式语句必须以 <code>。</code> 结尾</li>
<li><strong>函数体忘记双句号</strong>：<code>函 ...：...。。</code> 一定是双句号</li>
<li><strong>关键字全中文</strong>：使用 <code>若</code> 而非 <code>if</code>，<code>则</code> 而非 <code>then</code></li>
<li><strong>调用函数用空格</strong>：<code>平方 5</code> 而非 <code>平方(5)</code>（括号也可以但风格不同）</li>
</ul>
`;

function renderDocs() {
  sidebarBody.innerHTML = '<div class="docs-content">' + DOCS_HTML + '</div>';
}

// === Keyboard Shortcuts ===
editor.addEventListener('keydown', (e) => {
  // Tab → 2 spaces
  if (e.key === 'Tab') {
    e.preventDefault();
    const start = editor.selectionStart;
    const end = editor.selectionEnd;
    editor.value = editor.value.substring(0, start) + '  ' + editor.value.substring(end);
    editor.selectionStart = editor.selectionEnd = start + 2;
  }
  // Ctrl+Enter → Run
  if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
    e.preventDefault();
    runCode();
  }
});

// === Init ===
document.addEventListener('DOMContentLoaded', () => {
  // Default placeholder
  editor.value = '# 欢迎使用言知 Playground！\n# 试试运行这段代码：\n\n印 "你好，言知！"。\n\n定 data = 列 1 2 3 4 5。\n印 data，皆乘2，归加0。\n\n# 按 Ctrl+Enter 或点击 ▶ 运行';
  
  clearOutput();
  setStatus('就绪', '');
  updateFileLabel();

  // Code area auto-grows via CSS flex:1 already
});

// === Expose to HTML ===
window.runCode = runCode;
window.clearEditor = clearEditor;
window.clearOutput = clearOutput;
window.toggleSidebar = toggleSidebar;
window.closeSidebar = closeSidebar;

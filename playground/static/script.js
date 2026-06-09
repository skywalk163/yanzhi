/* === 言知 Playground v2 — 前端逻辑 === */
/* 参考: wenyan-lang IDE, CodeMirror playgrounds */

// ==================== 言知 CodeMirror 语法模式 ====================

// 关键字
const KEYWORDS = {
  '定义': true, '赋值': true, '函数': true, '宏': true,
  '如果': true, '那么': true, '否则': true,
  '遍历': true, '循环当': true, '导入': true, '导出': true,
  '真': true, '假': true, '空': true,
  '尝试': true, '试': true, '捕获': true, '结束': true, '完毕': true,
  '就': true, '不然': true, '是': true, '对于': true, '每次': true,
  '返回': true, '启用': true, '策略': true, '结构': true, '方法': true,
  '引用': true, '模板': true, '执行': true,
};

// 动词
const VERBS = {
  '相加': true, '相减': true, '相乘': true, '相除': true, '取余': true, '乘方': true, '取负': true, '绝对': true,
  '大于': true, '小于': true, '等于': true, '不等': true, '大于等于': true, '小于等于': true,
  '并且': true, '或者': true, '非也': true,
  '列表': true, '首个': true, '剩余': true, '索引': true, '长度': true, '添加': true, '连接': true, '包含': true, '删除': true,
  '打印': true, '读取': true, '写入': true,
  '取': true, '尾': true, '排': true, '反': true, '合': true, '字': true, '整': true, '类': true,
  '映射': true, '过滤': true, '归约': true, '合并': true,
  '范围': true, '反转': true, '去重': true, '位置': true, '子串': true, '子列': true,
  '开方': true, '正弦': true, '余弦': true, '指数': true, '对数': true,
  '随机': true, '输入': true,
};

CodeMirror.defineSimpleMode('yanzhi', {
  start: [
    { regex: /"(?:[^"\\]|\\.)*"/, token: 'string yanzhi-string' },
    { regex: /#.*/, token: 'comment yanzhi-comment' },
    { regex: /--.*/, token: 'comment yanzhi-comment' },
    { regex: /\b(真|假|空)\b/, token: 'builtin yanzhi-builtin' },
    { regex: /\b(定义|赋值|函数|宏|如果|那么|否则|遍历|循环当|导入|导出|返回|引用|模板|执行|结束|完毕)\b/, token: 'keyword yanzhi-keyword' },
    { regex: /\b(启用|策略|结构|方法|尝试|试|捕获|就|不然|是|对于|每次)\b/, token: 'keyword yanzhi-keyword' },
    { regex: /\b(相加|相减|相乘|相除|取余|乘方|取负|绝对|大于|小于|等于|不等|大于等于|小于等于|并且|或者|非也)\b/, token: 'operator yanzhi-operator' },
    { regex: /\b(列表|打印|首个|剩余|索引|长度|添加|连接|包含|删除|读取|写入|输入|范围|反转|去重|位置|子串|子列|随机|开方|正弦|余弦|指数|对数|四舍五入|最小|最大|求和|乘积|展平)\b/, token: 'variable-2 yanzhi-verb' },
    { regex: /\b(映射|过滤|归约|合并)\b/, token: 'variable-3 yanzhi-adverb' },
    { regex: /\b(取|尾|排|反|合|字|整|类)\b/, token: 'variable-2 yanzhi-verb' },
    { regex: /\b\d+(\.\d+)?\b/, token: 'number yanzhi-number' },
    { regex: /[。，：；]+/, token: 'punctuation yanzhi-punctuation' },
    { regex: /[+\-*/%^=<>!]+/, token: 'operator' },
    { regex: /[()\[\]{}'【】]/, token: 'bracket' },
  ],
  meta: {
    lineComment: '#',
  }
});

// ==================== 状态 ====================

const state = {
  sidebarOpen: false,
  sidebarTab: 'examples',
  currentFile: null,
  running: false,
  editor: null,
};

// ==================== DOM ====================

const outputBody = document.getElementById('output-body');
const runBtn = document.getElementById('run-btn');
const statusText = document.getElementById('status-text');
const statusDot = document.getElementById('status-dot');
const timingDisplay = document.getElementById('timing-display');
const shareLink = document.getElementById('share-link');
const sidebar = document.getElementById('sidebar');
const sidebarOverlay = document.getElementById('sidebar-overlay');
const sidebarBody = document.getElementById('sidebar-body');
const sidebarTabs = document.querySelectorAll('.sidebar-tabs button');

// ==================== 初始化 CodeMirror ====================

const textarea = document.getElementById('editor');
state.editor = CodeMirror.fromTextArea(textarea, {
  mode: 'yanzhi',
  theme: 'eclipse',
  lineNumbers: true,
  indentUnit: 2,
  tabSize: 2,
  lineWrapping: false,
  styleActiveLine: true,
  autoCloseBrackets: true,
  extraKeys: {
    'Tab': (cm) => cm.replaceSelection('  '),
    'Ctrl-Enter': () => runCode(),
    'Cmd-Enter': () => runCode(),
    'Shift-Enter': () => runCode(),
  },
});

// 默认填充代码
const DEFAULT_CODE = [
  '# 欢迎使用言知 Playground v2！',
  '# 按 Ctrl+Enter 或点击 ▶ 运行',
  '',
  '打印 "你好，言知！"。',
  '',
  '# 管道演示',
  '定义 data = 列表 1 2 3 4 5。',
  '打印 data，映射 相乘 2，过滤 大于 5，归约 相加 0。',
  '',
  '# 条件 + 作用域块',
  '定义 x = 10。',
  '如果 x 大于 5 那么：',
  '  打印 "x 大于 5"。',
  '否则：',
  '  打印 "x 不大于 5"。',
  '结束。',
  '',
  '# 函数定义',
  '定义 平方 = 函数 x 相乘 x x。',
  '定义 r1 = 平方 5。',
  '打印 r1  # 平方(5) = 25',
  '',
  '# 递归实现阶乘',
  '定义 fac = 函数 n：',
  '  如果 n 等于 1 那么 返回 1。',
  '  定义 t = 相减 n 1。',
  '  定义 r = fac t。',
  '  相乘 n r。',
  '结束。',
  '定义 r2 = fac 5。',
  '打印 r2  # 5! = 120',
].join('\n');
state.editor.setValue(DEFAULT_CODE);

// ==================== API（自动重试）====================

async function api(method, path, body, retries = 2) {
  const opts = { method, headers: {} };
  if (body) {
    opts.headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(body);
  }
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const res = await fetch(path, opts);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return res.json();
    } catch (e) {
      if (attempt < retries) {
        await new Promise(r => setTimeout(r, 500));
        continue;
      }
      throw e;
    }
  }
}

// ==================== 运行代码 ====================

async function runCode() {
  if (state.running) return;
  const code = state.editor.getValue().trim();
  if (!code) {
    addOutput('请输入代码后再运行', 'output-error');
    return;
  }

  state.running = true;
  runBtn.disabled = true;
  runBtn.textContent = '⏳ …';
  setStatus('运行中…', 'busy');
  timingDisplay.textContent = '';

  outputBody.innerHTML = '';

  try {
    const data = await api('POST', '/api/run', { code });

    if (data.stdout) {
      addOutput(data.stdout, 'output-stdout');
    }
    if (data.result !== null && data.result !== undefined) {
      const resultStr = typeof data.result === 'object' ? JSON.stringify(data.result) : String(data.result);
      addOutput(`=> ${resultStr}`, 'output-result');
    }
    if (data.error) {
      const errDiv = addOutput(`错误: ${data.error}`, 'output-error');
      // 可点击跳转到错误行
      const lineMatch = data.error.match(/第(\d+)行/);
      if (lineMatch) {
        const line = parseInt(lineMatch[1]) - 1;
        errDiv.title = '点击跳转到错误行';
        errDiv.onclick = () => {
          state.editor.setCursor({ line, ch: 0 });
          state.editor.focus();
        };
      }
      setStatus('有错误', 'error');
    } else {
      setStatus('执行完成', 'success');
    }

    // 显示计时和统计
    if (data.time !== undefined) {
      timingDisplay.textContent = `⚡ ${data.time}ms  |  ${data.tokens || '?'} tokens  |  ${data.instrs || '?'} instrs`;
    }
  } catch (e) {
    addOutput(`请求失败: ${e.message}`, 'output-error');
    setStatus('网络错误', 'error');
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
  return div;
}

function clearOutput() {
  outputBody.innerHTML = '<div class="output-placeholder">▶ 运行或 Ctrl+Enter</div>';
  timingDisplay.textContent = '';
}

function clearEditor() {
  state.editor.setValue('');
  state.currentFile = null;
  updateFileLabel();
  clearOutput();
}

function setStatus(text, type) {
  statusText.textContent = text;
  statusDot.className = 'status-indicator' + (type ? ' ' + type : '');
}

function updateFileLabel() {
  const label = document.getElementById('file-label');
  label.textContent = state.currentFile ? `📄 ${state.currentFile}` : '未命名';
}

// ==================== 分享链接 ====================

function copyShareLink() {
  const code = state.editor.getValue();
  const compressed = btoa(encodeURIComponent(code));
  const url = `${window.location.origin}${window.location.pathname}?code=${compressed}`;
  navigator.clipboard.writeText(url).then(() => {
    setStatus('✅ 分享链接已复制', 'success');
    setTimeout(() => setStatus('就绪', ''), 2000);
  }).catch(() => {
    // Fallback
    const input = document.createElement('input');
    input.value = url;
    document.body.appendChild(input);
    input.select();
    document.execCommand('copy');
    document.body.removeChild(input);
    setStatus('✅ 链接已复制', 'success');
  });
}

// 从 URL 参数加载代码
function loadFromURL() {
  const params = new URLSearchParams(window.location.search);
  const encoded = params.get('code');
  if (encoded) {
    try {
      const code = decodeURIComponent(atob(encoded));
      state.editor.setValue(code);
      setStatus('已从分享链接加载', 'success');
      setTimeout(() => setStatus('就绪', ''), 2000);
    } catch (e) {
      // ignore invalid share URLs
    }
  }
}

// ==================== 侧边栏 ====================

function toggleSidebar(tab) {
  if (state.sidebarOpen && state.sidebarTab === tab) {
    closeSidebar();
    return;
  }
  state.sidebarOpen = true;
  state.sidebarTab = tab;
  sidebar.classList.add('open');
  sidebarOverlay.classList.add('open');

  sidebarTabs.forEach(b => {
    b.classList.toggle('active', b.dataset.tab === tab);
  });

  const title = document.getElementById('sidebar-title');
  title.textContent = tab === 'examples' ? '📂 示例' : '📖 语法参考';

  if (tab === 'examples') renderExamples();
  else if (tab === 'docs') renderDocs();
}

function closeSidebar() {
  state.sidebarOpen = false;
  sidebar.classList.remove('open');
  sidebarOverlay.classList.remove('open');
}

// ==================== 示例 ====================

const EXAMPLE_META = {
  'advanced.yan': { desc: '高级特性 — 言律句式、高阶函数、块语法、列表操作' },
  'algorithms.yan': { desc: '算法集 — 冒泡排序、阶乘、条件链、循环块' },
  'bubblesort.yan': { desc: '冒泡排序 — 嵌套循环 + 数组交换' },
  'demo.yan': { desc: '基础语法总览 — 数学、条件、管道、递归、作用域块' },
  'fibonacci.yan': { desc: '斐波那契数列 — 递归经典范例' },
  'fizzbuzz.yan': { desc: 'FizzBuzz — 循环 + 条件嵌套 + 取余' },
  'hanoi.yan': { desc: '汉诺塔 — 递归分治算法' },
  'math_tools.yan': { desc: '数学工具 — 最大公约数、最小公倍数、互质判断' },
  'pipeline_demo.yan': { desc: '函数式管道 — 映射/过滤/归约 全链组合' },
  'primes.yan': { desc: '质数筛法 — 递归判断 + 循环遍历' },
  'quicksort.yan': { desc: '快速排序 — 分治思想' },
  'turing.yan': { desc: '图灵机模拟器 — 双轨设计，识别 aⁿbⁿ 语言' },
  'webserver.yan': { desc: 'Web 服务器 — 通过 {{}} 调用 Python http.server' },
  'yan_law.yan': { desc: '言律自然语法 — 要是句式、作用域块、循环当句式' },
};

async function renderExamples() {
  sidebarBody.innerHTML = '<p style="color:var(--fg3);padding:12px">加载中…</p>';
  try {
    const data = await api('GET', '/api/examples');
    const examples = data.examples || [];
    sidebarBody.innerHTML = '';
    examples.forEach(ex => {
      const name = ex.name;
      const meta = EXAMPLE_META[name] || { desc: '言知示例文件' };
      const item = document.createElement('div');
      item.className = 'example-item';
      item.innerHTML = `<div class="ex-name">📄 ${name}</div><div class="ex-desc">${meta.desc}</div>`;
      item.onclick = () => loadExample(name);
      sidebarBody.appendChild(item);
    });
    if (examples.length === 0) {
      sidebarBody.innerHTML = '<p style="color:var(--fg3);padding:12px">暂无示例文件</p>';
    }
  } catch (e) {
    console.error('renderExamples error:', e);
    sidebarBody.innerHTML = `<p style="color:var(--error);padding:12px">加载失败 (${e.message})<br><small>请按 Ctrl+F5 强制刷新，或确认服务器运行: <code>python playground/server.py</code></small></p>`;
  }
}

async function loadExample(name) {
  try {
    const data = await api('GET', `/api/examples/${encodeURIComponent(name)}`);
    state.editor.setValue(data.content || '');
    state.currentFile = name;
    updateFileLabel();
    closeSidebar();
    clearOutput();
    setStatus(`已加载: ${name}`, '');
  } catch (e) {
    setStatus(`加载失败: ${e.message}`, 'error');
  }
}

// ==================== 语法参考 ====================

const DOCS_HTML = `
<h2>言知语法速查</h2>

<p>言知是一门<strong>根植于汉语思维结构的中文编程语言</strong>。只有 <strong>6 个关键字</strong>，其他都是动词或宏。</p>

<h3>基本语法</h3>
<pre><code>定义 x = 5。                 # 常量
赋值 x = 10。                # 变量赋值
打印 "你好，言知！"。          # 输出
列表 1 2 3 4 5。             # 创建列表</code></pre>

<h3>条件判断</h3>
<pre><code>如果 x 大于 5 那么 "大" 否则 "小"。
如果 x 大于 5 那么：
  打印 "大"。
否则：
  打印 "小"。
结束。</code></pre>

<h3>循环</h3>
<pre><code>循环当 条件：打印 "循环中"。。         # while
遍历 i 从 1 到 10 ：
  打印 i。
结束。</code></pre>

<h3>函数</h3>
<pre><code>定义 平方 = 函数 n 相乘 n n。
打印 平方 5。                    # 25

# 多语句函数体
定义 阶乘 = 函数 n：
  如果 n 等于 1 那么 1 否则 相乘 n 阶乘 n 相减 1。
结束。
打印 阶乘 10。                   # 3628800</code></pre>

<h3>管道（标志性特性）</h3>
<pre><code>列表 1 2 3 4 5，映射 相乘 2，过滤 大于 5，归约 相加 0。
#     ───────  ───────  ───────  ───────
#     映射       过滤     归约     结果: 24</code></pre>

<h3>言律自然语法</h3>
<pre><code>回家的时候：
  打印 "进门了"。
  打印 "开灯了"。

循环当 真，就 打印 "循环中"。</code></pre>

<h3>动词一览</h3>
<table>
<tr><th>动词</th><th>功能</th><th>示例</th></tr>
<tr><td>打印</td><td>输出</td><td>打印 "hello"</td></tr>
<tr><td>相加/相减/相乘/相除</td><td>算术</td><td>相加 5 3 → 8</td></tr>
<tr><td>大于/小于/等于</td><td>比较</td><td>大于 5 3 → 真</td></tr>
<tr><td>列表</td><td>创建列表</td><td>列表 1 2 3 → [1,2,3]</td></tr>
<tr><td>映射</td><td>map</td><td>映射 相乘2 [1,2,3]</td></tr>
<tr><td>过滤</td><td>filter</td><td>过滤 大于5 [3,6,9]</td></tr>
<tr><td>归约</td><td>reduce</td><td>归约 相加0 [1,2,3] → 6</td></tr>
<tr><td>首个</td><td>first</td><td>首个 [1,2,3] → 1</td></tr>
<tr><td>长度</td><td>length</td><td>长度 [1,2,3] → 3</td></tr>
<tr><td>包含</td><td>contains</td><td>包含 [1,2] 1 → 真</td></tr>
</table>

<h3>键盘快捷键</h3>
<table>
<tr><th>按键</th><th>功能</th></tr>
<tr><td>Ctrl+Enter</td><td>运行代码</td></tr>
<tr><td>Tab</td><td>插入 2 空格</td></tr>
</table>

<h3>常见错误</h3>
<ul>
<li><strong>忘记句号</strong>：每个语句以 <code>。</code> 结尾</li>
<li><strong>函数体</strong>：单表达式用空格，多语句用 <code>：</code> 块 + <code>结束</code></li>
<li><strong>关键字</strong>：使用 <code>如果</code> 而非 <code>if</code>，<code>那么</code> 而非 <code>then</code></li>
</ul>
`;

function renderDocs() {
  sidebarBody.innerHTML = '<div class="docs-content">' + DOCS_HTML + '</div>';
}

// ==================== 键盘快捷键 ====================

document.addEventListener('keydown', (e) => {
  // Escape → close sidebar
  if (e.key === 'Escape' && state.sidebarOpen) {
    closeSidebar();
  }
});

// ==================== 初始化 ====================

document.addEventListener('DOMContentLoaded', () => {
  clearOutput();
  setStatus('就绪', '');
  updateFileLabel();
  loadFromURL();

  // 窗口大小改变时刷新编辑器
  window.addEventListener('resize', () => {
    state.editor.refresh();
  });

  // 延迟刷新（确保布局稳定）
  setTimeout(() => state.editor.refresh(), 100);
});

// ==================== 暴露到全局 ====================
window.runCode = runCode;
window.clearEditor = clearEditor;
window.clearOutput = clearOutput;
window.toggleSidebar = toggleSidebar;
window.closeSidebar = closeSidebar;
window.copyShareLink = copyShareLink;

// AI建议功能
let lastAiMtime = null;

function fetchAiAdvice() {
  fetch('/api/get_ai_advice')
    .then(r => r.json())
    .then(obj => {
      if (!obj || obj.success === false) return;
      const mtime = obj.mtime !== undefined ? obj.mtime : null;
      const ts = obj.timestamp || '--';
      const content = obj.content || '';

      function renderAdvice(container, text) {
        if (!container) return;
        const trimmed = String(text || '').trim();
        const hasHtml = /<[^>]+>/i.test(trimmed);
        if (hasHtml) {
          container.style.whiteSpace = '';
          container.innerHTML = text || '<div class="text-xs text-gray-400">暂无建议</div>';
        } else {
          container.style.whiteSpace = 'pre-wrap';
          container.textContent = text || '暂无建议';
        }
      }

      const container = document.getElementById('ai-advice-container');
      const el = document.getElementById('ai_timestamp');

      if (mtime === null) {
        renderAdvice(container, content);
        if (el) el.textContent = ts;
        lastAiMtime = null;
        return;
      }

      if (lastAiMtime === null || mtime !== lastAiMtime) {
        renderAdvice(container, content);
        if (el) el.textContent = ts;
        lastAiMtime = mtime;
      }
    })
    .catch(err => {
      console.error('获取AI建议失败:', err);
    });
}

// 绑定AI分析按钮
function bindAiButtons() {
  const runBtn = document.getElementById('run-ai-btn');
  const resultEl = document.getElementById('run-ai-result');
  if (!runBtn) return;

  runBtn.addEventListener('click', () => {
    runBtn.disabled = true;
    const origText = runBtn.textContent;
    runBtn.textContent = '运行中...';
    if (resultEl) resultEl.textContent = '';

    fetch('/run_ai', { method: 'POST' })
      .then(r => r.json().then(j => ({ status: r.status, body: j })).catch(() => ({ status: r.status, body: null })))
      .then(({ status, body }) => {
        if (!body) {
          if (resultEl) resultEl.textContent = '未能解析服务器返回';
        } else if (body.success) {
          if (resultEl) resultEl.innerText = `执行成功：${body.msg || ''}\n${body.stdout || ''}`;
          fetchAiAdvice();
        } else {
          let text = `执行失败：${body.msg || ''}`;
          if (body.stderr) text += '\n错误详情：' + body.stderr;
          if (body.stdout) text += '\n输出：' + body.stdout;
          if (resultEl) resultEl.innerText = text;
        }
      })
      .catch(err => {
        if (resultEl) resultEl.textContent = '调用失败：' + err;
      })
      .finally(() => {
        runBtn.disabled = false;
        runBtn.textContent = origText;
      });
  });
}

function initAiAdviceModule() {

  bindAiButtons();
}
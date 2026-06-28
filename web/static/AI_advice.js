// AI建议与状态管理模块
let lastAiMtime = null;
let aiStatusPollingInterval = null;
let aiLogs = [];
const MAX_LOGS = 20;



// 动作名称映射
const actionLabels = {
  'turn_off_fan': '关闭风扇',
  'turn_off_light': '关闭小灯',
  'no_action': '无动作',
  'turn_on_fan': '开启风扇',
  'turn_on_light': '开启小灯'
};

// 获取动作显示名称
function getActionLabel(action) {
  return actionLabels[action] || action;
}

// 格式化时间
function formatTime(date) {
  const hours = date.getHours().toString().padStart(2, '0');
  const minutes = date.getMinutes().toString().padStart(2, '0');
  const seconds = date.getSeconds().toString().padStart(2, '0');
  return `${hours}:${minutes}:${seconds}`;
}

// 更新AI状态卡片
function updateAIStatusCard(data) {
  // 同步开关状态
  const toggle = document.getElementById('auto-control-toggle');
  if (toggle) {
    toggle.checked = data.auto_control_enabled === true;
  }
  // 灰化/恢复整个 AI 状态卡片（但保留开关可点击）
  const statusCard = document.getElementById('ai-status-card');
  if (statusCard) {
    if (data.auto_control_enabled === true) {
      statusCard.classList.remove('opacity-40');
    } else {
      statusCard.classList.add('opacity-40');
    }
  }
  
  // 更新原因
  const reasonEl = document.getElementById('ai-reason');
  if (reasonEl) {
    reasonEl.textContent = data.reason || '系统正在分析环境数据...';
  }
  
  // 更新当前动作
  const actionEl = document.getElementById('ai-action');
  if (actionEl) {
    actionEl.textContent = data.action || '无动作';
  }
  
  // 更新执行状态
  const executeIcon = document.getElementById('execute-icon');
  const executeText = document.getElementById('execute-text');
  const executed = data.executed;
  
  if (executeIcon && executeText) {
    if (executed === true) {
      executeIcon.className = 'fa fa-check-circle mr-1 text-green-400';
      executeText.textContent = '已执行';
      executeText.className = 'text-green-400';
    } else {
      executeIcon.className = 'fa fa-circle-o mr-1 text-gray-400';
      executeText.textContent = '未执行';
      executeText.className = 'text-gray-400';
    }
  }
}

// 添加AI执行日志
function addAILog(statusData) {
  const logContainer = document.getElementById('ai-log-container');
  if (!logContainer) return;

  const logEntry = document.createElement('div');
  logEntry.className = 'ai-log-entry';
  
  const timestamp = statusData.time || new Date().toLocaleString('zh-CN');
  const action = statusData.action || '无动作';
  const executed = statusData.executed ? '已执行' : '未执行';
  const reason = statusData.reason || '';
  
  let logContent = `<div class="text-xs text-gray-500">${timestamp}</div>`;
  logContent += `<div class="text-sm font-medium text-gray-800">${action}</div>`;
  if (reason) {
    logContent += `<div class="text-xs text-gray-500">${reason}</div>`;
  }
  logContent += `<div class="text-xs ${statusData.executed ? 'text-green-500' : 'text-gray-400'}">${executed}</div>`;
  
  logEntry.innerHTML = logContent;
  
  logContainer.prepend(logEntry);
  
  // 保持最多10条日志
  const maxLogs = 10;
  while (logContainer.children.length > maxLogs) {
    logContainer.removeChild(logContainer.lastChild);
  }
}

// 轮询获取AI执行状态
function pollAIStatus() {
  fetch('/api/get_ai_status')
    .then(r => r.json())
    .then(data => {
      if (data && data.success && data.data) {
        const statusData = data.data;
        
        // 更新AI状态卡片
        updateAIStatusCard(statusData);
        
        // 如果有触发场景，添加到日志
        if (statusData.action && statusData.action !== '无动作') {
          addAILog(statusData);
        }
        
        // 更新AI在线状态
        const statusIndicator = document.getElementById('ai-status-indicator');
        if (statusIndicator) {
          statusIndicator.className = 'w-3 h-3 rounded-full bg-green-500 mr-2 animate-pulse';
        }
      }
    })
    .catch(err => {
      console.error('获取AI状态失败:', err);
      const statusIndicator = document.getElementById('ai-status-indicator');
      if (statusIndicator) {
        statusIndicator.className = 'w-3 h-3 rounded-full bg-red-500 mr-2';
      }
    });
}

// 获取AI建议
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
          // 触发一次状态获取
          pollAIStatus();
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

// 渲染AI日志列表
function renderLogs() {
  const logContainer = document.getElementById('ai-log-container');
  if (!logContainer) return;
  
  logContainer.innerHTML = '<div class="text-xs text-gray-500 text-center py-4">暂无执行记录</div>';
}

// 初始化AI状态模块（轮询由 ai_status.js 负责，此处仅做初始化）
function initAIStatusModule() {
  // 初始化日志容器
  renderLogs();
  // 轮询由 ai_status.js 的 AIStatusManager 统一管理
  // 仅执行一次立即获取
  pollAIStatus();
}

// 停止轮询
function stopAIStatusPolling() {
  if (aiStatusPollingInterval) {
    clearInterval(aiStatusPollingInterval);
    aiStatusPollingInterval = null;
  }
}

function initAiAdviceModule() {
  bindAiButtons();
  initAIStatusModule();
}

// 导出函数供其他模块使用
window.aiAdvice = {
  initAiAdviceModule,
  fetchAiAdvice,
  pollAIStatus,
  stopAIStatusPolling,
  addAILog
};

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
  initAiAdviceModule();
});
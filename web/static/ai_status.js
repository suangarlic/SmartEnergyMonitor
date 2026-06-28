// web/static/ai_status.js
// AI状态管理模块 - 独立模块

class AIStatusManager {
  constructor() {
    this.aiLogs = [];
    this.MAX_LOGS = 10; // 【优化】简化为最多10条日志
    this.pollingInterval = null;
    this.currentRiskLevel = 'normal';
    
    // 【优化】风险等级配置 - 仅保留 normal/warning/danger 三个等级
    this.riskConfig = {
      normal: { 
        label: '正常', 
        colorClass: 'text-green-400', 
        bgClass: 'bg-green-500/20'
      },
      warning: { 
        label: '警告', 
        colorClass: 'text-yellow-400', 
        bgClass: 'bg-yellow-500/20'
      },
      danger: { 
        label: '危险', 
        colorClass: 'text-red-400', 
        bgClass: 'bg-red-500/20'
      }
      // 【优化】删除 critical 等级
    };
    
    // 动作名称映射
    this.actionLabels = {
      'turn_off_fan': '关闭风扇',
      'turn_off_light': '关闭小灯',
      'no_action': '无动作',
      'turn_on_fan': '开启风扇',
      'turn_on_light': '开启小灯',
      'adjust_fan': '调节风扇',
      'adjust_light': '调节小灯'
    };
    
    this.init();
  }
  
  // 初始化
  init() {
    this.bindElements();
    this.fetchControlStatus();  // 页面加载时同步后端开关状态
    this.startPolling();
    this.initializeLogContainer();
  }
  
  // 【优化】绑定DOM元素 - 添加 aiStatusText
  bindElements() {
    this.elements = {
      aiStatusCard: document.getElementById('ai-status-card'),
      aiStatusText: document.getElementById('ai-status-text'),
      reason: document.getElementById('ai-reason'),
      action: document.getElementById('ai-action'),
      executeIcon: document.getElementById('execute-icon'),
      executeText: document.getElementById('execute-text'),
      aiStatusIndicator: document.getElementById('ai-status-indicator'),
      autoControlToggle: document.getElementById('auto-control-toggle'),
      logContainer: document.getElementById('ai-log-container')
    };
    // 绑定切换开关事件
    this.bindAutoControlToggle();
  }
  
  // 开始轮询AI状态
  startPolling(interval = 3000) {
    if (this.pollingInterval) {
      clearInterval(this.pollingInterval);
    }
    this.pollingInterval = setInterval(() => {
      this.fetchAIStatus();
    }, interval);
    // 立即执行一次
    this.fetchAIStatus();
  }
  
  // 停止轮询
  stopPolling() {
    if (this.pollingInterval) {
      clearInterval(this.pollingInterval);
      this.pollingInterval = null;
    }
  }
  
  // 绑定自动控制开关事件（已通过 HTML onchange 属性绑定，此处仅做日志确认）
  bindAutoControlToggle() {
    if (!this.elements.autoControlToggle) {
      console.warn('[AIStatus] auto-control-toggle 元素未找到，开关事件可能无法触发');
      return;
    }
    console.log('[AIStatus] 自动控制开关事件已通过 HTML onchange 绑定');
  }
  
  // 切换自动控制
  async toggleAutoControl(enabled) {
    try {
      const response = await fetch('/api/control/toggle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled: enabled })
      });
      const data = await response.json();
      if (data.success) {
        console.log(`自动控制已${enabled ? '开启' : '关闭'}`);
        // 同步灰化效果
        this.syncToggleState(enabled);
      }
    } catch (error) {
      console.error('切换自动控制失败:', error);
      // 失败则回滚开关状态，避免前后端不一致
      if (this.elements.autoControlToggle) {
        this.elements.autoControlToggle.checked = !enabled;
      }
    }
  }
  
  // 同步开关状态
  syncToggleState(auto_control_enabled) {
    if (this.elements.autoControlToggle) {
      this.elements.autoControlToggle.checked = auto_control_enabled === true;
    }
    // 灰化整个 AI 状态卡片（但保留开关可点击）
    if (this.elements.aiStatusCard) {
      if (auto_control_enabled === true) {
        this.elements.aiStatusCard.classList.remove('opacity-40');
      } else {
        this.elements.aiStatusCard.classList.add('opacity-40');
      }
    }
  }
  
  // 页面加载时从后端同步开关状态，避免刷新后状态错乱
  async fetchControlStatus() {
    try {
      const response = await fetch('/api/control/status');
      const data = await response.json();
      if (data.success) {
        console.log(`[Control] 页面加载同步开关状态: ${data.auto_control_enabled}`);
        this.syncToggleState(data.auto_control_enabled);
      }
    } catch (error) {
      console.error('[Control] 获取开关状态失败:', error);
    }
  }
  
  // 获取AI状态
  async fetchAIStatus() {
    try {
      const response = await fetch('/api/get_ai_status');
      const data = await response.json();
      
      if (data && data.success) {
        const statusData = data.data || {};
        this.updateStatus(statusData);
        
        // 如果有执行动作，添加日志
        if (statusData.action && statusData.action !== '无动作') {
          this.addLog(statusData);
        }
        
        // 更新在线状态
        this.updateOnlineStatus(true);
      }
    } catch (error) {
      console.error('获取AI状态失败:', error);
      this.updateOnlineStatus(false);
    }
  }
  
  // 更新AI状态
  updateStatus(data) {
    // 同步开关状态
    this.syncToggleState(data.auto_control_enabled);
    
    // 从 scenario 派生风险等级
    const riskMap = {
      'energy_saving': 'warning',
      'comfort_adjust': 'normal',
      'abnormal_schedule': 'danger',
      'gear_over': 'warning',
      'normal': 'normal',
    };
    const riskLevel = riskMap[data.scenario] || 'normal';
    const config = this.riskConfig[riskLevel];
    
    if (!config) return;
    
    // 更新原因
    this.updateReason(data.reason);
    
    // 更新动作（新格式：action 是字符串，如 "风扇3档→0档；小灯3档→0档"）
    this.updateActionText(data.action);
    
    // 更新执行状态
    this.updateExecuteStatus(data.executed);
  }
  
  // 更新在线状态指示器
  updateOnlineStatus(online) {
    if (this.elements.aiStatusIndicator) {
      this.elements.aiStatusIndicator.className = online 
        ? 'w-3 h-3 rounded-full bg-green-500 mr-2 animate-pulse'
        : 'w-3 h-3 rounded-full bg-red-500 mr-2';
    }
  }
  
  // 【优化】更新风险等级 - 简化为仅应用颜色类
  updateRiskLevel(riskLevel, config) {
    if (!this.elements.riskLevel) return;
    
    // 移除旧样式类
    this.elements.riskLevel.className = '';
    
    // 添加新样式
    this.elements.riskLevel.className = `text-sm font-bold px-2 py-0.5 rounded-full ${config.bgClass} ${config.colorClass}`;
    this.elements.riskLevel.textContent = config.label;
    
    this.currentRiskLevel = riskLevel;
  }
  
  // 更新原因描述
  updateReason(reason) {
    if (this.elements.reason) {
      this.elements.reason.textContent = reason || '系统正在分析环境数据...';
    }
  }
  
  // 更新动作显示（新格式：action 是字符串）
  updateActionText(action) {
    if (!this.elements.action) return;
    this.elements.action.textContent = action || '无动作';
  }
  
  // 保留旧方法兼容
  updateActions(actions) {
    if (!this.elements.action) return;
    const actionList = actions || [];
    if (actionList.length === 0) {
      this.elements.action.textContent = '无动作';
      return;
    }
    const actionLabels = actionList.map(action => this.actionLabels[action] || action);
    this.elements.action.textContent = actionLabels.join('、');
  }
  // 【优化】删除复杂的设备动画方法
  // 原有的 triggerDeviceAnimations、triggerFanShutdown、triggerFanStartup、triggerLightOff、triggerLightOn 已删除
  // 保留简单的状态表达
  
  // 更新执行状态
  updateExecuteStatus(executed) {
    if (!this.elements.executeIcon || !this.elements.executeText) return;
    
    // 更新AI状态文本
    if (this.elements.aiStatusText) {
      if (executed === true) {
        this.elements.aiStatusText.textContent = 'AI已自动执行控制';
      } else {
        this.elements.aiStatusText.textContent = 'AI自主监控中';
      }
    }
    
    if (executed === true) {
      this.elements.executeIcon.className = 'fa fa-check-circle mr-1 text-green-400';
      this.elements.executeText.textContent = '已执行';
      this.elements.executeText.className = 'text-green-400';
    } else {
      this.elements.executeIcon.className = 'fa fa-circle-o mr-1 text-gray-400';
      this.elements.executeText.textContent = '未执行';
      this.elements.executeText.className = 'text-gray-400';
    }
  }
  
  // 【优化】删除节能统计相关方法
  
  // 【优化】删除风险卡片状态更新方法
  
 
  
  // 添加日志
  addLog(data) {
    const log = {
      id: Date.now(),
      time: data.time || this.formatTime(new Date()),
      scenario: data.scenario || 'normal',
      reason: data.reason || '未知',
      action: data.action || '无动作',
      executed: data.executed
    };
    
    this.aiLogs.unshift(log);
    if (this.aiLogs.length > this.MAX_LOGS) {
      this.aiLogs.pop();
    }
    
    this.renderLogs();
  }
  
  // 格式化时间
  formatTime(date) {
    return date.toLocaleTimeString('zh-CN', { 
      hour: '2-digit', 
      minute: '2-digit', 
      second: '2-digit' 
    });
  }
  
  // 初始化日志容器
  initializeLogContainer() {
    if (!this.elements.logContainer) return;
    this.renderLogs();
  }
  
  // 渲染日志列表
  renderLogs() {
    if (!this.elements.logContainer) return;
    
    if (this.aiLogs.length === 0) {
      this.elements.logContainer.innerHTML = '<div class="text-xs text-gray-500 text-center py-4">暂无执行记录</div>';
      return;
    }
    
    const html = this.aiLogs.map(log => {
      const statusTag = log.executed ? '<span class="text-green-400">[已执行]</span>' : '<span class="text-gray-500">[未执行]</span>';
      return `<div class="text-xs py-1 border-b border-gray-700/30">
        <span class="text-primary font-semibold">${log.time}</span> 
        ${statusTag}
        <span class="text-gray-300">${log.action}</span>
        <div class="text-gray-500">${log.reason}</div>
      </div>`;
    }).join('');
    
    this.elements.logContainer.innerHTML = html;
  }
  
  // 手动添加日志（供外部调用）
  addManualLog(scenario, reason, action = '', executed = false) {
    const data = {
      scenario: scenario,
      reason: reason,
      action: action,
      executed: executed
    };
    this.addLog(data);
  }
  
  // 获取当前风险等级
  getCurrentRiskLevel() {
    return this.currentRiskLevel;
  }
  
  // 【优化】删除累计节省电量方法 - 重点放在执行型 Agent 而非能耗统计
  
  // 获取日志列表
  getLogs() {
    return [...this.aiLogs];
  }
}

// 全局自动控制开关处理函数（通过 HTML onchange 调用，确保事件一定触发）
window.handleAutoControlToggle = function(checked) {
  console.log(`[AutoControl] 开关被点击，新状态: ${checked}`);
  if (aiStatusManager) {
    aiStatusManager.toggleAutoControl(checked);
  } else {
    // 兜底：直接发送请求
    console.warn('[AutoControl] aiStatusManager 未初始化，直接发送请求');
    fetch('/api/control/toggle', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ enabled: checked })
    }).then(r => r.json()).then(d => {
      console.log(`[AutoControl] 兜底请求结果: ${JSON.stringify(d)}`);
      if (!d.success && document.getElementById('auto-control-toggle')) {
        document.getElementById('auto-control-toggle').checked = !checked;
      }
    }).catch(e => {
      console.error('[AutoControl] 兜底请求失败:', e);
      if (document.getElementById('auto-control-toggle')) {
        document.getElementById('auto-control-toggle').checked = !checked;
      }
    });
  }
};

// 创建全局实例
let aiStatusManager = null;

// 初始化函数
function initAIStatus() {
  if (!aiStatusManager) {
    aiStatusManager = new AIStatusManager();
  }
  return aiStatusManager;
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
  initAIStatus();
});

// 导出供其他模块使用
window.AIStatusManager = AIStatusManager;
window.initAIStatus = initAIStatus;
window.aiStatusManager = aiStatusManager;

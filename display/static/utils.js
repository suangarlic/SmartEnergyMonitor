// 更新时间显示
function updateTime() {
  const now = new Date();
  const hours = String(now.getHours()).padStart(2, '0');
  const minutes = String(now.getMinutes()).padStart(2, '0');
  const seconds = String(now.getSeconds()).padStart(2, '0');
  document.getElementById('update-time').textContent = `${hours}:${minutes}:${seconds}`;
}

// 数据下采样和填充
function downsamplePad(arr, targetLen) {
  if (!Array.isArray(arr)) return Array(targetLen).fill(null);
  const n = arr.length;
  if (targetLen <= 0) return [];
  if (n === 0) return Array(targetLen).fill(null);
  if (n >= targetLen) {
    if (targetLen === 1) return [arr[n-1]];
    const out = [];
    for (let i = 0; i < targetLen; i++) {
      const idx = Math.round(i * (n - 1) / (targetLen - 1));
      out.push(arr[idx]);
    }
    return out;
  }
  const pad = Array(targetLen - n).fill(null);
  return pad.concat(arr.slice());
}

// 根据视图模式获取固定标签
function getFixedLabelsForMode(mode) {
  if (mode === 'day') {
    const labels = [];
    for (let h = 0; h < 24; h++) {
      labels.push(String(h).padStart(2, '0') + ':00');
    }
    return labels;
  }
  return [];
}

// 描述文本与颜色设置
function setDesc(elementId, iconClass, colorClass, text) {
  const el = document.getElementById(elementId);
  if (!el) return;
  el.className = `mt-3 text-sm ${colorClass}`;
  el.innerHTML = `<i class="fa ${iconClass}"></i> ${text}`;
}

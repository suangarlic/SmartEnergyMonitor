// 实时功率趋势图
let powerChart = null;
const powerLabels = [];
const powerHistoryData = {};
const POWER_MAX_POINTS = 60;
const powerPalette = ['#00a8ff', '#00ffaa', '#ff7d00', '#ffd166', '#b39ddb', '#90caf9'];
let powerViewMode = 'realtime';
let lastPowerUpdateTime = Date.now();
const DATA_TIMEOUT = 2000;

function refreshPowerChartView() {
  if (!powerChart) return;
  if (powerViewMode === 'realtime') {
    powerChart.data.labels = powerLabels.slice();
    powerChart.data.datasets.forEach(ds => {
      ds.data = (powerHistoryData[ds.label] || []).slice();
      ds.hidden = ds.hidden === true;
    });
  }
  powerChart.update();
}

function setPowerViewMode(mode) {
  powerViewMode = mode;
  const bDay = document.getElementById('btn-range-day');
  const bRealtime = document.getElementById('btn-range-realtime');
  if (bDay && bRealtime) {
    bDay.className = mode === 'day' ? 'text-xs bg-primary/30 text-white px-3 py-1 rounded-full border border-primary/50' : 'text-xs bg-dark-lighter text-gray-400 px-3 py-1 rounded-full';
    bRealtime.className = mode === 'realtime' ? 'text-xs bg-primary/30 text-white px-3 py-1 rounded-full border border-primary/50' : 'text-xs bg-dark-lighter text-gray-400 px-3 py-1 rounded-full';
  }
  refreshPowerChartView();
}

function initPowerTrendChart() {
  const ctx = document.getElementById('power-trend-chart').getContext('2d');
  powerChart = new Chart(ctx, {
    type: 'line',
    data: { labels: powerLabels, datasets: [] },
    options: {
      responsive: true, maintainAspectRatio: false,
      scales: { x: { grid: { color: 'rgba(255,255,255,0.04)' }, ticks: { color: 'rgba(255,255,255,0.6)' } },
               y: { grid: { color: 'rgba(255,255,255,0.04)' }, ticks: { color: 'rgba(255,255,255,0.6)' }, beginAtZero: true } },
      plugins: { legend: { display: true, labels: { color: '#e0e0e0' } }, tooltip: { mode: 'nearest', intersect: false } },
      interaction: { intersect: false, mode: 'index' },
      animation: { duration: 200 }
    }
  });
}

function ensurePowerDataset(deviceName, colorIndex) {
  if (!powerChart) return;
  const ds = powerChart.data.datasets.find(d => d.label === deviceName);
  if (ds) return ds;
  const color = powerPalette[colorIndex % powerPalette.length];
  const newDs = {
    label: deviceName, data: powerHistoryData[deviceName] || [],
    borderColor: color, backgroundColor: color + '33',
    fill: true, tension: 0.35, pointRadius: 2, cubicInterpolationMode: 'monotone'
  };
  powerChart.data.datasets.push(newDs);
  return newDs;
}

function updatePowerData(devices) {
  lastPowerUpdateTime = Date.now();
  if (!Array.isArray(devices)) return;
  const nowLabel = new Date().toTimeString().slice(0,8);
  powerLabels.push(nowLabel);
  while (powerLabels.length > POWER_MAX_POINTS) powerLabels.shift();

  const targetDevices = devices.filter(d => {
    const name = (d.name || '').toLowerCase();
    return name.includes('小灯') || name.includes('灯') || name.includes('风扇') || name.includes('fan') || name.includes('light');
  });

  targetDevices.forEach((d, idx) => {
    const name = d.name || `设备${idx+1}`;
    const value = (d.power !== undefined ? d.power : (d.value !== undefined ? d.value : 0));
    if (!powerHistoryData[name]) {
      powerHistoryData[name] = Array(powerLabels.length - 1).fill(null);
    }
    powerHistoryData[name].push(Number.isFinite(+value) ? +value : null);
    while (powerHistoryData[name].length > POWER_MAX_POINTS) powerHistoryData[name].shift();
  });

  const totalPower = '功率和';
  if (!powerHistoryData[totalPower]) {
    powerHistoryData[totalPower] = Array(powerLabels.length - 1).fill(null);
  }
  let currentSum = 0;
  targetDevices.forEach(d => {
    const name = d.name || `设备${d.id || 0}`;
    const value = (d.power !== undefined ? d.power : (d.value !== undefined ? d.value : 0));
    if (Number.isFinite(+value)) currentSum += +value;
  });
  powerHistoryData[totalPower].push(currentSum);
  while (powerHistoryData[totalPower].length > POWER_MAX_POINTS) powerHistoryData[totalPower].shift();

  ensurePowerDataset(totalPower, 0);
  refreshPowerChartView();
}

function zeroPowerChart() {
  const nowLabel = new Date().toTimeString().slice(0,8);
  powerLabels.push(nowLabel);
  while (powerLabels.length > POWER_MAX_POINTS) powerLabels.shift();
  const totalPower = '功率和';
  Object.keys(powerHistoryData).forEach(name => {
    powerHistoryData[name].push(0);
    while (powerHistoryData[name].length > POWER_MAX_POINTS) powerHistoryData[name].shift();
  });
  if (!powerHistoryData[totalPower]) {
    powerHistoryData[totalPower] = Array(powerLabels.length).fill(0);
  }
  ensurePowerDataset(totalPower, 0);
  refreshPowerChartView();
  document.getElementById('device-light-power').textContent = '0W';
  document.getElementById('device-fan-power').textContent = '0W';
}

function initPowerModule() {
  initPowerTrendChart();
  (function bindPowerRangeButtons(){
    const bDay = document.getElementById('btn-range-day');
    const bRealtime = document.getElementById('btn-range-realtime');
    if (bDay) bDay.addEventListener('click', () => setPowerViewMode('day'));
    if (bRealtime) bRealtime.addEventListener('click', () => setPowerViewMode('realtime'));
    setPowerViewMode('realtime');
  })();
}
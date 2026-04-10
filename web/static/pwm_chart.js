// PWM占空比图表功能
let pwmChart = null;
const pwmLabels = [];
const pwmHistoryData = {};
const PWM_MAX_POINTS = 60;
const pwmPalette = ['#00a8ff', '#00ffaa', '#ff7d00', '#ffd166', '#b39ddb', '#90caf9'];

function initPwmModule() {
  initPwmChart();
}

function initPwmChart() {
  const ctx = document.getElementById('pwm-duty-chart').getContext('2d');
  pwmChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: pwmLabels,
      datasets: []
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          grid: { color: 'rgba(255,255,255,0.04)' },
          ticks: { color: 'rgba(255,255,255,0.6)' }
        },
        y: {
          grid: { color: 'rgba(255,255,255,0.04)' },
          ticks: { color: 'rgba(255,255,255,0.6)' },
          beginAtZero: true,
          max: 100
        }
      },
      plugins: {
        legend: { display: true, labels: { color: '#e0e0e0' } }
      }
    }
  });
}

// 确保设备数据集存在
function ensurePwmDataset(deviceName, colorIndex) {
  if (!pwmChart) return;
  const ds = pwmChart.data.datasets.find(d => d.label === deviceName);
  if (ds) return ds;
  
  const color = pwmPalette[colorIndex % pwmPalette.length];
  const newDs = {
    label: deviceName,
    data: pwmHistoryData[deviceName] || [],
    borderColor: color,
    backgroundColor: color + '33',
    fill: true,
    tension: 0.35,
    pointRadius: 2,
    cubicInterpolationMode: 'monotone'
  };
  pwmChart.data.datasets.push(newDs);
  return newDs;
}

// 更新PWM占空比数据
function updatePwmData(devices) {
  if (!pwmChart || !Array.isArray(devices)) return;
  
  // 添加时间标签
  const nowLabel = new Date().toTimeString().slice(0, 8);
  pwmLabels.push(nowLabel);
  
  // 保持历史数据点数量
  while (pwmLabels.length > PWM_MAX_POINTS) {
    pwmLabels.shift();
  }
  
  // 更新每个设备的占空比数据
  devices.forEach((device, index) => {
    if (!device || !device.name || device.duty_cycle === undefined) return;
    
    const name = device.name;
    const dutyCycle = parseFloat(device.duty_cycle);
    
    // 确保设备的历史数据数组存在
    if (!pwmHistoryData[name]) {
      pwmHistoryData[name] = Array(pwmLabels.length - 1).fill(null);
    }
    
    // 添加新数据点
    pwmHistoryData[name].push(dutyCycle);
    
    // 保持历史数据点数量
    while (pwmHistoryData[name].length > PWM_MAX_POINTS) {
      pwmHistoryData[name].shift();
    }
    
    // 确保数据集存在
    ensurePwmDataset(name, index);
  });
  
  // 更新图表显示
  pwmChart.update();
}
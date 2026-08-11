// 功率趋势图表功能
let pwmChart = null;
const pwmLabels = [];
const pwmHistoryData = {};
const PWM_MAX_POINTS = 60;
const pwmPalette = ['#00a8ff', '#ff7d00'];

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
      interaction: {
        mode: 'index',
        intersect: false
      },
      scales: {
        x: {
          grid: { color: 'rgba(255,255,255,0.04)' },
          ticks: { color: 'rgba(255,255,255,0.6)' },
          title: {
            display: true,
            text: '时间',
            color: 'rgba(255,255,255,0.8)'
          }
        },
        y: {
          grid: { color: 'rgba(255,255,255,0.04)' },
          ticks: { color: 'rgba(255,255,255,0.6)' },
          beginAtZero: true,
          max: 30,
          min: 0,
          title: {
            display: true,
            text: '功率 (W)',
            color: 'rgba(255,255,255,0.8)'
          }
        }
      },
      plugins: {
        legend: { 
          display: true, 
          labels: { 
            color: '#e0e0e0',
            usePointStyle: true,
            padding: 20
          }
        },
        tooltip: {
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          titleColor: '#fff',
          bodyColor: '#fff',
          padding: 12,
          displayColors: true
        }
      }
    }
  });
}

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
    fill: false,
    tension: 0.35,
    pointRadius: 3,
    pointHoverRadius: 5,
    borderWidth: 2,
    cubicInterpolationMode: 'monotone'
  };
  pwmChart.data.datasets.push(newDs);
  return newDs;
}

function updatePwmData(devices) {
  if (!pwmChart || !Array.isArray(devices)) return;
  
  const nowLabel = new Date().toTimeString().slice(0, 8);
  pwmLabels.push(nowLabel);
  
  while (pwmLabels.length > PWM_MAX_POINTS) {
    pwmLabels.shift();
  }
  
  devices.forEach((device, index) => {
    if (!device || !device.name || device.power === undefined) return;
    
    const name = device.name.includes('小灯') ? '小灯' : 
                 device.name.includes('风扇') ? '风扇' : device.name;
    const power = parseFloat(device.power) || 0;
    
    if (!pwmHistoryData[name]) {
      pwmHistoryData[name] = Array(pwmLabels.length - 1).fill(null);
    }
    
    pwmHistoryData[name].push(power);
    
    while (pwmHistoryData[name].length > PWM_MAX_POINTS) {
      pwmHistoryData[name].shift();
    }
    
    ensurePwmDataset(name, index);
  });
  
  pwmChart.update('none');
}
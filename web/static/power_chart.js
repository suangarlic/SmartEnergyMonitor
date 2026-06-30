// 双设备每日能耗柱状图
let powerChart = null;

function initPowerModule() {
  initPowerChart();
  fetchEnergyStats();
}

function initPowerChart() {
  const ctx = document.getElementById('power-trend-chart').getContext('2d');
  powerChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: [],
      datasets: [
        {
          label: '风扇',
          data: [],
          backgroundColor: '#00a8ff',
          borderColor: '#0090dd',
          borderWidth: 1,
          borderRadius: 4
        },
        {
          label: '小灯',
          data: [],
          backgroundColor: '#ff7d00',
          borderColor: '#dd6000',
          borderWidth: 1,
          borderRadius: 4
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: 'index',
        intersect: false,
        touch: {
          enabled: true,
          mode: 'nearest',
          axis: 'x'
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255,255,255,0.04)' },
          ticks: { 
            color: 'rgba(255,255,255,0.6)',
            maxRotation: 45,
            minRotation: 45,
            font: {
              size: Math.max(8, Math.min(12, window.innerWidth / 40))
            }
          },
          title: {
            display: window.innerWidth > 640,
            text: '日期',
            color: 'rgba(255,255,255,0.8)'
          }
        },
        y: {
          grid: { color: 'rgba(255,255,255,0.04)' },
          ticks: { 
            color: 'rgba(255,255,255,0.6)',
            font: {
              size: Math.max(8, Math.min(12, window.innerWidth / 40))
            }
          },
          beginAtZero: true,
          title: {
            display: window.innerWidth > 640,
            text: '能耗 (Wh)',
            color: 'rgba(255,255,255,0.8)'
          }
        }
      },
      plugins: {
        legend: {
          display: window.innerWidth > 640,
          labels: {
            color: '#e0e0e0',
            usePointStyle: true,
            padding: 15,
            font: {
              size: Math.max(10, Math.min(12, window.innerWidth / 50))
            }
          }
        },
        tooltip: {
          backgroundColor: 'rgba(0, 0, 0, 0.9)',
          titleColor: '#fff',
          bodyColor: '#fff',
          padding: window.innerWidth > 640 ? 12 : 8,
          titleFont: {
            size: Math.max(10, Math.min(14, window.innerWidth / 40))
          },
          bodyFont: {
            size: Math.max(10, Math.min(12, window.innerWidth / 50))
          },
          callbacks: {
            label: function(ctx) {
              return ctx.dataset.label + ': ' + ctx.parsed.y + ' Wh';
            }
          }
        }
      },
      animation: {
        duration: window.innerWidth > 640 ? 300 : 150
      }
    }
  });
}

function fetchEnergyStats() {
  fetch('/api/energy_stats')
    .then(response => response.json())
    .then(data => {
      renderEnergyChart(data);
    })
    .catch(error => {
      console.error('获取能耗统计数据失败:', error);
      showEnergyWarning('加载能耗数据失败');
    });
}

function renderEnergyChart(data) {
  if (!powerChart) return;

  const { dates, fan_energy, light_energy, days_available, expected_days } = data;

  powerChart.data.labels = dates;
  powerChart.data.datasets[0].data = fan_energy;
  powerChart.data.datasets[1].data = light_energy;
  powerChart.update();

  if (days_available < expected_days) {
    showEnergyWarning(
      `提示：数据库中仅有 <strong>${days_available}</strong> 天的数据，不足 ${expected_days} 天。更多数据将在设备运行后自动累积。`
    );
  } else {
    clearEnergyWarning();
  }
}

function showEnergyWarning(msg) {
  let el = document.getElementById('energy-warning');
  if (!el) {
    el = document.createElement('div');
    el.id = 'energy-warning';
    el.className = 'mt-2 px-3 py-2 bg-yellow-500/10 border border-yellow-500/30 rounded text-xs text-yellow-400';
    const chartContainer = document.getElementById('power-trend-chart')?.parentElement?.parentElement;
    if (chartContainer) {
      chartContainer.appendChild(el);
    }
  }
  el.innerHTML = msg;
}

function clearEnergyWarning() {
  const el = document.getElementById('energy-warning');
  if (el) el.remove();
}

// 保留兼容旧调用的空函数
function updatePowerData() {}
function zeroPowerChart() {}
function setPowerViewMode() {}
// 传感器数据更新功能
function initSensorDataModule() {
  // 定期获取最新传感器数据
  setInterval(fetchLatestData, 5000);
  // 初始获取一次
  fetchLatestData();
}

function fetchLatestData() {
  fetch('/api/get_latest_data')
    .then(response => response.json())
    .then(data => {
      updateSensorDisplay(data);
    })
    .catch(error => {
      console.error('获取传感器数据失败:', error);
    });
}

function updateSensorDisplay(data) {
  // 更新时间戳
  if (data.timestamp) {
    document.getElementById('timestamp').textContent = data.timestamp;
  }

  // 更新温度和湿度
  if (data.temperature) {
    document.getElementById('temp').innerHTML = `${data.temperature}<span class="text-lg">℃</span>`;
    // 更新温度描述
    const temp = parseFloat(data.temperature);
    let tempDesc = '';
    if (temp < 15) {
      tempDesc = '温度较低';
    } else if (temp > 30) {
      tempDesc = '温度较高';
    } else {
      tempDesc = '温度适宜';
    }
    document.getElementById('temp-desc').textContent = tempDesc;
  }

  if (data.humidity) {
    document.getElementById('humi').textContent = `${data.humidity}%`;
  }

  // 更新光线强度
  if (data.light) {
    document.getElementById('light').textContent = data.light;
  }

  // 更新人体红外状态
  if (data.pir_status) {
    document.getElementById('pir_status').textContent = data.pir_status;
  }

  // 更新设备列表和功率数据
  if (data.pwm_devices && Array.isArray(data.pwm_devices)) {
    data.pwm_devices.forEach(device => {
      if (device.name.includes('小灯')) {
        document.getElementById('device-light-power').textContent = `${device.power}W`;
        document.getElementById('current-device-name').textContent = device.name;
        document.getElementById('current-duty').textContent = `${device.duty_cycle}%`;
      } else if (device.name.includes('风扇')) {
        document.getElementById('device-fan-power').textContent = `${device.power}W`;
      }
    });

    // 更新功率图表
    updatePowerData(data.pwm_devices);
    
    // 更新PWM占空比图表（新增）
    updatePwmData(data.pwm_devices);
  }
}
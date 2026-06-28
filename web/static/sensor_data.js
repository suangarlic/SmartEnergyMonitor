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
    const pirStatusElement = document.getElementById('pir_status');
    const pirIconElement = pirStatusElement?.parentElement?.querySelector('i');
    
    pirStatusElement.textContent = data.pir_status;
    
    // 根据状态设置颜色：有人显示绿色，无人显示灰色
    if (data.pir_status === '有人') {
      pirStatusElement.style.color = '#4ade80'; // 绿色
      pirIconElement?.setAttribute('style', 'color: #4ade80');
    } else {
      pirStatusElement.style.color = '#6b7280'; // 灰色
      pirIconElement?.setAttribute('style', 'color: #6b7280');
    }
  }

  // 更新设备列表和功率数据
  if (data.pwm_devices && Array.isArray(data.pwm_devices)) {
    data.pwm_devices.forEach(device => {
      if (device.name.includes('小灯')) {
        document.getElementById('device-light-power').textContent = `${device.power}W`;
        
        document.getElementById('current-duty').textContent = `${device.duty_cycle}%`;
        const level = Number(device.level);
        if (!Number.isNaN(level)) {
          window.deviceControl?.syncDeviceLevel?.('light', level);
        }
      } else if (device.name.includes('风扇')) {
        document.getElementById('device-fan-power').textContent = `${device.power}W`;
        const level = Number(device.level);
        if (!Number.isNaN(level)) {
          window.deviceControl?.syncDeviceLevel?.('fan', level);
        }
      }
    });

    // 更新功率图表
    updatePowerData(data.pwm_devices);
    
    // 更新PWM占空比图表（新增）
    updatePwmData(data.pwm_devices);
  }

  // 根据后端返回的设备状态同步显示
  syncDeviceLevelsFromBackend(data);
}

// 如果设备状态是由后端传来，则同步显示级别
function syncDeviceLevelsFromBackend(data) {
  if (!data.pwm_devices || !Array.isArray(data.pwm_devices)) {
    return;
  }
  data.pwm_devices.forEach(device => {
    if (device.name.includes('小灯') || device.name.includes('风扇')) {
      const level = Number(device.level);
      if (!Number.isNaN(level) && window.deviceControl?.syncDeviceLevel) {
        const deviceKey = device.name.includes('小灯') ? 'light' : 'fan';
        window.deviceControl.syncDeviceLevel(deviceKey, level);
      }
    }
  });
}
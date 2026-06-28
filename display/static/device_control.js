// 设备挡位控制脚本
// 设备挡位配置（基于demo/Editor.py中的设置）
const deviceLevels = {
    light: {
        levels: [0, 1, 2, 3],
        pwmValues: [0, 307, 614, 1023],
        percentages: ['0%', '30%', '60%', '100%'],
        labels: ['关', '1档', '2档', '3档']
    },
    fan: {
        levels: [0, 1, 2, 3],
        pwmValues: [0, 409, 716, 1023],
        percentages: ['0%', '40%', '70%', '100%'],
        labels: ['关', '1档', '2档', '3档']
    }
};

// 当前设备挡位状态
let deviceStatus = {
    light: 0, // 默认关档
    fan: 0    // 默认关档
};

// 初始化设备挡位控制
function initDeviceControls() {
    // 为所有挡位按钮添加点击事件
    document.querySelectorAll('.device-level-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const device = this.dataset.device;
            const level = parseInt(this.dataset.level);
            setDeviceLevel(device, level);
        });
    });
    
    // 初始化显示当前挡位
    updateDeviceDisplay('light', deviceStatus.light);
    updateDeviceDisplay('fan', deviceStatus.fan);
}

// 设置设备挡位
function setDeviceLevel(device, level) {
    if (deviceLevels[device] && deviceLevels[device].levels.includes(level)) {
        // 更新按钮状态
        document.querySelectorAll(`.device-level-btn[data-device="${device}"]`).forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`.device-level-btn[data-device="${device}"][data-level="${level}"]`).classList.add('active');
        
        // 更新设备状态
        deviceStatus[device] = level;
        
        // 更新显示
        updateDeviceDisplay(device, level);
        
        // 发送控制命令到行空板
        sendDeviceControlCommand(device, level);
    }
}

// 更新设备显示
function updateDeviceDisplay(device, level) {
    const displayElement = document.getElementById(`${device}-level-display`);
    if (displayElement) {
        const percentage = deviceLevels[device].percentages[level];
        const label = deviceLevels[device].labels[level];
        displayElement.textContent = `${label} (${percentage})`;
    }
}

// 发送设备控制命令到行空板
function sendDeviceControlCommand(device, level) {
    const pwmValue = deviceLevels[device].pwmValues[level];
    
    // 构建控制命令（基于demo/Editor.py中的逻辑）
    const command = {
        device: device,
        level: level,
        pwm_value: pwmValue,
        timestamp: new Date().toISOString()
    };
    
    // 发送到行空板的API
    fetch('/control_device', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(command)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log(`${device} 挡位设置为 ${level} (PWM: ${pwmValue})`);
            showNotification(`${device === 'light' ? '小灯' : '风扇'} 已设置为 ${deviceLevels[device].labels[level]}`, 'success');
        } else {
            throw new Error(data.msg || '控制失败');
        }
    })
    .catch(error => {
        console.error('设备控制失败:', error);
        showNotification('设备控制失败，请检查网络连接', 'error');
    });
}

// 显示通知
function showNotification(message, type = 'info') {
    // 创建通知元素
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <span class="notification-icon">${type === 'success' ? '✅' : '❌'}</span>
            <span class="notification-message">${message}</span>
        </div>
    `;
    
    // 添加到页面
    document.body.appendChild(notification);
    
    // 自动移除
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initDeviceControls();
});

// 导出函数供其他模块使用
window.deviceControl = {
    initDeviceControls,
    setDeviceLevel,
    updateDeviceDisplay,
    sendDeviceControlCommand,
    showNotification
};
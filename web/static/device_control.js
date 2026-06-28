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
    console.log(`[设备控制] 尝试设置 ${device} 为 ${level}档`);
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
    } else {
        console.error(`[设备控制] 无效的设备或挡位: device=${device}, level=${level}`);
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

// 发送设备控制命令到行空板（旧路由 - 直接控制）
// 已废弃，使用命令中心模式替代
function sendDeviceControlCommand(device, level) {
    // 使用命令中心模式，将命令发送到服务器
    const currentFanLevel = device === 'fan' ? level : deviceStatus.fan;
    const currentLightLevel = device === 'light' ? level : deviceStatus.light;
    
    sendCommandToCmdCenter(currentFanLevel, currentLightLevel);
}

// ========== 命令中心模式：新路由 ==========
// 发送命令到命令中心（行空板主动轮询）
function sendCommandToCmdCenter(fanLevel, lightLevel) {
    const command = {
        fan_level: fanLevel,
        light_level: lightLevel
    };
    
    console.log(`[命令中心] 发送命令: ${JSON.stringify(command)}`);
    
    fetch('/set_command', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(command)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log(`[命令中心] 命令已保存: fan_level=${fanLevel}, light_level=${lightLevel}`);
            showNotification(`命令已保存，等待行空板执行`, 'success');
        } else {
            throw new Error(data.msg || '命令保存失败');
        }
    })
    .catch(error => {
        console.error('[命令中心] 发送命令失败:', error);
        showNotification('命令保存失败，请检查网络连接', 'error');
    });
}

// 获取当前设备状态
function getDeviceStatus(device) {
    return deviceStatus[device] ?? 0;
}

// 判断设备是否运行
function isDeviceRunning(device) {
    return getDeviceStatus(device) > 0;
}

// 同步设备状态到页面，不发送控制命令
function syncDeviceLevel(device, level) {
    if (deviceLevels[device] && deviceLevels[device].levels.includes(level)) {
        document.querySelectorAll(`.device-level-btn[data-device="${device}"]`).forEach(btn => {
            btn.classList.remove('active');
        });
        const btn = document.querySelector(`.device-level-btn[data-device="${device}"][data-level="${level}"]`);
        if (btn) {
            btn.classList.add('active');
        }
        deviceStatus[device] = level;
        updateDeviceDisplay(device, level);
    }
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
    sendCommandToCmdCenter,
    showNotification,
    getDeviceStatus,
    isDeviceRunning,
    syncDeviceLevel
};
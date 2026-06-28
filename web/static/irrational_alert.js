// 异常状态检测和弹窗提醒功能
class IrrationalAlert {
    constructor() {
        this.irrationalStartTime = null;
        this.alertThreshold = 10 * 1000; // 10秒异常状态阈值（毫秒）
        this.alertShown = false;
        this.userAcknowledged = false; // 新增：用户是否已确认警告
        this.checkInterval = null;

        this.initModal();
        this.startMonitoring();
    }

    // 初始化弹窗事件监听
    initModal() {
        const closeBtn = document.getElementById('close-modal-btn');
        const autoCloseBtn = document.getElementById('auto-close-devices-btn');

        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                this.hideModal();
                this.userAcknowledged = true; // 用户确认，不再提醒
            });
        }

        if (autoCloseBtn) {
            autoCloseBtn.addEventListener('click', () => {
                this.autoCloseDevices();
                this.hideModal();
                this.userAcknowledged = true; // 用户确认，不再提醒
            });
        }

        console.log('弹窗事件监听器已初始化');
    }

    // 监听传感器数据更新
    listenForSensorUpdates() {
        // 监听pir_status元素的变化
        const pirElement = document.getElementById('pir_status');
        if (pirElement) {
            // 使用MutationObserver监听文本变化
            const observer = new MutationObserver((mutations) => {
                mutations.forEach((mutation) => {
                    if (mutation.type === 'characterData' || mutation.type === 'childList') {
                        // 传感器数据更新时立即检查状态
                        setTimeout(() => {
                            this.checkIrrationalStatus();
                        }, 100);
                    }
                });
            });

            observer.observe(pirElement, {
                characterData: true,
                childList: true,
                subtree: true
            });

            console.log('传感器数据监听器已启动');
        }
    }

    startMonitoring() {
        // 每5秒检查一次异常状态
        this.checkInterval = setInterval(() => {
            this.checkIrrationalStatus();
        }, 5000);

        // 监听传感器数据更新
        this.listenForSensorUpdates();

        console.log('异常状态检测已启动，检测间隔: 5秒');
    }

    isDisplayRunning(displayText) {
        if (!displayText) {
            return false;
        }
        return !displayText.includes('关') && !displayText.includes('0%');
    }

    checkDeviceRunning(){
        // 先使用设备控制模块的状态作为权威来源
        const lightRunning = window.deviceControl?.isDeviceRunning?.('light') ?? false;
        const fanRunning = window.deviceControl?.isDeviceRunning?.('fan') ?? false;

        // 如果控制模块不可用，则回退到显示文本判断
        const lightDisplay = document.getElementById('light-level-display')?.textContent || '';
        const fanDisplay = document.getElementById('fan-level-display')?.textContent || '';

        const effectiveLightRunning = lightRunning || this.isDisplayRunning(lightDisplay);
        const effectiveFanRunning = fanRunning || this.isDisplayRunning(fanDisplay);
        const anyDeviceRunning = effectiveLightRunning || effectiveFanRunning;

        console.log(`设备状态检查 - 小灯显示: "${lightDisplay}", 小灯运行中: ${effectiveLightRunning}, 风扇显示: "${fanDisplay}", 风扇运行中: ${effectiveFanRunning}, 总体: ${anyDeviceRunning ? '有设备运行' : '所有设备已关闭'}`);

        return anyDeviceRunning;
    }

    checkIrrationalStatus() {
        // 获取当前人体检测状态
        const pirStatus = document.getElementById('pir_status')?.textContent || '';

        // 检查是否有人（假设有人状态包含"有人"或"检测到"）
        const hasPerson = pirStatus.includes('有人') || pirStatus.includes('检测到') ||
                         pirStatus.toLowerCase().includes('detected') ||
                         pirStatus === '1';

        if (!hasPerson) {
            // 异常状态
            if (!this.irrationalStartTime) {
                this.irrationalStartTime = Date.now();
                console.log('开始检测异常状态...');
            }

            const duration = Date.now() - this.irrationalStartTime;
            const durationSeconds = Math.floor(duration / 1000);

             // 只有在有设备运行的情况下才显示提醒
            const deviceRunning = this.checkDeviceRunning();
            
            if (duration >= this.alertThreshold && !this.alertShown && !this.userAcknowledged && deviceRunning) {
                this.showModal(durationSeconds);
                this.alertShown = true;
            } else if (!deviceRunning && this.alertShown) {
                // 如果所有设备都已关闭，隐藏弹窗
                console.log('所有设备已关闭，隐藏异常状态提醒');
                this.hideModal();
                this.alertShown = false;
            }
        } else {
            // 有人状态，重置所有状态
            if (this.irrationalStartTime) {
                console.log('检测到有人，重置异常状态计时器');
                this.irrationalStartTime = null;
                this.alertShown = false;
                this.userAcknowledged = false; // 检测到人，重置确认状态
            }
        }
    }

    showModal(durationSeconds) {
        const modal = document.getElementById('irrational-modal');
        const durationSpan = document.getElementById('irrational-duration');

        if (modal && durationSpan) {
            durationSpan.textContent = durationSeconds;
            modal.classList.remove('hidden');

            // 添加显示动画
            setTimeout(() => {
                modal.style.opacity = '1';
                modal.style.transform = 'scale(1)';
                modal.style.transition = 'all 0.3s ease';
            }, 10);

            console.log(`显示异常状态提醒，持续时间: ${durationSeconds}秒`);
        }
    }

    hideModal() {
        const modal = document.getElementById('irrational-modal');
        if (modal) {
            modal.style.opacity = '0';
            modal.style.transform = 'scale(0.9)';
            modal.style.transition = 'all 0.3s ease';

            setTimeout(() => {
                modal.classList.add('hidden');
            }, 300);
        }
    }

    resetAlert() {
        // 不再重置alertShown，只重置计时器
        this.irrationalStartTime = null;
        console.log('重置异常状态检测');
    }

    autoCloseDevices() {
        console.log('执行自动关闭设备操作...');

        // 关闭小灯
        this.controlDevice('light', 0, 0);

        // 关闭风扇
        this.controlDevice('fan', 0, 0);

        // 显示操作成功提示
        this.showNotification('设备已自动关闭', 'success');
    }

    controlDevice(device, level, pwmValue) {
        // 使用命令中心模式，向服务器发送命令
        let fanLevel = device === 'fan' ? level : window.deviceControl.getDeviceStatus().fan;
        let lightLevel = device === 'light' ? level : window.deviceControl.getDeviceStatus().light;
        
        // 调用命令中心API
        fetch('/set_command', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                fan_level: fanLevel,
                light_level: lightLevel
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log(`${device}设备已设置到${level}挡`);
            } else {
                console.error(`设置${device}设备失败:`, data.msg);
            }
        })
        .catch(error => {
            console.error(`控制${device}设备时发生错误:`, error);
        });
    }

    showNotification(message, type = 'info') {
        // 创建通知元素
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 z-50 px-4 py-3 rounded-lg shadow-lg transition-all duration-300 transform translate-x-full ${this.getNotificationClass(type)}`;
        notification.innerHTML = `
            <div class="flex items-center">
                <i class="fa ${this.getNotificationIcon(type)} mr-2"></i>
                <span>${message}</span>
            </div>
        `;

        // 添加到页面
        document.body.appendChild(notification);

        // 显示动画
        setTimeout(() => {
            notification.classList.remove('translate-x-full');
            notification.classList.add('translate-x-0');
        }, 10);

        // 3秒后自动移除
        setTimeout(() => {
            notification.classList.remove('translate-x-0');
            notification.classList.add('translate-x-full');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }

    getNotificationClass(type) {
        switch (type) {
            case 'success': return 'bg-green-500/20 text-green-400 border border-green-400/30';
            case 'error': return 'bg-red-500/20 text-red-400 border border-red-400/30';
            case 'warning': return 'bg-yellow-500/20 text-yellow-400 border border-yellow-400/30';
            default: return 'bg-blue-500/20 text-blue-400 border border-blue-400/30';
        }
    }

    getNotificationIcon(type) {
        switch (type) {
            case 'success': return 'fa-check-circle';
            case 'error': return 'fa-exclamation-circle';
            case 'warning': return 'fa-exclamation-triangle';
            default: return 'fa-info-circle';
        }
    }

    // 销毁方法，用于清理资源
    destroy() {
        if (this.checkInterval) {
            clearInterval(this.checkInterval);
        }
    }
}

// 页面加载完成后初始化异常状态检测
document.addEventListener('DOMContentLoaded', function() {
    // 等待其他脚本加载完成
    setTimeout(() => {
        window.irrationalAlert = new IrrationalAlert();
        console.log('异常状态检测功能已启动');
        console.log('检测间隔:', window.irrationalAlert.checkInterval);
        console.log('弹窗阈值:', window.irrationalAlert.alertThreshold);
    }, 2000);
});

// 导出类供其他模块使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = IrrationalAlert;
}
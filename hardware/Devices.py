# device_control.py - 执行器控制+数据传输（SIoT+HTTP）
import siot
import requests
import json
from datetime import datetime

class DeviceControl:
    def __init__(self, hardware):
        self.hardware = hardware
        # 自动逻辑变量
        self.pir_timer = 0
        self.pwm_change_count = 0
        self.editor = None  # 新增：编辑器实例引用

    def set_editor(self, editor):
        """设置编辑器实例，用于获取挡位信息"""
        self.editor = editor

    # ========== 新增：PWM核心功能（初学者友好版） ==========
    # 1. 计算占空比（PWM值转百分比）
    def _calc_duty_cycle(self, pwm_value):
        """将PWM原始值（0-1023）转换为占空比（0-100%），保留1位小数"""
        duty = round(pwm_value / 1023 * 100, 1)
        return duty

    # 2. 模拟PWM值变化（测试用，模拟挡位切换）
    def simulate_pwm_change(self):
        """每2秒改变一次PWM值，模拟占空比变化（30%→60%→100%→30%循环）"""
        self.pwm_change_count += 1
        if self.pwm_change_count % 2 != 0:  # 每2秒触发一次
            return
        
        # 遍历所有PWM设备，更新值
        for device in self.hardware.pwm_devices:
            # 每次增加205（≈1023*20%），超过1023则重置为307（30%）
            device["current_pwm_value"] = (device["current_pwm_value"] + 205) % 1024
            if device["current_pwm_value"] < 307:  # 保底30%
                device["current_pwm_value"] = 307
            # 更新占空比
            device["current_duty_cycle"] = self._calc_duty_cycle(device["current_pwm_value"])
            # 写入新的PWM值到引脚（实际控制设备）
            device["pin"].write_analog(device["current_pwm_value"])
            # 计算功率
            self.hardware._calc_device_power(device)
        
        fan = self.hardware.pwm_devices[0]
        light = self.hardware.pwm_devices[1]

    # 3. 获取所有PWM设备的实时数据（给前端用）
    def get_pwm_data(self):
        """返回PWM设备的名称、原始值、占空比、功率和挡位"""
        pwm_data = []
        for device in self.hardware.pwm_devices:
            # 获取挡位信息
            level = 0
            if self.editor:
                if device["name"] == "风扇":
                    level = self.editor.current_fan_level
                elif device["name"] == "小灯":
                    level = self.editor.current_light_level
            
            pwm_data.append({
                "name": device["name"],
                "pwm_value": device["current_pwm_value"],
                "duty_cycle": device["current_duty_cycle"],
                "power": device["current_power"],
                "level": level  # 新增：挡位信息
            })
        return pwm_data

    # ========== 数据传输 ==========
    # 原有SIoT上传（保留）
    def send_data_siot(self, temp, humi, light_val, pir):
        status = "有人" if pir == 1 else "无人"
        pwm_data = self.get_pwm_data()
        fan_duty = pwm_data[0]["duty_cycle"]
        light_duty = pwm_data[1]["duty_cycle"]
        data = f"温度:{temp} 湿度:{humi} 光照:{light_val} 红外:{status} 风扇占空比:{fan_duty}% 小灯占空比:{light_duty}%"
        siot.publish(self.hardware.TOPIC, data)

    # 新增：HTTP上传到VS Code后端（核心）
    def send_data_http(self, sensor_data):
        if not sensor_data:
            print("无有效数据，跳过HTTP发送")
            return False
        # 补充时间戳,pwm
        sensor_data["pwm_devices"] = self.get_pwm_data()
        sensor_data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            # 发送POST请求到电脑后端
            response = requests.post(
                url=self.hardware.HTTP_API,
                json=sensor_data,  # 发送JSON格式数据
                timeout=5          # 超时5秒
            )
            if response.status_code == 200:
                print(f"✅ HTTP数据发送成功：{sensor_data}")
                return True
            else:
                print(f"❌ HTTP发送失败，状态码：{response.status_code}")
                return False
        except Exception as e:
            print(f"❌ HTTP发送异常：{e}")
            return False
# Editor.py - 按钮界面控制模块（简化版，只用A/B键）
import time
from pinpong.extension.unihiker import button_a, button_b

class Editor:
    def __init__(self, hardware, device_control):
        self.hardware = hardware
        self.device_control = device_control
        
        # 状态变量 - 修改挡位设置
        # 风扇挡位：40%，70%，100% 对应PWM值
        self.fan_levels = [0, 409, 716, 1023]  # PWM值对应0%, 40%, 70%, 100%
        # 小灯挡位：30%，60%，100% 对应PWM值
        self.light_levels = [0, 307, 614, 1023]  # PWM值对应0%, 30%, 60%, 100%
        
        # 默认挡位设置为1（40%和30%）
        self.current_fan_level = 1  # 默认1档（40%）
        self.current_light_level = 1  # 默认1档（30%）
        
        # 防抖变量
        self.last_button_time = 0
        self.button_debounce = 0.3  # 300ms防抖时间
        
        # 初始化设备到默认档位
        self._apply_fan_level(self.current_fan_level)
        self._apply_light_level(self.current_light_level)
        
        print("编辑器初始化完成 - 使用A键调节小灯档位，B键调节风扇档位")
        print(f"风扇初始档位: {self.current_fan_level}档 ({self._calc_duty_cycle(self.fan_levels[self.current_fan_level])}%)")
        print(f"小灯初始档位: {self.current_light_level}档 ({self._calc_duty_cycle(self.light_levels[self.current_light_level])}%)")
    
    def check_buttons(self):
        """检查按钮状态（在主循环中调用）"""
        current_time = time.time()
        
        # 防抖检查
        if current_time - self.last_button_time < self.button_debounce:
            return False
        
        button_pressed = False
        
        # 检查A按钮（小灯控制）
        if button_a.is_pressed():
            self.last_button_time = current_time
            self._increase_light_level()
            button_pressed = True
            time.sleep(0.1)
        
        # 检查B按钮（风扇控制）
        if button_b.is_pressed():
            self.last_button_time = current_time
            self._increase_fan_level()
            button_pressed = True
            time.sleep(0.1)
        
        return button_pressed
    
    def _increase_fan_level(self):
        """增加风扇档位，循环切换"""
        self.current_fan_level = (self.current_fan_level + 1) % len(self.fan_levels)
        self._apply_fan_level(self.current_fan_level)
        duty_cycle = self._calc_duty_cycle(self.fan_levels[self.current_fan_level])
        print(f"风扇档位: {self.current_fan_level}档 ({duty_cycle}%)")
        return True
    
    def _increase_light_level(self):
        """增加小灯档位，循环切换"""
        self.current_light_level = (self.current_light_level + 1) % len(self.light_levels)
        self._apply_light_level(self.current_light_level)
        duty_cycle = self._calc_duty_cycle(self.light_levels[self.current_light_level])
        print(f"小灯档位: {self.current_light_level}档 ({duty_cycle}%)")
        return True
    
    def _apply_fan_level(self, level):
        """应用风扇档位设置"""
        pwm_value = self.fan_levels[level]
        for device in self.hardware.pwm_devices:
            if device["name"] == "风扇":
                device["current_pwm_value"] = pwm_value
                device["current_duty_cycle"] = self._calc_duty_cycle(pwm_value)
                device["pin"].write_analog(pwm_value)
                self.hardware._calc_device_power(device)
                break
    
    def _apply_light_level(self, level):
        """应用小灯档位设置"""
        pwm_value = self.light_levels[level]
        for device in self.hardware.pwm_devices:
            if device["name"] == "小灯":
                device["current_pwm_value"] = pwm_value
                device["current_duty_cycle"] = self._calc_duty_cycle(pwm_value)
                device["pin"].write_analog(pwm_value)
                self.hardware._calc_device_power(device)
                break
    
    def _calc_duty_cycle(self, pwm_value):
        """计算占空比"""
        return round(pwm_value / 1023 * 100, 1)
    
    def get_current_status(self):
        """获取当前状态信息"""
        fan_duty = self._calc_duty_cycle(self.fan_levels[self.current_fan_level])
        light_duty = self._calc_duty_cycle(self.light_levels[self.current_light_level])
        
        return {
            "fan_level": self.current_fan_level,
            "fan_duty": fan_duty,
            "light_level": self.current_light_level,
            "light_duty": light_duty
        }
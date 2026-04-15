# ScreenDisplay.py - 行空板屏幕显示模块（兼容所有版本，移除传感器数据）
from unihiker import GUI
import time
from Devices import DeviceControl
from Hardware import HardwareInit


class ScreenDisplay:
    def __init__(self):
        # 初始化行空板GUI
        self.gui = GUI()
        # 屏幕分辨率（行空板：320x240）
        self.screen_width = 320
        self.screen_height = 240
        
        # 存储文本参数（仅保留核心显示内容）
        self.text_params = {
            "title": {"text": "智能家居系统", "x": 160, "y": 30, "size": 18, "color": "#FFFFFF"},
            "interface": {"text": "选择界面", "x": 160, "y": 80, "size": 18, "color": "#FFFF00"},
            "status": {"text": "LED:0挡 | 风扇:0挡", "x": 160, "y": 130, "size": 16, "color": "#00FF00"},
            "tips": {"text": "A1/A2操作 | HOME返回", "x": 160, "y": 200, "size": 12, "color": "#888888"}
        }
        # 清空屏幕（初始化背景）
        self.gui.clear()


    def _draw_all_text(self):
        """绘制所有文本（适配不同API）"""
        # 清空屏幕（避免文字重叠）
        self.gui.clear()

        
        
        self.gui.draw_text(
            x=self.text_params["title"]["x"],
            y=self.text_params["title"]["y"],
            text=self.text_params["title"]["text"],
            font_size=self.text_params["title"]["size"],
            color=self.text_params["title"]["color"],
            anchor="center"
        )
        self.gui.draw_text(
            x=self.text_params["interface"]["x"],
            y=self.text_params["interface"]["y"],
            text=self.text_params["interface"]["text"],
            font_size=self.text_params["interface"]["size"],
            color=self.text_params["interface"]["color"],
            anchor="center"
        )
        self.gui.draw_text(
            x=self.text_params["status"]["x"],
            y=self.text_params["status"]["y"],
            text=self.text_params["status"]["text"],
            font_size=self.text_params["status"]["size"],
            color=self.text_params["status"]["color"],
            anchor="center"
        )
        self.gui.draw_text(
            x=self.text_params["tips"]["x"],
            y=self.text_params["tips"]["y"],
            text=self.text_params["tips"]["text"],
            font_size=self.text_params["tips"]["size"],
            color=self.text_params["tips"]["color"],
            anchor="center"
        )
        # 旧版需手动刷新屏幕
        self.gui.refresh()

    def update(self, device, sensor_data=None):
        """更新屏幕显示（核心方法）
        :param device: DeviceControl实例（包含界面/挡位信息）
        :param sensor_data: 传感器数据（可选，此处无实际作用）
        """
        # 1. 更新界面名称
        interface_map = {0: "选择界面", 1: "LED控制界面", 2: "风扇控制界面"}
        self.text_params["interface"]["text"] = interface_map.get(device.current_interface, "选择界面")
        
        # 2. 更新设备挡位
        # 根据当前界面显示更合适的状态信息
        if device.current_interface == 0:
            # 选择界面显示完整状态
            self.text_params["status"]["text"] = f"LED:{device.current_led_gear}挡 | 风扇:{device.current_fan_gear}挡"
            self.text_params["tips"]["text"] = "A1=LED控制 | A2=风扇控制"
        elif device.current_interface == 1:
            # LED控制界面
            gear_text = "关闭" if device.current_led_gear == 0 else f"{device.current_led_gear}挡"
            self.text_params["status"]["text"] = f"LED状态: {gear_text}"
            self.text_params["tips"]["text"] = "A1=加挡 | A2=减挡 | HOME=返回"
        elif device.current_interface == 2:
            # 风扇控制界面
            gear_text = "关闭" if device.current_fan_gear == 0 else f"{device.current_fan_gear}挡"
            self.text_params["status"]["text"] = f"风扇状态: {gear_text}"
            self.text_params["tips"]["text"] = "A1=加挡 | A2=减挡 | HOME=返回"
        
        # 重新绘制所有文本（无需传感器数据）
        self._draw_all_text()

    def set_background(self, color="#000000"):
        """设置屏幕背景色（兼容版）"""
        self.gui.fill_rect(color=color)

    def show_tips(self, text, color="#FF0000", duration=2):
        """临时显示提示文字"""
        # 保存原提示文字
        old_tips = self.text_params["tips"]["text"]
        old_color = self.text_params["tips"]["color"]
        
        # 更新提示文字
        self.text_params["tips"]["text"] = text
        self.text_params["tips"]["color"] = color
        self._draw_all_text()
        
        # 延时恢复
        time.sleep(duration)
        self.text_params["tips"]["text"] = old_tips
        self.text_params["tips"]["color"] = old_color
        self._draw_all_text()
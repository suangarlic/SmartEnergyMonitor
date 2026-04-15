# UI.py - 行空板界面显示模块（修复版）
from unihiker import GUI
import time

class UnihikerUI:
    def __init__(self, editor):
        self.gui = GUI()
        self.editor = editor
        self.screen_width = 240
        self.screen_height = 320
        
        # 存储进度条对象的列表，用于动态更新
        self.progress_bars = {}
        
        # 初始化UI元素
        self.init_ui()
        
    def init_ui(self):
        """初始化用户界面"""
        # 清空屏幕
        self.gui.clear()
        
        # 标题
        self.title = self.gui.draw_text(x=120, y=20, text="智能家居控制系统", 
                                       color="black", font_size=14, origin='center')
        
        # 风扇相关UI元素
        self.fan_title = self.gui.draw_text(x=20, y=60, text="风扇控制:", 
                                          color="blue", font_size=12, origin='top_left')
        
        # 风扇进度条背景（使用draw_rect而不是fill_rect）
        self.fan_progress_bg = self.gui.draw_rect(x=20, y=85, w=200, h=20, 
                                               color="lightgray", fill="lightgray")
        
        # 风扇进度条前景（初始40%）
        fan_width = 80  # 40% of 200
        self.fan_progress = self.gui.draw_rect(x=20, y=85, w=fan_width, h=20, 
                                            color="#1E90FF", fill="#1E90FF")
        
        # 风扇挡位显示
        self.fan_level_text = self.gui.draw_text(x=120, y=95, text="1档 (40%)", 
                                               color="white", font_size=10, origin='center')
        
        # 小灯相关UI元素
        self.light_title = self.gui.draw_text(x=20, y=130, text="小灯控制:", 
                                            color="orange", font_size=12, origin='top_left')
        
        # 小灯进度条背景
        self.light_progress_bg = self.gui.draw_rect(x=20, y=155, w=200, h=20, 
                                                  color="lightgray", fill="lightgray")
        
        # 小灯进度条前景（初始30%）
        light_width = 60  # 30% of 200
        self.light_progress = self.gui.draw_rect(x=20, y=155, w=light_width, h=20, 
                                               color="#FFA500", fill="#FFA500")
        
        # 小灯挡位显示
        self.light_level_text = self.gui.draw_text(x=120, y=165, text="1档 (30%)", 
                                                  color="white", font_size=10, origin='center')
        
        # 操作提示
        self.help_text = self.gui.draw_text(x=120, y=200, 
                                          text="A键:小灯挡位  B键:风扇挡位", 
                                          color="green", font_size=10, origin='center')
        
        # 传感器数据显示区域
        self.temp_text = self.gui.draw_text(x=20, y=230, text="温度: --.-°C", 
                                          color="black", font_size=10, origin='top_left')
        self.humi_text = self.gui.draw_text(x=20, y=250, text="湿度: --.-%", 
                                          color="black", font_size=10, origin='top_left')
        self.light_text = self.gui.draw_text(x=20, y=270, text="光照: ---", 
                                           color="black", font_size=10, origin='top_left')
        self.pir_text = self.gui.draw_text(x=20, y=290, text="红外: ---", 
                                          color="black", font_size=10, origin='top_left')
        
        print("UI界面初始化完成")
    
    def update_progress_bars(self):
        """更新进度条显示（修复版，使用config方法）"""
        status = self.editor.get_current_status()
        
        # 计算进度条宽度（0-200像素对应0-100%）
        fan_width = int(status['fan_duty'] * 2)  # 百分比转像素宽度
        light_width = int(status['light_duty'] * 2)
        
        # 限制宽度在0-200之间
        fan_width = max(0, min(200, fan_width))
        light_width = max(0, min(200, light_width))
        
        # 修复：使用config方法更新现有图形对象[1](@ref)
        try:
            # 方法1：使用config方法更新宽度（推荐方式）
            self.fan_progress.config(w=fan_width)
            self.light_progress.config(w=light_width)
        except AttributeError as e:
            # 方法2：如果config方法不可用，重新绘制进度条
            print(f"config方法不可用，使用重绘方式: {e}")
            try:
                # 尝试移除旧进度条
                if hasattr(self.fan_progress, 'undraw'):
                    self.fan_progress.undraw()
                if hasattr(self.light_progress, 'undraw'):
                    self.light_progress.undraw()
            except:
                pass
            
            # 重新绘制进度条
            self.fan_progress = self.gui.draw_rect(x=20, y=85, w=fan_width, h=20, 
                                                  color="#1E90FF", fill="#1E90FF")
            self.light_progress = self.gui.draw_rect(x=20, y=155, w=light_width, h=20, 
                                                   color="#FFA500", fill="#FFA500")
        
        # 更新挡位文字[1](@ref)
        self.fan_level_text.config(text=f"{status['fan_level']}档 ({status['fan_duty']}%)")
        self.light_level_text.config(text=f"{status['light_level']}档 ({status['light_duty']}%)")
        
        print(f"UI更新: 风扇{status['fan_level']}档({status['fan_duty']}%), 小灯{status['light_level']}档({status['light_duty']}%)")
    
    def update_sensor_data(self, sensor_data):
        """更新传感器数据显示"""
        temp = sensor_data.get("temperature", "--.-")
        humi = sensor_data.get("humidity", "--.-")
        light_val = sensor_data.get("light", "---")
        pir_status = sensor_data.get("pir_status", "---")
        
        # 更新文本显示[1](@ref)
        self.temp_text.config(text=f"温度: {temp}°C")
        self.humi_text.config(text=f"湿度: {humi}%")
        self.light_text.config(text=f"光照: {light_val}")
        self.pir_text.config(text=f"红外: {pir_status}")
    
    def show_message(self, message, duration=2):
        """显示临时消息"""
        try:
            msg = self.gui.draw_text(x=120, y=310, text=message, 
                                   color="red", font_size=10, origin='center')
            time.sleep(duration)
            # 尝试移除消息
            if hasattr(msg, 'undraw'):
                msg.undraw()
            elif hasattr(msg, 'config'):
                msg.config(text="")  # 清空文本
        except Exception as e:
            print(f"显示消息时出错: {e}")
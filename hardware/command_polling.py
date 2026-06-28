# command_polling.py - 行空板命令接收器（HTTP轮询模式，兼容所有环境）
import json
import time
import threading
import urllib.request
import urllib.error
from config import PC_IP, PC_PORT

class CommandPoller:
    """行空板命令接收器 - 使用HTTP轮询获取命令"""
    
    def __init__(self, editor=None, interval=2):
        """
        初始化命令接收器
        :param editor: Editor实例，用于应用命令
        :param interval: 轮询间隔（秒）
        """
        self.editor = editor
        self.api_url = f"http://{PC_IP}:{PC_PORT}/get_command"
        self.last_command = {"fan_level": 0, "light_level": 0}
        self.running = False
        self.thread = None
        self.interval = interval
        
    def _apply_command(self, command):
        """
        应用命令：对比设备实际状态，只在有变化时执行
        """
        if not command or not self.editor:
            return False
        
        changes = False
        
        # 检查风扇挡位变化（对比设备实际挡位，而非历史命令）
        target_fan = command.get("fan_level")
        if target_fan is not None and target_fan != self.editor.current_fan_level:
            print("[Command] Fan level:", self.editor.current_fan_level, "->", target_fan)
            self.editor.current_fan_level = target_fan
            self.editor._apply_fan_level(target_fan)
            changes = True
        
        # 检查小灯挡位变化（对比设备实际挡位，而非历史命令）
        target_light = command.get("light_level")
        if target_light is not None and target_light != self.editor.current_light_level:
            print("[Command] Light level:", self.editor.current_light_level, "->", target_light)
            self.editor.current_light_level = target_light
            self.editor._apply_light_level(target_light)
            changes = True
        
        return changes
    
    def _fetch_command(self):
        """从服务器获取命令"""
        try:
            response = urllib.request.urlopen(self.api_url, timeout=5)
            data = response.read().decode('utf-8')
            return json.loads(data)
        except urllib.error.URLError as e:
            print("[Command] Fetch error:", str(e))
            return None
        except json.JSONDecodeError as e:
            print("[Command] JSON parse error:", str(e))
            return None
        except Exception as e:
            print("[Command] Unexpected error:", str(e))
            return None
    
    def _poll_loop(self):
        """轮询循环"""
        print("[Command] Polling started, interval:", self.interval, "s")
        while self.running:
            try:
                command = self._fetch_command()
                if command:
                    print(f"[Command] 收到: fan={command.get('fan_level')}, light={command.get('light_level')}")
                    self._apply_command(command)
            except Exception as e:
                print("[Command] Polling error:", str(e))
            time.sleep(self.interval)
    
    def start(self):
        """启动轮询"""
        if self.running:
            print("[Command] Already running")
            return
        
        self.running = True
        print("[Command] v2.0 - 对比设备实际状态（非历史命令）")
        print("[Command] Starting command poller, server:", self.api_url)
        self.thread = threading.Thread(target=self._poll_loop, daemon=True)
        self.thread.start()
    
    def stop(self):
        """停止轮询"""
        self.running = False


# 为保持兼容性，保留旧类名
CommandWebSocket = CommandPoller

# ========== 使用示例 ==========
# from command_polling import CommandPoller
# command_poller = CommandPoller(editor=editor_instance)
# command_poller.start()
# main.py - 主程序（严格适配数据库短字段名）
import time
# 导入自定义模块
from Hardware import HardwareInit
from Sensors import SensorCollect
from Devices import DeviceControl
from Editor import Editor
from UI import UnihikerUI
import json
import os
from datetime import datetime, timedelta

import threading
from command_polling import CommandWebSocket  # 改为 WebSocket


# 程序入口
if __name__ == "__main__":
    # 1. 初始化硬件
    hardware = HardwareInit()
    # 2. 初始化传感器采集
    sensor = SensorCollect(hardware)
    # 3. 初始化设备控制
    device = DeviceControl(hardware)
    # 4. 初始化编辑器
    editor = Editor(hardware, device)
    # 5. 初始化 UI
    ui = UnihikerUI(editor)
    # 6. 设置设备控制的编辑器引用（新增）
    device.set_editor(editor)

    print("===== 智能家居系统启动 =====")
    print("操作说明: A键-调节小灯档位, B键-调节风扇档位")
    print("-" * 40)

    # 启动 WebSocket 命令接收器（替代轮询）
    command_ws = CommandWebSocket(editor=editor)
    command_ws.start()
    print("[命令中心] WebSocket 命令接收器已启动")

    # 数据采集间隔设置（单位：秒）
    COLLECTION_INTERVAL = 5 
    # 记录上次数据采集的时间
    last_collection_time = time.time()
    
    # 主循环
    while True:
        # 检查按钮输入（实时）
        if editor.check_buttons():
            ui.update_progress_bars()
        
        # 实时采集传感器数据用于UI更新
        sensor_data = sensor.get_all_data()
        temp = sensor_data["temperature"]
        humi = sensor_data["humidity"]
        light_val = sensor_data["light"]
        pir = sensor_data["pir"]

        # UI 显示更新（实时）
        ui.update_sensor_data(sensor_data)
        
        # 检查是否达到数据采集间隔
        current_time = time.time()
        if current_time - last_collection_time >= COLLECTION_INTERVAL:
            # ======================================
            # 数据采集完成，准备发送到web端
            # ======================================
            record_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 控制台打印
            now = datetime.now()
            print(f"\n【时间】{now}")
            print(f"温度：{temp}℃")
            print(f"湿度：{humi}%")
            print(f"光照：{light_val}")
            print(f"红外：{sensor_data['pir_status']}")

            status = editor.get_current_status()
            print(f"风扇档位：{status['fan_level']}档 ({status['fan_duty']}%)")
            print(f"小灯档位：{status['light_level']}档 ({status['light_duty']}%)")

            # 数据上传到web端（web端负责数据库存储）
            device.send_data_siot(temp, humi, light_val, pir)
            device.send_data_http(sensor_data)
            print("[HTTP] 数据已发送到web端")

          
            
            # 更新上次数据采集时间
            last_collection_time = current_time
        
        # 循环间隔（保持UI响应性）
        time.sleep(1)
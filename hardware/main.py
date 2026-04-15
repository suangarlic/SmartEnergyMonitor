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
from database import save_sensor_data, get_db_connection
import threading
import ai_http


# ===============================
# 从数据库读取最近 "一天" 数据 → 使用新的合并表结构
# ===============================
def load_last_day_from_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 过去 24 小时
    threshold = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")

    # 使用新的表结构字段名查询
    cursor.execute("""
        SELECT id, temperature, humidity, light, pir, pir_status, 
               pwm_f, pwm_l, power_f, power_l, level_f, level_l, 
               timestamp, create_at
        FROM sensor_data
        WHERE create_at >= ?
        ORDER BY id ASC
    """, (threshold,))

    rows = cursor.fetchall()

    history = []
    for row in rows:
        # 处理NULL值，统一替换为"--"
        temperature = row["temperature"] if row["temperature"] is not None else "--"
        humidity = row["humidity"] if row["humidity"] is not None else "--"
        light = row["light"] if row["light"] is not None else "--"
        pir = row["pir"] if row["pir"] is not None else 0
        pir_status = row["pir_status"] if row["pir_status"] is not None else "--"
        timestamp = row["timestamp"] if row["timestamp"] is not None else "--"
        
        # 处理设备数据（现在直接包含在sensor_data表中）
        pwm_list = []
        
        # 风扇设备数据
        pwm_f = row["pwm_f"] if row["pwm_f"] is not None else "--"
        power_f = row["power_f"] if row["power_f"] is not None else "--"
        level_f = row["level_f"] if row["level_f"] is not None else 0
        
        # 小灯设备数据
        pwm_l = row["pwm_l"] if row["pwm_l"] is not None else "--"
        power_l = row["power_l"] if row["power_l"] is not None else "--"
        level_l = row["level_l"] if row["level_l"] is not None else 0
        
        # 构建设备数据列表
        pwm_list.append({
            "dev": "风扇",
            "duty": pwm_f,
            "pow": power_f,
            "level": level_f
        })
        pwm_list.append({
            "dev": "小灯",
            "duty": pwm_l,
            "pow": power_l,
            "level": level_l
        })

        # 构建历史记录
        history.append({
            "id": row["id"],
            "t": temperature,        # 温度
            "h": humidity,           # 湿度
            "l": light,              # 光照
            "pir": pir,              # 红外
            "ps": pir_status,        # PIR状态
            "ts": timestamp,         # 时间戳
            "pwm": pwm_list          # PWM设备数据
        })

    conn.close()
    return history

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

    # 启动AI HTTP服务器并传递editor实例
    ai_http.set_editor(editor)
    t = threading.Thread(target=ai_http.run_server, kwargs={'host': '0.0.0.0', 'port': 5005}, daemon=True)
    t.start()

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
            # 写入数据库（database.py已适配，无需修改）
            # ======================================
            record_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            db_record = {
                "temperature": sensor_data["temperature"],
                "humidity": sensor_data["humidity"],
                "light": sensor_data["light"],
                "pir": sensor_data["pir"],
                "pir_status": sensor_data["pir_status"],
                "timestamp": record_timestamp,
                "pwm_devices": device.get_pwm_data()
            }

            if save_sensor_data(db_record):
                print("[数据库] 数据已写入 sensor_data.db")
            else:
                print("[数据库] ❌ 写入失败")

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

            # 数据上传
            device.send_data_siot(temp, humi, light_val, pir)
            device.send_data_http(sensor_data)

            # ======================================
            # 生成data.json（严格使用数据库字段名）
            # ======================================
            history = load_last_day_from_db()
            with open("data.json", "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
            
            # 更新上次数据采集时间
            last_collection_time = current_time
        
        # 循环间隔（保持UI响应性）
        time.sleep(1)
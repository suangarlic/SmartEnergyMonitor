from flask import Flask, render_template, request, jsonify
import threading
import time
import os
from database import save_sensor_data, clean_old_data, get_db_connection, create_tables
from AI_API import AIAnalyzer
import requests
import sys
app = Flask(__name__)

import requests
import sys

app = Flask(__name__)

# 重新加载配置
sys.path.append(os.path.abspath('..'))

# 直接设置正确的行空板IP地址
BOARD_BASE_URL = 'http://10.1.2.3:5005'
print(f"手动设置的BOARD_BASE_URL: {BOARD_BASE_URL}")


# 存储最新传感器数据（初始值）
latest_data = {
    "temperature": "--",
    "humidity": "--",
    "light": "--",
    "pir": 0,
    "pir_status": "--",
    "timestamp": "--",
    "pwm_devices": [        {"name": "风扇", "duty_cycle": "--", "power": "--"},
        {"name": "小灯", "duty_cycle": "--", "power": "--"}
    ]
}

# 定时清理过期数据
def scheduled_cleanup():
    while True:
        time.sleep(3600)
        clean_old_data()

# 初始化数据库表结构
create_tables()
print("数据库表结构初始化完成")

# 后台清理线程（清理统一数据库中的过期数据）
cleanup_thread = threading.Thread(target=scheduled_cleanup, daemon=True)
cleanup_thread.start()
print("定时清理任务已启动（清理统一数据库中的过期数据）")

# 1. 前端主页
@app.route('/')
def index():
    return render_template('index.html')

# 2. 接收行空板上报的传感器数据
@app.route('/api/sensor_data', methods=['POST'])
def receive_data():
    global latest_data

    data = request.get_json()
    if data:
        latest_data = data
        # 紧凑格式显示（不换行）
        import json
        compact_json = json.dumps(data, separators=(',', ':'))
        print(f"✅ 收到行空板数据：{compact_json}")
 # 检查是否是横向键值对格式
        if "light" in data and "humi" in data:  # 横向键值对格式
            print(f"✅ 收到横向键值对格式数据：{compact_json}")
            
            # 转换为完整格式用于前端显示和数据库存储
            pir_status = "有人" if data.get("pir", 0) == 1 else "无人"
            
            full_data = {
                "temperature": data.get("temp", 0),
                "humidity": data.get("humi", 0),
                "light": data.get("light", 0),
                "pir": data.get("pir", 0),
                "pir_status": pir_status,
                "timestamp": data.get("time", "--"),
                "pwm_devices": [
                    {
                        "name": "风扇",
                        "duty_cycle": "--",
                        "power": data.get("fan_power", 0),
                        "level": data.get("fan_level", 0)
                    },
                    {
                        "name": "小灯",
                        "duty_cycle": "--",
                        "power": data.get("light_power", 0),
                        "level": data.get("light_level", 0)
                    }
                ]
            }
            
            # 保存完整格式用于前端显示
            latest_data = full_data
            
            # 保存完整格式到数据库
            if save_sensor_data(full_data):
                print("数据已成功保存到数据库")
            else:
                print("⚠ 警告：数据保存到数据库失败")
                
        else:  # 原始格式（兼容性）
            print(f"✅ 收到原始格式数据：{compact_json}")
            
            # 保存原始格式用于前端显示
            latest_data = data
            
            if save_sensor_data(data):
                print("数据已成功保存到数据库")
            else:
                print("⚠ 警告：数据保存到数据库失败")

        return jsonify({"status": "success", "msg": "数据已接收并保存"})

    return jsonify({"status": "error", "msg": "无数据"}), 400

# 3. 前端拉取最新数据
@app.route('/api/get_latest_data')
def get_data():
    return jsonify(latest_data)


# 4. 新增：获取AI节能建议内容的接口
@app.route('/api/get_ai_advice')
def get_ai_advice():
    """
    读取并返回advice.txt文件的内容，供前端显示
    """
    try:
        advice_content = ""
        advice_mtime = None
        advice_ts = "--"
        if os.path.exists("advice.txt"):
            # 读取内容
            with open("advice.txt", 'r', encoding='utf-8') as f:
                advice_content = f.read()
            # 获取文件最后修改时间（unix timestamp）并格式化为本地时间字符串
            advice_mtime = os.path.getmtime("advice.txt")
            advice_ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(advice_mtime))

        # 返回建议内容，包含原始 mtime（用于前端比对）和格式化时间
        return jsonify({
            "success": True,
            "content": advice_content,
            "mtime": advice_mtime,
            "timestamp": advice_ts
        })
    except Exception as e:
        print(f"读取advice.txt失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# 5. 新增：前端点击按钮执行 AI 分析
@app.route('/run_ai', methods=['POST'])
def run_ai():
    """本地执行AI分析，不再请求hardware端"""
    try:
        # 从数据库获取最近24小时的数据
        from datetime import datetime, timedelta
        threshold = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, temperature, humidity, light, pir, pir_status, 
                   pwm_f, pwm_l, power_f, power_l, level_f, level_l, 
                   timestamp, create_at
            FROM sensor_data
            WHERE create_at >= ?
            ORDER BY create_at DESC
            LIMIT 100
        """, (threshold,))
        
        rows = cursor.fetchall()
        conn.close()
        
        # 转换为字典列表
        recent_records = [dict(row) for row in rows]
        
        if not recent_records:
            return jsonify({
                "success": False, 
                "msg": "暂无数据可供分析"
            }), 400
        
        print(f"正在分析 {len(recent_records)} 条最近数据...")
        
        # 调用本地AI分析器
        analyzer = AIAnalyzer()
        result = analyzer.send_to_ai(recent_records)
        
        # 保存AI建议到文件
        with open("advice.txt", "w", encoding="utf-8") as f:
            f.write(result)
        
        print("AI分析完成，建议已保存到advice.txt")
        
        return jsonify({
            "success": True,
            "msg": "AI分析完成",
            "advice": result
        })
        
    except Exception as e:
        print(f"AI分析失败: {e}")
        return jsonify({
            "success": False, 
            "msg": f"AI分析失败: {str(e)}"
        }), 500
# 6. 行空板控制接口
@app.route('/start_board_main', methods=['POST'])
def start_board_main():
    try:
        resp = requests.post(f'{BOARD_BASE_URL}/start_main', timeout=10)
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify({"success": False, "msg": f"请求行空板启动失败: {e}"}), 500

@app.route('/stop_board_main', methods=['POST'])
def stop_board_main():
    try:
        resp = requests.post(f'{BOARD_BASE_URL}/stop_main', timeout=10)
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify({"success": False, "msg": f"请求行空板终止失败: {e}"}), 500

# 7. 新增：通过网络更新行空板配置文件的接口
@app.route('/update_board_config', methods=['POST'])
def update_board_config():
    """通过网络API更新行空板上的配置文件"""
    try:
        # 获取请求参数
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "msg": "缺少请求数据"}), 400
        
        pc_ip = data.get('pc_ip')
        board_ip = data.get('board_ip')
        
        if not pc_ip or not board_ip:
            return jsonify({"success": False, "msg": "缺少必要的参数: pc_ip 和 board_ip"}), 400
        
        # 构建API请求URL
        api_url = f"http://{board_ip}:5005/update_config"
        
        # 准备请求数据
        request_data = {
            "pc_ip": pc_ip,
            "board_ip": board_ip
        }
        
        # 发送POST请求
        response = requests.post(api_url, json=request_data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"成功通过网络API更新行空板配置文件")
                print(f"更新结果: {result}")
                return jsonify({
                    "success": True, 
                    "msg": "行空板配置文件更新成功",
                    "board_response": result
                })
            else:
                print(f"行空板API返回错误: {result.get('msg')}")
                return jsonify({
                    "success": False, 
                    "msg": f"行空板API返回错误: {result.get('msg')}",
                    "board_response": result
                }), 500
        else:
            print(f"行空板API请求失败，状态码: {response.status_code}")
            return jsonify({
                "success": False, 
                "msg": f"行空板API请求失败，状态码: {response.status_code}"
            }), 500
            
    except Exception as e:
        print(f"通过网络API更新行空板配置失败: {e}")
        return jsonify({
            "success": False, 
            "msg": f"通过网络API更新行空板配置失败: {str(e)}"
        }), 500

# 8. 新增：设备控制接口
@app.route('/control_device', methods=['POST'])
def control_device():
    """控制行空板上的设备（灯和风扇）挡位"""
    try:
        # 获取请求参数
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "msg": "缺少请求数据"}), 400
        
        device = data.get('device')  # 'light' 或 'fan'
        level = data.get('level')    # 0-3
        pwm_value = data.get('pwm_value')  # PWM值
        
        if device not in ['light', 'fan']:
            return jsonify({"success": False, "msg": "设备类型错误，必须是 'light' 或 'fan'"}), 400
        
        if level is None or not (0 <= level <= 3):
            return jsonify({"success": False, "msg": "挡位参数错误，必须是 0-3"}), 400
        
        # 构建控制命令发送到行空板
        # 这里需要根据demo/Editor.py中的逻辑来构建控制命令
        control_data = {
            "device": device,
            "level": level,
            "pwm_value": pwm_value,
            "action": "set_level"
        }
        
        # 发送到行空板的设备控制API
        api_url = f"{BOARD_BASE_URL}/control_device"
        response = requests.post(api_url, json=control_data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                device_name = "小灯" if device == "light" else "风扇"
                print(f"成功控制{device_name}挡位: 挡位{level}, PWM值{pwm_value}")
                return jsonify({
                    "success": True,
                    "msg": f"{device_name}挡位已设置为{level}档",
                    "device": device,
                    "level": level,
                    "pwm_value": pwm_value
                })
            else:
                return jsonify({
                    "success": False,
                    "msg": f"行空板控制失败: {result.get('msg', '未知错误')}"
                }), 500
        else:
            return jsonify({
                "success": False,
                "msg": f"行空板API请求失败，状态码: {response.status_code}"
            }), 500
            
    except Exception as e:
        print(f"设备控制失败: {e}")
        return jsonify({
            "success": False,
            "msg": f"设备控制失败: {str(e)}"
        }), 500
    
# 9. 新增：数据统计和计算接口
@app.route('/api/data_statistics', methods=['GET'])
def get_data_statistics():
    """获取数据统计信息：平均值、最大值、最小值等"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取过去24小时的数据
        from datetime import datetime, timedelta
        threshold = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute("""
            SELECT temperature, humidity, light, power_f, power_l
            FROM sensor_data
            WHERE create_at >= ?
            AND temperature != '--' AND humidity != '--' AND light != '--'
        """, (threshold,))
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return jsonify({
                "success": True,
                "data": {
                    "temperature": {"avg": 0, "max": 0, "min": 0},
                    "humidity": {"avg": 0, "max": 0, "min": 0},
                    "light": {"avg": 0, "max": 0, "min": 0},
                    "power_f": {"avg": 0, "max": 0, "min": 0},
                    "power_l": {"avg": 0, "max": 0, "min": 0}
                }
            })
        
        # 计算统计数据
        def calculate_stats(data_list):
            valid_data = [float(x) for x in data_list if x is not None and x != '--']
            if not valid_data:
                return {"avg": 0, "max": 0, "min": 0}
            return {
                "avg": round(sum(valid_data) / len(valid_data), 2),
                "max": round(max(valid_data), 2),
                "min": round(min(valid_data), 2)
            }
        
        # 分别计算各字段的统计值
        temp_data = [row["temperature"] for row in rows]
        humidity_data = [row["humidity"] for row in rows]
        light_data = [row["light"] for row in rows]
        power_f_data = [row["power_f"] for row in rows]
        power_l_data = [row["power_l"] for row in rows]
        
        statistics = {
            "temperature": calculate_stats(temp_data),
            "humidity": calculate_stats(humidity_data),
            "light": calculate_stats(light_data),
            "power_f": calculate_stats(power_f_data),
            "power_l": calculate_stats(power_l_data)
        }
        
        return jsonify({
            "success": True,
            "data": statistics
        })
        
    except Exception as e:
        print(f"获取数据统计失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
 
 
# 10. 新增：历史数据查询接口
@app.route('/api/history_data', methods=['GET'])
def get_history_data():
    """获取历史数据，支持时间范围查询"""
    try:
        # 获取查询参数
        hours = request.args.get('hours', 24, type=int)  # 默认24小时
        limit = request.args.get('limit', 100, type=int)  # 默认100条
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 计算时间阈值
        from datetime import datetime, timedelta
        threshold = (datetime.now() - timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute("""
            SELECT id, temperature, humidity, light, pir, pir_status, 
                   pwm_f, pwm_l, power_f, power_l, level_f, level_l, 
                   timestamp, create_at
            FROM sensor_data
            WHERE create_at >= ?
            ORDER BY create_at ASC
            LIMIT ?
        """, (threshold, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        # 转换为字典列表
        history = [dict(row) for row in rows]
        
        return jsonify({
            "success": True,
            "data": history,
            "count": len(history)
        })
        
    except Exception as e:
        print(f"获取历史数据失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# 启动服务
if __name__ == '__main__':
    print("前端服务将运行在: http://0.0.0.0:8080")
    app.run(host='0.0.0.0', port=8080, debug=True)
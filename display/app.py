from flask import Flask, render_template, request, jsonify
import threading
import time
import os
from database import create_tables, save_sensor_data, clean_old_data
import requests
import sys

app = Flask(__name__)

# 重新加载配置
sys.path.append(os.path.abspath('..'))

BOARD_RUN_AI_URL = 'http://10.1.2.3:5005/run_ai'
print(f"使用默认的BOARD_RUN_AI_URL: {BOARD_RUN_AI_URL}")

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

# 初始化数据库
create_tables()
print("数据库表已创建/检查完成")

# 后台清理线程
cleanup_thread = threading.Thread(target=scheduled_cleanup, daemon=True)
cleanup_thread.start()
print("定时清理任务已启动")

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
        print(f"✅ 收到行空板数据：{latest_data}")

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

# 4. 新增：AI 建议上传接口（AI_advice_run.py 自动上传）
@app.route('/upload_ai_advice', methods=['POST'])
def upload_ai_advice():
    """
    接收设备端上传的 advice.txt（由 AI_advice_run.py 上传）
    """
    file = request.files.get("file")

    if not file:
        return jsonify({"success": False, "msg": "未收到文件"}), 400

    # 保存到当前目录，供前端读取
    file.save("advice.txt")

    print("📌收到并保存新的 AI 节能建议：advice.txt")
    return jsonify({"success": True, "msg": "AI 建议已更新"})

# 5. 新增：获取AI节能建议内容的接口
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

# 6. 新增：前端点击按钮执行 AI 分析
@app.route('/run_ai', methods=['POST'])
def run_ai():
    try:
        BOARD_URL = BOARD_RUN_AI_URL
        resp = requests.post(BOARD_URL, timeout=60)
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify({"success": False, "msg": f"主控端请求行空板失败: {e}"}), 500

# 7. 行空板控制接口
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

# 8. 新增：通过网络更新行空板配置文件的接口
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

# 9. 新增：设备控制接口
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

# 启动服务
if __name__ == '__main__':
    print("前端服务将运行在: http://0.0.0.0:8080")
    app.run(host='0.0.0.0', port=8080, debug=True)
# web/app.py
from flask import Flask, render_template, request, jsonify
import threading
import time
import os
import sys

app = Flask(__name__)

# 添加 WebSocket 支持，自动选择异步模式
from flask_socketio import SocketIO, emit
socketio = SocketIO(app, cors_allowed_origins="*")

sys.path.append(os.path.abspath('..'))
# 添加 Content Security Policy 头部，允许 eval（用于 Tailwind CSS）
@app.after_request
def add_security_headers(response):
    if response is None:
        return response
    response.headers['Content-Security-Policy'] = "default-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.tailwindcss.com https://cdn.jsdelivr.net;"
    return response

latest_data = {
    "temperature": "--",
    "humidity": "--",
    "light": "--",
    "pir": 0,
    "pir_status": "--",
    "timestamp": "--",
    "pwm_devices": [
        {"name": "风扇", "duty_cycle": "--", "power": "--"},
        {"name": "小灯", "duty_cycle": "--", "power": "--"}
    ]
}

# ========== 全局自动控制开关（默认关闭，更安全） ==========
auto_control_enabled = False

# ========== 命令中心模式：全局命令状态 ==========
import os

# 确保命令状态只初始化一次（防止Flask重新加载模块时重置）
if 'COMMAND_INITIALIZED' not in os.environ:
    current_command = {
        "fan_level": 0,
        "light_level": 0
    }
    print("[命令中心] 初始化全局命令状态")
    os.environ['COMMAND_INITIALIZED'] = '1'
else:
    # 必须重新定义变量，否则会报 not defined 错误
    current_command = {
        "fan_level": 0,
        "light_level": 0
    }
    print("[命令中心] 命令状态已初始化，使用现有值")

# 存储连接的客户端
connected_clients = set()

def update_command(fan_level, light_level):
    """更新命令并通过 WebSocket 推送"""
    global current_command
    current_command["fan_level"] = fan_level
    current_command["light_level"] = light_level
    # 通过 WebSocket 推送给所有连接的客户端
    socketio.emit('command_update', current_command)
    print(f"[WebSocket] 推送命令: fan={fan_level}, light={light_level}")

def scheduled_cleanup():
    from data.sensor_repository import clean_old_data
    while True:
        time.sleep(3600)
        clean_old_data()

def init_app():
    from data.sensor_repository import create_tables
    create_tables()
    print("数据库表结构初始化完成")
    
    cleanup_thread = threading.Thread(target=scheduled_cleanup, daemon=True)
    cleanup_thread.start()
    print("定时清理任务已启动")

    # 启动行为分析轮询（每 30s 从数据库取最近 6 条分析）
    from services.behavior_service import BehaviorAnalysisService
    BehaviorAnalysisService().start_polling(interval=30)
    print("行为分析轮询已启动")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/sensor_data', methods=['POST'])
def receive_data():
    global latest_data
    from controllers.sensor_controller import SensorController
    data = request.get_json()
    if data:
        # 确保数据格式正确转换
        processed_data = {
            "temperature": data.get("temp", data.get("temperature", "--")),
            "humidity": data.get("humi", data.get("humidity", "--")),
            "light": data.get("light", "--"),
            "pir": data.get("pir", 0),
            "pir_status": "有人" if data.get("pir", 0) == 1 else "无人",
            "timestamp": data.get("time", data.get("timestamp", "--")),
            "pwm_devices": [
                {
                    "name": "风扇",
                    "duty_cycle": data.get("fan_duty_cycle", "--"),
                    "power": data.get("fan_power", "--"),
                    "level": data.get("fan_level", 0)
                },
                {
                    "name": "小灯",
                    "duty_cycle": data.get("light_duty_cycle", "--"),
                    "power": data.get("light_power", "--"),
                    "level": data.get("light_level", 0)
                }
            ]
        }
        latest_data = processed_data
        return SensorController.receive_data()
    return jsonify({"status": "error", "msg": "无数据"}), 400

@app.route('/api/get_latest_data')
def get_data():
    from controllers.sensor_controller import SensorController
    return SensorController.get_latest_data(latest_data)

@app.route('/api/get_ai_advice')
def get_ai_advice():
    from controllers.ai_controller import AIController
    return AIController.get_ai_advice()

@app.route('/api/get_ai_status')
def get_ai_status():
    from controllers.ai_controller import AIController
    return AIController.get_ai_status()

# ========== 自动控制开关接口 ==========
@app.route('/api/control/status', methods=['GET'])
def control_status():
    """获取自动控制开关状态（页面加载时调用，回显开关状态）"""
    global auto_control_enabled
    return jsonify({"success": True, "auto_control_enabled": auto_control_enabled})

@app.route('/api/control/toggle', methods=['POST'])
def control_toggle():
    """切换自动控制开关状态（前端点击开关时调用）"""
    global auto_control_enabled
    data = request.get_json()
    enabled = data.get('enabled', False) if data else False
    auto_control_enabled = enabled
    status = "开启" if enabled else "关闭"
    print(f"[Control] 自动控制已{status} | enabled={enabled}")
    return jsonify({"success": True, "auto_control_enabled": enabled, "msg": f"自动控制已{status}"})

@app.route('/api/trigger_ai_analysis', methods=['POST'])
def trigger_ai_analysis():
    from controllers.ai_controller import AIController
    return AIController.trigger_ai_analysis()

@app.route('/run_ai', methods=['POST'])
def run_ai():
    from controllers.ai_controller import AIController
    return AIController.run_ai()

# ========== 命令中心模式：行空板主动轮询获取命令 ==========
@app.route('/set_command', methods=['POST'])
def set_command():
    """
    前端发送控制命令，Flask 只保存命令不直接控制设备
    请求示例：{"fan_level": 2, "light_level": 1}
    返回：{"success": true, "msg": "[INFO] command updated"}
    """
    global current_command
    try:
        data = request.get_json()
        if not data:
            print("[ERROR] /set_command: 缺少请求数据")
            return jsonify({"success": False, "msg": "缺少请求数据"}), 400
        
        fan_level = data.get('fan_level')
        light_level = data.get('light_level')
        
        # 验证参数范围
        if fan_level is not None and (not isinstance(fan_level, int) or not (0 <= fan_level <= 3)):
            print(f"[ERROR] /set_command: fan_level 参数错误: {fan_level}")
            return jsonify({"success": False, "msg": "fan_level 必须在 0-3 之间"}), 400
        
        if light_level is not None and (not isinstance(light_level, int) or not (0 <= light_level <= 3)):
            print(f"[ERROR] /set_command: light_level 参数错误: {light_level}")
            return jsonify({"success": False, "msg": "light_level 必须在 0-3 之间"}), 400
        
        # 更新命令
        if fan_level is not None:
            current_command["fan_level"] = fan_level
        if light_level is not None:
            current_command["light_level"] = light_level
        
        print(f"[INFO] command updated: fan={current_command['fan_level']}, light={current_command['light_level']}")
        return jsonify({"success": True, "msg": "[INFO] command updated"})
    except Exception as e:
        print(f"[ERROR] /set_command: {str(e)}")
        return jsonify({"success": False, "msg": f"命令设置失败: {str(e)}"}), 500

@app.route('/get_command', methods=['GET'])
def get_command():
    """
    行空板主动轮询获取当前命令
    返回：{"fan_level": 2, "light_level": 1}
    """
    global current_command
    try:
        print(f"[INFO] command fetched: fan_level={current_command['fan_level']}, light_level={current_command['light_level']}")
        return jsonify(current_command), 200
    except Exception as e:
        print(f"[ERROR] /get_command: {str(e)}")
        return jsonify({"success": False, "msg": f"命令获取失败: {str(e)}"}), 500

@app.route('/api/energy_stats', methods=['GET'])
def get_energy_stats():
    """获取最近5天分类能耗统计（用于前端功耗柱状图）"""
    from data.sensor_repository import get_daily_energy_stats
    return jsonify(get_daily_energy_stats())

@app.route('/api/data_statistics', methods=['GET'])
def get_data_statistics():
    from controllers.sensor_controller import SensorController
    return SensorController.get_statistics()

@app.route('/api/history_data', methods=['GET'])
def get_history_data():
    from controllers.sensor_controller import SensorController
    return SensorController.get_history_data()

# ========== WebSocket 事件处理 ==========
@socketio.on('connect')
def handle_connect():
    client_id = request.sid
    connected_clients.add(client_id)
    print(f"[WebSocket] 客户端连接: {client_id}")
    # 发送当前命令给新连接的客户端
    emit('command_update', current_command)

@socketio.on('disconnect')
def handle_disconnect():
    client_id = request.sid
    connected_clients.discard(client_id)
    print(f"[WebSocket] 客户端断开: {client_id}")

@socketio.on('request_command')
def handle_request_command():
    """客户端主动请求当前命令"""
    emit('command_update', current_command)

if __name__ == '__main__':
    init_app()
    
    print("前端服务将运行在: http://0.0.0.0:8080")
    print("[Command] 使用 HTTP 轮询模式")
    # 使用标准 Flask 启动
    app.run(host='0.0.0.0', port=8080, debug=False, threaded=True)

# web/app.py
from flask import Flask, render_template, request, jsonify
import threading
import time
import os
import sys

app = Flask(__name__)

sys.path.append(os.path.abspath('..'))
BOARD_BASE_URL = 'http://10.1.2.3:5005'
print(f"手动设置的BOARD_BASE_URL: {BOARD_BASE_URL}")

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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/sensor_data', methods=['POST'])
def receive_data():
    global latest_data
    from controllers.sensor_controller import SensorController
    data = request.get_json()
    if data:
        latest_data = data
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

@app.route('/run_ai', methods=['POST'])
def run_ai():
    from controllers.ai_controller import AIController
    return AIController.run_ai()

@app.route('/start_board_main', methods=['POST'])
def start_board_main():
    from controllers.device_controller import DeviceController
    return DeviceController.start_board_main()

@app.route('/stop_board_main', methods=['POST'])
def stop_board_main():
    from controllers.device_controller import DeviceController
    return DeviceController.stop_board_main()

@app.route('/update_board_config', methods=['POST'])
def update_board_config():
    from controllers.device_controller import DeviceController
    return DeviceController.update_board_config()

@app.route('/control_device', methods=['POST'])
def control_device():
    from controllers.device_controller import DeviceController
    return DeviceController.control_device()

@app.route('/api/data_statistics', methods=['GET'])
def get_data_statistics():
    from controllers.sensor_controller import SensorController
    return SensorController.get_statistics()

@app.route('/api/history_data', methods=['GET'])
def get_history_data():
    from controllers.sensor_controller import SensorController
    return SensorController.get_history_data()

if __name__ == '__main__':
    init_app()
    print("前端服务将运行在: http://0.0.0.0:8080")
    app.run(host='0.0.0.0', port=8080, debug=True)
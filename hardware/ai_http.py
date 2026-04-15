
from flask import Flask, jsonify, request
import os
import threading

app = Flask(__name__)


# 全局编辑器实例
global_editor = None

# 全局状态：记录main是否在运行
main_running = True

def set_editor(editor):
    """设置全局编辑器实例"""
    global global_editor
    global_editor = editor




@app.route('/control_device', methods=['POST'])
def control_device_handler():
    """处理设备控制命令"""
    global global_editor
    
    if not global_editor:
        return jsonify({"success": False, "msg": "编辑器实例未初始化"}), 500
    
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
        
        # 调用编辑器实例设置设备挡位
        if device == 'light':
            # 设置小灯挡位
            global_editor.current_light_level = level
            global_editor._apply_light_level(level)
            device_name = "小灯"
        else:
            # 设置风扇挡位
            global_editor.current_fan_level = level
            global_editor._apply_fan_level(level)
            device_name = "风扇"
        
        print(f"[HTTP控制] 成功设置{device_name}到{level}挡")
        return jsonify({
            "success": True,
            "msg": f"{device_name}挡位已设置为{level}档",
            "device": device,
            "level": level,
            "pwm_value": pwm_value
        })
        
    except Exception as e:
        print(f"[HTTP控制] 设备控制失败: {e}")
        return jsonify({
            "success": False,
            "msg": f"设备控制失败: {str(e)}"
        }), 500


@app.route('/start_main', methods=['POST'])
def start_main_handler():
    """启动主程序"""
    global main_running
    try:
        # main.py通常是作为系统的主入口运行的
        # 如果ai_http.py正在运行，那么main.py很可能已经在运行了
        if main_running:
            return jsonify({"success": True, "msg": "主程序已在运行"}), 200
        
        # 这里可以添加启动main.py的逻辑，如果需要的话
        # 但通常main.py是手动启动的，而不是通过API启动
        
        main_running = True
        print("[HTTP控制] 主程序启动命令已执行")
        return jsonify({"success": True, "msg": "主程序启动成功"}), 200
    except Exception as e:
        print(f"[HTTP控制] 启动主程序失败: {e}")
        return jsonify({"success": False, "msg": f"启动主程序失败: {str(e)}"}), 500


@app.route('/stop_main', methods=['POST'])
def stop_main_handler():
    """停止主程序"""
    global main_running
    try:
        if not main_running:
            return jsonify({"success": True, "msg": "主程序已停止"}), 200
        
        # 记录停止请求
        main_running = False
        
        # 注意：由于ai_http是作为main.py的线程运行的，
        # 这里无法直接停止main.py的主循环
        # 需要在main.py中检查main_running状态并自行退出
        
        print("[HTTP控制] 主程序停止命令已执行")
        return jsonify({"success": True, "msg": "主程序停止命令已发送"}), 200
    except Exception as e:
        print(f"[HTTP控制] 停止主程序失败: {e}")
        return jsonify({"success": False, "msg": f"停止主程序失败: {str(e)}"}), 500


def run_server(host='0.0.0.0', port=5005, debug=False, threaded=True):
    # When embedding, do not enable the reloader (it creates child processes)
    app.run(host=host, port=port, debug=debug, use_reloader=False, threaded=threaded)


if __name__ == '__main__':
    print(f"Starting device control server on 0.0.0.0:5005")
    run_server()
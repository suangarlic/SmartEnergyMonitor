# web/controllers/device_controller.py
from flask import jsonify, request
import requests

BOARD_BASE_URL = 'http://10.1.2.3:5005'

class DeviceController:
    @staticmethod
    def start_board_main():
        """启动行空板主程序"""
        try:
            resp = requests.post(f'{BOARD_BASE_URL}/start_main', timeout=10)
            return jsonify(resp.json()), resp.status_code
        except Exception as e:
            return jsonify({"success": False, "msg": f"请求行空板启动失败: {e}"}), 500
    
    @staticmethod
    def stop_board_main():
        """停止行空板主程序"""
        try:
            resp = requests.post(f'{BOARD_BASE_URL}/stop_main', timeout=10)
            return jsonify(resp.json()), resp.status_code
        except Exception as e:
            return jsonify({"success": False, "msg": f"请求行空板终止失败: {e}"}), 500
    
    @staticmethod
    def update_board_config():
        """更新行空板配置"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({"success": False, "msg": "缺少请求数据"}), 400
            
            pc_ip = data.get('pc_ip')
            board_ip = data.get('board_ip')
            
            if not pc_ip or not board_ip:
                return jsonify({"success": False, "msg": "缺少必要的参数: pc_ip 和 board_ip"}), 400
            
            api_url = f"http://{board_ip}:5005/update_config"
            request_data = {"pc_ip": pc_ip, "board_ip": board_ip}
            response = requests.post(api_url, json=request_data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    return jsonify({"success": True, "msg": "行空板配置文件更新成功", "board_response": result})
                else:
                    return jsonify({"success": False, "msg": f"行空板API返回错误: {result.get('msg')}", "board_response": result}), 500
            else:
                return jsonify({"success": False, "msg": f"行空板API请求失败，状态码: {response.status_code}"}), 500
        except Exception as e:
            print(f"通过网络API更新行空板配置失败: {e}")
            return jsonify({"success": False, "msg": f"通过网络API更新行空板配置失败: {str(e)}"}), 500
    
    @staticmethod
    def control_device():
        """控制设备挡位"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({"success": False, "msg": "缺少请求数据"}), 400
            
            device = data.get('device')
            level = data.get('level')
            pwm_value = data.get('pwm_value')
            
            if device not in ['light', 'fan']:
                return jsonify({"success": False, "msg": "设备类型错误，必须是 'light' 或 'fan'"}), 400
            
            if level is None or not (0 <= level <= 3):
                return jsonify({"success": False, "msg": "挡位参数错误，必须是 0-3"}), 400
            
            control_data = {"device": device, "level": level, "pwm_value": pwm_value, "action": "set_level"}
            api_url = f"{BOARD_BASE_URL}/control_device"
            response = requests.post(api_url, json=control_data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    device_name = "小灯" if device == "light" else "风扇"
                    return jsonify({"success": True, "msg": f"{device_name}挡位已设置为{level}档", "device": device, "level": level, "pwm_value": pwm_value})
                else:
                    return jsonify({"success": False, "msg": f"行空板控制失败: {result.get('msg', '未知错误')}"}), 500
            else:
                return jsonify({"success": False, "msg": f"行空板API请求失败，状态码: {response.status_code}"}), 500
        except Exception as e:
            print(f"设备控制失败: {e}")
            return jsonify({"success": False, "msg": f"设备控制失败: {str(e)}"}), 500
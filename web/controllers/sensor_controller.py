# web/controllers/sensor_controller.py
from flask import jsonify, request
from services.sensor_service import SensorService
from data.sensor_repository import get_history_data, get_statistics_data

class SensorController:
    @staticmethod
    def receive_data():
        """接收行空板上报的传感器数据"""
        data = request.get_json()
        if data:
            processed_data = SensorService.process_sensor_data(data)
            if SensorService.save_data(processed_data):
                print("数据已成功保存到数据库")
            else:
                print("⚠ 警告：数据保存到数据库失败")
            return jsonify({"status": "success", "msg": "数据已接收并保存"})
        return jsonify({"status": "error", "msg": "无数据"}), 400
    
    @staticmethod
    def get_latest_data(latest_data):
        """获取最新传感器数据"""
        return jsonify(latest_data)
    
    @staticmethod
    def get_history_data():
        """获取历史数据（三层架构：直接调用数据层）"""
        try:
            hours = request.args.get('hours', 24, type=int)
            limit = request.args.get('limit', 100, type=int)
            history = get_history_data(hours, limit)
            return jsonify({"success": True, "data": history, "count": len(history)})
        except Exception as e:
            print(f"获取历史数据失败: {e}")
            return jsonify({"success": False, "error": str(e)}), 500
    
    @staticmethod
    def get_statistics():
        """获取数据统计（三层架构：直接调用数据层）"""
        try:
            hours = request.args.get('hours', 24, type=int)
            statistics = get_statistics_data(hours)
            return jsonify({"success": True, "data": statistics})
        except Exception as e:
            print(f"获取数据统计失败: {e}")
            return jsonify({"success": False, "error": str(e)}), 500
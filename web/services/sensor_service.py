# web/services/sensor_service.py
from data.sensor_repository import save_sensor_data, get_history_data, get_statistics_data, get_ai_data

class SensorService:
    @staticmethod
    def process_sensor_data(data):
        """处理传感器数据，转换为统一格式并保存"""
        if "light" in data and "humi" in data:
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
            return full_data
        return data
    
    @staticmethod
    def save_data(data):
        """保存传感器数据到数据库"""
        return save_sensor_data(data)
    
    @staticmethod
    def get_ai_data(limit=400):
        """获取AI分析所需的数据（三层架构：只做AI查询）"""
        return get_ai_data(limit)
    
    @staticmethod
    def get_history(hours=24, limit=100):
        """获取历史数据"""
        return get_history_data(hours, limit)
    
    @staticmethod
    def get_statistics(hours=24):
        """获取统计数据"""
        rows = get_statistics_data(hours)
        if not rows:
            return {
                "temperature": {"avg": 0, "max": 0, "min": 0},
                "humidity": {"avg": 0, "max": 0, "min": 0},
                "light": {"avg": 0, "max": 0, "min": 0},
                "power_f": {"avg": 0, "max": 0, "min": 0},
                "power_l": {"avg": 0, "max": 0, "min": 0}
            }
        
        def calculate_stats(data_list):
            valid_data = [float(x) for x in data_list if x is not None and x != '--']
            if not valid_data:
                return {"avg": 0, "max": 0, "min": 0}
            return {
                "avg": round(sum(valid_data) / len(valid_data), 2),
                "max": round(max(valid_data), 2),
                "min": round(min(valid_data), 2)
            }
        
        temp_data = [row["temperature"] for row in rows]
        humidity_data = [row["humidity"] for row in rows]
        light_data = [row["light"] for row in rows]
        power_f_data = [row["power_f"] for row in rows]
        power_l_data = [row["power_l"] for row in rows]
        
        return {
            "temperature": calculate_stats(temp_data),
            "humidity": calculate_stats(humidity_data),
            "light": calculate_stats(light_data),
            "power_f": calculate_stats(power_f_data),
            "power_l": calculate_stats(power_l_data)
        }
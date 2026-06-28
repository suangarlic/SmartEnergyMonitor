# sensor_collect.py - 仅负责传感器数据读取
import time

class SensorCollect:
    def __init__(self, hardware):
        # 接收硬件初始化对象（避免重复初始化）
        self.hardware = hardware

    # 读取温度（重试3次）
    def read_temp(self):
        for _ in range(3):
            try:
                return self.hardware.dht20.temp_c()
            except:
                time.sleep(0.1)
        return None

    # 读取湿度
    def read_humi(self):
        try:
            return self.hardware.dht20.humidity()
        except:
            return None

    # 读取光照
    def read_light(self):
        return self.hardware.light_sensor.read()

    # 读取人体红外
    def read_pir(self):
        return self.hardware.ir_pin.read_digital()

    # 封装所有传感器数据为字典（便于传输）
    def get_all_data(self):
        temp = self.read_temp()
        humi = self.read_humi()
        light_val = self.read_light()
        pir = self.read_pir()
        # 封装为字典（前端易解析）
        return {
            "temperature": round(temp, 1) if temp else None,
            "humidity": round(humi, 1) if humi else None,
            "light": light_val,
            "pir": pir,
            "pir_status": "有人" if pir == 1 else "无人"
        }
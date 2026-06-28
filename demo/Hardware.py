from pinpong.board import Board, Pin
from pinpong.libs.dfrobot_dht20 import DHT20
import siot
from pinpong.extension.unihiker import light
from config import PC_IP, PC_PORT, HTTP_API  # 导入配置

class HardwareInit:
    def __init__(self):
        # 初始化行空板硬件
        Board().begin()
        print("行空板硬件初始化完毕")
        
        # HTTP传输配置（使用配置文件中的值）
        self.PC_IP = PC_IP
        self.PC_PORT = PC_PORT
        self.HTTP_API = HTTP_API
        # 自定义变量（自动逻辑用）
        self.pir_timer = 0

              # ========== 传感器初始化 ==========
        # 初始化DHT20温湿度传感器
        self.dht20 = DHT20()
        
        # 初始化光线传感器（行空板内置光线传感器）
        self.light_sensor = light
        
        # 初始化人体红外传感器（假设连接在P10引脚）
        self.ir_pin = Pin(Pin.P10, Pin.IN)  # P10为数字输入引脚

           # ========== SIoT 配置 ==========
        # SIoT 服务器地址（默认使用本地服务器）
        self.SIOT_SERVER = "127.0.0.1"
        self.SIOT_PORT = 1883
        self.SIOT_USER = "siot"
        self.SIOT_PASSWORD = "dfrobot"
        self.SIOT_CLIENT_ID = "unihiker_demo"
        
        # SIoT 主题配置
        self.TOPIC = "unihiker/sensor_data"  # 传感器数据主题
        
        # 初始化 SIoT 连接
        try:
            siot.init(self.SIOT_CLIENT_ID, self.SIOT_SERVER, self.SIOT_PORT, self.SIOT_USER, self.SIOT_PASSWORD)
            siot.connect()
            print("SIoT 连接成功")
        except Exception as e:
            print(f"SIoT 连接失败: {e}")


        print("硬件/SIoT/HTTP配置初始化完成\n")

         # ========== 新增：PWM设备初始化（核心） ==========
        # 定义风扇、小灯的PWM引脚和初始状态
        self.pwm_devices = [
            {
                "name": "风扇",       # 设备名称（前端显示）
                "pin": Pin(Pin.P9, Pin.PWM),  # 风扇PWM引脚（可修改）
                "current_pwm_value": 307,      # 初始PWM值（0-1023，307=30%）
                "current_duty_cycle": 30.0,     # 初始占空比（%）
                "power_map": [
                    (0, 0, 0),       # 0%占空比→0W（关）
                    (1, 30, 5),      # 1%-30%→低挡5W
                    (31, 60, 15),    # 31%-60%→中挡15W
                    (61, 100, 25)    # 61%-100%→高挡25W
                ],
                "current_power": 0.0  # 新增：当前功率（初始0W）
            },
            {
                "name": "小灯",
                "pin": Pin(Pin.P16, Pin.PWM),  # 小灯PWM引脚（可修改）
                "current_pwm_value": 512,      # 初始PWM值（512=50%）
                "current_duty_cycle": 50.0,     # 初始占空比（%）
                "power_map": [
                    (0, 0, 0),       # 0%→0W（关）
                    (1, 30, 1),      # 1%-30%→低挡1W
                    (31, 60, 3),      # 31%-60%→中挡3W
                    (61, 100, 5)      # 61%-100%→高挡5W
                ],
                "current_power": 0.0  # 新增：当前功率（初始0W）
            }
        ]
        # 初始化PWM输出（设置初始值）
        for device in self.pwm_devices:
            device["pin"].write_analog(device["current_pwm_value"])

        for device in self.pwm_devices:
            device["pin"].write_analog(device["current_pwm_value"])
            # 计算初始功率
            self._calc_device_power(device)

    # 新增：计算单个设备的功率（根据占空比匹配功率映射）
    def _calc_device_power(self, device):
        duty = device["current_duty_cycle"]
        for (min_duty, max_duty, power) in device["power_map"]:
            if min_duty <= duty <= max_duty:
                device["current_power"] = power
                break
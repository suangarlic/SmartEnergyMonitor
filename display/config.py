# 配置文件 - 集中管理所有IP地址和端口

# 前端电脑配置（局域网IP）
PC_IP = "192.168.43.250"  # 替换为电脑的实际局域网IP
PC_PORT = 8080           # 前端电脑的端口号

# 行空板配置（局域网IP）
BOARD_IP = "10.1.2.3"  # 替换为行空板的实际局域网IP
BOARD_PORT = 5005          # 行空板的端口号

# 生成完整的API地址
HTTP_API = f"http://{PC_IP}:{PC_PORT}/api/sensor_data"
UPLOAD_ADVICE_URL = f"http://{PC_IP}:{PC_PORT}/upload_ai_advice"
BOARD_BASE_URL = f"http://{BOARD_IP}:{BOARD_PORT}"
BOARD_RUN_AI_URL = f"{BOARD_BASE_URL}/run_ai"
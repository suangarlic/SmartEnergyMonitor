# 配置文件 - 仅保留PC端配置
import os

# 从前端环境变量获取，或者使用默认值
PC_IP = os.getenv("PC_IP", "192.168.1.106")  # 可通过环境变量PC_IP设置
PC_PORT = int(os.getenv("PC_PORT", "8080"))   # 可通过环境变量PC_PORT设置

# 生成完整的API地址（仅用于上传数据到服务器）
HTTP_API = f"http://{PC_IP}:{PC_PORT}/api/sensor_data"
UPLOAD_ADVICE_URL = f"http://{PC_IP}:{PC_PORT}/upload_ai_advice"

# BOARD_IP、BOARD_BASE_URL 等已不再使用
# 行空板主动轮询服务器获取命令，不再需要服务器访问行空板

print(f"Hardware config - HTTP_API: {HTTP_API}")
print(f"Hardware config - UPLOAD_ADVICE_URL: {UPLOAD_ADVICE_URL}")
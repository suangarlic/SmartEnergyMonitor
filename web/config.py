# web/config.py - Flask Web应用配置文件
import os

# ==================== 服务配置 ====================
DEBUG = False
HOST = '0.0.0.0'
PORT = 8080

# ==================== 数据库配置 ====================
DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'data', 'sensor_data.db')

# ==================== WebSocket 配置 ====================
SOCKETIO_CORS_ALLOWED_ORIGINS = "*"
SOCKETIO_ASYNC_MODE = None  # 默认使用 eventlet

# ==================== 行为分析配置 ====================
BEHAVIOR_POLLING_INTERVAL = 30  # 轮询间隔（秒）
BEHAVIOR_DEBOUNCE_COUNT = 2     # 防抖窗口数

# ==================== 模型文件路径 ====================
MODEL_PATHS = {
    'presence': os.path.join(os.path.dirname(__file__), 'models', 'behavior_presence.pkl'),
    'fan': os.path.join(os.path.dirname(__file__), 'models', 'behavior_fan.pkl'),
    'light': os.path.join(os.path.dirname(__file__), 'models', 'behavior_light.pkl')
}


# ==================== 日志配置 ====================
LOG_LEVEL = 'INFO'
LOG_FORMAT = '[%(asctime)s] %(levelname)s: %(message)s'

# ==================== 节能控制策略 ====================
CONTROL_CONFIG = {
    'enable_auto_control': True,
    'scenarios': ['energy_saving', 'comfort_adjust']
}
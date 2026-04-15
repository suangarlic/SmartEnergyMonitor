import sqlite3
import datetime
import os

# 数据库文件路径（指向根目录的统一数据库）
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'sensor_data.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # 启用WAL模式，提高并发访问性能
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA busy_timeout=5000')  # 5秒超时
    return conn

# 创建数据库表
def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 检查表是否存在
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sensor_data'")
    table_exists = cursor.fetchone()
    
    # 创建合并的传感器数据表
    if not table_exists:
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sensor_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            temperature REAL,          -- 温度（浮点型）
            humidity REAL,             -- 湿度（浮点型）
            light REAL,                -- 光照（浮点型）
            pir INTEGER,               -- PIR（整数型）
            pir_status TEXT,           -- PIR状态（文本型）
            pwm_f REAL,                -- 风扇占空比（浮点型）
            pwm_l REAL,                -- 小灯占空比（浮点型）
            power_f REAL,              -- 风扇功率（浮点型）
            power_l REAL,              -- 小灯功率（浮点型）
            level_f INTEGER,           -- 风扇挡位（整数型）
            level_l INTEGER,           -- 小灯挡位（整数型）
            timestamp TEXT,            -- 传感器时间戳
            create_at TEXT             -- 数据库写入时间（北京时间）
        )
         
        ''')
        conn.commit()
        print("数据库表结构已创建")
    else:
        print("数据库表已存在，跳过创建")

# 保存传感器数据和设备功率数据
def save_sensor_data(data):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 转换传感器数据为数值型
        temperature = float(data.get('temperature', 0)) if data.get('temperature', '--') != '--' else 0.0
        humidity = float(data.get('humidity', 0)) if data.get('humidity', '--') != '--' else 0.0
        light = float(data.get('light', 0)) if data.get('light', '--') != '--' else 0.0
        pir = int(data.get('pir', 0))
        
        # 获取设备数据
        pwm_devices = data.get('pwm_devices', [])
        
        # 初始化设备参数
        pwm_f = 0.0  # 风扇占空比
        pwm_l = 0.0  # 小灯占空比
        power_f = 0.0  # 风扇功率
        power_l = 0.0  # 小灯功率
        level_f = 0   # 风扇挡位
        level_l = 0   # 小灯挡位
        
        # 解析设备数据
        for device in pwm_devices:
            device_name = device.get('name', '').lower()
            duty = float(device.get('duty_cycle', 0)) if device.get('duty_cycle', '--') != '--' else 0.0
            power = float(device.get('power', 0)) if device.get('power', '--') != '--' else 0.0
            level = int(device.get('level', 0))
            
            if 'fan' in device_name or '风扇' in device_name:
                pwm_f = duty
                power_f = power
                level_f = level
            elif 'light' in device_name or '灯' in device_name:
                pwm_l = duty
                power_l = power
                level_l = level
        
        # 获取当前时间作为create_at
        create_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 保存合并数据
        cursor.execute(
            "INSERT INTO sensor_data (temperature, humidity, light, pir, pir_status, pwm_f, pwm_l, power_f, power_l, level_f, level_l, timestamp, create_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (temperature,
             humidity,
             light,
             pir,
             data.get('pir_status', '--'),
             pwm_f,
             pwm_l,
             power_f,
             power_l,
             level_f,
             level_l,
             data.get('timestamp', '--'),
             create_at)
        )
        
        conn.commit()
        return True
    except Exception as e:
        print(f"保存数据失败: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

# 清理一天前的数据
def clean_old_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 计算一天前的时间
        one_day_ago = datetime.datetime.now() - datetime.timedelta(days=1)
        one_day_ago_str = one_day_ago.strftime('%Y-%m-%d %H:%M:%S')
        
        # 删除传感器数据（现在只有一个表）
        cursor.execute(
            "DELETE FROM sensor_data WHERE create_at < ?",
            (one_day_ago_str,)
        )
        
        deleted_count = cursor.rowcount
        conn.commit()
        print(f"清理了 {deleted_count} 条过期数据")
        return True
    except Exception as e:
        print(f"清理过期数据失败: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

# 初始化数据库
if __name__ == '__main__':
    create_tables()
    print("数据库初始化完成")
    print(f"数据库文件位置: {os.path.abspath(DB_PATH)}")
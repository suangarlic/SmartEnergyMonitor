import sqlite3
import datetime
import os
import stat

# ================================
#  时区配置（仅用于数据库时间校准）
# ================================
def get_beijing_time_str():
    """获取当前北京时间字符串（解决8小时时差）"""
    # 计算UTC+8时间（无需pytz，纯内置函数实现）
    utc_now = datetime.datetime.utcnow()
    beijing_now = utc_now + datetime.timedelta(hours=8)
    return beijing_now.strftime('%Y-%m-%d %H:%M:%S')

def get_beijing_time_delta(days=0):
    """获取指定天数前的北京时间字符串"""
    utc_now = datetime.datetime.utcnow()
    target_time = utc_now + datetime.timedelta(hours=8) - datetime.timedelta(days=days)
    return target_time.strftime('%Y-%m-%d %H:%M:%S')

# ================================
#  数据库路径：固定为当前目录下
# ================================
DB_PATH = os.path.abspath("sensor_data.db")
print(f"[INFO] 数据库文件位置: {DB_PATH}")

# 创建数据库文件（若不存在）
try:
    if not os.path.exists(DB_PATH):
        open(DB_PATH, 'a').close()
    st = os.stat(DB_PATH)
    os.chmod(DB_PATH, st.st_mode | stat.S_IWUSR)
except Exception as e:
    print(f"[WARN] 无法创建数据库文件: {e}")

# ================================
#  数据库连接
# ================================
def get_db_connection():
    conn = sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# ================================
#  重建数据表（合并为单一表结构）
# ================================
def recreate_tables():
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 1. 先删除旧表
        print("[INFO] 开始删除旧表...")
        cursor.execute("DROP TABLE IF EXISTS device_power")  # 先删关联表
        cursor.execute("DROP TABLE IF EXISTS sensor_data")   # 再删主表
        print("[INFO] 旧表删除完成")

        # 2. 创建全新的合并数据表
        cursor.execute('''
        CREATE TABLE sensor_data (
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
        print("[INFO] 全新合并数据表创建完成")
        print("[INFO] 表结构：id | temperature | humidity | light | pir | pir_status | pwm_f | pwm_l | power_f | power_l | level_f | level_l | timestamp | create_at")
        return True

    except Exception as e:
        print(f"重建表失败: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

# ================================
#  数据转换辅助函数
# ================================
def safe_float_convert(value, default=None):
    """安全转换为浮点型，异常值返回默认值"""
    if value in ['--', '', None]:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def safe_int_convert(value, default=0):
    """安全转换为整数型，异常值返回默认值"""
    if value in ['--', '', None]:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

# ================================
#  保存数据（合并表结构）
# ================================
def save_sensor_data(data):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 转换传感器数据为数值型
        temperature = safe_float_convert(data.get('temperature', '--'))
        humidity = safe_float_convert(data.get('humidity', '--'))
        light = safe_float_convert(data.get('light', '--'))
        pir = safe_int_convert(data.get('pir', 0))
        
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
            duty = safe_float_convert(device.get('duty_cycle', 0))
            power = safe_float_convert(device.get('power', 0))
            level = safe_int_convert(device.get('level', 0))
            
            if 'fan' in device_name or '风扇' in device_name:
                pwm_f = duty
                power_f = power
                level_f = level
            elif 'light' in device_name or '灯' in device_name:
                pwm_l = duty
                power_l = power
                level_l = level
        
        # 传感器时间戳
        timestamp = data.get('timestamp', '--')
        # 获取当前北京时间作为create_at
        beijing_create_at = get_beijing_time_str()
        
        # 插入合并数据
        cursor.execute(
            "INSERT INTO sensor_data (temperature, humidity, light, pir, pir_status, pwm_f, pwm_l, power_f, power_l, level_f, level_l, timestamp, create_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                temperature,
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
                timestamp,
                beijing_create_at
            )
        )

        conn.commit()
        return True

    except Exception as e:
        print(f"保存数据失败: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

# ================================
#  清理一天前的数据（基于北京时间）
# ================================
def clean_old_data():
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 计算北京时间的一天前
        one_day_ago = get_beijing_time_delta(days=1)

        # 清理数据（现在只有一个表）
        cursor.execute(
            "DELETE FROM sensor_data WHERE create_at < ?",
            (one_day_ago,)
        )

        conn.commit()
        return True

    except Exception as e:
        print(f"清理数据失败: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

# ================================
#  查询最新数据
# ================================
def get_latest_sensor_data(limit=10):
    """获取最新的传感器数据"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT id, temperature, humidity, light, pir, pir_status, 
                   pwm_f, pwm_l, power_f, power_l, level_f, level_l, 
                   timestamp, create_at 
            FROM sensor_data 
            ORDER BY create_at DESC 
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        result = [dict(row) for row in rows]  # 简化结果转换
        return result
    except Exception as e:
        print(f"查询数据失败: {e}")
        return []
    finally:
        conn.close()

# ================================
#  初始化数据库（彻底重建）
# ================================
if __name__ == '__main__':
    # 执行重建表操作（删旧表+建新表）
    if recreate_tables():
        print("[INFO] 数据库彻底重建完成")
        print(f"[INFO] 使用数据库: {DB_PATH}")
        print("[INFO] 表结构说明：")
        print("  - sensor_data: 合并表结构，包含传感器数据和设备数据")
        print("  - 字段：id | temperature | humidity | light | pir | pir_status | pwm_f | pwm_l | power_f | power_l | level_f | level_l | timestamp | create_at")
# web/data/sensor_repository.py
import sqlite3
from datetime import datetime, timedelta
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'sensor_data.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA busy_timeout=5000')
    return conn



def create_tables():
    """创建优化后的数据表（精简字段名，保留完整数据）"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sensor_data (
            Id INTEGER PRIMARY KEY AUTOINCREMENT,
            Temperature REAL,
            Humidity REAL,
            Light REAL,
            PirStatus INTEGER,
            PirText TEXT,
            FanPower REAL,
            LightPower REAL,
            FanLevel INTEGER,
            LightLevel INTEGER,
            Timestamp TEXT,
            CollectionTime TEXT
        )
        ''')
        conn.commit()
        print("数据库表结构已创建")
    except Exception as e:
        print(f"创建表失败: {e}")
        conn.rollback()
    finally:
        conn.close()

def save_sensor_data(data):
    """保存传感器数据到数据库（三层架构：只做存储）"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        Temperature = float(data.get('temperature', 0)) if data.get('temperature', '--') != '--' else 0.0
        Humidity = float(data.get('humidity', 0)) if data.get('humidity', '--') != '--' else 0.0
        Light = float(data.get('light', 0)) if data.get('light', '--') != '--' else 0.0
        PirStatus = int(data.get('pir', 0))
        PirText = data.get('pir_status', '--')
        
        pwm_devices = data.get('pwm_devices', [])
        fanPower = 0.0
        lightPower = 0.0
        fanLevel = 0
        lightLevel = 0
        
        for device in pwm_devices:
            device_name = device.get('name', '').lower()
            power = float(device.get('power', 0)) if device.get('power', '--') != '--' else 0.0
            level = int(device.get('level', 0))
            
            if 'fan' in device_name or '风扇' in device_name:
                fanPower = power
                fanLevel = level
            elif 'light' in device_name or '灯' in device_name:
                lightPower = power
                lightLevel = level
        
        Timestamp = data.get('timestamp', '--')
        collectionTime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute(
            "INSERT INTO sensor_data (Temperature, Humidity, Light, PirStatus, PirText, FanPower, LightPower, FanLevel, LightLevel, Timestamp, CollectionTime) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (Temperature, Humidity, Light, PirStatus, PirText, fanPower, lightPower, fanLevel, lightLevel, Timestamp, collectionTime)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"保存数据失败: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def get_ai_data(limit=400):
    """获取AI分析所需的数据（三层架构：只做AI查询，最近400条）"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT Temperature, Humidity, Light, PirStatus, FanPower, LightPower, FanLevel, LightLevel, Timestamp, CollectionTime
            FROM sensor_data
            ORDER BY CollectionTime DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        
        print(f"[get_ai_data] 查询到 {len(rows)} 条记录")
        
        # 转换为精简格式，减少token使用
        ai_data = []
        for row in rows:
            record = {
                "t": row["Temperature"],
                "h": row["Humidity"],
                "l": row["Light"],
                "p": row["PirStatus"],
                "pf": row["FanPower"],
                "pl": row["LightPower"],
                "lf": row["FanLevel"],
                "ll": row["LightLevel"],
                "tm": row["Timestamp"],
                "ca": row["CollectionTime"]
            }
            ai_data.append(record)
        
        return ai_data
    finally:
        conn.close()
 
def get_history_data(hours=24, limit=100):
    """获取历史数据（用于前端展示）"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        threshold = (datetime.now() - timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            SELECT Temperature, Humidity, Light, PirStatus, PirText, FanPower, LightPower, FanLevel, LightLevel, Timestamp, CollectionTime
            FROM sensor_data
            WHERE CollectionTime >= ?
            ORDER BY CollectionTime ASC
            LIMIT ?
        """, (threshold, limit))
        rows = cursor.fetchall()
        
        history = []
        for row in rows:
            record = {
                "t": row["Temperature"],
                "h": row["Humidity"],
                "l": row["Light"],
                "p": row["PirStatus"],
                "ps": row["PirText"],
                "pf": row["FanPower"],
                "pl": row["LightPower"],
                "lf": row["FanLevel"],
                "ll": row["LightLevel"],
                "tm": row["Timestamp"],
                "ca": row["CollectionTime"]
            }
            history.append(record)
        
        return history
    finally:
        conn.close()
 
def get_statistics_data(hours=24):
    """获取统计数据（用于前端统计）"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        threshold = (datetime.now() - timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            SELECT Temperature, Humidity, Light, PirStatus, PirText, FanPower, LightPower, FanLevel, LightLevel, Timestamp, CollectionTime
            FROM sensor_data
            WHERE CollectionTime >= ?
            AND Temperature != 0 AND Humidity != 0 AND Light != 0
        """, (threshold,))
        rows = cursor.fetchall()
        
        return [{
            "t": row["Temperature"],
            "h": row["Humidity"],
            "l": row["Light"],
            "pf": row["FanPower"],
            "pl": row["LightPower"]
        } for row in rows]
    finally:
        conn.close()
 
def get_latest_records(n: int = 6):
    """获取最近 N 条传感器数据，用于行为分析窗口"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT Temperature, Humidity, Light, PirStatus, FanLevel, LightLevel, Timestamp
            FROM sensor_data
            ORDER BY CollectionTime DESC
            LIMIT ?
        """, (n,))
        rows = cursor.fetchall()
        return [dict(row) for row in reversed(rows)]  # 时间升序
    finally:
        conn.close()


def get_daily_energy_stats() -> dict:
    """获取最近5天（昨天及前4天）的分类能耗统计
    返回格式: {dates: [str], fan_energy: [float], light_energy: [float], days_available: int}
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        start_date = today - timedelta(days=5)  # 前5天
        end_date = today  # 到今天（不含今天）

        cursor.execute("""
            SELECT DATE(CollectionTime) as day,
                   FanPower, LightPower
            FROM sensor_data
            WHERE CollectionTime >= ? AND CollectionTime < ?
              AND (FanPower > 0 OR LightPower > 0)
            ORDER BY CollectionTime ASC
        """, (start_date.strftime('%Y-%m-%d %H:%M:%S'),
              end_date.strftime('%Y-%m-%d %H:%M:%S')))
        rows = cursor.fetchall()

        # 按日期分组，累加功率并计数
        daily_data = {}
        for row in rows:
            day = row["day"]
            if day not in daily_data:
                daily_data[day] = {"fan_sum": 0.0, "light_sum": 0.0, "count": 0}
            daily_data[day]["fan_sum"] += float(row["FanPower"] or 0)
            daily_data[day]["light_sum"] += float(row["LightPower"] or 0)
            daily_data[day]["count"] += 1

        # 生成5天日期列表，按公式计算能耗 (Wh) = sum(power) / 12
        dates = []
        fan_energy = []
        light_energy = []
        days_available = 0

        for i in range(5):
            d = start_date + timedelta(days=i)
            date_str = d.strftime('%m/%d')
            dates.append(date_str)

            day_key = d.strftime('%Y-%m-%d')
            if day_key in daily_data:
                data = daily_data[day_key]
                # 每条数据代表5秒，能耗(Wh) = 功率(W) × 5/3600(h) = 功率 / 720
                fan_wh = round(data["fan_sum"] / 720, 1)
                light_wh = round(data["light_sum"] / 720, 1)
                fan_energy.append(fan_wh)
                light_energy.append(light_wh)
                days_available += 1
            else:
                fan_energy.append(0)
                light_energy.append(0)

        return {
            "dates": dates,
            "fan_energy": fan_energy,
            "light_energy": light_energy,
            "days_available": days_available,
            "expected_days": 5
        }
    finally:
        conn.close()
 
def init_database():
    """初始化数据库（创建表）"""
    print("正在初始化数据库...")
    create_tables()
    print("数据库初始化完成")



import sqlite3
import datetime

def view_device_power_table():
    """专门查看device_power表的数据"""
    try:
        # 连接到数据库
        conn = sqlite3.connect('sensor_data.db')
        cursor = conn.cursor()
        
        print(f"device_power表查询结果 - {datetime.datetime.now()}")
        print("=" * 60)
        
        # 查询表的结构
        cursor.execute("PRAGMA table_info(device_power)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        # 打印列名
        print(" | ".join(column_names))
        print("-" * 60)
        
        # 查询表中的数据，按时间戳降序排列
        cursor.execute("SELECT * FROM device_power ORDER BY timestamp DESC LIMIT 10")
        rows = cursor.fetchall()
        
        # 打印数据行
        if rows:
            for row in rows:
                print(" | ".join(str(item) for item in row))
        else:
            print("(表中暂无数据)")
            
        # 打印数据行数
        cursor.execute("SELECT COUNT(*) FROM device_power")
        count = cursor.fetchone()[0]
        print(f"\n该表共有 {count} 条记录")
        
    except sqlite3.Error as e:
        print(f"数据库操作错误: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("查看device_power表工具")
    print("=" * 60)
    print("本工具将显示sensor_data.db数据库中device_power表的最近10条记录")
    print("=" * 60)
    view_device_power_table()
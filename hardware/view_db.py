import sqlite3
import datetime
import csv
import pandas as pd

def view_database_tables():
    """查看数据库中所有表的数据"""
    try:
        # 连接到数据库
        conn = sqlite3.connect('sensor_data.db')
        cursor = conn.cursor()
        
        # 获取所有表名
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"数据库表查询结果 - {datetime.datetime.now()}")
        print("=" * 80)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             
        
        for table in tables:
            table_name = table[0]
            print(f"\n表名: {table_name}")
            print("-" * 40)
            
            # 查询表的结构
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            # 打印列名和类型
            print("字段结构:")
            for col in columns:
                print(f"  {col[1]}: {col[2]}")
            
            print("-" * 80)
            
            # 查询表中的数据（根据是否有create_at字段决定排序方式）
            if 'create_at' in column_names:
                cursor.execute(f"SELECT * FROM {table_name} ORDER BY create_at DESC LIMIT 10")
            elif 'timestamp' in column_names:
                cursor.execute(f"SELECT * FROM {table_name} ORDER BY timestamp DESC LIMIT 10")
            else:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 10")
                
            rows = cursor.fetchall()
            
            # 打印数据行
            if rows:
                print("最近10条记录:")
                for row in rows:
                    formatted_row = []
                    for i, item in enumerate(row):
                        # 格式化显示
                        if isinstance(item, float):
                            formatted_row.append(f"{item:.2f}")
                        elif item is None:
                            formatted_row.append("NULL")
                        else:
                            formatted_row.append(str(item))
                    print(" | ".join(formatted_row))
            else:
                print("(表中暂无数据)")
                
            # 打印数据行数
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"\n该表共有 {count} 条记录")
            
            # 如果是sensor_data表，显示统计信息
            if table_name == 'sensor_data':
                print("\n传感器数据统计:")
                print("-" * 40)
                
                # 温度统计
                cursor.execute("SELECT AVG(temperature), MAX(temperature), MIN(temperature) FROM sensor_data WHERE temperature IS NOT NULL")
                temp_stats = cursor.fetchone()
                if temp_stats[0] is not None:
                    print(f"温度: 平均 {temp_stats[0]:.2f}°C, 最高 {temp_stats[1]:.2f}°C, 最低 {temp_stats[2]:.2f}°C")
                else:
                    print("温度: 暂无有效数据")
                
                # 湿度统计
                cursor.execute("SELECT AVG(humidity), MAX(humidity), MIN(humidity) FROM sensor_data WHERE humidity IS NOT NULL")
                humidity_stats = cursor.fetchone()
                if humidity_stats[0] is not None:
                    print(f"湿度: 平均 {humidity_stats[0]:.2f}%, 最高 {humidity_stats[1]:.2f}%, 最低 {humidity_stats[2]:.2f}%")
                else:
                    print("湿度: 暂无有效数据")
                
                # 光照统计
                cursor.execute("SELECT AVG(light), MAX(light), MIN(light) FROM sensor_data WHERE light IS NOT NULL")
                light_stats = cursor.fetchone()
                if light_stats[0] is not None:
                    print(f"光照: 平均 {light_stats[0]:.2f}, 最高 {light_stats[1]:.2f}, 最低 {light_stats[2]:.2f}")
                else:
                    print("光照: 暂无有效数据")
                
                # 设备功率统计
                cursor.execute("SELECT AVG(power_f), AVG(power_l) FROM sensor_data WHERE power_f IS NOT NULL AND power_l IS NOT NULL")
                power_stats = cursor.fetchone()
                if power_stats[0] is not None:
                    print(f"设备功率: 风扇平均 {power_stats[0]:.2f}W, 小灯平均 {power_stats[1]:.2f}W")
                else:
                    print("设备功率: 暂无有效数据")
                
                # 数据时间范围
                cursor.execute("SELECT MIN(create_at), MAX(create_at) FROM sensor_data")
                time_range = cursor.fetchone()
                if time_range[0] is not None:
                    print(f"数据时间范围: {time_range[0]} 到 {time_range[1]}")
                else:
                    print("数据时间范围: 暂无数据")
        
    except sqlite3.Error as e:
        print(f"数据库操作错误: {e}")
    finally:
        if conn:
            conn.close()

def view_sensor_data_details(limit=20):
    """查看传感器数据的详细内容"""
    try:
        conn = sqlite3.connect('sensor_data.db')
        cursor = conn.cursor()
        
        print(f"\n传感器数据详细内容 - 最近{limit}条记录")
        print("=" * 120)
        
        # 查询详细数据
        cursor.execute(f"""
            SELECT 
                id, temperature, humidity, light, pir, pir_status,
                pwm_f, pwm_l, power_f, power_l, level_f, level_l,
                timestamp, create_at
            FROM sensor_data 
            ORDER BY create_at DESC 
            LIMIT {limit}
        """)
        
        rows = cursor.fetchall()
        
        if rows:
            # 打印表头
            headers = ["ID", "温度", "湿度", "光照", "PIR", "PIR状态", 
                      "风扇PWM", "小灯PWM", "风扇功率", "小灯功率", 
                      "风扇挡位", "小灯挡位", "传感器时间", "创建时间"]
            print(" | ".join(f"{h:<10}" for h in headers))
            print("-" * 120)
            
            # 打印数据
            for row in rows:
                formatted_row = []
                for i, item in enumerate(row):
                    if i in [1, 2, 3, 6, 7, 8, 9]:  # 数值型字段
                        if item is not None:
                            formatted_row.append(f"{float(item):.2f}")
                        else:
                            formatted_row.append("NULL")
                    elif i in [4, 10, 11]:  # 整型字段
                        if item is not None:
                            formatted_row.append(f"{int(item)}")
                        else:
                            formatted_row.append("NULL")
                    else:  # 文本型字段
                        formatted_row.append(str(item) if item is not None else "NULL")
                
                print(" | ".join(f"{item:<10}" for item in formatted_row))
        else:
            print("(表中暂无数据)")
            
    except sqlite3.Error as e:
        print(f"数据库操作错误: {e}")
    finally:
        if conn:
            conn.close()

def export_to_csv(table_name="sensor_data", filename=None, limit=None):
    """导出数据库表到CSV文件"""
    try:
        conn = sqlite3.connect('sensor_data.db')
        cursor = conn.cursor()
        
        # 获取表结构
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        # 构建查询语句
        if limit:
            if 'create_at' in column_names:
                query = f"SELECT * FROM {table_name} ORDER BY create_at DESC LIMIT {limit}"
            elif 'timestamp' in column_names:
                query = f"SELECT * FROM {table_name} ORDER BY timestamp DESC LIMIT {limit}"
            else:
                query = f"SELECT * FROM {table_name} LIMIT {limit}"
        else:
            query = f"SELECT * FROM {table_name}"
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        # 生成文件名
        if filename is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{table_name}_export_{timestamp}.csv"
        
        # 写入CSV文件
        with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile)
            
            # 写入表头
            writer.writerow(column_names)
            
            # 写入数据
            for row in rows:
                writer.writerow(row)
        
        print(f"数据已成功导出到: {filename}")
        print(f"共导出 {len(rows)} 条记录")
        
        return filename
        
    except sqlite3.Error as e:
        print(f"数据库操作错误: {e}")
        return None
    except Exception as e:
        print(f"导出CSV文件错误: {e}")
        return None
    finally:
        if conn:
            conn.close()

def export_to_excel(table_name="sensor_data", filename=None, limit=None):
    """导出数据库表到Excel文件"""
    try:
        conn = sqlite3.connect('sensor_data.db')
        cursor = conn.cursor()
        
        # 获取表结构
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        # 构建查询语句
        if limit:
            if 'create_at' in column_names:
                query = f"SELECT * FROM {table_name} ORDER BY create_at DESC LIMIT {limit}"
            elif 'timestamp' in column_names:
                query = f"SELECT * FROM {table_name} ORDER BY timestamp DESC LIMIT {limit}"
            else:
                query = f"SELECT * FROM {table_name} LIMIT {limit}"
        else:
            query = f"SELECT * FROM {table_name}"
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        # 生成文件名
        if filename is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{table_name}_export_{timestamp}.xlsx"
        
        # 创建DataFrame并导出到Excel
        import pandas as pd
        df = pd.DataFrame(rows, columns=column_names)
        df.to_excel(filename, index=False, engine='openpyxl')
        
        print(f"数据已成功导出到: {filename}")
        print(f"共导出 {len(rows)} 条记录")
        
        return filename
        
    except sqlite3.Error as e:
        print(f"数据库操作错误: {e}")
        return None
    except ImportError:
        print("导出Excel文件需要安装pandas和openpyxl库，请运行: pip install pandas openpyxl")
        return None
    except Exception as e:
        print(f"导出Excel文件错误: {e}")
        return None
    finally:
        if conn:
            conn.close()

def export_all_tables_to_csv():
    """导出所有表到CSV文件"""
    try:
        conn = sqlite3.connect('sensor_data.db')
        cursor = conn.cursor()
        
        # 获取所有表名
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for table in tables:
            table_name = table[0]
            filename = f"{table_name}_export_{timestamp}.csv"
            
            # 导出单个表
            export_to_csv(table_name, filename)
        
        print(f"\n所有表已导出完成！")
        
    except sqlite3.Error as e:
        print(f"数据库操作错误: {e}")
    finally:
        if conn:
            conn.close()

def interactive_menu():
    """交互式菜单"""
    while True:
        print("\n" + "=" * 80)
        print("SQLite数据库工具菜单")
        print("=" * 80)
        print("1. 查看数据库表结构和数据")
        print("2. 查看传感器数据详细内容")
        print("3. 导出传感器数据到CSV文件")
        print("4. 导出传感器数据到Excel文件")
        print("5. 导出所有表到CSV文件")
        print("6. 退出")
        print("-" * 80)
        
        choice = input("请选择功能 (1-6): ").strip()
        
        if choice == "1":
            view_database_tables()
        elif choice == "2":
            try:
                limit = int(input("请输入要显示的记录数量 (默认20): ") or "20")
                view_sensor_data_details(limit)
            except ValueError:
                print("输入无效，使用默认值20")
                view_sensor_data_details()
        elif choice == "3":
            print("\n导出CSV文件选项:")
            print("1. 导出所有数据")
            print("2. 导出指定数量的数据")
            csv_choice = input("请选择 (1-2): ").strip()
            
            if csv_choice == "1":
                export_to_csv()
            elif csv_choice == "2":
                try:
                    limit = int(input("请输入要导出的记录数量: "))
                    export_to_csv(limit=limit)
                except ValueError:
                    print("输入无效，导出所有数据")
                    export_to_csv()
            else:
                print("无效选择，导出所有数据")
                export_to_csv()
        elif choice == "4":
            print("\n导出Excel文件选项:")
            print("1. 导出所有数据")
            print("2. 导出指定数量的数据")
            excel_choice = input("请选择 (1-2): ").strip()
            
            if excel_choice == "1":
                export_to_excel()
            elif excel_choice == "2":
                try:
                    limit = int(input("请输入要导出的记录数量: "))
                    export_to_excel(limit=limit)
                except ValueError:
                    print("输入无效，导出所有数据")
                    export_to_excel()
            else:
                print("无效选择，导出所有数据")
                export_to_excel()
        elif choice == "5":
            print("\n开始导出所有表到CSV文件...")
            export_all_tables_to_csv()
        elif choice == "6":
            print("感谢使用，再见！")
            break
        else:
            print("无效选择，请重新输入")

if __name__ == "__main__":
    print("SQLite数据库内容工具")
    print("=" * 80)
    print("本工具支持查看和导出sensor_data.db数据库中的数据")
    print("=" * 80)
    
    # 检查是否安装了必要的库
    try:
        import pandas as pd
        print("✓ pandas库已安装，支持Excel导出")
    except ImportError:
        print("⚠ pandas库未安装，Excel导出功能不可用")
        print("  请运行: pip install pandas openpyxl")
    
    try:
        import openpyxl
        print("✓ openpyxl库已安装，支持Excel导出")
    except ImportError:
        print("⚠ openpyxl库未安装，Excel导出功能不可用")
        print("  请运行: pip install openpyxl")
    
    interactive_menu()
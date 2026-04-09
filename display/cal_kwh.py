import sqlite3
import datetime
from database import get_db_connection

# 计算当天24小时每小时的能耗（kWh）
def calculate_hourly_energy_consumption():
    """
    计算当天24小时每小时的能耗（kWh）
    返回一个字典，包含每小时的能耗数据
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 获取当天的开始和结束时间
        today = datetime.datetime.now().date()
        today_start = datetime.datetime.combine(today, datetime.time.min)
        today_end = datetime.datetime.combine(today, datetime.time.max)
        
        # 格式化时间字符串
        today_start_str = today_start.strftime('%Y-%m-%d %H:%M:%S')
        today_end_str = today_end.strftime('%Y-%m-%d %H:%M:%S')
        
        # 查询当天所有设备的功率数据，按小时分组
        # power字段现在是REAL类型，不需要额外转换
        cursor.execute('''
        SELECT 
            strftime('%H', sensor_data.created_at) as hour,
            device_power.device_name,
            AVG(device_power.power) as avg_power,
            COUNT(*) as data_points
        FROM 
            device_power
        JOIN 
            sensor_data ON device_power.sensor_data_id = sensor_data.id
        WHERE 
            sensor_data.created_at >= ? AND sensor_data.created_at <= ?
            AND device_power.power IS NOT NULL
        GROUP BY 
            hour, device_power.device_name
        ORDER BY 
            hour, device_power.device_name
        ''', (today_start_str, today_end_str))
        
        results = cursor.fetchall()
        
        # 初始化24小时的能耗数据结构
        hourly_energy = {}
        for hour in range(24):
            hourly_energy[f"{hour:02d}"] = {
                'total_kwh': 0.0,
                'devices': {}
            }
        
        # 计算每小时的能耗
        # 能耗计算：平均功率(W) * 1小时 / 1000 = kWh
        for row in results:
            hour = row['hour']
            device_name = row['device_name']
            avg_power_w = row['avg_power']  # 瓦特(W)
            
            # 计算kWh (假设数据是每小时收集的，乘以1小时)
            energy_kwh = avg_power_w * 1 / 1000
            
            # 保存设备的能耗数据
            if device_name not in hourly_energy[hour]['devices']:
                hourly_energy[hour]['devices'][device_name] = 0.0
            hourly_energy[hour]['devices'][device_name] += energy_kwh
            
            # 更新总能耗
            hourly_energy[hour]['total_kwh'] += energy_kwh
        
        # 计算当天总能耗
        total_daily_kwh = sum(hour_data['total_kwh'] for hour_data in hourly_energy.values())
        
        return {
            'date': today.strftime('%Y-%m-%d'),
            'total_daily_kwh': round(total_daily_kwh, 4),
            'hourly_data': hourly_energy
        }
        
    except Exception as e:
        print(f"计算能耗时出错: {e}")
        return None
    finally:
        conn.close()

# 获取特定设备当天的能耗
def get_device_daily_energy(device_name):
    """
    获取特定设备当天的能耗
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 获取当天的开始和结束时间
        today = datetime.datetime.now().date()
        today_start = datetime.datetime.combine(today, datetime.time.min)
        today_end = datetime.datetime.combine(today, datetime.time.max)
        
        today_start_str = today_start.strftime('%Y-%m-%d %H:%M:%S')
        today_end_str = today_end.strftime('%Y-%m-%d %H:%M:%S')
        
        # 查询特定设备当天的平均功率
        # power字段现在是REAL类型，不需要额外转换
        cursor.execute('''
        SELECT 
            AVG(device_power.power) as avg_power,
            COUNT(*) as data_points
        FROM 
            device_power
        JOIN 
            sensor_data ON device_power.sensor_data_id = sensor_data.id
        WHERE 
            sensor_data.created_at >= ? 
            AND sensor_data.created_at <= ?
            AND device_power.device_name = ?
            AND device_power.power IS NOT NULL
        ''', (today_start_str, today_end_str, device_name))
        
        result = cursor.fetchone()
        
        if result and result['avg_power']:
            avg_power_w = result['avg_power']
            # 假设全天运行，计算总能耗 (kWh)
            daily_energy_kwh = avg_power_w * 24 / 1000
            return round(daily_energy_kwh, 4)
        else:
            return 0.0
            
    except Exception as e:
        print(f"获取设备能耗时出错: {e}")
        return 0.0
    finally:
        conn.close()

# 保存能耗计算结果到文件
def save_energy_report_to_file(report, filename=None):
    """
    将能耗报告保存到文件
    """
    if not report:
        print("没有可用的能耗报告数据")
        return False
    
    if not filename:
        filename = f"energy_report_{report['date']}.txt"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"能耗报告 - {report['date']}\n")
            f.write(f"当天总能耗: {report['total_daily_kwh']} kWh\n\n")
            f.write("每小时能耗详情:\n")
            
            for hour in sorted(report['hourly_data'].keys()):
                hour_data = report['hourly_data'][hour]
                f.write(f"\n{hour}:00 - {hour}:59\n")
                f.write(f"  总能耗: {hour_data['total_kwh']:.4f} kWh\n")
                
                for device, energy in hour_data['devices'].items():
                    f.write(f"  {device}: {energy:.4f} kWh\n")
        
        print(f"能耗报告已保存到: {filename}")
        return True
    except Exception as e:
        print(f"保存能耗报告失败: {e}")
        return False

# 打印能耗报告
def print_energy_report(report):
    """
    打印能耗报告到控制台
    """
    if not report:
        print("没有可用的能耗报告数据")
        return
    
    print(f"\n===== 能耗报告 - {report['date']} =====")
    print(f"当天总能耗: {report['total_daily_kwh']} kWh")
    print("\n每小时能耗详情:")
    
    for hour in sorted(report['hourly_data'].keys()):
        hour_data = report['hourly_data'][hour]
        print(f"\n{hour}:00 - {hour}:59")
        print(f"  总能耗: {hour_data['total_kwh']:.4f} kWh")
        
        if hour_data['devices']:
            print("  设备详情:")
            for device, energy in hour_data['devices'].items():
                print(f"    {device}: {energy:.4f} kWh")

# 测试代码
if __name__ == "__main__":
    print("开始计算当天24小时能耗...")
    
    # 计算每小时能耗
    energy_report = calculate_hourly_energy_consumption()
    
    if energy_report:
        # 打印报告
        print_energy_report(energy_report)
        
        # 保存报告到文件
        save_energy_report_to_file(energy_report)
        
        # 计算特定设备能耗
        fan_energy = get_device_daily_energy("风扇")
        light_energy = get_device_daily_energy("小灯")
        
        print(f"\n设备当天总能耗:")
        print(f"风扇: {fan_energy:.4f} kWh")
        print(f"小灯: {light_energy:.4f} kWh")
    else:
        print("无法生成能耗报告")

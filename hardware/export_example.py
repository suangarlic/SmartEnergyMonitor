#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库导出功能使用示例
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from view_db import export_to_csv, export_to_excel, export_all_tables_to_csv

def example_usage():
    """使用示例"""
    print("数据库导出功能使用示例")
    print("=" * 60)
    
    # 示例1: 导出传感器数据到CSV（最近100条记录）
    print("\n1. 导出传感器数据到CSV文件（最近100条记录）")
    print("-" * 50)
    filename = export_to_csv(limit=100)
    if filename:
        print(f"✓ 导出成功: {filename}")
    
    # 示例2: 导出所有传感器数据到Excel
    print("\n2. 导出所有传感器数据到Excel文件")
    print("-" * 50)
    filename = export_to_excel()
    if filename:
        print(f"✓ 导出成功: {filename}")
    
    # 示例3: 导出所有表到CSV
    print("\n3. 导出所有表到CSV文件")
    print("-" * 50)
    export_all_tables_to_csv()
    
    print("\n" + "=" * 60)
    print("示例执行完成！")
    print("\n提示：")
    print("- 要使用交互式菜单，请直接运行: python view_db.py")
    print("- 导出的文件会保存在当前目录下")
    print("- 文件名包含时间戳，避免覆盖已有文件")

if __name__ == "__main__":
    example_usage()
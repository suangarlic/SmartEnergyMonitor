# test_run.py - 测试行空板启动
import sys

print("=== 测试启动 ===")
print("Python版本:", sys.version)

# 测试基本导入
try:
    print("测试导入...")
    
    import time
    print("✓ time")
    
    import json
    print("✓ json")
    
    import threading
    print("✓ threading")
    
    import urllib.request
    print("✓ urllib.request")
    
    print("基本导入成功")
except Exception as e:
    print(f"导入失败: {e}")
    sys.exit(1)

# 测试配置导入
try:
    from config import PC_IP, PC_PORT
    print(f"✓ config.py - PC_IP={PC_IP}, PC_PORT={PC_PORT}")
except Exception as e:
    print(f"config导入失败: {e}")
    
print("=== 测试完成 ===")
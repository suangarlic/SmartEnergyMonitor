# test_model.py - 测试模型加载
import joblib
import os

base_dir = os.path.dirname(os.path.abspath(__file__))

print("Testing model loading...")
try:
    presence_model = joblib.load(os.path.join(base_dir, "behavior_presence.pkl"))
    print("presence_model loaded successfully")
except Exception as e:
    print("presence_model failed:", str(e))

try:
    fan_model = joblib.load(os.path.join(base_dir, "behavior_fan.pkl"))
    print("fan_model loaded successfully")
except Exception as e:
    print("fan_model failed:", str(e))

try:
    light_model = joblib.load(os.path.join(base_dir, "behavior_light.pkl"))
    print("light_model loaded successfully")
except Exception as e:
    print("light_model failed:", str(e))

print("Test complete!")
# test_behavior.py - 测试节能控制效果
import pandas as pd
from data.sensor_repository import get_latest_records
from analyzer.behavior_compare import BehaviorComparator

print("=" * 60)
print("           节能控制效果演示")
print("=" * 60)

df = pd.read_csv("data/sensor_data_week.csv")
df["Timestamp"] = pd.to_datetime(df["Timestamp"])
df = df.sort_values("Timestamp").reset_index(drop=True)

comp = BehaviorComparator(debounce_count=1)
results = comp.compare_batch(df, window_size=6, stride=2)

print(f"分析窗口总数: {len(results)}")

# 统计节能场景
from collections import Counter
scenario_counts = Counter(r.scenario for r in results)
energy_saving_count = scenario_counts.get("energy_saving", 0)
comfort_adjust_count = scenario_counts.get("comfort_adjust", 0)
total_saving = energy_saving_count + comfort_adjust_count

print(f"\n节能场景统计:")
print(f"  无人节能(energy_saving): {energy_saving_count} 次 → 关闭设备")
print(f"  智能调节(comfort_adjust): {comfort_adjust_count} 次 → 微调档位")
print(f"  总计节能操作: {total_saving} 次")

print("\n" + "=" * 60)
print("           节能控制案例展示")
print("=" * 60)

# 分类展示不同节能场景
energy_cases = []
comfort_cases = []
for r in results:
    if r.trigger:
        if r.scenario == "energy_saving":
            energy_cases.append(r)
        elif r.scenario == "comfort_adjust":
            comfort_cases.append(r)

# 展示无人节能案例
print("\n【节能类型1】无人状态 - 关闭设备")
print("-" * 40)
for i, r in enumerate(energy_cases[:3], 1):
    print(f"\n案例{i}: {r.timestamp}")
    print(f"  真实状态: 有人={r.real_presence} 风扇={r.real_fan_level}档 灯光={r.real_light_level}档")
    print(f"  判定: {r.reason}")
    print(f"  → [节能] 关闭风扇、灯光")

# 展示智能调节案例（调低档位）
print("\n\n【节能类型2】有人状态 - 调低档位")
print("-" * 40)
down_cases = [r for r in comfort_cases 
              if (r.real_fan_level > r.expected_fan_level) or (r.real_light_level > r.expected_light_level)]
for i, r in enumerate(down_cases[:3], 1):
    print(f"\n案例{i}: {r.timestamp}")
    print(f"  真实状态: 风扇={r.real_fan_level}档 灯光={r.real_light_level}档")
    print(f"  建议状态: 风扇={r.expected_fan_level}档 灯光={r.expected_light_level}档")
    print(f"  → [节能] 降低档位以节省用电")

# 展示智能调节案例（调高档位 - 舒适优先）
print("\n\n【舒适类型】有人状态 - 调高档位")
print("-" * 40)
up_cases = [r for r in comfort_cases 
            if (r.real_fan_level < r.expected_fan_level) or (r.real_light_level < r.expected_light_level)]
for i, r in enumerate(up_cases[:2], 1):
    print(f"\n案例{i}: {r.timestamp}")
    print(f"  真实状态: 风扇={r.real_fan_level}档 灯光={r.real_light_level}档")
    print(f"  建议状态: 风扇={r.expected_fan_level}档 灯光={r.expected_light_level}档")
    print(f"  → [舒适] 提升档位以改善体验")

print("\n" + "=" * 60)
print("           节能效果估算")
print("=" * 60)
# 假设风扇各档位功率: 0档=0W, 1档=5W, 2档=15W, 3档=25W
# 假设灯光各档位功率: 0档=0W, 1档=2W, 2档=4W, 3档=9W
fan_power = {0:0, 1:5, 2:15, 3:25}
light_power = {0:0, 1:2, 2:4, 3:9}

total_saved_watts = 0
for r in results:
    if r.trigger:
        if r.scenario == "energy_saving":
            # 关闭设备的节能
            saved = fan_power[r.real_fan_level] + light_power[r.real_light_level]
            total_saved_watts += saved
        elif r.scenario == "comfort_adjust":
            # 调低档位的节能
            fan_saved = max(0, fan_power[r.real_fan_level] - fan_power[r.expected_fan_level])
            light_saved = max(0, light_power[r.real_light_level] - light_power[r.expected_light_level])
            total_saved_watts += fan_saved + light_saved

print(f"\n一周预估节能: {total_saved_watts} 瓦时 ≈ {total_saved_watts/1000:.2f} 度")
print(f"按日均计算: {total_saved_watts/7/1000:.2f} 度/天")
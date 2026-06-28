import csv
import math
import random
from datetime import datetime, timedelta

# ====================== 核心配置 ======================
START_TIME  = datetime(2026, 6, 1, 2, 1, 43)   # 非准点起始，模拟真实场景
END_TIME    = datetime(2026, 6, 7, 23, 53, 17)  # 非准点结束
TIME_STEP   = timedelta(minutes=5)   # 5 分钟粒度
OUTPUT_FILE = "sensor_data_6.1-6.7_贴合课表数据_v7.csv"

WORKDAY_LIST = [1, 2, 3, 4, 5]
REST_DAY_LIST = [6, 7]

FAN_POWER_MAP   = {0: 0.0, 1: 5.0, 2: 15.0, 3: 25.0}
LIGHT_POWER_MAP = {0: 0.0, 1: 1.0, 2: 3.0,  3: 5.0}

# 档位错配：10% 概率在有人时使用过高档位（不节能习惯）
GEAR_MISMATCH_PROB = 0.10
# 暂时离场：15% 概率在有人使用设备时触发短时离开（<30min）
TEMP_LEAVE_PROB = 0.15

NIGHT_TEMP_RANGE    = (25.5, 26.0)
NIGHT_HUMIDITY_RANGE = (82.0, 83.0)
NIGHT_LIGHT_RANGE   = (80.0, 100.0)

TABLE_HEADERS = [
    "Id", "Temperature", "Humidity", "Light", "PirStatus", "PirText",
    "FanPower", "LightPower", "FanLevel", "LightLevel", "Timestamp", "CollectionTime"
]

# ====================== 作息时间配置 ======================
CLASS_SCHEDULE = {
    1: [(13.0, 15.5)],                # 周一 13:00-15:30
    2: [(13.0, 15.5)],                # 周二 13:00-15:30
    3: [(8.0, 10.0), (18.0, 20.0)],   # 周三 08:00-10:00 + 18:00-20:00
    4: [],
    5: [],
}

MEAL_TIME_RANGES = [(11.75, 13.17), (17.67, 18.92)]  # 11:45-13:10, 17:40-18:55

# 环境光照时段
NIGHT_BEGIN    = 20.83   # 20:50
MORNING_BEGIN  = 6.42    # 06:25
MORNING_END    = 8.83    # 08:50
EVENING_BEGIN  = 18.5    # 18:30

# ====================== 预选空转浪费时段 ======================
# 收集所有上课时段（周一~周三）和午间吃饭时段（全周7天）
all_class_periods = []
for day in [1, 2, 3]:
    for s, e in CLASS_SCHEDULE.get(day, []):
        all_class_periods.append((day, s, e, "class"))

all_lunch_periods = []
for day in range(1, 8):
    if day in WORKDAY_LIST:
        s, e = 12.583, 13.833   # 工作日午休 12:35-13:50
    else:
        s, e = 11.75, 13.167    # 休息日外出 11:45-13:10
    all_lunch_periods.append((day, s, e, "lunch"))

random.seed(42)
selected_class = random.sample(all_class_periods, 2)
selected_lunch = random.sample(all_lunch_periods, 3)
IDLE_WASTE_PERIODS = selected_class + selected_lunch

DAY_NAMES = {1: "一", 2: "二", 3: "三", 4: "四", 5: "五", 6: "六", 7: "日"}
print("预选空转浪费时段（2上课 + 3午餐）:")
for p in IDLE_WASTE_PERIODS:
    sh, sm = int(p[1]), int((p[1] - int(p[1])) * 60)
    eh, em = int(p[2]), int((p[2] - int(p[2])) * 60)
    print(f"  周{DAY_NAMES[p[0]]} {sh:02d}:{sm:02d} - {eh:02d}:{em:02d}  ({p[3]})")
print()

# ====================== 时间辅助函数 ======================
def td(h, m):
    return h + m / 60.0

def in_range(h, m, start, end):
    return start <= td(h, m) < end

def is_in_idle_waste(day, h, m):
    """返回 (is_in, period_index)"""
    t = td(h, m)
    for idx, (d, s, e, _) in enumerate(IDLE_WASTE_PERIODS):
        if d == day and s <= t < e:
            return True, idx
    return False, -1

# ====================== 作息判定 ======================
def is_falling_asleep(h, m):
    t = td(h, m)
    return t >= 23.25 or t < 0.333

def is_deep_sleep(h, m):
    return in_range(h, m, 0.333, 6.833)

def is_waking_up(h, m):
    return in_range(h, m, 6.833, 8.167)

def is_noon_rest(h, m):
    return in_range(h, m, 12.583, 13.833)

def is_meal_time(h, m):
    for s, e in MEAL_TIME_RANGES:
        if in_range(h, m, s, e):
            return True
    return False

def is_in_class(day, h, m):
    t = td(h, m)
    if day in CLASS_SCHEDULE:
        for s, e in CLASS_SCHEDULE[day]:
            if s <= t < e:
                return True
    return False

# ====================== 环境数据 ======================
def is_night(h, m):
    return td(h, m) >= NIGHT_BEGIN or td(h, m) < MORNING_BEGIN

def is_morning_transition(h, m):
    return in_range(h, m, MORNING_BEGIN, MORNING_END)

def is_evening_transition(h, m):
    return in_range(h, m, EVENING_BEGIN, NIGHT_BEGIN)

def gen_env(h, m):
    t = td(h, m)
    if is_night(h, m):
        temp = round(random.uniform(*NIGHT_TEMP_RANGE), 1)
        hum  = round(random.uniform(*NIGHT_HUMIDITY_RANGE), 1)
        lux  = round(random.uniform(*NIGHT_LIGHT_RANGE), 1)
    elif is_morning_transition(h, m):
        p = (t - MORNING_BEGIN) / (MORNING_END - MORNING_BEGIN)
        temp = round(25.8 + 1.8 * p + random.uniform(-0.3, 0.3), 1)
        hum  = round(82.5 - 12 * p + random.uniform(-1.5, 1.5), 1)
        lux  = round(90 + 350 * p + random.uniform(-25, 25), 1)
    elif is_evening_transition(h, m):
        p = (t - EVENING_BEGIN) / (NIGHT_BEGIN - EVENING_BEGIN)
        temp = round(27.0 - 1.3 * p + random.uniform(-0.3, 0.3), 1)
        hum  = round(72 + 10 * p + random.uniform(-1.5, 1.5), 1)
        lux  = round(max(80, 450 * (1 - p) + random.uniform(-30, 30)), 1)
    else:
        temp = round(25.5 + 3 * math.sin((t - 8.83) * math.pi / 9.67) + random.uniform(-0.4, 0.4), 1)
        hum  = round(55 - 8 * math.sin((t - 8.83) * math.pi / 9.67) + random.uniform(-2, 2), 1)
        if t <= 18.0:
            lux  = round(max(0, 520 * math.sin((t - 6.42) * math.pi / 11.58) + random.uniform(-25, 25)), 1)
        else:
            lux  = round(random.uniform(150, 320), 1)
    temp = max(22.0, min(30.0, temp))
    hum  = max(40.0, min(85.0, hum))
    lux  = max(0,   min(600, lux))
    return temp, hum, lux

# ====================== 人员状态（未被空转/暂时离场覆盖时） ======================
def get_pir(day, h, m, is_workday):
    if is_deep_sleep(h, m):
        return (0, "deep_sleep") if random.random() < 0.98 else (1, "deep_sleep")
    if is_falling_asleep(h, m):
        return (1, "fall_asleep") if random.random() < 0.85 else (0, "fall_asleep")
    if is_waking_up(h, m):
        return (1, "wake_up") if random.random() < 0.80 else (0, "wake_up")
    if is_noon_rest(h, m):
        return (0, "noon_rest") if random.random() < 0.85 else (1, "noon_rest")
    if is_workday:
        if is_in_class(day, h, m):
            return (0, "class") if random.random() < 0.95 else (1, "class")
        if in_range(h, m, 8.167, 18.5):
            return (1, "daytime") if random.random() < 0.70 else (0, "daytime")
    else:
        if is_meal_time(h, m):
            return (0, "meal") if random.random() < 0.90 else (1, "meal")
        if in_range(h, m, 8.167, 23.0):
            return (1, "rest_day") if random.random() < 0.80 else (0, "rest_day")
    return (1, "default") if random.random() < 0.85 else (0, "default")

# ====================== 主生成逻辑 ======================
def generate_sensor_data():
    data_rows = []
    ct = START_TIME
    rid = 1

    # 状态追踪
    last_present_fan   = 0   # 最近有人时的风扇档位
    last_present_light = 0   # 最近有人时的小灯档位
    prev_pir = 1

    # 空转浪费：预选时段 → 强制无人 + 设备保持离开时状态
    idle_waste_device_fan   = 0
    idle_waste_device_light = 0
    idle_waste_entered = {}  # {(day, period_index): True} 追踪每个时段是否已初始化

    # 暂时离场：短时离开（<30min），设备保持运行
    temp_leave_remaining = 0   # 剩余暂时离场点数
    temp_leave_fan   = 0
    temp_leave_light = 0
    temp_leave_cooldown = 0    # 触发冷却（避免频繁触发）

    while ct <= END_TIME:
        h = ct.hour
        m = ct.minute
        d = ct.day
        is_wd = d in WORKDAY_LIST

        # 1. 环境
        temp, hum, lux = gen_env(h, m)

        # 2. 人员（优先级：空转浪费 > 暂时离场 > 正常作息）
        in_idle, idle_idx = is_in_idle_waste(d, h, m)

        if in_idle:
            pir = 0
            pir_text = "无人"
            reason = "idle_waste"
        elif temp_leave_remaining > 0:
            pir = 0
            pir_text = "无人"
            reason = "temp_leave"
            temp_leave_remaining -= 1
        else:
            pir, reason = get_pir(d, h, m, is_wd)
            pir_text = "有人" if pir == 1 else "无人"

        # 3. 设备档位 & 功率
        fan_lv   = 0
        light_lv = 0
        fan_pw   = 0.0
        light_pw = 0.0

        if pir == 0:
            # === 无人状态 ===
            if in_idle:
                # 空转浪费：进入时段时记录设备状态，整个时段保持
                if idle_idx not in idle_waste_entered:
                    idle_waste_device_fan   = last_present_fan if last_present_fan > 0 else random.choice([2, 3])
                    idle_waste_device_light = last_present_light if last_present_light > 0 else random.choice([1, 2])
                    idle_waste_entered[idle_idx] = True
                fan_lv   = idle_waste_device_fan
                light_lv = idle_waste_device_light
            elif temp_leave_remaining >= 0 and reason == "temp_leave":
                # 暂时离场：设备保持离开时状态
                fan_lv   = temp_leave_fan
                light_lv = temp_leave_light
            else:
                # 正常无人：设备全关
                fan_lv   = 0
                light_lv = 0

            fan_pw   = FAN_POWER_MAP[fan_lv]
            light_pw = LIGHT_POWER_MAP[light_lv]

        else:
            # === 有人状态 ===
            temp_leave_remaining = 0

            # 正常档位
            if temp < 24.5:
                normal_fan = 0
            elif temp < 26.5:
                normal_fan = 1
            elif temp < 28.0:
                normal_fan = 2
            else:
                normal_fan = 3

            if lux > 400:
                normal_light = 0
            elif lux > 200:
                normal_light = 1
            elif lux > 100:
                normal_light = 2
            else:
                normal_light = 3

            # 档位错配 10%：不节能习惯，使用过高档位
            if random.random() < GEAR_MISMATCH_PROB:
                fan_lv   = min(normal_fan   + random.choice([1, 2]), 3)
                light_lv = min(normal_light + random.choice([1, 2]), 3)
            else:
                fan_lv   = normal_fan
                light_lv = normal_light

            fan_pw   = FAN_POWER_MAP[fan_lv]
            light_pw = LIGHT_POWER_MAP[light_lv]

            # 记录当前设备状态（用于空转浪费/暂时离场）
            last_present_fan   = fan_lv
            last_present_light = light_lv

            # 暂时离场触发：有人 + 设备运行 + 冷却结束 → 15% 概率短时离开
            if temp_leave_cooldown <= 0 and (fan_lv > 0 or light_lv > 0):
                if random.random() < TEMP_LEAVE_PROB:
                    temp_leave_remaining = random.randint(1, 5)   # 5~25 min
                    temp_leave_fan   = fan_lv
                    temp_leave_light = light_lv
                    temp_leave_cooldown = 12                      # 冷却 60 min

        # 冷却递减
        if temp_leave_cooldown > 0:
            temp_leave_cooldown -= 1

        prev_pir = pir

        # 4. 时间（两个时间戳：设备时间戳 vs 采集时间，模拟真实微小延迟）
        offset1 = random.randint(-2, 2)   # 设备时间戳偏移
        offset2 = random.randint(0, 2)    # 采集时间额外延迟
        ts_device = (ct + timedelta(seconds=offset1)).strftime("%Y-%m-%d %H:%M:%S")
        ts_collect = (ct + timedelta(seconds=offset1 + offset2)).strftime("%Y-%m-%d %H:%M:%S")

        # 5. 组装行
        data_rows.append([
            rid, temp, hum, lux, pir, pir_text,
            fan_pw, light_pw, fan_lv, light_lv, ts_device, ts_collect
        ])

        ct += TIME_STEP
        rid += 1

    return data_rows

# ====================== 写入 CSV ======================
def write_to_csv(data_rows):
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(TABLE_HEADERS)
        w.writerows(data_rows)

    print("[OK] 数据生成完成")
    print(f"  文件: {OUTPUT_FILE}")
    print(f"  条数: {len(data_rows)} 条")
    print(f"  范围: 2026-06-01 ~ 2026-06-07（5min粒度）")
    print(f"  空转: 预选 2上课+3午餐 时段，整个时段强制无人+设备运行")
    print(f"  暂离: 15%概率触发短时离开(<30min)，设备保持运行，60min冷却")
    print(f"  错配: 10%概率在有人时使用过高档位（不节能习惯）")

if __name__ == "__main__":
    write_to_csv(generate_sensor_data())
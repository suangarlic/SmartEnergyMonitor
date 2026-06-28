# dataset_builder.py - 行为建模数据集构建模块
# 滑动窗口生成行为特征X，y为用户习惯期望值（非下一时刻预测）
# 用于行为模型训练，学习用户设备使用习惯

import pandas as pd
from .feature_engine import extract_features


def build_dataset(csv_path: str = "data/sensor_data_week.csv", window_size: int = 6, stride: int = 2):
    """
    读取CSV，按时间排序，滑动窗口构建行为建模训练集。

    y 来自窗口内真实传感器数据（用户习惯期望值）：
      - expected_fan_level:   窗口内 FanLevel 均值取整
      - expected_light_level: 窗口内 LightLevel 均值取整
      - expected_presence:    窗口内真实 PIR 多数判定

    Args:
        csv_path:   CSV文件路径
        window_size: 滑动窗口大小（条数），默认 6
        stride:     滑动步长，默认 2

    Returns:
        X_behavior:          pd.DataFrame，行为特征向量
        y_expected_fan:      pd.Series，期望风扇档位（0/1/2/3）
        y_expected_light:    pd.Series，期望灯光档位（0/1/2/3）
        y_expected_presence: pd.Series，期望有人/无人（0/1）
    """
    df = pd.read_csv(csv_path, encoding='gbk')

    # 按时间排序
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])
    df = df.sort_values("Timestamp").reset_index(drop=True)

    WINDOW = window_size
    X_list = []
    y_fan_list = []
    y_light_list = []
    y_presence_list = []

    # 滑动窗口：仅用窗口内数据，不依赖下一时刻
    for i in range(0, len(df) - WINDOW + 1, stride):
        window_df = df.iloc[i : i + WINDOW]

        # X：行为特征向量
        features = extract_features(window_df)
        X_list.append(features)

        # y：用户习惯期望值（均来自窗口内真实数据）
        fan_mean = window_df["FanLevel"].mean()
        y_fan_list.append(round(fan_mean))

        light_mean = window_df["LightLevel"].mean()
        y_light_list.append(round(light_mean))

        # 真实PIR数据：窗口内多数采样点有人 → 判定为有人
        y_presence_list.append(1 if window_df["PirStatus"].mean() > 0.5 else 0)

    X_behavior = pd.DataFrame(X_list)
    y_expected_fan = pd.Series(y_fan_list, name="ExpectedFanLevel")
    y_expected_light = pd.Series(y_light_list, name="ExpectedLightLevel")
    y_expected_presence = pd.Series(y_presence_list, name="ExpectedPresence")

    return X_behavior, y_expected_fan, y_expected_light, y_expected_presence


if __name__ == "__main__":
    X, y_f, y_l, y_p = build_dataset()
    print(f"X_behavior shape: {X.shape}")
    print(f"特征列: {list(X.columns)}")
    print(f"\n期望风扇档位分布:\n{y_f.value_counts().sort_index()}")
    print(f"\n期望灯光档位分布:\n{y_l.value_counts().sort_index()}")
    print(f"\n期望有人/无人分布:\n{y_p.value_counts().sort_index()}")
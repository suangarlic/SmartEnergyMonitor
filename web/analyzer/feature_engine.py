# feature_engine.py - 用户行为特征工程模块
# 从窗口数据提取行为特征向量，训练和推理共用

import math
import pandas as pd


class FeatureExtractor:
    """用户行为特征提取器，输入窗口DataFrame，输出特征dict"""

    # 全量特征列名
    ALL_FEATURES = [
        "temp_mean", "humidity_mean", "light_mean",
        "hour", "hour_sin", "hour_cos", "weekday", "is_weekend",
        "pir_ratio", "fan_mean", "light_level_mean",
    ]

    # presence 模型排除的特征（防泄露）
    PRESENCE_EXCLUDE = {"pir_ratio", "fan_mean", "light_level_mean"}

    # fan 模型排除的特征
    FAN_EXCLUDE = {"fan_mean"}

    # light 模型排除的特征
    LIGHT_EXCLUDE = {"light_level_mean"}

    def transform(self, df: pd.DataFrame) -> dict:
        """
        从窗口传感器数据中提取用户行为特征向量。

        Args:
            df: 窗口传感器数据，必须包含以下列：
                Temperature, Humidity, Light, PirStatus, FanLevel, LightLevel, Timestamp

        Returns:
            dict: 11 维行为特征向量
        """
        if len(df) == 0:
            raise ValueError("输入DataFrame不能为空")

        features = {}

        # ---- 环境特征 ----
        features["temp_mean"] = df["Temperature"].mean()
        features["humidity_mean"] = df["Humidity"].mean()
        features["light_mean"] = df["Light"].mean()

        # ---- 时间特征 ----
        last_ts = pd.to_datetime(df["Timestamp"].iloc[-1])
        features["hour"] = last_ts.hour
        features["hour_sin"] = math.sin(2 * math.pi * last_ts.hour / 24)
        features["hour_cos"] = math.cos(2 * math.pi * last_ts.hour / 24)
        features["weekday"] = last_ts.weekday()       # 0=周一, 6=周日
        features["is_weekend"] = 1 if last_ts.weekday() >= 5 else 0

        # ---- 行为特征 ----
        features["pir_ratio"] = df["PirStatus"].mean()

        # ---- 历史习惯特征（用户设备使用偏好）----
        features["fan_mean"] = df["FanLevel"].mean()
        features["light_level_mean"] = df["LightLevel"].mean()

        return features

    def get_feature_names(self, model_type: str) -> list[str]:
        """返回指定模型使用的特征列名"""
        exclude = {
            "presence": self.PRESENCE_EXCLUDE,
            "fan": self.FAN_EXCLUDE,
            "light": self.LIGHT_EXCLUDE,
        }.get(model_type, set())
        return [f for f in self.ALL_FEATURES if f not in exclude]


# 兼容旧接口
def extract_features(df: pd.DataFrame) -> dict:
    """兼容旧版调用"""
    return FeatureExtractor().transform(df)
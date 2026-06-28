# behavior_compare.py - "期望 vs 真实" 行为比对模块
# 加载行为模型，预测期望状态，与真实传感器数据比对
# 防抖机制 + 预设场景分支 + 统一输出，对接大模型

from dataclasses import dataclass, field
from typing import Optional
from collections import deque

import joblib
import numpy as np
import pandas as pd

from .feature_engine import FeatureExtractor


# ============================================================
# 场景枚举
# ============================================================
class Scenario:
    NORMAL = "normal"                   # 正常状态：基准与真实一致
    ENERGY_SAVING = "energy_saving"      # 节能场景：无人但设备运行
    COMFORT_ADJUST = "comfort_adjust"    # 舒适调节：档位滞后
    ABNORMAL_SCHEDULE = "abnormal_schedule"  # 作息异常：上课时段持续有人


# ============================================================
# 比对结论（固定字段，对接大模型）
# ============================================================
@dataclass
class CompareResult:
    timestamp: str                          # 当前窗口时间戳
    # 人员
    real_presence: int                      # 真实有人/无人 (0/1)
    expected_presence: int                  # 模型期望有人/无人 (0/1)
    presence_match: bool                    # 是否一致
    # 风扇
    real_fan_level: int                     # 真实风扇档位
    expected_fan_level: int                 # 模型期望风扇档位
    fan_deviation: int                      # 偏差档位 (abs)
    # 灯光
    real_light_level: int                   # 真实灯光档位
    expected_light_level: int               # 模型期望灯光档位
    light_deviation: int                    # 偏差档位 (abs)
    # 场景与动作
    scenario: str                           # 场景分类
    trigger: bool                           # 是否触发控制/提醒
    action: str                             # 建议动作
    reason: str                             # 判定依据

    def to_dict(self) -> dict:
        """转为大模型可读的 dict"""
        return {
            "timestamp": self.timestamp,
            "real_presence": self.real_presence,
            "expected_presence": self.expected_presence,
            "presence_match": self.presence_match,
            "real_fan_level": self.real_fan_level,
            "expected_fan_level": self.expected_fan_level,
            "fan_deviation": self.fan_deviation,
            "real_light_level": self.real_light_level,
            "expected_light_level": self.expected_light_level,
            "light_deviation": self.light_deviation,
            "scenario": self.scenario,
            "trigger": self.trigger,
            "action": self.action,
            "reason": self.reason,
        }

    def to_llm_context(self) -> str:
        """生成可直接供大模型使用的格式化文本"""
        return (
            f"时间: {self.timestamp}\n"
            f"人员: 预期{'有人' if self.expected_presence else '无人'} "
            f"实际{'有人' if self.real_presence else '无人'} "
            f"{'一致' if self.presence_match else '不一致'}\n"
            f"风扇: 预期{self.expected_fan_level}档 实际{self.real_fan_level}档 "
            f"偏差{self.fan_deviation}档\n"
            f"灯光: 预期{self.expected_light_level}档 实际{self.real_light_level}档 "
            f"偏差{self.light_deviation}档\n"
            f"场景: {self.scenario}\n"
            f"触发: {'是' if self.trigger else '否'}\n"
            f"动作: {self.action}\n"
            f"依据: {self.reason}"
        )


# ============================================================
# 防抖器
# ============================================================
class Debouncer:
    """连续 N 个窗口检测到偏差才触发，避免传感器随机波动"""

    def __init__(self, threshold: int = 1):
        self._threshold = threshold
        self._buffer: deque = deque(maxlen=threshold)

    def push(self, deviated: bool) -> bool:
        """推入本次偏差结果，返回是否触发"""
        self._buffer.append(deviated)
        if len(self._buffer) < self._threshold:
            return False
        return all(self._buffer)

    def reset(self):
        self._buffer.clear()


# ============================================================
# 核心比对器
# ============================================================
class BehaviorComparator:
    """加载三个行为模型，对每个窗口执行期望 vs 真实比对"""

    def __init__(
        self,
        presence_model_path: str = None,
        fan_model_path: str = None,
        light_model_path: str = None,
        debounce_count: int = 1,
    ):
        import os
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        if presence_model_path is None:
            presence_model_path = os.path.join(base_dir, "models", "behavior_presence.pkl")
        if fan_model_path is None:
            fan_model_path = os.path.join(base_dir, "models", "behavior_fan.pkl")
        if light_model_path is None:
            light_model_path = os.path.join(base_dir, "models", "behavior_light.pkl")
        
        self.presence_model = joblib.load(presence_model_path)
        self.fan_model = joblib.load(fan_model_path)
        self.light_model = joblib.load(light_model_path)

        # 单线程预测，避免批量循环中 joblib 并行死锁
        self.presence_model.n_jobs = 1
        self.fan_model.n_jobs = 1
        self.light_model.n_jobs = 1

        self._debounce_presence = Debouncer(debounce_count)
        self._debounce_fan = Debouncer(debounce_count)
        self._debounce_light = Debouncer(debounce_count)

        self._extractor = FeatureExtractor()

        # 缓存特征重要性
        self._feature_importance = {
            "presence": dict(zip(
                self._extractor.get_feature_names("presence"),
                self.presence_model.feature_importances_)),
            "fan": dict(zip(
                self._extractor.get_feature_names("fan"),
                self.fan_model.feature_importances_)),
            "light": dict(zip(
                self._extractor.get_feature_names("light"),
                self.light_model.feature_importances_)),
        }

    # ----------------------------------------------------------
    # 判断是否上课时段
    # ----------------------------------------------------------
    @staticmethod
    def _is_class_time(hour: int, weekday: int) -> bool:
        """工作日上课时段 8:00-12:00 或 14:00-18:00"""
        if weekday >= 5:  # 周末
            return False
        return (8 <= hour < 12) or (14 <= hour < 18)

    # ----------------------------------------------------------
    # 单次比对
    # ----------------------------------------------------------
    def compare(self, window_df: pd.DataFrame, raise_empty: bool = False) -> Optional[CompareResult]:
        """
        对单个窗口执行比对。

        Args:
            window_df: 窗口传感器数据（6条）
            raise_empty: 窗口为空时是否抛异常，默认返回 None

        Returns:
            CompareResult 或 None
        """
        if len(window_df) == 0:
            if raise_empty:
                raise ValueError("窗口数据为空")
            return None

        # 提取特征
        feats = self._extractor.transform(window_df)
        timestamp = str(window_df["Timestamp"].iloc[-1])

        # 真实状态
        real_presence = 1 if window_df["PirStatus"].mean() > 0.5 else 0
        real_fan = int(round(window_df["FanLevel"].mean()))
        real_light = int(round(window_df["LightLevel"].mean()))

        # 模型预测期望状态（按模型过滤特征）
        X_vec = pd.DataFrame([feats])
        expected_presence = int(self.presence_model.predict(
            X_vec[self._extractor.get_feature_names("presence")])[0])
        expected_fan = int(self.fan_model.predict(
            X_vec[self._extractor.get_feature_names("fan")])[0])
        expected_light = int(self.light_model.predict(
            X_vec[self._extractor.get_feature_names("light")])[0])

        # 比对差异
        presence_match = (real_presence == expected_presence)
        fan_deviation = abs(real_fan - expected_fan)
        light_deviation = abs(real_light - expected_light)

        # 防抖
        hour = feats["hour"]
        weekday = feats["weekday"]
        is_class = self._is_class_time(hour, weekday)

        presence_deviated = not presence_match
        fan_deviated = fan_deviation >= 1
        light_deviated = light_deviation >= 1

        presence_trigger = self._debounce_presence.push(presence_deviated)
        fan_trigger = self._debounce_fan.push(fan_deviated)
        light_trigger = self._debounce_light.push(light_deviated)

        # ---- 场景分类 ----
        has_any_deviation = presence_deviated or fan_deviated or light_deviated

        if not has_any_deviation:
            scenario = Scenario.NORMAL
            trigger = False
            action = "无需干预"
            reason = "所有维度基准与真实一致"
        elif real_presence == 0 and expected_presence == 0 and (real_fan > 0 or real_light > 0):
            # 节能场景：无人 + 设备仍运行
            scenario = Scenario.ENERGY_SAVING
            trigger = fan_trigger or light_trigger
            parts = []
            if real_fan > 0:
                parts.append(f"风扇{real_fan}档")
            if real_light > 0:
                parts.append(f"灯光{real_light}档")
            action = "自动关停设备" if trigger else "待确认"
            reason = f"无人但{'、'.join(parts)}仍运行，建议节能关闭"
        elif real_presence == 1 and (fan_deviation >= 1 or light_deviation >= 1):
            # 舒适调节：有人状态，档位滞后
            scenario = Scenario.COMFORT_ADJUST
            trigger = fan_trigger or light_trigger
            parts = []
            if fan_deviation >= 1:
                parts.append(f"风扇(预期{expected_fan}档,实际{real_fan}档)")
            if light_deviation >= 1:
                parts.append(f"灯光(预期{expected_light}档,实际{real_light}档)")
            if trigger:
                action = f"自动调节至预期档位: 风扇{expected_fan}档, 灯光{expected_light}档"
            else:
                action = "待确认"
            reason = f"有人状态，档位滞后: {'; '.join(parts)}"
        elif is_class and real_presence == 1 and expected_presence == 0:
            # 作息异常：上课时段持续有人
            scenario = Scenario.ABNORMAL_SCHEDULE
            trigger = presence_trigger
            action = "标记异常作息" if trigger else "待确认"
            reason = f"工作日上课时段({hour}:00)预期无人，实际有人"
        else:
            scenario = Scenario.NORMAL
            trigger = False
            action = "无需干预"
            reason = "偏差未达触发阈值"

        return CompareResult(
            timestamp=timestamp,
            real_presence=real_presence,
            expected_presence=expected_presence,
            presence_match=presence_match,
            real_fan_level=real_fan,
            expected_fan_level=expected_fan,
            fan_deviation=fan_deviation,
            real_light_level=real_light,
            expected_light_level=expected_light,
            light_deviation=light_deviation,
            scenario=scenario,
            trigger=trigger,
            action=action,
            reason=reason,
        )

    def reset_debounce(self):
        """重置所有防抖缓冲区"""
        self._debounce_presence.reset()
        self._debounce_fan.reset()
        self._debounce_light.reset()

    # ----------------------------------------------------------
    # 批量比对
    # ----------------------------------------------------------
    def compare_batch(
        self,
        df: pd.DataFrame,
        window_size: int = 6,
        stride: int = 2,
    ) -> list[CompareResult]:
        """
        对整张 DataFrame 按滑动窗口批量比对。

        Args:
            df: 完整传感器数据
            window_size: 窗口大小
            stride: 滑动步长

        Returns:
            比对结果列表
        """
        df = df.sort_values("Timestamp").reset_index(drop=True)
        self.reset_debounce()

        results = []
        for i in range(0, len(df) - window_size + 1, stride):
            window_df = df.iloc[i : i + window_size]
            result = self.compare(window_df)
            if result is not None:
                results.append(result)

        return results

    # ----------------------------------------------------------
    # 标准化大模型输入
    # ----------------------------------------------------------
    def _get_top_features(self, model_type: str, n: int = 3) -> list[str]:
        """取指定模型 Top-N 特征名"""
        imp = self._feature_importance.get(model_type, {})
        return sorted(imp, key=imp.get, reverse=True)[:n]

    def build_llm_input(self, window_df: pd.DataFrame, result: CompareResult) -> dict:
        """
        构建标准化大模型输入结构体。

        Args:
            window_df:  窗口传感器数据
            result:     比对结果 (CompareResult)

        Returns:
            {
                "time": str,
                "is_weekend": int,
                "env": {"temp": float, "humidity": float, "light": float},
                "real_status": {"presence": int, "fan": int, "light": int},
                "baseline_status": {"presence": int, "fan": int, "light": int},
                "compare_result": str,
                "top_features": [str, str, str],
            }
        """
        feats = self._extractor.transform(window_df)

        # 场景 → 模型类型映射
        scenario_model_map = {
            Scenario.NORMAL: "presence",
            Scenario.ENERGY_SAVING: "fan",
            Scenario.COMFORT_ADJUST: "fan",
            Scenario.ABNORMAL_SCHEDULE: "presence",
        }
        model_type = scenario_model_map.get(result.scenario, "presence")

        return {
            "time": result.timestamp,
            "is_weekend": feats["is_weekend"],
            "env": {
                "temp": round(feats["temp_mean"], 1),
                "humidity": round(feats["humidity_mean"], 1),
                "light": round(feats["light_mean"], 1),
            },
            "real_status": {
                "presence": result.real_presence,
                "fan": result.real_fan_level,
                "light": result.real_light_level,
            },
            "baseline_status": {
                "presence": result.expected_presence,
                "fan": result.expected_fan_level,
                "light": result.expected_light_level,
            },
            "compare_result": result.reason,
            "top_features": self._get_top_features(model_type),
        }


# ============================================================
# 自测
# ============================================================
if __name__ == "__main__":
    from dataset_builder import build_dataset

    df = pd.read_csv("data/sensor_data_week.csv")
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])

    comp = BehaviorComparator(
        "web/behavior_presence.pkl",
        "web/behavior_fan.pkl",
        "web/behavior_light.pkl",
        debounce_count=1,
    )

    results = comp.compare_batch(df, window_size=6, stride=2)

    from collections import Counter
    scenario_counts = Counter(r.scenario for r in results)
    trigger_count = sum(1 for r in results if r.trigger)

    print(f"总窗口数: {len(results)}")
    print(f"触发控制/提醒: {trigger_count}")
    print(f"场景分布: {dict(scenario_counts)}")

    # 打印标准化 LLM 输入示例
    print("\n=== 标准化 LLM 输入示例 ===")
    triggered = [r for r in results if r.trigger]
    for r in triggered[:3]:
        # 重建窗口数据
        ts = pd.to_datetime(r.timestamp)
        window = df.iloc[max(0, df[df["Timestamp"] == ts].index[0] - 5):df[df["Timestamp"] == ts].index[0] + 1]
        if len(window) < 6:
            window = df.iloc[max(0, df[df["Timestamp"] == ts].index[0]):df[df["Timestamp"] == ts].index[0] + 6]
        llm_input = comp.build_llm_input(window, r)
        import json
        print(json.dumps(llm_input, ensure_ascii=False, indent=2))
        print("---")
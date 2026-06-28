# train_rf.py - 用户行为模型训练器
# 三个 RandomForestClassifier，学习用户设备使用习惯
# 目标：生成 expected_fan_level / expected_light_level / expected_presence（期望状态）
# 均衡分割 + 交叉验证，保存 behavior_*.pkl，输出评估指标

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix
)
from sklearn.model_selection import cross_val_score, train_test_split
import joblib

from .dataset_builder import build_dataset
from .feature_engine import FeatureExtractor

# 统一超参数
RF_PARAMS = {
    "n_estimators": 250,
    "max_depth": 14,
    "min_samples_split": 2,
    "class_weight": "balanced",
    "random_state": 42,
    "n_jobs": -1,
}

extractor = FeatureExtractor()


def _print_metrics(y_true, y_pred, model_name, class_names=None):
    """统一输出分类指标"""
    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, average="weighted", zero_division=0)
    rec = recall_score(y_true, y_pred, average="weighted", zero_division=0)
    f1 = f1_score(y_true, y_pred, average="weighted", zero_division=0)

    print(f"[{model_name}] Acc={acc:.4f}  Prec={prec:.4f}  Recall={rec:.4f}  F1={f1:.4f}")
    print(f"分类报告:\n{classification_report(y_true, y_pred, target_names=class_names, zero_division=0)}")
    print(f"混淆矩阵:\n{confusion_matrix(y_true, y_pred)}")
    return acc, f1


def _print_feature_importance(model, feature_names, top_n=5):
    """打印特征重要性 Top N"""
    print(f"\n--- 特征重要性 Top {top_n} ---")
    importances = sorted(
        zip(feature_names, model.feature_importances_),
        key=lambda x: x[1], reverse=True
    )
    for feat, imp in importances[:top_n]:
        print(f"  {feat}: {imp:.4f}")
    return importances


def train_and_evaluate():
    # ========== 1. 加载数据（stride=2 减少重复）==========
    X, y_fan, y_light, y_presence = build_dataset("data/sensor_data_week.csv", window_size=6, stride=2)
    print(f"数据集: {X.shape[0]} 样本, {X.shape[1]} 特征\n")

    # ========== 2. 周末/工作日均衡分割 ==========
    # 按 is_weekend 分层，确保训练/测试集周末比例一致
    X_train, X_test, y_f_train, y_f_test, y_l_train, y_l_test, y_p_train, y_p_test = \
        train_test_split(
            X, y_fan, y_light, y_presence,
            test_size=0.2,
            stratify=X["is_weekend"],
            random_state=42,
        )

    print(f"均衡分割: 训练集 {len(X_train)} / 测试集 {len(X_test)}")
    print(f"  训练集周末比例: {X_train['is_weekend'].mean():.3f}")
    print(f"  测试集周末比例: {X_test['is_weekend'].mean():.3f}\n")

    feature_names = X.columns.tolist()
    feature_names_presence = extractor.get_feature_names("presence")
    feature_names_fan = extractor.get_feature_names("fan")
    feature_names_light = extractor.get_feature_names("light")

    # ========== 3. 训练 behavior_presence（二分类：不含 pir_ratio/fan_mean/light_level_mean）==========
    print("=" * 50)
    print("训练 behavior_presence（期望有人/无人，排除 pir_ratio/fan_mean/light_level_mean）")
    print("=" * 50)
    behavior_presence = RandomForestClassifier(**RF_PARAMS)
    behavior_presence.fit(X_train[feature_names_presence], y_p_train)

    cv_scores = cross_val_score(behavior_presence, X_train[feature_names_presence], y_p_train, cv=5, scoring="f1_weighted")
    print(f"5折交叉验证 F1: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")

    y_p_pred = behavior_presence.predict(X_test[feature_names_presence])
    acc_p, f1_p = _print_metrics(y_p_test, y_p_pred, "behavior_presence", class_names=["无人", "有人"])
    p_importances = _print_feature_importance(behavior_presence, feature_names_presence)

    # ========== 4. 训练 behavior_fan（4分类：期望风扇档位，排除 fan_mean）==========
    print("\n" + "=" * 50)
    print("训练 behavior_fan（期望风扇档位 0/1/2/3，排除 fan_mean）")
    print("=" * 50)
    behavior_fan = RandomForestClassifier(**RF_PARAMS)
    behavior_fan.fit(X_train[feature_names_fan], y_f_train)

    cv_scores = cross_val_score(behavior_fan, X_train[feature_names_fan], y_f_train, cv=5, scoring="f1_weighted")
    print(f"5折交叉验证 F1: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")

    y_f_pred = behavior_fan.predict(X_test[feature_names_fan])
    acc_f, f1_f = _print_metrics(y_f_test, y_f_pred, "behavior_fan", class_names=["关", "低档", "中档", "高档"])
    f_importances = _print_feature_importance(behavior_fan, feature_names_fan)

    # ========== 5. 训练 behavior_light（4分类：期望灯光档位，排除 light_level_mean）==========
    print("\n" + "=" * 50)
    print("训练 behavior_light（期望灯光档位 0/1/2/3，排除 light_level_mean）")
    print("=" * 50)
    behavior_light = RandomForestClassifier(**RF_PARAMS)
    behavior_light.fit(X_train[feature_names_light], y_l_train)

    cv_scores = cross_val_score(behavior_light, X_train[feature_names_light], y_l_train, cv=5, scoring="f1_weighted")
    print(f"5折交叉验证 F1: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")

    y_l_pred = behavior_light.predict(X_test[feature_names_light])
    acc_l, f1_l = _print_metrics(y_l_test, y_l_pred, "behavior_light", class_names=["0档", "1档", "2档", "3档"])
    l_importances = _print_feature_importance(behavior_light, feature_names_light)

    # ========== 6. 保存行为模型 ==========
    import os
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    joblib.dump(behavior_presence, os.path.join(base_dir, "models", "behavior_presence.pkl"))
    joblib.dump(behavior_fan, os.path.join(base_dir, "models", "behavior_fan.pkl"))
    joblib.dump(behavior_light, os.path.join(base_dir, "models", "behavior_light.pkl"))
    print("\n用户习惯模型已保存到 models/ 目录")
    print("说明：以上模型用于生成期望状态，非预测未来时刻")

    # ========== 7. 用户习惯模型特征权重汇总（对接大模型）==========
    print("\n" + "=" * 50)
    print("用户习惯模型 - 特征权重汇总（对接大模型）")
    print("=" * 50)
    print(f"\n[behavior_presence] 期望有人/无人  Acc={acc_p:.4f}  F1={f1_p:.4f}")
    print(f"  Top3: {', '.join(f'{f}({i:.3f})' for f, i in p_importances[:3])}")

    print(f"\n[behavior_fan] 期望风扇档位  Acc={acc_f:.4f}  F1={f1_f:.4f}")
    print(f"  Top3: {', '.join(f'{f}({i:.3f})' for f, i in f_importances[:3])}")

    print(f"\n[behavior_light] 期望灯光档位  Acc={acc_l:.4f}  F1={f1_l:.4f}")
    print(f"  Top3: {', '.join(f'{f}({i:.3f})' for f, i in l_importances[:3])}")


if __name__ == "__main__":
    train_and_evaluate()
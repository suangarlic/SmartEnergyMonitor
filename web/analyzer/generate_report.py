import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import joblib
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split

from analyzer.dataset_builder import build_dataset
from analyzer.feature_engine import FeatureExtractor


def load_models():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    models = {
        'behavior_presence': joblib.load(os.path.join(base_dir, 'models', 'behavior_presence.pkl')),
        'behavior_fan': joblib.load(os.path.join(base_dir, 'models', 'behavior_fan.pkl')),
        'behavior_light': joblib.load(os.path.join(base_dir, 'models', 'behavior_light.pkl'))
    }
    return models


def evaluate_models(models, X_test, y_tests, feature_names_dict):
    results = {}
    
    for model_name, model in models.items():
        y_test = y_tests[model_name]
        feature_names = feature_names_dict[model_name]
        
        y_pred = model.predict(X_test[feature_names])
        acc = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
        
        importances = sorted(
            zip(feature_names, model.feature_importances_),
            key=lambda x: x[1], reverse=True
        )
        
        results[model_name] = {
            'accuracy': acc,
            'f1': f1,
            'top_features': importances[:3]
        }
    
    return results


def generate_report(results):
    report = """# RandomForest 模型评估总结报告

---

## 一、模型性能概览

| 模型名称 | 功能描述 | Accuracy | F1 Score |
|---------|---------|----------|----------|
| behavior_presence | 预测期望有人/无人 | {presence_acc:.4f} | {presence_f1:.4f} |
| behavior_fan | 预测期望风扇档位 | {fan_acc:.4f} | {fan_f1:.4f} |
| behavior_light | 预测期望灯光档位 | {light_acc:.4f} | {light_f1:.4f} |

---

## 二、特征重要性分析

### 2.1 behavior_presence（有人/无人检测）

**Top3 重要特征：**

| 特征名称 | 重要性权重 | 特征解释 |
|---------|-----------|---------|
| {p1_name} | {p1_val:.4f} | {p1_desc} |
| {p2_name} | {p2_val:.4f} | {p2_desc} |
| {p3_name} | {p3_val:.4f} | {p3_desc} |

**行为规律总结：**
{p_rule}

---

### 2.2 behavior_fan（风扇档位预测）

**Top3 重要特征：**

| 特征名称 | 重要性权重 | 特征解释 |
|---------|-----------|---------|
| {f1_name} | {f1_val:.4f} | {f1_desc} |
| {f2_name} | {f2_val:.4f} | {f2_desc} |
| {f3_name} | {f3_val:.4f} | {f3_desc} |

**行为规律总结：**
{f_rule}

---

### 2.3 behavior_light（灯光档位预测）

**Top3 重要特征：**

| 特征名称 | 重要性权重 | 特征解释 |
|---------|-----------|---------|
| {l1_name} | {l1_val:.4f} | {l1_desc} |
| {l2_name} | {l2_val:.4f} | {l2_desc} |
| {l3_name} | {l3_val:.4f} | {l3_desc} |

**行为规律总结：**
{l_rule}

---

## 三、模型应用价值

1. **行为识别**：通过 presence 模型准确判断宿舍是否有人，为后续智能控制提供基础
2. **习惯学习**：风扇和灯光模型学习用户使用习惯，生成期望状态
3. **节能优化**：结合实时检测与期望状态对比，识别异常用电行为，实现智能节能

---

*报告生成时间：自动生成*
"""
    
    feature_desc = {
        'temp_mean': '平均温度',
        'humidity_mean': '平均湿度',
        'light_mean': '环境光强度均值',
        'hour': '当前时刻（小时）',
        'hour_sin': '时间正弦编码',
        'hour_cos': '时间余弦编码',
        'weekday': '周几（0=周一）',
        'is_weekend': '是否周末',
        'pir_ratio': 'PIR人体感应触发比例',
        'fan_mean': '历史风扇档位均值',
        'light_level_mean': '历史灯光档位均值'
    }
    
    p_features = results['behavior_presence']['top_features']
    f_features = results['behavior_fan']['top_features']
    l_features = results['behavior_light']['top_features']
    
    p_rule = "模型主要通过时间特征（小时、周末）和环境光强度来判断用户是否在宿舍，学习到用户的日常作息规律。"
    f_rule = "模型发现温度是影响风扇使用的最关键因素，同时结合时间规律和历史使用习惯，预测用户期望的风扇档位。"
    l_rule = "环境光强度和时间是决定灯光档位的核心因素，模型学习到用户在不同时段和光照条件下的开灯习惯。"
    
    report = report.format(
        presence_acc=results['behavior_presence']['accuracy'],
        presence_f1=results['behavior_presence']['f1'],
        fan_acc=results['behavior_fan']['accuracy'],
        fan_f1=results['behavior_fan']['f1'],
        light_acc=results['behavior_light']['accuracy'],
        light_f1=results['behavior_light']['f1'],
        
        p1_name=p_features[0][0], p1_val=p_features[0][1], p1_desc=feature_desc.get(p_features[0][0], p_features[0][0]),
        p2_name=p_features[1][0], p2_val=p_features[1][1], p2_desc=feature_desc.get(p_features[1][0], p_features[1][0]),
        p3_name=p_features[2][0], p3_val=p_features[2][1], p3_desc=feature_desc.get(p_features[2][0], p_features[2][0]),
        p_rule=p_rule,
        
        f1_name=f_features[0][0], f1_val=f_features[0][1], f1_desc=feature_desc.get(f_features[0][0], f_features[0][0]),
        f2_name=f_features[1][0], f2_val=f_features[1][1], f2_desc=feature_desc.get(f_features[1][0], f_features[1][0]),
        f3_name=f_features[2][0], f3_val=f_features[2][1], f3_desc=feature_desc.get(f_features[2][0], f_features[2][0]),
        f_rule=f_rule,
        
        l1_name=l_features[0][0], l1_val=l_features[0][1], l1_desc=feature_desc.get(l_features[0][0], l_features[0][0]),
        l2_name=l_features[1][0], l2_val=l_features[1][1], l2_desc=feature_desc.get(l_features[1][0], l_features[1][0]),
        l3_name=l_features[2][0], l3_val=l_features[2][1], l3_desc=feature_desc.get(l_features[2][0], l_features[2][0]),
        l_rule=l_rule
    )
    
    return report


def main():
    print('加载数据集...')
    X, y_fan, y_light, y_presence = build_dataset('data/sensor_data_week.csv', window_size=6, stride=2)
    
    X_train, X_test, y_f_train, y_f_test, y_l_train, y_l_test, y_p_train, y_p_test = \
        train_test_split(X, y_fan, y_light, y_presence,
                        test_size=0.2,
                        stratify=X['is_weekend'],
                        random_state=42)
    
    extractor = FeatureExtractor()
    feature_names_dict = {
        'behavior_presence': extractor.get_feature_names('presence'),
        'behavior_fan': extractor.get_feature_names('fan'),
        'behavior_light': extractor.get_feature_names('light')
    }
    
    y_tests = {
        'behavior_presence': y_p_test,
        'behavior_fan': y_f_test,
        'behavior_light': y_l_test
    }
    
    print('加载模型...')
    models = load_models()
    
    print('评估模型...')
    results = evaluate_models(models, X_test, y_tests, feature_names_dict)
    
    print('生成报告...')
    report = generate_report(results)
    
    report_path = 'model_evaluation_report.md'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f'报告已保存到 {report_path}')
    print('\n' + '='*60)
    print(report)


if __name__ == '__main__':
    main()
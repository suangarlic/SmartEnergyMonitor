import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import joblib
import os

from sklearn.metrics import accuracy_score, f1_score, confusion_matrix
from sklearn.model_selection import train_test_split

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analyzer.dataset_builder import build_dataset
from analyzer.feature_engine import FeatureExtractor

plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


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
        
        results[model_name] = {
            'accuracy': acc,
            'f1': f1,
            'y_true': y_test,
            'y_pred': y_pred
        }
    
    return results


def plot_accuracy_f1(results):
    model_names = ['behavior_presence', 'behavior_fan', 'behavior_light']
    model_labels = ['有人/无人', '风扇档位', '灯光档位']
    
    accuracies = [results[m]['accuracy'] for m in model_names]
    f1_scores = [results[m]['f1'] for m in model_names]
    
    x = np.arange(len(model_names))
    width = 0.35
    
    fig, ax = plt.subplots(figsize=(10, 6))
    rects1 = ax.bar(x - width/2, accuracies, width, label='Accuracy')
    rects2 = ax.bar(x + width/2, f1_scores, width, label='F1 Score')
    
    ax.set_xlabel('模型类型', fontsize=12)
    ax.set_ylabel('分数', fontsize=12)
    ax.set_title('RandomForest模型 Accuracy vs F1 对比', fontsize=14)
    ax.set_xticks(x)
    ax.set_xticklabels(model_labels, fontsize=10)
    ax.legend()
    
    ax.set_ylim(0, 1.1)
    
    for rect in rects1:
        height = rect.get_height()
        ax.text(rect.get_x() + rect.get_width()/2., height,
                f'{height:.4f}', ha='center', va='bottom', fontsize=10)
    
    for rect in rects2:
        height = rect.get_height()
        ax.text(rect.get_x() + rect.get_width()/2., height,
                f'{height:.4f}', ha='center', va='bottom', fontsize=10)
    
    fig.tight_layout()
    plt.savefig('accuracy_f1_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    print('已保存: accuracy_f1_comparison.png')


def plot_confusion_matrix(results, model_name, class_names):
    y_true = results[model_name]['y_true']
    y_pred = results[model_name]['y_pred']
    
    cm = confusion_matrix(y_true, y_pred)
    
    fig, ax = plt.subplots(figsize=(8, 6))
    im = ax.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
    ax.figure.colorbar(im, ax=ax)
    
    ax.set(xticks=np.arange(cm.shape[1]),
           yticks=np.arange(cm.shape[0]),
           xticklabels=class_names,
           yticklabels=class_names,
           title=f'{model_name} 混淆矩阵',
           ylabel='真实标签',
           xlabel='预测标签')
    
    plt.setp(ax.get_xticklabels(), rotation=45, ha='right', rotation_mode='anchor')
    
    fmt = 'd'
    thresh = cm.max() / 2.
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, format(cm[i, j], fmt),
                    ha='center', va='center',
                    color='white' if cm[i, j] > thresh else 'black')
    
    fig.tight_layout()
    plt.savefig(f'{model_name}_confusion_matrix.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f'已保存: {model_name}_confusion_matrix.png')


def plot_feature_importance(models, feature_names_dict):
    for model_name, model in models.items():
        feature_names = feature_names_dict[model_name]
        importances = model.feature_importances_
        
        indices = np.argsort(importances)[::-1][:5]
        top_features = [feature_names[i] for i in indices]
        top_importances = importances[indices]
        
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(top_features, top_importances)
        
        ax.set_xlabel('特征名称', fontsize=12)
        ax.set_ylabel('特征重要性', fontsize=12)
        ax.set_title(f'{model_name} Top5 特征重要性', fontsize=14)
        ax.tick_params(axis='x', rotation=45)
        
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.4f}', ha='center', va='bottom', fontsize=10)
        
        fig.tight_layout()
        plt.savefig(f'{model_name}_feature_importance.png', dpi=300, bbox_inches='tight')
        plt.close()
        print(f'已保存: {model_name}_feature_importance.png')


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
    
    print('生成 Accuracy/F1 对比图...')
    plot_accuracy_f1(results)
    
    print('选择表现最好的模型生成混淆矩阵...')
    best_model = max(results.keys(), key=lambda m: results[m]['f1'])
    print(f'表现最好的模型: {best_model} (F1={results[best_model]["f1"]:.4f})')
    
    class_names_dict = {
        'behavior_presence': ['无人', '有人'],
        'behavior_fan': ['关', '低档', '中档', '高档'],
        'behavior_light': ['0档', '1档', '2档', '3档']
    }
    plot_confusion_matrix(results, best_model, class_names_dict[best_model])
    
    print('生成特征重要性图...')
    plot_feature_importance(models, feature_names_dict)
    
    print('\n所有可视化图已生成完成！')


if __name__ == '__main__':
    main()
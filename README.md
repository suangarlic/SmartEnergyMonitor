# SmartEnergyMonitor

## 项目简介
智能节能减排监测系统 - 基于行空板的物联网能耗监测与控制平台

## 功能特性
- 实时传感器数据监测（温度、湿度、光照、人体红外）
- 设备智能控制（风扇、小灯多档位调节）
- AI节能建议系统
- 无人状态自动提醒和设备关闭
- 能耗统计和分析
- 实时数据可视化

## 技术栈
- **硬件端**: Python + 行空板SDK
- **Web端**: Python + Flask + JavaScript
- **数据库**: SQLite
- **前端框架**: TailwindCSS + Chart.js

## 快速开始

### 硬件端启动
```bash
cd hardware
python main.py
```

### Web端启动
```bash
cd web
python app.py
```

访问Web界面: http://localhost:8080

## 项目结构
- hardware/: 行空板端传感器采集和设备控制程序
- web/: Flask Web应用和前端界面

## 作者
计算机应用能力大赛项目——固态硬盘组

# AI_API.py - 负责将 data.json 发送至 DeepSeek，并返回分析结果
import json
import requests
import os

class AIAnalyzer:
    def __init__(self):
        # DeepSeek API地址
        self.api_url = "https://api.deepseek.com/v1/chat/completions"

        # API KEY（必须配置：export DEEPSEEK_API_KEY=xxxx）
        self.api_key = os.getenv("DEEPSEEK_API_KEY", "sk-2296ee817f5c4135a59d2ecb13cf42c7")

    def load_data(self, path="data.json"):
        """读取最近一小时的传感器数据"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []

    def send_to_ai(self, recent_records):
        """将记录发送到 DeepSeek 进行能耗分析"""

        prompt = f"""
你是一名智能家居节能管家，需要输出格式化、可被前端直接展示的节能建议。

【必须严格按以下格式输出】：
每条建议格式如下（多条建议用空行分隔）：

标题：xxxx
描述：xxxx（2～3 行，简洁）
预计节电：0.xx 度/天
状态：已生效 或 推荐开启

【输出要求】
- 建议必须为多条，不少于 2 条，不超过 6 条
- “标题”必须为一句话总结
- “描述”不超过 50 字，语言像智能管家
- “预计节电”必须提供数值（根据数据合理推算）
- “状态”只能是：“已生效” 或 “推荐开启”
- 所有建议必须按以下 4 个字段输出：标题、描述、预计节电、状态
- 每条建议之间必须用一个空行分隔（前端将自动分段）

【分析要求】
1. 基于传感器数据分析风扇、小灯的耗能情况（功率 + 挡位）
2. 分析光照亮度 > 500lux 时开灯是否浪费
3. 分析温度较低时开风扇是否浪费
4. 根据用户作息（工作日：8-11，13-17 上课；23-8 睡觉）判断是否有人在但电器保持开启导致浪费
5. 给出最有效的节能提醒或自动化建议

【提供的数据】
{json.dumps(recent_records, ensure_ascii=False)}
"""
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        response = requests.post(self.api_url, headers=headers, json=payload)

        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]

        return f"[AI ERROR] {response.text}"

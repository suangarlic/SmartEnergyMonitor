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
你是智能家居节能管家，请根据用户近期的传感器历史数据，分析用户真实行为习惯，输出可直接前端展示的标准化节能建议。

【输出格式】
每条建议必须包含：
标题：一句话总结
描述：2–3行，简洁自然，像管家提醒（≤50字）
预计节电：0.xx 度/天
状态：已生效 / 建议按照建议调整 / 需要用户确认
状态字段说明：
- 已生效：建议已生效，无需用户确认。
- 建议按照建议调整：建议需要用户确认，用户确认后生效。
- 需要用户确认：建议需要用户确认，用户确认后生效。

多条建议之间用空行分隔，总数2–6条。

【分析规则——基于用户行为习惯，而非固定阈值】
【分析要求】
1. 基于历史数据自动分析用户使用习惯（光照、温度、时间、功率、挡位等）
2. 识别用户作息规律（工作日、周末、白天、夜间）
3. 分析电器使用模式（风扇、小灯的开关和挡位变化）
4. 找出节能优化点（不必要的开启、过高的挡位、不合理的时段使用）
5. 给出个性化的节能建议（基于实际数据，不使用固定阈值）
6. 【重要】请使用纯文本格式，不要使用Markdown格式符号（如**、##等），直接输出可读的文本内容。
7. 【重要】分析时间时要注意时间顺序，同时要加上年月日，确保开始时间早于结束时间。

【禁止使用固定阈值】
不准使用“光照>500lux”“温度>25℃”这类固定判断，必须从历史数据中总结用户习惯。
 
【数据格式说明】
数据采用精简的横向键值对格式（不换行）：{{"l":500,"h":60,"t":25,"p":1,"pf":5.2,"lf":2,"pl":3.7,"ll":1,"tm":"12:00","ca":"2023-10-01 10:30:00"}}
 
【数据字段说明】
【数据字段说明】（精简字段名）
- l: 光照(lux)
- h: 湿度(%)
- t: 温度(℃)
- p: PIR状态(1=有人,0=无人)
- pf: 风扇功率(W)
- lf: 风扇挡位(0-3)
- pl: 小灯功率(W)
- ll: 小灯挡位(0-3)
- tm: 设备时间戳
- ca: 数据采集时间
 
【提供的数据】
{json.dumps(recent_records, separators=(',', ':'))}
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

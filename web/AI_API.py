# AI_API.py - 负责将数据发送至 DeepSeek，并返回分析结果
import json
import requests
import os
from dotenv import load_dotenv

# 加载 .env 文件
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(env_path)

# 模拟建议库 - 当API不可用时使用
SIMULATED_ADVICES = [
    {
        "title": "智能节能模式已启用",
        "description": "系统根据您的使用习惯自动调整设备，兼顾舒适与节能",
        "saving": "0.85",
        "status": "已生效"
    },
    {
        "title": "夜间自动关闭",
        "description": "检测到深夜无人时自动关闭设备，预计节省电量",
        "saving": "0.32",
        "status": "已生效"
    },
    {
        "title": "智能挡位调节",
        "description": "根据环境光线自动调节灯光亮度",
        "saving": "0.15",
        "status": "已生效"
    }
]

SIMULATED_EXPLANATIONS = [
    "检测到您已离开，已自动关闭设备以节省能源",
    "根据您的使用习惯，已调整风扇至舒适挡位",
    "环境光线充足，已自动调低灯光亮度",
    "检测到有人活动，已自动开启设备",
    "一切正常，设备运行符合您的使用习惯",
    "已根据环境温度调整风扇挡位，兼顾舒适与节能"
]


class AIAnalyzer:
    def __init__(self):
        # 从环境变量读取配置
        self.api_url = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/chat/completions")
        self.api_key = os.getenv("DEEPSEEK_API_KEY", "")
        self.model = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")
        # 是否启用模拟模式（无API时自动启用）
        self.use_simulation = os.getenv("USE_SIMULATION", "false").lower() == "true"
        
        # 验证配置 - 如果没有API密钥或启用模拟模式，则使用模拟数据
        if not self.api_key:
            print("[AI] 警告：DEEPSEEK_API_KEY 未设置，将使用模拟模式")
            self.use_simulation = True
        
        if self.use_simulation:
            print("[AI] 模拟模式已启用")


    def send_to_ai(self, recent_records):
        """将记录发送到 DeepSeek 进行能耗分析"""
        
        # 模拟模式：返回预设的节能建议
        if self.use_simulation:
            return self._generate_simulated_advice()

        prompt = f"""
你是智能家居节能管家，请根据用户近期的传感器历史数据，分析用户真实行为习惯，输出可直接前端展示的标准化节能建议。

【输出格式】
每条建议必须包含：
标题：一句话总结
描述：2–3行，简洁自然，像管家提醒（≤50字）
预计节电：0.xx 度/天
预计节约电费：xx元（按照每度电费0.618元进行结算）
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
不准使用"光照>500lux""温度>25℃"这类固定判断，必须从历史数据中总结用户习惯。
 
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

        return self._call_api(prompt)

    def explain_behavior(self, llm_input: dict) -> str:
        """
        将行为分析结果发送给大模型，生成简洁的控制解释。

        Args:
            llm_input: build_llm_input() 输出的标准化 dict

        Returns:
            ≤40 字自然语言解释
        """
        
        # 模拟模式：返回预设的解释
        if self.use_simulation:
            return self._generate_simulated_explanation(llm_input)

        prompt = f"""角色：智能宿舍节能管家
任务：根据下方分析结果，生成一句设备状态/调整提醒
要求：
1. 严格40字以内，口语化，温和像管家提醒
2. 必须以「环境和用户使用习惯」为依据，不能凭空建议，突出对用户历史行为分析
3. 所有调整突出「兼顾舒适体验与节能降耗」，不只谈节能
4. 正常场景点明符合习惯，偏差场景说明动作与价值

【分析数据】
{json.dumps(llm_input, ensure_ascii=False, indent=2)}
"""
        return self._call_api(prompt)
    
    def _generate_simulated_advice(self):
        """生成模拟的节能建议"""
        advice_text = ""
        for advice in SIMULATED_ADVICES:
            advice_text += f"标题：{advice['title']}\n"
            advice_text += f"描述：{advice['description']}\n"
            advice_text += f"预计节电：{advice['saving']} 度/天\n"
            advice_text += f"状态：{advice['status']}\n\n"
        return advice_text.strip()
    
    def _generate_simulated_explanation(self, llm_input: dict) -> str:
        """根据场景生成模拟的行为解释"""
        import random
        
        scenario = llm_input.get("scenario", "normal")
        trigger = llm_input.get("trigger", False)
        
        if scenario == "energy_saving" and trigger:
            return "检测到无人状态，已自动关闭设备以节省能源"
        elif scenario == "comfort_adjust" and trigger:
            real_fan = llm_input.get("real_status", {}).get("fan", 0)
            target_fan = llm_input.get("baseline_status", {}).get("fan", 0)
            if real_fan > target_fan:
                return f"风扇从{real_fan}档降至{target_fan}档，兼顾舒适与节能"
            elif real_fan < target_fan:
                return f"风扇从{real_fan}档升至{target_fan}档，提升舒适度"
            return "已根据您的使用习惯调整设备挡位"
        elif scenario == "normal":
            return "一切正常，设备运行符合您的使用习惯"
        else:
            return random.choice(SIMULATED_EXPLANATIONS)

    def _call_api(self, prompt: str) -> str:
        """通用 API 调用"""
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            
            # 处理API错误
            error_msg = f"API调用失败 ({response.status_code})"
            print(f"[AI ERROR] {response.text}")
            
            # 判断是否是余额不足错误
            try:
                error_data = response.json()
                if error_data.get("error", {}).get("message") == "Insufficient Balance":
                    print("[AI] 检测到API余额不足，建议切换到模拟模式")
                    return "API服务暂时不可用，系统已切换到本地模式"
            except:
                pass
            
            return f"[AI ERROR] {error_msg}"
            
        except requests.exceptions.RequestException as e:
            print(f"[AI ERROR] 请求异常: {e}")
            return f"[AI ERROR] 请求异常: {str(e)}"
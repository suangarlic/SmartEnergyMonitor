# web/services/ai_service.py
from AI_API import AIAnalyzer
import os
import time


class AIService:
    @staticmethod
    def run_ai_analysis():
        """执行AI分析（三层架构：只做AI查询）"""
        from data.sensor_repository import get_ai_data
        
        # 尝试查询不同时间范围的数据，确保有足够的数据
        recent_records = get_ai_data(limit=400)
        
        
        analyzer = AIAnalyzer()
        result = analyzer.send_to_ai(recent_records)
        
        with open("advice.txt", "w", encoding="utf-8") as f:
            f.write(result)
        
        print("AI分析完成，建议已保存到advice.txt")
        return {"success": True, "msg": "AI分析完成", "advice": result}
    
    @staticmethod
    def get_ai_advice():
        """获取AI建议内容"""
        try:
            advice_content = ""
            advice_mtime = None
            advice_ts = "--"
            if os.path.exists("advice.txt"):
                with open("advice.txt", 'r', encoding='utf-8') as f:
                    advice_content = f.read()
                advice_mtime = os.path.getmtime("advice.txt")
                advice_ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(advice_mtime))
            
            return {
                "success": True,
                "content": advice_content,
                "mtime": advice_mtime,
                "timestamp": advice_ts
            }
        except Exception as e:
            print(f"读取advice.txt失败: {e}")
            return {"success": False, "error": str(e)}

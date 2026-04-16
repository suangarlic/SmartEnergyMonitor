# web/controllers/ai_controller.py
from flask import jsonify
from services.ai_service import AIService

class AIController:
    @staticmethod
    def get_ai_advice():
        """获取AI建议"""
        result = AIService.get_ai_advice()
        if result.get("success"):
            return jsonify(result)
        return jsonify(result), 500
    
    @staticmethod
    def run_ai():
        """执行AI分析"""
        result = AIService.run_ai_analysis()
        if result.get("success"):
            return jsonify(result)
        return jsonify(result), 400
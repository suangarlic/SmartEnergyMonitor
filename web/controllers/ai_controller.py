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
    
    @staticmethod
    def get_ai_status():
        """获取AI状态（包含行为分析自动控制结果和开关状态）"""
        import sys
        from services.behavior_service import BehaviorAnalysisService
        status = BehaviorAnalysisService().control_status
        # 从 app.py 全局变量获取开关状态
        main_mod = sys.modules.get('__main__')
        if main_mod and hasattr(main_mod, 'auto_control_enabled'):
            status["auto_control_enabled"] = main_mod.auto_control_enabled
        else:
            status["auto_control_enabled"] = False
        print(f"[DEBUG] API /api/get_ai_status 返回: {status}")
        return jsonify({"success": True, "data": status})
    
    @staticmethod
    def trigger_ai_analysis():
        """触发AI分析 - 事件驱动型调度"""
        from flask import request
        sensor_data = request.get_json()
        if not sensor_data:
            return jsonify({"success": False, "error": "缺少传感器数据"}), 400
        return AIController.run_ai()

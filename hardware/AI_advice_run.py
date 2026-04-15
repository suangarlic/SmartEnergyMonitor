# AI_advice_run.py
# 合并 advice.py + run_ai.py
# 功能：读取 data.json → 调用 AI_API → 保存节能建议 → 自动上传到后端

from AI_API import AIAnalyzer
import json
import requests
from config import UPLOAD_ADVICE_URL  # 导入配置


# ================================
#     建 议 存 储 模 块
# ================================
def save_advice(text, file="advice.txt"):
    """保存 AI 的节能建议"""
    with open(file, "w", encoding="utf-8") as f:
        f.write(text)


# ================================
#     上 传 到 后 端
# ================================
def upload_advice_to_backend(file="advice.txt"):
    """将 advice.txt 上传到后端服务器"""

    backend_url = UPLOAD_ADVICE_URL   # ← 你只需要改这里

    try:
        with open(file, "rb") as f:
            files = {
                "file": (file, f, "text/plain")
            }
            resp = requests.post(backend_url, files=files, timeout=5)

        print("\n=== AI 建议已成功上传到后端 ===")
        print("后端返回：", resp.text)

    except Exception as e:
        print("\n!!! 上传 AI 建议失败，请检查后端是否运行中。")
        print("错误信息：", e)


# ================================
#          主 逻 辑
# ================================
if __name__ == "__main__":
    analyzer = AIAnalyzer()

    print("正在读取 data.json ...")
    data = analyzer.load_data()

    print(f"共读取 {len(data)} 条最近 24 小时数据，正在提交给 DeepSeek 分析...")
    result = analyzer.send_to_ai(data)

    print("\nAI 分析完成，正在保存到 advice.txt ...")
    save_advice(result)

    print("DeepSeek 生成节能建议成功！")
    print("结果已保存到 advice.txt\n")

    print("正在将 AI 建议上传到后端 ...")
    upload_advice_to_backend()

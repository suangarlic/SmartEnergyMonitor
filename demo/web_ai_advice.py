# web_api.py
from flask import Flask, jsonify, make_response
import os
import time

app = Flask(__name__)

ADVICE_FILE = "advice.txt"

def read_advice():
    """读取 advice.txt，返回文本与最后修改时间"""
    if not os.path.exists(ADVICE_FILE):
        return "", None
    try:
        with open(ADVICE_FILE, "r", encoding="utf-8") as f:
            text = f.read()
        mtime = os.path.getmtime(ADVICE_FILE)
        # 返回 ISO 时间字符串
        last_updated = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(mtime))
        return text, last_updated
    except Exception as e:
        return f"Error reading advice: {e}", None

@app.route("/api/advice", methods=["GET"])
def api_advice():
    text, last_updated = read_advice()
    # 将文本按换行/空行拆成若干建议块（尽量智能拆分）
    blocks = []
    if text:
        # 按两次换行或 首尾分段
        parts = [p.strip() for p in text.split("\n\n") if p.strip()]
        if len(parts) == 0:
            parts = [line.strip() for line in text.splitlines() if line.strip()]
        blocks = parts
    return make_response(jsonify({
        "ok": True,
        "last_updated": last_updated,
        "advice_text": text,
        "advice_blocks": blocks
    }), 200)

if __name__ == "__main__":
    # dev server: 修改 host/port 按需改变
    app.run(host="0.0.0.0", port=8080, debug=True)

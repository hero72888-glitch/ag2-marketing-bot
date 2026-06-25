import os
from flask import Flask, request, jsonify
from agents import process_customer_message

app = Flask(__name__)

@app.route("/", methods=["GET"])
def health_check():
    return "AG2 虛擬特種部隊已上線！24小時待命！", 200

@app.route("/api/line-bot", methods=["POST", "GET"])
def line_webhook():
    if request.method == "GET":
        return "LINE Webhook 正在監聽中...", 200
        
    data = request.json
    print(f"收到 LINE Webhook 訊息: {data}")
    
    if not data or "events" not in data:
        return jsonify({"status": "ignored"}), 200
        
    for event in data["events"]:
        if event.get("type") == "message" and event["message"].get("type") == "text":
            user_msg = event["message"]["text"]
            
            # 交給 AG2 客服專員處理
            print(f"客人說: {user_msg}")
            ai_reply = process_customer_message(user_msg)
            print(f"AI 決定回覆: {ai_reply}")
            
            # 這裡未來會接上 LINE Bot SDK 把 ai_reply 傳回給客人
            # 並且把這段對話透過 LINE Notify 傳給您的私人群組備份
            
    return jsonify({"status": "success"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)

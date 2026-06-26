import os
import logging
from flask import Flask, request, jsonify, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    StickerMessage
)
from agents import process_customer_message
import json

# 設定結構化日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ADMINS_FILE = 'admins.json'

def load_admins():
    if os.path.exists(ADMINS_FILE):
        with open(ADMINS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_admin(user_id):
    admins = load_admins()
    if user_id not in admins:
        admins.append(user_id)
        with open(ADMINS_FILE, 'w', encoding='utf-8') as f:
            json.dump(admins, f)

app = Flask(__name__)

# 綁定 LINE 的大門鑰匙
line_bot_api = LineBotApi(os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', ''))
handler = WebhookHandler(os.environ.get('LINE_CHANNEL_SECRET', ''))

@app.route("/", methods=["GET"])
def health_check():
    return "AG2 虛擬特種部隊已上線！24小時待命！", 200

@app.route("/api/line-bot", methods=["POST"])
def line_webhook():
    signature = request.headers.get('X-Line-Signature')
    if not signature:
        logger.warning("收到沒有簽名的請求")
        return "Invalid signature", 400

    body = request.get_data(as_text=True)
    logger.info(f"收到 LINE 訊息: {body[:200]}")  # 限制日誌長度

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        logger.error("無效的簽名！")
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_msg = event.message.text
    user_id = event.source.user_id
    logger.info(f"收到文字訊息: {user_msg} (來自: {user_id})")

    # 檢查是否為老闆通關密語
    secret_passwords = ["大熊老闆", "貓咪老闆"]
    if user_msg in secret_passwords:
        save_admin(user_id)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"🫡 收到！身份確認完畢。歡迎登入，行銷總監隨時為您服務！\n(您的專屬ID已綁定：{user_id[:5]}...)")
        )
        return

    admins = load_admins()
    if user_id in admins:
        # 如果是老闆，就喚醒行銷總監 (階段三)
        from marketing_agent import generate_and_post_marketing_content
        
        # 暫時先回覆老闆正在處理中
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"【總監模式】收到！正在為「{user_msg}」撰寫並發布社群貼文，請稍候...")
        )
        
        # 執行發文 (這裡會稍微卡住幾秒鐘等待 AI 寫文和呼叫 API)
        result_msg = generate_and_post_marketing_content(user_msg)
        
        # 發布完成後，再次推播通知老闆 (因為 reply_token 只能用一次，所以改用 push_message)
        line_bot_api.push_message(
            user_id,
            TextSendMessage(text=result_msg)
        )
        return

    # 一般客人模式
    # 呼叫 AG2 的虛擬特種部隊處理客人訊息
    reply = process_customer_message(user_msg)

    # 回覆 LINE 用戶
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )

@handler.add(MessageEvent, message=StickerMessage)
def handle_sticker(event):
    """收到貼圖時，回覆親切的招呼"""
    logger.info(f"客人傳了貼圖 (package: {event.message.package_id}, sticker: {event.message.sticker_id})")

    # 隨機風格的親切回應
    import random
    greetings = [
        "哈囉！😊 有什麼我可以幫您的嗎？想了解抓周派對的資訊都可以問我喔！",
        "嗨嗨～歡迎來到大熊老師與蘋果老師的小天地！🐻🍎 需要什麼服務呢？",
        "您好呀！👋 想為寶貝規劃一場難忘的抓周派對嗎？隨時問我喔！",
        "哈囉哈囉～🎉 很高興收到您的訊息！有任何問題都歡迎詢問！",
    ]

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=random.choice(greetings))
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

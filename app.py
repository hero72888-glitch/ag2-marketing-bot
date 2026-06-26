import os
import logging
from flask import Flask, request, jsonify, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    StickerMessage, ImageMessage, PostbackEvent,
    TemplateSendMessage, ButtonsTemplate, PostbackAction
)
from agents import process_customer_message
import json
import threading

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
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"【總監模式】收到靈感！正在為您撰寫社群貼文草稿，請稍候...")
        )
        
        def process_text_draft():
            from marketing_agent import generate_draft
            # 產生草稿
            draft_data, preview_msg = generate_draft(user_id, topic=user_msg)
            
            if draft_data:
                # 傳送帶有確認按鈕的訊息
                buttons_template = ButtonsTemplate(
                    title='草稿審核',
                    text='老闆，這是為您準備的草稿，請問要發布嗎？',
                    actions=[
                        PostbackAction(label='✅ 確認發布', data='action=approve_post'),
                        PostbackAction(label='❌ 取消重寫', data='action=reject_post')
                    ]
                )
                template_message = TemplateSendMessage(
                    alt_text='草稿審核 (請在手機上查看)',
                    template=buttons_template
                )
                
                line_bot_api.push_message(
                    user_id,
                    [TextSendMessage(text=preview_msg), template_message]
                )
            else:
                line_bot_api.push_message(
                    user_id,
                    TextSendMessage(text=preview_msg) # 錯誤訊息
                )
                
        # 啟動背景執行緒，避免 LINE 逾時斷線
        threading.Thread(target=process_text_draft).start()
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

@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    user_id = event.source.user_id
    logger.info(f"收到圖片訊息 (來自: {user_id})")

    admins = load_admins()
    if user_id in admins:
        # 老闆傳照片，觸發 IG 九宮格模式
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="【總監模式】收到照片！正在啟動裁切引擎與撰寫三平台草稿，這需要一點時間，請稍候...")
        )
        
        # 下載圖片
        message_content = line_bot_api.get_message_content(event.message.id)
        image_bytes = b''
        for chunk in message_content.iter_content():
            image_bytes += chunk
            
        def process_image_draft():
            from marketing_agent import generate_draft
            
            # 產生草稿與切圖
            draft_data, preview_msg = generate_draft(user_id, image_bytes=image_bytes)
            
            if draft_data:
                # 傳送帶有確認按鈕的訊息
                buttons_template = ButtonsTemplate(
                    title='貼文草稿審核',
                    text='老闆，九宮格跟文案都準備就緒，請問要發布嗎？',
                    actions=[
                        PostbackAction(label='✅ 確認發布', data='action=approve_post'),
                        PostbackAction(label='❌ 取消重寫', data='action=reject_post')
                    ]
                )
                template_message = TemplateSendMessage(
                    alt_text='草稿審核 (請在手機上查看)',
                    template=buttons_template
                )
                
                line_bot_api.push_message(
                    user_id,
                    [TextSendMessage(text=preview_msg), template_message]
                )
            else:
                line_bot_api.push_message(
                    user_id,
                    TextSendMessage(text=preview_msg) # 錯誤訊息
                )
                
        # 啟動背景執行緒，避免 LINE 逾時斷線
        threading.Thread(target=process_image_draft).start()
    else:
        # 一般客人傳照片
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="好漂亮的照片呀！謝謝您的分享😊")
        )

@handler.add(PostbackEvent)
def handle_postback(event):
    user_id = event.source.user_id
    data = event.postback.data
    logger.info(f"收到 Postback: {data} (來自: {user_id})")
    
    from marketing_agent import execute_post, clear_draft
    
    if data == 'action=approve_post':
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="收到！正在為您執行正式發布，請稍候...")
        )
        
        def execute_post_in_background():
            result_msg = execute_post(user_id)
            line_bot_api.push_message(user_id, TextSendMessage(text=result_msg))
            
        threading.Thread(target=execute_post_in_background).start()
        
    elif data == 'action=reject_post':
        clear_draft(user_id)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="好的！這篇草稿已銷毀 🗑️，請給我新的照片或靈感來重寫一篇！")
        )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

import os
import logging
import json
import uuid
import google.generativeai as genai
from social_apis import post_to_facebook, post_to_threads, post_to_instagram_grid
from image_processor import crop_and_upload_to_imgbb, upload_single_image_to_imgbb

logger = logging.getLogger(__name__)

# 初始化 Gemini
genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-2.5-flash')

DRAFTS_FILE = 'drafts.json'

def save_draft(user_id, draft_data):
    drafts = {}
    if os.path.exists(DRAFTS_FILE):
        with open(DRAFTS_FILE, 'r', encoding='utf-8') as f:
            drafts = json.load(f)
    drafts[user_id] = draft_data
    with open(DRAFTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(drafts, f, ensure_ascii=False, indent=2)

def load_draft(user_id):
    if os.path.exists(DRAFTS_FILE):
        with open(DRAFTS_FILE, 'r', encoding='utf-8') as f:
            drafts = json.load(f)
            return drafts.get(user_id)
    return None

def clear_draft(user_id):
    if os.path.exists(DRAFTS_FILE):
        with open(DRAFTS_FILE, 'r', encoding='utf-8') as f:
            drafts = json.load(f)
        if user_id in drafts:
            del drafts[user_id]
            with open(DRAFTS_FILE, 'w', encoding='utf-8') as f:
                json.dump(drafts, f, ensure_ascii=False, indent=2)

def generate_draft(user_id, topic=None, image_bytes=None, mode='all'):
    """
    生成草稿並儲存，不發布。
    mode: 'ig', 'fb_threads', 'all'
    """
    try:
        if image_bytes:
            logger.info(f"收到圖片，執行模式: {mode}")
            
            ig_content = None
            fb_content = None
            threads_content = None
            image_urls = []
            original_image_url = None
            
            if mode in ['ig', 'all']:
                logger.info("產生 IG 九宮格草稿與圖片...")
                ig_prompt = """
                你是一個專業的社群行銷小編，為「大熊老師與蘋果老師」(專辦高品質抓周派對) 寫 Instagram 貼文。
                老闆給了一張活動照片。請寫一篇充滿愛與溫馨的貼文，適合九宮格排版。
                嚴格要求：
                1. 結尾附上預約網址：https://bearapple-zhuazhou-party.vercel.app/
                2. 加上 #抓周 #寶寶派對 等 Hashtag。
                3. 直接輸出貼文內容，**絕對不要**有「好的、總監出馬、附上照片」等開場白或對話，只要純粹的貼文文字。
                """
                ig_content = model.generate_content(ig_prompt).text.strip()
                image_urls = crop_and_upload_to_imgbb(image_bytes)
                if not image_urls or len(image_urls) != 9:
                    return None, "❌ 九宮格切圖或上傳失敗，請檢查 API Key 或稍後再試。"

            if mode in ['fb_threads', 'all']:
                logger.info("產生 FB、Threads 草稿與大圖上傳...")
                original_image_url = upload_single_image_to_imgbb(image_bytes)
                if not original_image_url:
                    return None, "❌ 單圖上傳失敗，請檢查 API Key 或稍後再試。"

                fb_prompt = """
                你是一個專業的社群行銷小編，為「大熊老師與蘋果老師」寫 Facebook 粉絲團長篇溫馨貼文。
                老闆給了一張活動照片。請用感性、故事性的筆觸寫作。
                嚴格要求：
                1. 結尾附上預約網址：https://bearapple-zhuazhou-party.vercel.app/
                2. 加上 Hashtag。
                3. 直接輸出貼文內容，**絕對不要**有「好的、沒問題、附上照片」等開場白或對話。
                """
                fb_content = model.generate_content(fb_prompt).text.strip()

                threads_prompt = """
                你是一個專業的社群行銷小編，為「大熊老師與蘋果老師」寫 Threads 短平快文案。
                請用非常簡短、幽默、生活化、像朋友聊天的風格。
                重要指示：必須巧妙地帶出我們是「辦抓周派對的專家」，稍微帶一點點宣傳味，但不要太過生硬。
                嚴格要求：直接輸出貼文內容，**絕對不要**有「好的、沒問題、總監出馬、附上照片」等開場白或對話。
                """
                threads_content = model.generate_content(threads_prompt).text.strip()
            
            draft_data = {
                "type": "image",
                "mode": mode,
                "ig_content": ig_content,
                "image_urls": image_urls,
                "fb_content": fb_content,
                "threads_content": threads_content,
                "original_image_url": original_image_url
            }
            save_draft(user_id, draft_data)
            
            preview = ""
            if mode in ['ig', 'all']:
                preview += f"【IG 草稿】(將發布九宮格)\n{ig_content}\n\n"
            if mode in ['fb_threads', 'all']:
                preview += f"【FB 草稿】(將發布單一大圖)\n{fb_content}\n\n"
                preview += f"【Threads 草稿】(將發布單一大圖)\n{threads_content}\n"
            
            return draft_data, preview.strip()
            
        elif topic:
            logger.info(f"行銷總監構思靈感：{topic}")
            
            fb_prompt = f"""
            你是一個專業的社群行銷小編。老闆給了一個貼文靈感：「{topic}」。
            請寫一篇適合發在 Facebook 粉絲團的溫馨長文。結尾附上預約網頁連結：https://bearapple-zhuazhou-party.vercel.app/
            加上 Hashtag。嚴格要求：直接輸出貼文內容，**絕對不要**有任何開場白或多餘對話。
            """
            fb_content = model.generate_content(fb_prompt).text.strip()
            
            threads_prompt = f"""
            你是一個專業的社群行銷小編。老闆給了一個貼文靈感：「{topic}」。
            請寫一篇適合發在 Threads 的短平快文案。保持幽默、生活化的口吻。
            重要指示：必須巧妙地帶出我們是「辦抓周派對的專家」，稍微帶一點點宣傳味，但不要像死板的廣告。
            嚴格要求：直接輸出貼文內容，**絕對不要**有任何開場白或多餘對話。
            """
            threads_content = model.generate_content(threads_prompt).text.strip()
            
            draft_data = {
                "type": "text",
                "fb_content": fb_content,
                "threads_content": threads_content
            }
            save_draft(user_id, draft_data)
            
            preview = f"【FB 草稿】\n{fb_content}\n\n---\n【Threads 草稿】\n{threads_content}"
            return draft_data, preview
            
    except Exception as e:
        logger.error(f"草稿生成失敗: {e}")
        return None, f"❌ 總監遇到錯誤：{str(e)}"

def execute_post(user_id):
    """
    執行真實的發布動作
    """
    draft = load_draft(user_id)
    if not draft:
        return "找不到草稿，請重新傳送指令。"
        
    try:
        if draft["type"] == "image":
            mode = draft.get("mode", "all")
            msg = "✅ 發布完成！\n"
            
            if mode in ['ig', 'all']:
                ig_success = post_to_instagram_grid(draft["image_urls"], draft["ig_content"])
                msg += f"📸 IG 九宮格：{'成功' if ig_success else '失敗'}\n"
                
            if mode in ['fb_threads', 'all']:
                original_img = draft.get("original_image_url")
                fb_success = post_to_facebook(draft["fb_content"], original_img)
                threads_success = post_to_threads(draft["threads_content"], original_img)
                msg += f"📘 Facebook：{'成功' if fb_success else '失敗'}\n"
                msg += f"🧵 Threads：{'成功' if threads_success else '失敗'}"
            
            clear_draft(user_id)
            return msg
                
        elif draft["type"] == "text":
            fb_success = post_to_facebook(draft["fb_content"])
            threads_success = post_to_threads(draft["threads_content"])
            clear_draft(user_id)
            
            msg = "✅ 文字貼文發布完成！\n"
            msg += f"📘 Facebook：{'成功' if fb_success else '失敗'}\n"
            msg += f"🧵 Threads：{'成功' if threads_success else '失敗'}"
            return msg
            
    except Exception as e:
        logger.error(f"執行發布失敗: {e}")
        return f"❌ 發布時發生錯誤：{str(e)}"

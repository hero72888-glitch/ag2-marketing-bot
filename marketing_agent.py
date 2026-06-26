import os
import logging
import json
import uuid
import google.generativeai as genai
from social_apis import post_to_facebook, post_to_threads, post_to_instagram_grid
from image_processor import crop_and_upload_to_imgbb

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

def generate_draft(user_id, topic=None, image_bytes=None):
    """
    生成草稿並儲存，不發布。
    """
    try:
        if image_bytes:
            logger.info("行銷總監收到圖片，準備 IG 草稿與切圖...")
            
            ig_prompt = """
            你現在是「大熊老師與蘋果老師」的行銷總監。這是一個提供高品質抓周派對、活動主持的品牌。
            老闆剛剛上傳了一張精彩的活動照片，準備要在 Instagram 上發布九宮格大圖。
            請幫我寫一篇適合發在 Instagram 的質感貼文。
            語氣要專業、充滿感情、營造出歡樂溫馨的氛圍，結尾附上預約網址：https://bearapple-zhuazhou-party.vercel.app/
            一定要加上豐富的 Hashtag (如 #抓周 #寶寶派對 #大熊老師)。
            直接輸出貼文內容，不要有任何多餘的對話。
            """
            ig_response = model.generate_content(ig_prompt)
            ig_content = ig_response.text.strip()
            
            # 切圖上傳
            image_urls = crop_and_upload_to_imgbb(image_bytes)
            if len(image_urls) != 9:
                return None, "❌ 九宮格切圖或上傳失敗，請檢查 ImgBB API Key 或稍後再試。"
                
            logger.info("開始生成 FB 與 Threads 草稿...")
            fb_prompt = f"""
            你現在是「大熊老師與蘋果老師」的行銷總監。這是一個提供高品質抓周派對、活動主持的品牌。
            老闆剛剛上傳了一張精彩的活動照片。
            請幫我寫一篇適合發在 Facebook 粉絲團的溫馨長文。
            語氣要專業、充滿感情，結尾必須附上預約網頁連結：https://bearapple-zhuazhou-party.vercel.app/
            加上適合的 Hashtag。直接輸出貼文內容，不要有多餘對話。
            """
            fb_content = model.generate_content(fb_prompt).text.strip()
            
            threads_prompt = f"""
            你現在是「大熊老師與蘋果老師」的行銷總監。老闆剛剛上傳了一張活動照片。
            請寫一篇適合發在 Threads 的短平快文案。幽默、口語化。直接輸出貼文內容。
            """
            threads_content = model.generate_content(threads_prompt).text.strip()
            
            draft_data = {
                "type": "image",
                "ig_content": ig_content,
                "image_urls": image_urls,
                "fb_content": fb_content,
                "threads_content": threads_content
            }
            save_draft(user_id, draft_data)
            
            preview = f"【IG 草稿】\n{ig_content[:50]}...\n\n【FB 草稿】\n{fb_content[:50]}...\n\n【Threads 草稿】\n{threads_content[:50]}...\n\n(已為您切好 9 張高畫質小圖準備發布！)"
            return draft_data, preview
            
        elif topic:
            logger.info(f"行銷總監構思靈感：{topic}")
            
            fb_prompt = f"""
            你現在是「大熊老師與蘋果老師」的行銷總監。老闆給了一個貼文靈感：「{topic}」。
            請寫一篇適合發在 Facebook 粉絲團的溫馨長文。結尾附上預約網頁連結：https://bearapple-zhuazhou-party.vercel.app/
            加上 Hashtag。直接輸出貼文內容。
            """
            fb_content = model.generate_content(fb_prompt).text.strip()
            
            threads_prompt = f"""
            你現在是「大熊老師與蘋果老師」的行銷總監。老闆給了一個貼文靈感：「{topic}」。
            請寫一篇適合發在 Threads 的短平快文案。幽默、口語化。直接輸出貼文內容。
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
            ig_success = post_to_instagram_grid(draft["image_urls"], draft["ig_content"])
            fb_success = post_to_facebook(draft["fb_content"])
            threads_success = post_to_threads(draft["threads_content"])
            
            clear_draft(user_id)
            
            msg = "✅ 三平台發布完成！\n"
            msg += f"📸 IG 九宮格：{'成功' if ig_success else '失敗'}\n"
            msg += f"📘 Facebook：{'成功' if fb_success else '失敗'}\n"
            msg += f"🧵 Threads：{'成功' if threads_success else '失敗'}"
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

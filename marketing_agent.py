import os
import logging
import google.generativeai as genai
from social_apis import post_to_facebook, post_to_threads, post_to_instagram_grid
from image_processor import crop_and_upload_to_imgbb

logger = logging.getLogger(__name__)

# 初始化 Gemini
genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-2.5-flash')

def generate_and_post_marketing_content(topic=None, image_bytes=None):
    """
    接收老闆的靈感 (topic) 或照片 (image_bytes)，自動生成文案，並發布。
    如果是文字：發布到 FB 和 Threads。
    如果是圖片：觸發 IG 九宮格裁切，生成專屬文案並發布 IG 九宮格。
    """
    try:
        if image_bytes:
            logger.info("行銷總監收到圖片任務，啟動九宮格引擎...")
            
            # 1. 構思 IG 文案 (因為收到的是圖片，我們讓 Gemini 直接產一篇通用/視覺導向的貼文)
            ig_prompt = """
            你現在是「大熊老師與蘋果老師」的行銷總監。這是一個提供高品質抓周派對、活動主持的品牌。
            老闆剛剛上傳了一張精彩的活動照片，準備要在 Instagram 上發布九宮格大圖。
            請幫我寫一篇適合發在 Instagram 的質感貼文。
            語氣要專業、充滿感情、營造出歡樂溫馨的氛圍，結尾附上預約網址：https://bearapple-zhuazhou-party.vercel.app/
            一定要加上豐富的 Hashtag (如 #抓周 #寶寶派對 #大熊老師與蘋果老師)。
            直接輸出貼文內容，不要有任何多餘的對話。
            """
            ig_response = model.generate_content(ig_prompt)
            ig_content = ig_response.text.strip()
            
            # 2. 啟動切圖引擎
            logger.info("開始裁切並上傳 ImgBB...")
            image_urls = crop_and_upload_to_imgbb(image_bytes)
            
            if len(image_urls) != 9:
                return "❌ 九宮格切圖或上傳失敗，請檢查 ImgBB API Key 或稍後再試。"
                
            # 3. 發布 IG
            logger.info("開始逆向發布 IG 九宮格...")
            ig_success = post_to_instagram_grid(image_urls, ig_content)
            
            result_msg = f"✅ 【IG 九宮格任務完成】\n\n"
            result_msg += f"📸 Instagram 發布：{'成功' if ig_success else '失敗'}\n\n"
            result_msg += f"預覽文案：\n{ig_content[:50]}..."
            return result_msg
            
        elif topic:
            logger.info(f"行銷總監收到靈感：{topic}")
            
            # 1. 構思 FB 文案
            fb_prompt = f"""
            你現在是「大熊老師與蘋果老師」的行銷總監。這是一個提供高品質抓周派對、活動主持的品牌。
            老闆給了一個貼文靈感：「{topic}」。
            請幫我寫一篇適合發在 Facebook 粉絲團的溫馨長文。
            語氣要專業、充滿感情，結尾必須附上預約網頁連結：https://bearapple-zhuazhou-party.vercel.app/
            加上適合的 Hashtag。
            直接輸出貼文內容，不要有任何多餘的對話。
            """
            fb_response = model.generate_content(fb_prompt)
            fb_content = fb_response.text.strip()
            
            # 2. 構思 Threads 文案
            threads_prompt = f"""
            你現在是「大熊老師與蘋果老師」的行銷總監。
            老闆給了一個貼文靈感：「{topic}」。
            請幫我寫一篇適合發在 Threads 的短平快文案。
            Threads 的風格是：幽默、口語化、能引起共鳴、像是在跟朋友聊天。字數不要太多。
            直接輸出貼文內容，不要有任何多餘的對話。
            """
            threads_response = model.generate_content(threads_prompt)
            threads_content = threads_response.text.strip()
            
            logger.info("文案生成完畢，準備發布...")
            
            # 3. 發布到社群平台
            fb_success = post_to_facebook(fb_content)
            threads_success = post_to_threads(threads_content)
            
            result_msg = f"✅ 【文字行銷任務完成】\n\n"
            result_msg += f"📘 Facebook 發布：{'成功' if fb_success else '失敗'}\n"
            result_msg += f"🧵 Threads 發布：{'成功' if threads_success else '失敗'}\n\n"
            result_msg += f"預覽 FB 文案：\n{fb_content[:50]}...\n\n"
            result_msg += f"預覽 Threads 文案：\n{threads_content[:50]}..."
            
            return result_msg
            
    except Exception as e:
        logger.error(f"行銷總監執行任務失敗: {e}")
        return f"❌ 總監遇到錯誤：{str(e)}"

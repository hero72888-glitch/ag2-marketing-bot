import os
import logging
import google.generativeai as genai
from social_apis import post_to_facebook, post_to_threads

logger = logging.getLogger(__name__)

# 初始化 Gemini
genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-2.5-flash')

def generate_and_post_marketing_content(topic):
    """
    接收老闆的靈感 (topic)，自動生成 FB 和 Threads 的文案，並發布。
    """
    try:
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
        
        result_msg = f"✅ 【行銷任務完成】\n\n"
        result_msg += f"📘 Facebook 發布：{'成功' if fb_success else '失敗'}\n"
        result_msg += f"🧵 Threads 發布：{'成功' if threads_success else '失敗'}\n\n"
        result_msg += f"預覽 FB 文案：\n{fb_content[:50]}...\n\n"
        result_msg += f"預覽 Threads 文案：\n{threads_content[:50]}..."
        
        return result_msg
        
    except Exception as e:
        logger.error(f"行銷總監執行任務失敗: {e}")
        return f"❌ 總監遇到錯誤：{str(e)}"

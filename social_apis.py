import os
import requests
import logging
import time

logger = logging.getLogger(__name__)

FB_PAGE_ACCESS_TOKEN = os.environ.get('FB_PAGE_ACCESS_TOKEN')
FB_PAGE_ID = os.environ.get('FB_PAGE_ID')
THREADS_ACCESS_TOKEN = os.environ.get('THREADS_ACCESS_TOKEN')
THREADS_USER_ID = os.environ.get('THREADS_USER_ID')
IG_USER_ID = os.environ.get('IG_USER_ID')

def post_to_facebook(message, image_url=None):
    """發布文字(或附帶圖片)到 Facebook 粉絲專頁"""
    if not FB_PAGE_ACCESS_TOKEN or not FB_PAGE_ID:
        logger.error("缺少 FB API Tokens")
        return False
        
    if image_url:
        url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/photos"
        payload = {
            'url': image_url,
            'message': message,
            'access_token': FB_PAGE_ACCESS_TOKEN
        }
    else:
        url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/feed"
        payload = {
            'message': message,
            'access_token': FB_PAGE_ACCESS_TOKEN
        }
    
    response = requests.post(url, data=payload)
    if response.status_code == 200:
        logger.info(f"Facebook 發布成功: {response.json()}")
        return True
    else:
        logger.error(f"Facebook 發布失敗: {response.text}")
        return False

def post_to_threads(text, image_url=None):
    """發布文字(或附帶圖片)到 Threads"""
    if not THREADS_ACCESS_TOKEN or not THREADS_USER_ID:
        logger.error("缺少 Threads API Tokens")
        return False

    # 1. Create a Threads Media Container
    url = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads"
    if image_url:
        payload = {
            'media_type': 'IMAGE',
            'image_url': image_url,
            'text': text,
            'access_token': THREADS_ACCESS_TOKEN
        }
    else:
        payload = {
            'media_type': 'TEXT',
            'text': text,
            'access_token': THREADS_ACCESS_TOKEN
        }
    
    res1 = requests.post(url, data=payload)
    if res1.status_code != 200:
        logger.error(f"Threads Container 建立失敗: {res1.text}")
        return False
        
    container_id = res1.json().get('id')
    
    # 加上 2 秒緩衝，等待 Threads 伺服器處理完圖片，避免馬上發布報錯
    time.sleep(2)
    
    # 2. Publish the Container
    publish_url = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads_publish"
    pub_payload = {
        'creation_id': container_id,
        'access_token': THREADS_ACCESS_TOKEN
    }
    
    res2 = requests.post(publish_url, data=pub_payload)
    if res2.status_code == 200:
        logger.info(f"Threads 發布成功: {res2.json()}")
        return True
    else:
        logger.error(f"Threads 發布失敗: {res2.text}")
        return False

# IG 單圖發布功能
def post_to_instagram_single(image_url, caption):
    """
    發布單張圖片到 Instagram
    """
    if not IG_USER_ID or not FB_PAGE_ACCESS_TOKEN:
        logger.error("缺少 IG_USER_ID 或 FB_PAGE_ACCESS_TOKEN")
        return False
        
    # 建立 IG Container
    url = f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media"
    payload = {
        'image_url': image_url,
        'caption': caption,
        'access_token': FB_PAGE_ACCESS_TOKEN
    }
    
    res1 = requests.post(url, data=payload)
    if res1.status_code != 200:
        logger.error(f"IG Container 建立失敗: {res1.text}")
        return False
        
    container_id = res1.json().get('id')
    
    # 加上 5 秒緩衝，等待 IG 伺服器從 ImgBB 下載並處理完圖片，避免 "Media ID is not available" 錯誤
    time.sleep(5)
    
    # 發布 IG Container
    publish_url = f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media_publish"
    pub_payload = {
        'creation_id': container_id,
        'access_token': FB_PAGE_ACCESS_TOKEN
    }
    
    res2 = requests.post(publish_url, data=pub_payload)
    if res2.status_code == 200:
        logger.info(f"IG 圖片發布成功: {res2.json()}")
        return True
    else:
        logger.error(f"IG 圖片發布失敗: {res2.text}")
        return False

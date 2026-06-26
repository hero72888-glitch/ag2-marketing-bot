import os
import requests
import logging

logger = logging.getLogger(__name__)

FB_PAGE_ACCESS_TOKEN = os.environ.get('FB_PAGE_ACCESS_TOKEN')
FB_PAGE_ID = os.environ.get('FB_PAGE_ID')
THREADS_ACCESS_TOKEN = os.environ.get('THREADS_ACCESS_TOKEN')
THREADS_USER_ID = os.environ.get('THREADS_USER_ID')
IG_USER_ID = os.environ.get('IG_USER_ID')

def post_to_facebook(message):
    """發布文字到 Facebook 粉絲專頁"""
    if not FB_PAGE_ACCESS_TOKEN or not FB_PAGE_ID:
        logger.error("缺少 FB API Tokens")
        return False
        
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

def post_to_threads(text):
    """發布文字到 Threads"""
    if not THREADS_ACCESS_TOKEN or not THREADS_USER_ID:
        logger.error("缺少 Threads API Tokens")
        return False

    # 1. Create a Threads Media Container (Text only)
    url = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads"
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

# IG 九宮格功能會在第二步加入 (需要切圖與上傳)

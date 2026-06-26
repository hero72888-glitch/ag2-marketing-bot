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

# IG 九宮格功能
def post_to_instagram_grid(image_urls, caption):
    """
    發布九宮格圖片到 Instagram
    image_urls 必須是 9 張已經按正確順序 (1到9) 切割好的圖片網址列表。
    為了讓 IG 頁面由左上到右下顯示拼圖，發布順序必須是逆向 (9, 8, 7... 1)。
    只有最後一張 (也就是網格最左上角，順序 1) 會附上完整的文案 (caption)。
    """
    if not IG_USER_ID or not FB_PAGE_ACCESS_TOKEN:
        logger.error("缺少 IG_USER_ID 或 FB_PAGE_ACCESS_TOKEN")
        return False
        
    if len(image_urls) != 9:
        logger.error(f"九宮格圖片數量錯誤: 收到 {len(image_urls)} 張，應該要 9 張")
        return False

    success = True
    # 逆向迴圈，從最後一張 (索引 8) 發佈到第一張 (索引 0)
    for i in range(8, -1, -1):
        img_url = image_urls[i]
        
        # 建立 IG Container
        url = f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media"
        payload = {
            'image_url': img_url,
            'access_token': FB_PAGE_ACCESS_TOKEN
        }
        
        # 只有最後一次發佈 (索引 0，對應九宮格左上角) 才加上文案
        if i == 0:
            payload['caption'] = caption
            
        res1 = requests.post(url, data=payload)
        if res1.status_code != 200:
            logger.error(f"IG Container 建立失敗 (圖片 {i+1}): {res1.text}")
            success = False
            continue
            
        container_id = res1.json().get('id')
        
        # 發布 IG Container
        publish_url = f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media_publish"
        pub_payload = {
            'creation_id': container_id,
            'access_token': FB_PAGE_ACCESS_TOKEN
        }
        
        res2 = requests.post(publish_url, data=pub_payload)
        if res2.status_code == 200:
            logger.info(f"IG 圖片 {i+1} 發布成功: {res2.json()}")
        else:
            logger.error(f"IG 圖片 {i+1} 發布失敗: {res2.text}")
            success = False

    return success

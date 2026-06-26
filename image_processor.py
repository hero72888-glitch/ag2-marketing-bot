import os
import requests
import logging
from PIL import Image
import io

logger = logging.getLogger(__name__)

IMGBB_API_KEY = os.environ.get('IMGBB_API_KEY')

def crop_and_upload_to_imgbb(image_path_or_bytes):
    """
    接收圖片路徑或二進位資料，裁切成 3x3 九宮格，
    並依序上傳至 ImgBB，回傳 9 個公開圖片網址的列表。
    網址順序為由左至右、由上至下 (1到9)。
    """
    if not IMGBB_API_KEY:
        logger.error("缺少 IMGBB_API_KEY，無法上傳圖片。")
        return []

    try:
        if isinstance(image_path_or_bytes, bytes):
            img = Image.open(io.BytesIO(image_path_or_bytes))
        else:
            img = Image.open(image_path_or_bytes)
            
        # 轉換為 RGB 以防有 Alpha 通道 (PNG)
        if img.mode != 'RGB':
            img = img.convert('RGB')
            
        width, height = img.size
        # 以短邊為基準，裁切出正中央的正方形
        size = min(width, height)
        left = (width - size) / 2
        top = (height - size) / 2
        right = (width + size) / 2
        bottom = (height + size) / 2
        
        img_square = img.crop((left, top, right, bottom))
        
        # 計算九宮格每格的寬高
        step = size // 3
        
        uploaded_urls = []
        
        # 產生 9 張小圖並上傳
        for i in range(3):
            for j in range(3):
                box = (j * step, i * step, (j + 1) * step, (i + 1) * step)
                cropped_img = img_square.crop(box)
                
                # 將圖片存入記憶體
                img_byte_arr = io.BytesIO()
                cropped_img.save(img_byte_arr, format='JPEG', quality=90)
                img_bytes = img_byte_arr.getvalue()
                
                # 呼叫 ImgBB API 上傳
                url = f"https://api.imgbb.com/1/upload?key={IMGBB_API_KEY}"
                files = {
                    'image': ('grid.jpg', img_bytes, 'image/jpeg')
                }
                
                res = requests.post(url, files=files)
                if res.status_code == 200:
                    data = res.json()
                    img_url = data['data']['url']
                    uploaded_urls.append(img_url)
                else:
                    logger.error(f"ImgBB 上傳失敗: {res.text}")
                    return []
                    
        return uploaded_urls

    except Exception as e:
        logger.error(f"裁切或上傳過程發生錯誤: {e}")
        return []

def upload_single_image_to_imgbb(image_path_or_bytes):
    """
    將單張原始大圖直接上傳到 ImgBB，並回傳圖片公開網址。
    """
    if not IMGBB_API_KEY:
        logger.error("缺少 IMGBB_API_KEY，無法上傳圖片。")
        return None

    try:
        if isinstance(image_path_or_bytes, bytes):
            img_bytes = image_path_or_bytes
        else:
            with open(image_path_or_bytes, "rb") as f:
                img_bytes = f.read()

        url = f"https://api.imgbb.com/1/upload?key={IMGBB_API_KEY}"
        files = {
            'image': ('original.jpg', img_bytes, 'image/jpeg')
        }
        
        res = requests.post(url, files=files)
        if res.status_code == 200:
            data = res.json()
            return data['data']['url']
        else:
            logger.error(f"ImgBB 單圖上傳失敗: {res.text}")
            return None

    except Exception as e:
        logger.error(f"單圖上傳過程發生錯誤: {e}")
        return None

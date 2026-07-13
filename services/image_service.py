import cv2
import numpy as np

class ImageService:
# =======================================
#       Image 預處理與辨識演算法
# =======================================
    @staticmethod
    def preprocess_image(image_file):
        try:
            img = cv2.imdecode(np.fromfile(image_file, dtype=np.uint8), cv2.IMREAD_COLOR)
            if img is None:
                print(f"❌ 圖片讀取失敗！")
                exit()
            print(f"✅ 圖片讀取成功！尺寸為: {img.shape[1]}x{img.shape[0]}\n格式: {type(img)}")
            return img
        except Exception as e:
            print(f"❌ 讀取圖片時發生異常: {e}")
            exit()

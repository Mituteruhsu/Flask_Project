import cv2
# =======================================
#       Image 預處理與辨識演算法
# =======================================
def preprocess_image(image_path):
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None: return None
    h, w = img.shape
    if w > 1000:
        img = cv2.resize(img, (1000, int(h * 1000 / w)), interpolation=cv2.INTER_AREA)
    _, binary_img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    output_path = os.path.join(UPLOAD_FOLDER, 'preprocessed.png')
    cv2.imwrite(output_path, binary_img)
    return output_path
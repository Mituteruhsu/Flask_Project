import re
from pyzbar.pyzbar import decode
from model_recieve import QRCodeInfo

class QRService:
    @staticmethod
    def parse_taiwan_qrcode(uploaded_image):
        # print(f"test the parse_taiwan_qrcode \n{uploaded_image}")
        # 使用 pyzbar 進行解碼
        barcodes = decode(uploaded_image)

        # 3. 讀取解碼結果
        for barcode in barcodes:
            # 條碼的內容 (型態為 bytes，需以 utf-8 解碼成字串)
            barcode_data = barcode.data
            # 條碼的類型 (例如: 'QRCODE', 'CODE128')
            barcode_type = barcode.type
            barcode_rect = barcode.rect
            barcode_polygon = barcode.polygon
            barcode_points = [(point.x, point.y) for point in barcode_polygon]
            barcode_orientation = barcode.orientation
            barcode_quality = barcode.quality

            print(f"型態: {barcode_type}\n內容: {barcode_data}\n頂點座標: {barcode_points}\n矩形座標: {barcode_rect}\n方向: {barcode_orientation}\n品質: {barcode_quality}")

        raw_qrs = []    
        for obj in barcodes:
            try:
                data = obj.data.decode('utf-8')  # 嘗試以 UTF-8 解碼
                # 過濾掉太短的資料
                if len(data) >= 8:
                    raw_qrs.append(data)
            except Exception:
                continue
        print(f"services/qr_service.py QRService.decode() - decoded {len(raw_qrs)} QR codes")
        print(f"decoded QR codes: {raw_qrs}")
        
        def recode(x):      # 判別 0 , 1 , 2 是否為 Big5, UTF-8, Base64
            print("-----From barcode.data.decode('utf-8')----- \n", x)
            y= list(filter(None, re.search("[0-9]{1}:[0-9]{1}:[0-9]{1}:", x, flags=0).group(0).split(':'))) # 正則表達找出與關鍵類似的字元
            y= int(y[2])
            if y == 0:
                try:
                    print('-----big5 decoded!!-----')
                    x=x.encode('shift-jis').decode('big5')
                    print(x)
                    return x
                except:
                    print('not decodeable')
                finally:
                    return x
            elif y == 1:
                print('-----utf-8 decoded!!-----')
                return x
            elif y == 2:
                print('undefinde decode: base64') 

        def reInfo(x):
            x=recode(x) # 判別0,1,2 是否為utf-8, base64, big5
            recieve = x[:10]
            recieve_date = x[10:17]
            recieve_randam = x[17:21]
            recieve_sale_Hex = x[21:29]
            recieve_sale = str(int(recieve_sale_Hex, 16))
            recieve_total_sale_Hex = x[29:37]
            recieve_total_sale = str(int(recieve_total_sale_Hex, 16))
            recieve_buyer_invoice_num = x[37:45]
            if recieve_buyer_invoice_num == "00000000":
                recieve_buyer_invoice_num = "一般消費者"
            recieve_seller_invoice_num = x[45:53]
            recieve_AESencode = x[53:77]
            # 第 77碼之後的資料，依照冒號分隔，並將空字串過濾掉
            after77 = x[77:]
            z = [i for i in after77.split(':') if i != ""]
            recieve_free_usage = z[0]
            recieve_Item = z[1]
            recieve_totle_Item = z[2]
            codetype = z[3]
            if codetype == '0': codetype = '0:Big5'
            elif codetype == '1': codetype = '1:UTF-8'
            elif codetype =='2': codetype = '2:Base64'

            # print("發票字軌(10位)    : " + self.recieve)
            # print("發票開立日期 (7位): " + self.recieve_date)
            # print("隨機碼 (4位)      : " + self.recieve_randam)
            # print("銷售額 (8位)      : " + self.recieve_sale + " 元")
            # print("總計額 (8位)      : " + self.recieve_total_sale + " 元")
            # print("買方統一編號 (8位): " + self.recieve_buyer_invoice_num)
            # print("賣方統一編號 (8位): " + self.recieve_seller_invoice_num)
            # print("加密驗證資訊(24位): " + self.recieve_AESencode)
            # print("營業人使用區(10位): " + self.recieve_free_usage)
            # print("品目筆數          : " + self.recieve_Item)
            # print("品目總筆數        : " + self.recieve_totle_Item)
            # =======span 鎖定品目比數後方資料彙整=======
            x = (x[(re.search("[0-9]{1}:[0-9]{1}:[0-9]{1}:", x, flags=0).span()[1]):]).split(":") # 正則表達找出與關鍵類似的字元
            # print(x)
            # =======split 將資料變成list一一拆解=======
            # =======將list依照[1, 3, 5]的資料連接=======
            items=' '.join(x[0:len(x):3])
            item_quantity=' '.join(x[1:len(x):3])
            items_price=' '.join(x[2:len(x):3])
            # print(items, item_quantity, items_price)
            return QRCodeInfo(
                recieve,
                recieve_date,
                recieve_randam,
                recieve_sale,
                recieve_total_sale,
                recieve_buyer_invoice_num,
                recieve_seller_invoice_num,
                recieve_AESencode,
                after77,
                recieve_free_usage,
                recieve_Item,
                recieve_totle_Item,
                codetype,
                items,
                item_quantity,
                items_price
                )
        def find_main_qr(raw_qrs):
            """
            從多個 QR Code 中找出電子發票主資料 QR

            判斷條件：
            - 長度 >= 77
            - 包含電子發票格式
            """
            for qr in raw_qrs:
                if len(qr) >= 77 and re.match(r'^[A-Z]{2}\d{8}', qr):
                    return qr
            print("❌ 未偵測到符合電子發票格式的 QR Code")
            return None
        
        # 避免 find_main_qr() 回傳 None 時，直接導致 reInfo() 報錯 
        main_qr = find_main_qr(raw_qrs)
        if main_qr is None:
            return None
        
        info=reInfo(main_qr)
        if info:
            invoice_num = info.recieve
            recive_total_sale = info.recieve_total_sale
            return {"發票號碼": invoice_num, "推算總金額": "NT$" + recive_total_sale, "辨識方法": "QR Code"}
        return None
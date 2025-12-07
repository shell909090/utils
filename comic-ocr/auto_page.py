import sys
import time
import numpy as np
import cv2
from PIL import ImageGrab, Image
from manga_ocr import MangaOcr
from deep_translator import GoogleTranslator

def main():
    print(">>> 正在初始化 MangaOCR...")
    mocr = MangaOcr()
    
    print(">>> 正在初始化 Google 翻译...")
    translator = GoogleTranslator(source='auto', target='zh-CN')

    print("\n" + "="*50)
    print(">>> 【OpenCV 自动检测模式】就绪！")
    print(">>> 复制漫画图片，脚本将尝试通过轮廓检测气泡。")
    print("="*50)

    last_image = None

    try:
        while True:
            try:
                pil_img = ImageGrab.grabclipboard()
            except Exception:
                pil_img = None

            if isinstance(pil_img, Image.Image):
                if last_image != pil_img:
                    print("\n>>> 检测到新图片，正在分析...")
                    start_time = time.time()
                    
                    # 1. 图像预处理
                    img_np = np.array(pil_img)
                    if img_np.shape[2] == 3:
                        img_np = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
                    
                    # 转灰度
                    gray = cv2.cvtColor(img_np, cv2.COLOR_BGR2GRAY)
                    
                    # 2. 寻找白色区域 (漫画气泡通常是白底黑字)
                    # 二值化：将接近白色的区域变成 255 (白)，其他变 0 (黑)
                    # 阈值设为 210，意味着只要比浅灰色更亮就算白色
                    _, binary = cv2.threshold(gray, 210, 255, cv2.THRESH_BINARY)
                    
                    # 3. 轮廓检测
                    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    
                    detected_boxes = []
                    h_img, w_img = gray.shape

                    for cnt in contours:
                        x, y, w, h = cv2.boundingRect(cnt)
                        
                        # 4. 筛选规则 (过滤掉噪点和非气泡)
                        # 规则A: 面积不能太小 (过滤噪点)
                        if w * h < 2000: continue
                        # 规则B: 面积不能太大 (过滤掉整个页面的边框)
                        if w * h > (h_img * w_img * 0.9): continue
                        # 规则C: 宽高比不能太夸张 (过滤掉细长的线条)
                        aspect_ratio = float(w)/h
                        if aspect_ratio > 5 or aspect_ratio < 0.2: continue

                        detected_boxes.append((x, y, w, h))

                    if not detected_boxes:
                        print("未检测到明显的对话框。")
                        last_image = pil_img
                        continue

                    print(f">>> 疑似发现 {len(detected_boxes)} 个气泡")

                    # 5. 排序 (简单的 从右到左，从上到下)
                    # 这里使用加权排序：Y轴权重高，X轴权重负 (实现从右往左)
                    # 这里的逻辑是：先看大致的行 (Y//100)，行内按 X 倒序
                    detected_boxes.sort(key=lambda b: (b[1] // 100, -b[0]))

                    full_translation = []

                    # 6. OCR 和 翻译
                    for i, (x, y, w, h) in enumerate(detected_boxes):
                        # 稍微向内裁剪一点，去除边框线条
                        pad = 5
                        crop = img_np[y+pad:y+h-pad, x+pad:x+w-pad]
                        
                        try:
                            crop_pil = Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))
                            text = mocr(crop_pil)
                            
                            # 如果识别出来的字太少，可能是误判了图形，跳过
                            if len(text) < 2: 
                                continue

                            trans = translator.translate(text)
                            print(f"[{i+1}] {trans}")
                            full_translation.append(trans)
                        except Exception:
                            pass

                    # 复制结果
                    if full_translation:
                        import pyperclip
                        result_text = "\n".join(full_translation)
                        pyperclip.copy(result_text)
                        print(f">>> 已复制 {len(full_translation)} 句译文")
                    
                    print(f"耗时: {time.time() - start_time:.2f}s")
                    print("-" * 50)
                    
                    last_image = pil_img

            time.sleep(1)

    except KeyboardInterrupt:
        print("\n程序已退出。")

if __name__ == '__main__':
    main()

# ⚠️ 加分项：图片文字识别
# 先装：pip install pytesseract pillow，并安装 tesseract 程序 + 中文语言包 chi_sim
import os# os模块（判断文件在不在）
import pytesseract# OCR引擎
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"    # ★引擎完整路径：必须写两层 pytesseract.pytesseract（只写一层=没生效，pytesseract的坑）
from PIL import Image    # 图片处理

def ocr_image(path):# ★图片→文字
    img = Image.open(path)# 打开图片
    text = pytesseract.image_to_string(img, lang="chi_sim")# ★识别文字（中文要chi_sim）
    return text.strip()# 去掉首尾空白

if __name__ == "__main__":# ★入口守卫：直接运行本文件才测试；被loader import时不触发
    if os.path.exists("扫描件.png"):# ★文件在才真识别，不在给提示不崩（别直接崩）
        print(ocr_image("扫描件.png"))# 测试：识别图片里的文字
    else:
        print("没找到扫描件.png——放一张图片到当前目录再测试")# 友好提示

# 集成思路：加载器多一种格式→转成文字→进切分→入库→图片内容也能被检索

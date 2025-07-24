import json
import os
import time
import base64
import requests
from pypdf import PdfWriter
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

# --------------------------------------------------------------------------
# API Key 和输出路径设置
# --------------------------------------------------------------------------
PEXELS_API_KEY = "WYTIJDKwaIxU8DujqrYnnTb8owdBSEXTiiXp1luyQgUBa3JC2rw8CU1C"
OUTPUT_DIR = r"C:\Users\Noah Chen\Documents\BaiduSyncdisk\个人文档\VS Creation\presentation_output"
# --------------------------------------------------------------------------

# --- 为不同类型的幻灯片设计的HTML和CSS模板 ---

# 模板 1: 封面（苹果风格）
HTML_TITLE_TEMPLATE = """
<!DOCTYPE html><html lang=\"zh-CN\"><head><meta charset=\"UTF-8\"><title>Title Slide</title><style>
body{{margin:0;padding:0;width:100vw;height:100vh;background:#000;display:flex;align-items:center;justify-content:center;}}
.slide{{width:1280px;height:720px;display:flex;flex-direction:column;justify-content:center;align-items:center;background:#000;}}
.title{{font-family:'San Francisco', 'Arial', sans-serif;font-size:90px;font-weight:700;color:#fff;letter-spacing:2px;margin-bottom:40px;line-height:1.1;text-shadow:0 4px 32px rgba(0,0,0,0.5);}}
.subtitle{{font-size:36px;font-weight:400;color:#fff;opacity:0.7;letter-spacing:1px;}}
</style></head>
<body><div class=\"slide\" id=\"capture\"><div class=\"title\">{title}</div><div class=\"subtitle\">{subtitle}</div></div></body></html>
"""

# 模板 2: 章节标题（苹果风格）
HTML_SECTION_TEMPLATE = """
<!DOCTYPE html><html lang=\"zh-CN\"><head><meta charset=\"UTF-8\"><title>Section Slide</title><style>
body{{margin:0;padding:0;width:100vw;height:100vh;background:#111;display:flex;align-items:center;justify-content:center;}}
.slide{{width:1280px;height:720px;display:flex;flex-direction:column;justify-content:center;align-items:center;background:#111;}}
.number{{font-size:40px;font-weight:700;color:#fff;opacity:0.5;margin-bottom:20px;letter-spacing:2px;}}
.title{{font-family:'San Francisco', 'Arial', sans-serif;font-size:70px;font-weight:700;color:#fff;letter-spacing:2px;line-height:1.1;text-shadow:0 2px 16px rgba(0,0,0,0.4);}}
</style></head>
<body><div class=\"slide\" id=\"capture\"><div class=\"number\">{number}</div><div class=\"title\">{title}</div></div></body></html>
"""

# 模板 3: 内容页（苹果风格，单页聚焦+大图+极简）
HTML_CONTENT_TEMPLATE = """
<!DOCTYPE html><html lang=\"zh-CN\"><head><meta charset=\"UTF-8\"><title>Content Slide</title><style>
body{{margin:0;padding:0;width:100vw;height:100vh;background:#000;display:flex;align-items:center;justify-content:center;}}
.slide{{width:1280px;height:720px;display:flex;flex-direction:column;justify-content:center;align-items:center;background:#000;position:relative;overflow:hidden;}}
.image-pane{{position:absolute;top:0;left:0;width:100%;height:100%;background-image:url('{image_url}');background-size:cover;background-position:center;filter:brightness(0.5) blur(2px);z-index:0;}}
.content-pane{{position:relative;z-index:1;display:flex;flex-direction:column;align-items:center;justify-content:center;width:100%;height:100%;}}
.title{{font-family:'San Francisco', 'Arial', sans-serif;font-size:60px;font-weight:700;color:#fff;text-align:center;margin-bottom:40px;letter-spacing:1px;text-shadow:0 2px 16px rgba(0,0,0,0.7);}}
.points ul{{list-style:none;padding:0;margin:0;}}
.points li{{font-size:32px;color:#fff;margin-bottom:24px;text-align:center;line-height:1.4;letter-spacing:1px;}}
.footer{{position:absolute;bottom:30px;left:0;width:100%;text-align:center;font-size:18px;color:#fff;opacity:0.3;letter-spacing:1px;}}
</style></head><body><div class=\"slide\" id=\"capture\">
<div class=\"image-pane\"></div>
<div class=\"content-pane\"><div class=\"title\">{title}</div><div class=\"points\"><ul>{points_html}</ul></div></div>
<div class=\"footer\">{footer_text}</div>
</div></body></html>
"""

# 模板 4: 结束页（苹果风格）
HTML_END_TEMPLATE = """
<!DOCTYPE html><html lang=\"zh-CN\"><head><meta charset=\"UTF-8\"><title>End Slide</title><style>
body{{margin:0;padding:0;width:100vw;height:100vh;background:#000;display:flex;align-items:center;justify-content:center;}}
.slide{{width:1280px;height:720px;display:flex;flex-direction:column;justify-content:center;align-items:center;background:#000;position:relative;overflow:hidden;}}
.image-pane{{position:absolute;top:0;left:0;width:100%;height:100%;background-image:url('{image_url}');background-size:cover;background-position:center;filter:brightness(0.4) blur(1px);z-index:0;}}
.overlay{{position:absolute;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);z-index:1;}}
.content{{position:relative;z-index:2;text-align:center;color:#fff;}}
.title{{font-family:'San Francisco', 'Arial', sans-serif;font-size:80px;font-weight:700;margin-bottom:30px;letter-spacing:2px;text-shadow:0 2px 16px rgba(0,0,0,0.7);}}
.subtitle{{font-size:36px;opacity:0.8;letter-spacing:1px;}}
</style></head>
<body><div class=\"slide\" id=\"capture\"><div class=\"image-pane\"></div><div class=\"overlay\"></div><div class=\"content\"><div class=\"title\">{title}</div><div class=\"subtitle\">{subtitle}</div></div></div></body></html>
"""

def get_image_url(query, api_key):
    """使用Pexels API搜索图片并返回URL。"""
    if not api_key or api_key == "YOUR_API_KEY_HERE":
        return "https://images.pexels.com/photos/1181345/pexels-photo-1181345.jpeg"
    headers = {"Authorization": api_key}
    url = f"https://api.pexels.com/v1/search?query={query}&per_page=1&orientation=landscape"
    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        data = response.json()
        if data.get("photos"):
            return data["photos"][0]["src"]["large2x"]
    except requests.exceptions.RequestException as e:
        print(f"网络错误: {e}")
    return "https://images.pexels.com/photos/1181345/pexels-photo-1181345.jpeg"

def create_pdf_presentation(json_data_str, output_filename):
    """通过生成网页并转换为矢量PDF，创建高质量的演示文稿。"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"所有文件将被保存在 '{OUTPUT_DIR}' 文件夹中。")

    print("正在初始化虚拟浏览器...")
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1280,720")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    data = json.loads(json_data_str)
    temp_files = []
    pdf_merger = PdfWriter()
    total_slides = len(data.get('slides', []))

    for i, slide_data in enumerate(data.get('slides', [])):
        print(f"正在处理第 {i+1}/{total_slides} 页: {slide_data.get('title', 'Slide')}")
        slide_type = slide_data.get("type", "content")
        
        # 1. 选择模板并填充内容
        if slide_type == "title":
            html_content = HTML_TITLE_TEMPLATE.format(title=slide_data.get("title"), subtitle=slide_data.get("subtitle"))
        elif slide_type == "section_header":
            html_content = HTML_SECTION_TEMPLATE.format(number=slide_data.get("number"), title=slide_data.get("title"))
        elif slide_type == "end":
            image_url = get_image_url(slide_data.get("search_term"), PEXELS_API_KEY)
            html_content = HTML_END_TEMPLATE.format(title=slide_data.get("title"), subtitle=slide_data.get("subtitle"), image_url=image_url)
        else: # 默认为内容页
            image_url = get_image_url(slide_data.get("search_term"), PEXELS_API_KEY)
            points_html = "".join([f"<li>{p}</li>" for p in slide_data.get("points", [])])
            footer_text = f"{data.get('global_footer', '')} | {i+1}"
            html_content = HTML_CONTENT_TEMPLATE.format(title=slide_data.get("title"), points_html=points_html, image_url=image_url, footer_text=footer_text)

        # 2. 创建临时HTML文件
        html_filename = os.path.join(OUTPUT_DIR, f"temp_slide_{i}.html")
        with open(html_filename, "w", encoding="utf-8") as f:
            f.write(html_content)
        temp_files.append(html_filename)

        # 3. 使用Selenium打印为PDF
        driver.get("file:///" + os.path.abspath(html_filename))
        time.sleep(1) # 等待渲染
        pdf_data_b64 = driver.execute_cdp_cmd("Page.printToPDF", {"printBackground": True, "width": 1280/96, "height": 720/96})['data']
        
        # 4. 将单页PDF保存到临时文件并添加到合并器
        pdf_filename = os.path.join(OUTPUT_DIR, f"temp_page_{i}.pdf")
        with open(pdf_filename, "wb") as f:
            f.write(base64.b64decode(pdf_data_b64))
        temp_files.append(pdf_filename)
        pdf_merger.append(pdf_filename)

    # 5. 保存合并后的最终PDF
    final_pdf_path = os.path.join(OUTPUT_DIR, output_filename)
    print(f"\n正在合并所有页面并保存到 {final_pdf_path}...")
    with open(final_pdf_path, "wb") as f:
        pdf_merger.write(f)
    pdf_merger.close()
    driver.quit()

    # 6. 清理临时文件
    print("正在清理临时文件...")
    for f in temp_files:
        try:
            os.remove(f)
        except OSError as e:
            print(f"清理文件 {f} 失败: {e}")
            
    print(f"\n🎉 恭喜！排版精美的PDF演示文稿 '{final_pdf_path}' 已成功创建！")

if __name__ == '__main__':
    # 填充详细内容和图片关键词的json结构
    # 自动生成100页苹果风格AI主题内容
    slides = []
    # 封面
    slides.append({"type": "title", "title": "人工智能的未来", "subtitle": "机遇、挑战与展望"})
    # 章节页
    slides.append({"type": "section_header", "number": "第一部分", "title": "AI基础与发展"})
    # 生成内容页（1-30）
    for i in range(1, 31):
        slides.append({
            "type": "content",
            "title": f"AI基础知识 {i}",
            "search_term": "artificial intelligence concept minimalism",
            "points": [f"AI基础知识点{i}：简明扼要的描述，突出重点。", f"相关应用场景{i}，展示AI如何改变世界。"]
        })
    slides.append({"type": "section_header", "number": "第二部分", "title": "AI行业应用"})
    # 生成内容页（31-70）
    for i in range(31, 71):
        slides.append({
            "type": "content",
            "title": f"AI行业应用 {i-30}",
            "search_term": "AI industry application minimalism",
            "points": [f"行业应用{i-30}：AI在该领域的创新与变革。", f"实际案例{i-30}，突出AI带来的价值。"]
        })
    slides.append({"type": "section_header", "number": "第三部分", "title": "AI前沿与未来"})
    # 生成内容页（71-98）
    for i in range(71, 99):
        slides.append({
            "type": "content",
            "title": f"AI前沿探索 {i-70}",
            "search_term": "AI future technology minimalism",
            "points": [f"前沿方向{i-70}：AI技术的最新突破。", f"未来展望{i-70}，描绘AI的无限可能。"]
        })
    # 总结页
    slides.append({"type": "content", "title": "AI总结与展望", "search_term": "AI summary minimalism", "points": ["AI已成为推动社会进步的核心动力。", "未来AI将更加智能、普惠与安全。"]})
    # 结束页
    slides.append({"type": "end", "title": "谢谢观看", "subtitle": "共同迎接智能新时代", "search_term": "future technology city skyline minimalism"})
    json_content = json.dumps({"global_footer": "人工智能的未来：机遇与挑战", "slides": slides}, ensure_ascii=False, indent=2)
    create_pdf_presentation(json_content, "人工智能的未来.pdf")

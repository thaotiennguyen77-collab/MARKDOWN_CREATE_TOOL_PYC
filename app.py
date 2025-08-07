import os
import re
import datetime
import random
import traceback
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import zipfile
import io

app = Flask(__name__)
CORS(app)

FIXED_APPS = [
    "91视频", "台湾Swag", "Porn高清", "Pornbest", "Pornhub", "tiktok成人版",
    "50度灰", "黄瓜视频", "香蕉视频", "樱桃视频", "蜜桃视频", "幸福宝",
    "中国X站", "果冻传媒", "麻豆传媒", "天美传媒", "精东传媒", "大象传媒",
]

FIXED_URLS = [
    "最新在线地址", "入口地址发布页", "当前可用地址", "永久地址", "官方最新地址",
    "在线观看入口", "免费观看入口", "不用付费观看", "无广告在线播放", "高清视频免费看",
]

TEMPLATES = [
    """# {title}

🎉 欢迎来到 {app}{url} 官方导航页！

尊敬的用户您好，为了帮助您更轻松地找到{app}的最新地址，我们特意设立了本页面。无论您是第一次访问，还是老用户寻找稳定入口，都可以在这里快速找到可用链接。

关键词：{keywords_text}  
更新时间：{date}  

以下是我们的可用访问入口，建议您立即收藏：

- [主站入口]({domain})  
- [备用链接一]({domain})  
- [备用链接二]({domain})  

📌 本站优势：
- 实时更新地址，避免失效
- 支持所有设备访问
- 无需登录，永久免费

遇到无法访问时，请尝试以下方法：
- 刷新页面
- 切换浏览器或使用隐私模式
- 尝试使用 VPN 或代理工具

感谢您的支持，我们将不断优化服务质量，带来更流畅的访问体验！
""",

    """# {title}

🔥 {app} - {url} 最新可用地址合集！

随着网络环境不断变化，为确保您可以顺利访问{app}的优质内容，我们特别制作了本页面，帮助您获取每日最新可用地址。

关键词：{keywords_text}  
页面更新日期：{date}  

🔗 当前可访问地址：
- [主入口]({domain})  
- [备用入口一]({domain})  
- [备用入口二]({domain})  

为什么选择我们？
- 极速访问，不限速
- 多线路保障，永不失联
- 内容丰富，定期更新
- 无广告干扰，观看更专注

🔐 温馨提示：本平台不收集任何用户信息，完全匿名、安全。请务必将本页面加入收藏夹，避免迷路！

如遇问题，欢迎反馈，我们将第一时间修复！
""",

    """# {title}

🚀 {app} 官方跳转入口说明 - {url}

您好，欢迎使用由我们维护的 {app} 导航服务页面。本页提供的所有链接，均为最新、稳定可用的访问地址。

关键词聚合：{keywords_text}  
日期：{date}  

🌍 可用地址一览：
- [主站点]({domain})  
- [备用站点A]({domain})  
- [备用站点B]({domain})  

📢 使用建议：
- 移动端推荐使用 Chrome 浏览器；
- WiFi 网络下如有屏蔽现象，请尝试 4G/5G 或 VPN；
- 使用无痕模式可避免缓存干扰；

本页地址为【唯一导航入口】，无任何弹窗、木马或捆绑行为。请您放心使用，并及时收藏本页面以备不时之需。

我们承诺每日检测并替换失效链接，确保您永远可以第一时间访问所需内容。
""",

    """# {title}

🌟 {app} 永久导航页 - {url}

感谢您一直以来对{app}的支持与信赖。为了解决用户频繁因域名被封无法访问的问题，我们推出了本页面，用于集中展示每日可用地址。

关键词：{keywords_text}  
最后更新：{date}  

🔗 请从以下任一链接访问平台内容：
- [主域名]({domain})  
- [备用1]({domain})  
- [备用2]({domain})  

💡 技术说明：
我们的系统会自动检测访问状态，一旦发现失效，会自动替换为新地址。无需用户操作，轻松无忧。

❤️ 我们重视每一位用户的浏览体验：
- 页面无广告；
- 加载速度快；
- 无需安装任何软件；
- 完全匿名不留痕。

建议您将此页设为书签，或转发给朋友一起收藏。让我们共同建立一个安全、快捷的访问环境！
""",

    """# {title}

📘 {app} - {url} 全新访问指南

网络限制越来越多，想要稳定访问{app}，本页面将是您最可靠的助手。

关键词聚焦：{keywords_text}  
更新时间：{date}  

推荐访问链接（建议全部收藏）：
- [主入口地址]({domain})
- [备用镜像1]({domain})
- [备用镜像2]({domain})

🧩 访问受限怎么办？
1. 先尝试刷新或更换浏览器；
2. 尝试关闭代理工具；
3. 尝试启用手机数据流量；
4. 若问题依旧，请使用 VPN 工具。

🎯 小贴士：
- 页面每日更新，可用率 99.99%
- 不记录、不追踪您的任何行为
- 所有资源均为超清播放

感谢您的支持与耐心使用，我们致力于为您打造最畅快的访问体验！
"""
]

OUTPUT_FOLDER = "generated_markdown_files"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def log_error(msg):
    with open("error.log", "a", encoding="utf-8") as f:
        f.write(msg + "\n")

def sanitize_filename(text):
    return re.sub(r'[\\/*?:"<>|]', "_", text)

def generate_md_content(app, url, keyword_list, suffix):
    title = f"{app}-{url}-{'-'.join(keyword_list)}-{suffix}"
    date_now = datetime.datetime.now().strftime("%Y-%m-%d")
    keywords_text = "，".join(keyword_list)
    subdomain = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=3))
    domain_link = f"https://{subdomain}.zaixianyule.top/"

    template = random.choice(TEMPLATES)
    content = template.format(
        title=title,
        app=app,
        url=url,
        keywords_text=keywords_text,
        suffix=suffix,
        date=date_now,
        domain=domain_link
    )
    return content

@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"msg": "pong"})

@app.route("/", methods=["GET"])
def root_home():
    return jsonify({"msg": "Welcome to the Flask API. Use /ping to test or /generate to create markdown files."}), 200

@app.route("/generate", methods=["POST"])
def generate_markdown_files():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Missing JSON body"}), 400

        keywords = data.get("keywords")
        cy = data.get("cy")

        if not keywords or not isinstance(keywords, list) or not all(isinstance(k, str) for k in keywords):
            return jsonify({"error": "Invalid or missing 'keywords' list"}), 400
        if not cy or not isinstance(cy, str):
            return jsonify({"error": "Invalid or missing 'cy' string"}), 400

        today_str = datetime.datetime.now().strftime("%m%d")
        suffix = f"{today_str}{cy}|881比鸭"

        used_filenames = set()
        created_files = []

        app_fixed = random.choice(FIXED_APPS)
        url_fixed = random.choice(FIXED_URLS)

        selected_keywords = random.sample(keywords, min(5, len(keywords)))

        memory_zip = io.BytesIO()
        with zipfile.ZipFile(memory_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            for idx, keyword in enumerate(selected_keywords, start=1):
                safe_keyword = sanitize_filename(keyword)
                filename_prefix = f"{idx:03d}-"
                filename = f"{filename_prefix}{safe_keyword}.md"

                other_keywords = random.sample(keywords, min(2, len(keywords)))
                if keyword not in other_keywords:
                    keyword_list = [keyword] + other_keywords
                else:
                    keyword_list = other_keywords

                content = generate_md_content(app_fixed, url_fixed, keyword_list, suffix)
                zf.writestr(filename, content)
                created_files.append(filename)

        memory_zip.seek(0)
        zip_filename = f"Tool-MARKDOWN-TCTL-PYC-{datetime.datetime.now().strftime('%Y-%m-%d')}.zip"

        return send_file(
            memory_zip,
            as_attachment=True,
            download_name=zip_filename,
            mimetype="application/zip"
        )

    except Exception as e:
        err = f"Error: {e}\n{traceback.format_exc()}"
        log_error(err)
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Server running on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)

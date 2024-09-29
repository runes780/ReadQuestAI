import os
import requests
import feedparser
import time
import re
# 设置 RSS 源地址
rss_url = "https://feedx.net/rss/economistp.xml"



# 设置 API 端点
api_endpoint = "https://cfcus02.opapi.win/v1/chat/completions"

# 设置 API 密钥
api_key = "sk-7GZdGfvB2f439d09Ec50T3BlbKFJ249013a543a34bf0806D"


# 设置文件夹路径
raw_folder = "raw_articles"
processed_folder = "processed_articles"

# 创建文件夹（如果不存在）
os.makedirs(raw_folder, exist_ok=True)
os.makedirs(processed_folder, exist_ok=True)

# 获取 RSS 源内容
feed = feedparser.parse(rss_url)

# 获取文章总数
total_articles = len(feed.entries)

# 遍历每篇文章
for index, entry in enumerate(feed.entries, start=1):
    title = entry.title
    content = entry.summary

    # 处理文章标题，将其转换为合法的文件名
    title = re.sub(r'[<>:"/\\|?*]', '_', title)

    # 检查文章是否已经处理过
    raw_file_path = os.path.join(raw_folder, f"{title}.txt")
    processed_file_path = os.path.join(processed_folder, f"{title}.txt")

    if os.path.exists(processed_file_path):
        print(f"文章 '{title}' 已经处理过，跳过。")
        continue

    # 保存原始文章内容
    with open(raw_file_path, "w", encoding="utf-8") as file:
        file.write(content)

    # 构建请求数据
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "You are a professional english teacher"},
            {"role": "user", "content": f"modify content below to make reading comprehension text(within 350 words),make four quetions and each give four answer to chose from and give right answer：\n\n{content}"}
        ],
        "temperature": 0.7
    }

    # 发送请求到 API
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    response = requests.post(api_endpoint, json=data, headers=headers)

    # 检查响应状态码
    if response.status_code == 200:
        result = response.json()
        summary = result["choices"][0]["message"]["content"].strip()

        # 保存处理后的内容
        with open(processed_file_path, "w", encoding="utf-8") as file:
            file.write(summary)

        print(f"文章 '{title}' 处理完成。")
    else:
        print(f"请求失败，状态码：{response.status_code}")

    # 显示处理进度
    progress = index / total_articles * 100
    print(f"处理进度：{progress:.2f}%")

    # 询问是否继续处理
    if index < total_articles:
        choice = input("按 Enter 继续处理下一篇文章，输入 'q' 退出：")
        if choice.lower() == 'q':
            break

    # 添加延迟以避免超过 API 速率限制
    time.sleep(1)
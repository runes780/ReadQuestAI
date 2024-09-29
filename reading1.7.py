import os
import re
import time
import feedparser
from bs4 import BeautifulSoup
import requests

# 设置 RSS 源地址
rss_urls = [
    "https://feedx.net/rss/economist.xml",
    "https://feedx.net/rss/economistp.xml",
    "https://feedx.net/rss/newyorker.xml",
    "https://feedx.net/rss/hbr.xml",
    "https://www.npr.org/rss/rss.php?id=1002",
    "https://www.npr.org/rss/rss.php?id=1019",
]

# 设置 API 端点
api_endpoint = "http://localhost:11434/api"

# 设置文件夹路径
raw_folder = "raw_articles"
processed_folder = "processed_articles"

# 创建文件夹(如果不存在)
os.makedirs(raw_folder, exist_ok=True)
os.makedirs(processed_folder, exist_ok=True)

def process_segment_with_model(segment, base_url="http://127.0.0.1:11434/api"):
    headers = {"Content-Type": "application/json"}
    data = {
        "model": "llama3:8b-instruct-q8_0",
        "prompt": f"你是专业翻译，请将'原文'文本完整的，忠实的翻译为中文：  原文：{segment}  全文翻译（只输出翻译内容）：",
        "stream": False
    }

    try:
        # 发送 POST 请求到本地模型 API
        response = requests.post(f"{base_url}/generate", headers=headers, json=data)
        if response.status_code == 200:
            response_data = response.json()
            # 根据实际响应结构获取翻译文本
            if 'response' in response_data:
                translated_text = response_data['response'].strip()
                return translated_text
            else:
                print("Response does not contain 'response'.")
                return segment
        else:
            print(f"Request failed with status code: {response.status_code}")
            return segment
    except Exception as e:
        print(f"Failed to translate segment: {e}")
        return segment

for rss_url in rss_urls:
    print(f"Processing RSS feed: {rss_url}")
    feed = feedparser.parse(rss_url)
    total_articles = len(feed.entries)

    for index, entry in enumerate(feed.entries, start=1):
        title = entry.title
        content = entry.summary

        # Check if the content is a summary or full article
        if len(content) < 1000:  # Adjust the threshold as needed
            # Content is likely a summary, fetch the full article
            article_url = entry.link
            response = requests.get(article_url)
            if response.status_code == 200:
                article_html = response.text
                soup = BeautifulSoup(article_html, "html.parser")
                article_content = soup.find("article")  # Adjust the selector as needed
                if article_content:
                    content = article_content.get_text()
                else:
                    print(f"Could not find article content for '{title}', using summary.")
            else:
                print(f"Failed to fetch full article for '{title}', using summary.")

        # Process article title to make it a valid file name
        title = re.sub(r'[<>:"/\\|?*]', '_', title)

        # Check if the article has already been processed
        raw_file_path = os.path.join(raw_folder, f"{title}.md")
        processed_file_path = os.path.join(processed_folder, f"{title}.md")

        if os.path.exists(raw_file_path):
            print(f"Article '{title}' has already been saved in the raw folder, skipping.")
            continue

        if os.path.exists(processed_file_path):
            print(f"Article '{title}' has already been processed, skipping.")
            continue

        # Save the original article content
        with open(raw_file_path, "w", encoding="utf-8") as file:
            file.write(f"# {title}\n\n{content}")

        # Get partial content for screening
        soup = BeautifulSoup(content, "html.parser")
        text_content = soup.get_text()
        partial_content = text_content[:100]  # Take the first 100 characters as partial content
        print(f"Processing article '{title}' ...{partial_content}...")

        # Build request data for article screening
        screening_data = {
            "model": "llama3:8b-instruct-q8_0",
            "prompt": f"你是一个英语考试设计者。审查文章标题以生成阅读理解问题。允许各种话题，但排除战争和政治。仅关注标题。如果合适，请回复'合适'并提供问题潜力评分（1-10分，如'合适，8'）。如果不合适，请回复'不合适'并简要解释。\n\n文章标题: {title}",
            "stream": False
        }

        # Send screening request to API
        screening_response = requests.post(f"{api_endpoint}/generate", headers={"Content-Type": "application/json"}, json=screening_data)

        # Check screening request response status code
        if screening_response.status_code == 200:
            screening_result = screening_response.json()
            screening_output = screening_result["response"].strip()
            print(f"Article '{title}' screening result: {screening_output}")
            if "不合适" in screening_output:
                print(f"Article '{title}' is unsuitable for generating reading comprehension questions, skipping.")
                continue

            if "合适" in screening_output:
                score_match = re.search(r'\d+', screening_output)
                if score_match:
                    suitability_score = int(score_match.group())
                    if suitability_score < 6:
                        print(f"Article '{title}' suitability score is {suitability_score}, lower than the threshold, skipping.")
                        continue
                else:
                    print(f"Article '{title}' screening result does not contain a score, assuming it's suitable.")

                # Build request data for generating reading comprehension questions
                generation_data = {
                    "model": "llama3:8b-instruct-q8_0",
                    "prompt": f"你是一名专业的英语教师。请修改以下内容以创建一个阅读理解文本（350字以内）。生成四个问题，每个问题有四个答案选项，并提供每个问题的正确答案：\n\n{content}",
                    "stream": False
                }

                # Send request to generate reading comprehension questions to API
                generation_response = requests.post(f"{api_endpoint}/generate", headers={"Content-Type": "application/json"}, json=generation_data)

                # Check reading comprehension generation request response status code
                if generation_response.status_code == 200:
                    generation_result = generation_response.json()
                    reading_comprehension = generation_result["response"].strip()
                    print(f"Article '{title}' reading comprehension questions generated successfully.")
                    # Save processed content
                    with open(processed_file_path, "w", encoding="utf-8") as file:
                        file.write(f"# {title}\n\n{reading_comprehension}")

                    print(f"Article '{title}' processed.")
                else:
                    print(f"Reading comprehension generation request failed, status code: {generation_response.status_code}")
            else:
                print(f"Article '{title}' screening result format is incorrect, skipping.")
                continue
        else:
            print(f"Screening request failed, status code: {screening_response.status_code}")
            continue
        
    # Display processing progress
        progress = index / total_articles * 100
        print(f"Processing progress: {progress:.2f}%")
        
        # Ask if you want to continue processing
        if index < total_articles:
            choice = input("Press Enter to process the next article, or enter 'q' to exit: ")
            if choice.lower() == 'q':
                break
        
        # Add delay to avoid exceeding API rate limit
        time.sleep(1)

    print(f"RSS feed '{rss_url}' processed.")
    print("="*50)  # Add a separator line to distinguish different RSS feeds

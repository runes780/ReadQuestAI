import os
import requests
import feedparser
import time
import re
# 设置 RSS 源地址
rss_urls = [
    "https://feedx.net/rss/economist.xml",
    "https://feedx.net/rss/economistp.xml",
    "https://feedx.net/rss/newyorker.xml",
    "https://feedx.net/rss/hbr.xml",
    "https://www.npr.org/rss/rss.php?id=1002",
]

from bs4 import BeautifulSoup



# 设置 API 端点
api_endpoint = API-ENDPOINT

# 设置 API 密钥
api_key = API-KEY

# 设置文件夹路径
raw_folder = "raw_articles"
processed_folder = "processed_articles"

# 创建文件夹(如果不存在)
os.makedirs(raw_folder, exist_ok=True)
os.makedirs(processed_folder, exist_ok=True)





for rss_url in rss_urls:
    print(f"Processing RSS feed: {rss_url}")
    feed = feedparser.parse(rss_url)
    total_articles = len(feed.entries)

    for index, entry in enumerate(feed.entries, start=1):
        title = entry.title
        content = entry.summary

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
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "You are an English exam designer."},
                {"role": "user", "content": f"Review article titles for generating reading comprehension questions. Allow various topics, but exclude war and politics. Focus on the title only. If suitable, reply 'Suitable' and provide a score from 1-10 for question potential (e.g., 'Suitable, 8'). If not, reply 'Unsuitable' and explain briefly.\n\nArticle Title: {title}"}
            ],
            "temperature": 0.7
        }

        # Send screening request to API
        screening_response = requests.post(api_endpoint, json=screening_data, headers={"Authorization": f"Bearer {api_key}"})

        # Check screening request response status code
        if screening_response.status_code == 200:
            screening_result = screening_response.json()
            screening_output = screening_result["choices"][0]["message"]["content"].strip()
            print(f"Article '{title}' screening result: {screening_output}")
            if "Unsuitable" in screening_output:
                print(f"Article '{title}' is unsuitable for generating reading comprehension questions, skipping.")
                continue

            if "Suitable" in screening_output:
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
                    "model": "gpt-3.5-turbo",
                    "messages": [
                        {"role": "system", "content": "You are a professional English teacher."},
                        {"role": "user", "content": f"Please modify the content below to create a reading comprehension text (within 350 words). Generate four questions, each with four answer choices, and provide the correct answer for each question:\n\n{content}"}
                    ],
                    "temperature": 0.7
                }

                # Send request to generate reading comprehension questions to API
                generation_response = requests.post(api_endpoint, json=generation_data, headers={"Authorization": f"Bearer {api_key}"})

                # Check reading comprehension generation request response status code
                if generation_response.status_code == 200:
                    generation_result = generation_response.json()
                    reading_comprehension = generation_result["choices"][0]["message"]["content"].strip()
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

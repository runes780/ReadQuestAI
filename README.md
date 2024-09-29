# ReadQuestAI


**ReadQuestAI** 是一个从多个 RSS 源获取文章，并使用 AI 模型自动生成阅读理解问题的项目。该项目会筛选并处理文章，同时排除政治和战争主题，并通过本地 API 模型生成高质量的阅读理解问题。

## 功能
- 从多个 RSS 源抓取文章
- 使用 AI 模型筛选文章主题
- 自动生成阅读理解问题及答案
- 忽略政治和战争相关内容

## 安装与使用

1. 克隆仓库：
   ```bash
   git clone https://github.com/runes780/ReadQuestAI.git
   ```

2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

3. 配置 `.env` 文件：
   在项目根目录创建 `.env` 文件，并添加你的 API 端点和其他敏感信息：
   ```bash
   API_KEY=your-api-key
   ```

4. 运行项目：
   ```bash
   python main.py
   ```

## 项目结构

```bash
├── raw_articles/          # 原始文章文件
├── processed_articles/     # 处理后的文章文件
├── main.py                # 主脚本
├── .gitignore             # Git 忽略规则
├── README.md              # 项目说明
└── requirements.txt       # 依赖列表
```

## API 设置

本项目依赖一个本地部署的 AI 模型 API，请确保在 `main.py` 中正确配置 API 端点。

## 贡献

欢迎提交 issue 和 pull request！

---
name: wechat-publisher
description: 自动化将本地内容发布为微信公众号图文。用于将 Markdown/HTML 转草稿并提交发布（draft+freepublish），当你需要把文章自动发布到公众号时触发。
license: Proprietary. LICENSE.txt has complete terms
---

# 公众号自动发布

## 概览

- 支持将本地 Markdown/HTML 内容发布为公众号图文
- 通过官方草稿与发布接口：draft/add → freepublish/submit
- 需要服务号并具备相关接口权限及有效 access_token
- **实现方式**：纯 Python 脚本（位于 `scripts/` 目录）
- **不支持**：Node.js 或其他语言实现

## 依赖管理

**CRITICAL - Always Check Dependencies Before Execution**

This skill requires Python packages: `requests` and `markdown`. Before executing any script, verify and install dependencies.

### Automatic Dependency Check (Recommended)

**Always run this check before executing Python scripts:**

```bash
# Quick check and auto-install if missing
python3 -c "import requests, markdown" 2>/dev/null || pip3 install requests markdown
```

### Virtual Environment Approach (Best Practice)

For better isolation, use a virtual environment in the workspace:

```bash
# Create and activate venv if it doesn't exist
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
else
    source .venv/bin/activate
fi

# Then execute your script
python3 scripts/publish_article.py --title "..." --content-file "..." --cover "..."
```

### Error Handling

If you encounter `ModuleNotFoundError: No module named 'requests'` or `'markdown'`:

1. **Immediate fix**: Run `pip3 install requests markdown`
2. **Better approach**: Create virtual environment as shown above
3. **Verify**: Run `python3 -c "import requests, markdown"` to confirm
4. **Retry**: Execute the original command again

### Manual Installation (if needed)

```bash
# Install from requirements.txt
pip3 install -r requirements.txt

# Or install individually
pip3 install requests markdown
```

## 配置说明

凭证获取优先级（从高到低）：

1. **配置文件**（推荐）：`assets/wechat_config.json`
   - 通过助手设置界面配置（点击助手卡片上的齿轮图标）
   - 格式：`{"appId": "YOUR_APP_ID", "appSecret": "YOUR_APP_SECRET"}`

2. **环境变量**：
   - `WECHAT_MP_APPID` + `WECHAT_MP_APPSECRET`（使用稳定凭证）
   - 或 `WECHAT_MP_ACCESS_TOKEN`（直接使用 token）

3. **IP 白名单**：
   - 服务器出口 IP 需加入公众号平台"开发者中心"IP 白名单
   - 否则会出现凭证或接口调用失败

## 快速开始

### Step 1: Ensure Dependencies (REQUIRED)

```bash
# Check and install dependencies
python3 -c "import requests, markdown" 2>/dev/null || pip3 install requests markdown
```

### Step 2: Publish Article

发布单图文（news）：

```bash
python scripts/publish_article.py \
  --title "标题" \
  --author "作者" \
  --digest "摘要" \
  --content-file ./article.md \
  --cover ./cover.jpg
```

**Note**: Always check dependencies before running scripts to avoid errors.

## 草稿

- 新增草稿（支持 news 与 newspic）

```bash
python scripts/add_draft.py \
  --type news \
  --title "标题" \
  --author "作者" \
  --digest "摘要" \
  --content-file ./article.md \
  --content-source-url https://example.com/source \
  --cover ./cover.jpg \
  --pic-crop-235-1 0.1945_0_1_0.5236 \
  --pic-crop-1-1 0.166454_0_0.833545_1
```

```bash
python scripts/add_draft.py \
  --type newspic \
  --title "图片消息标题" \
  --content-file ./desc.md \
  --image ./img1.jpg --image ./img2.jpg \
  --cover-crop 1_1:0.166454,0,0.833545,1 \
  --product-key YOUR_PRODUCT_KEY
```

- 草稿列表

```bash
python scripts/list_drafts.py --offset 0 --count 10 --no-content 1
```

## 行为与约束

- 自动上传封面为永久素材并生成 thumb_media_id
- 自动解析并上传内容中的本地图片为有效 URL
- 成功后返回发布任务信息（publish_id、msg_data_id）
- Markdown 内容会自动转换为 HTML 格式

## 内容创作指南

### 标题要求

- **吸引力**：标题必须极具吸引力，能够激发读者的点击欲望，但避免过度标题党
- **长度**：控制在 64 字节以内（约 32 个汉字）
- **风格**：可以使用适量的 emoji，语气要符合公众号读者的阅读习惯

### 内容要求

- **结构清晰**：使用 Markdown 格式，包含引人入胜的导语、清晰的小标题、总结或引导互动的结语
- **排版**：适当使用加粗强调重点，列表项使用无序或有序列表，段落之间保留空行
- **语气**：专业但亲切，避免过于生硬的官方腔调
- **长度**：内容详实，字数适中（通常 800-2000 字，视主题而定）

## 发布管理

- 发布草稿

```bash
python scripts/publish_draft.py --media-id MEDIA_ID
```

- 发布列表

```bash
python scripts/list_publish.py --offset 0 --count 10 --no-content 0
```

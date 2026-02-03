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

### 配置文件

**推荐方式**：通过 `assets/wechat_config.json` 统一配置（可通过助手设置界面配置）

配置文件格式：

```json
{
  "appId": "YOUR_APP_ID",
  "appSecret": "YOUR_APP_SECRET"
}
```

**字段说明**：

1. **appId** 和 **appSecret**（必填）：
   - 微信公众号的 AppID 和 AppSecret
   - 用于获取 access_token 调用微信 API

### 凭证获取优先级

**微信公众号凭证**（从高到低）：

1. **配置文件**：`assets/wechat_config.json` 中的 `appId` 和 `appSecret`
2. **环境变量**：`WECHAT_MP_APPID` + `WECHAT_MP_APPSECRET`
3. **环境变量**：`WECHAT_MP_ACCESS_TOKEN`（直接使用 token）

**Unsplash 图片搜索凭证**（从高到低）：

1. **配置文件**：`assets/wechat_config.json` 中的 `unsplashAccessKey`
2. **环境变量**：`UNSPLASH_ACCESS_KEY`

### 其他要求

- **IP 白名单**：
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

#### 图片配置说明

系统支持多种图片来源，**优先级从高到低**：

1. **用户提供的封面图片**
   - 使用 `--cover` 参数指定本地图片路径
   - 支持 JPG、PNG 等常见格式
   - 图片会自动上传到微信服务器
   - 适合需要精确控制封面样式的场景

2. **用户素材库**（推荐）
   - 使用 `--material-dir` 参数指定素材库目录路径
   - 系统会从目录中选择图片作为封面和正文配图
   - 支持 JPG、JPEG、PNG、GIF、BMP、WEBP 格式
   - 自动防止重复使用同一张图片
   - 适合有自己素材库的用户

3. **自动搜索匹配的图片**（默认，无需 API Key）
   - 不提供 `--cover` 或 `--material-dir` 参数时自动触发
   - 系统会从文章标题和内容中提取关键词
   - 自动从免费图片源（Pexels + Lorem Picsum）获取高质量图片
   - 完全免费，无需任何 API Key 或配置
   - 智能防止封面和正文图片重复
   - 适合快速发布或没有现成素材的场景

**注意**：微信公众号的 news 类型文章必须包含封面图片，因此系统会自动确保至少有一张封面图（通过用户提供、素材库或自动搜索）

#### 使用示例

**方式 1：使用用户提供的封面图片**

```bash
python scripts/publish_article.py \
  --title "AI 正在重塑职场：5 种你必须知道的工作方式变革" \
  --author "作者名" \
  --digest "探索人工智能如何改变我们的工作方式" \
  --content-file ./article.md \
  --cover ./my_cover.jpg
```

**方式 2：使用用户素材库**

```bash
python scripts/publish_article.py \
  --title "AI 正在重塑职场：5 种你必须知道的工作方式变革" \
  --author "作者名" \
  --digest "探索人工智能如何改变我们的工作方式" \
  --content-file ./article.md \
  --material-dir ./my_materials
```

系统会自动：

1. 从素材库目录中选择图片作为封面
2. 为正文章节选择不同的图片（自动防止重复）
3. 上传图片到微信服务器
4. 如果素材库图片不足，自动回退到搜索模式

**方式 3：自动搜索匹配的图片（默认）**

```bash
python scripts/publish_article.py \
  --title "AI 正在重塑职场：5 种你必须知道的工作方式变革" \
  --author "作者名" \
  --digest "探索人工智能如何改变我们的工作方式" \
  --content-file ./article.md
```

系统会自动：

1. 从文章标题和内容中提取关键词（如 "artificial intelligence", "workplace"）
2. 从免费图片源（Pexels + Lorem Picsum）搜索匹配的高质量图片
3. 智能防止封面和正文使用相同关键词（避免重复图片）
4. 下载并上传为封面和正文配图
5. 发布成功后自动删除本地下载的图片

#### 正文配图说明

系统会自动在文章正文中插入相关配图：

- **插入策略**：
  - 3-4 个章节：在第 2 个章节后插入 1 张图片
  - ≥5 个章节：在第 2 和第 4 个章节后各插入 1 张图片
- **关键词提取**：从每个章节的标题和内容中提取关键词
- **自动清理**：发布成功后自动删除所有下载的图片
- **禁用选项**：使用 `--no-content-images` 参数可禁用正文配图

**Note**: Always check dependencies before running scripts to avoid errors.

## 草稿管理

### 新增草稿

支持 news（图文消息）与 newspic（图片消息）两种类型。

#### 图片配置说明

与发布文章相同，草稿也支持多种图片来源（参见上文"图片配置说明"）。

#### 使用示例

**方式 1：使用用户提供的封面图片**

```bash
python scripts/add_draft.py \
  --type news \
  --title "AI 正在重塑职场：5 种你必须知道的工作方式变革" \
  --author "作者名" \
  --digest "探索人工智能如何改变我们的工作方式" \
  --content-file ./article.md \
  --content-source-url https://example.com/source \
  --cover ./my_cover.jpg
```

可选参数（封面裁剪）：

```bash
  --pic-crop-235-1 0.1945_0_1_0.5236 \
  --pic-crop-1-1 0.166454_0_0.833545_1
```

**方式 2：使用用户素材库**

```bash
python scripts/add_draft.py \
  --type news \
  --title "AI 正在重塑职场：5 种你必须知道的工作方式变革" \
  --author "作者名" \
  --digest "探索人工智能如何改变我们的工作方式" \
  --content-file ./article.md \
  --material-dir ./my_materials
```

**方式 3：自动搜索图片（默认）**

```bash
python scripts/add_draft.py \
  --type news \
  --title "AI 正在重塑职场：5 种你必须知道的工作方式变革" \
  --author "作者名" \
  --digest "探索人工智能如何改变我们的工作方式" \
  --content-file ./article.md
```

**方式 4：禁用正文配图**

```bash
python scripts/add_draft.py \
  --type news \
  --title "标题" \
  --content-file ./article.md \
  --cover ./my_cover.jpg \
  --no-content-images
```

使用 `--no-content-images` 参数可以只使用封面图片，不在正文中插入配图。

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

- **智能图片处理**（优先级从高到低）：
  1. **用户提供的封面**：通过 `--cover` 参数指定本地图片路径
  2. **用户素材库**：通过 `--material-dir` 参数指定素材库目录，系统自动选择图片
     - 自动防止重复使用同一张图片（封面和正文配图不重复）
     - 如果素材库图片不足，自动回退到搜索模式
  3. **自动搜索匹配**（默认）：从文章内容提取关键词并搜索匹配的高质量图片
     - 智能防止封面和正文使用相同关键词（避免重复图片）
     - 完全免费，无需任何 API Key
  - **注意**：微信公众号的 news 类型文章必须包含封面图片
  - 自动上传封面为永久素材并生成 thumb_media_id
- **正文配图**：
  - 默认自动在正文章节中插入相关配图
  - 使用 `--no-content-images` 参数可禁用正文配图（仅保留封面）
  - 支持素材库和自动搜索两种模式
- **图片处理**：
  - 自动解析并上传内容中的本地图片为有效 URL
  - 支持 Markdown 中的图片引用自动转换
  - 发布成功后自动删除下载的临时图片
- **内容转换**：
  - Markdown 内容会自动转换为 HTML 格式
- **发布结果**：
  - 成功后返回发布任务信息（publish_id、msg_data_id）

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

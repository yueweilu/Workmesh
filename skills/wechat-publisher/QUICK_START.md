# 快速开始指南

## 🚀 5 分钟上手微信公众号自动发布

### 第一步：配置凭证

编辑 `assets/wechat_config.json`：

```json
{
  "appId": "你的微信公众号AppID",
  "appSecret": "你的微信公众号AppSecret"
}
```

**获取方式**:

- 微信凭证: [微信公众平台](https://mp.weixin.qq.com/) → 开发 → 基本配置

### 第二步：创建文章

创建一个 Markdown 文件，例如 `my_article.md`：

```markdown
# 你的文章标题

这是文章的导语部分...

## 第一个小标题

文章内容...

## 第二个小标题

更多内容...
```

**提示**: 可以让 AI 助手根据 `assets/prompt.md` 的指引自动生成文章！

### 第三步：发布到草稿箱

#### 方式 A：使用自己的封面图片（推荐）

如果你有准备好的封面图片：

```bash
cd skills/wechat-publisher

python3 scripts/add_draft.py \
  --title "你的文章标题" \
  --author "作者名" \
  --digest "文章摘要（显示在列表中）" \
  --content-file ./my_article.md \
  --cover ./my_cover.jpg \
  --type news
```

#### 方式 B：自动搜索封面图片

如果没有封面图片，系统会自动搜索：

```bash
cd skills/wechat-publisher

python3 scripts/add_draft.py \
  --title "你的文章标题" \
  --author "作者名" \
  --digest "文章摘要（显示在列表中）" \
  --content-file ./my_article.md \
  --type news
```

**自动配图说明**:

- 省略 `--cover` 参数时，系统会自动根据文章标题和内容提取关键词
- 从免费图片源（Pexels + Lorem Picsum）搜索匹配的高质量封面图片
- 完全免费，无需任何 API Key 或配置
- 同时会在正文中插入 1-2 张相关配图（根据章节数量）
- 发布成功后自动删除本地下载的图片

### 第四步：在公众号后台发布

1. 登录 [微信公众平台](https://mp.weixin.qq.com/)
2. 进入"素材管理" → "草稿箱"
3. 找到刚刚添加的文章
4. 预览并发布

## 📝 完整示例

### 示例 1: 使用自己的封面图片（最佳实践）

```bash
python3 scripts/add_draft.py \
  --title "🚀 5个实用技巧，让你的工作效率翻倍！" \
  --author "效率专家" \
  --digest "从番茄工作法到时间管理，掌握这5个技巧让你事半功倍。" \
  --content-file ./articles/productivity.md \
  --cover ./images/productivity_cover.jpg \
  --type news
```

**优势**：

- 完全控制封面样式和品牌形象
- 不依赖外部 API，发布更快速
- 适合有设计团队或固定视觉风格的场景

### 示例 2: 自动搜索封面图片（快速发布）

```bash
python3 scripts/add_draft.py \
  --title "🚀 5个实用技巧，让你的工作效率翻倍！" \
  --author "效率专家" \
  --digest "从番茄工作法到时间管理，掌握这5个技巧让你事半功倍。" \
  --content-file ./articles/productivity.md \
  --type news
```

系统会自动：

1. 从标题提取关键词: "productivity efficiency work"
2. 使用 Unsplash API 搜索匹配的高质量图片
3. 下载并上传到微信服务器作为封面
4. 在正文第 2 和第 4 个章节插入相关配图
5. 添加到草稿箱
6. 发布成功后自动删除本地下载的图片

**优势**：

- 无需准备图片素材，节省时间
- 自动匹配高质量图片，视觉效果好
- 适合快速发布或个人博客场景

### 示例 3: 只用封面，不插入正文配图

```bash
python3 scripts/add_draft.py \
  --title "我的文章标题" \
  --author "作者" \
  --digest "文章摘要" \
  --content-file ./my_article.md \
  --cover ./my_cover.jpg \
  --no-content-images \
  --type news
```

**适用场景**：

- 文章已经包含了图片链接
- 希望保持纯文字风格
- 对正文排版有特殊要求

## 🎯 使用技巧

### 1. 让 AI 帮你写文章

在 Workmesh 中对话：

```
请根据 wechat-publisher skill 的 prompt.md 指引，
写一篇关于"如何提高工作效率"的文章，
保存为 productivity.md
```

AI 会自动：

- 生成吸引人的标题
- 撰写结构清晰的正文
- 使用合适的 Markdown 格式

### 2. 批量发布文章

创建一个脚本 `batch_publish.sh`：

```bash
#!/bin/bash

articles=(
  "article1.md:标题1:摘要1"
  "article2.md:标题2:摘要2"
  "article3.md:标题3:摘要3"
)

for item in "${articles[@]}"; do
  IFS=':' read -r file title digest <<< "$item"
  python3 scripts/add_draft.py \
    --title "$title" \
    --author "你的名字" \
    --digest "$digest" \
    --content-file "$file" \
    --type news
  echo "✅ $title 已添加到草稿箱"
  sleep 2
done
```

### 3. 查看草稿列表

```bash
python3 scripts/list_drafts.py
```

查看所有草稿的详细信息。

## ⚠️ 常见问题

### Q: 为什么会提示 "api unauthorized"？

A: 这通常出现在尝试使用 `publish_article.py` 或 `publish_draft.py` 时。这些接口需要认证的服务号权限。

**解决方案**: 使用 `add_draft.py` 添加到草稿箱，然后在公众号后台手动发布。

### Q: 图片搜索失败怎么办？

A: 可能的原因：

1. Unsplash API Key 未配置或无效
2. 网络连接问题
3. 关键词太具体，找不到匹配的图片

**解决方案**:

- 检查 `wechat_config.json` 中的 `unsplashAccessKey`
- 使用 `--cover` 参数手动指定封面图片

### Q: 如何自定义关键词映射？

A: 编辑 `scripts/util.py` 中的 `extract_keywords_from_content` 函数，在 `keyword_mapping` 字典中添加你的映射：

```python
keyword_mapping = {
    'ai': 'artificial intelligence',
    '你的中文词': 'your english keywords',
    ...
}
```

## 🎉 开始使用

现在你已经掌握了所有基础知识，开始创作你的第一篇文章吧！

```bash
cd skills/wechat-publisher
python3 scripts/add_draft.py \
  --title "我的第一篇 AI 自动发布文章" \
  --author "我" \
  --digest "这是我使用 AI 助手自动发布的第一篇文章！" \
  --content-file ./test_article.md \
  --type news
```

祝你发布愉快！🎊

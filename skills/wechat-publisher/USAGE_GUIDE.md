# 微信公众号发布助手 - 使用指南

## 图片配置模式

系统支持 4 种图片配置模式，优先级从高到低：

### 1. 用户提供的封面图片

适合需要精确控制封面样式的场景。

```bash
python3 scripts/add_draft.py \
  --type news \
  --title "文章标题" \
  --content-file article.md \
  --cover my_cover.jpg
```

**特点**：

- ✅ 完全控制封面样式
- ✅ 支持 JPG、PNG 等常见格式
- ✅ 自动上传到微信服务器

### 2. 用户素材库（推荐）

适合有自己素材库的用户，系统会自动选择图片。

```bash
python3 scripts/add_draft.py \
  --type news \
  --title "文章标题" \
  --content-file article.md \
  --material-dir ./my_materials
```

**特点**：

- ✅ 自动从素材库选择图片
- ✅ 自动防止重复使用同一张图片
- ✅ 支持 JPG、JPEG、PNG、GIF、BMP、WEBP 格式
- ✅ 如果素材库图片不足，自动回退到搜索模式
- ✅ 封面和正文配图不会重复

**素材库准备**：

```bash
# 创建素材库目录
mkdir -p my_materials

# 添加图片到素材库
cp your_images/*.jpg my_materials/
cp your_images/*.png my_materials/
```

### 3. 自动搜索图片（默认）

适合快速发布或没有现成素材的场景。

```bash
python3 scripts/add_draft.py \
  --type news \
  --title "文章标题" \
  --content-file article.md
```

**特点**：

- ✅ 完全免费，无需任何 API Key
- ✅ 自动从文章标题和内容提取关键词
- ✅ 从免费图片源（Pexels + Lorem Picsum）获取高质量图片
- ✅ 智能防止封面和正文使用相同关键词（避免重复图片）
- ✅ 自动清理下载的临时图片

**工作流程**：

1. 从文章标题和内容中提取关键词
2. 将中文关键词映射为英文（支持多词短语）
3. 从 Pexels 搜索匹配的图片
4. 如果 Pexels 失败，回退到 Lorem Picsum
5. 下载并上传到微信服务器
6. 发布成功后自动删除本地图片

### 4. 纯文本模式

适合纯文字内容或后续手动添加图片的场景。

```bash
python3 scripts/add_draft.py \
  --type news \
  --title "文章标题" \
  --content-file article.md \
  --no-images
```

**特点**：

- ✅ 不配任何图片
- ⚠️ 仅支持草稿模式（add_draft.py）
- ⚠️ 不支持直接发布（publish_article.py）

## 正文配图

系统默认会在正文中自动插入相关配图。

### 插入策略

- **3-4 个章节**：在第 2 个章节后插入 1 张图片
- **≥5 个章节**：在第 2 和第 4 个章节后各插入 1 张图片

### 关键词提取

- 从每个章节的 H2 标题和内容中提取关键词
- 自动防止与封面使用相同关键词
- 支持中文到英文的智能映射

### 禁用正文配图

如果只想使用封面图片，不在正文中插入配图：

```bash
python3 scripts/add_draft.py \
  --type news \
  --title "文章标题" \
  --content-file article.md \
  --cover my_cover.jpg \
  --no-content-images
```

## 完整示例

### 示例 1：使用素材库发布文章

```bash
# 准备素材库
mkdir -p my_materials
cp ~/Pictures/article_images/*.jpg my_materials/

# 发布文章
python3 scripts/publish_article.py \
  --title "人工智能的未来发展趋势" \
  --author "张三" \
  --digest "探索 AI 技术的最新进展和未来方向" \
  --content-file article.md \
  --material-dir my_materials
```

### 示例 2：自动搜索图片创建草稿

```bash
python3 scripts/add_draft.py \
  --type news \
  --title "区块链技术在金融领域的应用" \
  --author "李四" \
  --digest "深入分析区块链如何改变金融行业" \
  --content-file blockchain_article.md
```

### 示例 3：纯文本草稿

```bash
python3 scripts/add_draft.py \
  --type news \
  --title "纯文字文章" \
  --content-file text_only.md \
  --no-images
```

## 测试所有模式

运行测试脚本验证所有功能：

```bash
./test_all_modes.sh
```

测试脚本会依次测试：

1. ✅ 纯文本模式
2. ✅ 自动搜索图片模式
3. ✅ 用户提供封面图片模式
4. ✅ 用户素材库模式
5. ✅ 禁用正文配图模式

## 常见问题

### Q: 素材库图片不够怎么办？

A: 系统会自动回退到搜索模式，从免费图片源获取图片。

### Q: 如何防止图片重复？

A: 系统使用两种机制防止重复：

1. **关键词去重**：封面和正文使用不同的关键词
2. **素材库去重**：已使用的图片不会再次选择

### Q: 自动搜索的图片质量如何？

A: 系统从 Pexels（高质量免费图片库）和 Lorem Picsum（占位图服务）获取图片，质量有保证。

### Q: 可以混合使用不同模式吗？

A: 可以！例如：

- 封面使用用户提供的图片，正文使用自动搜索
- 封面使用素材库，正文使用自动搜索（如果素材库图片不足）

### Q: 如何查看创建的草稿？

A: 使用草稿列表命令：

```bash
python3 scripts/list_drafts.py --count 10
```

## 技术细节

### 关键词提取算法

1. **标题权重**：标题中的词频 × 5
2. **首段权重**：第一段中的词频 × 2
3. **常用词过滤**：自动过滤"的"、"是"、"在"等常用词
4. **中英文映射**：支持多词短语映射（如"人工智能" → "artificial intelligence"）

### 图片来源

1. **Pexels**：高质量免费图片库，无需 API Key
2. **Lorem Picsum**：占位图服务，作为备用方案

### 防重复机制

1. **used_keywords 集合**：跟踪已使用的关键词
2. **used_material_images 集合**：跟踪已使用的素材库图片
3. **智能回退**：如果无法找到新关键词或新图片，自动回退到其他模式

## 更多信息

- 详细 API 文档：[SKILL.md](./SKILL.md)
- 项目说明：[README.md](./README.md)
- 配置说明：查看 `assets/wechat_config.json`

# 微信公众号发布助手 / WeChat Publisher

自动化将本地 Markdown/HTML 内容发布为微信公众号图文。

## 快速开始

### 1. 安装依赖

```bash
cd skills/wechat-publisher
pip3 install -r requirements.txt
```

### 2. 配置凭证

**方式 A：通过助手设置界面（推荐）**

1. 在助手列表中找到"微信公众号助手"
2. 点击齿轮图标打开设置
3. 输入你的 AppID 和 AppSecret
4. 保存配置

**方式 B：手动编辑配置文件**

编辑 `assets/wechat_config.json`：

```json
{
  "appId": "YOUR_APP_ID",
  "appSecret": "YOUR_APP_SECRET"
}
```

**方式 C：使用环境变量**

```bash
export WECHAT_MP_APPID="YOUR_APP_ID"
export WECHAT_MP_APPSECRET="YOUR_APP_SECRET"
```

### 3. 发布文章

```bash
python3 scripts/publish_article.py \
  --title "我的第一篇文章" \
  --author "作者名" \
  --digest "文章摘要" \
  --content-file examples/article.md \
  --cover examples/cover.jpg
```

## 功能特性

- ✅ 支持 Markdown 自动转 HTML
- ✅ 自动上传本地图片到微信服务器
- ✅ 自动创建草稿并发布
- ✅ 支持封面图片上传
- ✅ 支持评论设置
- ✅ 完整的草稿管理功能

## 文件结构

```
wechat-publisher/
├── SKILL.md              # Skill 定义文件
├── README.md             # 本文件
├── requirements.txt      # Python 依赖
├── assets/
│   ├── wechat_config.json  # 配置文件
│   └── prompt.md           # 内容创作指南
├── examples/
│   ├── article.md          # 示例文章
│   ├── cover.jpg           # 示例封面
│   └── cover.png
└── scripts/
    ├── util.py             # 工具函数
    ├── publish_article.py  # 发布文章（草稿+群发）
    ├── add_draft.py        # 创建草稿
    ├── publish_draft.py    # 发布草稿
    ├── list_drafts.py      # 列出草稿
    └── list_publish.py     # 列出已发布内容
```

## 注意事项

1. **服务号要求**：需要微信服务号，订阅号不支持
2. **接口权限**：需要开通草稿箱和发布接口权限
3. **IP 白名单**：服务器 IP 需要加入公众号平台的 IP 白名单
4. **图片格式**：支持 JPG、PNG 格式，建议封面尺寸 900x500

## 常见问题

### Q: 提示"缺少访问凭证"？

A: 请检查配置文件或环境变量是否正确设置。

### Q: 提示"稳定凭证获取失败"？

A: 请检查 AppID 和 AppSecret 是否正确，以及 IP 是否在白名单中。

### Q: 图片上传失败？

A: 请确保图片格式正确（JPG/PNG），大小不超过 2MB。

### Q: 如何只创建草稿不发布？

A: 使用 `add_draft.py` 脚本而不是 `publish_article.py`。

## 更多信息

详细文档请参考 [SKILL.md](./SKILL.md)

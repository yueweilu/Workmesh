---
name: wechat-mp
description: 自动化将本地内容发布为微信公众号图文。用于将 Markdown/HTML 转草稿并提交发布（draft+freepublish），当你需要把文章自动发布到公众号时触发。
license: Proprietary. LICENSE.txt has complete terms
---

# 公众号自动发布

## 概览

- 支持将本地 Markdown/HTML 内容发布为公众号图文
- 通过官方草稿与发布接口：draft/add → freepublish/submit
- 需要服务号并具备相关接口权限及有效 access_token

## 快速开始

-
- 环境变量：
  - WECHAT_MP_ACCESS_TOKEN 或配置稳定凭证：
  - WECHAT_MP_USE_STABLE_TOKEN=1、WECHAT_MP_APPID、WECHAT_MP_APPSECRET
- 发布单图文（news）

```bash
python scripts/publish_article.py \
  --title "标题" \
  --author "作者" \
  --digest "摘要" \
  --content-file ./article.md \
  --cover ./cover.jpg
```

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
- 服务器出口 IP 需加入公众号平台“开发者中心”IP白名单，否则会出现凭证或接口调用失败

## 发布管理

- 发布草稿

```bash
python scripts/publish_draft.py --media-id MEDIA_ID
```

- 发布列表

```bash
python scripts/list_publish.py --offset 0 --count 10 --no-content 0
```

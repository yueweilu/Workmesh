#!/usr/bin/env python3
import sys
import argparse
import json
from pathlib import Path
from util import get_access_token, load_content, replace_local_images_with_wechat_urls, upload_permanent_image
import requests


def parse_cover_crop(values):
    items = []
    for v in values:
        ratio, coords = v.split(":", 1)
        x1, y1, x2, y2 = coords.split(",")
        items.append({"ratio": ratio, "x1": x1, "y1": y1, "x2": x2, "y2": y2})
    return {"crop_percent_list": items} if items else None


def upload_images_as_material(token, images):
    ids = []
    for path in images:
        ids.append(upload_permanent_image(token, path))
    return [{"image_media_id": mid} for mid in ids]


def add_draft(token, article):
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
    payload = {"articles": [article]}
    r = requests.post(url, data=json.dumps(payload, ensure_ascii=False).encode("utf-8"), headers={"Content-Type": "application/json"}, timeout=30).json()
    if r.get("errcode", 0) != 0 or "media_id" not in r:
        print(json.dumps(r, ensure_ascii=False))
        sys.exit(1)
    print(r["media_id"])


def main():
    p = argparse.ArgumentParser(prog="add_draft")
    p.add_argument("--type", choices=["news", "newspic"], required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--author", default="")
    p.add_argument("--digest", default="")
    p.add_argument("--content-file", required=True)
    p.add_argument("--content-source-url", default="")
    p.add_argument("--cover", help="仅news类型需要封面")
    p.add_argument("--open-comment", action="store_true")
    p.add_argument("--fans-only-comment", action="store_true")
    p.add_argument("--pic-crop-235-1", default="")
    p.add_argument("--pic-crop-1-1", default="")
    p.add_argument("--image", action="append", default=[])
    p.add_argument("--cover-crop", action="append", default=[])
    p.add_argument("--product-key", default="")
    args = p.parse_args()

    token = get_access_token()
    html = load_content(args.content_file)
    html = replace_local_images_with_wechat_urls(token, html, Path(args.content_file).parent)

    base = {
        "title": args.title,
        "author": args.author,
        "digest": args.digest,
        "content": html,
        "content_source_url": args.content_source_url,
        "need_open_comment": 1 if args.open_comment else 0,
        "only_fans_can_comment": 1 if args.fans_only_comment else 0,
    }

    if args.type == "news":
        if not args.cover:
            print("缺少封面: --cover")
            sys.exit(1)
        base["article_type"] = "news"
        base["thumb_media_id"] = upload_permanent_image(token, args.cover)
        if args.pic_crop_235_1:
            base["pic_crop_235_1"] = args.pic_crop_235_1
        if args.pic_crop_1_1:
            base["pic_crop_1_1"] = args.pic_crop_1_1
    else:
        base["article_type"] = "newspic"
        image_list = upload_images_as_material(token, args.image)
        base["image_info"] = {"image_list": image_list}
        cover_info = parse_cover_crop(args.cover_crop)
        if cover_info:
            base["cover_info"] = cover_info
        if args.product_key:
            base["product_info"] = {"footer_product_info": {"product_key": args.product_key}}

    add_draft(token, base)


if __name__ == "__main__":
    main()


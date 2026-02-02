#!/usr/bin/env python3
import sys
import argparse
import json
from pathlib import Path
from util import get_access_token, load_content, replace_local_images_with_wechat_urls, upload_permanent_image


def add_draft(access_token, article_obj):
    import requests
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={access_token}"
    payload = {"articles": [article_obj]}
    r = requests.post(url, data=json.dumps(payload, ensure_ascii=False).encode("utf-8"), headers={"Content-Type": "application/json"}, timeout=30).json()
    if r.get("errcode", 0) != 0 or "media_id" not in r:
        print(json.dumps(r, ensure_ascii=False))
        sys.exit(1)
    return r["media_id"]


def publish_draft(access_token, media_id):
    import requests
    url = f"https://api.weixin.qq.com/cgi-bin/freepublish/submit?access_token={access_token}"
    payload = {"media_id": media_id}
    r = requests.post(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}, timeout=30).json()
    if r.get("errcode", 0) != 0:
        print(json.dumps(r, ensure_ascii=False))
        sys.exit(1)
    return r


def main():
    parser = argparse.ArgumentParser(prog="publish_article")
    parser.add_argument("--title", required=True)
    parser.add_argument("--author", default="")
    parser.add_argument("--digest", default="")
    parser.add_argument("--content-file", required=True)
    parser.add_argument("--content-source-url", default="")
    parser.add_argument("--cover", required=True)
    parser.add_argument("--open-comment", action="store_true")
    parser.add_argument("--fans-only-comment", action="store_true")
    args = parser.parse_args()

    token = get_access_token()
    content_raw = load_content(args.content_file)
    content_final = replace_local_images_with_wechat_urls(token, content_raw, Path(args.content_file).parent)
    thumb_media_id = upload_permanent_image(token, args.cover)

    article = {
        "title": args.title,
        "author": args.author,
        "digest": args.digest,
        "content": content_final,
        "content_source_url": args.content_source_url,
        "thumb_media_id": thumb_media_id,
        "need_open_comment": 1 if args.open_comment else 0,
        "only_fans_can_comment": 1 if args.fans_only_comment else 0,
    }

    media_id = add_draft(token, article)
    result = publish_draft(token, media_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

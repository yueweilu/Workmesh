#!/usr/bin/env python3
import sys
import argparse
import json
from pathlib import Path
from util import (
    get_access_token, 
    load_content, 
    replace_local_images_with_wechat_urls, 
    upload_permanent_image,
    search_and_download_cover_image,
    extract_keywords_from_content,
    insert_images_into_content,
    select_image_from_material_dir
)


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
    parser.add_argument("--cover", default="")
    parser.add_argument("--open-comment", action="store_true")
    parser.add_argument("--fans-only-comment", action="store_true")
    parser.add_argument("--no-content-images", action="store_true", help="不在正文中插入图片")
    parser.add_argument("--material-dir", help="用户素材库目录，优先使用该目录中的图片")
    args = parser.parse_args()

    token = get_access_token()
    content_raw = load_content(args.content_file)
    content_final = replace_local_images_with_wechat_urls(token, content_raw, Path(args.content_file).parent)
    
    downloaded_images = []
    used_keywords = set()
    used_material_images = set()
    
    if args.cover:
        cover_path = args.cover
        print(f"使用用户提供的封面图片: {cover_path}")
    elif args.material_dir:
        print(f"从素材库选择封面图片: {args.material_dir}")
        try:
            cover_path = select_image_from_material_dir(args.material_dir, used_material_images)
            print(f"✓ 已选择素材库图片: {Path(cover_path).name}")
        except ValueError as e:
            print(f"× 素材库选择失败: {str(e)}")
            print("回退到自动搜索模式...")
            keywords = extract_keywords_from_content(content_raw, used_keywords=used_keywords)
            print(f"提取的关键词: {keywords}")
            cover_path = search_and_download_cover_image(keywords, Path(args.content_file).parent)
            downloaded_images.append(cover_path)
            print(f"已下载封面图片: {cover_path}")
    else:
        print("未提供封面图片，正在根据文章内容自动搜索...")
        keywords = extract_keywords_from_content(content_raw, used_keywords=used_keywords)
        print(f"提取的关键词: {keywords}")
        cover_path = search_and_download_cover_image(keywords, Path(args.content_file).parent)
        downloaded_images.append(cover_path)
        print(f"已下载封面图片: {cover_path}")
    
    if not args.no_content_images:
        print("\n正在为正文插入配图...")
        if args.material_dir:
            content_final = insert_images_into_content(
                token, content_final, Path(args.content_file).parent, downloaded_images,
                used_keywords=used_keywords, material_dir=args.material_dir,
                used_material_images=used_material_images
            )
        else:
            content_final = insert_images_into_content(
                token, content_final, Path(args.content_file).parent, downloaded_images,
                used_keywords=used_keywords
            )
    
    thumb_media_id = upload_permanent_image(token, cover_path)

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
    
    if downloaded_images:
        print(f"\n清理本地下载的图片...")
        for img_path in downloaded_images:
            try:
                Path(img_path).unlink()
                print(f"✓ 已删除: {Path(img_path).name}")
            except Exception as e:
                print(f"× 删除失败 {Path(img_path).name}: {str(e)}")


if __name__ == "__main__":
    main()

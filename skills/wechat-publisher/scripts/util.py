import os
import json
import mimetypes
from pathlib import Path
import requests


def get_access_token():
    use_stable = os.getenv("WECHAT_MP_USE_STABLE_TOKEN", "").lower() in {"1", "true", "yes"}
    appid = os.getenv("WECHAT_MP_APPID", "")
    secret = os.getenv("WECHAT_MP_APPSECRET", "")
    if use_stable and appid and secret:
        url = "https://api.weixin.qq.com/cgi-bin/stable_token"
        payload = {"grant_type": "client_credential", "appid": appid, "secret": secret}
        r = requests.post(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}, timeout=15).json()
        token = r.get("access_token", "")
        if token:
            return token
        else:
            msg = json.dumps(r, ensure_ascii=False)
            raise RuntimeError(f"稳定凭证获取失败: {msg}")
    token = os.getenv("WECHAT_MP_ACCESS_TOKEN", "")
    if not token:
        raise RuntimeError("缺少访问凭证")
    return token


def convert_markdown_to_html(text):
    try:
        import markdown
        return markdown.markdown(text, extensions=["extra"])
    except Exception:
        return "<p>" + "</p><p>".join(line for line in text.splitlines()) + "</p>"


def load_content(path):
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(str(path))
    data = p.read_text(encoding="utf-8")
    if p.suffix.lower() in [".md", ".markdown"]:
        return convert_markdown_to_html(data)
    return data


def upload_permanent_image(access_token, image_path):
    url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={access_token}&type=image"
    with open(image_path, "rb") as f:
        files = {"media": (Path(image_path).name, f, mimetypes.guess_type(image_path)[0] or "application/octet-stream")}
        r = requests.post(url, files=files, timeout=30).json()
    if r.get("errcode", 0) != 0 or "media_id" not in r:
        raise RuntimeError(json.dumps(r, ensure_ascii=False))
    return r["media_id"]


def upload_content_image(access_token, image_path):
    url = f"https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={access_token}"
    with open(image_path, "rb") as f:
        files = {"media": (Path(image_path).name, f, mimetypes.guess_type(image_path)[0] or "application/octet-stream")}
        r = requests.post(url, files=files, timeout=30).json()
    if r.get("errcode", 0) != 0 or "url" not in r:
        raise RuntimeError(json.dumps(r, ensure_ascii=False))
    return r["url"]


def replace_local_images_with_wechat_urls(access_token, content_html, base_dir):
    import re
    def repl(match):
        src = match.group(1).strip()
        if src.startswith("http://") or src.startswith("https://") or src.startswith("data:"):
            return match.group(0)
        local_path = Path(base_dir, src).resolve()
        if not local_path.exists():
            return match.group(0)
        url = upload_content_image(access_token, str(local_path))
        return match.group(0).replace(src, url)
    pattern = re.compile(r'<img[^>]*src=["\']([^"\']+)["\']', re.IGNORECASE)
    return pattern.sub(repl, content_html)

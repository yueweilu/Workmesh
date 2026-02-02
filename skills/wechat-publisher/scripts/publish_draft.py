#!/usr/bin/env python3
import sys
import argparse
import json
import requests
from util import get_access_token


def main():
    p = argparse.ArgumentParser(prog="publish_draft")
    p.add_argument("--media-id", required=True)
    args = p.parse_args()

    token = get_access_token()
    url = f"https://api.weixin.qq.com/cgi-bin/freepublish/submit?access_token={token}"
    payload = {"media_id": args.media_id}
    r = requests.post(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}, timeout=30).json()
    print(json.dumps(r, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()


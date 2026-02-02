#!/usr/bin/env python3
import sys
import argparse
import json
import requests
from util import get_access_token


def main():
    p = argparse.ArgumentParser(prog="list_publish")
    p.add_argument("--offset", type=int, default=0)
    p.add_argument("--count", type=int, default=10)
    p.add_argument("--no-content", type=int, default=0)
    args = p.parse_args()

    token = get_access_token()
    url = f"https://api.weixin.qq.com/cgi-bin/freepublish/batchget?access_token={token}"
    payload = {"offset": args.offset, "count": args.count, "no_content": args.no_content}
    r = requests.post(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}, timeout=30).json()
    print(json.dumps(r, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()


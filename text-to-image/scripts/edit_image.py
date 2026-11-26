#!/usr/bin/env python3
"""Edit images through Alibaba Cloud Bailian (DashScope) qwen-image models."""

import argparse
import base64
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

BASE = "https://dashscope.aliyuncs.com/api/v1"
QWEN_SYNC_URL = f"{BASE}/services/aigc/multimodal-generation/generation"
DEFAULT_MODEL = "qwen-image-3.0-pro"
MAX_BYTES = 10 * 1024 * 1024


def die(message, code=1):
    print(f"Error: {message}", file=sys.stderr)
    raise SystemExit(code)


def request_json(url, key, payload, timeout):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        try:
            j = json.loads(body)
            die(f"{j.get('code', 'HTTP ' + str(e.code))}: {j.get('message', body[:300])}")
        except json.JSONDecodeError:
            die(f"HTTP {e.code}: {body[:300]}")
    except urllib.error.URLError as e:
        die(f"网络错误: {e.reason}")


def to_data_uri(path):
    data = Path(path).expanduser().read_bytes()
    if len(data) > MAX_BYTES:
        die(f"图片超过 10MB: {path}")
    mime, _ = mimetypes.guess_type(str(path))
    mime = mime or "image/png"
    return f"data:{mime};base64," + base64.b64encode(data).decode()


def build_payload(args):
    content = [{"image": to_data_uri(img)} for img in args.image]
    content.append({"text": args.prompt})
    parameters = {"n": args.n}
    if args.size:
        parameters["size"] = args.size
    if args.seed is not None:
        parameters["seed"] = args.seed
    if args.watermark:
        parameters["watermark"] = True
    return {
        "model": args.model,
        "input": {"messages": [{"role": "user", "content": content}]},
        "parameters": parameters,
    }


def submit(payload, key, timeout):
    j = request_json(QWEN_SYNC_URL, key, payload, timeout)
    urls = []
    for choice in j.get("output", {}).get("choices", []):
        for item in choice.get("message", {}).get("content", []):
            if isinstance(item, dict) and item.get("image"):
                urls.append(item["image"])
    return urls


def unique_path(base):
    if not base.exists():
        return base
    i = 2
    while True:
        candidate = base.with_name(f"{base.stem}-v{i}{base.suffix}")
        if not candidate.exists():
            return candidate
        i += 1


def download(url, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "text-to-image-skill/1.0"})
    with urllib.request.urlopen(req, timeout=180) as resp:
        dest.write_bytes(resp.read())


def main():
    p = argparse.ArgumentParser(description="通过阿里云百炼 qwen-image 模型编辑图片")
    p.add_argument("--image", required=True, action="append", help="输入图片路径（1-3 张，重复传入）")
    p.add_argument("--prompt", required=True, help="编辑指令")
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--size", help="输出尺寸，如 1024*1024、2048*2048")
    p.add_argument("--n", type=int, default=1)
    p.add_argument("--seed", type=int)
    p.add_argument("--watermark", action="store_true")
    p.add_argument("-o", "--output", help="输出文件或目录（默认与输入同目录）")
    p.add_argument("--timeout", type=int, default=180)
    args = p.parse_args()

    if not 1 <= len(args.image) <= 3:
        die("输入图片须为 1–3 张")
    for img in args.image:
        if not Path(img).expanduser().is_file():
            die(f"输入图片不存在: {img}")
    if not 1 <= args.n <= 4:
        die("--n 须在 1–4 之间")

    key = os.environ.get("DASHSCOPE_API_KEY", "").strip()
    if not key:
        die("DASHSCOPE_API_KEY 未设置。按 ~/.agents/docs/models.md 中 providers.bailian.api_key_env 注入环境变量后重试。")

    urls = submit(build_payload(args), key, args.timeout)
    if not urls:
        die("接口未返回图片 URL")

    src = Path(args.image[0]).expanduser()
    if args.output:
        out = Path(args.output).expanduser()
        dir_target = out.is_dir() or args.output.endswith("/") or len(urls) > 1
    else:
        out, dir_target = src.parent, True

    suffix_ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    saved = []
    for i, url in enumerate(urls):
        if dir_target:
            out.mkdir(parents=True, exist_ok=True)
            part = f"-{i}" if len(urls) > 1 else ""
            target = unique_path(out / f"{src.stem}-edit-{suffix_ts}{part}.png")
        else:
            target = unique_path(out)
        download(url, target)
        saved.append(str(target))
    for path in saved:
        print(path)


if __name__ == "__main__":
    main()

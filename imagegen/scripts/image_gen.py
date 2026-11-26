#!/usr/bin/env python3
"""Generate or edit images through Alibaba Cloud Bailian (DashScope) qwen-image models."""

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
SYNC_URL = f"{BASE}/services/aigc/multimodal-generation/generation"
DEFAULT_MODEL = "qwen-image-3.0-pro"
DEFAULT_SIZE = "1024*1024"
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
    return f"data:{mime or 'image/png'};base64," + base64.b64encode(data).decode()


def submit(payload, key, timeout):
    j = request_json(SYNC_URL, key, payload, timeout)
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
    req = urllib.request.Request(url, headers={"User-Agent": "imagegen-skill/1.0"})
    with urllib.request.urlopen(req, timeout=180) as resp:
        dest.write_bytes(resp.read())


def save(urls, output_arg, stem):
    if output_arg:
        out = Path(output_arg).expanduser()
        dir_target = out.is_dir() or output_arg.endswith("/") or len(urls) > 1
    else:
        out, dir_target = Path("."), True
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    saved = []
    for i, url in enumerate(urls):
        if dir_target:
            out.mkdir(parents=True, exist_ok=True)
            part = f"-{i}" if len(urls) > 1 else ""
            target = unique_path(out / f"{stem}-{ts}{part}.png")
        else:
            target = unique_path(out)
        download(url, target)
        saved.append(str(target))
    return saved


def build_generate_payload(args):
    params = {
        "n": args.n,
        "size": args.size or DEFAULT_SIZE,
        "prompt_extend": not args.no_prompt_extend,
        "watermark": args.watermark,
    }
    if args.negative_prompt:
        params["negative_prompt"] = args.negative_prompt
    if args.seed is not None:
        params["seed"] = args.seed
    return {
        "model": args.model,
        "input": {"messages": [{"role": "user", "content": [{"text": args.prompt}]}]},
        "parameters": params,
    }


def build_edit_payload(args):
    content = [{"image": to_data_uri(img)} for img in args.image]
    content.append({"text": args.prompt})
    params = {"n": args.n}
    if args.size:
        params["size"] = args.size
    if args.seed is not None:
        params["seed"] = args.seed
    return {
        "model": args.model,
        "input": {"messages": [{"role": "user", "content": content}]},
        "parameters": params,
    }


def main():
    p = argparse.ArgumentParser(description="通过阿里云百炼 qwen-image 生成或编辑图片")
    sub = p.add_subparsers(dest="command", required=True)

    def common(sp):
        sp.add_argument("--model", default=DEFAULT_MODEL)
        sp.add_argument("--size", help="如 1024*1024、1536*1024")
        sp.add_argument("--n", type=int, default=1)
        sp.add_argument("--seed", type=int)
        sp.add_argument("-o", "--output", help="输出文件或目录（默认当前目录）")
        sp.add_argument("--timeout", type=int, default=180)

    gen = sub.add_parser("generate", help="文生图")
    gen.add_argument("prompt")
    gen.add_argument("--negative-prompt", default="")
    gen.add_argument("--no-prompt-extend", action="store_true")
    gen.add_argument("--watermark", action="store_true")
    common(gen)

    edit = sub.add_parser("edit", help="按指令编辑已有图片")
    edit.add_argument("--image", required=True, action="append", help="输入图片路径（1-3 张，重复传入）")
    edit.add_argument("--prompt", required=True, help="编辑指令")
    common(edit)

    args = p.parse_args()

    if args.command == "generate":
        if not 1 <= args.n <= 6:
            die("--n 须在 1–6 之间")
        payload = build_generate_payload(args)
        stem = "imagegen"
    else:
        if not 1 <= len(args.image) <= 3:
            die("输入图片须为 1–3 张")
        for img in args.image:
            if not Path(img).expanduser().is_file():
                die(f"输入图片不存在: {img}")
        if not 1 <= args.n <= 4:
            die("--n 须在 1–4 之间")
        payload = build_edit_payload(args)
        stem = Path(args.image[0]).expanduser().stem + "-edit"

    key = os.environ.get("DASHSCOPE_API_KEY", "").strip()
    if not key:
        die("DASHSCOPE_API_KEY 未设置。按 ~/.agents/docs/models.md 中 providers.bailian.api_key_env 注入环境变量后重试。")

    urls = submit(payload, key, args.timeout)
    if not urls:
        die("接口未返回图片 URL")

    for path in save(urls, args.output, stem):
        print(path)


if __name__ == "__main__":
    main()

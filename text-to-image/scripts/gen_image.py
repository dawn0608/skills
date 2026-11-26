#!/usr/bin/env python3
"""Generate images through Alibaba Cloud Bailian (DashScope)."""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

BASE = "https://dashscope.aliyuncs.com/api/v1"
SYNC_URL = f"{BASE}/services/aigc/multimodal-generation/generation"
ASYNC_SUBMIT_URL = f"{BASE}/services/aigc/text2image/image-synthesis"
TASK_URL = f"{BASE}/tasks"
DEFAULT_MODEL = "qwen-image-3.0-pro"
DEFAULT_SIZE = "1024*1024"


def die(message, code=1):
    print(f"Error: {message}", file=sys.stderr)
    raise SystemExit(code)


def request_json(url, key, payload=None, headers=None, timeout=120):
    hdrs = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    if headers:
        hdrs.update(headers)
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=hdrs)
    if data is None:
        req.method = "GET"
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


def build_payload(args):
    params = {"n": args.n}
    if args.size:
        params["size"] = args.size
    if args.negative_prompt:
        params["negative_prompt"] = args.negative_prompt
    if args.seed is not None:
        params["seed"] = args.seed
    params["watermark"] = args.watermark
    if args.model.startswith("qwen-image"):
        params["prompt_extend"] = not args.no_prompt_extend
    return {
        "model": args.model,
        "input": {"messages": [{"role": "user", "content": [{"text": args.prompt}]}]},
        "parameters": params,
    }


def submit_sync(payload, key, timeout):
    j = request_json(SYNC_URL, key, payload, timeout=timeout)
    urls = []
    for choice in j.get("output", {}).get("choices", []):
        for item in choice.get("message", {}).get("content", []):
            if isinstance(item, dict) and item.get("image"):
                urls.append(item["image"])
    return urls


def submit_async(payload, key, timeout):
    j = request_json(ASYNC_SUBMIT_URL, key, payload, headers={"X-DashScope-Async": "enable"}, timeout=timeout)
    task_id = j.get("output", {}).get("task_id")
    if not task_id:
        die(f"未获得 task_id: {json.dumps(j, ensure_ascii=False)[:300]}")
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(3)
        r = request_json(f"{TASK_URL}/{task_id}", key, timeout=60)
        output = r.get("output", {})
        status = output.get("task_status")
        if status == "SUCCEEDED":
            return [item["url"] for item in output.get("results", []) if item.get("url")]
        if status in ("FAILED", "CANCELED"):
            die(f"任务 {task_id} {status}: {json.dumps(r, ensure_ascii=False)[:400]}")
    die(f"任务 {task_id} 超时（{timeout}s）")


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
    p = argparse.ArgumentParser(description="通过阿里云百炼生成图片")
    p.add_argument("prompt")
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--size", default=DEFAULT_SIZE, help="如 1024*1024、1536*1024")
    p.add_argument("--n", type=int, default=1)
    p.add_argument("--negative-prompt", default="")
    p.add_argument("--seed", type=int)
    p.add_argument("--no-prompt-extend", action="store_true")
    p.add_argument("--watermark", action="store_true")
    p.add_argument("-o", "--output", default=".")
    p.add_argument("--timeout", type=int, default=180)
    args = p.parse_args()

    if not 1 <= args.n <= 6:
        die("--n 须在 1–6 之间")

    key = os.environ.get("DASHSCOPE_API_KEY", "").strip()
    if not key:
        die("DASHSCOPE_API_KEY 未设置。按 ~/.agents/docs/models.md 中 providers.bailian.api_key_env 注入环境变量后重试。")

    payload = build_payload(args)
    if args.model.startswith("qwen-image"):
        urls = submit_sync(payload, key, args.timeout)
    else:
        urls = submit_async(payload, key, args.timeout)
    if not urls:
        die("接口未返回图片 URL")

    out = Path(args.output).expanduser()
    dir_target = out.is_dir() or args.output.endswith("/") or len(urls) > 1
    stem = "imagegen-" + datetime.now().strftime("%Y%m%d-%H%M%S")
    saved = []
    for i, url in enumerate(urls):
        if dir_target:
            out.mkdir(parents=True, exist_ok=True)
            suffix = f"-{i}" if len(urls) > 1 else ""
            target = unique_path(out / f"{stem}{suffix}.png")
        else:
            target = unique_path(out)
        download(url, target)
        saved.append(str(target))
    for path in saved:
        print(path)


if __name__ == "__main__":
    main()

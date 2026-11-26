#!/usr/bin/env python3
"""Edit images through Alibaba Cloud Bailian (DashScope).

Two modes selected by --model:
- wanx* models: function-based editing (remove_watermark / super_resolution / ...)
- qwen-image-* models: instruction editing with 1-3 reference images
"""

import argparse
import base64
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

BASE = "https://dashscope.aliyuncs.com/api/v1"
SUBMIT_URL = f"{BASE}/services/aigc/image2image/image-synthesis"
QWEN_SYNC_URL = f"{BASE}/services/aigc/multimodal-generation/generation"
TASK_URL = f"{BASE}/tasks"
DEFAULT_MODEL = "wanx2.1-imageedit"
FUNCTIONS = [
    "remove_watermark",
    "super_resolution",
    "colorization",
    "expand",
    "stylization_all",
    "stylization_local",
    "description_edit",
    "description_edit_with_mask",
    "doodle",
    "control_cartoon_feature",
]
DEFAULT_PROMPTS = {
    "remove_watermark": "去除图片中的文字水印",
    "super_resolution": "高清放大，增强细节与清晰度",
    "colorization": "为黑白图片上色",
    "expand": "自然扩展画面",
    "stylization_all": "整体风格化处理",
    "stylization_local": "局部风格化处理",
    "doodle": "根据线稿生成图像",
    "control_cartoon_feature": "根据卡通形象生成图像",
}
MAX_BYTES = 10 * 1024 * 1024


def die(message, code=1):
    print(f"Error: {message}", file=sys.stderr)
    raise SystemExit(code)


def request_json(url, key, payload=None, headers=None, timeout=60):
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


def to_data_uri(path):
    data = Path(path).expanduser().read_bytes()
    if len(data) > MAX_BYTES:
        die(f"图片超过 10MB: {path}")
    mime, _ = mimetypes.guess_type(str(path))
    mime = mime or "image/png"
    return f"data:{mime};base64," + base64.b64encode(data).decode()


def build_wanx_payload(args):
    input_obj = {
        "function": args.function,
        "base_image_url": to_data_uri(args.image[0]),
        "prompt": args.prompt or DEFAULT_PROMPTS.get(args.function, ""),
    }
    if args.function == "description_edit_with_mask":
        if not args.mask:
            die("description_edit_with_mask 需要 --mask 参数")
        input_obj["mask_image_url"] = to_data_uri(args.mask)

    parameters = {"n": args.n}
    if args.seed is not None:
        parameters["seed"] = args.seed
    if args.watermark:
        parameters["watermark"] = True
    if args.function == "super_resolution":
        parameters["upscale_factor"] = args.upscale
    if args.function == "expand":
        parameters.update(
            top_scale=args.top_scale,
            bottom_scale=args.bottom_scale,
            left_scale=args.left_scale,
            right_scale=args.right_scale,
        )
    if args.function in ("stylization_all", "description_edit") and args.strength is not None:
        parameters["strength"] = args.strength
    if args.function == "doodle":
        parameters["is_sketch"] = args.is_sketch
    return {"model": args.model, "input": input_obj, "parameters": parameters}


def build_qwen_payload(args):
    content = [{"image": to_data_uri(img)} for img in args.image]
    content.append({"text": args.prompt})
    parameters = {"n": args.n}
    if args.size:
        parameters["size"] = args.size
    if args.watermark:
        parameters["watermark"] = True
    if args.seed is not None:
        parameters["seed"] = args.seed
    return {
        "model": args.model,
        "input": {"messages": [{"role": "user", "content": content}]},
        "parameters": parameters,
    }


def submit_wanx(payload, key, timeout):
    j = request_json(SUBMIT_URL, key, payload, headers={"X-DashScope-Async": "enable"})
    task_id = j.get("output", {}).get("task_id")
    if not task_id:
        die(f"未获得 task_id: {json.dumps(j, ensure_ascii=False)[:300]}")
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(3)
        r = request_json(f"{TASK_URL}/{task_id}", key)
        output = r.get("output", {})
        status = output.get("task_status")
        if status == "SUCCEEDED":
            return [item["url"] for item in output.get("results", []) if item.get("url")]
        if status in ("FAILED", "CANCELED"):
            die(f"任务 {task_id} {status}: {json.dumps(r, ensure_ascii=False)[:400]}")
    die(f"任务 {task_id} 超时（{timeout}s）")


def submit_qwen(payload, key, timeout):
    j = request_json(QWEN_SYNC_URL, key, payload, timeout=timeout)
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
    p = argparse.ArgumentParser(description="通过阿里云百炼编辑图片")
    p.add_argument("--image", required=True, action="append", help="输入图片路径（重复传入可传 1-3 张）")
    p.add_argument("--function", choices=FUNCTIONS, help="wanx 模型的功能函数；使用 qwen-image-* 指令编辑时省略")
    p.add_argument("--model", default=None, help=f"默认 {DEFAULT_MODEL}；可传 qwen-image-3.0-pro 走指令编辑")
    p.add_argument("--prompt", default="", help="编辑指令（qwen 模式必填）")
    p.add_argument("--mask", help="description_edit_with_mask 的遮罩图（白色=编辑区）")
    p.add_argument("--size", help="qwen 模式输出尺寸，如 1024*1024、1536*1024")
    p.add_argument("--upscale", type=int, default=2, help="super_resolution 放大倍数 1-4")
    p.add_argument("--strength", type=float, help="风格化/编辑强度 0-1")
    p.add_argument("--top-scale", type=float, default=1.0)
    p.add_argument("--bottom-scale", type=float, default=1.0)
    p.add_argument("--left-scale", type=float, default=1.0)
    p.add_argument("--right-scale", type=float, default=1.0)
    p.add_argument("--is-sketch", action="store_true", help="doodle 输入直接视为线稿")
    p.add_argument("--n", type=int, default=1)
    p.add_argument("--seed", type=int)
    p.add_argument("--watermark", action="store_true")
    p.add_argument("-o", "--output", help="输出文件或目录（默认与输入同目录）")
    p.add_argument("--timeout", type=int, default=180)
    args = p.parse_args()

    args.model = args.model or DEFAULT_MODEL
    model = args.model
    qwen_mode = model.startswith("qwen-image")

    for img in args.image:
        if not Path(img).expanduser().is_file():
            die(f"输入图片不存在: {img}")
    if qwen_mode:
        if not args.prompt:
            die("qwen 指令编辑需要 --prompt 描述编辑要求")
        if args.function:
            die("qwen 模式不使用 --function")
        if len(args.image) > 3:
            die("qwen 编辑最多 3 张输入图")
    else:
        if not args.function:
            die("wanx 模型需要 --function（如 remove_watermark、super_resolution）")
        if len(args.image) > 1:
            die("wanx 模型只接受 1 张输入图")
        if args.function == "super_resolution" and not 1 <= args.upscale <= 4:
            die("--upscale 须在 1–4 之间")
    if not 1 <= args.n <= 4:
        die("--n 须在 1–4 之间")

    key = os.environ.get("DASHSCOPE_API_KEY", "").strip()
    if not key:
        die("DASHSCOPE_API_KEY 未设置。按 ~/.agents/docs/models.md 中 providers.bailian.api_key_env 注入环境变量后重试。")

    if qwen_mode:
        urls = submit_qwen(build_qwen_payload(args), key, args.timeout)
    else:
        urls = submit_wanx(build_wanx_payload(args), key, args.timeout)
    if not urls:
        die("接口未返回图片 URL")

    src = Path(args.image[0]).expanduser()
    if args.output:
        out = Path(args.output).expanduser()
        dir_target = out.is_dir() or args.output.endswith("/") or len(urls) > 1
    else:
        out, dir_target = src.parent, True

    tag = args.function or "qwen-edit"
    suffix_ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    saved = []
    for i, url in enumerate(urls):
        if dir_target:
            out.mkdir(parents=True, exist_ok=True)
            part = f"-{i}" if len(urls) > 1 else ""
            target = unique_path(out / f"{src.stem}-{tag}-{suffix_ts}{part}.png")
        else:
            target = unique_path(out)
        download(url, target)
        saved.append(str(target))
    for path in saved:
        print(path)


if __name__ == "__main__":
    main()

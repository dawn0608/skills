---
name: text-to-image
description: 生成位图图像（照片、插画、海报、配图、贴图、商品图、UI 概念图等）。当用户要求画图、生成图片、配图、插图、海报、文生图，或说 generate image、make a picture、create an illustration 时使用。默认通过阿里云百炼 qwen-image-3.0-pro 生成。不适用于：SVG 图标、流程图、图表、简单几何示意图——这些应直接用代码（SVG/HTML/CSS/Mermaid）绘制。
allowed-tools: Bash(python3:*)
---

# text-to-image

通过阿里云百炼（DashScope）生成位图图像。

## 选择模型

| 场景 | 模型 |
| --- | --- |
| 默认：插画、海报、含中文文字的设计图 | `qwen-image-3.0-pro` |
| 4K 分辨率、品牌色控制、多图参考、角色一致性 | `wan2.7-image-pro` |
| 追求速度与成本、写实人像/产品图（仅文生图） | `z-image-turbo` |

## 用法

```bash
# 基本用法：输出到当前目录（imagegen-<时间戳>.png）
python3 scripts/gen_image.py "一只橘猫坐在窗台上晒太阳，水彩插画风格"

# 指定输出路径与尺寸
python3 scripts/gen_image.py "春天的城市海报" -o ~/Desktop/poster.png --size 1536*1024

# 一次生成多张（n=4），输出到目录
python3 scripts/gen_image.py "科技感抽象背景" -o ./assets/bg/ --n 4

# 排除元素与固定种子
python3 scripts/gen_image.py "极简产品包装" --negative-prompt "文字, 水印" --seed 42
```

参数：`--model`、`--size`（默认 `1024*1024`，总像素 512²–2048²）、`--n`（1–6）、`--negative-prompt`、`--seed`、`--no-prompt-extend`、`--watermark`、`-o`、`--timeout`。

## 密钥

仅从环境变量 `DASHSCOPE_API_KEY` 读取，缺失时脚本会报错并提示。按 `~/.agents/docs/models.md` 的 `providers.bailian.api_key_env` 注入测试进程：

```bash
DASHSCOPE_API_KEY="$KEY" python3 scripts/gen_image.py "..."
```

密钥不得进入脚本文件、命令回显、日志或回复。

## 保存规则

- 用户指定路径优先，否则输出到当前目录。
- 项目使用的图片移入工作区，不留在临时目录。
- 不覆盖已有文件：脚本遇到同名自动改用 `-v2`、`-v3`。
- 接口返回的图片 URL 仅 24 小时有效，脚本内置立即下载，无需手动处理。

## 图像编辑（去水印 / 超分 / 上色 / 扩图）

```bash
# 去文字水印
python3 scripts/edit_image.py --image 输入.png --function remove_watermark -o 输出.png

# 超分辨率：--upscale 2 放大 2 倍；--upscale 1 只增强清晰度不放大
python3 scripts/edit_image.py --image 低清.png --function super_resolution --upscale 2

# 黑白/老照片上色
python3 scripts/edit_image.py --image 老照片.jpg --function colorization

# 指令编辑（换背景、改元素、风格迁移）——推荐 qwen 模式
python3 scripts/edit_image.py --image 原图.png --model qwen-image-3.0-pro --prompt "把背景换成海边日落，保持主体不变"

# 扩图（四边各 1.0–2.0 倍）
python3 scripts/edit_image.py --image 构图过紧.png --function expand --left-scale 1.5 --right-scale 1.5
```

function 取值：`remove_watermark`、`super_resolution`、`colorization`、`expand`、`description_edit`、`description_edit_with_mask`（需 `--mask`）、`stylization_all`、`stylization_local`、`doodle`、`control_cartoon_feature`。

限制：输入图宽高 512–4096px、≤10MB；仅北京地域；异步任务约 5–15 秒，脚本已内置轮询与下载。只对有处理权的图片做去水印。

注意：`super_resolution` 输出上限约 1024px（实测 512→1024 放大有效，1024 输入不再放大）；需要更大尺寸时改用 `wan2.7-image-pro` 或本地插值放大。

实测对比（同图同指令）：`qwen-image-3.0-pro` 指令编辑能完整保留原图结构、输出 2048px；`wanx2.1-imageedit` 的 `description_edit` 易破坏画面结构（实测灯塔被改坏），**指令编辑一律用 qwen 模式**，wanx 仅用于其专用功能（去水印/超分/上色/扩图/线稿）。

## 提示词

提示词结构、中文文字渲染技巧与参数速查见 [references/prompting.md](references/prompting.md)。

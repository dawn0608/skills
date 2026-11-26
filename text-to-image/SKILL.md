---
name: text-to-image
description: 生成与编辑位图图像（照片、插画、海报、配图、贴图、商品图、UI 概念图等）。当用户要求画图、生成图片、配图、插图、海报、文生图，或说 generate image、make a picture、create an illustration 时使用；也用于编辑已有图片：去水印、提升清晰度、上色、换背景、风格迁移（edit image、remove watermark、upscale、colorize）。默认通过阿里云百炼 qwen-image-3.0-pro。不适用于：SVG 图标、流程图、图表、简单几何示意图——这些应直接用代码（SVG/HTML/CSS/Mermaid）绘制。
allowed-tools: Bash(python3:*)
---

# text-to-image

通过阿里云百炼（DashScope）生成与编辑位图图像。

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

## 图像编辑（qwen-image-3.0-pro）

```bash
# 去水印
python3 scripts/edit_image.py --image 图.png --prompt "去掉右下角的 WATERMARK 文字水印，自然补全，其余完全保持不变"

# 提升清晰度（生成式增强，可输出 2048）
python3 scripts/edit_image.py --image 低清.png --prompt "保持构图与内容完全不变，提升清晰度、增强细节" --size "2048*2048"

# 黑白/老照片上色
python3 scripts/edit_image.py --image 老照片.jpg --prompt "为黑白照片自然上色，保持原貌"

# 换背景、改元素、风格迁移
python3 scripts/edit_image.py --image 原图.png --prompt "把背景换成海边日落，保持主体不变"

# 多图参考（1–3 张，重复 --image）
python3 scripts/edit_image.py --image 人物.png --image 风格参考.png --prompt "把第一张图的人物画成第二张图的画风"
```

- 默认模型 `qwen-image-3.0-pro`；输入 1–3 张、单张 ≤10MB、建议 384–3072px；输出尺寸用 `--size` 指定（512²–2048²，默认 1024×1024）
- 指令中写明"保持原图构图与主体不变，仅修改 X"，效果更稳
- 实测：去水印、清晰度增强效果均优于旧 wanx2.1-imageedit 专用功能，且输出 2048px
- 只对有处理权的图片做去水印

## 提示词

提示词结构、中文文字渲染技巧与参数速查见 [references/prompting.md](references/prompting.md)。

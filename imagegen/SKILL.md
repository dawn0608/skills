---
name: imagegen
description: 生成或编辑位图图像（照片、插画、海报、配图、贴图、商品图、UI 概念图等）。当用户要求画图、生成图片、配图、插图、海报、文生图、改图、修图、编辑图片，或说 generate image、edit image、make a picture、create an illustration 时使用。通过阿里云百炼 qwen-image-3.0-pro 执行。不适用于：SVG 图标、流程图、图表、简单几何示意图——这些应直接用代码（SVG/HTML/CSS/Mermaid）绘制。
allowed-tools: Bash(python3:*)
---

# imagegen

通过阿里云百炼 qwen-image-3.0-pro 生成或编辑位图图像。

## When to use

- 生成新图像：插画、照片、海报、配图、素材、概念图、UI 概念稿
- 编辑已有图像：按指令修改现有图片（增删或替换元素、换背景、改风格、调整细节）
- 使用 1–3 张参考图指导生成或融合

## When not to use

- SVG 图标、logo 等应与现有矢量资产匹配的图形
- 流程图、图表、简单示意图——用代码（SVG/HTML/CSS/Mermaid）绘制更准确

## 用法

```bash
# 生成
python3 scripts/image_gen.py generate "一只橘猫坐在窗台上晒太阳，水彩插画风格"

# 编辑：指令描述改动，写明保持不变的部分
python3 scripts/image_gen.py edit --image 原图.png --prompt "把背景换成海边日落，人物与姿势保持不变"

# 多图参考
python3 scripts/image_gen.py edit --image 人物.png --image 风格参考.png --prompt "把第一张图的人物画成第二张图的画风"
```

参数：`--size`（512²–2048²，默认 `1024*1024`）、`--n`、`--seed`、`-o`、`--timeout`；生成另支持 `--negative-prompt`、`--no-prompt-extend`；编辑可重复 `--image` 传 1–3 张（单张 ≤10MB）。

## 提示词

- 生成：用陈述句按「主体 + 环境 + 风格 + 光线」描述，详见 [references/prompting.md](references/prompting.md)
- 编辑：明确「保持原图 X 不变，仅修改 Y」，避免模型改动无关部分

## 保存规则

- 用户指定路径优先，否则输出到当前目录；项目用图移入工作区
- 不覆盖已有文件（自动 `-v2`、`-v3`）
- 图片 URL 仅 24 小时有效，脚本内置立即下载

## 密钥

仅从环境变量 `DASHSCOPE_API_KEY` 读取（按 `~/.agents/docs/models.md` 的 `providers.bailian.api_key_env` 注入），不进入文件、日志或回复。

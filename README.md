# Skills

## 技能清单

| 技能 | 适用场景 |
| --- | --- |
| [agent-browser](agent-browser/SKILL.md) | 用浏览器执行网页交互、截图和测试，通过本机 `agent-browser` CLI 按需加载与版本匹配的指南。 |
| [web-reverse](web-reverse/SKILL.md) | 复现网页数据请求，交付可独立运行的 Python HTTP 爬虫和原始响应样例。 |
| [ui-taste](ui-taste/SKILL.md) | 使用 [Uizze 官方发布](https://uizze.sh/.well-known/skills/index.json)的设计指南，设计、打磨和评审 Web 或 iOS 界面。 |
| [imagegen](imagegen/SKILL.md) | 通过阿里云百炼 `qwen-image-3.0-pro` 生成与编辑位图图像：文生图、去水印、清晰度增强、上色、风格迁移。 |

## 使用示例

安装后，在目标项目中开启新会话，点名技能并说明想要的结果。把下面的网址占位符换成实际页面地址。

> 请用 `web-reverse` 分析 `<公告列表网址>`，提取标题、发布日期和详情链接，交付可运行的 Python HTTP 脚本和前两页的原始响应样例。

- `web-reverse` 用 `uv` 管理生成的 Python 脚本和依赖。 [Python HTTP 交付说明](web-reverse/references/python-http-delivery.md)

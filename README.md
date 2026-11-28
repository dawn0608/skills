# Skills

## 技能清单

| 技能 | 适用场景 |
| --- | --- |
| [agent-browser](agent-browser/SKILL.md) | 用浏览器执行网页交互、截图和测试，通过本机 `agent-browser` CLI 按需加载与版本匹配的指南。 |
| [opencli-browser](opencli-browser/SKILL.md) | 通过 OpenCLI 操作你已登录的真实 Chrome：绑定当前标签页、检查页面、点击填表、抓取接口证据，以及管理标签页、标签组和窗口。 |
| [web-reverse](web-reverse/SKILL.md) | 复现网页数据请求，交付可独立运行的 Python HTTP 爬虫和原始响应样例。 |
| [ui-taste](ui-taste/SKILL.md) | 使用 [Uizze 官方发布](https://uizze.sh/.well-known/skills/index.json)的设计指南，设计、打磨和评审 Web 或 iOS 界面。 |
| [imagegen](imagegen/SKILL.md) | 通过阿里云百炼 `qwen-image-3.0-pro` 生成或编辑位图图像：文生图、按指令编辑、1–3 张参考图融合。 |
| [find-skills](find-skills/SKILL.md) | 通过 `npx skills` 检索、安装和更新开放技能生态中的技能；浏览 [skills.sh](https://skills.sh/) 并按安装量与来源筛选。 |
| [skill-creator](skill-creator/SKILL.md) | 来自 [anthropics/skills](https://github.com/anthropics/skills)，创建、修改和评估技能；脚本依赖 PyYAML，评估与描述优化依赖 Claude Code CLI（`claude -p`）。 |
| [doc-coauthoring](doc-coauthoring/SKILL.md) | 来自 [anthropics/skills](https://github.com/anthropics/skills)，引导文档协作流程：收集上下文、分节头脑风暴与起草、用子 Agent 做读者测试；适用于 PRD、RFC、决策文档、提案等。 |
| [mcp-builder](mcp-builder/SKILL.md) | 来自 [anthropics/skills](https://github.com/anthropics/skills)，指导构建高质量 MCP 服务器（Python FastMCP / TypeScript SDK），含研究、实现、测试与评估流程；评估脚本依赖 `anthropic` 与 `mcp` Python 包。 |

## 使用示例

安装后，在目标项目中开启新会话，点名技能并说明想要的结果。把下面的网址占位符换成实际页面地址。

> 请用 `web-reverse` 分析 `<公告列表网址>`，提取标题、发布日期和详情链接，交付可运行的 Python HTTP 脚本和前两页的原始响应样例。

- `web-reverse` 用 `uv` 管理生成的 Python 脚本和依赖。 [Python HTTP 交付说明](web-reverse/references/python-http-delivery.md)

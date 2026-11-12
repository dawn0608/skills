# Skills

## 技能清单

| 技能 | 适用场景 |
| --- | --- |
| [web-reverse](web-reverse/SKILL.md) | 复现网页数据请求，交付可独立运行的 Python HTTP 爬虫和原始响应样例。 |
| [reverse-engineer-anything](reverse-engineer-anything/SKILL.md) | 用 REA 分析原生程序、固件、浏览器等目标的发布产物或运行时行为。 |
| [lov-media-crawler](lov-media-crawler/SKILL.md) | 下载有权保存的社交媒体内容，并生成本地文件和诊断报告。 |
| [grilling](grilling/SKILL.md) | 逐轮追问设计方案，梳理分歧和待定决策。 |
| [domain-modeling](domain-modeling/SKILL.md) | 明确领域术语，维护术语表与架构决策记录。 |
| [grill-with-docs](grill-with-docs/SKILL.md) | 结合方案访谈与领域建模，在讨论中记录术语和架构决策。 |
| [prototype](prototype/SKILL.md) | 搭建一次性界面或逻辑原型，验证设计想法。 |
| [setup-matt-pocock-skills](setup-matt-pocock-skills/SKILL.md) | 为 Matt Pocock 的工程技能配置议题跟踪器、分诊标签和领域文档。 |
| [to-spec](to-spec/SKILL.md) | 把已讨论的方案整理为规格，并发布到项目的议题跟踪器。 |

## 使用示例

安装后，在目标项目中开启新会话，点名技能并说明想要的结果。把下面的网址占位符换成实际页面地址。

> 请用 `web-reverse` 分析 `<公告列表网址>`，提取标题、发布日期和详情链接，交付可运行的 Python HTTP 脚本和前两页的原始响应样例。

- `web-reverse` 用 `uv` 管理生成的 Python 脚本和依赖。 [Python HTTP 交付说明](web-reverse/references/python-http-delivery.md)
- 需要分析浏览器运行时或发布产物时，可按目标使用 REA CLI 或 MCP。 [REA 连接与恢复](reverse-engineer-anything/references/connection-and-recovery.md)
- 下载需要登录的媒体时，按平台准备授权。视频号的元宝授权和微信客户端取流各有准备步骤。 [媒体下载使用说明](lov-media-crawler/README.md)

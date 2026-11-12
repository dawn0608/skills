# Skills

## 技能清单

| 技能 | 适用场景 |
| --- | --- |
| [agent-browser](agent-browser/SKILL.md) | 用浏览器执行网页交互、截图和测试。通过本机 `agent-browser` CLI 按需加载与版本匹配的指南。 |
| [web-reverse](web-reverse/SKILL.md) | 复现网页数据请求，交付可独立运行的 Python HTTP 爬虫和原始响应样例。 |
| [reverse-engineer-anything](reverse-engineer-anything/SKILL.md) | 用 REA 分析原生程序、固件、浏览器等目标的发布产物或运行时行为。 |
| [lov-media-crawler](lov-media-crawler/SKILL.md) | 下载有权保存的社交媒体内容，并生成本地文件和诊断报告。 |
| [grilling](grilling/SKILL.md) | 逐轮追问设计方案，梳理分歧和待定决策。 |
| [domain-modeling](domain-modeling/SKILL.md) | 明确领域术语，维护术语表与架构决策记录。 |
| [grill-with-docs](grill-with-docs/SKILL.md) | 结合方案访谈与领域建模，在讨论中记录术语和架构决策。 |
| [prototype](prototype/SKILL.md) | 搭建一次性界面或逻辑原型，验证设计想法。 |
| [setup-matt-pocock-skills](setup-matt-pocock-skills/SKILL.md) | 为 Matt Pocock 的工程技能配置议题跟踪器、分诊标签和领域文档。 |
| [to-spec](to-spec/SKILL.md) | 把已讨论的方案整理为规格，并发布到项目的议题跟踪器。 |
| [planning-and-task-breakdown](planning-and-task-breakdown/SKILL.md) | 将明确需求拆成有依赖顺序、验收条件和验证步骤的开发任务。 |
| [incremental-implementation](incremental-implementation/SKILL.md) | 按可验证的小步实现功能，每步完成测试、验证和提交。 |
| [test-driven-development](test-driven-development/SKILL.md) | 按项目实际测试工具执行红、绿、重构循环，并用回归测试复现缺陷。 |
| [code-review-and-quality](code-review-and-quality/SKILL.md) | 从正确性、可读性、架构、安全和性能五个维度审查改动。 |
| [debugging-and-error-recovery](debugging-and-error-recovery/SKILL.md) | 通过复现、定位、缩小范围、修复根因和回归验证来排查错误。 |

## 工程技能来源与配套文件

上述 5 个工程技能来自 [Addy Osmani Agent Skills](https://github.com/addyosmani/agent-skills)，导入版本固定为提交 [`301b02b12bff98e4688e6984af6556802322bbde`](https://github.com/addyosmani/agent-skills/tree/301b02b12bff98e4688e6984af6556802322bbde)。各技能保留上游默认触发方式和正文，仅将 `../../references/` 引用改为 `../references/addyosmani-agent-skills/`，适配本仓库的平铺目录。

配套文档与技能来自同一提交，集中保存在 [references/addyosmani-agent-skills](references/addyosmani-agent-skills/)：

- [完成标准](references/addyosmani-agent-skills/definition-of-done.md)：供任务拆解和增量实现使用。
- [测试模式](references/addyosmani-agent-skills/testing-patterns.md)：供测试驱动开发使用，示例以 JavaScript/TypeScript 为主。
- [安全检查清单](references/addyosmani-agent-skills/security-checklist.md)和[性能检查清单](references/addyosmani-agent-skills/performance-checklist.md)：供代码审查使用。

每个新增技能目录及共享文档目录均保留上游 MIT 许可证，来源登记在 [.provenance.json](.provenance.json)。文中提及的其他上游技能作为扩展阅读，不属于本次安装清单；实际使用遵循用户要求及全局、项目协作规范。

## 使用示例

安装后，在目标项目中开启新会话，点名技能并说明想要的结果。把下面的网址占位符换成实际页面地址。

> 请用 `web-reverse` 分析 `<公告列表网址>`，提取标题、发布日期和详情链接，交付可运行的 Python HTTP 脚本和前两页的原始响应样例。

- `web-reverse` 用 `uv` 管理生成的 Python 脚本和依赖。 [Python HTTP 交付说明](web-reverse/references/python-http-delivery.md)
- 需要分析浏览器运行时或发布产物时，可按目标使用 REA CLI 或 MCP。 [REA 连接与恢复](reverse-engineer-anything/references/connection-and-recovery.md)
- 下载需要登录的媒体时，按平台准备授权。视频号的元宝授权和微信客户端取流各有准备步骤。 [媒体下载使用说明](lov-media-crawler/README.md)

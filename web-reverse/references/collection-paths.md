# 网页与接口分析路径

## 角色边界与终止条件

浏览器、Playwright 和 REA 只用于理解结构、网络请求、相关脚本和少量对照样本。最终成果必须由独立 Python HTTP 请求取得。分析后仍无法还原必要算法/输入、会话前提或分页行为时，停止并简短说明阻塞点，不转为浏览器自动化采集，也不交付 DOM 抓取或 `context.request` 作为替代实现。

可以用 JS 做临时对照，但算法优先还原为 Python。不要因浏览器能显示数据，就把任务改成用浏览器把数据取出来。

## 围绕目标字段定位

从用户给定 URL 出发，检查少量 HTML/JSON 和相关脚本。已有 API、内嵌数据或静态 HTML 可直接用 Python 复现；不要求每个网站都经过 Playwright 和 REA。

| 观察到的情况 | 有针对性的下一步 |
| --- | --- |
| HTML 已有目标内容 | Python HTTP 获取，使用 lxml/bs4 等解析目标节点 |
| HTML 内有结构化数据 | 确认目标字段与分页来源，直接解析或请求已观察接口 |
| 页面加载后才有列表 | 浏览器先监听，再导航/翻页，读取少量相关响应定位接口 |
| 参数/签名随页码变化 | 对比请求，追踪输入和计算过程，优先用 Python 重建 |
| 响应密文、页面明文 | 追踪解密/解码，确认算法细节并用 Python 对照实现 |
| 浏览器成功、Python 失败 | 检查必要头、会话、动态参数及 HTTP/TLS 差异；有证据时选包括 curl_cffi 在内的合适客户端 |
| 只有浏览器内能取数，关键逻辑仍不明 | 结束，说明当前未完成独立 Python HTTP 复现及具体限制 |

区分候选接口、实际观察的请求、已由 Python 成功复现的请求。仅复现正常读取，包含已验证的只读 POST/GraphQL query；不重放提交、支付或删除等写入操作。

## 浏览器分析

- 先注册相关响应监听，再执行必要导航/翻页/检索，读取真实响应体并对应目标字段。[1]
- 主动导航、刷新、翻页、检索和手工重放遵守同站点串行及默认 3–5 秒间隔；已有站点要求更慢时从其要求。页面一次加载的自然资源请求不能据此宣称已逐条限速；不为分析反复刷新，优先利用已捕获响应和脚本离线定位。
- 出现限流时暂停主动操作与跨工具验证，必要时停止分析页的自动刷新/轮询，避免冷却期间仍发送请求；按主文档与 Python HTTP 参考处理等待或结束。
- 记录最少的 method、endpoint、必要参数/头、输入变换和分页关系。静态 JS 可用 HTTP 下载分析。
- `browser_context.request` / `page.request` 共享 Cookie 的能力仅用于诊断，不能作为独立 Python 复现的证明。[2]
- Cookie 不等于全部 localStorage/Bearer/签名状态。仅使用必要的合法输入，不默认保存完整 storage state 或 HAR。
- 同时满足请求节流与页面就绪：主动操作之间保留间隔，再以实际响应/字段/元素变化确认就绪；节流延迟不能替代就绪检查，不单靠 sleep / networkidle。分析用 DOM/响应样本只用于定位和核对，不批量导出作为最终数据。
- 清理最终项目中的浏览器依赖和分析残留。不得生成 `collector_browser.py`、浏览器认证刷新链或隐藏自动启动浏览器的采集后备分支。

## REA 按实际能力使用

遇到具体问题时读取已安装 `reverse-engineer-anything`，检查当前工具名、schema 和返回证据，不假定版本、9222 端口或浏览器连接可用。[3]

| 具体问题 | 服务实际提供时可用的能力 |
| --- | --- |
| 相关脚本与请求 | `inspect_web_page`、`observe_web_session` |
| bundle 调用链与参数来源 | `analyze_web_bundle`、`analyze_javascript_application` |
| 已有捕获中的请求 | `inspect_web_network_capture` |
| 提取相关脚本 | `export_web_scripts` |
| 追踪字段/算法 | `trace_application_feature` / `trace_javascript_semantics` |

元数据、`json_body_shapes` 或类型摘要不是业务值，实际数据须由真实响应确认。被动观察不代替浏览器操作。普通网页/JS 分析不以 Ghidra 为前提。[3][4]

采用短证据链：具体问题 → 相关请求/脚本 → 输入与算法 → Python 样例验证。有限、有证据的尝试仍无进展或已知关键条件不可得时结束；不无限去混淆、扩大抓取或更换成浏览器批采。

## 失败说明

只写已确认的事实，区分未还原算法、缺少授权/密钥、工具不可用、环境依赖和分页未验证。用 2–4 句或最多 3 个短点说明结果、原因与限制，不输出长日志，不询问是否改用 Playwright。已有有效 Python 结果可以说明“部分验证”，但不以浏览器数据补齐并宣称成功。

## 官方参考

核对日期：2026-10-29。运行时实际能力优先。

1. Playwright network：https://playwright.dev/python/docs/network
2. Playwright APIRequestContext：https://playwright.dev/python/docs/api/class-apirequestcontext
3. REA 官方技能：https://github.com/morluto/rea/blob/main/.agents/skills/reverse-engineer-anything/SKILL.md
4. REA browser observation：https://github.com/morluto/rea/blob/main/docs/browser-observation.md

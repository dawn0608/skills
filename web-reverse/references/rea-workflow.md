# REA 网页分析工作流

仅在网页分析阶段使用本文件。最终爬虫独立使用 Python HTTP；不要让 REA、Playwright、Chrome 或 CDP 成为采集运行时依赖。复杂算法如需最小本地 JS/WASM 辅助，按主技能第 3 节执行；辅助模块不发送网络请求。

## 目录

- [版本与环境](#版本与环境)
- [按能力选择工具](#按能力选择工具)
- [被动页面与脚本分析](#被动页面与脚本分析)
- [主动交互与网络正文](#主动交互与网络正文)
- [导出脚本与深入分析](#导出脚本与深入分析)
- [缺失能力与失败处理](#缺失能力与失败处理)
- [核验来源](#核验来源)

## 版本与环境

本文件核对于 2026-10-30，依据 `morluto/rea` 的 `317bf3fe235e655b2d752d3be261cc0da7d00f2b`。该快照的 `package.json` 声明 `6.8.0`；这不证明用户已安装版本或 npm 当前发布版本与之相同。

优先使用已有 REA MCP 或 CLI。先读取实际工具 schema，或检查版本和本次要用的子命令帮助；不要每次运行 setup/doctor，也不要猜测选项。

```bash
rea --version
rea inspect-web-page --help
rea capture-browser-scenario --help
```

REA 是 Node/npm 工具；Python 包统一通过 `uv` 管理，两者不要混淆。上述快照的 Node 要求为 `^22.23.4 || ^24.22.1 || >=26.12.1`；采用实际选定版本的要求。

官方提供 `npx rea-agents setup` 注册 agent，以及 `npm install --global rea-agents` 安装 CLI。它们不是每次分析的准备步骤；不要为了使用本 skill 自动修改全局 MCP 配置、升级 Node 或安装 Hopper/Ghidra 等无关原生引擎。

没有 CLI、但任务允许获取 REA 包时，可在可信目录使用 `npx -y rea-agents@latest <子命令>`，记录实际版本并采用绝对目标路径。只有创建本 skill 不代表 REA、MCP 或浏览器已经可用。

## 按能力选择工具

| 需要的证据 | 优先工具 | 不能推断的能力 |
| --- | --- | --- |
| 页面结构、可访问性、JS 源码、请求发起位置 | `inspect_web_page` | 不提供完整网络正文或凭据值 |
| Bundle 中路由、接口候选、可选 source map | `analyze_web_bundle` | 静态候选不证明接口可用 |
| 点击、填写、翻页、捕获请求与响应正文 | `capture_browser_scenario` | 固定动作词汇，不是通用 JS hook |
| 已保存 HAR/SAZ | `inspect_web_network_capture` | 离线读取，不重放请求、不启动代理 |
| REA 未开放的调试或必要会话信息 | 当前允许的 Playwright/Chrome 工具 | 不虚构接口、不绕过工具权限拒绝 |

在宿主允许的任务临时工作区保存小范围、可复核的分析证据，用真实请求返回的数据确认页面字段与接口的对应关系，再迁移到 Python HTTP。分析场景、捕获结果和导出源码默认留在最终交付目录之外；确需交付的材料按[主技能第 6 节的扩展条件](../SKILL.md#6-保存与最终说明)保留，并在 README 说明用途。

## 被动页面与脚本分析

使用已经存在、可访问且属于任务范围的 Chrome 调试会话。CDP endpoint 必须是带显式端口的 loopback 地址。先列目标，再使用返回的真实 `target_id`，不要硬编码旧会话 ID。

```bash
rea list-browser-targets http://127.0.0.1:9222 --json
rea inspect-web-page http://127.0.0.1:9222 TARGET_ID \
  --observation-ms 1500 \
  --include-accessibility-text --include-script-sources \
  --include-json-body-shapes --json
rea analyze-web-bundle http://127.0.0.1:9222 TARGET_ID --json
```

必要时使用 `--allowed-origins` 收窄到目标站点及已观察到的相关 API/CDN origin，具体数组传参语法以 installed help 为准。不要为方便而打开所有来源。

需要 source map 时，确认当前 `analyze-web-bundle` 支持 `--fetch-source-maps` 再启用。它的 map 抓取不携带 Cookie、凭据或 Referrer；抓取失败不等于该资源不存在。

识别被动分析的边界：

- 网络覆盖从附加并启用相应域后开始；页面已经加载不能证明首屏请求已经捕获。先建立监听窗口，再由允许的交互工具触发刷新、搜索或翻页。
- `--include-json-body-shapes` 只有字段路径、类型和计数，没有 JSON 值；不能把它当作原始响应。
- `--include-storage-keys` 只有键名；`--include-storage-fingerprints` 是不可逆指纹；两者均不导出 Cookie/token 值。
- `observation-ms` 是观察窗口，不是 HTTP 请求间隔；仍须单独落实页面交互与请求间的适当延迟。
- 被动 provider 不导航、点击、执行任意 JS，也不开放通用 CDP、`eval`、`hook` 或 Cookie 导出命令。不要编造 `rea network/body/cookies/eval`。
- 导航造成 `target_changed` 时，等页面稳定后重新列目标并捕获；保留真实错误，不把部分证据说成完整成功。

## 主动交互与网络正文

在任务临时工作区将以下对象保存为分析用 `analysis-scenario.json`，后续相对路径命令均在该临时目录运行。替换实际浏览器绝对路径和目标网址；REA 不自动安装浏览器。首次结构检查可短暂等待，正式翻页时还应等待本次结果更新的真实状态标记。

```json
{
  "browser": {
    "mode": "launch",
    "executable_path": "/absolute/path/to/chromium"
  },
  "start_url": { "url": "https://example.com/list" },
  "actions": [
    { "step_id": "settle", "action": "wait_for_timeout", "duration_ms": 1500 }
  ],
  "capture": {
    "at_end": ["dom", "accessibility", "url"],
    "network": {
      "request_body": true,
      "response_body": true,
      "header_values": true
    }
  }
}
```

```bash
rea validate-browser-scenario ./analysis-scenario.json --json
rea capture-browser-scenario ./analysis-scenario.json --json > analysis-capture.json
```

连接已有会话时，将 `browser` 替换为 `{"mode":"connect","cdp_endpoint":"http://127.0.0.1:9222","target_id":"ACTUAL_TARGET_ID"}`。launch 使用自身临时配置；connect 会操作选定页面但只断开连接，不关闭用户浏览器。

按已检查的 DOM 添加点击翻页动作，再跟随等待新页状态的 `wait_for` 或适当延迟。不要照抄占位选择器：

```json
{
  "step_id": "next-page",
  "action": "click",
  "locator": { "kind": "css", "selector": "ACTUAL_NEXT_BUTTON_SELECTOR" },
  "timeout_ms": 10000
}
```

当前声明式动作包含 `goto`、`click`、`fill`、`press`、`select_option`、`check`、`uncheck`、`wait_for`、`wait_for_timeout`、`request`。使用前核对对应 schema；`request` 仍是在浏览器中的请求，不得留在最终采集脚本。

理解输出，避免误判：

- 网络正文/Header 选择默认均为 false；上面的显式选择也会启用 network metadata。
- 用 `transaction_id` 与 `network-content.source_event_sequence` 关联请求、响应和正文；同一个 URL 的多次请求必须区分。
- 保留正文的 base64、字节数、MIME、SHA-256 与完整性状态。它们是 Playwright body API 暴露的内容，不是压缩 wire bytes。
- Playwright 可能通过后续有凭据的加载补取 body；事件关联本身不能证明正文一定来自最初的网络 transaction。最终原始样例使用 Python HTTP 的实际响应保存。
- `Authorization`、`Proxy-Authorization`、`Cookie`、`Set-Cookie` 值仍会被脱敏；不要假称已经得到可复用凭据。优先由 Python 正常请求初始化会话；确需已有登录时按用户授权与工具能力处理。
- 未完成、未暴露或超限正文不是空正文。等目标请求完成并检查捕获状态；不要交付缺失内容并标为完整 JSON。
- scenario 不提供 initiator stack；需要请求发起位置时结合被动捕获或允许的其他调试工具。
- 默认阻止 service workers；有证据表明站点依赖它们时设 `environment.service_workers: "allow"`。
- `command_timeout_ms` 应写入 scenario JSON；不要编造 `capture-browser-scenario --command-timeout-ms`。

## 导出脚本与深入分析

被动捕获须选择 `include_script_sources`；scenario 须选择 `capture.network.response_body`。在任务临时工作区保存完整 Evidence 或标准化结果，再导出到该工作区内一个尚不存在的目录；以下绝对路径替换为实际临时路径：

```bash
rea export-web-scripts /absolute/analysis-capture.json /absolute/exported-scripts --json
rea analyze-javascript-application /absolute/exported-scripts/files --json
```

以导出结果实际返回的 `analysis_input` 为准。检查 manifest、源码 digest 与 unavailable 原因；导出不补抓缺失 URL，不执行 JS，不自动还原所有 source map。

用 `rg` 定位已经观察到的接口路径、签名字段和调用上下文，追踪序列化、编码、时间戳、nonce、加密参数与响应解码。不要只凭出现 `AES`、`RSA`、`CryptoJS` 等字符串认定算法链已解决。

需要缩小实际执行位置时，可用当前版本提供的 `observe-web-execution`；等 armed progress 后再触发动作。它是 V8 coverage，会影响 JIT/计数/时序，不捕获任意函数参数，也不等同于加密 hook。

已有 HAR 可离线读取：`rea inspect-web-network-capture /absolute/session.har har --json`。该操作不会发送 HAR 中记录的请求；正文是否完整取决于原始 HAR。缺失、脱敏、截断内容均须如实标注。

## 缺失能力与失败处理

REA 不可用时继续已授权且能完成的网页结构检查、HTTP 探测、页面 JS 阅读与接口复现，并说明实际采用的路径。不要把缺少 REA/MCP/CDP 当作网站封禁，也不要声称使用了并不存在的工具。

需要补充网络正文、调试调用链或观察验证码时，使用当前环境真实允许的 Playwright 或 Chrome 插件；先读取对应工具/浏览器 skill，遵守它公开的能力边界。工具明确拒绝访问时，不更换通道规避拒绝。

REA 没有内置通用 CAPTCHA/滑块破解器。图形识别、算法复现及服务端验证是另行实现的 Python 分支；只有验证接口接受并能继续返回目标数据才算通过。

最终移除全部浏览器运行依赖，以 Python HTTP 独立验证分页、动态参数和会话初始化。只保留任务需要的源码、实际样例与必要说明；真实阻断须报告发生阶段、已试路径、原始错误与缺失条件。

## 核验来源

- [REA README 与安装入口](https://github.com/morluto/rea)
- [浏览器被动观察](https://github.com/morluto/rea/blob/317bf3fe235e655b2d752d3be261cc0da7d00f2b/docs/browser-observation.md)
- [浏览器 scenario 合同](https://github.com/morluto/rea/blob/317bf3fe235e655b2d752d3be261cc0da7d00f2b/docs/browser-scenario-contract.md)
- [脚本导出](https://github.com/morluto/rea/blob/317bf3fe235e655b2d752d3be261cc0da7d00f2b/docs/website-script-export.md)
- [CLI 实现与参数](https://github.com/morluto/rea/blob/317bf3fe235e655b2d752d3be261cc0da7d00f2b/src/cli/browserCommands.ts)
- [scenario schema](https://github.com/morluto/rea/blob/317bf3fe235e655b2d752d3be261cc0da7d00f2b/src/domain/browserScenarioValues.ts)
- [历史网络捕获](https://github.com/morluto/rea/blob/317bf3fe235e655b2d752d3be261cc0da7d00f2b/docs/web-network-captures.md)

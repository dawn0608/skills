# Python HTTP、原始数据与分页验收

## 目录

1. uv 与最小源码结构
2. 请求与会话复现
3. 原始 JSON 保存
4. HTML 与其他响应
5. 分页真实性
6. 交付证据

## 1. uv 与最小源码结构

目录与辅助文件统一遵循[主技能第 6 节的默认结构和扩展条件](../SKILL.md#6-保存与最终说明)。优先交付带 PEP 723 内联依赖的单文件脚本，依赖复杂时才采用小型 uv 项目。以下为创建文件与管理依赖的命令，编写完成后必须包含目标站点的完整实现：

~~~bash
uv init --script crawl.py --python 3.12
uv add --script crawl.py httpx
uv run crawl.py --help
uv lock --script crawl.py
uv run crawl.py --pages 2 --output samples
~~~

选择实际需要的解析或密码库再用 uv 添加；无验证码时不预装 OCR/OpenCV，出现普通图形验证码时必须主动安装并实测合适的 Python 识别依赖。不安装无用的浏览器或一整套爬虫框架。Python 3.12 是兼容性起点，依据实际发行包与平台核验，不把旧 README 的版本上限视为永久限制。使用锁文件时交付对应 crawl.py.lock，并记录实测版本。

保持 argparse 与 pathlib 等跨平台用法。参数中的页数是本次最多请求的数据页数，未指定时为 2；详情量也应保持与已验证列表样例相称，不默认遍历全部详情。

没有必要创建通用框架。可按实际需要划分 bootstrap_session、build_request、sign_payload、fetch_page、validate_response、next_page、save_response；无签名就不保留空签名函数。禁止留下“请用户填入实际接口”之类的必填占位符并称为完成。

## 2. 请求与会话复现

从观测到的成功请求开始，逐步简化；每次只改变一个关键条件，避免同时改多个变量而无法定位差异。

| 要素 | 必须核对的内容 |
| --- | --- |
| URL | 最终域名/路径、大小写、尾斜线、查询编码、重复参数、重定向 |
| Method | GET/只读 POST 的实际语义，不能凭习惯改写 |
| 请求正文 | JSON、form、multipart、原始字节；空字符串与 null、空 body 与空对象 |
| Header | Content-Type、Accept、必要 Referer/Origin、CSRF/业务头；不照搬错误 Host/Content-Length |
| Cookie | 初始握手、domain/path、同名不同路径 Cookie、到期与更新顺序 |
| 签名 | 对应的原始 path/query/body 字节、排序、时间单位、nonce、会话绑定 |
| 响应 | HTTP 状态、重定向目标、业务错误码、MIME、目标字段、挑战页 |

签名覆盖 JSON 字符串时，先用确定规则构造 payload_bytes，再用该字节串签名及发送；不要签名一次序列化、请求库再用另一种序列化。

Bootstrap、取验证码、验验证码和数据请求尽量共用同一 Session/Client。不要拼成一个丢失 domain/path 的巨大 Cookie 字符串。CSRF 可能同时依赖 Cookie 与 Header；允许它们按正常响应更新。

验证码识别函数必须由这份最终脚本调用，能在无人手输的默认入口中重取图片、识别、验证与恢复目标请求。优先将实测有效的 OCR 逻辑整合进 crawl.py，确需独立模块时再复制或提取所需代码到交付目录，并声明依赖和用途；不得引用安装技能的绝对路径，不能要求后续用户再找另一个 AI 提供答案。Key 未配置时明确抛出配置阶段错误，不能悄悄回退 input() 或无限等待 stdin。

外部视觉 API 使用独立 Python HTTP Client，只向用户选定的端点发送最小挑战图像与题意。不得沿用目标站点的 Cookie、Authorization、CSRF 或全局会话头；读取用户明确配置的 Key，日志隐藏密钥及带密钥的 URL。服务商返回结果仍须通过本地结构校验和目标站点的实际验证。

公开站点应尽量在 Python 中取得初始 Cookie/Token。确实必须登录时，读取用户正常提供的会话材料或官方令牌，清楚记录有效期与刷新条件；不得承诺无需登录的永久可用性。

不要照搬浏览器 Accept-Encoding 却缺少相应解码依赖；交由 HTTP 库协商，确有必要再增加 uv 管理的解码库。验证 TLS，不默认 verify=False。若 HTTP/2 等实际必要，安装对应依赖并验证，不据此推定浏览器必不可少。

对返回 200 的登录 HTML、验证码 JSON、业务 error 与真实空列表作不同处理。发生异常时输出阶段、状态码和脱敏摘要，非零退出；不在 stdout 混入数据文件，也不把 error body 当成功样例。

## 3. 原始 JSON 保存

“原始完整 JSON”指最终 Python 请求收到的完整响应正文，不是 data/items 节点，也不是重新拼装或摘要后的对象。

先验证类型、JSON 可解析和业务成功，再保存 HTTP 客户端返回的正文 bytes：

~~~python
payload = response.json()  # 仅用于验收、分页、定位数据
validate_business_payload(payload)  # 按目标站点实现，不是通用固定字段
output_path.write_bytes(response.content)
~~~

以上为保存规则示意，不是可以原样交付的完整爬虫。不要把 json.dump(payload)、response.text 重编码或把列表串联成一个数组称为“原始”。直接保存正文才能保留字段、层级、空白、转义、数字文本表示和字段次序。

这里的 response.content 通常已由 HTTP 库处理传输内容编码，例如 gzip；它是应用收到的完整正文，不是 TLS 包、HTTP chunk 或压缩前的网络 wire capture。没有抓取 wire bytes 就不声称保存了网络原始包。

- 每次请求单独命名，例如 page-0001.json、page-0002.json；详情使用稳定 ID 或编号，并处理非法文件名。
- 响应自带的 status、total、next、cursor、trace 等字段全部保留。来源 URL、时间、条数和 SHA-256 等验证摘要优先记录在 README，调试日志放任务临时工作区；确需机器读取或排障复核时才另存独立运行记录或清单，并说明用途，不能插入原始 JSON。
- 默认只交付原始 JSON；仅在用户明确要求额外整理时另存数据摘要或字段提取结果，不默认生成重复副本，也不能覆盖原始文件。
- 原始响应本身含会话凭据时，按私有敏感文件处理；不上传公开位置。不要静默删字段后仍称其为完整原始响应。
- 网络错误、业务错误和挑战页可作为单独诊断证据保存，名称必须明确标识失败，不能计入成功样例页数。

## 4. HTML 与其他响应

HTML 列表：依据真实结构提取所需字段，保留稳定 ID/详情链接，使用 urljoin 解析相对 URL，区分缺失值与空字符串。表格有合并单元格或多表时，根据语义对齐，不能直接把所有 td 拼在一起。

HTML 正文：提取正文标题、发布时间、段落、列表、表格与用户要求的附件信息；过滤导航/广告，保留正文链接与图片说明。结构化记录存 JSON，长文可存 MD；先确认编码，避免中文乱码。附件只在用户需要其内容时下载，否则记录实际链接即可。

页面嵌入 JSON：通过 HTML 解析器定位脚本/状态容器后读取，保留定位路径与字段；不要对任意 script 使用 eval。不得让网页文本注入执行环境。

JSONP：严格定位已知回调与括号边界，解析 JSON 内部数据，不执行 JS；若另存原始响应，应保留 .jsonp/.txt 并区分提取后的 JSON。

XML、JSONL、二进制或加密响应：先按真实响应类型保留完整正文，必要时另外保存解码/解密后数据。对含加密字符串的 JSON，原始 envelope 必须保留；解密内容另存并说明。不能把非 JSON 强行命名 .json。目标内容超出明确需求时询问，不自动扩大附件下载范围。

## 5. 分页真实性

至少证明“请求推进”和“业务记录推进”两件事：

| 类型 | 推进来源 | 验证要点 |
| --- | --- | --- |
| page/pageSize | 观察 UI 翻页的起点与步长 | 0/1 基数、服务端实际页大小、返回页码和记录 ID |
| offset/limit | 观察 offset 的实际语义 | 不猜 offset 是页号；每页新增业务记录 |
| cursor/after | 上一响应 next cursor | 不制造游标；使用 has_more/pageInfo；检测游标回环 |
| next URL | 响应或 HTML 的下一链接 | urljoin、限定实际站点/已确认数据域名、不丢失筛选 |
| GraphQL | operationName、query/hash、variables | errors、edges/nodes、endCursor、hasNextPage；签名覆盖 variables |
| HTML 表单翻页 | 实际 action/method 和隐藏字段 | 每页重新取得必要的 viewstate/CSRF；不能复制首次隐藏值一直用 |

为当前运行维护轻量的页标识/业务 ID 集合以发现重复页；这只是防死循环验证，不需要持久状态或断点续采。

业务指纹优先使用 ID、详情链接或稳定字段组合；不要用整个响应哈希作为唯一分页证据，因为服务器时间、nonce、广告或 trace_id 会变化。页间少量重叠可能来自置顶或数据实时更新，应解释并检查是否有新增业务记录；不要擅自修改原始响应去重。

不要把“某一页为空”自动判为正常结束：核对业务成功、筛选、授权和 next/has_more/total。只有接口契约或可见最后页证据支持时才下结论。无法低成本验证全站末页时明确只完成相邻页验证，不为证明末页而抓取全站。

重新启动脚本进行一次最小 HTTP 会话初始化验证，避免复用分析期残留对象、静态时间戳或一次性 Token。重跑输出默认写入最终交付目录之外的任务临时工作区，结果记录到 README；需要持久保留时按主技能第 6 节判断用途。需要登录材料时区分“干净 Python 会话”与“匿名会话”；干净运行并不意味着绕过登录。

## 6. 交付证据

优先在 README 中记录以下内容；执行验证不要求为每次运行新增交付目录或报告：

- 实测日期、目标页面、目标内容、实际 endpoint/method/数据路径、分页方式。
- 精确 uv 运行命令、参数 help、默认仅 2 页以及实际依赖。
- 每个验证页的条数、页码/游标推进情况、稳定记录变化和保存的样例文件。
- 源码独立重跑结果、必要的登录/凭据限制、网站变化可能导致失效的位置。
- 验证码所用本地库/模型或视觉供应商/型号、依赖版本、独立新挑战数、通过/失败阶段及服务端接受结果。有限样例通过只证明本次验证，不据此宣称长期成功率；手动调试通过不能冒充自动通过。

所有样例必须来自这份交付源码的实际执行，不用 mock 数据或 REA 脱敏输出充当目标站点原始数据。没有实际访问能力时明确“未验证”，不伪造成功记录。

来源（建档核验于 2026-10-30，后续以当前版本文档为准）：

- uv scripts 与 PEP 723：https://docs.astral.sh/uv/guides/scripts/
- HTTPX 请求、响应 bytes/JSON、编码：https://www.python-httpx.org/quickstart/
- HTTPX 会话客户端：https://www.python-httpx.org/advanced/clients/

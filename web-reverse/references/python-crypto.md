# Python 算法还原与最小 JS 例外

## 默认先还原为 Python

网页 JS 用来理解真实算法、参数来源和结果，不默认作为最终运行依赖。定位请求/响应链路后，先用 Python 标准库、PyCryptodome、cryptography 或项目已有的合适库实现；通过真实请求和分页验证再交付。

1. 区分编码、摘要、HMAC、签名、请求加密与响应解密。Base64/Hex 不是加密，摘要不可以当作可逆密文。
2. 确认原始输入及其类型/字节、变换顺序、动态参数、输出用途和必要密钥来源。不要仅凭“AES”“RSA”名称猜默认参数。
3. 标准库可处理的字节、哈希、HMAC、编码和序列化直接用标准库；AES/RSA 等用经过验证的 Python 库，不手写密码原语。
4. 可以临时保存/调用必要 JS 对照输入输出，但 Python 等价实现通过后，最终项目不保留无用 JS、Node、PyExecJS2 或浏览器依赖。
5. 必要参数尚未找到或一次分析未成功时，继续沿其输入来源、调用栈、相关模块和中间值定位；对照各层字节，缩小最早出现差异的位置。停止统一遵循主文档第 6 节，不能仅因算法复杂或 REA 没有结果就结束。不得改用浏览器把数据抓出来。

## 安装名、导入名与 uv

| 用途 | uv 依赖名 | Python 导入示例 |
| --- | --- | --- |
| 新实现采用 PyCryptodome | `pycryptodome` | `from Crypto.Cipher import AES` |
| 已有 PyCryptodomex 项目 | `pycryptodomex` | `from Cryptodome.Cipher import AES` |
| 采用 cryptography | `cryptography` | 按该库实际 API 导入 |

在对应项目根目录通过 `uv add pycryptodome` 声明并安装实际需要的依赖，运行普通 Python 脚本时使用项目环境；不默认另建内联脚本依赖。不要将口语名称 `cryptodome` 当作安装名，也不要把 `Crypto` 与 `Cryptodome` 导入混用。

按项目锁定的真实版本选择 API。当前官方文档说明 4.x 不再发布 pycryptodomex 新主线，因此后者作为既有项目兼容情况处理，不与 pycryptodome 并列作为新项目默认；不为此擅自升级已有项目，也不混装旧 pycrypto。[1]

## 协议兼容检查

| 项目 | 必须对应原站点的细节 |
| --- | --- |
| 输入字节 | UTF-8/UTF-16、Hex/Base64/Base64URL、JSON 序列化与字段顺序、URL 编码时机、时间戳单位、32 位位运算和字节序 |
| AES | key 是字节还是口令、key/IV 来源、模式、padding、IV/nonce、salt/KDF；CFB segment size、CTR 计数器布局；GCM 等模式的 AAD/tag 与拼接 |
| CryptoJS 迁移 | 字符串 passphrase 与 WordArray key 不同，可能涉及 key/IV 派生、salt 和 OpenSSL 格式，不能把字符串直接当原始 AES key [2] |
| RSA 加密 | 密钥角色/格式、PKCS#1 v1.5 或 OAEP、OAEP hash/MGF1 hash/label、明文长度/分块和输出编码 |
| RSA 签名/验证 | 与加密分开，核对 v1.5/PSS、摘要、MGF、salt 长度和签名前字节；不寻找或推导服务端私钥 |
| 自定义签名/HMAC | 实际算法与输入/密钥来源、拼接和排序、大小写、每步编码、动态字段是否全部参与 |

不同库的默认值可能不同，不用“同名算法”代替兼容性验证。[3][4] Python 发送的正文/query 字节必须与计算签名或密文时的表示一致。

## 验证流程中的算法边界

复杂签名、混淆脚本或验证状态参与业务请求时，实际尝试可用且相关的 REA 能力定位输入来源、调用链和中间值，再对照 Python 字节。区分可复现的业务签名/游客初始化与必须人工完成的挑战；不将“还原算法”解释成自动破解人工挑战、伪造通过令牌或绕过访问控制。需要人工操作时遵循主文档第 6 节暂停并可续接。

用户完成验证后，以实际正常业务请求确认必要会话及动态参数，继续 Python 差异对照；不沿用过期或一次性的验证值，不把人工通过当作算法或独立 HTTP 已验证成功。

## 比对和真实请求验证

- 用原网页/JS 的少量实际输入与结果做对照，覆盖中文、分页和必要边界值；仅在临时分析环境使用 JS，避免污染交付依赖。
- 确定性计算可比较字节。随机 padding、salt、IV/nonce 参与时，两次密文不同可能正常；核对协议、可用解密/验签结果和实际接口接受情况，不把随机过程改成固定值来凑一致。
- 每次请求与重试先完成节流/冷却等待，再在发送前更新页码/cursor、时间戳、nonce 和相关签名/密文；不预先批量计算，不沿用一次抓包值，避免延迟导致动态参数过期。
- 独立 Python HTTP 取得真实字段后验证下一批，并通过新的 uv/Python 进程重复运行。
- 解密不对时先区分错误响应、封装/编码、密钥派生、padding/IV 和解析层；只有第一页可用时检查分页输入、签名覆盖和 token 生命周期。继续有证据的修正与对照，只有主文档第 6 节的条件满足才收束；不要给浏览器兜底采集代码。

## 仅在必要时保留少量 JS

用户偏好是尽量不用额外 JS，并非一律禁止计算辅助。只有已定位必要逻辑，Python 等价还原存在具体困难，而最小 JS 能使独立 Python HTTP 复现通过时，才采用例外；说明具体原因，用户明确要求纯 Python 时不采用。

- 只保留最小计算函数和必要模块，Python 仍负责 HTTP 请求、响应处理和输出，不保留网页渲染、DOM 采集或浏览器启动。
- 如采用 PyExecJS2，在对应项目内通过 `uv add` 声明实际依赖，Python 导入名仍是 `execjs`，另检查实际 Node/runtime 依赖；不默认引入它。[5]
- UMD/CommonJS 导出要用薄包装暴露可调用函数；不要把模块内部函数直接当作全局入口。参数和返回值使用明确的可序列化形式，必要二进制编码为 Hex/Base64。
- 不假设桥接库自动等待 Promise、支持所有模块语法或提供 window/document/DOM。报环境错误时先定位真实所需的输入/状态，尝试提取最小纯计算或还原等价 Python；不能因一个 `window` 未定义就结束，也不无依据补齐整个浏览器。确实不可分离时按主文档第 6 节判定。
- 不直接执行未检查的整包脚本，不让分析脚本访问无关本地秘密；只有实际必要的 JS 才进入交付项目。

## 官方参考

核对日期：2026-10-29。根据项目实际版本验证。

1. PyCryptodome installation：https://www.pycryptodome.org/src/installation
2. CryptoJS：https://cryptojs.gitbook.io/docs
3. PyCryptodome AES：https://www.pycryptodome.org/src/cipher/aes
4. PyCryptodome OAEP：https://www.pycryptodome.org/src/cipher/oaep
5. PyExecJS2：https://github.com/meatjam/PyExecJS
6. RSA 规范：https://www.rfc-editor.org/rfc/rfc8017

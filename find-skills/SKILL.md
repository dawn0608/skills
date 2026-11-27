---
name: find-skills
description: Use when you need to discover which skills are installed on this machine or in the current project, or to search installed skills by keyword before starting a task. Triggers include "find skills", "list skills", "search skills", "which skills exist", "有没有相关技能", "查找技能", "列出技能".
---

# find-skills

列出本机共享技能目录和当前项目中的技能，输出可直接交给 Read 工具的 `SKILL.md` 绝对路径。

## 何时使用

- 开始任务前，确认已有可用技能，避免重复实现
- 只记得关键词（如 `pdf`、`browser`、`爬虫`），需要定位对应技能
- 核对本机各编码 Agent 实际可见的技能清单

## 用法

在技能目录内执行：

```bash
# 列出全部技能
bash scripts/find-skills

# 按关键词过滤（对技能内容和路径做不区分大小写的 ERE 匹配）
bash scripts/find-skills pdf
bash scripts/find-skills 'test|tdd'
```

输出格式：

```
/absolute/path/SKILL.md - description
```

命中后必须用 Read 工具读取完整 `SKILL.md` 再使用；不要只读 frontmatter，也不要凭记忆套用旧版本。

## 搜索范围

按顺序搜索以下目录，不存在的目录跳过，按真实路径去重：

1. `$FIND_SKILLS_DIRS`（可选，冒号分隔的额外目录）
2. `~/.agents/skills`
3. `~/.claude/skills`
4. `~/.codex/skills`
5. `~/.gemini/skills`
6. `$PWD/.agents/skills`
7. `$PWD/.claude/skills`

其中 `~/.agents/skills` 是共享技能仓库；Codex、Copilot CLI 和 Gemini CLI 也原生识别该目录。以 `.` 开头的目录（如 Codex 的 `.system`）和 `node_modules` 会被跳过。

## 约束

- 只读操作，不修改任何技能文件。
- 兼容 macOS 自带的 bash 3.2。
- `~/.claude/skills` 是指向 `~/.agents/skills` 的软链接时会自动去重。

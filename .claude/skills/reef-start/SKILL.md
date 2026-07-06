---
name: reef-start
description: 从 Issue 跟踪系统或从零需求讨论启动开发生命周期。用户提供 Issue 编号时获取 Issue 详情和相关上下文（PRD 设计稿）；无 Issue 时直接走 OpenSpec 自由讨论流程。通过 SDD 工作流生成高质量 spec 文档并进入 TDD 实现阶段。
argument-hint: url
arguments: url
allowed-tools: Agent, Bash(git:*), Bash(openspec:*), Read, Edit, Write
mcpCapabilities:
  issue_tracker:
    domain: project-management
  knowledge_base:
    domain: knowledge-base
  design_tools:
    domain: design-tools
deepstorm:
  tool: reef
---

# Reef Start

## 功能概述

```mermaid
flowchart LR
    ENTRY["📥 reef-start 被调用"] --> DECIDE{"入口路由"}
    DECIDE -->|"有 Issue 信息"| A["Path A<br/>Issue 驱动"]
    DECIDE -->|"无 Issue 信息"| B["Path B<br/>开放讨论"]
    A --> P1A["① 获取需求<br/>Issue + PRD + 设计稿 + 澄清"]
    B --> P1B["① 需求讨论<br/>OpenSpec new + BMAD 讨论<br/>+ brainstorming 文件"]
    P1A --> P2A["② 创建分支"]
    P2A --> SDD["③ SDD 文档 + 实现计划<br/>proposal→specs→design→tasks<br/>→ spec-hardener → writing-plans"]
    P1B --> BRAINSTORM["② Brainstorming 文件"]
    BRAINSTORM --> SDD
    SDD --> GATE["⛔ 检查 superpowers<br/>硬性门禁"]
    GATE --> P4["④ TDD 实现<br/>Path B 先创建分支<br/>→ RED→GREEN→REFACTOR<br/>逐 task 循环"]
    P4 --> END["⑤ 分支结束<br/>提交 / PR"]
```

> **💡 自动触发：** 如果 reef 已安装且本项目配置了 `before-read` hook，当用户自然口述开发需求（如"我想加个用户注册功能"）时，系统会自动识别并加载本 skill，无需手动输入 `/reef-start`。

> **📍 当前步骤：** 每次进入本 skill 后，在第一句回复中声明当前阶段编号。例如：
> ```
> > 📍 当前：Path A · 阶段一 — 获取需求
> ```
> 或
> ```
> > 📍 当前：Path B · 阶段一 — 需求讨论
> ```

## 入口路由

**这是每次进入本 skill 后的第一步，在执行任何阶段之前完成。**

AI SHALL 根据用户输入判断是否存在 Issue 相关信息，路由到对应路径：

| 用户输入特征 | 路由 |
|-------------|------|
| 包含 Issue URL（如 `https://*.atlassian.net/browse/LC-1234`）、Issue 编号（如 `LC-1234`、`PROJ-456`）或明确引用某个 Issue | → **Path A**（Issue 驱动流程） |
| 不包含任何 Issue 引用，仅描述需求/想法/问题 | → **Path B**（开放讨论流程） |
| 模棱两可、无法确定是否包含 Issue 信息 | 向用户确认："你是基于某个 Issue 开始，还是想从零讨论一个新需求？" |

```mermaid
flowchart TD
    ENTRY["📥 reef-start 被调用"] --> CHECK{"用户输入中包含<br/>Issue 信息？"}
    CHECK -->|"是"| A["→ Path A<br/>Issue 驱动流程<br/><br/>阶段一→五"]
    CHECK -->|"否"| B["→ Path B<br/>开放讨论流程<br/><br/>讨论 → SDD → 实现"]
    CHECK -->|"不确定"| ASK["询问用户：<br/>'基于 Issue 还是从零讨论？'"]
    ASK --> A
    ASK --> B
```

## 前置条件（含 MCP 能力映射）

- 项目已通过 DeepStorm CLI 安装 setup 阶段
- 当前 MCP 服务状态已注入到本技能文件中
- 运行时通过 `.claude/settings.json` 的 `deepstorm.mcpCapabilities` 确认服务可用性

### 运行时 MCP 服务发现

进入 Stage 1 前，AI SHALL 读取 `.claude/settings.json` → `deepstorm.mcpCapabilities`，确定当前可用的 provider。

能力映射结构说明：

```
{
  "issue_tracker": {
    "available": true/false,        // 是否有可用的 Issue 跟踪服务
    "providers": [                  // 可用的 MCP 服务列表
      { "id": "jira", "label": "Jira" }
    ]
  },
  "knowledge_base": {
    "available": true/false,        // 是否有可用的知识库服务
    "providers": [...]
  },
  "design_tools": {
    "available": true/false,        // 是否有可用的设计工具服务
    "providers": [...]
  }
}
```

每个 provider 的 MCP 操作指南按读写方向拆分，位于 `.claude/skills/deepstorm-mcp-{service}-{op}/SKILL.md`。AI 根据当前步骤所需的操作类型读取对应指南（读取 Issue → `deepstorm-mcp-jira-read`、读取文档 → `deepstorm-mcp-feishu-wiki-read`、读取设计稿 → `deepstorm-mcp-figma-read`）。AI 调用前可读取该文件了解工具使用方式。

如果 `deepstorm.mcpCapabilities` 读取失败（文件不存在/格式错误），AI SHALL 降级为"无 MCP 服务安装"，按手动模式运行各子步骤。

## 工作流

### 🅰️ Path A — 阶段一：获取需求

#### 1.1 解析 Issue 编号

按以下优先级获取 Issue 地址：

1. **slash 命令参数** — 如通过 `/jira-start <url>` 调用，`$url` 已传入，优先使用
2. **用户消息** — 从用户当前输入中提取 Issue URL 或编号
3. **询问用户** — 以上均未获取到时，请用户提供

支持以下输入格式，提取规则统一：

| 格式 | 示例 | 提取方式 |
|------|------|---------|
| 完整 URL | `https://<instance>.atlassian.net/browse/LC-1234` | 从 URL path 中提取 `LC-1234` |
| 完整编号 | `LC-1234` | 直接使用 |
| 纯数字 | `1234` | 加项目前缀（从 URL 或用户输入推断） |

#### 1.2 获取 Issue 详情（MCP 动态适配）

根据运行时能力映射决定 Issue 获取方式：

**如果 `issue_tracker.available === true`：**

1. 从能力映射中确定使用的 provider（多 provider 时 AI 根据用户输入推断，推断不出时询问用户）
2. 读取 `.claude/skills/deepstorm-mcp-jira-read/SKILL.md` 了解工具调用方式（仅读取 Issue，无需写入权限）
3. 使用该 MCP 工具获取 Issue 详情（如 Jira 的 `get_issue`、Linear 的等效方法）
4. 从响应中提取 Issue 元数据：

```
jira:
  key: "LC-1234"                            # issue 编号
  title: "表单提交按钮优化"                    # issue 摘要（用于分支命名和 proposal）
  url: "https://<instance>.atlassian.net/browse/LC-1234"  # issue 链接
  type: "Story"                               # issue 类型
  status: "In Progress"                       # 当前状态
```

**如果 `issue_tracker.available === false`：**

- 请求用户手动粘贴 Issue 摘要和描述
- 提取用户提供的元数据录入上述结构

#### 1.3 获取 PRD 上下文（MCP 动态适配）

从 Issue `description` 中搜索知识库相关链接。如 `knowledge_base.available === true`：

1. 从能力映射中确定使用的 knowledge_base provider
2. 读取 `.claude/skills/deepstorm-mcp-feishu-wiki-read/SKILL.md` 了解工具调用方式（仅读取文档，无需写入权限）
3. 使用该 MCP 工具的文档读取方法获取 PRD 内容
4. 提取需求上下文整合到 proposal 的 Summary / Scope 段

**降级处理：** `knowledge_base.available === false` 时，询问用户是否手动提供 PRD 内容。

PRD 上下文获取的详细操作方式见 `.claude/skills/deepstorm-mcp-feishu-wiki-read/SKILL.md`。

#### 1.4 澄清需求

拿到 Issue 描述和 PRD 上下文后，**先不做实现**。向用户做一轮针对性澄清：

- 根据 Issue 摘要提问："这个 issue 的核心改动范围是什么？"
- 根据 Issue 类型提问：Bug 问复现环境 / Story 问用户场景 / Task 问验收标准
- 根据 Issue 描述中的模糊点提问：如有提到多个模块，确认优先级和范围
- 常规兜底问题："第一版明确不做什么？有什么是故意推迟的？"

将澄清结果记录下来，后续写入 proposal 的 "不做什么" 段。

#### 1.5 获取设计稿（MCP 动态适配）

从 Issue 的 Design 字段或描述中提取设计工具链接。如 `design_tools.available === true`：

1. 从能力映射中确定使用的 design_tools provider
2. 读取 `.claude/skills/deepstorm-mcp-figma-read/SKILL.md` 了解工具调用方式
3. 从 Issue 的 Design 字段（如 Jira 的 `customfield_10032`）或描述中提取设计工具链接
4. 使用该 MCP 工具获取设计数据
5. 派遣子代理分析设计数据（详细操作方式见 `.claude/skills/deepstorm-mcp-figma-read/SKILL.md`，具体设计数据的字段说明见参考文件中对应 provider 的文档）

**降级处理：** `design_tools.available === false` 时，告知用户"未检测到设计工具服务，将不生成设计稿摘要"。

### 🅰️ Path A — 阶段二：创建分支

分支命名流程：

1. 取 Issue 摘要，翻译为英文 kebab-case，限制 3-6 个单词
2. 从 main 分支岔出：

```bash
git stash push -m "jira-start-auto-stash"
git checkout main && git fetch origin main && git reset --hard origin/main
git checkout -b <kebab-case-name>
git stash pop 2>/dev/null || true
```

**上下文约定**：分支名 = OpenSpec change 名。后续所有 skill 通过以下方式感知当前上下文：
- `git branch --show-current` → 当前 change 名
- `openspec/changes/$(git branch --show-current)/` → 当前 change 目录

### 🅱️ Path B — 阶段一：需求讨论

**此阶段仅 Path B 执行。Path A 跳过本节，直接进入阶段三（共享）。**

需求讨论阶段的目标：在无 Issue 信息的前提下，通过结构化讨论明确需求范围，产出 brainstorming 文件作为后续 SDD 流程的输入。

#### B1.1 创建 OpenSpec change

根据用户的第一句话或当前讨论话题，提取 3-6 词英文摘要作为 change 名：

```bash
openspec new change "<kebab-case-name>"
```

讨论过程中记录关键信息，讨论结束后整理到 brainstorming 文件。

#### B1.2 结构化需求讨论

按以下框架以对话方式引导用户讨论，**逐步推进而非一次性提问**：

1. **核心意图**：你想解决什么问题或做什么功能？
2. **具体范围**：具体要改什么？涉及哪些模块或文件？
3. **边界定义**：第一版明确不做什么？有什么故意推迟的？
4. **注意事项**：有没有已知约束、技术依赖或风险？

讨论过程中 AI SHALL 及时记录用户的关键回答，无需一次性记录所有细节。

#### B1.3 需求澄清

根据讨论内容做针对性追问：

- **功能类**：核心用户场景是什么？目标用户是谁？
- **重构/改进类**：当前有什么痛点？预期改善后的理想状态？
- **边界模糊时**：提到多个模块时，确认优先级和先后顺序

#### B1.4 产出 Brainstorming 文件

当需求讨论已基本收敛（用户对"做什么"和"不做什么"已达成一致），将讨论内容整理为：

```
_bmad-output/brainstorming/brainstorming-session-{date}-{seq}.md
```

文件内容包括：
- **讨论主题**：本次讨论的核心话题
- **关键决策**：讨论中达成的共识和决策
- **需求要点**：整理后的需求描述
- **边界范围**：明确不做的内容
- **后续步骤**：下一阶段需要处理的要点

> **注意**：Path B 不在此处创建 git 分支。分支创建推迟到 superpowers 门禁通过后、TDD 实现开始前（见阶段四入口）。

### 🅰️🅱️ 阶段三（共享）：openspec SDD 文档生成

使用 openspec CLI。Path A 的阶段二已创建分支，分支名即为 change 名。Path B 通过 B1.1 已创建 change：

```bash
CHANGE=$(git branch --show-current)  # Path A：通过分支名获取
# 或
CHANGE=$(ls openspec/changes/ | sort -r | head -1)  # Path B：获取最新 change
```

#### 3.1 创建 openspec change

Path A 跳过本步骤（分支名已对应 change 名）。Path B 通过 B1.1 已创建 change，也跳过。

#### 3.2 创建 proposal

```bash
openspec instructions proposal --change "$CHANGE" --json
```

必须包含：Issue Reference（Path A）/ 需求来源说明（Path B）、Motivation/Scope、Out of Scope（≥5 条）、Acceptance Criteria Mapping、Impact（FE/BE/API/DB/Permission/Tenant）、Known Risks、Validation。

#### 3.2b 对 proposal 执行 grill-me

```bash
skill "grill-me" "当前 change: $CHANGE - proposal"
```

#### 3.3 创建 specs

```bash
openspec instructions specs --change "$CHANGE" --json
```

#### 3.3b 对 specs 执行 grill-me

```bash
skill "grill-me" "当前 change: $CHANGE - specs"
```

#### 3.4 创建 design

```bash
openspec instructions design --change "$CHANGE" --json
```

整合设计工具数据和代码探索结果。design.md 必须包含 Change Scope Matrix 和 API Contract。

#### 3.5 创建 tasks

```bash
openspec instructions tasks --change "$CHANGE" --json
```

#### 3.6 应用 spec-hardener

加载 `reef:reef-harden` 技能过五道筛。

#### 3.7 生成实现计划 (Writing-Plans)

将经过 spec-hardener 处理后的 SDD 文档（specs/、design.md、tasks.md）输入到 `superpowers:writing-plans`，生成逐任务的、可执行的实现计划。这是连接 openspec（需求→任务分解）与 Stage 4（TDD 实现）的关键桥梁。

**流程：**

1. **加载 `superpowers:writing-plans`**

   ```bash
   skill "superpowers:writing-plans" "当前 change: $CHANGE — 基于 tasks.md 和 specs/ 生成实现计划"
   ```

   按 writing-plans 技能指导执行以下步骤。

2. **生成实现计划**

   writing-plans 技能将：
   - 从 tasks.md 和 specs/ 读取任务范围和验收标准
   - 从 design.md 读取 Change Scope Matrix 和 API Contract
   - 扫描代码库，映射需要创建/修改的文件结构（File Structure 阶段）
   - 将 openspec tasks 拆解为 bite-sized 实现步骤（每步 2-5 分钟，含完整代码和测试代码）
   - 保存到 `docs/superpowers/plans/$(date +%Y-%m-%d)-$(git branch --show-current).md`

3. **自审 (Self-Review)**

   按 writing-plans 技能的 Self-Review 检查清单逐项校验：
   - Spec 覆盖度：每个 task 是否对应 spec 中的需求
   - 占位符扫描：无 "TBD"、"TODO"、"implement later" 等占位符
   - 类型一致性：跨 task 的函数签名、类型定义一致

4. **记录计划路径**

   记录计划文件路径，供阶段四的 TDD 实现读取：

   ```bash
   PLAN_FILE="docs/superpowers/plans/$(date +%Y-%m-%d)-$(git branch --show-current).md"
   ```

> **关键原则：** 实现计划覆盖 openspec tasks 不是重新定义范围，而是将每个 task 分解为文件级操作步骤。plan 中的 task 粒度应达到"每一步是一个文件变更 + 测试 + 提交"级别。
>
> **Handoff 说明：** writing-plans 在计划生成后会提供执行选项（Subagent-Driven / Inline Execution）。本 SKILL.md 的 Stage 4 已有完整的 TDD 实现流程，handoff 由 Stage 4 接管，不在此处选择 execution 方式。

#### 3.8 语言规范

中文正文 + 英文专有名词。

#### 3.9 用户确认

展示文档概览（含实现计划），请用户审阅后再进入实现。

## ⛔ 实现前硬性门禁：检查 Superpowers（共享）

### 强制规则（不可协商）

> **tasks.md 生成并通过用户审阅后，必须先执行本步骤检查 superpowers，然后才能进入阶段四（实现）。不检查直接进入实现的违反工作流纪律，等同于跳步。本规则适用于 Path A 和 Path B。**

### 流程

1. **调用 Skill 工具** — 根据 tasks.md 的任务范围，加载可能适用的 superpowers：
   - `superpowers:test-driven-development`（如果 tasks 涉及 TypeScript/Java/Python 等代码改动）
   - `superpowers:verification-before-completion`
   - 根据 tasks.md 内容判断是否适用其他 superpowers

2. **遵循技能指导** — 如果技能包含检查清单，通过 TaskCreate 创建对应的 todo 项

3. **覆盖默认行为** — 已加载的技能中的规则优先于本 SKILL.md 中的通用规则

> **⚠️ 刚性技能（Rigid）优先级高于实现流程**
>
> 已加载的 superpowers 分为两种：
>
> | 类型 | 说明 | 示例 |
> |------|------|------|
> | **Rigid（刚性）** | 铁律不可协商。其每条规则必须严格遵循，**覆盖默认实现指令** | `test-driven-development`、`verification-before-completion` |
> | **Flexible（灵活）** | 提供参考模式和建议，可根据上下文调整 | `writing-skills`、`frontend-design` |
>
> **如果加载了 Rigid 技能，进入实现前必须先做以下声明，并获得用户确认：**
>
> ```
> "我已确认已加载 [rigid-skill-name]。该技能的以下纪律将覆盖默认实现行为："
>   - [纪律 1：例如"任何生产代码必须先有失败测试"]
>   - [纪律 2]
> ```

### Rigid 技能声明模板（加载后立即执行）

加载完所有 superpowers 后，按以下格式向用户声明：

```
## ✅ Superpowers 门闸通过

### 已加载的技能

| 技能 | 类型 | 对本变更的要求 |
|------|------|---------------|
| test-driven-development | 🔴 **Rigid** | 每个代码行为改动必须先写测试、看失败、再写实现 |

### Rigid 纪律确认

进入实现前，以下 rigid 纪律将覆盖默认实现流程：
- `test-driven-development` 的铁律：**NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST**
- 配置文件、SKILL.md 模板、markdown 文件豁免 TDD

用户确认后，才能进入阶段四。
```

**声明后等待用户确认。用户未确认前不得进入实现阶段。**

### 安全检查清单（增强版）

- [ ] proposal.md 已生成并通过 spec-hardener
- [ ] specs/ 已生成并通过 spec-hardener
- [ ] design.md 已生成
- [ ] tasks.md 已生成
- [ ] 📝 **实现计划已生成**（superpowers:writing-plans 完成，存于 `docs/superpowers/plans/`）
- [ ] 用户已审阅并批准所有 SDD 文档及实现计划
- [ ] 🔍 **Superpowers 技能已加载**（Skill 工具已调用）
- [ ] 🚨 **Rigid 纪律已向用户声明并获得确认**
- [ ] Path A 检查项：Git 分支已从 main 岔出
- [ ] Path B 检查项：OpenSpec change 已创建，brainstorming 文件已产出

### 🚩 Red Flags — 你正在绕过 Superpowers 检查

> 以下每一个想法都是一个危险信号。**任何一个出现 → 立即停止 → 回到本步骤执行 superpowers 检查。**

| 想法 | 现实 |
|------|------|
| "tasks + plan 都完成了，直接实现吧" | ❌ 必须先走完 3.8 语言规范 → 3.9 用户确认 → Superpowers 门禁。plan 生成 ≠ 可以跳过后续步骤。 |
| "tasks 完成了，直接进入实现吧" | ❌ 必须先检查 superpowers。顺序不可颠倒。 |
| "这个变更很简单，不需要检查" | 只要有 1% 的可能性适用，就**必须**检查。 |
| "我知道 TDD 是什么，不用加载技能" | 技能会更新。加载当前版本才有效。 |
| "先搞快点，后面再补测试" | 补 = 不补。不可协商的纪律。 |
| "子代理一次性写代码效率高，TDD 太慢" | TDD 铁律优先于效率。质量不可妥协。 |
| "已经改了代码，回头补测试也一样" | 测试-after 和 TDD 不等价。测试-after 验证的是"代码做了什么"，不是"代码应该做什么"。 |

---

### 🅰️🅱️ 阶段四（共享）：TDD 实现

```mermaid
flowchart TD
    CHK["⛔ 门闸通过"] --> BRANCH{"Path B 且<br/>分支未创建？"}
    BRANCH -->|"是（Path B）"| BR["创建 git 分支<br/>基于 change 名"]
    BRANCH -->|"否（Path A）"| NEXT{"还有未完成的 task ？"}
    BR --> NEXT
    NEXT -->|"有"| J{"涉及代码<br/>行为改动？"}
    J -->|"是"| RED["🔴 RED<br/>编写测试<br/>预期失败"]
    J -->|"否"| TT{"Task 具体类型？"}
    TT -->|"纯配置 / markdown /<br>SKILL.md / Shell"| DIR["直接实现"]
    TT -->|"测试框架<br>基础设施搭建"| FRAME["先创建框架<br>后续代码用 TDD"]
    RED --> GREEN["🟢 GREEN<br/>写最小实现<br/>通过测试"]
    GREEN --> REFACTOR["🔵 REFACTOR<br/>重构优化<br/>保持测试通过"]
    REFACTOR --> MARK["✅ 标记完成"]
    DIR --> MARK
    FRAME --> MARK
    MARK --> NEXT
    NEXT -->|"无"| CA["4.4 code-audit"]
    CA -->|"通过"| SYNC["openspec sync --change"]
    CA -->|"失败"| REPAIR["修复后重跑"]
    REPAIR --> CA
    SYNC --> END["4.5 分支结束处理<br/>提交 / PR / 保留 / 丢弃"]
```

### 核心原则

- **实现阶段必须遵循 TDD（Red → Green → Refactor）纪律**
- 每个涉及代码行为改动的 task，第一步永远是写测试（RED），不是看实现细节
- 配置文件、SKILL.md 模板、markdown 文件豁免 TDD

#### 4.1 准备工作

**Path A：**

```bash
CHANGE=$(git branch --show-current)
PLAN_FILE="docs/superpowers/plans/$(date +%Y-%m-%d)-$CHANGE.md"
```

**Path B：** 超powers 门禁通过后，**先创建 git 分支**，再进入 TDD 循环：

```bash
# 获取 change 名
CHANGE=$(ls openspec/changes/ | sort -r | head -1)
# 创建分支
git stash push -m "reef-start-auto-stash" 2>/dev/null || true
git checkout main && git fetch origin main && git reset --hard origin/main
git checkout -b "$CHANGE"
git stash pop 2>/dev/null || true
# 记录计划文件路径
PLAN_FILE="docs/superpowers/plans/$(date +%Y-%m-%d)-$CHANGE.md"
```

如果 `$PLAN_FILE` 存在，读取实现计划，按 plan 中的 task 分解顺序逐 task 实现。计划中的每个 task 已包含完整的文件路径、测试代码、实现代码和提交步骤。

#### 4.2 逐 task TDD 实现

**🔴 RED — 先写测试**
- 根据 spec 的 Scenario 编写单元测试
- 运行测试，确认失败（红）
- 如果测试意外通过了，说明测试写的太弱，需改进
- **不写实现代码**

**🟢 GREEN — 最小实现**
- 只写让当前测试通过的最小代码量
- 不提前实现未测试的功能
- 运行测试，确认全绿
- 如果感觉"这段代码还没写完"，那是正常的 — 下一个 task 会覆盖

**🔵 REFACTOR — 保持测试通过的前提下重构**
- 清理重复代码、提取函数、重命名
- 保持测试运行通过
- 不改变行为

**完成一个 task 后：**
1. 标记 tasks.md 中对应项为 `- [x]`
2. 如 `$PLAN_FILE` 存在，同步标记 plan 中对应步骤为 `- [x]`
3. 运行完整测试套件确认没有回归
4. 进入下一个 task（参照 plan 中的步骤顺序）
5. 如遇到阻塞或模糊需求，暂停并询问用户

#### 4.3 全部任务完成后的 code-audit

加载 `reef:reef-review` skill。检测变更范围，并行派发 agent。全部通过后执行 `openspec sync --change "$CHANGE"`。

#### 4.4 分支结束处理

询问用户：**创建提交 / 创建 PR / 保留分支 / 丢弃分支**

| 操作 | 说明 |
|------|------|
| 创建提交 | 中文 message + Issue URL（Path A 有则加，Path B 可选） + PRD 链接（如有） |
| 创建 PR | `git push -u origin "$CHANGE"` → `gh pr create` |
| 保留分支 | 报告分支名和变更位置 |
| 丢弃分支 | 用户确认后删除 |

## 关键原则

- **先理解，再设计，最后实现** — 不要跳过 SDD 直接写代码
- **MCP 无关** — 不绑定特定 Issue 跟踪 / 知识库 / 设计工具服务，通过能力映射动态适配
- **划红线比列功能更重要** — "不做什么"段是 SDD 的脊椎
- **路径意识** — 每次回复开头声明当前路径（Path A / Path B）和阶段编号

## 注意事项

- 每个 MCP provider 的 skill 指南按读写方向拆分，位于 `.claude/skills/deepstorm-mcp-{service}-{op}/SKILL.md`。各步骤已硬编码对应操作路径，AI 根据上下文读取正确指南即可
- 旧版 `references/jira-start-feishu.md` 和 `references/jira-start-figma.md` 已移入对应 deepstorm-mcp-* 指南，无需单独引用
- 如果 Issue 有子任务或关联 Issue，提及但先专注主 Issue（仅 Path A）
- 提交时始终在 commit message 中包含 issue 引用（Path A 必含，Path B 可选）

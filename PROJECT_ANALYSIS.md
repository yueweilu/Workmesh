# AionUi 项目深度架构分析文档

## 1. 项目概览 (Project Overview)

AionUi 是一个基于 Electron 的现代化桌面应用，旨在为命令行 AI 代理（如 Gemini CLI）提供图形化界面（GUI）。它不仅仅是一个简单的 Shell 包装器，而是通过 SDK 集成的方式，将 AI 智能体的核心逻辑（`@office-ai/aioncli-core`）内嵌到应用程序中，实现了文件管理、多模态交互、技能扩展（Skills）和 MCP（Model Context Protocol）协议的支持。

### 核心技术栈

- **前端 (Renderer):** React 19, Arco Design (UI 组件库), TailwindCSS/UnoCSS (样式), Vite (构建).
- **主进程 (Main):** Electron, Node.js.
- **智能体核心 (Agent):** `@office-ai/aioncli-core` (Gemini SDK), Node.js Child Process (多进程模型).
- **通信 (IPC):** 自研 Bridge 模式 (基于 Electron IPC 的强类型封装).
- **存储 (Storage):** `better-sqlite3` (结构化数据), JSON 文件 (配置与历史), 文件系统.

---

## 2. 系统架构 (System Architecture)

该项目采用了 **主进程-渲染进程-工作进程 (Main-Renderer-Worker)** 的三层分离架构，以确保 UI 的流畅性和 AI 任务的稳定性。

```mermaid
graph TD
    User[用户界面 (Renderer)] <-->|IPC Bridge| Main[主进程 (Main Process)]
    Main <-->|Fork/Pipe| Worker[工作进程 (Worker Process)]

    subgraph "Renderer Process (React)"
        UI[聊天界面 / 设置 / 预览]
        Hooks[Hooks & Context]
    end

    subgraph "Main Process (Node.js)"
        WindowManager[窗口管理]
        Bridge[IPC 路由与处理]
        Storage[配置与数据库管理]
        AgentManager[智能体管理器 (GeminiAgentManager)]
    end

    subgraph "Worker Process (独立线程)"
        GeminiAgent[GeminiAgent 实例]
        AionCliCore[aioncli-core SDK]
        Tools[工具执行 (Shell/Python/JS)]
    end
```

### 2.1 关键目录结构映射

| 路径             | 说明           | 核心职责                                                                    |
| :--------------- | :------------- | :-------------------------------------------------------------------------- |
| `src/renderer/`  | 前端界面代码   | 负责所有 UI 展示、组件渲染、用户交互。                                      |
| `src/adapter/`   | 适配层         | 将 Electron 的原生能力暴露给 Web 环境（如窗口控制）。                       |
| `src/process/`   | 主进程业务逻辑 | **核心中枢**。包含数据库、文件桥接、Agent 管理器、初始化逻辑。              |
| `src/worker/`    | 子进程入口     | 定义了实际运行 AI 逻辑的独立进程代码，避免阻塞 UI 主线程。                  |
| `src/agent/`     | 智能体实现     | **大脑**。封装了 `GeminiAgent` 类，负责与 LLM 交互、工具调度、Prompt 组装。 |
| `src/common/`    | 公共模块       | 定义类型、常量、IPC 桥接接口 (`ipcBridge.ts`)、存储工具类。                 |
| `src/webserver/` | Web 服务       | 提供 HTTP/WebSocket 接口，支持浏览器远程访问模式。                          |
| `skills/`        | 技能库         | 存放内置的 Python/JS 技能脚本和定义文件 (`SKILL.md`)。                      |

---

## 3. 核心功能与工作流程 (Workflows)

### 3.1 启动与初始化 (Startup)

1.  **入口**: `src/index.ts` 启动 Electron，创建主窗口。
2.  **存储初始化**: `src/process/initStorage.ts` 被调用。
    - 它会扫描 `ASSISTANT_PRESETS`（预设助手列表）。
    - 将内置的 `rules` (规则) 和 `skills` (技能) 复制到用户的应用数据目录。
    - 初始化 SQLite 数据库。
3.  **Agent 检测**: `AcpDetector` 扫描系统环境变量，检测是否安装了外部 CLI 工具（如 Claude Code）。

### 3.2 聊天与消息发送 (Chat Loop)

这是一个典型的异步流式处理流程：

1.  **用户输入**: 前端 `GeminiChat.tsx` 获取用户输入。
2.  **IPC 调用**: 调用 `ipcBridge.geminiConversation.sendMessage`。
3.  **主进程转发**: `src/process/bridge/geminiConversationBridge.ts` 接收请求，找到对应的 `GeminiAgentManager` 实例。
4.  **任务分发**: `GeminiAgentManager` 将消息通过 `pipe.call` 发送给后台 Worker (`src/worker/gemini.ts`)。
5.  **AI 思考 (Worker)**:
    - `src/worker/gemini.ts` 调用 `agent.send()`。
    - `src/agent/gemini/index.ts` (GeminiAgent) 组装 Prompt（包含系统规则、技能描述）。
    - 调用 `@office-ai/aioncli-core` 与 Google API 通信。
6.  **流式响应**:
    - LLM 返回数据块 (Chunk) 或工具调用请求 (Tool Call)。
    - Worker 通过 `pipe` 将事件回传给主进程。
    - 主进程通过 `ipcBridge` 将事件转发给前端渲染。

### 3.3 工具与技能执行 (Tools & Skills)

这是 AionUi 最强大的部分，支持 **原生工具** 和 **扩展技能**。

#### A. 原生工具 (Native Tools)

- **定义**: 直接在 TypeScript 代码中实现的工具，如 `read_file`, `run_shell_command`。
- **位置**: `@office-ai/aioncli-core` 内部及 `src/agent/gemini/cli/tools/`。
- **流程**: AI 发出 JSON 指令 -> SDK 解析 -> 执行 TS 函数 -> 返回结果。

#### B. 扩展技能 (Skills)

- **定义**: 基于文件的能力包，通常包含 `SKILL.md` (描述) 和 Python 脚本。
- **位置**: `skills/` 目录。
- **流程**:
  1.  **加载**: 启动时，`GeminiAgentManager` 读取 `SKILL.md` 的 Frontmatter。
  2.  **注入**: 将技能描述注入到 System Prompt 中。
  3.  **触发**: 用户提问 -> AI 决定使用技能 -> AI 生成 `run_shell_command("python skills/.../script.py")` 指令。
  4.  **执行**: AionUi 的 Shell 工具执行该 Python 脚本并捕获 stdout 输出。

### 3.4 全局根上下文 (Global Context) - _[新功能]_

这是最新添加的功能，允许用户自定义全局 AI 行为。

- **配置**: 用户在 UI 设置路径，保存到 `ConfigStorage` (`globalContextFilePath`)。
- **注入**: `GeminiAgentManager` 在初始化 Worker 时，读取该文件内容。
- **执行**: `GeminiAgent` (`src/agent/gemini/index.ts`) 在发送消息前，强制将此内容拼接到 System Prompt 的最前端，确保最高优先级。

---

## 4. 关键设计模式

### 4.1 Bridge 模式 (Type-Safe IPC)

项目没有直接使用 `ipcMain.on` 和 `ipcRenderer.send`，而是封装了一套 `bridge` (`src/common/ipcBridge.ts`)。

- **优势**: 实现了前后端通信的强类型约束。前端调用 `ipcBridge.fs.readFile` 时，TypeScript 会自动提示参数类型和返回值类型。

### 4.2 代理管理器 (Agent Manager Pattern)

`src/process/task/BaseAgentManager.ts` 定义了通用的代理行为。

- `GeminiAgentManager`: 管理内置 Gemini。
- `AcpAgentManager`: 管理外部进程（如 Claude Code）。
- 这种设计使得项目可以轻松扩展支持其他的 AI 模型或 CLI 工具。

### 4.3 预设系统 (Preset System)

`src/common/presets/assistantPresets.ts` 定义了所有“开箱即用”的助手。

- 通过配置化数据（JSON/Object）驱动助手的创建。
- 只需添加配置项，系统就会自动完成资源复制、数据库注册和 UI 渲染。

---

## 5. 扩展开发指南

### 如何添加新助手？

1.  在 `src/common/presets/assistantPresets.ts` 中添加配置。
2.  在 `assistant/` 下创建对应的 `.md` 提示词文件。

### 如何开发新技能？

1.  在 `skills/` 下新建目录。
2.  编写 `SKILL.md` 定义工具接口。
3.  编写 Python/JS 脚本实现逻辑。
4.  在设置中导入或将其加入预设。

### 如何修改 UI？

1.  UI 组件位于 `src/renderer/components`。
2.  页面位于 `src/renderer/pages`。
3.  修改后，Webpack HMR 会自动热更新。

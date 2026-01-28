# AionUi UI 层重构方案

> **目标**: 在保持底层架构不变的情况下，重新设计 UI 层创建新工程

---

## 1. 可行性分析

### ✅ 为什么可以重构 UI？

AionUi 采用了**清晰的分层架构**，UI 层与业务逻辑完全解耦：

```
┌─────────────────────────────────────┐
│   UI 层 (可替换)                     │  ← 你要改的部分
│   src/renderer/                     │
│   - React 组件                       │
│   - 页面布局                         │
│   - 样式主题                         │
└─────────────┬───────────────────────┘
              │ IPC Bridge (类型安全接口)
┌─────────────▼───────────────────────┐
│   业务逻辑层 (保持不变)               │  ← 不需要改
│   src/process/                      │
│   - Agent 管理                       │
│   - 数据存储                         │
│   - 文件操作                         │
└─────────────┬───────────────────────┘
              │
┌─────────────▼───────────────────────┐
│   核心层 (保持不变)                   │  ← 不需要改
│   src/agent/, src/worker/          │
│   - AI 代理                          │
│   - 工具执行                         │
└─────────────────────────────────────┘
```

### 🔑 关键优势

1. **IPC Bridge 抽象** - 前后端通过类型安全的接口通信，UI 层只需调用 API
2. **无业务逻辑耦合** - UI 层不包含任何 AI 逻辑，只负责展示和交互
3. **配置化驱动** - 主题、布局、样式都可以独立配置
4. **模块化设计** - 组件之间低耦合，易于替换

---

## 2. 重构方案

### 方案 A: 完全独立新工程（推荐）

**适用场景**: 想要完全不同的 UI 风格和交互方式

#### 目录结构

```
my-aionui-app/
├── package.json              # 新的依赖配置
├── src/
│   ├── main/                 # 复用原主进程代码（符号链接）
│   │   ├── index.ts          → ../../AionUi/src/index.ts
│   │   ├── process/          → ../../AionUi/src/process/
│   │   ├── agent/            → ../../AionUi/src/agent/
│   │   ├── worker/           → ../../AionUi/src/worker/
│   │   └── common/           → ../../AionUi/src/common/
│   │
│   ├── renderer/             # 全新的 UI 层
│   │   ├── App.tsx           # 你的新 UI 入口
│   │   ├── pages/            # 你的页面
│   │   ├── components/       # 你的组件
│   │   ├── styles/           # 你的样式
│   │   └── hooks/            # 你的 Hooks
│   │
│   └── preload.ts            → ../../AionUi/src/preload.ts
│
├── public/                   # 你的静态资源
├── config/                   # 你的构建配置
└── README.md
```

#### 实施步骤

```bash
# 1. 创建新工程
mkdir my-aionui-app
cd my-aionui-app
npm init -y

# 2. 安装依赖（选择你喜欢的 UI 框架）
npm install electron react react-dom
npm install -D typescript webpack electron-forge

# 3. 创建符号链接（复用底层代码）
mkdir -p src/main
ln -s ../../../AionUi/src/process src/main/process
ln -s ../../../AionUi/src/agent src/main/agent
ln -s ../../../AionUi/src/worker src/main/worker
ln -s ../../../AionUi/src/common src/main/common

# 4. 创建你的 UI 层
mkdir -p src/renderer
```

#### 核心代码示例

```typescript
// src/renderer/App.tsx - 你的新 UI 入口
import { ipcBridge } from '@/common/ipcBridge'; // 复用 IPC Bridge
import { useState, useEffect } from 'react';

export const App = () => {
  const [conversations, setConversations] = useState([]);

  useEffect(() => {
    // 使用原有的 IPC 接口获取数据
    ipcBridge.database.getUserConversations({ page: 1, pageSize: 20 })
      .then(setConversations);
  }, []);

  const handleSendMessage = async (input: string) => {
    // 使用原有的 IPC 接口发送消息
    await ipcBridge.geminiConversation.sendMessage({
      input,
      msg_id: generateId(),
      conversation_id: currentConversationId,
    });
  };

  return (
    <div className="my-custom-ui">
      {/* 你的全新 UI 设计 */}
      <YourCustomSidebar conversations={conversations} />
      <YourCustomChatArea onSend={handleSendMessage} />
    </div>
  );
};
```

---

### 方案 B: Fork 并修改（适合大改）

**适用场景**: 想要保留部分原有 UI，但大幅修改

```bash
# 1. Fork 原仓库
git clone https://github.com/iOfficeAI/AionUi.git my-aionui-app
cd my-aionui-app

# 2. 创建新分支
git checkout -b ui-redesign

# 3. 删除原有 UI 层
rm -rf src/renderer/*

# 4. 创建你的新 UI
# ... 开发你的 UI
```

---

### 方案 C: 主题定制（适合小改）

**适用场景**: 只想改变视觉风格，不改变交互逻辑

```typescript
// src/renderer/theme/myTheme.ts
export const myCustomTheme = {
  colors: {
    primary: '#FF6B6B',
    secondary: '#4ECDC4',
    background: '#1A1A2E',
    surface: '#16213E',
    text: '#EAEAEA',
  },
  typography: {
    fontFamily: 'Inter, sans-serif',
    fontSize: {
      small: '12px',
      medium: '14px',
      large: '16px',
    },
  },
  layout: {
    sidebarWidth: '280px',
    headerHeight: '60px',
  },
};
```

---

## 3. 可选的 UI 框架

### 选项 1: Material-UI (MUI)

```bash
npm install @mui/material @emotion/react @emotion/styled
```

```typescript
// src/renderer/App.tsx
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Box, AppBar, Drawer } from '@mui/material';

const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: { main: '#90caf9' },
  },
});

export const App = () => (
  <ThemeProvider theme={theme}>
    <CssBaseline />
    <Box sx={{ display: 'flex' }}>
      <AppBar position="fixed">
        {/* 你的顶栏 */}
      </AppBar>
      <Drawer variant="permanent">
        {/* 你的侧边栏 */}
      </Drawer>
      <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
        {/* 你的主内容区 */}
      </Box>
    </Box>
  </ThemeProvider>
);
```

### 选项 2: Ant Design

```bash
npm install antd
```

```typescript
// src/renderer/App.tsx
import { ConfigProvider, Layout, Menu, theme } from 'antd';

const { Header, Sider, Content } = Layout;

export const App = () => (
  <ConfigProvider theme={{ algorithm: theme.darkAlgorithm }}>
    <Layout style={{ minHeight: '100vh' }}>
      <Sider>
        <Menu theme="dark" mode="inline" items={menuItems} />
      </Sider>
      <Layout>
        <Header style={{ background: '#001529' }}>
          {/* 你的顶栏 */}
        </Header>
        <Content style={{ margin: '24px 16px 0' }}>
          {/* 你的主内容区 */}
        </Content>
      </Layout>
    </Layout>
  </ConfigProvider>
);
```

### 选项 3: Chakra UI

```bash
npm install @chakra-ui/react @emotion/react @emotion/styled framer-motion
```

```typescript
// src/renderer/App.tsx
import { ChakraProvider, Box, Flex, VStack } from '@chakra-ui/react';

export const App = () => (
  <ChakraProvider>
    <Flex h="100vh">
      <Box w="250px" bg="gray.800">
        {/* 你的侧边栏 */}
      </Box>
      <VStack flex="1" bg="gray.900">
        {/* 你的主内容区 */}
      </VStack>
    </Flex>
  </ChakraProvider>
);
```

### 选项 4: Tailwind CSS + Headless UI

```bash
npm install tailwindcss @headlessui/react
```

```typescript
// src/renderer/App.tsx
import { Dialog, Transition } from '@headlessui/react';

export const App = () => (
  <div className="flex h-screen bg-gray-900">
    <aside className="w-64 bg-gray-800 border-r border-gray-700">
      {/* 你的侧边栏 */}
    </aside>
    <main className="flex-1 flex flex-col">
      <header className="h-16 bg-gray-800 border-b border-gray-700">
        {/* 你的顶栏 */}
      </header>
      <div className="flex-1 overflow-auto p-4">
        {/* 你的主内容区 */}
      </div>
    </main>
  </div>
);
```

---

## 4. 必须保留的核心接口

### 4.1 IPC Bridge 调用

```typescript
// ✅ 必须使用原有的 IPC Bridge
import { ipcBridge } from '@/common/ipcBridge';

// 会话管理
ipcBridge.conversation.create(params);
ipcBridge.conversation.get({ id });
ipcBridge.conversation.update({ id, updates });

// 消息发送
ipcBridge.geminiConversation.sendMessage(params);
ipcBridge.geminiConversation.responseStream.subscribe(handler);

// 文件操作
ipcBridge.fs.readFile({ path });
ipcBridge.fs.writeFile({ path, data });

// 系统配置
ipcBridge.application.systemInfo();
ipcBridge.mode.getModelConfig();
```

### 4.2 类型定义

```typescript
// ✅ 必须使用原有的类型定义
import type { TChatConversation, TMessage, IProvider, TProviderWithModel } from '@/common/storage';

import type { ISendMessageParams, IResponseMessage } from '@/common/ipcBridge';
```

### 4.3 事件监听

```typescript
// ✅ 必须监听原有的事件
useEffect(() => {
  // 监听消息流
  const unsubscribe = ipcBridge.geminiConversation.responseStream.subscribe((msg) => {
    if (msg.type === 'text') {
      // 更新 UI
    }
  });

  // 监听文件变化
  const unsubscribeFile = ipcBridge.fileWatch.fileChanged.subscribe((event) => {
    // 刷新预览
  });

  return () => {
    unsubscribe();
    unsubscribeFile();
  };
}, []);
```

---

## 5. 推荐的项目结构

```
my-aionui-app/
├── src/
│   ├── main/                      # 主进程（复用原代码）
│   │   ├── index.ts               # 入口文件
│   │   ├── process/               → 符号链接到 AionUi
│   │   ├── agent/                 → 符号链接到 AionUi
│   │   ├── worker/                → 符号链接到 AionUi
│   │   └── common/                → 符号链接到 AionUi
│   │
│   ├── renderer/                  # 渲染进程（全新 UI）
│   │   ├── App.tsx                # 应用入口
│   │   ├── main.tsx               # React 挂载
│   │   │
│   │   ├── layouts/               # 布局组件
│   │   │   ├── MainLayout.tsx
│   │   │   └── ChatLayout.tsx
│   │   │
│   │   ├── pages/                 # 页面
│   │   │   ├── ConversationPage.tsx
│   │   │   ├── SettingsPage.tsx
│   │   │   └── HomePage.tsx
│   │   │
│   │   ├── components/            # 通用组件
│   │   │   ├── ChatMessage.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── MessageInput.tsx
│   │   │   └── FilePreview.tsx
│   │   │
│   │   ├── hooks/                 # 自定义 Hooks
│   │   │   ├── useConversation.ts
│   │   │   ├── useMessages.ts
│   │   │   └── useSettings.ts
│   │   │
│   │   ├── stores/                # 状态管理
│   │   │   ├── conversationStore.ts
│   │   │   └── settingsStore.ts
│   │   │
│   │   ├── styles/                # 样式
│   │   │   ├── globals.css
│   │   │   └── theme.ts
│   │   │
│   │   └── utils/                 # 工具函数
│   │       ├── formatters.ts
│   │       └── validators.ts
│   │
│   └── preload.ts                 # 预加载脚本（复用）
│
├── public/                        # 静态资源
│   ├── index.html
│   └── assets/
│
├── config/                        # 构建配置
│   ├── webpack.main.config.js
│   └── webpack.renderer.config.js
│
├── package.json
├── tsconfig.json
└── README.md
```

---

## 6. 实战示例：创建简约风格 UI

### 步骤 1: 初始化项目

```bash
# 创建项目
mkdir aionui-minimal
cd aionui-minimal

# 初始化
npm init -y

# 安装核心依赖
npm install electron react react-dom
npm install -D @types/react @types/react-dom typescript webpack ts-loader
npm install -D electron-forge @electron-forge/cli

# 安装 UI 库（选择 Tailwind CSS）
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init
```

### 步骤 2: 创建符号链接

```bash
# 创建目录
mkdir -p src/main

# 链接到原 AionUi 代码（假设在同级目录）
ln -s ../../../AionUi/src/process src/main/process
ln -s ../../../AionUi/src/agent src/main/agent
ln -s ../../../AionUi/src/worker src/main/worker
ln -s ../../../AionUi/src/common src/main/common
ln -s ../../AionUi/src/preload.ts src/preload.ts
```

### 步骤 3: 创建主进程入口

```typescript
// src/main/index.ts
import { app, BrowserWindow } from 'electron';
import path from 'path';

// 复用原有的初始化逻辑
import { initializeProcess } from './process';

let mainWindow: BrowserWindow;

const createWindow = () => {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, '../preload.js'),
    },
  });

  mainWindow.loadFile('public/index.html');
};

app.whenReady().then(async () => {
  await initializeProcess(); // 复用原有初始化
  createWindow();
});
```

### 步骤 4: 创建简约 UI

```typescript
// src/renderer/App.tsx
import { useState, useEffect } from 'react';
import { ipcBridge } from '@/common/ipcBridge';

export const App = () => {
  const [conversations, setConversations] = useState([]);
  const [currentId, setCurrentId] = useState<string | null>(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');

  // 加载会话列表
  useEffect(() => {
    ipcBridge.database.getUserConversations({ page: 1, pageSize: 50 })
      .then(setConversations);
  }, []);

  // 加载消息
  useEffect(() => {
    if (!currentId) return;
    ipcBridge.database.getConversationMessages({ conversation_id: currentId })
      .then(setMessages);
  }, [currentId]);

  // 监听新消息
  useEffect(() => {
    const unsubscribe = ipcBridge.geminiConversation.responseStream.subscribe((msg) => {
      if (msg.conversation_id === currentId) {
        setMessages(prev => [...prev, msg.data]);
      }
    });
    return unsubscribe;
  }, [currentId]);

  // 发送消息
  const handleSend = async () => {
    if (!input.trim() || !currentId) return;

    await ipcBridge.geminiConversation.sendMessage({
      input,
      msg_id: Date.now().toString(),
      conversation_id: currentId,
    });

    setInput('');
  };

  return (
    <div className="flex h-screen bg-gray-950 text-gray-100">
      {/* 侧边栏 */}
      <aside className="w-64 bg-gray-900 border-r border-gray-800">
        <div className="p-4">
          <h1 className="text-xl font-bold">AionUI Minimal</h1>
        </div>
        <div className="overflow-auto">
          {conversations.map(conv => (
            <button
              key={conv.id}
              onClick={() => setCurrentId(conv.id)}
              className={`w-full p-3 text-left hover:bg-gray-800 ${
                currentId === conv.id ? 'bg-gray-800' : ''
              }`}
            >
              {conv.name}
            </button>
          ))}
        </div>
      </aside>

      {/* 主内容区 */}
      <main className="flex-1 flex flex-col">
        {/* 消息列表 */}
        <div className="flex-1 overflow-auto p-4 space-y-4">
          {messages.map(msg => (
            <div
              key={msg.id}
              className={`p-3 rounded-lg ${
                msg.role === 'user'
                  ? 'bg-blue-600 ml-auto max-w-2xl'
                  : 'bg-gray-800 mr-auto max-w-2xl'
              }`}
            >
              {msg.content}
            </div>
          ))}
        </div>

        {/* 输入框 */}
        <div className="p-4 border-t border-gray-800">
          <div className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Type a message..."
              className="flex-1 px-4 py-2 bg-gray-800 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              onClick={handleSend}
              className="px-6 py-2 bg-blue-600 rounded-lg hover:bg-blue-700"
            >
              Send
            </button>
          </div>
        </div>
      </main>
    </div>
  );
};
```

### 步骤 5: 配置构建

```javascript
// webpack.renderer.config.js
module.exports = {
  entry: './src/renderer/main.tsx',
  output: {
    path: path.resolve(__dirname, 'dist/renderer'),
    filename: 'renderer.js',
  },
  module: {
    rules: [
      {
        test: /\.tsx?$/,
        use: 'ts-loader',
        exclude: /node_modules/,
      },
      {
        test: /\.css$/,
        use: ['style-loader', 'css-loader', 'postcss-loader'],
      },
    ],
  },
  resolve: {
    extensions: ['.tsx', '.ts', '.js'],
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
};
```

---

## 7. 注意事项

### ⚠️ 必须保持的部分

1. **IPC Bridge 接口** - 不能修改接口定义
2. **数据结构** - 会话、消息的数据结构必须兼容
3. **事件名称** - IPC 事件名称不能改变
4. **文件路径约定** - 工作空间、配置文件路径

### ✅ 可以自由修改的部分

1. **UI 框架** - React、Vue、Svelte 都可以
2. **样式系统** - CSS-in-JS、Tailwind、Sass 都可以
3. **状态管理** - Redux、Zustand、Jotai 都可以
4. **路由系统** - React Router、TanStack Router 都可以
5. **组件库** - MUI、Ant Design、Chakra UI 都可以

---

## 8. 快速启动模板

我为你准备了一个快速启动脚本：

```bash
#!/bin/bash
# create-aionui-app.sh

PROJECT_NAME=$1
AIONUI_PATH=$2

if [ -z "$PROJECT_NAME" ] || [ -z "$AIONUI_PATH" ]; then
  echo "Usage: ./create-aionui-app.sh <project-name> <path-to-aionui>"
  exit 1
fi

# 创建项目
mkdir $PROJECT_NAME
cd $PROJECT_NAME

# 初始化
npm init -y

# 安装依赖
npm install electron react react-dom
npm install -D typescript @types/react @types/react-dom
npm install -D webpack webpack-cli ts-loader
npm install -D tailwindcss postcss autoprefixer

# 创建目录结构
mkdir -p src/main src/renderer public

# 创建符号链接
ln -s $AIONUI_PATH/src/process src/main/process
ln -s $AIONUI_PATH/src/agent src/main/agent
ln -s $AIONUI_PATH/src/worker src/main/worker
ln -s $AIONUI_PATH/src/common src/main/common
ln -s $AIONUI_PATH/src/preload.ts src/preload.ts

echo "✅ Project created successfully!"
echo "📁 Project: $PROJECT_NAME"
echo "🔗 Linked to: $AIONUI_PATH"
```

使用方法：

```bash
chmod +x create-aionui-app.sh
./create-aionui-app.sh my-custom-ui ../AionUi
```

---

## 9. 总结

### ✅ 可行性：100%

- AionUi 的架构完全支持 UI 层独立开发
- IPC Bridge 提供了清晰的接口边界
- 底层逻辑与 UI 完全解耦

### 🎯 推荐方案

**方案 A（独立新工程）** 最适合你的需求：

- 保持底层架构不变
- 完全自由的 UI 设计
- 易于维护和升级

### 🚀 下一步

1. 选择你喜欢的 UI 框架
2. 使用快速启动脚本创建项目
3. 开始设计你的 UI
4. 复用所有 IPC Bridge 接口

**需要我帮你生成完整的项目模板吗？** 我可以为你创建一个开箱即用的项目结构！

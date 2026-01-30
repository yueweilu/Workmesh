# Google 账号与服务端账号绑定方案

> **方案类型**: OAuth 后自动绑定  
> **创建日期**: 2026-01-29  
> **适用项目**: AionUi  
> **难度**: ⭐⭐⭐ (中等)

---

## 📋 目录

1. [方案概述](#方案概述)
2. [架构设计](#架构设计)
3. [实现步骤](#实现步骤)
4. [服务端 API 设计](#服务端-api-设计)
5. [前端改动](#前端改动)
6. [数据库设计](#数据库设计)
7. [安全考虑](#安全考虑)
8. [测试方案](#测试方案)
9. [部署清单](#部署清单)

---

## 方案概述

### 核心思路

用户通过 **Google OAuth** 登录后，自动调用你的服务端 API 进行账号绑定或创建，实现：

- ✅ 用户只需一次 Google 登录
- ✅ 自动创建/绑定服务端账号
- ✅ 获取服务端 JWT Token
- ✅ 后续请求携带 Token 访问服务端

### 用户体验流程

```
用户点击"Google 登录"
    ↓
Google OAuth 授权页面
    ↓
授权成功，获取 Google 邮箱
    ↓
自动调用服务端绑定 API
    ↓
服务端创建/查找账号
    ↓
返回 JWT Token
    ↓
本地存储 Token
    ↓
登录完成
```

### 优势

- **用户体验好**: 一键登录，无需额外注册
- **实现简单**: 在现有 Google OAuth 基础上扩展
- **安全性高**: 利用 Google 的身份验证
- **维护成本低**: 不需要管理密码

---

## 架构设计

### 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      AionUi 客户端                           │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Google OAuth 登录流程                    │  │
│  │                                                        │  │
│  │  1. 用户点击登录                                      │  │
│  │  2. 打开 Google 授权页面                              │  │
│  │  3. 用户授权                                          │  │
│  │  4. 获取 Access Token                                 │  │
│  │  5. 获取用户信息 (email, name, picture)              │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           调用服务端绑定 API                          │  │
│  │                                                        │  │
│  │  POST /auth/bind-google                               │  │
│  │  Body: {                                              │  │
│  │    googleEmail: "user@gmail.com",                     │  │
│  │    googleId: "1234567890",                            │  │
│  │    name: "User Name",                                 │  │
│  │    picture: "https://..."                             │  │
│  │  }                                                     │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           存储服务端返回的 Token                      │  │
│  │                                                        │  │
│  │  localStorage:                                        │  │
│  │    - server.token: "eyJhbGc..."                       │  │
│  │    - server.userId: "uuid-1234"                       │  │
│  │    - server.user: { email, name, avatar }            │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                      你的服务端                              │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         POST /auth/bind-google                        │  │
│  │                                                        │  │
│  │  1. 接收 Google 账号信息                              │  │
│  │  2. 查询数据库是否存在该 googleId                     │  │
│  │  3. 不存在 → 创建新用户                               │  │
│  │     存在   → 更新最后登录时间                         │  │
│  │  4. 生成 JWT Token                                    │  │
│  │  5. 返回 Token 和用户信息                             │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              数据库 (users 表)                        │  │
│  │                                                        │  │
│  │  - id: uuid                                           │  │
│  │  - googleId: string (唯一索引)                        │  │
│  │  - email: string                                      │  │
│  │  - name: string                                       │  │
│  │  - avatar: string                                     │  │
│  │  - createdAt: timestamp                               │  │
│  │  - lastLogin: timestamp                               │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 数据流向

```
Google OAuth → AionUi 客户端 → 你的服务端 → 数据库
     ↓              ↓                ↓
  用户信息      存储 Token      创建/更新用户
```

---

## 实现步骤

### 步骤 1: 修改客户端 OAuth 登录逻辑

**文件**: `src/process/bridge/authBridge.ts`

**位置**: `ipcBridge.googleAuth.login.provider` 方法内

**改动内容**:

```typescript
// src/process/bridge/authBridge.ts

import { AuthType, clearCachedCredentialFile, Config, getOauthInfoWithCache, loginWithOauth, Storage } from '@office-ai/aioncli-core';
import { ipcBridge } from '../../common';
import * as fs from 'node:fs';

export function initAuthBridge(): void {
  // ... 现有的 status 处理器保持不变

  // Google OAuth 登录处理器
  ipcBridge.googleAuth.login.provider(async ({ proxy }) => {
    try {
      // ========== 第 1 步: Google OAuth 登录 ==========
      const config = new Config({
        proxy,
        sessionId: '',
        targetDir: '',
        debugMode: false,
        cwd: '',
        model: '',
      });

      const timeoutPromise = new Promise<null>((_, reject) => {
        setTimeout(() => reject(new Error('Login timed out after 2 minutes')), 2 * 60 * 1000);
      });

      const client = await Promise.race([loginWithOauth(AuthType.LOGIN_WITH_GOOGLE, config), timeoutPromise]);

      if (!client) {
        return { success: false, msg: 'Login failed: No client returned' };
      }

      // 短暂延迟确保凭证文件写入完成
      await new Promise((resolve) => setTimeout(resolve, 500));

      const oauthInfo = await getOauthInfoWithCache(proxy);

      if (!oauthInfo || !oauthInfo.email) {
        return {
          success: false,
          msg: 'Login completed but no credentials found',
        };
      }

      console.log('[Auth] Google login successful:', oauthInfo.email);

      // ========== 第 2 步: 调用服务端绑定 API ==========
      try {
        const serverResponse = await fetch('https://your-api.com/auth/bind-google', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            googleEmail: oauthInfo.email,
            googleId: oauthInfo.sub, // Google 用户唯一 ID
            name: oauthInfo.name || '', // 用户名
            picture: oauthInfo.picture || '', // 头像 URL
          }),
        });

        if (!serverResponse.ok) {
          throw new Error(`Server responded with ${serverResponse.status}`);
        }

        const serverData = await serverResponse.json();

        // ========== 第 3 步: 存储服务端返回的 Token ==========
        if (serverData.success && serverData.token) {
          // 使用 ipcBridge.config 存储到本地配置
          await ipcBridge.config.set('server.token', serverData.token);
          await ipcBridge.config.set('server.userId', serverData.userId);
          await ipcBridge.config.set('server.user', JSON.stringify(serverData.user));

          console.log('[Auth] Server binding successful, userId:', serverData.userId);

          return {
            success: true,
            data: {
              account: oauthInfo.email,
              serverUserId: serverData.userId,
              serverToken: serverData.token,
              serverUser: serverData.user,
            },
          };
        } else {
          // 服务端绑定失败，但 Google 登录成功
          console.warn('[Auth] Server binding failed:', serverData.message);
          return {
            success: true, // Google 登录成功
            data: {
              account: oauthInfo.email,
              serverBindingFailed: true,
              serverMessage: serverData.message,
            },
          };
        }
      } catch (serverError) {
        // 服务端请求失败，但 Google 登录成功
        console.error('[Auth] Failed to bind with server:', serverError);
        return {
          success: true, // Google 登录成功
          data: {
            account: oauthInfo.email,
            serverBindingFailed: true,
            serverError: serverError.message,
          },
        };
      }
    } catch (error) {
      console.error('[Auth] Login error:', error);
      return { success: false, msg: error.message || error.toString() };
    }
  });

  // ... 现有的 logout 处理器保持不变
}
```

### 步骤 2: 添加配置项定义

**文件**: `src/common/ipcBridge.ts` (如果需要类型定义)

**改动内容**:

```typescript
// 在 ipcBridge 定义中添加服务端相关的配置项
export interface ServerConfig {
  token?: string;
  userId?: string;
  user?: string; // JSON 字符串
}

// 如果需要，可以添加专门的服务端 API 接口
export const ipcBridge = {
  // ... 现有代码

  serverAuth: {
    // 获取服务端 Token
    getToken: createIpcBridge<void, string | null>('server-auth:get-token'),

    // 获取服务端用户信息
    getUser: createIpcBridge<void, any | null>('server-auth:get-user'),

    // 清除服务端登录信息
    clearServerAuth: createIpcBridge<void, boolean>('server-auth:clear'),
  },
};
```

### 步骤 3: 实现服务端 Token 获取工具

**文件**: `src/process/bridge/serverAuthBridge.ts` (新建)

**内容**:

```typescript
/**
 * @license
 * Copyright 2025 AionUi (aionui.com)
 * SPDX-License-Identifier: Apache-2.0
 */

import { ipcBridge } from '../../common';

export function initServerAuthBridge(): void {
  // 获取服务端 Token
  ipcBridge.serverAuth.getToken.provider(async () => {
    try {
      const token = await ipcBridge.config.get('server.token');
      return token || null;
    } catch {
      return null;
    }
  });

  // 获取服务端用户信息
  ipcBridge.serverAuth.getUser.provider(async () => {
    try {
      const userJson = await ipcBridge.config.get('server.user');
      if (userJson) {
        return JSON.parse(userJson);
      }
      return null;
    } catch {
      return null;
    }
  });

  // 清除服务端登录信息
  ipcBridge.serverAuth.clearServerAuth.provider(async () => {
    try {
      await ipcBridge.config.delete('server.token');
      await ipcBridge.config.delete('server.userId');
      await ipcBridge.config.delete('server.user');
      return true;
    } catch {
      return false;
    }
  });
}
```

**注册到主进程**:

```typescript
// src/process/bridge/index.ts
import { initAuthBridge } from './authBridge';
import { initServerAuthBridge } from './serverAuthBridge'; // 新增

export function initBridge(): void {
  initAuthBridge();
  initServerAuthBridge(); // 新增
  // ... 其他 bridge 初始化
}
```

### 步骤 4: 在需要的地方使用服务端 Token

**示例 1: 发送请求到服务端**

```typescript
// 任何需要调用服务端 API 的地方
async function callServerAPI(endpoint: string, data: any) {
  // 获取 Token
  const token = await ipcBridge.serverAuth.getToken.invoke();

  if (!token) {
    throw new Error('Not logged in to server');
  }

  // 发送请求
  const response = await fetch(`https://your-api.com${endpoint}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });

  return response.json();
}

// 使用示例
const result = await callServerAPI('/api/conversations', {
  title: 'New Conversation',
});
```

**示例 2: 在前端显示用户信息**

```tsx
// src/renderer/components/UserProfile.tsx
import { useEffect, useState } from 'react';
import { ipcBridge } from '@/common';

export function UserProfile() {
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    ipcBridge.serverAuth.getUser.invoke().then(setUser);
  }, []);

  if (!user) return null;

  return (
    <div className='user-profile'>
      <img src={user.avatar} alt={user.name} />
      <div>
        <div>{user.name}</div>
        <div>{user.email}</div>
      </div>
    </div>
  );
}
```

---

## 服务端 API 设计

### API 端点: POST /auth/bind-google

**请求格式**:

```http
POST /auth/bind-google HTTP/1.1
Host: your-api.com
Content-Type: application/json

{
  "googleEmail": "user@gmail.com",
  "googleId": "1234567890",
  "name": "User Name",
  "picture": "https://lh3.googleusercontent.com/..."
}
```

**响应格式 (成功)**:

```json
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "userId": "uuid-1234-5678-90ab",
  "user": {
    "id": "uuid-1234-5678-90ab",
    "email": "user@gmail.com",
    "name": "User Name",
    "avatar": "https://lh3.googleusercontent.com/...",
    "createdAt": "2026-01-29T10:00:00Z",
    "lastLogin": "2026-01-29T10:00:00Z"
  },
  "isNewUser": false
}
```

**响应格式 (失败)**:

```json
{
  "success": false,
  "message": "Invalid Google account",
  "code": "INVALID_GOOGLE_ACCOUNT"
}
```

### 服务端实现示例

#### Node.js + Express + MongoDB

```javascript
// routes/auth.js
const express = require('express');
const jwt = require('jsonwebtoken');
const { v4: uuidv4 } = require('uuid');
const User = require('../models/User');

const router = express.Router();

/**
 * POST /auth/bind-google
 * 绑定 Google 账号或创建新用户
 */
router.post('/bind-google', async (req, res) => {
  try {
    const { googleEmail, googleId, name, picture } = req.body;

    // 验证必填字段
    if (!googleEmail || !googleId) {
      return res.status(400).json({
        success: false,
        message: 'Missing required fields: googleEmail, googleId',
        code: 'MISSING_FIELDS',
      });
    }

    // 查找是否已存在该 Google 账号
    let user = await User.findOne({ googleId });

    if (user) {
      // 用户已存在，更新最后登录时间
      user.lastLogin = new Date();
      user.name = name || user.name; // 更新名称（如果提供）
      user.avatar = picture || user.avatar; // 更新头像（如果提供）
      await user.save();

      console.log(`[Auth] Existing user logged in: ${user.email}`);
    } else {
      // 新用户，创建账号
      user = new User({
        id: uuidv4(),
        googleId,
        email: googleEmail,
        name: name || googleEmail.split('@')[0],
        avatar: picture || '',
        createdAt: new Date(),
        lastLogin: new Date(),
      });
      await user.save();

      console.log(`[Auth] New user created: ${user.email}`);
    }

    // 生成 JWT Token
    const token = jwt.sign(
      {
        userId: user.id,
        email: user.email,
        googleId: user.googleId,
      },
      process.env.JWT_SECRET || 'your-secret-key',
      {
        expiresIn: '30d', // Token 有效期 30 天
      }
    );

    // 返回成功响应
    res.json({
      success: true,
      token,
      userId: user.id,
      user: {
        id: user.id,
        email: user.email,
        name: user.name,
        avatar: user.avatar,
        createdAt: user.createdAt,
        lastLogin: user.lastLogin,
      },
      isNewUser: !user.lastLogin || user.createdAt === user.lastLogin,
    });
  } catch (error) {
    console.error('[Auth] Error in bind-google:', error);
    res.status(500).json({
      success: false,
      message: 'Internal server error',
      code: 'SERVER_ERROR',
    });
  }
});

module.exports = router;
```

#### 用户模型 (MongoDB)

```javascript
// models/User.js
const mongoose = require('mongoose');

const userSchema = new mongoose.Schema({
  id: {
    type: String,
    required: true,
    unique: true,
  },
  googleId: {
    type: String,
    required: true,
    unique: true,
    index: true, // 添加索引提高查询性能
  },
  email: {
    type: String,
    required: true,
    unique: true,
    index: true,
  },
  name: {
    type: String,
    required: true,
  },
  avatar: {
    type: String,
    default: '',
  },
  createdAt: {
    type: Date,
    default: Date.now,
  },
  lastLogin: {
    type: Date,
    default: null,
  },
  // 可选：添加其他字段
  subscription: {
    type: String,
    enum: ['free', 'pro', 'enterprise'],
    default: 'free',
  },
  settings: {
    type: Object,
    default: {},
  },
});

module.exports = mongoose.model('User', userSchema);
```

#### JWT 验证中间件

```javascript
// middleware/auth.js
const jwt = require('jsonwebtoken');

/**
 * JWT 验证中间件
 * 用于保护需要登录的 API 端点
 */
function authenticateToken(req, res, next) {
  // 从 Authorization header 获取 token
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1]; // Bearer TOKEN

  if (!token) {
    return res.status(401).json({
      success: false,
      message: 'Access token required',
      code: 'NO_TOKEN',
    });
  }

  jwt.verify(token, process.env.JWT_SECRET || 'your-secret-key', (err, user) => {
    if (err) {
      return res.status(403).json({
        success: false,
        message: 'Invalid or expired token',
        code: 'INVALID_TOKEN',
      });
    }

    // 将用户信息附加到 request 对象
    req.user = user;
    next();
  });
}

module.exports = { authenticateToken };
```

#### 使用中间件保护 API

```javascript
// routes/api.js
const express = require('express');
const { authenticateToken } = require('../middleware/auth');

const router = express.Router();

/**
 * 示例：获取用户的对话列表
 * 需要登录才能访问
 */
router.get('/conversations', authenticateToken, async (req, res) => {
  try {
    const userId = req.user.userId; // 从 JWT 中获取用户 ID

    // 查询该用户的对话
    const conversations = await Conversation.find({ userId });

    res.json({
      success: true,
      conversations,
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: 'Failed to fetch conversations',
    });
  }
});

/**
 * 示例：创建新对话
 */
router.post('/conversations', authenticateToken, async (req, res) => {
  try {
    const userId = req.user.userId;
    const { title, type } = req.body;

    const conversation = new Conversation({
      id: uuidv4(),
      userId,
      title,
      type,
      createdAt: new Date(),
    });

    await conversation.save();

    res.json({
      success: true,
      conversation,
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: 'Failed to create conversation',
    });
  }
});

module.exports = router;
```

---

## 数据库设计

### MySQL 版本

```sql
-- 用户表
CREATE TABLE users (
  id VARCHAR(36) PRIMARY KEY,
  google_id VARCHAR(255) NOT NULL UNIQUE,
  email VARCHAR(255) NOT NULL UNIQUE,
  name VARCHAR(255) NOT NULL,
  avatar TEXT,
  subscription ENUM('free', 'pro', 'enterprise') DEFAULT 'free',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_login TIMESTAMP NULL,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  INDEX idx_google_id (google_id),
  INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 对话表（示例）
CREATE TABLE conversations (
  id VARCHAR(36) PRIMARY KEY,
  user_id VARCHAR(36) NOT NULL,
  title VARCHAR(255) NOT NULL,
  type ENUM('gemini', 'claude', 'codex') NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### PostgreSQL 版本

```sql
-- 用户表
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  google_id VARCHAR(255) NOT NULL UNIQUE,
  email VARCHAR(255) NOT NULL UNIQUE,
  name VARCHAR(255) NOT NULL,
  avatar TEXT,
  subscription VARCHAR(20) DEFAULT 'free',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_login TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_google_id ON users(google_id);
CREATE INDEX idx_users_email ON users(email);

-- 对话表（示例）
CREATE TABLE conversations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title VARCHAR(255) NOT NULL,
  type VARCHAR(20) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_conversations_user_id ON conversations(user_id);
```

---

## 前端改动

### 改动 1: 登录成功后显示服务端绑定状态

**文件**: `src/renderer/pages/settings/Account.tsx` (或相关设置页面)

```tsx
import { useEffect, useState } from 'react';
import { Message } from '@arco-design/web-react';
import { ipcBridge } from '@/common';

export function AccountSettings() {
  const [googleAccount, setGoogleAccount] = useState<string | null>(null);
  const [serverUser, setServerUser] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  // 检查登录状态
  useEffect(() => {
    checkLoginStatus();
  }, []);

  const checkLoginStatus = async () => {
    // 检查 Google 登录状态
    const googleStatus = await ipcBridge.googleAuth.status.invoke({});
    if (googleStatus.success && googleStatus.data?.account) {
      setGoogleAccount(googleStatus.data.account);
    }

    // 检查服务端登录状态
    const user = await ipcBridge.serverAuth.getUser.invoke();
    setServerUser(user);
  };

  const handleLogin = async () => {
    setLoading(true);
    try {
      const result = await ipcBridge.googleAuth.login.invoke({});

      if (result.success) {
        Message.success('登录成功');

        // 检查服务端绑定状态
        if (result.data?.serverBindingFailed) {
          Message.warning('服务端绑定失败，部分功能可能不可用');
        }

        await checkLoginStatus();
      } else {
        Message.error(result.msg || '登录失败');
      }
    } catch (error) {
      Message.error('登录过程出错');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    // 登出 Google
    await ipcBridge.googleAuth.logout.invoke();

    // 清除服务端登录信息
    await ipcBridge.serverAuth.clearServerAuth.invoke();

    setGoogleAccount(null);
    setServerUser(null);
    Message.success('已登出');
  };

  return (
    <div className='account-settings'>
      <h2>账号设置</h2>

      {/* Google 账号状态 */}
      <div className='account-section'>
        <h3>Google 账号</h3>
        {googleAccount ? (
          <div>
            <p>已登录: {googleAccount}</p>
            <button onClick={handleLogout}>登出</button>
          </div>
        ) : (
          <button onClick={handleLogin} disabled={loading}>
            {loading ? '登录中...' : '使用 Google 登录'}
          </button>
        )}
      </div>

      {/* 服务端账号状态 */}
      {serverUser && (
        <div className='account-section'>
          <h3>服务端账号</h3>
          <div className='user-info'>
            <img src={serverUser.avatar} alt={serverUser.name} />
            <div>
              <p>用户名: {serverUser.name}</p>
              <p>邮箱: {serverUser.email}</p>
              <p>注册时间: {new Date(serverUser.createdAt).toLocaleString()}</p>
              <p>最后登录: {new Date(serverUser.lastLogin).toLocaleString()}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
```

### 改动 2: 在需要的地方调用服务端 API

**示例: 同步对话到服务端**

```typescript
// src/process/services/conversationSync.ts
import { ipcBridge } from '@/common';

/**
 * 同步对话到服务端
 */
export async function syncConversationToServer(conversation: any) {
  try {
    // 获取服务端 Token
    const token = await ipcBridge.serverAuth.getToken.invoke();

    if (!token) {
      console.log('[Sync] Not logged in to server, skipping sync');
      return;
    }

    // 发送到服务端
    const response = await fetch('https://your-api.com/api/conversations', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        id: conversation.id,
        title: conversation.title,
        type: conversation.type,
        messages: conversation.messages,
        createdAt: conversation.createdAt,
      }),
    });

    const result = await response.json();

    if (result.success) {
      console.log('[Sync] Conversation synced successfully');
    } else {
      console.error('[Sync] Failed to sync conversation:', result.message);
    }
  } catch (error) {
    console.error('[Sync] Error syncing conversation:', error);
  }
}
```

---

## 安全考虑

### 1. Token 安全

**问题**: JWT Token 存储在本地，可能被窃取

**解决方案**:

- ✅ 使用 HTTPS 传输
- ✅ Token 设置合理的过期时间（如 30 天）
- ✅ 支持 Token 刷新机制
- ✅ 敏感操作需要二次验证

**Token 刷新实现**:

```typescript
// 服务端添加刷新 Token 接口
router.post('/auth/refresh-token', authenticateToken, async (req, res) => {
  const userId = req.user.userId;

  // 生成新 Token
  const newToken = jwt.sign({ userId, email: req.user.email }, process.env.JWT_SECRET, { expiresIn: '30d' });

  res.json({
    success: true,
    token: newToken,
  });
});
```

### 2. Google ID 验证

**问题**: 客户端可能伪造 Google ID

**解决方案**:

- ✅ 服务端验证 Google Token（可选）
- ✅ 记录 IP 地址和设备信息
- ✅ 异常登录检测

**Google Token 验证**:

```javascript
const { OAuth2Client } = require('google-auth-library');
const client = new OAuth2Client(process.env.GOOGLE_CLIENT_ID);

async function verifyGoogleToken(token) {
  try {
    const ticket = await client.verifyIdToken({
      idToken: token,
      audience: process.env.GOOGLE_CLIENT_ID,
    });
    const payload = ticket.getPayload();
    return {
      valid: true,
      googleId: payload.sub,
      email: payload.email,
    };
  } catch (error) {
    return { valid: false };
  }
}

// 在绑定 API 中使用
router.post('/bind-google', async (req, res) => {
  const { googleToken } = req.body;

  // 验证 Google Token
  const verification = await verifyGoogleToken(googleToken);
  if (!verification.valid) {
    return res.status(401).json({
      success: false,
      message: 'Invalid Google token',
    });
  }

  // 继续绑定流程...
});
```

### 3. API 限流

**问题**: 防止暴力攻击

**解决方案**:

```javascript
const rateLimit = require('express-rate-limit');

// 登录接口限流
const loginLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 分钟
  max: 5, // 最多 5 次请求
  message: {
    success: false,
    message: 'Too many login attempts, please try again later',
    code: 'RATE_LIMIT_EXCEEDED',
  },
});

router.post('/bind-google', loginLimiter, async (req, res) => {
  // 处理登录...
});
```

### 4. CORS 配置

**问题**: 跨域请求安全

**解决方案**:

```javascript
const cors = require('cors');

app.use(
  cors({
    origin: [
      'http://localhost:3000', // 开发环境
      'https://your-app.com', // 生产环境
    ],
    credentials: true,
    methods: ['GET', 'POST', 'PUT', 'DELETE'],
    allowedHeaders: ['Content-Type', 'Authorization'],
  })
);
```

---

## 测试方案

### 单元测试

**测试客户端绑定逻辑**:

```typescript
// tests/auth.test.ts
import { describe, it, expect, vi } from 'vitest';
import { ipcBridge } from '@/common';

describe('Google Auth with Server Binding', () => {
  it('should bind Google account to server on login', async () => {
    // Mock Google OAuth
    vi.spyOn(global, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        success: true,
        token: 'mock-token',
        userId: 'mock-user-id',
        user: {
          email: 'test@gmail.com',
          name: 'Test User',
        },
      }),
    } as Response);

    // 执行登录
    const result = await ipcBridge.googleAuth.login.invoke({});

    // 验证结果
    expect(result.success).toBe(true);
    expect(result.data?.serverToken).toBe('mock-token');
    expect(result.data?.serverUserId).toBe('mock-user-id');
  });

  it('should handle server binding failure gracefully', async () => {
    // Mock 服务端返回失败
    vi.spyOn(global, 'fetch').mockResolvedValueOnce({
      ok: false,
      status: 500,
    } as Response);

    const result = await ipcBridge.googleAuth.login.invoke({});

    // Google 登录成功，但服务端绑定失败
    expect(result.success).toBe(true);
    expect(result.data?.serverBindingFailed).toBe(true);
  });
});
```

### 集成测试

**测试完整登录流程**:

```bash
# 1. 启动服务端
npm run server:start

# 2. 启动客户端
npm run dev

# 3. 执行测试
npm run test:e2e
```

**E2E 测试脚本**:

```typescript
// tests/e2e/auth.spec.ts
import { test, expect } from '@playwright/test';

test('complete login flow', async ({ page }) => {
  // 1. 打开应用
  await page.goto('http://localhost:3000');

  // 2. 点击登录按钮
  await page.click('button:has-text("使用 Google 登录")');

  // 3. 等待 Google OAuth 页面
  await page.waitForURL(/accounts\.google\.com/);

  // 4. 输入 Google 账号（测试账号）
  await page.fill('input[type="email"]', 'test@gmail.com');
  await page.click('button:has-text("Next")');

  // 5. 输入密码
  await page.fill('input[type="password"]', 'test-password');
  await page.click('button:has-text("Next")');

  // 6. 等待回到应用
  await page.waitForURL('http://localhost:3000');

  // 7. 验证登录成功
  await expect(page.locator('text=test@gmail.com')).toBeVisible();
  await expect(page.locator('text=已登录')).toBeVisible();
});
```

---

## 部署清单

### 客户端部署

**1. 环境变量配置**:

```bash
# .env.production
VITE_SERVER_API_URL=https://your-api.com
VITE_ENABLE_SERVER_BINDING=true
```

**2. 构建配置**:

```typescript
// vite.config.ts
export default defineConfig({
  define: {
    'process.env.SERVER_API_URL': JSON.stringify(process.env.VITE_SERVER_API_URL),
  },
});
```

**3. 更新 API 地址**:

```typescript
// src/config/api.ts
export const API_BASE_URL = process.env.SERVER_API_URL || 'http://localhost:3001';

// 在 authBridge.ts 中使用
const serverResponse = await fetch(`${API_BASE_URL}/auth/bind-google`, {
  // ...
});
```

### 服务端部署

**1. 环境变量**:

```bash
# .env
NODE_ENV=production
PORT=3001
JWT_SECRET=your-super-secret-key-change-this
MONGODB_URI=mongodb://localhost:27017/aionui
# 或 PostgreSQL
DATABASE_URL=postgresql://user:password@localhost:5432/aionui

# Google OAuth (可选，用于验证)
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
```

**2. 启动脚本**:

```json
// package.json
{
  "scripts": {
    "start": "node server.js",
    "dev": "nodemon server.js",
    "migrate": "node scripts/migrate.js"
  }
}
```

**3. 数据库迁移**:

```bash
# 创建数据库表
npm run migrate

# 或使用 SQL 文件
mysql -u root -p aionui < migrations/001_create_users.sql
```

**4. 使用 PM2 部署**:

```bash
# 安装 PM2
npm install -g pm2

# 启动服务
pm2 start server.js --name aionui-api

# 设置开机自启
pm2 startup
pm2 save

# 查看日志
pm2 logs aionui-api
```

**5. Nginx 反向代理**:

```nginx
# /etc/nginx/sites-available/aionui-api
server {
    listen 80;
    server_name your-api.com;

    # 重定向到 HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-api.com;

    # SSL 证书
    ssl_certificate /etc/letsencrypt/live/your-api.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-api.com/privkey.pem;

    # 反向代理到 Node.js
    location / {
        proxy_pass http://localhost:3001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

**6. 申请 SSL 证书**:

```bash
# 使用 Let's Encrypt
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d your-api.com
```

---

## 常见问题

### Q1: 如果服务端绑定失败怎么办？

**A**: 客户端会继续使用 Google 登录，但服务端功能不可用。可以：

1. 在设置页面显示"服务端未连接"提示
2. 提供"重试绑定"按钮
3. 降级到本地存储模式

### Q2: 如何处理 Token 过期？

**A**: 实现 Token 刷新机制：

```typescript
// src/utils/apiClient.ts
async function callAPI(endpoint: string, options: RequestInit = {}) {
  let token = await ipcBridge.serverAuth.getToken.invoke();

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      ...options.headers,
      Authorization: `Bearer ${token}`,
    },
  });

  // Token 过期，尝试刷新
  if (response.status === 401) {
    const refreshResponse = await fetch(`${API_BASE_URL}/auth/refresh-token`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (refreshResponse.ok) {
      const { token: newToken } = await refreshResponse.json();
      await ipcBridge.config.set('server.token', newToken);

      // 重试原请求
      return callAPI(endpoint, options);
    } else {
      // 刷新失败，需要重新登录
      throw new Error('Token expired, please login again');
    }
  }

  return response;
}
```

### Q3: 如何支持多个 Google 账号？

**A**: 修改数据库设计，允许一个用户绑定多个 Google 账号：

```sql
CREATE TABLE user_google_accounts (
  id VARCHAR(36) PRIMARY KEY,
  user_id VARCHAR(36) NOT NULL,
  google_id VARCHAR(255) NOT NULL UNIQUE,
  email VARCHAR(255) NOT NULL,
  is_primary BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

### Q4: 如何迁移现有用户？

**A**: 创建迁移脚本：

```javascript
// scripts/migrate-users.js
const User = require('../models/User');

async function migrateUsers() {
  // 从本地数据库读取现有用户
  const localUsers = await getLocalUsers();

  for (const localUser of localUsers) {
    // 检查是否已存在
    const existing = await User.findOne({ email: localUser.email });

    if (!existing) {
      // 创建新用户
      await User.create({
        id: localUser.id,
        googleId: localUser.googleId || '',
        email: localUser.email,
        name: localUser.name,
        createdAt: localUser.createdAt,
      });
      console.log(`Migrated user: ${localUser.email}`);
    }
  }
}

migrateUsers().then(() => {
  console.log('Migration completed');
  process.exit(0);
});
```

---

## 总结

### 实现要点

1. ✅ 在 Google OAuth 成功后立即调用服务端绑定 API
2. ✅ 服务端自动创建或查找用户
3. ✅ 返回 JWT Token 并存储到本地
4. ✅ 后续请求携带 Token 访问服务端
5. ✅ 实现 Token 刷新机制
6. ✅ 处理绑定失败的降级方案

### 时间估算

- **客户端改动**: 2-4 小时
- **服务端实现**: 4-8 小时
- **数据库设计**: 1-2 小时
- **测试**: 2-4 小时
- **部署**: 2-4 小时
- **总计**: 11-22 小时

### 下一步

1. 阅读并理解本方案
2. 搭建服务端环境（Node.js + 数据库）
3. 实现服务端 API
4. 修改客户端代码
5. 本地测试
6. 部署到生产环境

---

**文档版本**: 1.0  
**创建日期**: 2026-01-29  
**作者**: Kiro AI Assistant

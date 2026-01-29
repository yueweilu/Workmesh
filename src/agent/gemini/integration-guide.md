# GeminiAgent 集成 SkillManager 指南

## ✅ 集成状态

### 已完成

- ✅ SkillManager 导入
- ✅ 构造函数初始化
- ✅ 配置选项添加
- ✅ send 方法集成
- ✅ checkAndCreateSkills() 实现
- ✅ reloadSkills() 实现
- ✅ 事件通知系统

### 待完成（可选）

- ⏳ 前端通知组件
- ⏳ 设置界面开关

---

## 已完成的集成

### 1. SkillManager 初始化 ✅

```typescript
// src/agent/gemini/index.ts

import { SkillManager } from './SkillManager';

export class GeminiAgent {
  private skillManager: SkillManager | null = null;
  private autoCreateSkills: boolean = true;

  constructor(options: GeminiAgent2Options) {
    // ... 现有初始化代码

    // 初始化 SkillManager
    if (options.skillsDir) {
      this.skillManager = new SkillManager(
        options.skillsDir,
        options.enabledSkills || [],
        options.autoCreateSkills !== false // 默认启用
      );
    }

    this.bootstrap = this.initialize();
  }
}
```

### 2. send 方法集成 ✅

```typescript
async send(params: {
  input: string;
  msg_id: string;
  files?: string[];
  loading_id?: string;
}): Promise<void> {
  const { input, msg_id, files, loading_id } = params;

  // 检查是否需要创建新技能
  if (this.skillManager && this.skillManager.isAutoCreateEnabled()) {
    await this.checkAndCreateSkills(input, msg_id);
  }

  // 继续原有的发送逻辑
  // ... 现有代码
}
```

### 3. 技能检测和创建方法 ✅

```typescript
private async checkAndCreateSkills(message: string, msg_id: string): Promise<void> {
  try {
    // 分析是否需要新技能
    const requirement = await this.skillManager!.analyzeSkillRequirement(message);

    if (requirement.needed && requirement.requirement) {
      // 通知用户正在创建技能
      this.onStreamEvent({
        type: 'skill-creating',
        data: {
          message: `🔧 Detecting need for new skill: ${requirement.reason}`,
          requirement: requirement.requirement,
        },
        msg_id,
      });

      // 创建技能
      const result = await this.skillManager!.createSkill(requirement.requirement);

      if (result.status === 'success' && result.skill_name) {
        // 加载新技能
        await this.skillManager!.loadSkill(result.skill_name);

        // 重新加载技能内容到 System Prompt
        await this.reloadSkills();

        // 通知用户技能已创建
        this.onStreamEvent({
          type: 'skill-created',
          data: {
            skill_name: result.skill_name,
            message: `✅ Created new skill: ${result.skill_name}`,
            usage: result.usage,
            category: result.category,
          },
          msg_id,
        });
      } else {
        // 创建失败，记录错误但继续执行
        console.error('[GeminiAgent] Skill creation failed:', result.error);
        this.onStreamEvent({
          type: 'skill-creation-failed',
          data: {
            error: result.error,
            message: '⚠️ Failed to create skill, continuing with existing capabilities',
          },
          msg_id,
        });
      }
    }
  } catch (error) {
    // 捕获错误但不中断主流程
    console.error('[GeminiAgent] Error in skill creation:', error);
  }
}

private async reloadSkills(): Promise<void> {
  if (!this.skillManager || !this.config) return;

  try {
    // 获取更新后的技能列表
    const enabledSkills = this.skillManager.getEnabledSkills();

    // 更新 enabledSkills 列表
    this.enabledSkills = enabledSkills;

    console.log('[GeminiAgent] Skills reloaded:', enabledSkills);
  } catch (error) {
    console.error('[GeminiAgent] Error reloading skills:', error);
  }
}
```

### 4. 配置选项 ✅

```typescript
interface GeminiAgent2Options {
  // ... 现有选项

  /** 是否启用自动技能创建 / Enable automatic skill creation */
  autoCreateSkills?: boolean;
}
```

---

## 待完成的前端集成（可选）

```typescript
// src/renderer/pages/conversation/GeminiChat.tsx

useEffect(() => {
  const unsubscribe = ipcBridge.geminiConversation.responseStream.subscribe((msg) => {
    if (msg.type === 'skill-creating') {
      // 显示"正在创建技能"提示
      Message.info({
        content: `🔧 ${msg.data.message}`,
        duration: 3000,
      });
    } else if (msg.type === 'skill-created') {
      // 显示"技能已创建"通知
      Message.success({
        content: `🎉 ${msg.data.message}`,
        duration: 5000,
      });
    } else if (msg.type === 'skill-creation-failed') {
      // 显示创建失败警告
      Message.warning({
        content: `⚠️ ${msg.data.message}`,
        duration: 3000,
      });
    }
  });

  return unsubscribe;
}, []);
```

## 使用示例

### 场景 1: 用户请求 CSV 分析

```
用户: 帮我分析这个 sales_data.csv 文件

AI 内部流程:
1. checkAndCreateSkills() 被调用
2. analyzeSkillRequirement() 检测到需要 csv_analyzer
3. 发送 'skill-creating' 事件
4. 调用 auto_create_skill.py 创建技能
5. 加载新技能到 enabledSkills
6. 发送 'skill-created' 事件
7. 继续处理用户消息，使用新技能

用户看到:
🔧 Detecting need for new skill: csv analysis
🎉 Created new skill: csv_analyzer
[AI 使用新技能分析 CSV 文件]
```

### 场景 2: 用户请求图像处理

```
用户: 把这张图片转成灰度图

AI 内部流程:
1. 检测到需要 image_processor
2. 自动创建技能
3. 立即使用新技能处理图片

用户看到:
🔧 Creating image processing skill...
🎉 New skill created: image_processor
✅ Image converted to grayscale: output_grayscale.png
```

## 配置选项

### 在会话创建时配置

```typescript
const conversation = await ipcBridge.conversation.create({
  type: 'gemini',
  model: selectedModel,
  extra: {
    workspace: '/path/to/workspace',
    enabledSkills: ['skill-creator'], // 必须包含 skill-creator
    autoCreateSkills: true, // 启用自动创建
  },
});
```

### 在设置中添加开关

```typescript
// src/renderer/pages/settings/SkillSettings.tsx

<Switch
  checked={autoCreateSkills}
  onChange={(checked) => {
    setAutoCreateSkills(checked);
    ipcBridge.config.set('skills.autoCreate', checked);
  }}
/>
```

## 注意事项

1. **必须启用 skill-creator**: 自动创建功能依赖 skill-creator 技能
2. **Python 环境**: 需要 Python 3 环境和 pip
3. **依赖安装**: 新技能的依赖会自动安装
4. **错误处理**: 技能创建失败不会中断主流程
5. **性能考虑**: 技能创建可能需要几秒钟

## 测试

### 单元测试

```typescript
// tests/unit/SkillManager.test.ts

describe('SkillManager', () => {
  it('should detect CSV analysis requirement', async () => {
    const manager = new SkillManager('/path/to/skills', [], true);
    const result = await manager.analyzeSkillRequirement('Analyze this CSV file');

    expect(result.needed).toBe(true);
    expect(result.requirement).toContain('CSV');
  });

  it('should create skill successfully', async () => {
    const manager = new SkillManager('/path/to/skills', [], true);
    const result = await manager.createSkill('Analyze CSV file data');

    expect(result.status).toBe('success');
    expect(result.skill_name).toBe('csv_analyzer');
  });
});
```

### 集成测试

```bash
# 测试自动创建功能
npm run test:integration -- --grep "auto skill creation"
```

## 故障排查

### 问题 1: 技能创建失败

**检查**:

- Python 3 是否安装
- skill-creator 是否在 enabledSkills 中
- 技能目录是否有写权限

### 问题 2: 技能未生效

**检查**:

- 技能是否成功加载到 enabledSkills
- SKILL.md 格式是否正确
- 脚本是否有执行权限

### 问题 3: 依赖安装失败

**解决**:

- 手动安装依赖: `pip install pandas pillow requests`
- 检查网络连接
- 使用国内镜像: `pip install -i https://pypi.tuna.tsinghua.edu.cn/simple`

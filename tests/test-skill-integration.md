# 动态技能创建系统 - 集成测试指南

## ✅ 后端集成已完成

GeminiAgent 已成功集成 SkillManager，现在可以进行测试。

## 测试步骤

### 1. 准备环境

确保以下配置正确：

```typescript
// 创建会话时的配置
const conversation = await ipcBridge.conversation.create({
  type: 'gemini',
  model: selectedModel,
  extra: {
    workspace: '/path/to/workspace',
    skillsDir: '/path/to/skills', // 技能目录
    enabledSkills: ['skill-creator'], // 必须包含 skill-creator
    autoCreateSkills: true, // 启用自动创建（默认）
  },
});
```

### 2. 测试场景

#### 场景 1: CSV 分析技能

**用户输入**:

```
帮我分析这个 sales_data.csv 文件的数据分布
```

**预期行为**:

1. SkillManager 检测到需要 csv_analyzer 技能
2. 自动调用 auto_create_skill.py 创建技能
3. 发送 `skill-creating` 事件（控制台可见）
4. 创建成功后发送 `skill-created` 事件
5. 技能被加载到 enabledSkills 列表
6. AI 使用新技能处理用户请求

**验证**:

```bash
# 检查技能是否创建
ls -la skills/csv_analyzer/

# 应该看到:
# - SKILL.md
# - csv_analyzer.py
```

#### 场景 2: 图像处理技能

**用户输入**:

```
把这张图片转成灰度图
```

**预期行为**:

1. 检测到需要 image_processor 技能
2. 自动创建技能
3. 安装依赖 (pillow)
4. 加载并使用新技能

**验证**:

```bash
ls -la skills/image_processor/
```

#### 场景 3: API 调用技能

**用户输入**:

```
帮我调用这个 REST API 获取数据
```

**预期行为**:

1. 检测到需要 api_caller 技能
2. 自动创建技能
3. 安装依赖 (requests)
4. 加载并使用新技能

### 3. 查看日志

**控制台日志**:

```
[GeminiAgent] Detecting need for new skill: csv analysis
[GeminiAgent] Creating skill: csv_analyzer
[GeminiAgent] Skill created successfully: csv_analyzer
[GeminiAgent] Skills reloaded: ['skill-creator', 'csv_analyzer']
```

**事件流**:

```typescript
// 1. 技能创建中
{
  type: 'skill-creating',
  data: {
    message: '🔧 Detecting need for new skill: csv analysis',
    requirement: 'Analyze CSV file data distribution'
  },
  msg_id: '...'
}

// 2. 技能创建成功
{
  type: 'skill-created',
  data: {
    skill_name: 'csv_analyzer',
    message: '✅ Created new skill: csv_analyzer',
    usage: 'python skills/csv_analyzer/csv_analyzer.py <args>',
    category: 'data_analysis'
  },
  msg_id: '...'
}

// 3. 技能创建失败（如果失败）
{
  type: 'skill-creation-failed',
  data: {
    error: '...',
    message: '⚠️ Failed to create skill, continuing with existing capabilities'
  },
  msg_id: '...'
}
```

### 4. 验证技能文件

**检查 SKILL.md**:

```bash
cat skills/csv_analyzer/SKILL.md
```

应该包含：

- Frontmatter (name, description, category, auto_generated, created_at)
- Overview
- Quick Start
- Tools
- Notes

**检查 Python 脚本**:

```bash
cat skills/csv_analyzer/csv_analyzer.py
```

应该包含：

- Import 语句
- 主要功能函数
- main() 入口
- 错误处理
- JSON 输出

**测试脚本执行**:

```bash
python3 skills/csv_analyzer/csv_analyzer.py --help
```

### 5. 调试技巧

#### 问题 1: 技能未创建

**检查**:

- `autoCreateSkills` 是否为 true
- `skillsDir` 路径是否正确
- `skill-creator` 是否在 enabledSkills 中
- Python 3 是否安装

**解决**:

```bash
# 手动测试创建脚本
python3 skills/skill-creator/scripts/auto_create_skill.py "Analyze CSV file" skills
```

#### 问题 2: 依赖安装失败

**检查**:

- pip 是否安装
- 网络连接是否正常

**解决**:

```bash
# 手动安装依赖
pip install pandas pillow requests beautifulsoup4
```

#### 问题 3: 技能未加载

**检查**:

- 技能文件是否创建成功
- SKILL.md 格式是否正确
- enabledSkills 列表是否更新

**解决**:

```typescript
// 查看 enabledSkills
console.log(this.skillManager.getEnabledSkills());
```

## 前端集成（可选）

如果需要用户界面通知，可以添加以下代码：

### 在 GeminiChat.tsx 中

```typescript
useEffect(() => {
  const unsubscribe = ipcBridge.geminiConversation.responseStream.subscribe((msg) => {
    if (msg.type === 'skill-creating') {
      Message.info({
        content: msg.data.message,
        duration: 3000,
      });
    } else if (msg.type === 'skill-created') {
      Message.success({
        content: msg.data.message,
        duration: 5000,
      });
    } else if (msg.type === 'skill-creation-failed') {
      Message.warning({
        content: msg.data.message,
        duration: 3000,
      });
    }
  });

  return unsubscribe;
}, []);
```

### 在 SkillSettings.tsx 中

```typescript
<Form.Item label="自动创建技能">
  <Switch
    checked={autoCreateSkills}
    onChange={(checked) => {
      setAutoCreateSkills(checked);
      ipcBridge.config.set('skills.autoCreate', checked);
    }}
  />
  <div className="form-item-tip">
    当检测到需要新技能时自动创建
  </div>
</Form.Item>
```

## 性能监控

### 创建时间

正常情况下，技能创建应该在 2-5 秒内完成：

- 分析需求: < 100ms
- 创建文件: < 500ms
- 安装依赖: 1-3s
- 加载技能: < 100ms

### 内存使用

每个技能占用约 10-50KB 磁盘空间。

## 总结

✅ 后端集成已完成，核心功能可用
⏳ 前端通知为可选功能，可以后续添加
🎯 现在可以开始测试自动技能创建功能

**下一步**:

1. 启动应用测试基本功能
2. 根据需要添加前端通知
3. 根据使用反馈优化技能模板

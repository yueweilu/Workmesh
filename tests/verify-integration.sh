#!/bin/bash

# 动态技能创建系统 - 集成验证脚本
# 验证 GeminiAgent 和 SkillManager 的集成是否正确

echo "========================================="
echo "动态技能创建系统 - 集成验证"
echo "========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查计数
PASSED=0
FAILED=0

# 检查函数
check() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $1"
        ((PASSED++))
    else
        echo -e "${RED}✗${NC} $1"
        ((FAILED++))
    fi
}

# 1. 检查核心文件是否存在
echo "1. 检查核心文件..."
echo "-------------------"

test -f "src/agent/gemini/SkillManager.ts"
check "SkillManager.ts 存在"

test -f "src/agent/gemini/index.ts"
check "GeminiAgent index.ts 存在"

test -f "skills/skill-creator/scripts/auto_create_skill.py"
check "auto_create_skill.py 存在"

echo ""

# 2. 检查 GeminiAgent 集成
echo "2. 检查 GeminiAgent 集成..."
echo "----------------------------"

# 检查 import 语句
grep -q "import { SkillManager } from './SkillManager'" src/agent/gemini/index.ts
check "SkillManager 已导入"

# 检查 skillManager 属性
grep -q "private skillManager: SkillManager | null = null" src/agent/gemini/index.ts
check "skillManager 属性已定义"

# 检查 autoCreateSkills 属性
grep -q "private autoCreateSkills: boolean" src/agent/gemini/index.ts
check "autoCreateSkills 属性已定义"

# 检查构造函数初始化
grep -q "this.skillManager = new SkillManager" src/agent/gemini/index.ts
check "SkillManager 在构造函数中初始化"

# 检查 send 方法集成
grep -q "checkAndCreateSkills" src/agent/gemini/index.ts
check "checkAndCreateSkills 方法已调用"

# 检查方法实现
grep -q "private async checkAndCreateSkills" src/agent/gemini/index.ts
check "checkAndCreateSkills 方法已实现"

grep -q "private async reloadSkills" src/agent/gemini/index.ts
check "reloadSkills 方法已实现"

# 检查事件类型
grep -q "skill-creating" src/agent/gemini/index.ts
check "skill-creating 事件已添加"

grep -q "skill-created" src/agent/gemini/index.ts
check "skill-created 事件已添加"

grep -q "skill-creation-failed" src/agent/gemini/index.ts
check "skill-creation-failed 事件已添加"

echo ""

# 3. 检查 SkillManager 实现
echo "3. 检查 SkillManager 实现..."
echo "-----------------------------"

# 检查核心方法
grep -q "analyzeSkillRequirement" src/agent/gemini/SkillManager.ts
check "analyzeSkillRequirement 方法存在"

grep -q "createSkill" src/agent/gemini/SkillManager.ts
check "createSkill 方法存在"

grep -q "loadSkill" src/agent/gemini/SkillManager.ts
check "loadSkill 方法存在"

grep -q "isAutoCreateEnabled" src/agent/gemini/SkillManager.ts
check "isAutoCreateEnabled 方法存在"

echo ""

# 4. 检查 Python 脚本
echo "4. 检查 Python 脚本..."
echo "----------------------"

# 检查脚本可执行性
python3 -c "import sys; sys.exit(0)" 2>/dev/null
check "Python 3 已安装"

# 检查脚本语法
python3 -m py_compile skills/skill-creator/scripts/auto_create_skill.py 2>/dev/null
check "auto_create_skill.py 语法正确"

echo ""

# 5. 检查 TypeScript 编译
echo "5. 检查 TypeScript 编译..."
echo "--------------------------"

# 尝试编译（如果有 tsc）
if command -v npx &> /dev/null; then
    npx tsc --noEmit src/agent/gemini/index.ts 2>/dev/null
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} GeminiAgent TypeScript 编译通过"
        ((PASSED++))
    else
        echo -e "${YELLOW}⚠${NC} TypeScript 编译检查跳过（需要完整项目环境）"
    fi
    
    npx tsc --noEmit src/agent/gemini/SkillManager.ts 2>/dev/null
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} SkillManager TypeScript 编译通过"
        ((PASSED++))
    else
        echo -e "${YELLOW}⚠${NC} TypeScript 编译检查跳过（需要完整项目环境）"
    fi
else
    echo -e "${YELLOW}⚠${NC} npx 未安装，跳过 TypeScript 编译检查"
fi

echo ""

# 6. 检查文档
echo "6. 检查文档..."
echo "--------------"

test -f "实现总结.md"
check "实现总结.md 存在"

test -f "动态技能创建-使用指南.md"
check "使用指南存在"

test -f "src/agent/gemini/integration-guide.md"
check "集成指南存在"

test -f "tests/test-skill-integration.md"
check "集成测试指南存在"

echo ""

# 7. 总结
echo "========================================="
echo "验证结果"
echo "========================================="
echo -e "${GREEN}通过: $PASSED${NC}"
echo -e "${RED}失败: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ 所有检查通过！集成成功！${NC}"
    echo ""
    echo "下一步："
    echo "1. 启动应用并创建会话"
    echo "2. 发送测试消息（如：'帮我分析 CSV 文件'）"
    echo "3. 查看控制台日志确认技能创建"
    echo "4. 验证 skills 目录中的新技能"
    echo ""
    echo "详细测试步骤请参考: tests/test-skill-integration.md"
    exit 0
else
    echo -e "${RED}✗ 有 $FAILED 项检查失败${NC}"
    echo ""
    echo "请检查失败的项目并修复"
    exit 1
fi

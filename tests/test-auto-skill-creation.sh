#!/bin/bash
# 测试自动技能创建功能
# Test automatic skill creation functionality

set -e

echo "========================================="
echo "Testing Auto Skill Creation"
echo "========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 测试目录
TEST_SKILLS_DIR="./test-skills"
SCRIPT_PATH="skills/skill-creator/scripts/auto_create_skill.py"

# 清理测试目录
cleanup() {
    echo ""
    echo "Cleaning up test directory..."
    rm -rf "$TEST_SKILLS_DIR"
}

# 注册清理函数
trap cleanup EXIT

# 创建测试目录
mkdir -p "$TEST_SKILLS_DIR"

# 测试函数
test_skill_creation() {
    local requirement="$1"
    local expected_skill="$2"
    
    echo -e "${YELLOW}Test: Creating skill for '$requirement'${NC}"
    
    # 运行创建脚本
    if python3 "$SCRIPT_PATH" "$requirement" "$TEST_SKILLS_DIR" > /tmp/skill_output.json 2>&1; then
        # 检查输出
        if grep -q '"status": "success"' /tmp/skill_output.json; then
            echo -e "${GREEN}✓ Skill created successfully${NC}"
            
            # 验证文件存在
            if [ -d "$TEST_SKILLS_DIR/$expected_skill" ]; then
                echo -e "${GREEN}✓ Skill directory exists${NC}"
                
                if [ -f "$TEST_SKILLS_DIR/$expected_skill/SKILL.md" ]; then
                    echo -e "${GREEN}✓ SKILL.md exists${NC}"
                else
                    echo -e "${RED}✗ SKILL.md not found${NC}"
                    return 1
                fi
                
                if [ -f "$TEST_SKILLS_DIR/$expected_skill/$expected_skill.py" ]; then
                    echo -e "${GREEN}✓ Python script exists${NC}"
                else
                    echo -e "${RED}✗ Python script not found${NC}"
                    return 1
                fi
                
                # 测试脚本是否可执行
                if [ -x "$TEST_SKILLS_DIR/$expected_skill/$expected_skill.py" ]; then
                    echo -e "${GREEN}✓ Script is executable${NC}"
                else
                    echo -e "${RED}✗ Script is not executable${NC}"
                    return 1
                fi
                
                echo -e "${GREEN}✓ All checks passed${NC}"
                return 0
            else
                echo -e "${RED}✗ Skill directory not found${NC}"
                return 1
            fi
        else
            echo -e "${RED}✗ Skill creation failed${NC}"
            cat /tmp/skill_output.json
            return 1
        fi
    else
        echo -e "${RED}✗ Script execution failed${NC}"
        cat /tmp/skill_output.json
        return 1
    fi
}

# 运行测试
echo "Test 1: CSV Analyzer"
echo "-------------------"
test_skill_creation "Analyze CSV file data distribution" "csv_analyzer"
echo ""

echo "Test 2: Image Processor"
echo "----------------------"
test_skill_creation "Convert images to grayscale" "image_processor"
echo ""

echo "Test 3: API Caller"
echo "-----------------"
test_skill_creation "Make HTTP API requests" "api_caller"
echo ""

echo "Test 4: Generic Skill"
echo "--------------------"
test_skill_creation "Process custom data format" "process_custom"
echo ""

# 测试脚本执行
echo "Test 5: Script Execution"
echo "-----------------------"
echo "Testing CSV analyzer script..."

# 创建测试 CSV 文件
cat > /tmp/test.csv << EOF
name,age,city
Alice,30,New York
Bob,25,Los Angeles
Charlie,35,Chicago
EOF

# 测试脚本（如果 pandas 已安装）
if python3 -c "import pandas" 2>/dev/null; then
    if python3 "$TEST_SKILLS_DIR/csv_analyzer/csv_analyzer.py" /tmp/test.csv > /tmp/csv_result.json 2>&1; then
        if grep -q '"status": "success"' /tmp/csv_result.json; then
            echo -e "${GREEN}✓ CSV analyzer script works${NC}"
            echo "Output:"
            cat /tmp/csv_result.json | python3 -m json.tool
        else
            echo -e "${RED}✗ CSV analyzer script failed${NC}"
            cat /tmp/csv_result.json
        fi
    else
        echo -e "${RED}✗ Script execution failed${NC}"
    fi
else
    echo -e "${YELLOW}⚠ pandas not installed, skipping script execution test${NC}"
fi

echo ""
echo "========================================="
echo "All Tests Completed"
echo "========================================="

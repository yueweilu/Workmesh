#!/usr/bin/env python3
"""
自动技能创建器 - 根据需求描述自动生成技能
Auto Skill Creator - Automatically generate skills based on requirement descriptions

Usage:
    auto_create_skill.py "<requirement description>" [skills_dir]

Examples:
    auto_create_skill.py "Analyze CSV file data distribution"
    auto_create_skill.py "Convert images to grayscale" /path/to/skills
"""

import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime


def analyze_requirement(requirement: str) -> dict:
    """
    分析用户需求，提取技能信息
    Analyze user requirement and extract skill information
    
    Args:
        requirement: 用户需求描述 / User requirement description
        
    Returns:
        {
            "skill_name": "csv_analyzer",
            "description": "Analyze CSV file data distribution",
            "language": "python",
            "dependencies": ["pandas", "matplotlib"],
            "input_params": ["file_path"],
            "output_format": "json",
            "category": "data_analysis"
        }
    """
    requirement_lower = requirement.lower()
    
    skill_info = {
        "skill_name": "",
        "description": requirement,
        "language": "python",
        "dependencies": [],
        "input_params": [],
        "output_format": "json",
        "category": "general"
    }
    
    # 根据关键词推断技能类型 / Infer skill type based on keywords
    if any(kw in requirement_lower for kw in ["csv", "excel", "spreadsheet", "data analysis"]):
        skill_info["skill_name"] = "csv_analyzer"
        skill_info["dependencies"] = ["pandas"]
        skill_info["input_params"] = ["file_path"]
        skill_info["category"] = "data_analysis"
        
    elif any(kw in requirement_lower for kw in ["image", "picture", "photo", "png", "jpg"]):
        skill_info["skill_name"] = "image_processor"
        skill_info["dependencies"] = ["pillow"]
        skill_info["input_params"] = ["image_path"]
        skill_info["category"] = "image_processing"
        
    elif any(kw in requirement_lower for kw in ["api", "http", "rest", "request", "fetch"]):
        skill_info["skill_name"] = "api_caller"
        skill_info["dependencies"] = ["requests"]
        skill_info["input_params"] = ["url", "method"]
        skill_info["category"] = "api_integration"
        
    elif any(kw in requirement_lower for kw in ["json", "parse", "format"]):
        skill_info["skill_name"] = "json_processor"
        skill_info["dependencies"] = []
        skill_info["input_params"] = ["json_data"]
        skill_info["category"] = "data_processing"
        
    elif any(kw in requirement_lower for kw in ["text", "string", "parse text"]):
        skill_info["skill_name"] = "text_processor"
        skill_info["dependencies"] = []
        skill_info["input_params"] = ["text"]
        skill_info["category"] = "text_processing"
        
    elif any(kw in requirement_lower for kw in ["web", "scrape", "crawl", "html"]):
        skill_info["skill_name"] = "web_scraper"
        skill_info["dependencies"] = ["requests", "beautifulsoup4"]
        skill_info["input_params"] = ["url"]
        skill_info["category"] = "web_scraping"
        
    else:
        # 通用技能 / Generic skill
        # 从需求中提取关键词作为技能名 / Extract keywords from requirement as skill name
        words = re.findall(r'\b[a-z]+\b', requirement_lower)
        if len(words) >= 2:
            skill_info["skill_name"] = f"{words[0]}_{words[1]}"
        else:
            skill_info["skill_name"] = "custom_task"
        skill_info["input_params"] = ["input_data"]
        skill_info["category"] = "general"
    
    return skill_info


def generate_skill_md(skill_info: dict) -> str:
    """生成 SKILL.md 内容 / Generate SKILL.md content"""
    
    skill_title = skill_info["skill_name"].replace('_', ' ').title()
    
    params_doc = "\n".join([
        f"- `{param}`: Input parameter for {param.replace('_', ' ')}"
        for param in skill_info["input_params"]
    ])
    
    deps_doc = ", ".join(skill_info["dependencies"]) if skill_info["dependencies"] else "None (uses Python standard library)"
    
    return f"""---
name: {skill_info["skill_name"]}
description: {skill_info["description"]}. Auto-generated skill for {skill_info["category"]}. Use when the user needs to {skill_info["description"].lower()}.
auto_generated: true
created_at: {datetime.now().isoformat()}
category: {skill_info["category"]}
---

# {skill_title}

## Overview

This skill was automatically generated to handle: {skill_info["description"]}

**Category**: {skill_info["category"]}  
**Language**: {skill_info["language"]}  
**Dependencies**: {deps_doc}

## Quick Start

Execute the skill with:

```bash
python skills/{skill_info["skill_name"]}/{skill_info["skill_name"]}.py <arguments>
```

## Tools

### {skill_info["skill_name"]}.py

**Location:** `skills/{skill_info["skill_name"]}/{skill_info["skill_name"]}.py`

**Dependencies:** {deps_doc}

**Usage:**
```bash
python skills/{skill_info["skill_name"]}/{skill_info["skill_name"]}.py <args>
```

**Arguments:**
{params_doc}

**Output Format:**
Returns {skill_info["output_format"].upper()} with the following structure:
```json
{{
  "status": "success" | "error",
  "result": "...",
  "message": "..."
}}
```

**Example:**
```bash
python skills/{skill_info["skill_name"]}/{skill_info["skill_name"]}.py "example_input"
```

## Notes

- This skill was automatically generated based on the requirement: "{skill_info["description"]}"
- You may need to customize the implementation for your specific use case
- The script includes basic error handling and JSON output
- Dependencies are automatically installed during skill creation

## Customization

To customize this skill:
1. Edit `{skill_info["skill_name"]}.py` to modify the implementation
2. Update this SKILL.md to reflect any changes
3. Add additional scripts to `scripts/` if needed
4. Add reference documentation to `references/` if needed
"""


def generate_csv_analyzer_script() -> str:
    """生成 CSV 分析脚本 / Generate CSV analyzer script"""
    return '''#!/usr/bin/env python3
"""
CSV Analyzer - Analyze CSV file data distribution
Auto-generated skill
"""
import sys
import json

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

def analyze_csv(file_path: str) -> dict:
    """Analyze CSV file and return statistics"""
    if not PANDAS_AVAILABLE:
        return {
            "status": "error",
            "error": "pandas is not installed. Install with: pip install pandas"
        }
    
    try:
        # Read CSV
        df = pd.read_csv(file_path)
        
        # Basic statistics
        result = {
            "status": "success",
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": df.columns.tolist(),
            "data_types": df.dtypes.astype(str).to_dict(),
            "missing_values": df.isnull().sum().to_dict(),
            "sample_data": df.head(5).to_dict(orient='records'),
        }
        
        # Add numeric summary if there are numeric columns
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            result["numeric_summary"] = df[numeric_cols].describe().to_dict()
        
        return result
    except FileNotFoundError:
        return {
            "status": "error",
            "error": f"File not found: {file_path}"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

def main():
    if len(sys.argv) < 2:
        print(json.dumps({
            "status": "error",
            "error": "Missing file_path argument",
            "usage": "python csv_analyzer.py <file_path>"
        }))
        sys.exit(1)
    
    file_path = sys.argv[1]
    result = analyze_csv(file_path)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
'''


def generate_image_processor_script() -> str:
    """生成图像处理脚本 / Generate image processor script"""
    return '''#!/usr/bin/env python3
"""
Image Processor - Process and manipulate images
Auto-generated skill
"""
import sys
import json
from pathlib import Path

def process_image(image_path: str, operation: str = "info") -> dict:
    """Process image and return result"""
    try:
        from PIL import Image
        
        # Open image
        img = Image.open(image_path)
        
        result = {
            "status": "success",
            "image_path": image_path,
            "operation": operation,
        }
        
        if operation == "info":
            result["info"] = {
                "format": img.format,
                "mode": img.mode,
                "size": img.size,
                "width": img.width,
                "height": img.height,
            }
        elif operation == "grayscale":
            output_path = str(Path(image_path).with_stem(Path(image_path).stem + "_grayscale"))
            gray_img = img.convert('L')
            gray_img.save(output_path)
            result["output_path"] = output_path
            result["message"] = "Image converted to grayscale"
        elif operation == "resize":
            # Default resize to 50%
            new_size = (img.width // 2, img.height // 2)
            output_path = str(Path(image_path).with_stem(Path(image_path).stem + "_resized"))
            resized_img = img.resize(new_size)
            resized_img.save(output_path)
            result["output_path"] = output_path
            result["new_size"] = new_size
            result["message"] = "Image resized"
        else:
            result["status"] = "error"
            result["error"] = f"Unknown operation: {operation}"
        
        return result
    except ImportError:
        return {
            "status": "error",
            "error": "Pillow is not installed. Install with: pip install pillow"
        }
    except FileNotFoundError:
        return {
            "status": "error",
            "error": f"File not found: {image_path}"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

def main():
    if len(sys.argv) < 2:
        print(json.dumps({
            "status": "error",
            "error": "Missing image_path argument",
            "usage": "python image_processor.py <image_path> [operation]"
        }))
        sys.exit(1)
    
    image_path = sys.argv[1]
    operation = sys.argv[2] if len(sys.argv) > 2 else "info"
    
    result = process_image(image_path, operation)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
'''


def generate_api_caller_script() -> str:
    """生成 API 调用脚本 / Generate API caller script"""
    return '''#!/usr/bin/env python3
"""
API Caller - Make HTTP API requests
Auto-generated skill
"""
import sys
import json

def call_api(url: str, method: str = "GET", data: dict = None) -> dict:
    """Call API and return response"""
    try:
        import requests
        
        method = method.upper()
        
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "PUT":
            response = requests.put(url, json=data)
        elif method == "DELETE":
            response = requests.delete(url)
        else:
            return {
                "status": "error",
                "error": f"Unsupported HTTP method: {method}"
            }
        
        result = {
            "status": "success",
            "url": url,
            "method": method,
            "status_code": response.status_code,
            "headers": dict(response.headers),
        }
        
        # Try to parse JSON response
        try:
            result["response"] = response.json()
        except:
            result["response"] = response.text
        
        return result
    except ImportError:
        return {
            "status": "error",
            "error": "requests is not installed. Install with: pip install requests"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

def main():
    if len(sys.argv) < 2:
        print(json.dumps({
            "status": "error",
            "error": "Missing url argument",
            "usage": "python api_caller.py <url> [method] [data_json]"
        }))
        sys.exit(1)
    
    url = sys.argv[1]
    method = sys.argv[2] if len(sys.argv) > 2 else "GET"
    data = json.loads(sys.argv[3]) if len(sys.argv) > 3 else None
    
    result = call_api(url, method, data)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
'''


def generate_generic_script(skill_info: dict, requirement: str) -> str:
    """生成通用脚本模板 / Generate generic script template"""
    params_list = ", ".join(skill_info["input_params"])
    params_doc = "\n    ".join([f"{param}: Input parameter" for param in skill_info["input_params"]])
    
    return f'''#!/usr/bin/env python3
"""
{skill_info["skill_name"]} - {skill_info["description"]}
Auto-generated skill

Requirement: {requirement}
"""
import sys
import json

def execute_task({params_list}) -> dict:
    """
    Execute the task based on requirement:
    {requirement}
    
    Args:
        {params_doc}
    
    Returns:
        dict: Result with status and data
    
    TODO: Implement the actual logic here
    """
    try:
        # TODO: Add your implementation here
        # This is a template - customize based on your specific needs
        
        result = {{
            "status": "success",
            "message": "Task completed successfully",
            "requirement": "{requirement}",
            "inputs": {{{", ".join([f'"{p}": {p}' for p in skill_info["input_params"]])}}},
            "output": "TODO: Implement actual logic and return meaningful results"
        }}
        
        return result
    except Exception as e:
        return {{
            "status": "error",
            "error": str(e)
        }}

def main():
    if len(sys.argv) < {len(skill_info["input_params"]) + 1}:
        print(json.dumps({{
            "status": "error",
            "error": "Missing required arguments",
            "usage": "python {skill_info["skill_name"]}.py {' '.join([f'<{p}>' for p in skill_info["input_params"]])}"
        }}))
        sys.exit(1)
    
    # Parse arguments
    {chr(10).join([f'    {param} = sys.argv[{i+1}]' for i, param in enumerate(skill_info["input_params"])])}
    
    result = execute_task({params_list})
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
'''


def generate_python_script(skill_info: dict, requirement: str) -> str:
    """生成 Python 脚本内容 / Generate Python script content"""
    
    # 根据技能类型生成不同的模板 / Generate different templates based on skill type
    if "csv" in skill_info["skill_name"] or "analyzer" in skill_info["skill_name"]:
        return generate_csv_analyzer_script()
    elif "image" in skill_info["skill_name"]:
        return generate_image_processor_script()
    elif "api" in skill_info["skill_name"]:
        return generate_api_caller_script()
    else:
        return generate_generic_script(skill_info, requirement)


def install_dependencies(dependencies: list) -> dict:
    """安装 Python 依赖 / Install Python dependencies"""
    if not dependencies:
        return {"status": "success", "message": "No dependencies to install"}
    
    try:
        import subprocess
        
        print(f"Installing dependencies: {', '.join(dependencies)}")
        result = subprocess.run(
            ["pip", "install"] + dependencies,
            check=True,
            capture_output=True,
            text=True
        )
        
        return {
            "status": "success",
            "message": f"Successfully installed: {', '.join(dependencies)}",
            "output": result.stdout
        }
    except subprocess.CalledProcessError as e:
        return {
            "status": "warning",
            "message": f"Failed to install some dependencies: {e}",
            "error": e.stderr
        }
    except Exception as e:
        return {
            "status": "warning",
            "message": f"Dependency installation failed: {e}"
        }


def create_skill(requirement: str, skills_dir: str = None) -> dict:
    """
    自动创建技能 / Automatically create a skill
    
    Args:
        requirement: 用户需求描述 / User requirement description
        skills_dir: 技能目录路径 / Skills directory path
        
    Returns:
        创建结果 / Creation result
    """
    # 确定技能目录 / Determine skills directory
    if skills_dir is None:
        # 默认使用当前脚本的父目录的父目录 / Default to parent's parent directory
        skills_dir = Path(__file__).parent.parent.parent
    else:
        skills_dir = Path(skills_dir)
    
    print(f"Skills directory: {skills_dir}")
    
    # 分析需求 / Analyze requirement
    skill_info = analyze_requirement(requirement)
    skill_name = skill_info["skill_name"]
    
    print(f"Creating skill: {skill_name}")
    print(f"Category: {skill_info['category']}")
    print(f"Dependencies: {skill_info['dependencies']}")
    
    # 创建技能目录 / Create skill directory
    skill_dir = skills_dir / skill_name
    if skill_dir.exists():
        return {
            "status": "error",
            "error": f"Skill '{skill_name}' already exists at {skill_dir}"
        }
    
    try:
        skill_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {skill_dir}")
    except Exception as e:
        return {
            "status": "error",
            "error": f"Failed to create directory: {e}"
        }
    
    # 生成 SKILL.md / Generate SKILL.md
    try:
        skill_md_content = generate_skill_md(skill_info)
        (skill_dir / "SKILL.md").write_text(skill_md_content)
        print("Created SKILL.md")
    except Exception as e:
        return {
            "status": "error",
            "error": f"Failed to create SKILL.md: {e}"
        }
    
    # 生成 Python 脚本 / Generate Python script
    try:
        script_content = generate_python_script(skill_info, requirement)
        script_path = skill_dir / f"{skill_name}.py"
        script_path.write_text(script_content)
        script_path.chmod(0o755)  # 添加执行权限 / Add execute permission
        print(f"Created {skill_name}.py")
    except Exception as e:
        return {
            "status": "error",
            "error": f"Failed to create script: {e}"
        }
    
    # 安装依赖（如果需要）/ Install dependencies (if needed)
    dep_result = {"status": "success"}
    if skill_info["dependencies"]:
        dep_result = install_dependencies(skill_info["dependencies"])
        if dep_result["status"] == "warning":
            print(f"Warning: {dep_result['message']}")
    
    # 返回成功结果 / Return success result
    return {
        "status": "success",
        "message": f"Skill '{skill_name}' created successfully",
        "skill_name": skill_name,
        "skill_path": str(skill_dir),
        "script_path": str(script_path),
        "usage": f"python {script_path} <args>",
        "category": skill_info["category"],
        "dependencies": skill_info["dependencies"],
        "dependency_installation": dep_result
    }


def main():
    if len(sys.argv) < 2:
        print(json.dumps({
            "status": "error",
            "error": "Usage: python auto_create_skill.py '<requirement description>' [skills_dir]",
            "examples": [
                "python auto_create_skill.py 'Analyze CSV file data distribution'",
                "python auto_create_skill.py 'Convert images to grayscale' /path/to/skills"
            ]
        }, indent=2))
        sys.exit(1)
    
    requirement = sys.argv[1]
    skills_dir = sys.argv[2] if len(sys.argv) > 2 else None
    
    print("=" * 60)
    print("Auto Skill Creator")
    print("=" * 60)
    print(f"Requirement: {requirement}")
    print()
    
    result = create_skill(requirement, skills_dir)
    
    print()
    print("=" * 60)
    print("Result:")
    print("=" * 60)
    print(json.dumps(result, indent=2))
    
    if result["status"] == "success":
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()

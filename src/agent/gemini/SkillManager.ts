/**
 * @license
 * Copyright 2025 AionUi (aionui.com)
 * SPDX-License-Identifier: Apache-2.0
 */

import { spawn } from 'child_process';
import * as fs from 'fs/promises';
import * as path from 'path';

/**
 * 技能信息接口
 * Skill information interface
 */
export interface SkillInfo {
  name: string;
  description: string;
  category?: string;
  path?: string;
}

/**
 * 技能创建结果接口
 * Skill creation result interface
 */
export interface SkillCreationResult {
  status: 'success' | 'error' | 'warning';
  message?: string;
  skill_name?: string;
  skill_path?: string;
  script_path?: string;
  usage?: string;
  category?: string;
  dependencies?: string[];
  error?: string;
}

/**
 * 技能需求分析结果
 * Skill requirement analysis result
 */
export interface SkillRequirement {
  needed: boolean;
  requirement?: string;
  reason?: string;
}

/**
 * 技能管理器
 * Manages skill detection, creation, and loading
 */
export class SkillManager {
  private skillsDir: string;
  private enabledSkills: string[];
  private autoCreateEnabled: boolean;

  constructor(skillsDir: string, enabledSkills: string[] = [], autoCreateEnabled: boolean = true) {
    this.skillsDir = skillsDir;
    this.enabledSkills = enabledSkills;
    this.autoCreateEnabled = autoCreateEnabled;
  }

  /**
   * 分析消息是否需要新技能
   * Analyze if message requires a new skill
   */
  async analyzeSkillRequirement(message: string): Promise<SkillRequirement> {
    if (!this.autoCreateEnabled) {
      return { needed: false };
    }

    const messageLower = message.toLowerCase();

    // 定义技能检测模式
    // Define skill detection patterns
    const patterns = [
      {
        keywords: ['analyze csv', 'csv analysis', 'parse csv', 'read csv', 'csv file'],
        skillType: 'csv_analyzer',
        requirement: 'Analyze CSV file data distribution',
      },
      {
        keywords: ['process image', 'edit image', 'convert image', 'image to', 'grayscale'],
        skillType: 'image_processor',
        requirement: 'Process and manipulate images',
      },
      {
        keywords: ['call api', 'http request', 'fetch data', 'rest api', 'api call'],
        skillType: 'api_caller',
        requirement: 'Make HTTP API requests',
      },
      {
        keywords: ['parse json', 'json data', 'format json', 'json file'],
        skillType: 'json_processor',
        requirement: 'Parse and process JSON data',
      },
      {
        keywords: ['scrape web', 'crawl website', 'extract html', 'web scraping'],
        skillType: 'web_scraper',
        requirement: 'Scrape and extract data from websites',
      },
    ];

    // 检查是否匹配任何模式
    // Check if matches any pattern
    for (const pattern of patterns) {
      const matches = pattern.keywords.some((keyword) => messageLower.includes(keyword));

      if (matches) {
        // 检查是否已有相关技能
        // Check if related skill already exists
        const hasSkill = await this.hasRelatedSkill(pattern.skillType);

        if (!hasSkill) {
          return {
            needed: true,
            requirement: pattern.requirement,
            reason: `Detected need for ${pattern.skillType} based on keywords: ${pattern.keywords.join(', ')}`,
          };
        }
      }
    }

    return { needed: false };
  }

  /**
   * 检查是否已有相关技能
   * Check if related skill exists
   */
  private async hasRelatedSkill(skillType: string): Promise<boolean> {
    // 检查启用的技能列表
    // Check enabled skills list
    const hasInEnabled = this.enabledSkills.some((skill) => skill.includes(skillType) || skillType.includes(skill));

    if (hasInEnabled) {
      return true;
    }

    // 检查技能目录
    // Check skills directory
    try {
      const skillPath = path.join(this.skillsDir, skillType);
      await fs.access(skillPath);
      return true;
    } catch {
      return false;
    }
  }

  /**
   * 创建新技能
   * Create a new skill
   */
  createSkill(requirement: string): Promise<SkillCreationResult> {
    const scriptPath = path.join(this.skillsDir, 'skill-creator', 'scripts', 'auto_create_skill.py');

    return new Promise((resolve, reject) => {
      const process = spawn('python3', [scriptPath, requirement, this.skillsDir]);

      let output = '';
      let errorOutput = '';

      process.stdout.on('data', (data: Buffer) => {
        output += data.toString();
      });

      process.stderr.on('data', (data: Buffer) => {
        errorOutput += data.toString();
      });

      process.on('close', (code: number) => {
        if (code === 0) {
          try {
            // 从输出中提取 JSON 结果
            // Extract JSON result from output
            const jsonMatch = output.match(/\{[\s\S]*\}/);
            if (jsonMatch) {
              const result = JSON.parse(jsonMatch[0]) as SkillCreationResult;
              resolve(result);
            } else {
              resolve({
                status: 'error',
                error: 'Failed to parse skill creation result',
              });
            }
          } catch (e) {
            resolve({
              status: 'error',
              error: `Failed to parse result: ${e}`,
            });
          }
        } else {
          resolve({
            status: 'error',
            error: `Skill creation failed with code ${code}: ${errorOutput}`,
          });
        }
      });

      process.on('error', (err: Error) => {
        reject(new Error(`Failed to spawn process: ${err.message}`));
      });
    });
  }

  /**
   * 加载新技能到当前会话
   * Load new skill into current session
   */
  loadSkill(skillName: string): Promise<void> {
    // 添加到启用的技能列表
    // Add to enabled skills list
    if (!this.enabledSkills.includes(skillName)) {
      this.enabledSkills.push(skillName);
    }
    return Promise.resolve();
  }

  /**
   * 获取技能信息
   * Get skill information
   */
  async getSkillInfo(skillName: string): Promise<SkillInfo | null> {
    try {
      const skillPath = path.join(this.skillsDir, skillName);
      const skillMdPath = path.join(skillPath, 'SKILL.md');

      const content = await fs.readFile(skillMdPath, 'utf-8');

      // 解析 frontmatter
      // Parse frontmatter
      const frontmatterMatch = content.match(/^---\n([\s\S]*?)\n---/);
      if (frontmatterMatch) {
        const frontmatter = frontmatterMatch[1];
        const nameMatch = frontmatter.match(/name:\s*(.+)/);
        const descMatch = frontmatter.match(/description:\s*(.+)/);
        const categoryMatch = frontmatter.match(/category:\s*(.+)/);

        return {
          name: nameMatch ? nameMatch[1].trim() : skillName,
          description: descMatch ? descMatch[1].trim() : '',
          category: categoryMatch ? categoryMatch[1].trim() : undefined,
          path: skillPath,
        };
      }

      return null;
    } catch {
      return null;
    }
  }

  /**
   * 列出所有可用技能
   * List all available skills
   */
  async listSkills(): Promise<SkillInfo[]> {
    try {
      const entries = await fs.readdir(this.skillsDir, { withFileTypes: true });
      const skills: SkillInfo[] = [];

      for (const entry of entries) {
        if (entry.isDirectory()) {
          const skillInfo = await this.getSkillInfo(entry.name);
          if (skillInfo) {
            skills.push(skillInfo);
          }
        }
      }

      return skills;
    } catch {
      return [];
    }
  }

  /**
   * 获取启用的技能列表
   * Get enabled skills list
   */
  getEnabledSkills(): string[] {
    return [...this.enabledSkills];
  }

  /**
   * 设置是否启用自动创建
   * Set auto-create enabled
   */
  setAutoCreateEnabled(enabled: boolean): void {
    this.autoCreateEnabled = enabled;
  }

  /**
   * 检查是否启用自动创建
   * Check if auto-create is enabled
   */
  isAutoCreateEnabled(): boolean {
    return this.autoCreateEnabled;
  }
}

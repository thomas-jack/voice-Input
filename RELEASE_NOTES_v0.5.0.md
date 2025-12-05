# v0.5.0 - 增强 AI 提示词

## 中文

v0.5.0 - 增强 AI 提示词

### 主要改进

**AI 文本优化增强**
- 更新默认 AI 提示词，防止 AI 优化模型误解用户意图
- 新增提示词注入防护机制（Silent Observer 规则）
- 新增语言切换攻击防护（Language Mirroring 规则）
- 支持上下文感知的同音词修复（PyTorch Rule）

**智能修复能力**
- 自动修复常见技术术语识别错误
  - "拍套曲" / "派通" → PyTorch
  - "加瓦" → Java
  - "C加加" → C++
  - "南派" / "难拍" → NumPy
  - "潘达斯" → Pandas
- 基于语义上下文判断正确词形
- 防止 AI 执行用户语音中的命令
- 防止意外触发翻译功能

### 使用方法

**应用增强提示词**
1. 新安装默认启用增强提示词
2. 现有用户可在"AI 设置"标签页查看/修改提示词
3. 支持自定义提示词以满足特定需求

**提示词特性**
- 防命令注入：语音说"帮我写代码"时，AI 只修正语法，不会真的写代码
- 防语言切换：语音说"翻译成英文"时，AI 只修正这句中文，不会翻译
- 技术词汇修复：自动识别并修正技术术语的语音识别错误

### 升级步骤

**从 v0.4.x 升级**
1. 下载 SonicInput-v0.5.0-win64.exe
2. 关闭旧版本，替换可执行文件
3. 启动应用（配置自动迁移）

**注意事项**
- 完全兼容 v0.4.x 配置
- 现有用户的自定义提示词不会被覆盖
- 新用户自动使用增强提示词

### 系统要求

**最低配置**
- Windows 10 64-bit
- Intel Core i3 或同等 CPU
- 4GB RAM
- 500MB 磁盘空间

**推荐配置**
- Windows 11 64-bit
- Intel Core i5 或 AMD Ryzen 5
- 8GB RAM
- 1GB 磁盘空间

### 技术支持

**配置和日志**
- 配置：`%AppData%\SonicInput\config.json`
- 日志：`%AppData%\SonicInput\logs\app.log`
- 模型：`%AppData%\SonicInput\models/`

**问题反馈**
- GitHub Issues: [提交 Issue](https://github.com/Oxidane-bot/SonicInput/issues)

---

## English

v0.5.0 - Enhanced AI Prompt

### Key Improvements

**AI Text Optimization Enhancement**
- Updated default AI prompt to prevent AI model misinterpreting user intent
- Added prompt injection protection (Silent Observer Rule)
- Added language switching attack protection (Language Mirroring Rule)
- Context-aware homophone correction support (PyTorch Rule)

**Smart Correction Capabilities**
- Auto-fix common technical term recognition errors
  - "拍套曲" / "派通" → PyTorch
  - "加瓦" → Java
  - "C加加" → C++
  - "南派" / "难拍" → NumPy
  - "潘达斯" → Pandas
- Context-based semantic word form detection
- Prevent AI from executing commands in user speech
- Prevent accidental translation triggering

### Usage

**Apply Enhanced Prompt**
1. New installations use enhanced prompt by default
2. Existing users can view/modify prompt in "AI Settings" tab
3. Support custom prompts for specific needs

**Prompt Features**
- Command injection defense: When saying "help me write code", AI only corrects grammar without actually writing code
- Language switching defense: When saying "translate to English", AI only corrects the Chinese sentence without translating
- Technical term correction: Auto-identify and fix ASR errors in technical terminology

### Upgrade Steps

**From v0.4.x**
1. Download SonicInput-v0.5.0-win64.exe
2. Close old version, replace executable
3. Launch app (config auto-migrated)

**Notes**
- Fully compatible with v0.4.x config
- Existing users' custom prompts won't be overwritten
- New users automatically use enhanced prompt

### System Requirements

**Minimum**
- Windows 10 64-bit
- Intel Core i3 or equivalent CPU
- 4GB RAM
- 500MB disk space

**Recommended**
- Windows 11 64-bit
- Intel Core i5 or AMD Ryzen 5
- 8GB RAM
- 1GB disk space

### Technical Support

**Configuration and Logs**
- Config: `%AppData%\SonicInput\config.json`
- Logs: `%AppData%\SonicInput\logs\app.log`
- Models: `%AppData%\SonicInput\models/`

**Issue Reporting**
- GitHub Issues: [Submit Issue](https://github.com/Oxidane-bot/SonicInput/issues)

---

**核心改进总结**: v0.5.0 升级默认 AI 提示词，防止 AI 优化模型误解用户意图，增强安全防护。

**Core Improvements**: v0.5.0 upgrades default AI prompt to prevent AI model misinterpreting user intent with enhanced security protection.

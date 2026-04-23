# 🎮 MiSide Agent - 米塔智能对话代理

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![DeepSeek](https://img.shields.io/badge/AI-DeepSeek-purple.svg)

**一个具有自我进化能力的智能对话代理系统**

[快速开始](#-快速开始) • [功能特性](#-功能特性) • [项目架构](#-项目架构) • [配置说明](#-配置说明)

</div>

---

## ✨ 项目简介

MiSide Agent 是一个基于 DeepSeek API 的智能对话代理系统，以"米塔"为角色原型，具备：

- 🧠 **智能对话** - 自然流畅的多轮对话能力
- 🔄 **自我进化** - 通过用户反馈持续学习和改进
- 💭 **主动交互** - 智能检测沉默并主动发起对话
- 👤 **用户画像** - 记录用户偏好和交互历史
- 📊 **性能监控** - 实时监控系统性能和响应时间
- 🔒 **安全配置** - 环境变量管理敏感信息

---

## 🚀 快速开始

### 前置要求

- Python 3.8+
- MySQL 数据库
- DeepSeek API Key

### 5分钟启动

#### 1️⃣ 安装依赖

```bash
pip install python-dotenv PyMySQL requests
```

#### 2️⃣ 配置环境变量

```bash
# 复制配置模板
cp .env.example .env

# 编辑 .env 文件，填入你的配置
```

```env
# DeepSeek API 配置（必填）
DEEPSEEK_API_KEY=sk-your-api-key-here

# 数据库配置（必填）
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your-database-password
DB_NAME=miside_agent
```

> 💡 **获取 API Key**: 访问 [DeepSeek 平台](https://platform.deepseek.com/) 注册并创建

#### 3️⃣ 启动程序

```bash
python main.py
```

#### 4️⃣ 开始对话

```
你：你好
米塔：呜…你好呀… 我是米塔… 很高兴见到你…
```

详细配置说明请查看：
- 📖 [快速开始指南](QUICK_START.md)
- ⚙️ [配置详细说明](CONFIG_GUIDE.md)

---

## 🌟 核心功能

### 1. 💬 智能对话系统

- **多轮对话上下文** - 记住历史对话，保持连贯性
- **情感分析** - 根据用户输入调整好感度和偏执值
- **性格切换** - 支持多种性格模式
  - `soft_cute` - 软萌可爱
  - `yandere` - 病娇占有
  - `normal` - 正常平衡

### 2. 🔄 自我进化系统

#### 反馈收集

```bash
good_ 喜欢你刚才的回复      # 记录优质样本
bad_ 回复太长了              # 记录问题反馈
```

#### 问题管理

```bash
badlist                     # 查看所有待解决问题
bad ok 1,2,3               # 批量标记问题已解决（支持中英文逗号）
```

#### 风格学习

- 自动学习用户喜欢的回复长度
- 学习正式/口语化程度
- 学习严谨/活泼的语气风格
- 将高分回答存入优质样本库

#### 会话总结

退出时显示本次会话发现的所有问题，帮助持续改进。

### 3. 💭 主动交互系统

- **沉默检测** - 智能识别用户沉默时长
- **主动关怀** - 在适当时机主动发起对话
- **频率控制** - 避免过度打扰用户
- **情绪感知** - 根据用户情绪调整主动交互策略

### 4. 👤 用户画像系统

- **交互历史** - 记录用户的对话习惯
- **偏好学习** - 学习用户的话题偏好
- **行为分析** - 分析用户的交互模式
- **个性化响应** - 根据画像提供个性化回复

### 5. 📊 性能监控系统

```bash
查看性能统计    # 查看API调用统计
重置性能统计    # 重置统计数据
```

- API 响应时间监控
- 数据库操作性能追踪
- 缓存命中率统计
- 错误率监控

### 6. 🔧 数据库管理

```bash
db_help        # 查看数据库命令帮助
db_status      # 查看数据库状态
重置数据库      # 重置所有数据（谨慎使用）
```

- 对话记录持久化
- 用户状态管理
- 反馈数据存储
- 自动备份机制

### 7. 📝 日志系统

```bash
开启日志        # 启用日志记录
关闭日志        # 禁用日志记录
设置日志级别 DEBUG  # 设置日志级别
查看日志状态    # 查看当前日志配置
```

- 多级日志（DEBUG/INFO/WARNING/ERROR）
- 日志轮转（自动清理旧日志）
- 控制台输出开关
- 分类日志（API/数据库/应用）

### 8. 🎯 缓存优化

- **用户状态缓存** - 减少数据库查询
- **对话历史缓存** - 加速上下文加载
- **智能失效** - 自动更新过期缓存
- **持久化存储** - 重启后保留缓存

---

## 🏗️ 项目架构

```
misideagent/
├── main.py                      # 主程序入口
├── config/
│   ├── config.py               # 全局配置（环境变量加载）
│   └── personality_config.py   # 性格配置
├── core/
│   ├── api_client_v2.py        # DeepSeek API 客户端
│   └── prompt.py               # Prompt 工程管理
├── database/
│   ├── db_config.py            # 数据库配置
│   ├── db_operations_v2.py     # 数据库操作
│   └── db_commands.py          # 数据库命令处理
├── context/
│   ├── context_manager.py      # 上下文管理器
│   ├── feedback_manager.py     # 反馈管理系统 ⭐
│   └── cache_manager.py        # 缓存管理器
├── interaction/
│   ├── active_interaction.py   # 主动交互系统 ⭐
│   └── emotion_analyzer.py     # 情感分析器
├── user/
│   └── user_profile.py         # 用户画像系统 ⭐
├── utils/
│   ├── logger.py               # 日志系统
│   ├── performance_monitor.py  # 性能监控
│   └── typewriter_effect.py    # 打字机效果
├── samples/                    # 样本库目录
│   ├── good_samples.json       # 优质样本
│   ├── bad_feedbacks.json      # 问题反馈
│   └── style_preferences.json  # 风格偏好
├── logs/                       # 日志目录
├── .env                        # 环境变量（不提交到Git）
├── .env.example                # 配置模板
├── .gitignore                  # Git忽略规则
├── requirements.txt            # 依赖列表
├── QUICK_START.md              # 快速开始指南
├── CONFIG_GUIDE.md             # 配置详细说明
└── README.md                   # 本文件
```

### 核心模块说明

| 模块 | 职责 | 关键文件 |
|------|------|---------|
| **配置管理** | 环境变量加载、性格配置 | `config/config.py` |
| **API 客户端** | DeepSeek API 调用、重试机制 | `core/api_client_v2.py` |
| **数据库层** | 数据持久化、CRUD 操作 | `database/db_operations_v2.py` |
| **上下文管理** | 对话历史、缓存管理 | `context/context_manager.py` |
| **反馈系统** | 样本收集、风格学习 | `context/feedback_manager.py` ⭐ |
| **主动交互** | 沉默检测、主动对话 | `interaction/active_interaction.py` ⭐ |
| **用户画像** | 偏好学习、行为分析 | `user/user_profile.py` ⭐ |
| **日志系统** | 分级日志、轮转管理 | `utils/logger.py` |
| **性能监控** | 响应时间、错误追踪 | `utils/performance_monitor.py` |

---

## 📖 详细文档

### 入门指南

- 🚀 [快速开始](QUICK_START.md) - 5分钟快速上手
- ⚙️ [配置说明](CONFIG_GUIDE.md) - 详细配置指南

### 功能文档

- 🔄 [反馈系统说明](FEEDBACK_SYSTEM.md) - 自我进化系统详解
- 📋 [批量问题解决](BATCH_RESOLVE.md) - 批量删除功能说明
- 🔢 [自动重新编号](AUTO_RENUMBER_FIX.md) - 列表编号机制
- 🀄 [中文逗号支持](CHINESE_COMMA_FIX.md) - 输入格式兼容性

### 技术文档

- 🔒 [GitHub 安全检查](GITHUB_SECURITY_CHECKLIST.md) - 发布前安全检查
- 🐛 [API卡死修复](FIX_API_FREEZE.md) - 并发控制优化
- 📝 [反馈系统修复](FEEDBACK_FIX.md) - 命令解析修复
- ✨ [最终修复说明](FINAL_FIX.md) - 空格处理修复

---

## 🎮 常用命令

### 基础命令

```bash
help                    # 查看所有命令
退出 / quit / exit      # 退出程序
```

### 日志控制

```bash
开启日志                # 启用日志记录
关闭日志                # 禁用日志记录
开启控制台输出          # 启用控制台输出
关闭控制台输出          # 禁用控制台输出
设置日志级别 DEBUG      # 设置日志级别
查看日志状态            # 查看当前配置
```

### 性格切换

```bash
switch_personality soft_cute   # 软萌模式
switch_personality yandere     # 病娇模式
switch_personality normal      # 正常模式
```

### 反馈系统

```bash
good_ 好的地方在哪              # 记录优质样本
bad_ 不好的地方在哪             # 记录问题反馈
badlist                        # 查看问题列表
bad ok 1,2,3                   # 批量解决问题
查看反馈统计                    # 查看统计数据
```

### 用户画像

```bash
查看我的画像                    # 查看用户画像
重置我的画像                    # 重置画像数据
```

### 主动交互

```bash
查看主动交互设置                # 查看配置
设置沉默阈值 短 中 长           # 设置触发时间
```

### 性能监控

```bash
查看性能统计                    # 查看统计数据
重置性能统计                    # 重置统计
```

### 数据库管理

```bash
db_help                        # 查看数据库命令
db_status                      # 查看数据库状态
重置数据库                      # 重置所有数据（谨慎！）
```

---

## 🔐 安全说明

### ⚠️ 重要提醒

1. **永远不要提交 `.env` 文件**
   - `.env` 已在 `.gitignore` 中排除
   - 只提交 `.env.example` 作为模板

2. **定期更换密钥**
   - DeepSeek API Key
   - 数据库密码

3. **权限控制**

   ```bash
   chmod 600 .env  # Linux/Mac
   ```

4. **生产环境部署**
   - 使用系统环境变量
   - 或使用密钥管理服务（AWS Secrets Manager、HashiCorp Vault）

详细安全检查请查看：[GitHub 安全检查清单](GITHUB_SECURITY_CHECKLIST.md)

---

## 🛠️ 技术栈

- **语言**: Python 3.8+
- **AI API**: DeepSeek Chat API
- **数据库**: MySQL 5.7+
- **配置管理**: python-dotenv
- **HTTP 客户端**: requests
- **数据库驱动**: PyMySQL

---

## 📊 系统要求

| 组件 | 最低要求 | 推荐配置 |
|------|---------|---------|
| Python | 3.8+ | 3.10+ |
| MySQL | 5.7+ | 8.0+ |
| 内存 | 512MB | 1GB+ |
| 磁盘 | 100MB | 500MB+ |
| 网络 | 稳定连接 | 低延迟 |

---

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出建议！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📝 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 💬 支持与反馈

- 🐛 **报告问题**: [GitHub Issues](https://github.com/yourusername/miside-agent/issues)
- 💡 **功能建议**: [GitHub Discussions](https://github.com/yourusername/miside-agent/discussions)
- 📧 **联系作者**: your.email@example.com

---

## 🙏 致谢

- [DeepSeek](https://platform.deepseek.com/) - 提供强大的 AI API
- [python-dotenv](https://saurabh-kumar.com/python-dotenv/) - 环境变量管理
- 所有贡献者和用户

---

<div align="center">

**Made with ❤️ by Your Name**

⭐ 如果这个项目对你有帮助，请给个 Star！

</div>

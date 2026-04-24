# 🎮 MiSide Agent - 米塔智能对话代理

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![DeepSeek](https://img.shields.io/badge/AI-DeepSeek-purple.svg)
![MySQL](https://img.shields.io/badge/Database-MySQL-orange.svg)

**一个具有自我进化能力的智能对话代理系统**

[快速开始](#-快速开始) • [功能特性](#-功能特性) • [常见问题](#-常见问题) • [项目架构](#-项目架构)

</div>

---

## ✨ 项目简介

知识产权与素材声明 ⚠️

项目中使用的所有二次元角色名称、设定、图像资源（包含但不限于立绘、截图、图标等）的版权均属于其原版权方或原作者（如各大动画制作委员会、游戏开发商、插画师等）。
本项目不主张对任何引用的角色 IP 拥有所有权。本项目属于"合理使用（Fair Use）"范畴下的同人衍生交流性质。如有侵权，请提交 Issue 或通过邮件联系，我们将第一时间配合下架并删除相关内容。
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

- ✅ Python 3.8+
- ✅ MySQL 5.7+（或 MariaDB）
- ✅ DeepSeek API Key

### ⚡ 5分钟启动指南

#### 1️⃣ 克隆项目

```bash
git clone https://github.com/yourusername/mitaagent.git
cd mitaagent
2️⃣ 创建虚拟环境（推荐）
使用 venv：
bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
或使用 Conda：
bash
conda create -n mitaagent python=3.10
conda activate mitaagent
3️⃣ 安装依赖
bash
pip install -r requirements.txt
这将自动安装：
python-dotenv - 环境变量管理
PyMySQL - MySQL 数据库驱动
requests - HTTP 客户端
4️⃣ 配置环境变量
bash
# 复制配置模板
cp .env.example .env

# 编辑 .env 文件
在 .env 文件中填入你的配置：
env
# DeepSeek API 配置（必填）
DEEPSEEK_API_KEY=sk-your-api-key-here
DEEPSEEK_API_URL=https://api.deepseek.com/v1/chat/completions
DEEPSEEK_MODEL=deepseek-chat

# 数据库配置（必填）
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your-database-password
DB_NAME=miside_agent

# API 参数（可选）
API_TEMPERATURE=0.7
API_MAX_TOKENS=150

# 日志配置（可选）
LOG_LEVEL=INFO
LOG_ENABLED=True
CONSOLE_OUTPUT=True
💡 获取 API Key: 访问 DeepSeek 平台 注册并创建
5️⃣ 准备数据库
确保 MySQL 服务正在运行：
bash
# Windows
net start mysql

# Linux
sudo systemctl start mysql

# macOS
brew services start mysql
创建数据库（如果不存在）：
bash
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS miside_agent CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
6️⃣ 启动程序
bash
python main.py
7️⃣ 开始对话
plaintext
你：你好
米塔：呜…你好呀… 我是米塔… 很高兴见到你…
❓ 常见问题
问题1：ModuleNotFoundError: No module named 'dotenv'
原因： 依赖未正确安装解决：
bash
pip install -r requirements.txt
问题2：数据库连接失败
检查清单：
MySQL 服务是否启动？
bash
# Windows
net start mysql

# 检查服务状态
sc query mysql
数据库是否存在？
bash
mysql -u root -p -e "SHOW DATABASES;" | findstr miside_agent
配置是否正确？
检查 .env 文件中的 DB_HOST、DB_PORT、DB_USER、DB_PASSWORD
确保密码正确无误
测试连接：
bash
python test_db_connection.py
问题3：从 GitHub 克隆后无法连接数据库
原因： .env 文件被 .gitignore 忽略（这是正确的安全做法）解决：
复制 .env.example 为 .env
填入你的实际配置
确保数据库已创建
bash
cp .env.example .env
# 编辑 .env 文件
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS miside_agent;"
问题4：多 Python 环境问题
症状： 安装了依赖但仍然报错原因： 依赖安装在了错误的 Python 环境中解决：
bash
# 确认当前使用的 Python
where python        # Windows
which python        # Linux/Mac

# 在正确的环境中安装
python -m pip install -r requirements.txt

# 如果使用 Conda
conda activate your_env_name
pip install -r requirements.txt
问题5：API 配额耗尽
症状： 收到 "我现在有点忙，暂时无法回复你" 的提示解决：
检查 DeepSeek API 配额使用情况
等待配额重置
考虑升级 API 套餐
更多问题请查看 FAQ 或提交 Issue
🌟 核心功能
1. 💬 智能对话系统
多轮对话上下文 - 记住历史对话，保持连贯性
情感分析 - 根据用户输入调整好感度和偏执值
性格切换 - 支持多种性格模式
soft_cute - 软萌可爱
yandere - 病娇占有
normal - 正常平衡
2. 🔄 自我进化系统
反馈收集
bash
good_ 喜欢你刚才的回复      # 记录优质样本
bad_ 回复太长了              # 记录问题反馈
问题管理
bash
badlist                     # 查看所有待解决问题
bad ok 1,2,3               # 批量标记问题已解决（支持中英文逗号）
风格学习
自动学习用户喜欢的回复长度
学习正式/口语化程度
学习严谨/活泼的语气风格
将高分回答存入优质样本库
会话总结
退出时显示本次会话发现的所有问题，帮助持续改进。
3. 💭 主动交互系统
沉默检测 - 智能识别用户沉默时长
主动关怀 - 在适当时机主动发起对话
频率控制 - 避免过度打扰用户
情绪感知 - 根据用户情绪调整主动交互策略
4. 👤 用户画像系统
交互历史 - 记录用户的对话习惯
偏好学习 - 学习用户的话题偏好
行为分析 - 分析用户的交互模式
个性化响应 - 根据画像提供个性化回复
5. 📊 性能监控系统
bash
查看性能统计    # 查看API调用统计
重置性能统计    # 重置统计数据
API 响应时间监控
数据库操作性能追踪
缓存命中率统计
错误率监控
6. 🔧 数据库管理
bash
db_help        # 查看数据库命令帮助
db_status      # 查看数据库状态
重置数据库      # 重置所有数据（谨慎使用）
对话记录持久化
用户状态管理
反馈数据存储
自动备份机制
7. 📝 日志系统
bash
开启日志        # 启用日志记录
关闭日志        # 禁用日志记录
设置日志级别 DEBUG  # 设置日志级别
查看日志状态    # 查看当前日志配置
多级日志（DEBUG/INFO/WARNING/ERROR）
日志轮转（自动清理旧日志）
控制台输出开关
分类日志（API/数据库/应用）
8. 🎯 缓存优化
用户状态缓存 - 减少数据库查询
对话历史缓存 - 加速上下文加载
智能失效 - 自动更新过期缓存
持久化存储 - 重启后保留缓存
🏗️ 项目架构
plaintext
mitaagent/
├── main.py                      # 主程序入口
├── config/
│   ├── __init__.py
│   ├── config.py               # 全局配置（环境变量加载）
│   ├── config_manager.py       # 配置管理器
│   └── personality_config.py   # 性格配置
├── core/
│   ├── __init__.py
│   ├── api_client_v2.py        # DeepSeek API 客户端
│   └── typewriter_effect.py    # 打字机效果
├── database/
│   ├── __init__.py
│   ├── db_config.py            # 数据库配置
│   ├── db_operations_v2.py     # 数据库操作（增强版）
│   └── db_commands.py          # 数据库命令处理
├── context/
│   ├── __init__.py
│   ├── context_manager.py      # 上下文管理器
│   ├── cache_manager.py        # 缓存管理器
│   ├── feedback_manager.py     # 反馈管理系统 ⭐
│   ├── emotion_analyzer.py     # 情感分析器
│   └── user_profile.py         # 用户画像
├── interaction/
│   ├── __init__.py
│   └── active_interaction.py   # 主动交互系统 ⭐
├── utils/
│   ├── __init__.py
│   ├── logger.py               # 日志系统
│   ├── performance_monitor.py  # 性能监控
│   └── prompt.py               # Prompt 工程管理
├── samples/                    # 样本库目录
│   ├── good_samples.json       # 优质样本
│   ├── bad_feedbacks.json      # 问题反馈
│   ├── style_preferences.json  # 风格偏好
│   └── last_session_summary.json
├── logs/                       # 日志目录（自动生成）
│   ├── app.log
│   ├── database.log
│   └── api.log
├── .env                        # 环境变量（不提交到Git）⚠️
├── .env.example                # 配置模板
├── .gitignore                  # Git忽略规则
├── requirements.txt            # Python依赖列表
├── user_profile.json           # 用户画像数据
├── backup_conversations.txt    # 对话备份文件
└── README.md                   # 本文件
核心模块说明
模块	职责	关键文件
配置管理	环境变量加载、性格配置	config/config.py
API 客户端	DeepSeek API 调用、重试机制	core/api_client_v2.py
数据库层	数据持久化、CRUD 操作	database/db_operations_v2.py
上下文管理	对话历史、缓存管理	context/context_manager.py
反馈系统	样本收集、风格学习	context/feedback_manager.py ⭐
主动交互	沉默检测、主动对话	interaction/active_interaction.py ⭐
用户画像	偏好学习、行为分析	context/user_profile.py ⭐
日志系统	分级日志、轮转管理	utils/logger.py
性能监控	响应时间、错误追踪	utils/performance_monitor.py
🎮 常用命令
基础命令
bash
help                    # 查看所有命令
退出 / quit / exit      # 退出程序
日志控制
bash
开启日志                # 启用日志记录
关闭日志                # 禁用日志记录
开启控制台输出          # 启用控制台输出
关闭控制台输出          # 禁用控制台输出
设置日志级别 DEBUG      # 设置日志级别
查看日志状态            # 查看当前配置
性格切换
bash
switch_personality soft_cute   # 软萌模式
switch_personality yandere     # 病娇模式
switch_personality normal      # 正常模式
反馈系统
bash
good_ 好的地方在哪              # 记录优质样本
bad_ 不好的地方在哪             # 记录问题反馈
badlist                        # 查看问题列表
bad ok 1,2,3                   # 批量解决问题
查看反馈统计                    # 查看统计数据
用户画像
bash
查看我的画像                    # 查看用户画像
重置我的画像                    # 重置画像数据
主动交互
bash
查看主动交互设置                # 查看配置
设置沉默阈值 短 中 长           # 设置触发时间
性能监控
bash
查看性能统计                    # 查看统计数据
重置性能统计                    # 重置统计
数据库管理
bash
db_help                        # 查看数据库命令
db_status                      # 查看数据库状态
重置数据库                      # 重置所有数据（谨慎！）
🔐 安全说明
⚠️ 重要提醒
永远不要提交 .env 文件
.env 已在 .gitignore 中排除
只提交 .env.example 作为模板
包含敏感的 API Key 和数据库密码
定期更换密钥
DeepSeek API Key
数据库密码
文件权限保护
bash
# Linux/Mac
chmod 600 .env

# Windows（PowerShell）
icacls .env /inheritance:r
icacls .env /grant:r "%USERNAME%":R
生产环境部署
使用系统环境变量而非 .env 文件
或使用密钥管理服务（AWS Secrets Manager、HashiCorp Vault、Azure Key Vault）
数据库安全
不要使用 root 用户连接生产数据库
创建专用的数据库用户并限制权限
启用 SSL/TLS 加密连接
🛠️ 技术栈
类别	技术	版本要求
编程语言	Python	3.8+
AI API	DeepSeek Chat API	-
数据库	MySQL / MariaDB	5.7+ / 10.3+
配置管理	python-dotenv	>=1.0.0
HTTP 客户端	requests	>=2.31.0
数据库驱动	PyMySQL	>=1.1.0
📊 系统要求
组件	最低要求	推荐配置
Python	3.8+	3.10+
MySQL	5.7+	8.0+
内存	512MB	1GB+
磁盘	100MB	500MB+
网络	稳定连接	低延迟
🤝 贡献指南
欢迎贡献代码、报告问题或提出建议！
贡献步骤
Fork 本仓库
创建特性分支 (git checkout -b feature/AmazingFeature)
提交更改 (git commit -m 'Add some AmazingFeature')
推送到分支 (git push origin feature/AmazingFeature)
开启 Pull Request
开发环境设置
bash
# 1. Fork 并克隆
git clone https://github.com/yourusername/mitaagent.git
cd mitaagent

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 创建 .env 文件
cp .env.example .env
# 编辑 .env 填入配置

# 5. 运行测试
python main.py
代码规范
遵循 PEP 8 编码规范
添加必要的注释和文档字符串
确保新功能有适当的测试
更新相关文档
📝 许可证
本项目采用 MIT 许可证 - 详见 LICENSE 文件
💬 支持与反馈
🐛 报告问题: GitHub Issues
💡 功能建议: GitHub Discussions
📧 联系作者: your.email@example.com
🙏 致谢
DeepSeek - 提供强大的 AI API
python-dotenv - 环境变量管理
PyMySQL - MySQL 数据库驱动
所有贡献者和用户
📚 相关资源
📘 Python 官方文档
📗 DeepSeek API 文档
📙 MySQL 官方文档
<div align="center">Made with ❤️ by 衣服修改⭐ 如果这个项目对你有帮助，请给个 Star！🚀 快速开始 • ❓ 常见问题 • 📖 详细文档</div>
plaintext

---

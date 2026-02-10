# 贡献指南

感谢您对 yonglelaoren-feedland-parser 的关注！我们欢迎各种形式的贡献。

## 如何贡献

### 报告 Bug

如果您发现了 bug，请：
1. 搜索现有的 [Issues](https://github.com/yonglelaoren/yonglelaoren-feedland-parser/issues) 确认问题未被报告
2. 创建新的 Issue，提供详细的信息：
   - 问题描述
   - 复现步骤
   - 预期行为
   - 实际行为
   - 环境信息（操作系统、Python 版本等）
   - 相关的日志或错误信息

### 提交功能请求

如果您有新的功能想法，请：
1. 搜索现有的 Issues 确认请求未被提出
2. 创建新的 Issue，详细描述：
   - 功能描述
   - 使用场景
   - 预期的效果

### 提交代码

如果您想修复 bug 或添加新功能，请遵循以下步骤：

#### 1. Fork 项目

在 GitHub 上 Fork 项目到您的账号。

#### 2. 克隆仓库

```bash
git clone https://github.com/YOUR_USERNAME/yonglelaoren-feedland-parser.git
cd yonglelaoren-feedland-parser
```

#### 3. 创建分支

```bash
git checkout -b feature/your-feature-name
# 或
git checkout -b fix/your-bug-fix
```

#### 4. 设置开发环境

```bash
pip install -e ".[dev]"
```

#### 5. 进行开发

- 遵循 PEP 8 代码规范
- 添加必要的测试
- 更新相关文档

#### 6. 运行测试

```bash
pytest
```

#### 7. 代码格式化

```bash
black src/ tests/
```

#### 8. 类型检查

```bash
mypy src/
```

#### 9. 提交更改

```bash
git add .
git commit -m "feat: add your feature description"
# 或
git commit -m "fix: fix bug description"
```

提交消息遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范：
- `feat:` 新功能
- `fix:` bug 修复
- `docs:` 文档更新
- `style:` 代码格式（不影响功能）
- `refactor:` 重构
- `test:` 测试相关
- `chore:` 构建/工具相关

#### 10. 推送分支

```bash
git push origin feature/your-feature-name
```

#### 11. 创建 Pull Request

在 GitHub 上创建 Pull Request，提供：
- 清晰的标题
- 详细的描述
- 关联的 Issue（如果有）

## 代码规范

### Python 代码风格

- 遵循 PEP 8 规范
- 使用 Black 进行代码格式化
- 使用 flake8 进行代码检查
- 使用 mypy 进行类型检查

### 测试

- 为新功能添加测试
- 确保所有测试通过
- 保持测试覆盖率在 80% 以上

### 文档

- 为公共 API 添加文档字符串
- 遵循 Google 风格的文档字符串
- 更新 README 和相关文档

## 项目结构

```
yonglelaoren-feedland-parser/
├── src/
│   └── yonglelaoren_feedland_parser/
│       ├── __init__.py
│       ├── config.py
│       ├── opml_parser.py
│       ├── feed_parser.py
│       ├── article_extractor.py
│       ├── tracker.py
│       ├── deduplicator.py
│       ├── parallel_processor.py
│       └── cli.py
├── tests/
│   ├── test_config.py
│   ├── test_opml_parser.py
│   ├── test_feed_parser.py
│   ├── test_article_extractor.py
│   ├── test_tracker.py
│   ├── test_deduplicator.py
│   ├── test_parallel_processor.py
│   └── test_cli.py
├── config.example.json
├── pyproject.toml
├── setup.cfg
├── README.md
├── CONTRIBUTING.md
├── CHANGELOG.md
└── LICENSE
```

## 问题或疑问

如果您在贡献过程中有任何问题，请随时：
- 提交 Issue
- 发送邮件至 yonglelaoren@example.com
- 在 Pull Request 中提问

## 许可证

通过提交代码，您同意您的贡献将按照项目的 MIT 许可证进行授权。
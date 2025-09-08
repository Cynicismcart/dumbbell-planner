# Contributing Guide

感谢你的贡献意愿！

## 开发环境
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install pytest black flake8
```

## 代码规范
- 使用 **Black** 自动格式化（`black .`）。
- 使用 **Flake8** 进行静态检查。

## 提交流程
- Fork 并创建分支：`feat/<feature-name>` 或 `fix/<bug-name>`。
- 保持提交粒度清晰；涉及逻辑变更请补充/更新测试。
- 提交 PR 前：`black . && flake8 . && pytest -q` 全部通过。

## 反馈问题
- 请使用 Bug 模板，描述环境与复现步骤。

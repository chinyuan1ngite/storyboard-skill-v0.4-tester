# 安装与环境

## 真实依赖

- Python：3.10 或更高版本。
- 第三方 Python dependencies：none。
- 文件编码：UTF-8。
- 必需环境变量：none。
- Seedance 凭据或视频服务：不包含，也不是本地工具链依赖。

当前代码只使用 Python 标准库：`argparse`、`copy`、`hashlib`、`importlib`、`json`、`pathlib`、`re`、`subprocess`、`tempfile` 等。

Python 3.10 是最低版本，因为运行代码使用 Python 3.10 语法和 API。不要为了安装本包额外运行 `pip install`。

## 平台状态

Windows 已完成同等级结构、回归、依赖闭包和打包隔离验证。代码没有主动调用 Windows 专用 API，macOS/Linux 理论兼容，但本次交付没有完成同等级平台验证。

## Windows PowerShell

```powershell
Expand-Archive .\storyboard-skill-v0.4-tester.zip -DestinationPath .\storyboard-tester
Set-Location .\storyboard-tester
python scripts\check_environment.py
python scripts\verify_package.py
python scripts\smoke_test.py
```

如果 `python` 不存在，可尝试 Windows Python Launcher：

```powershell
py -3.10 scripts\check_environment.py
```

## macOS / Linux

```bash
unzip storyboard-skill-v0.4-tester.zip -d storyboard-tester
cd storyboard-tester
python3 scripts/check_environment.py
python3 scripts/verify_package.py
python3 scripts/smoke_test.py
```

## 安装为 Agent Skill

`skill/` 本身是自包含 Skill，并且不依赖外层目录名称。复制整个 `skill/` 到你的 Skill loader 所要求的位置，确保：

```text
your-skill-name/
├── SKILL.md
├── core/
├── capabilities/
├── routing/
├── adapters/
├── schemas/
├── scripts/
├── runtime/
└── _runtime/
```

不同 Agent/LLM 产品的 Skill 安装方式可能不同；本包只保证目录自包含，不编造特定产品不存在的安装命令。

## 当前目录与写权限

核心工具通过脚本自身位置定位 `skill/`，不要求终端位于固定父目录。示例命令假设当前目录是 Tester 包根目录。

Adapter 输出目录和 smoke test 临时目录需要写权限。Skill 源文件本身不需要写权限。

## 推荐环境设置

不是必需，但中文终端输出异常时可设置：

Windows PowerShell：

```powershell
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONDONTWRITEBYTECODE = "1"
```

macOS/Linux：

```bash
export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8
export PYTHONDONTWRITEBYTECODE=1
```

## 安全

本包不需要 API key、token 或 password。不要把任何凭据写入 `config/environment.example`、模板或问题报告。

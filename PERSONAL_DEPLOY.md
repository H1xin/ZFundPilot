# H1xin 的 ZFundPilot 本机部署

仓库：<https://github.com/H1xin/ZFundPilot>。源项目：<https://github.com/Euzohn/ZFundPilot>。

## 分支安排

- `main`：保留源项目代码，通过 GitHub 的 **Sync fork → Update branch** 同步。
- `personal`：本机部署和后续定制。设为默认分支，以运行此分支的更新检查工作流。
- `Check upstream updates`：每周一北京时间 09:17 检查上游与 `main` 的提交是否相同，也可在 Actions 手动运行。结果见工作流 Summary；不会自动合并或部署。

## 日常使用

在项目根目录双击 `start-local.cmd`，然后打开 <http://127.0.0.1:8000>。
关闭启动窗口或按 Ctrl+C 可以停止服务。系统只监听本机回环地址，不对局域网或公网开放；电脑关机、休眠或服务停止后，定时任务不会执行。

本次安装位置为 `D:\Codex github\ZFundPilot`，数据保存在该目录的 `data` 文件夹。启动脚本会使用项目的 `.venv` Python 环境和已构建的 `frontend/dist` 页面。

## 在新电脑上安装

需要 Git、Python 3.11.5+ 和 Node.js 22。PowerShell 中执行：

```powershell
git clone --branch personal https://github.com/H1xin/ZFundPilot.git
Set-Location ZFundPilot
python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -e .
Push-Location frontend
npm.cmd ci
npm.cmd run build
Pop-Location
.\start-local.cmd
```

启动脚本不自动读取 Docker 使用的 `.env` 文件。首次启动后可在设置页配置访问密码；若需首次启动就设密码，可在运行脚本前设置进程环境变量 `ZFUNDPILOT_PASSWORD`。请勿把密码写进启动脚本。

## 接入 AI

打开系统设置中的 AI 配置，填写服务商的 API Key、Base URL 和当前可用模型名称，并测试连接。

- DeepSeek：`https://api.deepseek.com/v1`
- OpenAI：`https://api.openai.com/v1`
- Gemini 的 OpenAI 兼容接口：`https://generativelanguage.googleapis.com/v1beta/openai/`，需要实测所选模型的流式响应和工具调用兼容性。

这些配置使用 API Key；本仓库没有增加 ChatGPT 或 Gemini 订阅账号登录功能。密钥由原项目加密保存于本机 `data` 目录，不提交到 GitHub。调用远程 AI 时，相应持仓上下文或上传图片会发往所选模型服务商。

截图导入需要支持图片输入的模型，可与文字分析分别配置。未填写 API Key 时，持仓和净值等基础功能仍可使用。

## 接收源项目更新

1. 在 GitHub 切换到 `main`，执行 **Sync fork → Update branch**。
2. 在自己的仓库创建 PR，确认目标为 `H1xin/ZFundPilot`，**base: personal，compare: main**。检查差异、处理冲突并合并。
3. 停止本机服务，将整个 `data` 文件夹复制到仓库以外的位置备份。它包含数据库、AI 加密密钥及登录配置。
4. 在本机项目目录执行以下命令，再双击启动脚本。

```powershell
git switch personal
git pull --ff-only origin personal
& .\.venv\Scripts\python.exe -m pip install -e .
Push-Location frontend
npm.cmd ci
npm.cmd run build
Pop-Location
```

若工作区存在未提交修改，先保存自己的改动再拉取，不要强制覆盖。更新前阅读上游版本说明，特别留意数据库迁移。

`.gitignore` 已排除 `data/`、`.env`、`.venv/` 和前端构建产物。不要使用 `git add -f` 上传这些目录或文件。本地数据不随 Git 更新自动备份。

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
& .\.venv\Scripts\python.exe .\build-local.py
```

按下文校验并安装构建产物后，双击 `start-local.cmd`。

启动脚本不自动读取 Docker 使用的 `.env` 文件。首次启动后可在设置页配置访问密码；若需首次启动就设密码，可在运行脚本前设置进程环境变量 `ZFUNDPILOT_PASSWORD`。请勿把密码写进启动脚本。

## 构建、溯源和回滚

日常部署前，先提交或合并要部署的代码，并记录改动。用 `.venv\Scripts\python.exe .\build-local.py` 构建当前 `HEAD`，或加 `--ref <完整 SHA>` 构建指定提交。脚本用 `git archive` 提取该提交中的前端文件，然后依次执行 `npm ci`、现有前端测试及生产构建。工作区未提交文件和本机 `.env` 不会进入源码快照。开发调试可继续使用上游的开发命令。

成功后，脚本在 `data/build-history/` 下保留一个新目录，包含 `build.json` 和 `frontend-dist.zip`。记录包括源码完整 SHA、与本地 `origin/main` 的共同祖先、构建脚本和依赖文件的 SHA-256、工具版本、构建命令和产物 SHA-256。共同祖先基于最近一次拉取的 `origin/main`，浅克隆缺少历史时可能为空。Python 包清单记录本机环境，后端及数据库仍需单独备份。此记录为本机生成的未签名清单，构建记录与产物保存在本机。

安装前停止本机服务，确认 `build.json` 中的 `source_commit` 与 `git rev-parse HEAD` 一致。将下方目录替换为脚本输出的目录，再执行：

```powershell
$build = Get-Item -LiteralPath 'data\build-history\<构建目录>'
$record = Get-Content -LiteralPath (Join-Path $build.FullName 'build.json') -Raw | ConvertFrom-Json
if ((git rev-parse HEAD) -ne $record.source_commit) { throw 'Source commit does not match build.json.' }
$bundle = Join-Path $build.FullName 'frontend-dist.zip'
if ((Get-FileHash -LiteralPath $bundle -Algorithm SHA256).Hash -ne $record.artifact.sha256) {
    throw 'Frontend archive checksum does not match build.json.'
}
$backup = Join-Path 'data' ('previous-dist-' + $build.Name)
if (Test-Path -LiteralPath $backup) { throw 'The previous frontend backup already exists.' }
$staged = Join-Path $build.FullName 'staged-dist'
Expand-Archive -LiteralPath $bundle -DestinationPath $staged
if (Test-Path -LiteralPath 'frontend\dist') { Move-Item -LiteralPath 'frontend\dist' -Destination $backup }
Move-Item -LiteralPath $staged -Destination 'frontend\dist'
```

回滚时从旧 `build.json` 找回完整源码 SHA，用 `git worktree add --detach <恢复目录> <完整 SHA>` 在独立目录检出，按当时的 Python 环境与配置恢复后端，并用旧压缩包恢复前端。若新版已迁移 SQLite，优先使用升级前的数据库备份在恢复目录验证旧版，避免旧程序直接打开新版数据库。

功能、修复及迁移说明写入 [个人更新记录](PERSONAL_CHANGELOG.md)。上游版本变化仍查看 [上游更新日志](CHANGELOG.md)。本机溯源规则参考 [SLSA 构建溯源](https://slsa.dev/spec/v1.2/build-provenance)、[npm ci](https://docs.npmjs.com/cli/commands/npm-ci/)、[pip 可重复安装](https://pip.pypa.io/en/stable/topics/repeatable-installs/) 和 [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)。如果未来发布供他人下载的版本，可用 [GitHub Artifact Attestations](https://docs.github.com/en/actions/concepts/security/artifact-attestations) 签署发布产物的来源。

## 接入 AI

打开系统设置中的 AI 配置，填写服务商的 API Key、Base URL 和当前可用模型名称，并测试连接。

- DeepSeek：`https://api.deepseek.com/v1`
- OpenAI：`https://api.openai.com/v1`
- Gemini 的 OpenAI 兼容接口：`https://generativelanguage.googleapis.com/v1beta/openai/`，需要实测所选模型的流式响应和工具调用兼容性。

这些配置使用 API Key；本仓库没有增加 ChatGPT 或 Gemini 订阅账号登录功能。密钥由原项目加密保存于本机 `data` 目录，不提交到 GitHub。调用远程 AI 时，相应持仓上下文或上传图片会发往所选模型服务商。

截图导入需要支持图片输入的模型，可与文字分析分别配置。未填写 API Key 时，持仓和净值等基础功能仍可使用。

## 接收源项目更新

1. 在 GitHub 切换到 `main`，执行 **Sync fork → Update branch**。
2. 在自己的仓库创建 PR，确认目标为 `H1xin/ZFundPilot`，**base: personal，compare: main**。检查差异，记录涉及的上游提交和迁移事项，再用 **Create a merge commit** 合并，以保留上游提交关系。
3. 停止本机服务，将整个 `data` 文件夹复制到仓库以外的位置备份。它包含数据库、AI 加密密钥、登录配置和构建历史。
4. 在本机项目目录执行以下命令，再按上文校验并安装产物，最后双击启动脚本。

```powershell
git switch personal
git fetch origin main
git pull --ff-only origin personal
& .\.venv\Scripts\python.exe -m pip install -e .
& .\.venv\Scripts\python.exe .\build-local.py
```

若工作区存在未提交修改，先保存自己的改动再拉取，不要强制覆盖。更新前阅读上游版本说明，特别留意数据库迁移。

`.gitignore` 已排除 `data/`、`.env`、`.venv/` 和前端构建产物。不要使用 `git add -f` 上传这些目录或文件。本地数据不随 Git 更新自动备份。

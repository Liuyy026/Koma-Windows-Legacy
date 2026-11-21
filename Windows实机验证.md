# Koma Windows Legacy 实机验证

在 Windows x64 上用 Python 3.12 和 CPU 版 OCR 做基础验收。有 NVIDIA GPU 时，再单独验证 CUDA。验收目标是在冷缓存下用 `samples\01.webp` 识别出 **5 个文字块**，获得 **5 条有效中文译文**，关闭并重开阅读器后可直接读取同一份缓存。

拆分时已在 Mac 上用 CPU 实际识别出 5 个文字块并确认再次处理跳过 OCR，另外通过 7 项 Python 回归及 1 项 PySide6 无界面回归。两种服务的自动检查使用模拟回复。Windows 批处理、依赖安装、实机渲染、真实翻译服务和 CUDA 需按下文验收。

## 1. 解压源码并准备 CPU 环境

若收到 ZIP，可用 `Get-FileHash -Algorithm SHA256 .\Koma-Windows-Legacy-source.zip` 与随附校验值比较。在资源管理器选择「全部解压缩」，保留 `windows`、`backend`、`samples` 和 `scripts` 的相对位置。下面的命令均从包含 [README.md](README.md) 的项目根目录执行。

先安装 64 位 Python 3.12，并确认 `py -3.12 --version` 可用。若本机只安装了 Python 解释器，可用该 `python.exe` 的完整路径替换下面的 `py -3.12`。

```powershell
py -3.12 -m venv .\windows\.venv
$komaPython = '.\windows\.venv\Scripts\python.exe'
& $komaPython -X utf8 -m pip install --index-url https://download.pytorch.org/whl/cpu torch==2.5.1 torchvision==0.20.1
& $komaPython -X utf8 -m pip install -r .\windows\requirements.lock
& $komaPython -X utf8 -m pip check
& $komaPython -X utf8 -c "import torch, cv2, PySide6; print(torch.__version__, 'CUDA:', torch.version.cuda, 'Qt:', PySide6.__version__); assert torch.version.cuda is None"
& '.\windows\启动Windows.bat' --check
$LASTEXITCODE
& $komaPython -B -X utf8 .\scripts\check_regressions.py --qt
```

预期 `pip check` 无依赖冲突，Torch 显示 `CUDA: None`，`--check` 返回 `0`，离线回归显示 `Ran 8 tests` 和 `OK`。只检查 Python 后端时可省去 `--qt`，预期执行 7 项。无需激活虚拟环境。在 Windows 上移动源码目录后，建议重新用本机 Python 创建虚拟环境。

启动器优先选择 `windows\.venv-cuda`。验证 CPU 时使用刚解压的目录，确认 `windows\.runtime\windows-launch.log` 中的 `selected Python` 指向 `windows\.venv\Scripts\python.exe`。

## 2. 下载 OCR 模型

首次准备需要联网。下面让准备脚本使用发布版固定的模型版本与 SHA-256，下载位置与旧版阅读器一致。

```powershell
$previousModelDir = $env:KOMA_MODEL_DIR
$env:KOMA_MODEL_DIR = Join-Path (Get-Location).Path '.models'
try {
    & $komaPython -X utf8 .\scripts\prepare_models.py
    if ($LASTEXITCODE -ne 0) { throw 'OCR 模型准备失败' }
} finally {
    $env:KOMA_MODEL_DIR = $previousModelDir
}
Test-Path .\.models\manga-ocr\pytorch_model.bin
Test-Path .\.models\comictextdetector.pt
```

预期脚本显示「OCR 模型已下载，可离线运行」，两个 `Test-Path` 均为 `True`。阅读器从项目根目录的 `.models` 读取 OCR 权重。若沿用该旧版后端的提示遇到「安装.command」，应执行本节的 PowerShell 命令。

## 3. 准备翻译服务并获取模型

### 默认使用本机 Ollama

安装 [Windows 版 Ollama](https://ollama.com/download/windows)。首次下载模型时，建议从项目根目录另开一个 PowerShell 窗口，明确启动项目使用的服务端口及模型目录。保留这个窗口运行。若 `11439` 已被占用，先确认监听进程是否为所需 Ollama、是否使用了预期模型目录；已有正确服务可直接使用。

```powershell
$komaOllama = (Get-Command ollama.exe -ErrorAction SilentlyContinue).Source
if (-not $komaOllama) { $komaOllama = Join-Path $env:LOCALAPPDATA 'Programs\Ollama\ollama.exe' }
$env:OLLAMA_HOST = '127.0.0.1:11439'
$env:OLLAMA_NO_CLOUD = '1'
$env:OLLAMA_MODELS = Join-Path (Get-Location).Path '.models\ollama'
New-Item -ItemType Directory -Force -Path $env:OLLAMA_MODELS | Out-Null
& $komaOllama serve
```

回到第一个 PowerShell 窗口执行。两个窗口都用 `11439`，以便模型进入项目实际连接的服务。

```powershell
$komaOllama = (Get-Command ollama.exe -ErrorAction SilentlyContinue).Source
if (-not $komaOllama) { $komaOllama = Join-Path $env:LOCALAPPDATA 'Programs\Ollama\ollama.exe' }
$env:OLLAMA_HOST = '127.0.0.1:11439'
& $komaOllama pull qwen3:4b-q6k
& $komaOllama list
& $komaPython -X utf8 .\backend\worker.py --provider ollama --base-url http://127.0.0.1:11439 --list-models
```

预期 `ollama list` 和后端 `models` 均含 `qwen3:4b-q6k`。日常启动时，若保存的是默认 Ollama 地址、`11439` 尚无监听、并能找到 Ollama 程序，启动器会尝试启动服务。已有模型仓库可按 [Windows 阅读器说明](windows/README.md) 复用。

### 在界面确认服务

双击 [启动Windows.bat](windows/启动Windows.bat)。点击「服务设置…」，选择提供方，填写地址，在需要时输入 API Key。点击「测试连接并获取模型」，选中要使用的模型，再点「保存」。

| 提供方 | 地址和模型 |
| --- | --- |
| Ollama | 基础验收用 `http://127.0.0.1:11439` 和 `qwen3:4b-q6k`。如要连接已运行的另一实例，填写该实例的实际地址。 |
| oMLX | 连接已启动且 Windows 可访问的服务，填写形如 `http://<服务主机>:8000/v1` 的地址。`127.0.0.1` 表示本机。选择该服务返回的模型 ID，模型需支持结构化文本输出。 |

服务地址和模型会保存。API Key 随应用关闭而清除。更换提供方、地址或模型后，再点「识别并翻译」会按新配置更新机器译文，并保留已有缓存里标记为手改的译文。

## 4. 验收样页与缓存

1. 先确认缓存中无 `01.webp` 的结果。如果以前处理过这张样页，先关闭阅读器，把下述命令查到的对应 JSON 移至安全位置备份。缓存按图片内容哈希定位，复制或改名同一张图仍会命中原缓存。

   ```powershell
   $sampleHash = (Get-FileHash -Algorithm SHA256 .\samples\01.webp).Hash.ToLowerInvariant()
   $pageCache = Join-Path $env:LOCALAPPDATA "KomaReader\pages\$sampleHash.json"
   $pageCache
   Test-Path -LiteralPath $pageCache
   ```

2. 打开阅读器，点「打开文件夹」选取本项目的 `samples`，选中 `01.webp`。点击「识别并翻译」，观察模型加载、OCR 和翻译进度。完成后确认右侧显示 **5 处文字**、**5 处已翻译**，逐条检查有日文和有效中文。切换「原图」「文字框」「中文」查看显示。如果个别区域标记为「暂不覆盖」，在右侧核对译文及原因。

3. 检查页面缓存及内容。预期 `OCR` 和 `Translated` 均为 `5`。记录最后写入时间与 SHA-256。

   ```powershell
   $cached = Get-Content -LiteralPath $pageCache -Raw -Encoding UTF8 | ConvertFrom-Json
   $valid = @($cached.blocks | Where-Object { $_.translation -and -not $_.error -and $_.translation -ne $_.source })
   [pscustomobject]@{ OCR = @($cached.blocks).Count; Translated = $valid.Count; Model = $cached.model }
   Get-Item -LiteralPath $pageCache | Select-Object LastWriteTimeUtc
   Get-FileHash -LiteralPath $pageCache -Algorithm SHA256
   ```

4. 关闭阅读器并重开，重新打开 `samples`。在不点击「识别并翻译」的情况下，右侧应直接出现同样 5 条结果。再次检查最后写入时间和 SHA-256，与上一步一致即确认界面读取了原有缓存。若备份过原缓存，可在关闭阅读器后先移走此次验收生成的 JSON，再把原缓存移回原位。

## 5. 可选的 NVIDIA CUDA 验收

基础验收完成后，用支持 CUDA 12.8 的 NVIDIA 驱动和第二个虚拟环境验证 Manga OCR 日文识别加速。Comic Text Detector 仍由现有 Mokuro 流程在 CPU 上运行，Ollama 的设备选择由 Ollama 单独管理。

```powershell
py -3.12 -m venv .\windows\.venv-cuda
$komaCudaPython = '.\windows\.venv-cuda\Scripts\python.exe'
& $komaCudaPython -X utf8 -m pip install --index-url https://download.pytorch.org/whl/cu128 torch==2.7.1 torchvision==0.22.1
& $komaCudaPython -X utf8 -m pip install -r .\windows\requirements-cuda.txt PySide6==6.9.2 setuptools==80.10.2
& $komaCudaPython -X utf8 -m pip check
& $komaCudaPython -X utf8 -c "import torch; print(torch.__version__, torch.version.cuda); assert torch.cuda.is_available(); print(torch.cuda.get_device_name(0)); print(torch.tensor([1.0], device='cuda').item())"
& '.\windows\启动Windows.bat' --check
Get-Content .\windows\.runtime\windows-launch.log -Tail 30 -Encoding UTF8
```

预期显示 `2.7.1+cu128`、NVIDIA GPU 名称和 `1.0`，启动日志选中 `.venv-cuda`。按第 4 节备份当前样页缓存后再跑一轮，确认真正触发识别。若要看到 Manga OCR 的 `Using CUDA` 诊断，可在清空本次样页缓存的条件下，用 CUDA 环境直接运行第 6 节的 worker 命令并读取 stderr 日志。若 CUDA 未通过，可通过 CPU 虚拟环境直接启动 `windows\windows_app.py` 并手动保持所需翻译服务运行。

## 6. 失败定位与记录

| 现象 | 检查位置 |
| --- | --- |
| 双击没窗口或解释器选错 | 运行启动器 `--check`，查看 `windows\.runtime\windows-launch.log` 的 Python 路径及 PySide6 错误，确认没有另一窗口正在运行。日志每次运行都会重写。 |
| OCR 失败或缺少模型 | 检查 `.models` 的两个权重文件和第 2 节下载输出。必要时先用界面的「只识别 OCR」区分 OCR 与翻译故障。 |
| 模型列表为空、连接失败或 401/403 | 核对服务状态、地址、端口、模型 ID 和 Key。Ollama 确认 `ollama list` 使用的是 `11439` 实例。 |
| 状态显示「完成」，但译文少于五条 | 读取右侧每块的失败原因和页面 JSON 的 `blocks[].error`。检查占位输出、原样返回日文、结构化回复失败和模型超时。 |
| 想分辨缓存与真实 OCR | 核对按样页哈希定位的 JSON 和最后写入时间。需要冷跑时只备份该文件。 |

可用命令行重现本地 Ollama 流程并保留进度、错误。若是 OCR 问题，用 `--operation ocr`。验证 CUDA 时将 `$komaPython` 换为 `$komaCudaPython`。

```powershell
New-Item -ItemType Directory -Force .\windows\.runtime | Out-Null
& $komaPython -X utf8 .\backend\worker.py --image .\samples\01.webp --operation both --provider ollama --base-url http://127.0.0.1:11439 --model qwen3:4b-q6k --status .\windows\.runtime\cli-status.json 2> .\windows\.runtime\cli-worker-stderr.log
$LASTEXITCODE
Get-Content .\windows\.runtime\cli-status.json -Encoding UTF8
Get-Content .\windows\.runtime\cli-worker-stderr.log -Tail 40
```

```text
Windows 版本 / 架构：
Python 版本 / 启动器选中的解释器：
CPU 或 GPU 与驱动：
翻译服务 / 地址端口 / 模型：
01.webp 冷跑的 OCR 块数 / 有效译文数：
重开缓存结果 / SHA-256 是否一致：
失败步骤 / 完整报错 / 日志文件：
```

分享记录时可隐去 API Key、个人路径和漫画内容。旧版界面支持单页 OCR、普通文本翻译以及可信区域的中文覆盖。对白区只读，暂无界面编辑、单句重译、文件夹队列和视觉辅助翻译。此样页验收覆盖识别、连接、翻译和缓存流程，译文语义与实际覆盖效果仍须逐页查看。

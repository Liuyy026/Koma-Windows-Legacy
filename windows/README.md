# Windows 阅读器

[项目首页](../README.md) · [English](README.en.md)

[Windows 实机验证](../Windows实机验证.md)涵盖全新 CPU 环境、可选 CUDA、模型准备、服务选择、样页冷跑和缓存复用。命令均从项目根目录执行。首次准备完成后，双击本目录的 [启动Windows.bat](启动Windows.bat)。

启动器按 `.venv-cuda`、`.venv` 的顺序选择第一个能加载 PySide6 的解释器，识别子进程沿用该解释器。`--check` 只检查环境。启动日志为 `windows\.runtime\windows-launch.log`，页面缓存为 `%LOCALAPPDATA%\KomaReader\pages\`。

若已将整个 Ollama 模型仓库集中放在其他位置，可在启动器继承的环境中设置 `KOMA_OLLAMA_MODELS`，指向同时包含 `blobs` 和 `manifests` 的目录。随附的 [Ollama 模型仓库迁移脚本](scripts/migrate_ollama_models.ps1)可预览将项目模型仓库移到用户默认位置的计划。现有模型正常使用时可保留原位。

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\windows\scripts\migrate_ollama_models.ps1
```

实际迁移前先退出阅读器和 Ollama，确认源目录与目标路径，且目标没有模型数据，再运行同一命令并添加 `-Apply`。成功后脚本会在原位置创建 Windows 目录联接。模型缓存文件与清单应一起迁移。

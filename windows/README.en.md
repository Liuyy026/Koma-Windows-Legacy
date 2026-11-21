# Windows reader

[Project overview](../README.en.md) · [简体中文](README.md)

The [Windows verification guide](../Windows实机验证.md) covers a fresh CPU setup, optional CUDA, model downloads, service selection, a cold sample run, and cache reuse. Run its commands from the project root. After setup, double-click [启动Windows.bat](启动Windows.bat) here.

The launcher checks `.venv-cuda` first, followed by `.venv`, and selects the first Python environment that imports PySide6. The OCR process uses that interpreter. `--check` validates the environment without opening the reader. Find startup logs in `windows\.runtime\windows-launch.log` and page caches in `%LOCALAPPDATA%\KomaReader\pages\`.

Set `KOMA_OLLAMA_MODELS` in the launcher's environment to reuse a model store that already contains both `blobs` and `manifests`. The included [migration script](scripts/migrate_ollama_models.ps1) can preview moving the project model store to the user's default Ollama location.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\windows\scripts\migrate_ollama_models.ps1
```

To apply the migration, close the reader and Ollama, confirm the paths and that the target contains no model data, then add `-Apply` to the same command. The script creates a Windows directory junction at the source path when it succeeds.

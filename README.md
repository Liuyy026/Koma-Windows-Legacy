# Koma Windows Legacy

简体中文 · [English](README.en.md)

**旧版源码，按需维护。** 此次拆分后的 Windows 实机启动、翻译和 CUDA 验证待完成。[Windows 实机验证步骤](Windows实机验证.md) · [Mac 主项目与下载](https://github.com/Liuyy026/screen-capture-translator-public)

Koma 的独立 Windows 阅读器源码。打开本地日文漫画文件夹，用 Mokuro 和 Manga OCR 识别文字，通过 Ollama 或 oMLX 翻成简体中文，在右侧查看对照，也可在可信区域切换中文覆盖。

第一次使用请按 [Windows 实机验证](Windows实机验证.md) 安装 Python 依赖和模型。环境就绪后，双击 [启动Windows.bat](windows/启动Windows.bat)，打开 `samples` 文件夹，选中 `01.webp`，点击「识别并翻译」。翻译后的样页预期为 5 个文字块和 5 条有效译文。页面缓存位于 `%LOCALAPPDATA%\KomaReader\pages\`。

| 路径 | 用途 |
| --- | --- |
| [`windows/`](windows/) | PySide6 阅读器、批处理启动器、CPU 与 CUDA 依赖 |
| [`backend/`](backend/) | 单页识别、翻译服务客户端、分镜、对白和覆盖区域 |
| [`samples/`](samples/) | 两张上游已有样页 |
| [`scripts/prepare_models.py`](scripts/prepare_models.py) | 下载 OCR 模型 |
| [`scripts/check_regressions.py`](scripts/check_regressions.py) | 离线回归入口，支持 `--qt` 验证界面读取缓存 |

此版本从原公开仓库提交 `cfb1f6d593e1dd074f92123b4e581c332a64258a` 拆出，保留 Windows 阅读器、Python 后端和样页。源码需要在 Windows 上安装 Python 依赖及模型后运行。右侧对照区为只读，普通文本翻译逐页执行。

依赖及模型各自遵循上游许可。 [Mokuro](https://github.com/kha-white/mokuro) · [Manga OCR](https://github.com/kha-white/manga-ocr) · [Comic Text Detector](https://github.com/dmMaze/comic-text-detector) · [Qt for Python](https://www.qt.io/qt-for-python) · [Ollama](https://github.com/ollama/ollama)

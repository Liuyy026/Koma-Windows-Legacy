# Koma Windows Legacy

[简体中文](README.md) · English

Koma is a standalone Windows reader for local Japanese manga. It recognizes text with Mokuro and Manga OCR, translates it into Simplified Chinese through Ollama or an oMLX endpoint, and displays the original text and translation side by side. Chinese text can be overlaid where the reader finds a suitable region.

Follow the [Windows verification guide](Windows实机验证.md) for a fresh install, including Python, OCR weights, Ollama, and optional NVIDIA CUDA. Once set up, open [启动Windows.bat](windows/启动Windows.bat), select the `samples` folder, choose `01.webp`, and click **识别并翻译** (Recognize and translate). The sample baseline is five OCR blocks with five valid translations. Page caches live at `%LOCALAPPDATA%\KomaReader\pages\`.

| Path | Purpose |
| --- | --- |
| [`windows/`](windows/) | PySide6 reader, launcher, and CPU/CUDA requirements |
| [`backend/`](backend/) | Page worker, service client, dialogue structure, and overlay geometry |
| [`samples/`](samples/) | Two upstream sample pages |
| [`scripts/`](scripts/) | Model setup and offline regression checks |

The Windows source was split from upstream commit `cfb1f6d593e1dd074f92123b4e581c332a64258a`. The source distribution requires a Windows Python environment and model downloads. The result pane is read-only and the text workflow processes one page at a time.

Dependencies and models follow their upstream licenses. [Mokuro](https://github.com/kha-white/mokuro) · [Manga OCR](https://github.com/kha-white/manga-ocr) · [Comic Text Detector](https://github.com/dmMaze/comic-text-detector) · [Qt for Python](https://www.qt.io/qt-for-python) · [Ollama](https://github.com/ollama/ollama)

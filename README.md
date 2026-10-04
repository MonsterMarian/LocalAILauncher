# Local AI Launcher

Desktop controller for running local GGUF models via llama-server with multi-instance support and automatic IDE configuration for MiniMax Code and OpenCode.

<p align="center">
  <img src="app_icon.ico" alt="Local AI Launcher" width="128" />
</p>

## Overview

Local AI Launcher manages local LLM runtimes on Windows. It allows running models individually or concurrently across separate ports, monitors GPU VRAM and RAM in real time, and auto-generates configurations for developer IDEs.

## Features

- Multi-model concurrency: Run instances on dedicated ports (8080, 8081, 8082).
- Hardware targeting: Toggle between CUDA GPU offload and CPU/RAM execution per model.
- Live telemetry: Real-time NVIDIA VRAM and system memory utilization meters.
- Direct downloads: Fetch missing GGUF weights directly from Hugging Face.
- IDE sync: Updates configuration files for MiniMax Code and OpenCode on launch.
- Web UI and API: Direct access to built-in web chat and OpenAI-compatible /v1 endpoints.

## Supported Presets

- Qwen 2.5 Coder 7B (Port 8082)
- Bonsai 2 27B Abliterated v2 (Port 8080)
- Bonsai 2 27B Base (Port 8081)

## Setup

```bash
git clone https://github.com/MonsterMarian/LocalAILauncher.git
cd LocalAILauncher
pip install -r requirements.txt
python app.py
```

### Build Executable

```bash
pyinstaller --noconfirm --onefile --windowed --icon "app_icon.ico" --collect-all customtkinter app.py
```

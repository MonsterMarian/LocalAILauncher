# ⚡ Local AI Launcher (HYPERCORE Local AI Studio)

Awwwards-winning, high-performance desktop orchestrator for running local AI models (GGUF via `llama-server`) with multi-model concurrency, real-time hardware telemetry, in-app model downloads, and 1-click IDE synchronization for **MiniMax Code** and **OpenCode**.

![Dark Obsidian UI](app_icon.ico)

---

## 🌟 Key Features

- **🏆 Awwwards-Class Dark Obsidian UI:**
  - Modern Bento Grid architecture with deep obsidian background and frosted accent borders.
  - Live hardware telemetry meters: real-time NVIDIA VRAM & System RAM gauges.
  - Glowing status pills (`● ONLINE`, `⏳ NAČÍTÁM`, `○ ZASTAVENO`, `○ NENÍ STAŽENO`).

- **⚡ Dual Concurrency & Exclusive Modes:**
  - **Single Instance Mode:** Dedicated 100% GPU offload for peak generation speeds.
  - **Dual Concurrent Mode:** Run multiple models simultaneously (e.g. Qwen Coder on Port 8082, Bonsai 2 on Port 8080/8081).
  - Target selector per model: `⚡ GPU (CUDA)` or `🖥️ CPU / RAM`.

- **📥 In-App Model Downloader:**
  - Automatically checks if model files exist on disk.
  - Direct 1-click downloads from Hugging Face with live progress indicator (MB / %).

- **🔌 Seamless IDE Synchronization:**
  - Automatically generates and synchronizes configuration files for:
    - **MiniMax Code** (`~/.minimax/config.yaml`)
    - **OpenCode** (`~/.config/opencode/opencode.jsonc`)
  - Enables instant tool calling, image attachments, and reasoning modes in IDEs.

- **🌐 Instant Web UI & OpenAI-Compatible API:**
  - Direct access to local browser chat interface per model.
  - Standard OpenAI-compatible `/v1/chat/completions` API endpoints with 1-click copy.

---

## 🤖 Supported Models

| Model | Port | Architecture | Best For |
| :--- | :---: | :--- | :--- |
| **Qwen 2.5 Coder 7B (Instruct)** | `:8082` | Q4_K_M (~4.7 GB) | Code generation, structured JSON, tool-calling, logic decisions |
| **Bonsai 2 27B (Abliterated v2)** | `:8080` | Ternary PQ2_0 (~7.2 GB) | Unrestricted deep reasoning, multimodal vision support |
| **Bonsai 2 27B (Base Official)** | `:8081` | Ternary PQ2_0 (~7.2 GB) | High stability reference model, general knowledge |

---

## 🚀 Quick Start

### Prerequisites
- Windows 10/11 (64-bit)
- Python 3.10+ (for running from source)
- NVIDIA GPU with CUDA support (e.g. RTX 3060 Ti or higher recommended)

### Running from Source
```bash
git clone https://github.com/MonsterMarian/LocalAILauncher.git
cd LocalAILauncher
pip install -r requirements.txt
python app.py
```

### Building Standalone Executable
```bash
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --icon "app_icon.ico" --collect-all customtkinter app.py
```
The output `.exe` will be generated in `dist/app.exe`.

---

## 🔒 Privacy & Local Security
- 100% local inference: no telemetry, prompts, or code leaves your workstation.
- Fully compatible with offline environments.

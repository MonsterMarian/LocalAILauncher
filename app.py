import os
import sys
import time
import json
import yaml
import psutil
import urllib.request
import threading
import subprocess
import webbrowser
import customtkinter as ctk
from tkinter import messagebox

# Set dark theme appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Constants & Dynamic Paths (No personal usernames hardcoded)
USER_HOME = os.path.expanduser("~")
DEFAULT_REPOS = os.path.join(USER_HOME, "Desktop", "REPOS")
APP_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(APP_DIR, "models")

BONSAI_DEMO_DIR = os.environ.get("BONSAI_DEMO_DIR", os.path.join(DEFAULT_REPOS, "Bonsai-demo"))
LLAMA_SERVER_EXE = os.path.join(BONSAI_DEMO_DIR, r"bin\cuda\llama-server.exe")
MMPROJ_PATH = os.path.join(BONSAI_DEMO_DIR, r"models\bonsai2-gguf\27B\Ternary-Bonsai-2-27B-mmproj-Q8_0.gguf")

MINIMAX_CONFIG_PATH = os.path.expandvars(r"%USERPROFILE%\.minimax\config.yaml")
OPENCODE_CONFIG_PATH = os.path.expandvars(r"%USERPROFILE%\.config\opencode\opencode.jsonc")

MODEL_CONFIGS = {
    "qwen_coder": {
        "key": "qwen_coder",
        "name": "Qwen 2.5 Coder 7B (Instruct)",
        "short_name": "Qwen Coder 7B",
        "badge": "💻 TOP CODE & LOGIC",
        "badge_color": "#10B981",
        "badge_bg": "#064E3B",
        "port": 8082,
        "path": os.path.join(MODELS_DIR, "qwen2.5-coder-7b-instruct-q4_k_m.gguf"),
        "download_url": "https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct-GGUF/resolve/main/qwen2.5-coder-7b-instruct-q4_k_m.gguf",
        "download_size_gb": 4.7,
        "description": "Špičkový model pod 8 GB na kód a logické rozhodování od Alibaby. Perfektní na Python, JSON schémata a blesková rychlost na RTX 3060 Ti.",
        "ide_model_id": "qwen-2.5-coder-7b",
        "default_target": "GPU"
    },
    "abliterated": {
        "key": "abliterated",
        "name": "Bonsai 2 27B (Craknutý / Abliterated v2)",
        "short_name": "Craknutý v2",
        "badge": "🔓 UNRESTRICTED CORE",
        "badge_color": "#8B5CF6",
        "badge_bg": "#3B1A66",
        "port": 8080,
        "path": os.path.join(BONSAI_DEMO_DIR, r"models\bonsai2-gguf\27B\Ternary-Bonsai-2-27B-Abliterated-v2-PQ2_0.gguf"),
        "download_url": "https://huggingface.co/BoldingBuilds/Ternary-Bonsai-2-27B-Abliterated-v2-PQ2_0-MTP-GGUF/resolve/main/Ternary-Bonsai-2-27B-Abliterated-v2-PQ2_0.gguf",
        "download_size_gb": 7.2,
        "description": "Necenzurovaná verze v2 od PrismML. Plný reasoning, maximální inteligence a bez umělých filtrů.",
        "ide_model_id": "bonsai-2-27b-abliterated",
        "default_target": "GPU"
    },
    "original": {
        "key": "original",
        "name": "Bonsai 2 27B (Originální / Base)",
        "short_name": "Originální Base",
        "badge": "🔒 BASE OFFICIAL",
        "badge_color": "#06B6D4",
        "badge_bg": "#0E3A4B",
        "port": 8081,
        "path": os.path.join(BONSAI_DEMO_DIR, r"models\bonsai2-gguf\27B\Ternary-Bonsai-2-27B-PQ2_0.gguf"),
        "download_url": "https://huggingface.co/prism-ml/Ternary-Bonsai-2-27B-gguf/resolve/main/Ternary-Bonsai-2-27B-PQ2_0.gguf",
        "download_size_gb": 7.2,
        "description": "Původní referenční model od PrismML. Maximální stabilita pro obecné úlohy a kódování.",
        "ide_model_id": "bonsai-2-27b",
        "default_target": "CPU"
    }
}


class AwwwardsTheme:
    BG_ROOT = "#07090E"
    CARD_BG = "#0D111A"
    CARD_BORDER = "#1B2436"
    CARD_HOVER = "#131926"
    SURFACE_SUBTLE = "#111724"
    SURFACE_INPUT = "#0A0E17"
    
    TEXT_MAIN = "#F8FAFC"
    TEXT_MUTED = "#94A3B8"
    TEXT_DIM = "#64748B"
    
    ACCENT_EMERALD = "#10B981"
    ACCENT_EMERALD_HOVER = "#059669"
    ACCENT_EMERALD_BG = "#064E3B"
    
    ACCENT_CRIMSON = "#EF4444"
    ACCENT_CRIMSON_HOVER = "#DC2626"
    ACCENT_CRIMSON_BG = "#7F1D1D"
    
    ACCENT_CYAN = "#06B6D4"
    ACCENT_VIOLET = "#8B5CF6"
    ACCENT_AMBER = "#F59E0B"
    ACCENT_BLUE = "#3B82F6"
    ACCENT_BLUE_HOVER = "#2563EB"


class LocalAILauncherApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("⚡ HYPERCORE // Local AI Studio")
        self.geometry("860x930")
        self.minsize(780, 800)
        self.configure(fg_color=AwwwardsTheme.BG_ROOT)

        icon_path = os.path.join(os.path.dirname(__file__), "app_icon.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        # Execution State
        self.mode_var = ctk.StringVar(value="single")  # "single" (GPU priority) or "dual" (both at once)
        self.instances = {
            "qwen_coder": {
                "config": MODEL_CONFIGS["qwen_coder"],
                "process": None,
                "is_running": False,
                "is_starting": False,
                "target_var": ctk.StringVar(value="GPU"),
                "ctx_var": ctk.StringVar(value="8192"),
                "ui": {}
            },
            "abliterated": {
                "config": MODEL_CONFIGS["abliterated"],
                "process": None,
                "is_running": False,
                "is_starting": False,
                "target_var": ctk.StringVar(value="GPU"),
                "ctx_var": ctk.StringVar(value="8192"),
                "ui": {}
            },
            "original": {
                "config": MODEL_CONFIGS["original"],
                "process": None,
                "is_running": False,
                "is_starting": False,
                "target_var": ctk.StringVar(value="CPU"),
                "ctx_var": ctk.StringVar(value="8192"),
                "ui": {}
            }
        }

        self.build_ui()
        self.check_initial_ports()
        self.start_monitoring()

    def build_ui(self):
        # Top Brand & Telemetry Header
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=24, pady=(18, 10))

        # Brand row
        self.brand_row = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.brand_row.pack(fill="x")

        self.logo_box = ctk.CTkFrame(self.brand_row, fg_color=AwwwardsTheme.SURFACE_SUBTLE, corner_radius=8, width=38, height=38)
        self.logo_box.pack(side="left", padx=(0, 12))
        self.logo_box.pack_propagate(False)

        self.logo_text = ctk.CTkLabel(
            self.logo_box,
            text="◈",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=AwwwardsTheme.ACCENT_CYAN
        )
        self.logo_text.place(relx=0.5, rely=0.5, anchor="center")

        self.title_box = ctk.CTkFrame(self.brand_row, fg_color="transparent")
        self.title_box.pack(side="left")

        self.title_label = ctk.CTkLabel(
            self.title_box,
            text="HYPERCORE LOCAL AI STUDIO",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=AwwwardsTheme.TEXT_MAIN
        )
        self.title_label.pack(anchor="w")

        self.subtitle_label = ctk.CTkLabel(
            self.title_box,
            text="Awwwards-Class High Performance Model Runtime & Orchestrator",
            font=ctk.CTkFont(size=11),
            text_color=AwwwardsTheme.TEXT_MUTED
        )
        self.subtitle_label.pack(anchor="w")

        # Global Quick Actions in Top-Right
        self.global_actions = ctk.CTkFrame(self.brand_row, fg_color="transparent")
        self.global_actions.pack(side="right")

        self.launch_both_btn = ctk.CTkButton(
            self.global_actions,
            text="🚀 Spustit oba naráz",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#4F46E5",
            hover_color="#4338CA",
            height=32,
            corner_radius=8,
            command=self.start_both_models
        )
        self.launch_both_btn.pack(side="left", padx=(0, 8))

        self.stop_all_btn = ctk.CTkButton(
            self.global_actions,
            text="⏹ Zastavit vše",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=AwwwardsTheme.ACCENT_CRIMSON,
            hover_color=AwwwardsTheme.ACCENT_CRIMSON_HOVER,
            height=32,
            corner_radius=8,
            command=self.stop_all_models
        )
        self.stop_all_btn.pack(side="left")

        # Telemetry Bento Strip (Live Metrics)
        self.telemetry_strip = ctk.CTkFrame(
            self.header_frame,
            fg_color=AwwwardsTheme.CARD_BG,
            border_color=AwwwardsTheme.CARD_BORDER,
            border_width=1,
            corner_radius=12
        )
        self.telemetry_strip.pack(fill="x", pady=(12, 0))

        self.telemetry_grid = ctk.CTkFrame(self.telemetry_strip, fg_color="transparent")
        self.telemetry_grid.pack(fill="x", padx=16, pady=10)

        # 1. GPU VRAM Metric
        self.metric_gpu_box = ctk.CTkFrame(self.telemetry_grid, fg_color="transparent")
        self.metric_gpu_box.pack(side="left", fill="x", expand=True)

        self.gpu_title_row = ctk.CTkFrame(self.metric_gpu_box, fg_color="transparent")
        self.gpu_title_row.pack(fill="x")

        self.gpu_metric_title = ctk.CTkLabel(
            self.gpu_title_row,
            text="RTX 3060 Ti VRAM",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=AwwwardsTheme.TEXT_MUTED
        )
        self.gpu_metric_title.pack(side="left")

        self.gpu_metric_val = ctk.CTkLabel(
            self.gpu_title_row,
            text="-- / 8.0 GB",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=AwwwardsTheme.ACCENT_CYAN
        )
        self.gpu_metric_val.pack(side="right")

        self.gpu_progress = ctk.CTkProgressBar(
            self.metric_gpu_box,
            height=6,
            corner_radius=3,
            fg_color="#1E293B",
            progress_color=AwwwardsTheme.ACCENT_CYAN
        )
        self.gpu_progress.pack(fill="x", pady=(5, 0))
        self.gpu_progress.set(0.0)

        # Separator
        self.sep1 = ctk.CTkFrame(self.telemetry_grid, width=1, height=30, fg_color=AwwwardsTheme.CARD_BORDER)
        self.sep1.pack(side="left", padx=14)

        # 2. System RAM Metric
        self.metric_ram_box = ctk.CTkFrame(self.telemetry_grid, fg_color="transparent")
        self.metric_ram_box.pack(side="left", fill="x", expand=True)

        self.ram_title_row = ctk.CTkFrame(self.metric_ram_box, fg_color="transparent")
        self.ram_title_row.pack(fill="x")

        self.ram_metric_title = ctk.CTkLabel(
            self.ram_title_row,
            text="SYSTÉMOVÁ RAM (32 GB)",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=AwwwardsTheme.TEXT_MUTED
        )
        self.ram_metric_title.pack(side="left")

        self.ram_metric_val = ctk.CTkLabel(
            self.ram_title_row,
            text="-- / 32 GB",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=AwwwardsTheme.ACCENT_VIOLET
        )
        self.ram_metric_val.pack(side="right")

        self.ram_progress = ctk.CTkProgressBar(
            self.metric_ram_box,
            height=6,
            corner_radius=3,
            fg_color="#1E293B",
            progress_color=AwwwardsTheme.ACCENT_VIOLET
        )
        self.ram_progress.pack(fill="x", pady=(5, 0))
        self.ram_progress.set(0.0)

        # Separator
        self.sep2 = ctk.CTkFrame(self.telemetry_grid, width=1, height=30, fg_color=AwwwardsTheme.CARD_BORDER)
        self.sep2.pack(side="left", padx=14)

        # 3. Active Server Engines
        self.metric_srv_box = ctk.CTkFrame(self.telemetry_grid, fg_color="transparent")
        self.metric_srv_box.pack(side="left", fill="x", expand=True)

        self.srv_title_row = ctk.CTkFrame(self.metric_srv_box, fg_color="transparent")
        self.srv_title_row.pack(fill="x")

        self.srv_metric_title = ctk.CTkLabel(
            self.srv_title_row,
            text="AKTIVNÍ SERVERY",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=AwwwardsTheme.TEXT_MUTED
        )
        self.srv_metric_title.pack(side="left")

        self.srv_metric_val = ctk.CTkLabel(
            self.srv_title_row,
            text="0 / 3 BĚŽÍ",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=AwwwardsTheme.TEXT_DIM
        )
        self.srv_metric_val.pack(side="right")

        self.srv_ports_label = ctk.CTkLabel(
            self.metric_srv_box,
            text="Porty :8082 (Qwen Coder) | :8080 (Bonsai v2) | :8081 (Base)",
            font=ctk.CTkFont(family="Consolas", size=10),
            text_color=AwwwardsTheme.TEXT_DIM,
            anchor="w"
        )
        self.srv_ports_label.pack(fill="x", pady=(4, 0))

        # Main Scrollable Body
        self.scroll_frame = ctk.CTkScrollableFrame(
            self,
            corner_radius=12,
            fg_color="transparent",
            scrollbar_button_color="#1E293B",
            scrollbar_button_hover_color="#334155"
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=24, pady=(6, 14))

        # Concurrency Mode Switcher Banner
        self.build_concurrency_banner()

        # Model Engine Cards (Card 1: Qwen Coder, Card 2: Craknutý, Card 3: Originální)
        self.build_model_card("qwen_coder")
        self.build_model_card("abliterated")
        self.build_model_card("original")

        # IDE Integration Bento Card (MiniMax Code & OpenCode)
        self.build_ide_hub()

        # Live Telemetry Console
        self.build_console_hub()

    def build_concurrency_banner(self):
        self.concurrency_card = ctk.CTkFrame(
            self.scroll_frame,
            corner_radius=12,
            fg_color=AwwwardsTheme.CARD_BG,
            border_color=AwwwardsTheme.CARD_BORDER,
            border_width=1
        )
        self.concurrency_card.pack(fill="x", pady=(0, 12))

        inner = ctk.CTkFrame(self.concurrency_card, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=10)

        left_part = ctk.CTkFrame(inner, fg_color="transparent")
        left_part.pack(side="left", fill="x", expand=True)

        mode_header = ctk.CTkLabel(
            left_part,
            text="⚙️ REŽIM SOUBĚŽNÉHO BĚHU (CONCURRENCY)",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=AwwwardsTheme.TEXT_MAIN
        )
        mode_header.pack(anchor="w")

        self.concurrency_desc = ctk.CTkLabel(
            left_part,
            text="Jednotlivý režim (Single) šetří 8 GB VRAM pro plný výkon GPU. V souběžném režimu (Dual) běží oba modely naráz na portech 8080 a 8081.",
            font=ctk.CTkFont(size=11),
            text_color=AwwwardsTheme.TEXT_MUTED,
            anchor="w"
        )
        self.concurrency_desc.pack(anchor="w", pady=(2, 0))

        # Segmented Button for Mode
        self.mode_segmented = ctk.CTkSegmentedButton(
            inner,
            values=["⚡ Exkluzivní GPU (Jeden model)", "🔄 Souběžný běh (Oba naráz)"],
            font=ctk.CTkFont(size=11, weight="bold"),
            selected_color="#4F46E5",
            selected_hover_color="#4338CA",
            unselected_color="#182030",
            unselected_hover_color="#202A3F",
            height=32,
            command=self.on_mode_switched
        )
        self.mode_segmented.pack(side="right", padx=(10, 0))
        self.mode_segmented.set("⚡ Exkluzivní GPU (Jeden model)")

    def on_mode_switched(self, choice):
        if "Souběžný" in choice:
            self.mode_var.set("dual")
            self.concurrency_desc.configure(
                text="✅ Souběžný režim aktivní: Můžeš mít zapnuté oba modely naráz (Port 8080 + 8081). V MiniMax i OpenCode fungují oba současně!"
            )
        else:
            self.mode_var.set("single")
            self.concurrency_desc.configure(
                text="⚡ Exkluzivní GPU režim: Spuštěním jednoho modelu se druhý automaticky uvolní z GPU pro 100% rychlost."
            )

    def build_model_card(self, key):
        cfg = MODEL_CONFIGS[key]
        inst = self.instances[key]

        card = ctk.CTkFrame(
            self.scroll_frame,
            corner_radius=12,
            fg_color=AwwwardsTheme.CARD_BG,
            border_color=AwwwardsTheme.CARD_BORDER,
            border_width=1
        )
        card.pack(fill="x", pady=(0, 12))
        inst["ui"]["card"] = card

        # Top Bar of the Card
        top_bar = ctk.CTkFrame(card, fg_color="transparent")
        top_bar.pack(fill="x", padx=16, pady=(14, 6))

        # Title + Badge
        title_box = ctk.CTkFrame(top_bar, fg_color="transparent")
        title_box.pack(side="left")

        # Pill Badge
        badge_frame = ctk.CTkFrame(title_box, fg_color=cfg["badge_bg"], corner_radius=6)
        badge_frame.pack(side="left", padx=(0, 10))
        badge_lbl = ctk.CTkLabel(
            badge_frame,
            text=f" {cfg['badge']} ",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=cfg["badge_color"]
        )
        badge_lbl.pack(padx=6, pady=2)

        # Title
        card_title = ctk.CTkLabel(
            title_box,
            text=cfg["name"],
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=AwwwardsTheme.TEXT_MAIN
        )
        card_title.pack(side="left")

        # Status Pill Indicator
        status_pill = ctk.CTkFrame(top_bar, fg_color="#182030", corner_radius=12)
        status_pill.pack(side="right")
        inst["ui"]["status_pill"] = status_pill

        status_lbl = ctk.CTkLabel(
            status_pill,
            text=f"○ ZASTAVENO (Port :{cfg['port']})",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=AwwwardsTheme.TEXT_MUTED
        )
        status_lbl.pack(padx=12, pady=4)
        inst["ui"]["status_lbl"] = status_lbl

        # Description
        desc_lbl = ctk.CTkLabel(
            card,
            text=cfg["description"],
            font=ctk.CTkFont(size=11),
            text_color=AwwwardsTheme.TEXT_MUTED,
            justify="left",
            anchor="w"
        )
        desc_lbl.pack(fill="x", padx=16, pady=(0, 10))

        # Hardware & Parameters Options Row
        opts_box = ctk.CTkFrame(
            card,
            fg_color=AwwwardsTheme.SURFACE_SUBTLE,
            corner_radius=8
        )
        opts_box.pack(fill="x", padx=16, pady=(0, 12))

        opts_inner = ctk.CTkFrame(opts_box, fg_color="transparent")
        opts_inner.pack(fill="x", padx=12, pady=8)

        # Hardware Target
        target_lbl = ctk.CTkLabel(
            opts_inner,
            text="Hardware:",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=AwwwardsTheme.TEXT_MUTED
        )
        target_lbl.pack(side="left", padx=(0, 8))

        target_seg = ctk.CTkSegmentedButton(
            opts_inner,
            values=["⚡ GPU (RTX 3060 Ti)", "🖥️ CPU / RAM"],
            variable=inst["target_var"],
            font=ctk.CTkFont(size=11),
            selected_color="#2563EB",
            unselected_color="#182030",
            height=26
        )
        target_seg.pack(side="left", padx=(0, 18))
        target_seg.set("⚡ GPU (RTX 3060 Ti)" if cfg["default_target"] == "GPU" else "🖥️ CPU / RAM")

        # Context Window
        ctx_lbl = ctk.CTkLabel(
            opts_inner,
            text="Kontext:",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=AwwwardsTheme.TEXT_MUTED
        )
        ctx_lbl.pack(side="left", padx=(0, 8))

        ctx_seg = ctk.CTkSegmentedButton(
            opts_inner,
            values=["4K", "8K", "16K", "32K"],
            font=ctk.CTkFont(size=11),
            height=26,
            selected_color="#334155",
            unselected_color="#182030",
            command=lambda val, k=key: self.on_ctx_changed(k, val)
        )
        ctx_seg.pack(side="left")
        ctx_seg.set("8K")

        # Endpoints Box
        endpoint_lbl = ctk.CTkLabel(
            opts_inner,
            text=f"API: http://127.0.0.1:{cfg['port']}/v1",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=AwwwardsTheme.ACCENT_CYAN
        )
        endpoint_lbl.pack(side="right")

        # Action Buttons Row
        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(0, 14))

        # Main Start / Stop Button
        launch_btn = ctk.CTkButton(
            btn_row,
            text=f"▶ Spustit model ({cfg['short_name']})",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=AwwwardsTheme.ACCENT_EMERALD,
            hover_color=AwwwardsTheme.ACCENT_EMERALD_HOVER,
            height=38,
            corner_radius=8,
            command=lambda k=key: self.toggle_model(k)
        )
        launch_btn.pack(side="left", fill="x", expand=True, padx=(0, 10))
        inst["ui"]["launch_btn"] = launch_btn

        # Web Chat Button
        web_btn = ctk.CTkButton(
            btn_row,
            text="🌐 Otevřít Web Chat",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=AwwwardsTheme.ACCENT_BLUE,
            hover_color=AwwwardsTheme.ACCENT_BLUE_HOVER,
            height=38,
            corner_radius=8,
            command=lambda port=cfg['port']: self.open_browser_chat(port)
        )
        web_btn.pack(side="left", padx=(0, 10))

        # Copy API Button
        copy_btn = ctk.CTkButton(
            btn_row,
            text="📋 Kopírovat /v1",
            font=ctk.CTkFont(size=12),
            fg_color="#334155",
            hover_color="#475569",
            height=38,
            corner_radius=8,
            width=120,
            command=lambda port=cfg['port']: self.copy_api_url(port)
        )
        copy_btn.pack(side="left")

    def on_ctx_changed(self, key, val):
        mapping = {"4K": "4096", "8K": "8192", "16K": "16384", "32K": "32768"}
        self.instances[key]["ctx_var"].set(mapping.get(val, "8192"))

    def build_ide_hub(self):
        self.ide_card = ctk.CTkFrame(
            self.scroll_frame,
            corner_radius=12,
            fg_color=AwwwardsTheme.CARD_BG,
            border_color=AwwwardsTheme.CARD_BORDER,
            border_width=1
        )
        self.ide_card.pack(fill="x", pady=(0, 12))

        inner = ctk.CTkFrame(self.ide_card, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=12)

        # Header
        head_row = ctk.CTkFrame(inner, fg_color="transparent")
        head_row.pack(fill="x", pady=(0, 8))

        ide_title = ctk.CTkLabel(
            head_row,
            text="🔌 INTEGRACE DO VÝVOJOVÝCH PROSTŘEDÍ (IDE HUB)",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=AwwwardsTheme.TEXT_MAIN
        )
        ide_title.pack(side="left")

        sync_btn = ctk.CTkButton(
            head_row,
            text="⚡ Synchronizovat MiniMax & OpenCode",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#4F46E5",
            hover_color="#4338CA",
            height=28,
            corner_radius=6,
            command=self.sync_all_ides
        )
        sync_btn.pack(side="right")

        # Two columns: MiniMax Code & OpenCode
        cols_row = ctk.CTkFrame(inner, fg_color="transparent")
        cols_row.pack(fill="x")

        # MiniMax Code Box
        mm_box = ctk.CTkFrame(cols_row, fg_color=AwwwardsTheme.SURFACE_SUBTLE, corner_radius=8)
        mm_box.pack(side="left", fill="both", expand=True, padx=(0, 6))

        mm_inner = ctk.CTkFrame(mm_box, fg_color="transparent")
        mm_inner.pack(fill="x", padx=12, pady=10)

        mm_title = ctk.CTkLabel(
            mm_inner,
            text="🟣 MiniMax Code",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=AwwwardsTheme.TEXT_MAIN
        )
        mm_title.pack(anchor="w")

        mm_info = ctk.CTkLabel(
            mm_inner,
            text="Modely nastaveny:\n• qwen-2.5-coder-7b (:8082)\n• bonsai-2-27b-abliterated (:8080)\n• bonsai-2-27b (:8081)",
            font=ctk.CTkFont(size=11),
            text_color=AwwwardsTheme.TEXT_MUTED,
            justify="left",
            anchor="w"
        )
        mm_info.pack(anchor="w", pady=(4, 6))

        # OpenCode Box
        oc_box = ctk.CTkFrame(cols_row, fg_color=AwwwardsTheme.SURFACE_SUBTLE, corner_radius=8)
        oc_box.pack(side="left", fill="both", expand=True, padx=(6, 0))

        oc_inner = ctk.CTkFrame(oc_box, fg_color="transparent")
        oc_inner.pack(fill="x", padx=12, pady=10)

        oc_title = ctk.CTkLabel(
            oc_inner,
            text="🟢 OpenCode",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=AwwwardsTheme.TEXT_MAIN
        )
        oc_title.pack(anchor="w")

        oc_info = ctk.CTkLabel(
            oc_inner,
            text="Providery nastaveny:\n• qwen_coder (:8082)\n• bonsai_abliterated (:8080)\n• bonsai_original (:8081)",
            font=ctk.CTkFont(size=11),
            text_color=AwwwardsTheme.TEXT_MUTED,
            justify="left",
            anchor="w"
        )
        oc_info.pack(anchor="w", pady=(4, 6))

    def build_console_hub(self):
        self.console_card = ctk.CTkFrame(
            self.scroll_frame,
            corner_radius=12,
            fg_color=AwwwardsTheme.CARD_BG,
            border_color=AwwwardsTheme.CARD_BORDER,
            border_width=1
        )
        self.console_card.pack(fill="both", expand=True, pady=(0, 5))

        top_bar = ctk.CTkFrame(self.console_card, fg_color="transparent")
        top_bar.pack(fill="x", padx=16, pady=(10, 6))

        con_title = ctk.CTkLabel(
            top_bar,
            text="📟 ŽIVÁ TELEMETRIE A SYSTÉMOVÉ LOGY",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=AwwwardsTheme.TEXT_MAIN
        )
        con_title.pack(side="left")

        clear_btn = ctk.CTkButton(
            top_bar,
            text="Vyčistit konzoli",
            font=ctk.CTkFont(size=11),
            fg_color="#1E293B",
            hover_color="#334155",
            width=100,
            height=24,
            corner_radius=6,
            command=self.clear_logs
        )
        clear_btn.pack(side="right")

        self.log_textbox = ctk.CTkTextbox(
            self.console_card,
            height=160,
            font=ctk.CTkFont(family="Consolas", size=11),
            fg_color="#05070D",
            text_color="#CBD5E1",
            corner_radius=8,
            wrap="word"
        )
        self.log_textbox.pack(fill="both", expand=True, padx=16, pady=(0, 12))

    # --- Server Orchestration & Concurrency ---

    def toggle_model(self, key):
        inst = self.instances[key]
        if inst["is_running"]:
            self.stop_model(key)
        else:
            self.start_model(key)

    def start_model(self, key):
        inst = self.instances[key]
        cfg = inst["config"]

        # Check file existence
        if not os.path.exists(cfg["path"]):
            messagebox.showerror("Chyba", f"Soubor modelu nebyl nalezen:\n{cfg['path']}")
            return

        if not os.path.exists(LLAMA_SERVER_EXE):
            messagebox.showerror("Chyba", f"llama-server.exe nenalezen:\n{LLAMA_SERVER_EXE}")
            return

        # Check Concurrency Mode: if single mode, stop all other running instances first
        if self.mode_var.get() == "single":
            for other_key in self.instances:
                if other_key != key and self.instances[other_key]["is_running"]:
                    self.append_log(f"[CONCURRENCY] Exkluzivní režim: Zastavuji druhý model ({other_key})...\n")
                    self.stop_model(other_key)

        # Check if port is already occupied by old orphan
        self.terminate_port_process(cfg["port"])

        # Determine target device
        target = inst["target_var"].get()
        is_gpu = "GPU" in target
        ngl_val = "99" if is_gpu else "0"
        ctx_val = inst["ctx_var"].get()
        temp_val = "0.7" if "qwen" in key else "1.0"

        self.append_log(f"\n[ENGINE START] Spouštím {cfg['name']}\n")
        self.append_log(f"               Hardware: {target} (ngl={ngl_val}) | Port: {cfg['port']} | Ctx: {ctx_val}\n")

        args = [
            LLAMA_SERVER_EXE,
            "-m", cfg["path"],
            "--host", "127.0.0.1",
            "--port", str(cfg["port"]),
            "-ngl", ngl_val,
            "-fa", "on",
            "-c", ctx_val,
            "--temp", temp_val,
            "--top-p", "0.95",
            "--top-k", "20",
            "--jinja"
        ]

        if "bonsai" in cfg["path"].lower() and os.path.exists(MMPROJ_PATH):
            args.extend(["--mmproj", MMPROJ_PATH, "--no-mmproj-offload"])
            self.append_log("               Multimodální projektor (Vision): Aktivní v RAM\n")

        env = os.environ.copy()
        bin_dir = os.path.dirname(LLAMA_SERVER_EXE)
        env["PATH"] = f"{bin_dir};" + env.get("PATH", "")

        try:
            inst["is_starting"] = True
            self.update_card_ui(key)

            proc = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=env,
                text=True,
                bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            inst["process"] = proc
            inst["is_running"] = True

            threading.Thread(target=self._stream_instance_logs, args=(key, proc), daemon=True).start()
            threading.Thread(target=self._wait_for_port_ready, args=(key, cfg["port"]), daemon=True).start()

            # Automatically sync IDE configs so they are immediately connected
            self.sync_all_ides(silent=True)

        except Exception as e:
            inst["is_running"] = False
            inst["is_starting"] = False
            self.update_card_ui(key)
            self.append_log(f"[CHYBA] Selhalo spuštění {key}: {e}\n")
            messagebox.showerror("Chyba", str(e))

    def _stream_instance_logs(self, key, proc):
        tag = f"[{self.instances[key]['config']['short_name']}]"
        try:
            for line in iter(proc.stdout.readline, ''):
                if line:
                    self.after(0, self.append_log, f"{tag} {line}")
        except Exception:
            pass

    def _wait_for_port_ready(self, key, port):
        inst = self.instances[key]
        for _ in range(60):
            try:
                req = urllib.request.Request(f"http://127.0.0.1:{port}/health")
                with urllib.request.urlopen(req, timeout=1) as resp:
                    if resp.status == 200:
                        inst["is_starting"] = False
                        self.after(0, lambda: self.on_instance_ready(key))
                        return
            except Exception:
                time.sleep(1)
        inst["is_starting"] = False
        self.after(0, lambda: self.update_card_ui(key))

    def on_instance_ready(self, key):
        inst = self.instances[key]
        self.update_card_ui(key)
        self.append_log(f"[READY] Model {inst['config']['name']} je plně připraven na http://127.0.0.1:{inst['config']['port']}!\n")

    def stop_model(self, key):
        inst = self.instances[key]
        cfg = inst["config"]
        self.append_log(f"[ENGINE STOP] Zastavuji model {cfg['name']} (Port {cfg['port']})...\n")

        if inst["process"]:
            try:
                inst["process"].terminate()
                inst["process"].wait(timeout=2)
            except Exception:
                try:
                    inst["process"].kill()
                except Exception:
                    pass
            inst["process"] = None

        self.terminate_port_process(cfg["port"])

        inst["is_running"] = False
        inst["is_starting"] = False
        self.update_card_ui(key)
        self.append_log(f"[STOPPED] Model {cfg['name']} byl ukončen.\n")

    def start_both_models(self):
        self.mode_var.set("dual")
        self.mode_segmented.set("🔄 Souběžný běh (Oba naráz)")
        self.append_log("[CONCURRENCY] Spouštím souběžný běh obou modelů...\n")
        
        # Start abliterated on GPU, original on CPU (or per user selector)
        if not self.instances["abliterated"]["is_running"]:
            self.start_model("abliterated")
        if not self.instances["original"]["is_running"]:
            self.after(2000, lambda: self.start_model("original"))

    def stop_all_models(self):
        for key in self.instances:
            if self.instances[key]["is_running"]:
                self.stop_model(key)

    def terminate_port_process(self, port):
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'] and 'llama-server' in proc.info['name'].lower():
                    # Check connections of this process
                    for conn in proc.connections():
                        if conn.laddr and conn.laddr.port == port:
                            proc.terminate()
                            proc.wait(timeout=2)
                            break
            except Exception:
                pass

    def update_card_ui(self, key):
        inst = self.instances[key]
        cfg = inst["config"]
        ui = inst["ui"]

        # Check if currently downloading
        if inst.get("is_downloading", False):
            ui["status_pill"].configure(fg_color="#1E3A8A")
            ui["status_lbl"].configure(
                text=inst.get("download_status_text", f"⏳ STAHOVÁNÍ (Port :{cfg['port']})"),
                text_color="#60A5FA"
            )
            ui["launch_btn"].configure(
                text=inst.get("download_btn_text", "⏳ Stahuji..."),
                fg_color="#1E3A8A",
                hover_color="#1E3A8A",
                state="disabled"
            )
            ui["card"].configure(border_color="#3B82F6")
            return

        file_exists = os.path.exists(cfg["path"])

        if inst["is_running"]:
            if inst["is_starting"]:
                ui["status_pill"].configure(fg_color="#451A03")
                ui["status_lbl"].configure(
                    text=f"⏳ NAČÍTÁM DO PAMĚTI (Port :{cfg['port']})",
                    text_color=AwwwardsTheme.ACCENT_AMBER
                )
            else:
                ui["status_pill"].configure(fg_color=AwwwardsTheme.ACCENT_EMERALD_BG)
                ui["status_lbl"].configure(
                    text=f"● ONLINE (Port :{cfg['port']})",
                    text_color="#34D399"
                )
            ui["launch_btn"].configure(
                text=f"⏹ Zastavit model ({cfg['short_name']})",
                fg_color=AwwwardsTheme.ACCENT_CRIMSON,
                hover_color=AwwwardsTheme.ACCENT_CRIMSON_HOVER,
                state="normal",
                command=lambda k=key: self.toggle_model(k)
            )
            border_c = AwwwardsTheme.ACCENT_EMERALD if "qwen" in key else (AwwwardsTheme.ACCENT_VIOLET if key == "abliterated" else AwwwardsTheme.ACCENT_CYAN)
            ui["card"].configure(border_color=border_c)
        else:
            if not file_exists:
                ui["status_pill"].configure(fg_color="#182030")
                ui["status_lbl"].configure(
                    text=f"○ NENÍ STAŽENO (Port :{cfg['port']})",
                    text_color=AwwwardsTheme.TEXT_MUTED
                )
                ui["launch_btn"].configure(
                    text=f"📥 Stáhnout model (~{cfg['download_size_gb']} GB)",
                    fg_color=AwwwardsTheme.ACCENT_BLUE,
                    hover_color=AwwwardsTheme.ACCENT_BLUE_HOVER,
                    state="normal",
                    command=lambda k=key: self.start_model_download(k)
                )
                ui["card"].configure(border_color=AwwwardsTheme.CARD_BORDER)
            else:
                ui["status_pill"].configure(fg_color="#182030")
                ui["status_lbl"].configure(
                    text=f"○ ZASTAVENO (Port :{cfg['port']})",
                    text_color=AwwwardsTheme.TEXT_MUTED
                )
                ui["launch_btn"].configure(
                    text=f"▶ Spustit model ({cfg['short_name']})",
                    fg_color=AwwwardsTheme.ACCENT_EMERALD,
                    hover_color=AwwwardsTheme.ACCENT_EMERALD_HOVER,
                    state="normal",
                    command=lambda k=key: self.toggle_model(k)
                )
                ui["card"].configure(border_color=AwwwardsTheme.CARD_BORDER)

    def start_model_download(self, key):
        inst = self.instances[key]
        cfg = inst["config"]
        if inst.get("is_downloading", False):
            return

        inst["is_downloading"] = True
        inst["download_status_text"] = "⏳ PŘÍPRAVA STAHOVÁNÍ..."
        inst["download_btn_text"] = "⏳ Zahajuji..."
        self.update_card_ui(key)
        self.append_log(f"\n[DOWNLOAD] Zahajuji stahování {cfg['name']} (~{cfg['download_size_gb']} GB)...\n")
        self.append_log(f"           URL: {cfg['download_url']}\n")

        threading.Thread(target=self._download_worker, args=(key,), daemon=True).start()

    def _download_worker(self, key):
        inst = self.instances[key]
        cfg = inst["config"]
        target_path = cfg["path"]
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        temp_path = target_path + ".tmp"
        url = cfg["download_url"]

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "LocalAILauncher/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp, open(temp_path, "wb") as f:
                total_bytes = int(resp.headers.get("content-length", 0))
                downloaded = 0
                last_time = time.time()
                while True:
                    chunk = resp.read(1024 * 1024)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    now = time.time()
                    if now - last_time > 0.4:
                        last_time = now
                        pct = (downloaded / total_bytes * 100) if total_bytes > 0 else 0
                        mb = downloaded / (1024 * 1024)
                        total_mb = total_bytes / (1024 * 1024) if total_bytes > 0 else 0
                        self.after(0, lambda k=key, p=pct, m=mb, tm=total_mb: self._update_download_progress(k, p, m, tm))

            if os.path.exists(target_path):
                os.remove(target_path)
            os.rename(temp_path, target_path)

            self.after(0, lambda k=key: self._on_download_success(k))

        except Exception as e:
            self.after(0, lambda k=key, err=str(e): self._on_download_error(k, err))

    def _update_download_progress(self, key, pct, mb, total_mb):
        inst = self.instances[key]
        inst["download_status_text"] = f"⏳ STAHOVÁNÍ: {pct:.1f} % ({mb:.0f}/{total_mb:.0f} MB)"
        inst["download_btn_text"] = f"⏳ Stahuji... {pct:.0f} %"
        self.update_card_ui(key)

    def _on_download_success(self, key):
        inst = self.instances[key]
        inst["is_downloading"] = False
        self.update_card_ui(key)
        self.append_log(f"\n[OK] Model {inst['config']['name']} byl úspěšně stažen a je připraven ke spuštění!\n")
        messagebox.showinfo("Hotovo", f"Model {inst['config']['name']} byl úspěšně stažen!")

    def _on_download_error(self, key, err):
        inst = self.instances[key]
        inst["is_downloading"] = False
        self.update_card_ui(key)
        self.append_log(f"\n[CHYBA] Stahování selhalo: {err}\n")
        messagebox.showerror("Chyba stahování", f"Stahování modelu selhalo:\n{err}")

        # Update Telemetry counter
        running_cnt = sum(1 for k in self.instances if self.instances[k]["is_running"])
        self.srv_metric_val.configure(
            text=f"{running_cnt} / {len(self.instances)} BĚŽÍ",
            text_color="#34D399" if running_cnt > 0 else AwwwardsTheme.TEXT_DIM
        )

    def check_initial_ports(self):
        for key in self.instances:
            port = self.instances[key]["config"]["port"]
            try:
                req = urllib.request.Request(f"http://127.0.0.1:{port}/health")
                with urllib.request.urlopen(req, timeout=1) as resp:
                    if resp.status == 200:
                        self.instances[key]["is_running"] = True
                        self.update_card_ui(key)
                        self.append_log(f"[INFO] Detekován již aktivní server pro {key} na portu {port}.\n")
            except Exception:
                pass
            self.update_card_ui(key)

    def open_browser_chat(self, port):
        webbrowser.open(f"http://localhost:{port}")

    def copy_api_url(self, port):
        url = f"http://127.0.0.1:{port}/v1"
        self.clipboard_clear()
        self.clipboard_append(url)
        messagebox.showinfo("Zkopírováno", f"URL API byla zkopírována do schránky:\n{url}")

    # --- IDE Synchronizations ---

    def sync_all_ides(self, silent=False):
        self.sync_minimax_config(silent=True)
        self.sync_opencode_config(silent=True)
        if not silent:
            messagebox.showinfo(
                "Synchronizace dokončena",
                "Konfigurace pro MiniMax Code i OpenCode byly úspěšně aktualizovány!\n\n"
                "• Port 8082: Qwen 2.5 Coder 7B\n"
                "• Port 8080: Craknutý Bonsai 2 27B\n"
                "• Port 8081: Originální Bonsai 2 27B\n\n"
                "(V MiniMax Code stačí stisknout Ctrl+R pro znovunačtení)."
            )

    def sync_minimax_config(self, silent=False):
        try:
            if not os.path.exists(MINIMAX_CONFIG_PATH):
                return

            with open(MINIMAX_CONFIG_PATH, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

            custom_provider = data.get("custom_provider", {})

            # 0. Dedicated Provider for Qwen 2.5 Coder 7B (Port 8082)
            custom_provider["qwen_coder"] = {
                "name": "Qwen 2.5 Coder 7B (:8082)",
                "kind": "custom",
                "enabled": True,
                "api": "openai-completions",
                "options": {
                    "apiKey": "dummy",
                    "baseURL": "http://127.0.0.1:8082/v1",
                    "authMode": "api-key"
                },
                "models": {
                    "qwen-2.5-coder-7b": {
                        "name": "Qwen 2.5 Coder 7B (Instruct)",
                        "configuration_source": "manual",
                        "enabled": True,
                        "tool_call": True,
                        "attachment": False,
                        "temperature": True,
                        "modalities": {"input": ["text"], "output": ["text"]},
                        "limit": {"context": 32768, "output": 8192},
                        "reasoning": False
                    }
                }
            }

            # 1. Dedicated Provider for Abliterated (Port 8080)
            custom_provider["bonsai_abliterated"] = {
                "name": "Bonsai 2 (Craknutý :8080)",
                "kind": "custom",
                "enabled": True,
                "api": "openai-completions",
                "options": {
                    "apiKey": "dummy",
                    "baseURL": "http://127.0.0.1:8080/v1",
                    "authMode": "api-key"
                },
                "models": {
                    "bonsai-2-27b-abliterated": {
                        "name": "Bonsai 2 27B (Craknutý / Abliterated)",
                        "configuration_source": "manual",
                        "enabled": True,
                        "tool_call": True,
                        "attachment": True,
                        "temperature": True,
                        "modalities": {"input": ["text", "image"], "output": ["text"]},
                        "limit": {"context": 32768, "output": 4096},
                        "capabilities": {"support_image": True},
                        "reasoning": True,
                        "thinking_config": {"mode": "switchable", "default_value": "true"}
                    }
                }
            }

            # 2. Dedicated Provider for Original (Port 8081)
            custom_provider["bonsai_original"] = {
                "name": "Bonsai 2 (Originální :8081)",
                "kind": "custom",
                "enabled": True,
                "api": "openai-completions",
                "options": {
                    "apiKey": "dummy",
                    "baseURL": "http://127.0.0.1:8081/v1",
                    "authMode": "api-key"
                },
                "models": {
                    "bonsai-2-27b": {
                        "name": "Bonsai 2 27B (Originální)",
                        "configuration_source": "manual",
                        "enabled": True,
                        "tool_call": True,
                        "attachment": True,
                        "temperature": True,
                        "modalities": {"input": ["text", "image"], "output": ["text"]},
                        "limit": {"context": 32768, "output": 4096},
                        "capabilities": {"support_image": True},
                        "reasoning": True,
                        "thinking_config": {"mode": "switchable", "default_value": "true"}
                    }
                }
            }

            # 3. Unified Legacy Provider (Port 8080) for backwards compatibility
            bonsai_legacy = custom_provider.get("bonsai", {})
            bonsai_legacy["name"] = "Bonsai 2 (Auto :8080)"
            bonsai_legacy["kind"] = "custom"
            bonsai_legacy["enabled"] = True
            bonsai_legacy["api"] = "openai-completions"
            bonsai_legacy["options"] = {
                "apiKey": "dummy",
                "baseURL": "http://127.0.0.1:8080/v1",
                "authMode": "api-key"
            }
            bonsai_legacy["models"] = {
                "bonsai-2-27b-abliterated": custom_provider["bonsai_abliterated"]["models"]["bonsai-2-27b-abliterated"],
                "bonsai-2-27b": custom_provider["bonsai_original"]["models"]["bonsai-2-27b"]
            }
            custom_provider["bonsai"] = bonsai_legacy

            data["custom_provider"] = custom_provider

            with open(MINIMAX_CONFIG_PATH, "w", encoding="utf-8") as f:
                yaml.dump(data, f, allow_unicode=True, sort_keys=False)

            self.append_log("[OK] MiniMax Code: Konfigurace pro porty :8082, :8080 a :8081 úspěšně zapsána.\n")
        except Exception as e:
            self.append_log(f"[CHYBA] Selhala aktualizace MiniMax: {e}\n")

    def sync_opencode_config(self, silent=False):
        try:
            config = {
                "$schema": "https://opencode.ai/config.json",
                "providers": {
                    "qwen_coder": {
                        "name": "Qwen 2.5 Coder 7B (:8082)",
                        "package": "@ai-sdk/openai-compatible",
                        "settings": {"baseURL": "http://127.0.0.1:8082/v1"},
                        "models": {
                            "qwen-2.5-coder-7b": {"name": "Qwen 2.5 Coder 7B (Instruct)"}
                        }
                    },
                    "bonsai_abliterated": {
                        "name": "Bonsai 2 Craknutý (:8080)",
                        "package": "@ai-sdk/openai-compatible",
                        "settings": {"baseURL": "http://127.0.0.1:8080/v1"},
                        "models": {
                            "bonsai-2-27b-abliterated": {"name": "Bonsai 2 27B (Craknutý)"}
                        }
                    },
                    "bonsai_original": {
                        "name": "Bonsai 2 Originální (:8081)",
                        "package": "@ai-sdk/openai-compatible",
                        "settings": {"baseURL": "http://127.0.0.1:8081/v1"},
                        "models": {
                            "bonsai-2-27b": {"name": "Bonsai 2 27B (Originální)"}
                        }
                    },
                    "bonsai": {
                        "name": "Bonsai 2 (:8080)",
                        "package": "@ai-sdk/openai-compatible",
                        "settings": {"baseURL": "http://127.0.0.1:8080/v1"},
                        "models": {
                            "bonsai-2-27b-abliterated": {"name": "Bonsai 2 27B (Craknutý)"},
                            "bonsai-2-27b": {"name": "Bonsai 2 27B (Originální)"}
                        }
                    }
                }
            }
            os.makedirs(os.path.dirname(OPENCODE_CONFIG_PATH), exist_ok=True)
            with open(OPENCODE_CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            self.append_log("[OK] OpenCode: Konfigurace pro porty :8082, :8080 a :8081 úspěšně zapsána.\n")
        except Exception as e:
            self.append_log(f"[CHYBA] Selhala aktualizace OpenCode: {e}\n")

    def append_log(self, text):
        if "log_textbox" in self.__dict__ and self.__dict__["log_textbox"] is not None:
            try:
                self.log_textbox.insert("end", text)
                self.log_textbox.see("end")
            except Exception:
                pass
        else:
            print(text, end="")

    def clear_logs(self):
        self.log_textbox.delete("1.0", "end")

    # --- Live System Monitoring Loop ---

    def start_monitoring(self):
        threading.Thread(target=self._monitoring_loop, daemon=True).start()

    def _monitoring_loop(self):
        while True:
            try:
                # GPU VRAM via nvidia-smi
                out = subprocess.check_output(
                    ["nvidia-smi", "--query-gpu=memory.used,memory.total,utilization.gpu", "--format=csv,noheader,nounits"],
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                ).strip()
                parts = [p.strip() for p in out.split(",")]
                if len(parts) >= 3:
                    u_gpu = float(parts[0]) / 1024
                    t_gpu = float(parts[1]) / 1024
                    ratio_gpu = u_gpu / t_gpu if t_gpu > 0 else 0
                    self.after(0, lambda u=u_gpu, t=t_gpu, r=ratio_gpu: self._update_gpu_metrics(u, t, r))
            except Exception:
                pass

            try:
                # System RAM via psutil
                vm = psutil.virtual_memory()
                u_ram = vm.used / (1024 ** 3)
                t_ram = vm.total / (1024 ** 3)
                r_ram = vm.percent / 100.0
                self.after(0, lambda u=u_ram, t=t_ram, r=r_ram: self._update_ram_metrics(u, t, r))
            except Exception:
                pass

            time.sleep(2.5)

    def _update_gpu_metrics(self, used, total, ratio):
        self.gpu_metric_val.configure(text=f"{used:.1f} / {total:.1f} GB")
        self.gpu_progress.set(min(1.0, max(0.0, ratio)))
        if ratio > 0.92:
            self.gpu_progress.configure(progress_color=AwwwardsTheme.ACCENT_CRIMSON)
        elif ratio > 0.75:
            self.gpu_progress.configure(progress_color=AwwwardsTheme.ACCENT_AMBER)
        else:
            self.gpu_progress.configure(progress_color=AwwwardsTheme.ACCENT_CYAN)

    def _update_ram_metrics(self, used, total, ratio):
        self.ram_metric_val.configure(text=f"{used:.1f} / {total:.0f} GB")
        self.ram_progress.set(min(1.0, max(0.0, ratio)))


if __name__ == "__main__":
    app = LocalAILauncherApp()
    app.mainloop()

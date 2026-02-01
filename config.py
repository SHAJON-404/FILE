#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration and utilities for cross-platform Facebook tool.
Supports: Windows, Linux, Termux (Android)

Author: SHAJON
GitHub: SHAJON-404
"""

import os
import sys
import json
import platform
import signal
import time
import random
import binascii
import subprocess
import shutil
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional, Callable, Dict, Any


# ================== PLATFORM INFO ==================

@dataclass
class PlatformInfo:
    """Platform-specific configuration."""
    name: str
    is_termux: bool = False
    is_windows: bool = False
    is_linux: bool = False
    output_dir: Path = field(default_factory=Path)
    clear_cmd: str = "clear"


# ================== COLORS ==================

@dataclass
class Colors:
    """ANSI color codes."""
    BLACK: str = '\x1b[1;30m'
    RED: str = '\x1b[1;31m'
    GREEN: str = '\x1b[1;32m'
    YELLOW: str = '\x1b[1;33m'
    BLUE: str = '\x1b[1;34m'
    PURPLE: str = '\x1b[1;35m'
    CYAN: str = '\x1b[1;36m'
    WHITE: str = '\x1b[1;37m'
    ORANGE: str = '\x1b[38;5;208m'
    RESET: str = '\x1b[0m'


# ================== CONFIG CLASS ==================

class Config:
    """
    Singleton configuration manager for the Facebook tool.
    Handles platform detection, session storage, and utilities.
    """
    
    _instance: Optional['Config'] = None
    
    # Device models for user agent generation
    SAMSUNG_MODELS: List[str] = [
        "SM-G991B", "SM-G996B", "SM-G998B", "SM-A528B", "SM-M336B", 
        "SM-F926B", "SM-F711B", "SM-A127F", "SM-M127F", "SM-G973F", 
        "SM-G975F", "SM-G970F", "SM-A225F", "SM-M225FV", "SM-A325F", 
        "SM-M325F", "SM-A426B", "SM-M426B", "SM-A526B", "SM-M526B",
        "SM-A715F", "SM-M715F", "SM-A515F", "SM-M515F", "SM-A105F", 
        "SM-M105F", "SM-A205F", "SM-M205F", "SM-N980F", "SM-N986B"
    ]
    
    NETWORK_OPERATORS: List[str] = [
        "Robi", "Airtel", "Grameenphone", "Banglalink", "Teletalk", 
        "Jio", "Vodafone", "Airtel India", "Telenor", "AT&T", 
        "Verizon", "Sprint", "T-Mobile", "Orange", "O2", 
        "Vodafone UK", "China Mobile", "China Unicom", "China Telecom", 
        "NTT Docomo", "SK Telecom", "KT", "Telstra", "Optus", 
        "Rogers", "Bell", "Telus", "MTN", "Vodacom", "Etisalat"
    ]
    
    TERMINAL_TITLE: str = "🔥SHAJON~404🔥"
    
    def __new__(cls) -> 'Config':
        """Singleton pattern - ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self) -> None:
        """Initialize configuration (only once due to singleton)."""
        if self._initialized:
            return
        
        self._initialized = True
        self._colors = Colors()
        self._platform = self._detect_platform()
        self._script_dir = Path(__file__).parent.resolve()
        self._session_file = self._script_dir / ".shajon_session.json"
        
        # Enable ANSI on Windows
        if self._platform.is_windows:
            try:
                import colorama
                colorama.init()
            except ImportError:
                os.system("")
    
    # ================== PROPERTIES ==================
    
    @property
    def platform(self) -> PlatformInfo:
        """Get platform information."""
        return self._platform
    
    @property
    def colors(self) -> Colors:
        """Get color codes."""
        return self._colors
    
    @property
    def session_file(self) -> Path:
        """Get session file path."""
        return self._session_file
    
    @property
    def script_dir(self) -> Path:
        """Get script directory path."""
        return self._script_dir
    
    @property
    def r(self) -> str:
        return self._colors.RED
    
    @property
    def g(self) -> str:
        return self._colors.GREEN
    
    @property
    def w(self) -> str:
        return self._colors.WHITE
    
    @property
    def b(self) -> str:
        return self._colors.BLUE
    
    @property
    def p(self) -> str:
        return self._colors.PURPLE
    
    @property
    def o(self) -> str:
        return self._colors.BLACK
    
    @property
    def y(self) -> str:
        return self._colors.YELLOW
    
    @property
    def style_box(self) -> str:
        """Get styled box prefix."""
        return f"{self.r}[{self.w}ヅ{self.r}]{self.w}"
    
    @property
    def line(self) -> str:
        """Get separator line."""
        return f"{self.b}━" * 56
    
    @property
    def logo(self) -> str:
        """Get application logo."""
        return f'''{self.g}888888 88 88     888888        {self.r}/{self.g}/{self.r}/{self.w}OWNER {self.g}>{self.r}={self.g}={self.r}>{self.g} SHAJON
{self.g}88__   88 88     88__         {self.r}/{self.g}/{self.r}/{self.w}GitHub {self.g}>{self.r}={self.g}={self.r}>{self.g} SHAJON-404
{self.g}88""   88 88  .o 88""        {self.r}/{self.g}/{self.r}/{self.w}TOOL {self.g}>{self.r}={self.g}={self.r}>{self.g} FILE MAKE
{self.g}88     88 88ood8 888888     {self.r}/{self.g}/{self.r}/{self.w}VERSION {self.g}>{self.r}={self.g}={self.r}>{self.g} 3.1 {self.r}[{self.g}BETA{self.r}]
{self.line}'''
    
    # ================== PLATFORM DETECTION ==================
    
    @staticmethod
    def _detect_platform() -> PlatformInfo:
        """Detect current platform and return configuration."""
        system = platform.system().lower()
        
        is_termux = (
            os.path.exists("/data/data/com.termux") or
            "com.termux" in os.environ.get("PREFIX", "") or
            os.environ.get("TERMUX_VERSION") is not None
        )
        
        if is_termux:
            return PlatformInfo(
                name="Termux",
                is_termux=True,
                output_dir=Path("/sdcard/SHAJON"),
                clear_cmd="clear"
            )
        elif system == "windows":
            return PlatformInfo(
                name="Windows",
                is_windows=True,
                output_dir=Path.cwd() / "SHAJON",
                clear_cmd="cls"
            )
        else:
            return PlatformInfo(
                name="Linux",
                is_linux=True,
                output_dir=Path.cwd() / "SHAJON",
                clear_cmd="clear"
            )
    
    # ================== USER AGENT GENERATORS ==================
    
    @staticmethod
    def generate_fb_user_agent() -> str:
        """Generate a random Facebook mobile user agent."""
        fbav = f"{random.randint(11, 470)}.0.0.{random.randrange(9, 49)}{random.randint(11, 77)}"
        fbbv = str(random.randint(100000000, 409614015))
        fbcr = random.choice(Config.NETWORK_OPERATORS)
        model = random.choice(Config.SAMSUNG_MODELS)
        
        return (
            f"[FBAN/FB4A;FBAV/{fbav};FBBV/{fbbv};"
            f"FBDM/{{density=2.0,width=720,height=1456}};"
            f"FBLC/en_GB;FBRV/{fbbv};FBCR/{fbcr};"
            f"FBMF/samsung;FBBD/samsung;FBPN/com.facebook.katana;"
            f"FBDV/{model};FBSV/10;FBBK/1;FBOP/1;FBCA/arm64-v8a:;]"
        )
    
    # ================== DISPLAY UTILITIES ==================
    
    def clear_screen(self) -> None:
        """Clear terminal screen and show logo."""
        os.system(self._platform.clear_cmd)
        print(self.logo)
    
    def set_terminal_title(self, title: str = None) -> None:
        """Set terminal title cross-platform."""
        title = title or self.TERMINAL_TITLE
        if self._platform.is_windows:
            os.system(f'title {title}')
        else:
            sys.stdout.write(f'\x1b]2;{title}\x07')
            sys.stdout.flush()
    
    def linex(self) -> None:
        """Print a separator line."""
        print(self.line)
    
    def box(self, value: str) -> str:
        """Format a value in a styled box."""
        return f"{self.r}[{self.w}{value}{self.r}]{self.w}"
    
    def animate(self, text: str, delay: float = 0.01) -> None:
        """Animate text output character by character."""
        for char in text + "\n":
            sys.stdout.write(char)
            sys.stdout.flush()
            time.sleep(delay)
    
    def random_color(self) -> str:
        """Get a random ANSI color."""
        colors = [self.o, self.r, self.g, self.y, self.b, self.p, self.w]
        return random.choice(colors)
    
    # ================== FILE OPERATIONS ==================
    
    def ensure_output_dir(self) -> Path:
        """Ensure output directory exists and return path."""
        self._platform.output_dir.mkdir(parents=True, exist_ok=True)
        return self._platform.output_dir
    
    def get_output_path(self, filename: str) -> Path:
        """Get full path for output file."""
        self.ensure_output_dir()
        return self._platform.output_dir / filename
    
    def generate_filename(self, prefix: str = "shajon", ext: str = "txt") -> Path:
        """Generate a unique filename in output directory."""
        random_id = random.randint(1, 9999)
        return self.get_output_path(f"{prefix}_{random_id}.{ext}")
    
    def clean_small_files(self, min_size_kb: int = 10) -> None:
        """Remove small txt files from output directory."""
        try:
            for file_path in self._platform.output_dir.glob("*.txt"):
                if file_path.stat().st_size < min_size_kb * 1024:
                    file_path.unlink()
        except Exception:
            pass
    
    def remove_duplicates_from_file(self, filepath: Path) -> int:
        """Remove duplicate lines from file. Returns count of unique lines."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.read().splitlines()
            
            unique_lines = sorted(set(lines), reverse=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write('\n'.join(unique_lines))
            
            return len(unique_lines)
        except Exception as e:
            print(f"{self.style_box} ERROR: {self.o}{e}")
            return 0
    
    # ================== SESSION MANAGEMENT ==================
    
    def _load_session(self) -> Dict[str, Any]:
        """Load session data from JSON file."""
        try:
            return json.loads(self._session_file.read_text(encoding='utf-8'))
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _save_session(self, data: Dict[str, Any]) -> None:
        """Save session data to JSON file."""
        self._session_file.write_text(
            json.dumps(data, indent=2, ensure_ascii=False), 
            encoding='utf-8'
        )
    
    def save_token(self, token: str) -> None:
        """Save token to session."""
        session = self._load_session()
        session['token'] = token
        self._save_session(session)
    
    def load_token(self) -> Optional[str]:
        """Load token from session."""
        return self._load_session().get('token')
    
    def save_cookie(self, cookie: str) -> None:
        """Save cookie to session."""
        session = self._load_session()
        session['cookie'] = cookie
        self._save_session(session)
    
    def load_cookie(self) -> Optional[str]:
        """Load cookie from session."""
        return self._load_session().get('cookie')
    
    def save_login_check(self, friend_ids: List[str]) -> None:
        """Save login check friend IDs to session."""
        session = self._load_session()
        session['login_check'] = friend_ids
        self._save_session(session)
    
    def load_login_check(self) -> List[str]:
        """Load login check friend IDs from session."""
        return self._load_session().get('login_check', [])
    
    def clear_credentials(self) -> None:
        """Remove session file and legacy files."""
        try:
            self._session_file.unlink()
        except FileNotFoundError:
            pass
        
        # Remove legacy .txt files
        legacy_files = [
            self._script_dir / ".shajon_token.txt",
            self._script_dir / ".shajon_cookies.txt",
            self._script_dir / ".login_check.txt"
        ]
        for file in legacy_files:
            try:
                file.unlink()
            except FileNotFoundError:
                pass
    
    def get_session_info(self) -> Dict[str, Any]:
        """Get full session info for display."""
        session = self._load_session()
        return {
            'has_token': bool(session.get('token')),
            'has_cookie': bool(session.get('cookie')),
            'friend_count': len(session.get('login_check', []))
        }
    
    # ================== SIGNAL HANDLING ==================
    
    def setup_signal_handlers(self, on_exit: Optional[Callable] = None) -> None:
        """Setup signal handlers for graceful exit."""
        
        def handle_interrupt(signum, frame):
            pass
        
        def handle_stop(signum, frame):
            self.linex()
            print(f"\r{self.style_box} THANKS FOR USING THIS TOOL....")
            if on_exit:
                on_exit()
            self.linex()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, handle_interrupt)
        
        if hasattr(signal, 'SIGTSTP') and not self._platform.is_windows:
            signal.signal(signal.SIGTSTP, handle_stop)
    
    # ================== URL HANDLING ==================
    
    def open_url(self, url: str) -> None:
        """Open URL in default browser - cross-platform."""
        try:
            if self._platform.is_termux:
                os.system(f'am start -a android.intent.action.VIEW -d "{url}" > /dev/null 2>&1')
            elif self._platform.is_windows:
                os.system(f'start "" "{url}"')
            else:
                os.system(f'xdg-open "{url}" 2>/dev/null || open "{url}" 2>/dev/null')
        except Exception:
            pass
    
    def open_social(self, platform_name: str) -> None:
        """Open social media links."""
        urls = {
            "wp": "https://chat.whatsapp.com/FBMupd6ED8xA3B3IvofPb5",
            "tg": "https://t.me/SHAJON",
            "git": "https://github.com/SHAJON-404/",
            "fb": "https://www.facebook.com/share/1A3Ljftimf/"
        }
        # Disabled for now
        # url = urls.get(platform_name, urls["fb"])
        # self.open_url(url)
    
    # ================== STORAGE CHECK ==================
    
    def check_storage_permission(self) -> bool:
        """Check and request storage permission on Termux."""
        if not self._platform.is_termux:
            return True
        
        try:
            test_file = Path("/sdcard/.shajon_test")
            test_file.write_text("test")
            test_file.unlink()
            return True
        except PermissionError:
            print(f"{self.style_box} PLEASE ALLOW STORAGE PERMISSION...✅")
            self.linex()
            os.system("termux-setup-storage")
            return False
        except Exception as e:
            print(f"{self.style_box} ERROR: {self.o}{e}")
            return False
    
    # ================== INITIALIZATION ==================
    
    def initialize(self) -> None:
        """Initialize the application."""
        self.set_terminal_title()
        self.ensure_output_dir()
        self.clean_small_files()


# ================== GLOBAL INSTANCE ==================

# Create singleton instance for backward compatibility
config = Config()

# Backward compatibility exports
PLATFORM = config.platform
C = config.colors
r, g, w, b, p, o, y = config.r, config.g, config.w, config.b, config.p, config.o, config.y
STYLE_BOX = config.style_box
LINE = config.line
LOGO = config.logo
SESSION_FILE = config.session_file

# Function aliases for backward compatibility
clear_screen = config.clear_screen
linex = config.linex
box = config.box
animate = config.animate
random_color = config.random_color
open_social = config.open_social
save_token = config.save_token
load_token = config.load_token
save_cookie = config.save_cookie
load_cookie = config.load_cookie
save_login_check = config.save_login_check
load_login_check = config.load_login_check
clear_credentials = config.clear_credentials
get_output_path = config.get_output_path
generate_filename = config.generate_filename
ensure_output_dir = config.ensure_output_dir
remove_duplicates_from_file = config.remove_duplicates_from_file
setup_signal_handlers = config.setup_signal_handlers
initialize = config.initialize
check_storage_permission = config.check_storage_permission
generate_fb_user_agent = Config.generate_fb_user_agent


if __name__ == "__main__":
    cfg = Config()
    print(f"Platform: {cfg.platform.name}")
    print(f"Output Directory: {cfg.platform.output_dir}")
    print(f"Session File: {cfg.session_file}")


#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Core Facebook API logic and async operations.
Supports: Windows, Linux, Termux (Android)

Author: SHAJON
GitHub: SHAJON-404
"""

import os
import sys
import re
import asyncio
import random
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple, Any, Callable

# Third-party imports (will be installed if missing)
try:
    import aiohttp
    import aiofiles
    import requests
except ImportError:
    import subprocess
    for module in ['aiohttp', 'aiofiles', 'requests']:
        subprocess.run([sys.executable, "-m", "pip", "install", module, "-q"])
    import aiohttp
    import aiofiles
    import requests

from config import Config


class FacebookAPI:
    """
    Facebook API operations handler.
    Manages authentication, friend dumping, and API requests.
    """
    
    # API Endpoints
    GRAPH_API_BASE: str = "https://graph.facebook.com"
    OAUTH_URL: str = "https://www.facebook.com/x/oauth/status"
    TOKEN_API_URL: str = "https://api.shajon.dev/get_token"
    LOGIN_API_URL: str = "https://api.shajon.dev/facebook_token"
    UID_API_URL: str = "https://api.shajon.dev/facebook_info"
    
    # Retry settings
    MAX_API_RETRIES: int = 10
    
    def __init__(self, config: Optional[Config] = None) -> None:
        """
        Initialize FacebookAPI with config.
        
        Args:
            config: Configuration instance (uses singleton if not provided)
        """
        self._config = config or Config()
        self._token: Optional[str] = None
        self._cookie: Optional[str] = None
        
        # Load existing session
        self._load_session()
    
    # ================== PROPERTIES ==================
    
    @property
    def config(self) -> Config:
        """Get configuration instance."""
        return self._config
    
    @property
    def token(self) -> Optional[str]:
        """Get current access token."""
        return self._token
    
    @token.setter
    def token(self, value: str) -> None:
        """Set access token and save to session."""
        self._token = value
        self._config.save_token(value)
    
    @property
    def cookie(self) -> Optional[str]:
        """Get current cookie."""
        return self._cookie
    
    @cookie.setter
    def cookie(self, value: str) -> None:
        """Set cookie and save to session."""
        self._cookie = value
        self._config.save_cookie(value)
    
    @property
    def is_logged_in(self) -> bool:
        """Check if user is logged in."""
        return bool(self._token and self._cookie)
    
    @property
    def headers(self) -> Dict[str, str]:
        """Get API request headers."""
        return {
            "User-Agent": Config.generate_fb_user_agent()
        }
    
    # ================== SESSION MANAGEMENT ==================
    
    def _load_session(self) -> None:
        """Load token and cookie from saved session."""
        self._token = self._config.load_token()
        self._cookie = self._config.load_cookie()
    
    def logout(self) -> None:
        """Clear credentials and logout."""
        self._token = None
        self._cookie = None
        self._config.clear_credentials()
    
    # ================== UTILITY METHODS ==================
    
    @staticmethod
    def parse_cookies(cookie_str: str) -> Dict[str, str]:
        """Parse cookie string to dictionary."""
        cookies = {}
        for cookie in cookie_str.split(';'):
            if '=' in cookie:
                key, value = cookie.strip().split('=', 1)
                cookies[key] = value
        return cookies
    
    async def _make_request(
        self,
        session: aiohttp.ClientSession,
        url: str,
        headers: Dict[str, str],
        cookies: Dict[str, str]
    ) -> Optional[Dict[str, Any]]:
        """Make an async GET request and return JSON response."""
        try:
            async with session.get(url, headers=headers, cookies=cookies) as response:
                if response.status == 200:
                    return await response.json()
        except Exception:
            pass
        return None
    
    # ================== TOKEN EXTRACTION ==================
    
    def _extract_token_from_cookie(self, cookie: str) -> Optional[str]:
        """Try to extract access token using OAuth endpoint."""
        vsn = random.randint(80, 133)
        
        headers = {
            'Accept-Language': 'id,en;q=0.9',
            'User-Agent': f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{vsn}.0.0.0 Safari/537.36',
            'Referer': 'https://www.instagram.com/',
            'Host': 'www.facebook.com',
            'Origin': 'https://www.instagram.com',
        }
        
        try:
            response = requests.get(
                f'{self.OAUTH_URL}?client_id=124024574287414&wants_cookie_data=true&origin=1&input_token=&sdk=joey&redirect_uri=https://www.instagram.com/brutalid_/',
                headers=headers,
                cookies={'cookie': cookie},
                timeout=30
            )
            
            if '"access_token":' in str(response.headers):
                match = re.search(r'"access_token":"([^"]+)"', str(response.headers))
                if match:
                    return match.group(1)
        except Exception:
            pass
        
        return None
    
    def _extract_token_from_api(self, cookie: str) -> Optional[str]:
        """Try to extract token using external API."""
        try:
            response = requests.post(
                self.TOKEN_API_URL,
                json={'cookies': cookie},
                timeout=30
            )
            data = response.json()
            
            if data.get('status') == 'success' and data.get('data', {}).get('access_token'):
                return data['data']['access_token']
        except Exception:
            pass
        
        return None
    
    # ================== UID EXTRACTION ==================
    
    def extract_uid_from_url(self, url: str) -> Optional[str]:
        """Extract Facebook UID from profile URL."""
        if not url.startswith("https://www.facebook.com/"):
            return None
        
        try:
            response = requests.post(
                self.UID_API_URL,
                json={
                    "url": url,
                    "show_all_social_links": False
                },
                timeout=30
            )
            data = response.json()
            
            if data.get('status') == 'success' and data.get('data', {}).get('user_id'):
                return data['data']['user_id']
        except Exception:
            pass
        
        return None
    
    # ================== LOGIN METHODS ==================
    
    def login_with_credentials(self, uid: str, password: str) -> Tuple[bool, str]:
        """
        Login using UID and password via API.
        
        Args:
            uid: Facebook UID or email
            password: Account password
        
        Returns:
            (success, status_message)
        """
        retry_count = 0
        
        while retry_count < self.MAX_API_RETRIES:
            try:
                # Call login API
                response = requests.post(
                    self.LOGIN_API_URL,
                    json={
                        "email": uid,
                        "password": password,
                        "convert_all": True
                    },
                    timeout=30
                )
                
                response_text = response.text
                
                # Check for proxy error - retry if found
                if "SOCKSHTTPSConnectionPool" in response_text:
                    retry_count += 1
                    self._config.animate(
                        f'{self._config.style_box} PROXY ERROR, RETRYING ({retry_count}/{self.MAX_API_RETRIES})...'
                    )
                    continue
                
                data = response.json()
                
                # Check for success
                if data.get('status') == 'success' and data.get('data', {}).get('cookies'):
                    cookie = data['data']['cookies']
                    
                    # Use cookies to get token
                    token = self._extract_token_from_cookie(cookie)
                    if not token:
                        token = self._extract_token_from_api(cookie)
                    
                    if token:
                        self.cookie = cookie
                        self.token = token
                        return True, "SUCCESS"
                    return False, "TOKEN_FAILED"
                
                # Check for checkpoint
                error_msg = str(data.get('message', '')).lower()
                if 'checkpoint' in error_msg or 'two-factor' in error_msg:
                    return False, "CHECKPOINT"
                
                # Check for invalid credentials
                if 'invalid' in error_msg or 'incorrect' in error_msg or 'wrong' in error_msg:
                    return False, "INVALID_CREDENTIALS"
                
                # Generic error
                return False, data.get('message', 'LOGIN_FAILED')
                
            except requests.exceptions.Timeout:
                retry_count += 1
                self._config.animate(
                    f'{self._config.style_box} TIMEOUT, RETRYING ({retry_count}/{self.MAX_API_RETRIES})...'
                )
                continue
            except Exception as e:
                return False, f"ERROR: {e}"
        
        return False, "MAX_RETRIES_EXCEEDED"
    
    def login_with_cookie(self, cookie: str) -> Tuple[bool, str]:
        """
        Login using cookie.
        
        Args:
            cookie: Facebook cookie string
        
        Returns:
            (success, status_message)
        """
        # Ensure cookie has 'sb=' prefix
        if not re.search(r'sb=[^;]+', cookie):
            cookie = f'sb=By.ShajoN-404.OfficiaL;{cookie}'
        
        # Try OAuth method first
        token = self._extract_token_from_cookie(cookie)
        if token:
            self.cookie = cookie
            self.token = token
            return True, "SUCCESS"
        
        # Fallback to API method
        token = self._extract_token_from_api(cookie)
        if token:
            self.cookie = cookie
            self.token = token
            return True, "SUCCESS"
        
        return False, "TOKEN_FAILED"
    
    # ================== LOGIN VALIDATION ==================
    
    def validate_login(self) -> Tuple[bool, List[str]]:
        """
        Validate login by checking if we can fetch friends data.
        
        Returns:
            (success, list_of_friend_ids)
        """
        if not self.is_logged_in:
            return False, []
        
        # Load test UIDs
        uid_file = None
        possible_paths = [
            Path(".uid.txt"),
            Path("IMAGE/.uid.txt"),
            self._config.script_dir / ".uid.txt",
        ]
        
        for path in possible_paths:
            if path.exists():
                uid_file = path
                break
        
        if not uid_file:
            print(f"{self._config.style_box} {self._config.r}WARNING:{self._config.w} .uid.txt not found, skipping validation")
            return True, []
        
        try:
            test_uids = uid_file.read_text().splitlines()
        except Exception as e:
            print(f"{self._config.style_box} {self._config.r}ERROR:{self._config.w} Cannot read .uid.txt: {e}")
            return True, []
        
        if not test_uids:
            return True, []
        
        cookies_dict = self.parse_cookies(self._cookie)
        friend_ids = []
        blocked_detected = False
        login_success = False
        
        for uid in test_uids:
            uid = uid.strip()
            if not uid:
                continue
            
            uid_masked = uid[:8] + "*****" if len(uid) > 8 else uid
            self._config.animate(f'{self._config.style_box} TRYING {uid_masked}...')
            
            try:
                url = f"{self.GRAPH_API_BASE}/{uid}?access_token={self._token}&fields=friends"
                response = requests.get(url, headers=self.headers, cookies=cookies_dict, timeout=10)
                data = response.json()
                
                error_words = ["blocked", "misuse", "abusive", "exceeded", "misusing", "error"]
                if any(word in str(data).lower() for word in error_words):
                    self._config.animate(f'{self._config.style_box}{self._config.r} BLOCKED {self._config.w}→ {uid_masked}')
                    self._config.linex()
                    blocked_detected = True
                    continue
                
                friends = data.get('friends', {}).get('data', [])
                if friends:
                    self._config.animate(f'{self._config.style_box}{self._config.g} SUCCESS {self._config.w}→ {uid_masked}')
                    friend_ids = [f['id'] for f in friends]
                    self._config.save_login_check(friend_ids)
                    login_success = True
                    self._config.linex()
                    self._config.animate(f"{self._config.style_box}{self._config.g} LOGIN SUCCESSFUL! FRIENDS DATA EXTRACTED.")
                    self._config.linex()
                    return True, friend_ids
                else:
                    self._config.animate(f'{self._config.style_box}{self._config.r} NO FRIENDS {self._config.w}→ {uid_masked}')
                    continue
                    
            except requests.exceptions.Timeout:
                self._config.animate(f'{self._config.style_box}{self._config.r} TIMEOUT {self._config.w}→ {uid_masked}')
                continue
            except Exception:
                self._config.animate(f'{self._config.style_box}{self._config.r} ERROR {self._config.w}→ {uid_masked}')
                continue
        
        if blocked_detected and not login_success:
            self._config.linex()
            self._config.animate(f'{self._config.style_box} TRY THIS COOKIES AFTER 10 HOURS...')
            self._config.animate(f'{self._config.style_box} IT IS NOT POSSIBLE TO DUMP WITH THIS COOKIES AT THIS TIME.')
            self._config.animate(f'{self._config.style_box} NOW TRY WITH ANOTHER INSTA ADDED FACEBOOK ID COOKIES.')
            self._config.linex()
        elif not login_success:
            self._config.linex()
            self._config.animate(f"{self._config.style_box} PLEASE LOGIN WITH ANOTHER COOKIE...!!")
            self._config.animate(f"{self._config.style_box} ALL IDS FAILED, PLEASE USE VPN OR TRY ANOTHER COOKIE...!!")
            self._config.linex()
        
        return False, []
    
    # ================== DUMP OPERATIONS ==================
    
    async def _fetch_friends(
        self,
        session: aiohttp.ClientSession,
        uid: str
    ) -> Optional[Dict[str, Any]]:
        """Fetch friends list for a UID."""
        url = f"{self.GRAPH_API_BASE}/{uid}?access_token={self._token}&fields=friends"
        return await self._make_request(session, url, self.headers, {"cookies": self._cookie})
    
    async def dump_friends(
        self,
        uids: List[str],
        output_file: Path,
        unsep_file: Optional[Path] = None,
        sep_prefixes: Optional[List[str]] = None,
        recursive: bool = True,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Tuple[int, int]:
        """
        Dump friends from list of UIDs.
        
        Args:
            uids: List of UIDs to dump friends from
            output_file: Path to save matching IDs
            unsep_file: Path to save non-matching IDs (when separating)
            sep_prefixes: Prefixes to filter by
            recursive: Whether to also dump friends of friends
            progress_callback: Function to call with progress updates
        
        Returns:
            (count_main, count_unsep)
        """
        if not self.is_logged_in:
            return 0, 0
        
        written_main: Set[str] = set()
        written_unsep: Set[str] = set()
        all_friend_ids: List[str] = []
        
        # Phase 1: Get initial friends
        async with aiohttp.ClientSession() as session:
            tasks = [self._fetch_friends(session, uid) for uid in uids]
            responses = await asyncio.gather(*tasks)
            
            for response in responses:
                if response and 'error' not in response:
                    friends = response.get('friends', {}).get('data', [])
                    for friend in friends:
                        friend_id = friend.get('id')
                        if friend_id and friend_id not in all_friend_ids:
                            all_friend_ids.append(friend_id)
        
        if not all_friend_ids:
            return 0, 0
        
        all_friend_ids = sorted(set(all_friend_ids), reverse=True)
        
        if progress_callback:
            progress_callback(f"Found {len(all_friend_ids)} friends to process")
        
        # Phase 2: Dump friends
        target_uids = all_friend_ids if recursive else uids
        line_count = 0
        line_count_un = 0
        
        async with aiohttp.ClientSession() as session:
            tasks = [self._fetch_friends(session, uid) for uid in target_uids]
            
            for i, uid in enumerate(target_uids):
                if progress_callback and i % 10 == 0:
                    progress_callback(f"Requesting: {uid}")
            
            responses = await asyncio.gather(*tasks)
            
            for response in responses:
                if not response:
                    continue
                
                friends = response.get('friends', {}).get('data', [])
                new_main = []
                new_unsep = []
                
                for friend in friends:
                    try:
                        friend_id = friend['id']
                        friend_name = friend.get('name', 'Unknown')
                        item = f"{friend_id}|{friend_name}"
                        
                        if sep_prefixes:
                            if any(friend_id.startswith(p) for p in sep_prefixes):
                                if item not in written_main:
                                    written_main.add(item)
                                    new_main.append(item)
                            else:
                                if item not in written_unsep:
                                    written_unsep.add(item)
                                    new_unsep.append(item)
                        else:
                            if item not in written_main:
                                written_main.add(item)
                                new_main.append(item)
                                
                    except KeyError:
                        continue
                
                if new_main:
                    async with aiofiles.open(output_file, 'a', encoding='utf-8') as f:
                        await f.write('\n'.join(new_main) + '\n')
                    line_count += len(new_main)
                
                if new_unsep and unsep_file:
                    async with aiofiles.open(unsep_file, 'a', encoding='utf-8') as f:
                        await f.write('\n'.join(new_unsep) + '\n')
                    line_count_un += len(new_unsep)
                
                if progress_callback:
                    progress_callback(f"Extracted: {line_count} main, {line_count_un} unsep")
        
        return line_count, line_count_un
    
    async def dump_simple(
        self,
        uids: List[str],
        output_file: Path,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> int:
        """Simple dump - just get friends from input UIDs."""
        result = await self.dump_friends(
            uids=uids,
            output_file=output_file,
            recursive=False,
            progress_callback=progress_callback
        )
        return result[0]
    
    async def dump_unlimited(
        self,
        uids: List[str],
        output_file: Path,
        unsep_file: Optional[Path] = None,
        sep_prefixes: Optional[List[str]] = None,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Tuple[int, int]:
        """Unlimited dump - get friends of friends recursively."""
        return await self.dump_friends(
            uids=uids,
            output_file=output_file,
            unsep_file=unsep_file,
            sep_prefixes=sep_prefixes,
            recursive=True,
            progress_callback=progress_callback
        )


class FileUtils:
    """File utility operations."""
    
    def __init__(self, config: Optional[Config] = None) -> None:
        """Initialize with config."""
        self._config = config or Config()
    
    @staticmethod
    def shuffle_file_lines(filepath: Path) -> bool:
        """Shuffle lines in a file randomly."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            random.shuffle(lines)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            return True
        except Exception:
            return False
    
    @staticmethod
    def divide_file(filepath: Path, parts: int, output_dir: Path) -> List[Path]:
        """Divide a file into multiple parts."""
        output_files = []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            base_name = filepath.stem.lower()
            part_size = len(lines) // parts
            remainder = len(lines) % parts
            
            for i in range(parts):
                start = i * part_size
                end = start + part_size
                if i == parts - 1:
                    end += remainder
                
                part_file = output_dir / f"{base_name}_part_{i+1}.txt"
                with open(part_file, 'w', encoding='utf-8') as f:
                    f.writelines(lines[start:end])
                
                output_files.append(part_file)
            
            return output_files
        except Exception:
            return []
    
    @staticmethod
    def cut_or_delete_lines(
        filepath: Path,
        start_line: int,
        end_line: int,
        cut_to: Optional[Path] = None
    ) -> bool:
        """Cut or delete lines from a file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            start_idx = start_line - 1
            end_idx = end_line
            
            if cut_to:
                with open(cut_to, 'w', encoding='utf-8') as f:
                    f.writelines(lines[start_idx:end_idx])
            
            del lines[start_idx:end_idx]
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            return True
        except Exception:
            return False
    
    @staticmethod
    def separate_by_prefix(filepath: Path, prefixes: List[str], output_file: Path) -> int:
        """Separate lines that start with given prefixes."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.read().splitlines()
            
            matching = [line for line in lines if line.startswith(tuple(prefixes))]
            
            if matching:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(matching))
                return len(matching)
            
            return 0
        except Exception:
            return 0
    
    @staticmethod
    def remove_emoji_names(filepath: Path) -> int:
        """Remove lines with emoji or stylish names."""
        import unicodedata
        
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"
            "\U0001F300-\U0001F5FF"
            "\U0001F680-\U0001F6FF"
            "\U0001F1E0-\U0001F1FF"
            "\U00002700-\U000027BF"
            "\U0001F900-\U0001F9FF"
            "\U00002600-\U000026FF"
            "\U00002B00-\U00002BFF"
            "\U0001FA70-\U0001FAFF"
            "\U000025A0-\U000025FF"
            "]+", flags=re.UNICODE
        )
        
        def has_invalid_chars(text: str) -> bool:
            for ch in text:
                cat = unicodedata.category(ch)
                if not (cat.startswith(('L', 'M')) or cat == 'Zs'):
                    return True
            return False
        
        def is_repeated_char(text: str) -> bool:
            chars = [c for c in text if not c.isspace()]
            return bool(chars) and len(set(chars)) == 1
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.read().splitlines()
            
            unique_lines = sorted(set(lines), reverse=True)
            clean_lines = []
            
            for line in unique_lines:
                line = line.strip()
                if not line or 'name' in line.lower() or not re.match(r'^[1-9]', line):
                    continue
                
                parts = line.split('|', 1)
                if len(parts) != 2:
                    continue
                
                uid, name = parts
                name = name.strip()
                
                if not name:
                    continue
                if emoji_pattern.search(name):
                    continue
                if has_invalid_chars(name):
                    continue
                if is_repeated_char(name):
                    continue
                
                clean_lines.append(f"{uid}|{name}")
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write('\n'.join(clean_lines))
            
            return len(clean_lines)
        except Exception:
            return 0


# ================== BACKWARD COMPATIBILITY ==================

# Create default instances
_config = Config()
_api = FacebookAPI(_config)
_file_utils = FileUtils(_config)

# Function aliases for backward compatibility
def login_with_credentials(uid: str, password: str) -> Tuple[Optional[str], Optional[str], str]:
    success, status = _api.login_with_credentials(uid, password)
    if success:
        return _api.cookie, _api.token, status
    return None, None, status

def login_with_cookie(cookie: str) -> Tuple[Optional[str], str]:
    success, status = _api.login_with_cookie(cookie)
    if success:
        return _api.token, status
    return None, status

def validate_login(token: str, cookie: str) -> Tuple[bool, List[str]]:
    _api._token = token
    _api._cookie = cookie
    return _api.validate_login()

def extract_uid_from_url(url: str) -> Optional[str]:
    return _api.extract_uid_from_url(url)

async def dump_unlimited(
    uids: List[str],
    token: str,
    cookie: str,
    output_file: Path,
    unsep_file: Optional[Path] = None,
    sep_prefixes: Optional[List[str]] = None,
    progress_callback: Optional[Callable[[str], None]] = None
) -> Tuple[int, int]:
    _api._token = token
    _api._cookie = cookie
    return await _api.dump_unlimited(uids, output_file, unsep_file, sep_prefixes, progress_callback)

async def dump_simple(
    uids: List[str],
    token: str,
    cookie: str,
    output_file: Path,
    progress_callback: Optional[Callable[[str], None]] = None
) -> int:
    _api._token = token
    _api._cookie = cookie
    return await _api.dump_simple(uids, output_file, progress_callback)

shuffle_file_lines = FileUtils.shuffle_file_lines
divide_file = FileUtils.divide_file
cut_or_delete_lines = FileUtils.cut_or_delete_lines
separate_by_prefix = FileUtils.separate_by_prefix
remove_emoji_names = FileUtils.remove_emoji_names


if __name__ == "__main__":
    cfg = Config()
    api = FacebookAPI(cfg)
    print(f"Core module loaded successfully!")
    print(f"Platform: {cfg.platform.name}")
    print(f"Logged in: {api.is_logged_in}")

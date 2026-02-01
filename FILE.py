#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main entry point for cross-platform Facebook tool.
Supports: Windows, Linux, Termux (Android)

Author: SHAJON
GitHub: SHAJON-404
"""

import sys
import time
import asyncio
from pathlib import Path
from typing import List, Optional

from config import Config
from core import FacebookAPI, FileUtils


class App:
    """
    Main application controller.
    Handles user interface, menus, and orchestrates operations.
    """
    
    def __init__(self) -> None:
        """Initialize application with config and API instances."""
        self._config = Config()
        self._api = FacebookAPI(self._config)
        self._file_utils = FileUtils(self._config)
    
    # ================== PROPERTIES ==================
    
    @property
    def config(self) -> Config:
        """Get configuration instance."""
        return self._config
    
    @property
    def api(self) -> FacebookAPI:
        """Get API instance."""
        return self._api
    
    @property
    def is_logged_in(self) -> bool:
        """Check if user is logged in."""
        return self._api.is_logged_in
    
    # ================== INPUT UTILITIES ==================
    
    def _get_input(self, prompt: str, color_code: str = None) -> str:
        """Get user input with styled prompt."""
        color = color_code or self._config.g
        return input(f'{self._config.style_box} {prompt}: {color}').strip()
    
    def _get_int_input(self, prompt: str, default: int = 1) -> int:
        """Get integer input with default fallback."""
        try:
            value = int(self._get_input(prompt))
            return value if value > 0 else default
        except ValueError:
            print(f"{self._config.style_box} DEFAULT VALUE: {self._config.r}[{self._config.g}{default}{self._config.r}]")
            return default
    
    def _get_yes_no(self, prompt: str) -> bool:
        """Get yes/no input."""
        response = self._get_input(
            f"{prompt} {self._config.r}[{self._config.g}y{self._config.r}/{self._config.g}n{self._config.r}]"
        ).lower()
        return response in ['y', 'yes', '1']
    
    def _get_uid_list(self) -> List[str]:
        """Get list of UIDs from user input."""
        print(f"{self._config.style_box} PASTE UID LIST (DOUBLE ENTER TO CONTINUE)")
        self._config.linex()
        
        uids = []
        while True:
            line = input().strip()
            if not line:
                break
            uid = line.split('|')[0].strip()
            if uid:
                uids.append(uid)
        
        return uids
    
    def _get_uids_numbered(self, count: int) -> List[str]:
        """Get specified number of UIDs."""
        uids = []
        for i in range(count):
            uid = self._get_input(f"UID {i+1}")
            if '|' in uid:
                uid = uid.split('|')[0]
            uids.append(uid.strip())
        return uids
    
    def _get_urls_to_uids(self, count: int) -> List[str]:
        """Convert Facebook URLs to UIDs."""
        uids = []
        for i in range(count):
            url = self._get_input(f"URL {i+1}")
            if not url.startswith("https://www.facebook.com/"):
                print(f"{self._config.style_box} INVALID URL")
                print(f"{self._config.style_box} EXAMPLE: {self._config.r}'{self._config.g}https://www.facebook.com/...{self._config.r}'")
                continue
            
            uid = self._api.extract_uid_from_url(url)
            if uid:
                print(f"{self._config.style_box} UID: {self._config.g}{uid}")
                uids.append(uid)
            else:
                print(f"{self._config.style_box} UID: {self._config.g}NOT FOUND")
            self._config.linex()
        
        return uids
    
    def _get_separation_links(self) -> List[str]:
        """Get list of separation link prefixes."""
        self._config.linex()
        count = self._get_int_input("HOW MANY LINKS TO SEPARATE")
        self._config.linex()
        print(f'{self._config.style_box} EXAMPLE: {self._config.g}10007 {self._config.w}|{self._config.g} 10008 {self._config.w}|{self._config.g} 61571')
        self._config.linex()
        
        links = []
        for i in range(count):
            link = self._get_input(f"LINK {i+1}")
            if link:
                links.append(link)
        
        return links
    
    # ================== FILE UTILITIES MENU ==================
    
    def _menu_file_mixer(self) -> None:
        """Mix/shuffle lines in a file."""
        self._config.clear_screen()
        self._config.linex()
        filepath = self._get_input("FILE NAME")
        self._config.linex()
        
        try:
            path = Path(filepath)
            if self._file_utils.shuffle_file_lines(path):
                print(f"{self._config.style_box} LINES SHUFFLED AND SAVED TO '{filepath}'")
            else:
                print(f"{self._config.style_box} FAILED TO SHUFFLE FILE")
        except FileNotFoundError:
            print(f"{self._config.style_box} FILE NOT FOUND")
        
        self._config.linex()
        time.sleep(1.5)
    
    def _menu_file_divider(self) -> None:
        """Divide file into parts."""
        self._config.clear_screen()
        self._config.linex()
        filepath = self._get_input("ENTER FILE PATH")
        self._config.linex()
        parts = self._get_int_input("PARTS TO DIVIDE INTO")
        
        try:
            path = Path(filepath)
            output_dir = self._config.ensure_output_dir()
            result_files = self._file_utils.divide_file(path, parts, output_dir)
            
            for i, part_file in enumerate(result_files):
                self._config.linex()
                print(f"{self._config.style_box} PART {self._config.g}{i+1}{self._config.w} SAVED AT: {self._config.g}{part_file}")
        except FileNotFoundError:
            print(f"{self._config.style_box} FILE NOT FOUND")
        except Exception as e:
            print(f"{self._config.style_box} ERROR: {self._config.o}{e}")
        
        self._config.linex()
        input(f"{self._config.style_box} PRESS ENTER TO CONTINUE")
    
    def _menu_duplicate_remover(self) -> None:
        """Remove duplicate lines from file."""
        self._config.clear_screen()
        self._config.linex()
        filepath = self._get_input("FILE NAME")
        
        try:
            path = Path(filepath)
            count = self._config.remove_duplicates_from_file(path)
            self._config.linex()
            print(f"{self._config.style_box} SUCCESSFULLY REMOVED DUPLICATES")
            print(f"{self._config.style_box} UNIQUE LINES: {self._config.g}{count}")
        except FileNotFoundError:
            self._config.linex()
            print(f"{self._config.style_box} FILE NOT FOUND")
        
        self._config.linex()
        time.sleep(2)
    
    def _menu_emoji_remover(self) -> None:
        """Remove emoji/stylish names from file."""
        self._config.clear_screen()
        self._config.linex()
        filepath = self._get_input("ENTER FILE NAME")
        self._config.linex()
        
        try:
            path = Path(filepath)
            count = self._file_utils.remove_emoji_names(path)
            print(f"{self._config.style_box} STYLISH NAME & EMOJI REMOVED")
            print(f"{self._config.style_box} CLEAN LINES: {self._config.g}{count}")
        except FileNotFoundError:
            print(f"{self._config.style_box} FILE NOT FOUND")
        
        self._config.linex()
        time.sleep(1)
    
    def _menu_cutter(self) -> None:
        """Cut or delete lines from file."""
        self._config.clear_screen()
        self._config.linex()
        filepath = self._get_input("ENTER FILE PATH")
        self._config.linex()
        
        try:
            path = Path(filepath)
            with open(path, 'r') as f:
                total_lines = len(f.readlines())
            
            print(f"{self._config.style_box} TOTAL LINES: {total_lines}")
            self._config.linex()
            
            start = self._get_int_input("STARTING LINE NUMBER")
            end = self._get_int_input("ENDING LINE NUMBER")
            self._config.linex()
            
            action = self._get_input(
                f"DELETE OR CUT? {self._config.r}[{self._config.g}delete{self._config.r}/{self._config.g}cut{self._config.r}]"
            ).lower()
            
            cut_file = None
            if action == "cut":
                cut_path = self._get_input("FILE PATH TO SAVE CUT LINES")
                cut_file = Path(cut_path)
            
            if self._file_utils.cut_or_delete_lines(path, start, end, cut_file):
                if action == "cut":
                    print(f"{self._config.style_box} LINES {start} TO {end} CUT AND SAVED")
                else:
                    print(f"{self._config.style_box} LINES {start} TO {end} DELETED")
                print(f"{self._config.style_box} FILE UPDATED: {filepath}")
            else:
                print(f"{self._config.style_box} OPERATION FAILED")
                
        except FileNotFoundError:
            print(f"{self._config.style_box} FILE NOT FOUND")
        
        self._config.linex()
        input(f"{self._config.style_box} PRESS ENTER TO CONTINUE")
    
    def _menu_separator(self) -> None:
        """Separate lines by prefix."""
        self._config.clear_screen()
        self._config.linex()
        filepath = self._get_input("ENTER FILE NAME")
        self._config.linex()
        
        prefixes = self._get_separation_links()
        
        try:
            path = Path(filepath)
            output = self._config.generate_filename("custom_separet")
            
            count = self._file_utils.separate_by_prefix(path, prefixes, output)
            
            self._config.linex()
            if count > 0:
                print(f'{self._config.style_box} FILE SAVED TO: {self._config.g}{output}')
                print(f'{self._config.style_box} MATCHING LINES: {self._config.g}{count}')
            else:
                print(f'{self._config.style_box} NO MATCHING LINES FOUND')
        except FileNotFoundError:
            self._config.linex()
            print(f'{self._config.style_box} FILE NOT FOUND')
        
        self._config.linex()
        time.sleep(2)
    
    def _menu_get_uid(self) -> None:
        """Get UID from Facebook URL."""
        self._config.clear_screen()
        self._config.linex()
        
        while True:
            url = self._get_input("URL (or 'exit' to quit)")
            
            if url.lower() == 'exit':
                break
            
            if not url.startswith("https://www.facebook.com/"):
                self._config.linex()
                print(f"{self._config.style_box} INVALID URL")
                print(f"{self._config.style_box} EXAMPLE: {self._config.r}'{self._config.g}https://www.facebook.com/...{self._config.r}'")
                self._config.linex()
                continue
            
            uid = self._api.extract_uid_from_url(url)
            self._config.linex()
            if uid:
                print(f"{self._config.style_box} UID: {self._config.g}{uid}")
            else:
                print(f"{self._config.style_box} UID: {self._config.g}NOT FOUND")
            self._config.linex()
    
    # ================== LOGIN METHODS ==================
    
    def _do_cookie_login(self) -> bool:
        """Login with cookie."""
        self._config.clear_screen()
        print(f"{self._config.style_box} EXTRACT COOKIE FROM KIWI BROWSER {self._config.r}[{self._config.g}BEST{self._config.r}]{self._config.w}")
        print(f"{self._config.style_box} NO NEED TO HAVE INSTAGRAM CONNECTION")
        print(f"{self._config.style_box} WITH YOUR FACEBOOK ID.")
        self._config.linex()
        print(f"{self._config.style_box} USE {self._config.r}'{self._config.g}sb={self._config.r}'{self._config.w} ADDED VALID COOKIE")
        self._config.linex()
        
        cookie = self._get_input("ENTER COOKIE")
        self._config.linex()
        self._config.open_social("wp")
        
        success, status = self._api.login_with_cookie(cookie)
        
        if success:
            print(f"{self._config.style_box} TOKEN: {self._config.p}{self._api.token[:50]}...")
            self._config.linex()
            self._config.animate(f'{self._config.style_box} COOKIE LOGIN SUCCESSFUL!!')
            self._config.linex()
            time.sleep(1)
            return True
        else:
            self._config.animate(f'{self._config.style_box} CHANGE COOKIES 🍪...!!')
            self._api.logout()
            self._config.linex()
            input(f'{self._config.style_box} PRESS ENTER TO RETRY')
            return False
    
    def _do_id_pass_login(self) -> bool:
        """Login with ID and password."""
        self._config.clear_screen()
        print(f"{self._config.style_box} MAKE SURE YOUR {self._config.g}FACEBOOK{self._config.w} ID ADDED WITH {self._config.g}INSTAGRAM{self._config.w}")
        self._config.linex()
        
        uid = self._get_input("ENTER UID")
        password = self._get_input("ENTER PASSWORD")
        self._config.linex()
        
        success, status = self._api.login_with_credentials(uid, password)
        
        if success:
            print(f'{self._config.style_box} COOKIES: {self._config.g}{self._api.cookie[:50]}...')
            self._config.linex()
            print(f"{self._config.style_box} TOKEN: {self._config.p}{self._api.token[:50]}...")
            self._config.linex()
            self._config.animate(f'{self._config.style_box} LOGIN SUCCESSFUL!!')
            self._config.linex()
            time.sleep(1)
            return True
        elif status == "CHECKPOINT":
            input(f'{self._config.style_box} ACCOUNT ON CHECKPOINT')
            return False
        else:
            print(f"{self._config.style_box} {status}")
            self._config.linex()
            input(f'{self._config.style_box} INCORRECT USERNAME OR PASSWORD 🔑')
            return False
    
    def _validate_current_login(self) -> bool:
        """Validate saved credentials."""
        if not self._api.is_logged_in:
            return False
        
        try:
            success, friends = self._api.validate_login()
            
            if not success:
                self._api.logout()
            
            return success
        except Exception as e:
            print(f"{self._config.style_box} VALIDATION ERROR: {self._config.o}{e}")
            return False
    
    # ================== DUMP METHODS ==================
    
    def _get_output_filename(self) -> Path:
        """Get output filename from user."""
        filename = self._get_input("FILE NAME")
        
        if self._config.platform.is_termux:
            if not filename.startswith("/sdcard/"):
                self._config.linex()
                print(f'{self._config.style_box} {self._config.r}"{self._config.g}/sdcard/{self._config.r}"{self._config.w} NOT FOUND')
                new_file = self._config.generate_filename()
                print(f'{self._config.style_box} NEW FILE: {self._config.r}"{self._config.g}{new_file}{self._config.r}"')
                return new_file
            return Path(filename)
        else:
            return self._config.get_output_path(Path(filename).name) if "/" in filename or "\\" in filename else Path(filename)
    
    def _get_uid_input_type(self) -> str:
        """Get UID input type selection."""
        print(f"{self._config.style_box} UID INPUT {self._config.r}[{self._config.g}1{self._config.r}]{self._config.w} LIST {self._config.r}[{self._config.g}2{self._config.r}]{self._config.w} NUMBER {self._config.r}[{self._config.g}3{self._config.r}]{self._config.w} URL")
        self._config.linex()
        choice = self._get_input("SELECT").lower()
        return choice if choice in ['1', '2', '3', 'a', 'b', 'c'] else '1'
    
    def _collect_uids(self, input_type: str) -> List[str]:
        """Collect UIDs based on input type."""
        self._config.linex()
        
        if input_type in ['1', 'a']:
            return self._get_uid_list()
        elif input_type in ['2', 'b']:
            count = self._get_int_input("UID LIMIT")
            self._config.linex()
            return self._get_uids_numbered(count)
        elif input_type in ['3', 'c']:
            count = self._get_int_input("URL LIMIT")
            self._config.linex()
            return self._get_urls_to_uids(count)
        
        return []
    
    def _progress_display(self, message: str) -> None:
        """Display progress message."""
        color = self._config.random_color()
        sys.stdout.write(f"\r{self._config.style_box} {color}{message}{self._config.w}")
        sys.stdout.flush()
    
    async def _do_unlimited_dump(self) -> None:
        """Unlimited dump - friends + followers."""
        self._config.clear_screen()
        print(f"{self._config.style_box}━━━━━━━━━━━━━━━━━━━━{self._config.r}[{self._config.g}ACTIVE{self._config.r}]{self._config.w}━━━━━━━━━━━━━━━━━━━━{self._config.style_box}")
        self._config.linex()
        
        if not self._api.is_logged_in:
            self._config.animate(f'{self._config.style_box} PLEASE LOGIN FIRST')
            return
        
        output_file = self._get_output_filename()
        self._config.linex()
        
        input_type = self._get_uid_input_type()
        uids = self._collect_uids(input_type)
        
        if not uids:
            print(f"{self._config.style_box} NO UIDS PROVIDED")
            return
        
        self._config.linex()
        separate = self._get_yes_no("SEPARATE LINKS")
        
        sep_prefixes = None
        unsep_file = None
        
        if separate:
            sep_prefixes = self._get_separation_links()
            unsep_file = self._config.generate_filename("unseparet_ids")
        
        self._config.linex()
        print(f'{self._config.style_box} TOTAL UIDS: {self._config.g}{len(uids)}')
        print(f'{self._config.style_box} USE CTRL+Z TO STOP')
        self._config.open_social("tg")
        self._config.linex()
        
        main_count, unsep_count = await self._api.dump_unlimited(
            uids=uids,
            output_file=output_file,
            unsep_file=unsep_file,
            sep_prefixes=sep_prefixes,
            progress_callback=self._progress_display
        )
        
        print()
        self._config.linex()
        print(f'{self._config.style_box} DUPLICATES REMOVED')
        self._config.linex()
        print(f'{self._config.style_box} MAIN FILE: \n{self._config.style_box} {self._config.r}>{self._config.g}>{self._config.r}> {self._config.g}{output_file}')
        print(f'{self._config.style_box} EXTRACTED: {self._config.g}{main_count}')
        
        if separate and unsep_file:
            self._config.linex()
            print(f'{self._config.style_box} UNSEPARATE FILE: \n{self._config.style_box} {self._config.r}>{self._config.g}>{self._config.r}> {self._config.g}{unsep_file}')
            print(f'{self._config.style_box} EXTRACTED: {self._config.g}{unsep_count}')
        
        self._config.linex()
        input(f'{self._config.style_box} PRESS ENTER TO EXIT')
    
    async def _do_simple_dump(self) -> None:
        """Simple dump - friends list only."""
        self._config.clear_screen()
        print(f"{self._config.style_box}━━━━━━━━━{self._config.r}[{self._config.g}SIMPLE DUMP ACTIVATED{self._config.r}]{self._config.w}━━━━━━━━━{self._config.style_box}")
        self._config.linex()
        
        if not self._api.is_logged_in:
            self._config.animate(f'{self._config.style_box} PLEASE LOGIN FIRST')
            return
        
        output_file = self._get_output_filename()
        self._config.linex()
        
        input_type = self._get_uid_input_type()
        uids = self._collect_uids(input_type)
        
        if not uids:
            print(f"{self._config.style_box} NO UIDS PROVIDED")
            return
        
        self._config.linex()
        print(f'{self._config.style_box} TOTAL UIDS: {self._config.g}{len(uids)}')
        print(f'{self._config.style_box} USE CTRL+Z TO STOP')
        self._config.linex()
        
        count = await self._api.dump_simple(
            uids=uids,
            output_file=output_file,
            progress_callback=self._progress_display
        )
        
        print()
        self._config.linex()
        print(f'{self._config.style_box} FILE: {self._config.g}{output_file}')
        print(f'{self._config.style_box} EXTRACTED: {self._config.g}{count}')
        self._config.linex()
        input(f'{self._config.style_box} PRESS ENTER TO EXIT')
    
    # ================== MAIN MENUS ==================
    
    def _main_login_menu(self) -> None:
        """Main login menu."""
        while True:
            self._config.clear_screen()
            self._config.open_social("wp")
            
            print(f"{self._config.box('A')}{self._config.g} LOGIN{self._config.w} TOOL {self._config.g}WITH {self._config.w}COOKIE")
            print(f"{self._config.box('B')} LOGIN{self._config.g} TOOL {self._config.w}WITH {self._config.g}ID {self._config.w}PASSWORD")
            print(f"{self._config.box('C')}{self._config.g} FILE {self._config.w}MIXER ")
            print(f"{self._config.box('D')} FILE {self._config.g}DIVIDER ")
            print(f"{self._config.box('E')}{self._config.g} REMOVE {self._config.w}DUPLICATES{self._config.g} LINES ")
            print(f"{self._config.box('F')} REMOVE {self._config.g}STYLISH {self._config.r}&{self._config.g} EMOJI {self._config.g}NAME ID")
            print(f"{self._config.box('G')}{self._config.g} CUT {self._config.w}OR {self._config.g}DELETE{self._config.w} FILE {self._config.g}LINES ")
            print(f"{self._config.box('H')} SEPARATE {self._config.g}LINKS {self._config.w}FROM {self._config.g}FILE")
            print(f"{self._config.box('I')}{self._config.g} FACEBOOK {self._config.w}PROFILE {self._config.g}URL {self._config.w}TO {self._config.g}UID")
            print(f"{self._config.box('J')} JOIN {self._config.g}TELEGRAM {self._config.w}CHANNEL")
            print(f"{self._config.box('K')}{self._config.g} JOIN {self._config.w}WHATSAPP {self._config.g}GROUP")
            print(f"{self._config.box('L')}{self._config.r} EXIT FROM TOOL{self._config.g}....✅")
            self._config.linex()
            
            choice = self._get_input("SELECT").upper()
            
            if choice in ['A', '1', '01']:
                if self._do_cookie_login():
                    if self._validate_current_login():
                        return self._home_menu()
                    else:
                        self._config.animate(f'{self._config.style_box} VALIDATION FAILED, TRY AGAIN')
            elif choice in ['B', '2', '02']:
                if self._do_id_pass_login():
                    if self._validate_current_login():
                        return self._home_menu()
            elif choice in ['C', '3', '03']:
                self._menu_file_mixer()
            elif choice in ['D', '4', '04']:
                self._menu_file_divider()
            elif choice in ['E', '5', '05']:
                self._menu_duplicate_remover()
            elif choice in ['F', '6', '06']:
                self._menu_emoji_remover()
            elif choice in ['G', '7', '07']:
                self._menu_cutter()
            elif choice in ['H', '8', '08']:
                self._menu_separator()
            elif choice in ['I', '9', '09']:
                self._menu_get_uid()
            elif choice in ['J', '10']:
                self._config.open_social("tg")
            elif choice in ['K', '11']:
                self._config.open_social("wp")
            elif choice in ['L', '12']:
                self._config.linex()
                self._config.open_social("wp")
                sys.exit(0)
            else:
                self._config.linex()
                self._config.animate(f"{self._config.style_box} SELECT CORRECT OPTION....!!")
                time.sleep(2)
    
    def _home_menu(self) -> None:
        """Home menu after login."""
        while True:
            self._config.clear_screen()
            self._config.open_social("tg")
            
            print(f"{self._config.style_box}━━━━━━━━━━━━━━━━━━━━{self._config.r}[{self._config.g}ACTIVE{self._config.r}]{self._config.w}━━━━━━━━━━━━━━━━━━━━{self._config.style_box}")
            self._config.linex()
            print(f"{self._config.box('A')}{self._config.g} UNLIMITED{self._config.w} IDS EXTRACT {self._config.r}[{self._config.g}FRIENDS {self._config.r}+{self._config.g} FOLLOWERS{self._config.r}]")
            print(f"{self._config.box('B')}{self._config.r} EXTRA {self._config.g}UTILITY DUMP {self._config.r}[{self._config.g}ONLY SEPARATE SERIES{self._config.r}]")
            print(f"{self._config.box('C')}{self._config.g} SIMPLE DUMP {self._config.r}[{self._config.g}FRIENDS LIST ONLY{self._config.r}]")
            self._config.linex()
            print(f"{self._config.box('D')} FILE {self._config.g}DIVIDER ")
            print(f"{self._config.box('E')}{self._config.g} FILE {self._config.w}MIXER ")
            print(f"{self._config.box('F')} REMOVE {self._config.g}DUPLICATES{self._config.w} LINES ")
            print(f"{self._config.box('G')}{self._config.g} REMOVE {self._config.w}STYLISH {self._config.r}&{self._config.w} EMOJI {self._config.g}NAME ID")
            print(f"{self._config.box('H')} CUT{self._config.g} OR {self._config.w}DELETE{self._config.g} LINES ")
            print(f"{self._config.box('I')}{self._config.g} SEPARATE {self._config.w}LINKS {self._config.g}FROM {self._config.w}FILE")
            print(f"{self._config.box('J')} CONTACT {self._config.g}ADMIN ")
            print(f"{self._config.box('K')}{self._config.r} LOGOUT {self._config.w}COOKIE ")
            self._config.linex()
            
            choice = self._get_input("SELECT").upper()
            
            if choice in ['A', '1', '01']:
                self._config.open_social("wp")
                asyncio.run(self._do_unlimited_dump())
            elif choice in ['B', '2', '02']:
                self._config.open_social("wp")
                asyncio.run(self._do_unlimited_dump())
            elif choice in ['C', '3', '03']:
                self._config.open_social("wp")
                asyncio.run(self._do_simple_dump())
            elif choice in ['D', '4', '04']:
                self._menu_file_divider()
            elif choice in ['E', '5', '05']:
                self._menu_file_mixer()
            elif choice in ['F', '6', '06']:
                self._menu_duplicate_remover()
            elif choice in ['G', '7', '07']:
                self._menu_emoji_remover()
            elif choice in ['H', '8', '08']:
                self._menu_cutter()
            elif choice in ['I', '9', '09']:
                self._menu_separator()
            elif choice in ['J', '10']:
                self._config.open_social("fb")
            elif choice in ['K', '11']:
                self._api.logout()
                self._config.linex()
                self._config.animate(f'{self._config.style_box} SUCCESSFULLY REMOVED COOKIE')
                return self._main_login_menu()
            else:
                self._config.linex()
                self._config.animate(f"{self._config.style_box} SELECT CORRECT OPTION....!!")
                time.sleep(1)
    
    # ================== ENTRY POINT ==================
    
    def run(self) -> None:
        """Main entry point - run the application."""
        try:
            # Initialize
            self._config.initialize()
            self._config.setup_signal_handlers(lambda: self._config.open_social("git"))
            
            # Check storage on Termux
            if self._config.platform.is_termux:
                if not self._config.check_storage_permission():
                    sys.exit(1)
            
            # Ensure output directory exists
            self._config.ensure_output_dir()
            
            # Check for existing valid login
            if self._validate_current_login():
                self._config.animate(f'{self._config.style_box} RESTORING PREVIOUS SESSION...')
                time.sleep(1)
                self._home_menu()
            else:
                self._main_login_menu()
                
        except KeyboardInterrupt:
            self._config.linex()
            print(f"\n{self._config.style_box} EXITING...")
            sys.exit(0)
        except Exception as e:
            print(f"{self._config.style_box} ERROR: {self._config.o}{e}")
            sys.exit(1)


# ================== MAIN ==================

def main() -> None:
    """Application entry point."""
    app = App()
    app.run()


if __name__ == "__main__":
    main()

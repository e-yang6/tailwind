"""
tailwind
View player info and auto-lock agents in Valorant.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import time
import os
from tailwind_core import TailwindCore


class tailwind:
    def __init__(self):
        self.core = TailwindCore()
        self.auto_lock_running = False
        self.auto_lock_thread = None
        
        # Create main window
        self.root = tk.Tk()
        self.root.title("tailwind")
        self.root.geometry("600x700")
        self.root.resizable(True, True)
        self.root.minsize(500, 600)
        
        # Set window icon
        self.set_icon()
        
        # Modern dark theme with good contrast
        self.colors = {
            "bg": "#121212",
            "surface": "#1e1e1e",
            "surface_light": "#2d2d2d",
            "border": "#3d3d3d",
            "primary": "#6366f1",      # Indigo
            "primary_hover": "#818cf8",
            "secondary": "#ec4899",     # Pink
            "text": "#f5f5f5",
            "text_secondary": "#a3a3a3",
            "success": "#22c55e",
            "warning": "#eab308",
            "error": "#ef4444",
        }
        
        self.root.configure(bg=self.colors["bg"])
        self.setup_styles()
        self.create_widgets()
    
    def set_icon(self):
        """Set the window icon from icon.png if it exists."""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(script_dir, "icon.png")
        ico_path = os.path.join(script_dir, "icon.ico")
        
        # Try .ico file first (Windows native)
        if os.path.exists(ico_path):
            try:
                self.root.iconbitmap(ico_path)
                return
            except Exception:
                pass
        
        # Try .png with Pillow
        if os.path.exists(icon_path):
            try:
                from PIL import Image, ImageTk, ImageOps
                img = Image.open(icon_path)
                # Invert colors (white becomes black, etc.)
                if img.mode == 'RGBA':
                    # Handle transparency: only invert RGB, keep alpha
                    r, g, b, a = img.split()
                    rgb = Image.merge('RGB', (r, g, b))
                    rgb = ImageOps.invert(rgb)
                    r, g, b = rgb.split()
                    img = Image.merge('RGBA', (r, g, b, a))
                else:
                    img = ImageOps.invert(img.convert('RGB'))
                # Resize if too large
                img = img.resize((64, 64), Image.Resampling.LANCZOS)
                icon = ImageTk.PhotoImage(img)
                self.root.iconphoto(True, icon)
                self._icon = icon
                return
            except ImportError:
                pass  # Pillow not installed
            except Exception:
                pass
        
        # Fallback: try native PhotoImage
        if os.path.exists(icon_path):
            try:
                icon = tk.PhotoImage(file=icon_path)
                self.root.iconphoto(True, icon)
                self._icon = icon
            except Exception:
                pass
        
    def setup_styles(self):
        """Configure ttk styles."""
        style = ttk.Style()
        style.theme_use("clam")
        
        # Frame
        style.configure("TFrame", background=self.colors["bg"])
        style.configure("Card.TFrame", background=self.colors["surface"])
        
        # Labels
        style.configure("TLabel", 
                       background=self.colors["bg"], 
                       foreground=self.colors["text"],
                       font=("Segoe UI", 11))
        style.configure("Title.TLabel",
                       background=self.colors["bg"],
                       foreground=self.colors["text"],
                       font=("Segoe UI", 24, "bold"))
        style.configure("Subtitle.TLabel",
                       background=self.colors["bg"],
                       foreground=self.colors["text_secondary"],
                       font=("Segoe UI", 11))
        style.configure("Card.TLabel",
                       background=self.colors["surface"],
                       foreground=self.colors["text"],
                       font=("Segoe UI", 11))
        style.configure("CardTitle.TLabel",
                       background=self.colors["surface"],
                       foreground=self.colors["text"],
                       font=("Segoe UI", 12, "bold"))
        
        # Buttons
        style.configure("TButton",
                       background=self.colors["surface_light"],
                       foreground=self.colors["text"],
                       font=("Segoe UI", 10),
                       padding=(16, 10),
                       borderwidth=0)
        style.map("TButton",
                 background=[("active", self.colors["border"]),
                            ("disabled", self.colors["surface"])])
        style.map("TButton",
                 foreground=[("disabled", self.colors["text_secondary"])])
        
        style.configure("Primary.TButton",
                       background=self.colors["primary"],
                       foreground="#ffffff",
                       font=("Segoe UI", 10, "bold"),
                       padding=(16, 10))
        style.map("Primary.TButton",
                 background=[("active", self.colors["primary_hover"]),
                            ("disabled", self.colors["surface_light"])])
        
        style.configure("Secondary.TButton",
                       background=self.colors["secondary"],
                       foreground="#ffffff",
                       font=("Segoe UI", 10, "bold"),
                       padding=(16, 10))
        style.map("Secondary.TButton",
                 background=[("active", "#f472b6"),
                            ("disabled", self.colors["surface_light"])])
        
        # Combobox
        style.configure("TCombobox",
                       fieldbackground=self.colors["surface_light"],
                       background=self.colors["surface_light"],
                       foreground=self.colors["text"],
                       arrowcolor=self.colors["text"],
                       padding=8)
        style.map("TCombobox",
                 fieldbackground=[("readonly", self.colors["surface_light"])],
                 foreground=[("readonly", self.colors["text"])])
        
        # Configure combobox dropdown
        self.root.option_add("*TCombobox*Listbox.background", self.colors["surface"])
        self.root.option_add("*TCombobox*Listbox.foreground", self.colors["text"])
        self.root.option_add("*TCombobox*Listbox.selectBackground", self.colors["primary"])
        self.root.option_add("*TCombobox*Listbox.selectForeground", "#ffffff")
        
    def create_card(self, parent, **kwargs):
        """Create a card-style frame."""
        card = tk.Frame(parent, 
                       bg=self.colors["surface"],
                       highlightbackground=self.colors["border"],
                       highlightthickness=1,
                       **kwargs)
        return card
        
    def create_widgets(self):
        """Create all GUI widgets."""
        # Main container with padding
        main_frame = tk.Frame(self.root, bg=self.colors["bg"])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=24, pady=24)
        
        # Header
        header_frame = tk.Frame(main_frame, bg=self.colors["bg"])
        header_frame.pack(fill=tk.X, pady=(0, 24))
        
        # Title row
        title_row = tk.Frame(header_frame, bg=self.colors["bg"])
        title_row.pack(fill=tk.X)
        
        title_label = tk.Label(title_row, text="tailwind",
                              font=("Segoe UI", 24, "bold"),
                              fg=self.colors["text"],
                              bg=self.colors["bg"])
        title_label.pack(side=tk.LEFT)
        
        # Status indicator
        self.status_frame = tk.Frame(title_row, bg=self.colors["bg"])
        self.status_frame.pack(side=tk.RIGHT)
        
        self.status_dot = tk.Canvas(self.status_frame, width=10, height=10, 
                                    bg=self.colors["bg"], highlightthickness=0)
        self.status_dot.pack(side=tk.LEFT, padx=(0, 8))
        self.status_dot.create_oval(1, 1, 9, 9, fill=self.colors["error"], outline="")
        
        self.status_label = tk.Label(self.status_frame, 
                                    text="not connected",
                                    font=("Segoe UI", 11),
                                    fg=self.colors["text_secondary"],
                                    bg=self.colors["bg"])
        self.status_label.pack(side=tk.LEFT)
        
        # Connect button card
        connect_card = self.create_card(main_frame)
        connect_card.pack(fill=tk.X, pady=(0, 16))
        
        connect_inner = tk.Frame(connect_card, bg=self.colors["surface"])
        connect_inner.pack(fill=tk.X, padx=16, pady=16)
        
        connect_text = tk.Label(connect_inner, 
                               text="connect to valorant to get started",
                               font=("Segoe UI", 11),
                               fg=self.colors["text_secondary"],
                               bg=self.colors["surface"])
        connect_text.pack(side=tk.LEFT)
        
        self.connect_btn = ttk.Button(connect_inner, text="connect",
                                      command=self.connect, style="Primary.TButton")
        self.connect_btn.pack(side=tk.RIGHT)
        
        # Players card
        players_card = self.create_card(main_frame)
        players_card.pack(fill=tk.X, pady=(0, 16))
        
        players_inner = tk.Frame(players_card, bg=self.colors["surface"])
        players_inner.pack(fill=tk.X, padx=16, pady=16)
        
        players_title = tk.Label(players_inner, text="view players",
                                font=("Segoe UI", 12, "bold"),
                                fg=self.colors["text"],
                                bg=self.colors["surface"])
        players_title.pack(anchor=tk.W, pady=(0, 12))
        
        players_btns = tk.Frame(players_inner, bg=self.colors["surface"])
        players_btns.pack(fill=tk.X)
        
        self.pregame_btn = ttk.Button(players_btns, text="pre-game",
                                      command=self.view_pregame)
        self.pregame_btn.pack(side=tk.LEFT, padx=(0, 8))
        
        self.ingame_btn = ttk.Button(players_btns, text="current game",
                                     command=self.view_current_game)
        self.ingame_btn.pack(side=tk.LEFT)
        
        # Agent Lock card
        agent_card = self.create_card(main_frame)
        agent_card.pack(fill=tk.X, pady=(0, 16))
        
        agent_inner = tk.Frame(agent_card, bg=self.colors["surface"])
        agent_inner.pack(fill=tk.X, padx=16, pady=16)
        
        agent_title = tk.Label(agent_inner, text="agent lock",
                              font=("Segoe UI", 12, "bold"),
                              fg=self.colors["text"],
                              bg=self.colors["surface"])
        agent_title.pack(anchor=tk.W, pady=(0, 12))
        
        agent_row = tk.Frame(agent_inner, bg=self.colors["surface"])
        agent_row.pack(fill=tk.X)
        
        self.agent_var = tk.StringVar()
        agents = sorted(self.core.agents.values())
        self.agent_combo = ttk.Combobox(agent_row, textvariable=self.agent_var,
                                        values=agents, state="readonly", width=18,
                                        font=("Segoe UI", 10))
        self.agent_combo.pack(side=tk.LEFT, padx=(0, 8))
        self.agent_combo.set("Jett")
        
        self.select_btn = ttk.Button(agent_row, text="hover", command=self.select_agent)
        self.select_btn.pack(side=tk.LEFT, padx=(0, 8))
        
        self.lock_btn = ttk.Button(agent_row, text="lock", command=self.lock_agent)
        self.lock_btn.pack(side=tk.LEFT, padx=(0, 8))
        
        self.autolock_btn = ttk.Button(agent_row, text="auto-lock", 
                                       command=self.toggle_autolock,
                                       style="Secondary.TButton")
        self.autolock_btn.pack(side=tk.LEFT)
        
        # Output card
        output_card = self.create_card(main_frame)
        output_card.pack(fill=tk.BOTH, expand=True)
        
        output_inner = tk.Frame(output_card, bg=self.colors["surface"])
        output_inner.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)
        
        output_header = tk.Frame(output_inner, bg=self.colors["surface"])
        output_header.pack(fill=tk.X, pady=(0, 12))
        
        output_title = tk.Label(output_header, text="output",
                               font=("Segoe UI", 12, "bold"),
                               fg=self.colors["text"],
                               bg=self.colors["surface"])
        output_title.pack(side=tk.LEFT)
        
        clear_btn = ttk.Button(output_header, text="clear", 
                              command=self.clear_output)
        clear_btn.pack(side=tk.RIGHT)
        
        # Output text area with custom scrollbar
        output_container = tk.Frame(output_inner, bg=self.colors["surface_light"])
        output_container.pack(fill=tk.BOTH, expand=True)
        
        self.output = tk.Text(
            output_container,
            wrap=tk.WORD,
            font=("Consolas", 10),
            bg=self.colors["surface_light"],
            fg=self.colors["text"],
            insertbackground=self.colors["text"],
            selectbackground=self.colors["primary"],
            relief=tk.FLAT,
            padx=12,
            pady=12,
            borderwidth=0
        )
        
        scrollbar = tk.Scrollbar(output_container, command=self.output.yview,
                                bg=self.colors["surface_light"],
                                troughcolor=self.colors["surface_light"],
                                activebackground=self.colors["border"])
        self.output.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.output.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configure text tags
        self.output.tag_configure("success", foreground=self.colors["success"])
        self.output.tag_configure("warning", foreground=self.colors["warning"])
        self.output.tag_configure("error", foreground=self.colors["error"])
        self.output.tag_configure("info", foreground=self.colors["text_secondary"])
        self.output.tag_configure("header", foreground=self.colors["primary"], 
                                  font=("Consolas", 11, "bold"))
        self.output.tag_configure("highlight", foreground=self.colors["secondary"])
        
        # Initial state
        self.set_buttons_state(False)
        
    def set_buttons_state(self, enabled: bool):
        """Enable or disable action buttons."""
        state = "normal" if enabled else "disabled"
        self.pregame_btn.configure(state=state)
        self.ingame_btn.configure(state=state)
        self.select_btn.configure(state=state)
        self.lock_btn.configure(state=state)
        self.autolock_btn.configure(state=state)
        self.agent_combo.configure(state="readonly" if enabled else "disabled")
        
    def log(self, message: str, tag: str = None):
        """Add a message to the output."""
        self.output.configure(state=tk.NORMAL)
        if tag:
            self.output.insert(tk.END, message + "\n", tag)
        else:
            self.output.insert(tk.END, message + "\n")
        self.output.see(tk.END)
        self.output.configure(state=tk.DISABLED)
        
    def clear_output(self):
        """Clear the output text area."""
        self.output.configure(state=tk.NORMAL)
        self.output.delete(1.0, tk.END)
        self.output.configure(state=tk.DISABLED)
        
    def update_status(self, connected: bool, message: str = None):
        """Update the connection status indicator."""
        if connected:
            self.status_dot.delete("all")
            self.status_dot.create_oval(1, 1, 9, 9, fill=self.colors["success"], outline="")
            self.status_label.configure(text=message or "connected", fg=self.colors["success"])
            self.connect_btn.configure(text="reconnect")
        else:
            self.status_dot.delete("all")
            self.status_dot.create_oval(1, 1, 9, 9, fill=self.colors["error"], outline="")
            self.status_label.configure(text=message or "not connected", fg=self.colors["text_secondary"])
            self.connect_btn.configure(text="connect")
            
    def connect(self):
        """Connect to Valorant."""
        self.log("connecting...", "info")
        self.connect_btn.configure(state="disabled")
        
        def do_connect():
            success = self.core.initialize()
            self.root.after(0, lambda: self.on_connect_complete(success))
            
        thread = threading.Thread(target=do_connect, daemon=True)
        thread.start()
        
    def on_connect_complete(self, success: bool):
        """Handle connection result."""
        self.connect_btn.configure(state="normal")
        
        if success:
            self.update_status(True, f"connected ({self.core.region})")
            self.set_buttons_state(True)
            self.log("connected", "success")
            self.log(f"region: {self.core.region}", "info")
        else:
            self.update_status(False, "failed")
            self.set_buttons_state(False)
            self.log("connection failed. is valorant running?", "error")
            
    def view_pregame(self):
        """View pre-game players."""
        def do_fetch():
            match_id = self.core.get_pregame_player()
            if not match_id:
                self.root.after(0, lambda: self.log("not in pre-game.", "warning"))
                return
                
            match_data = self.core.get_pregame_match(match_id)
            if not match_data:
                self.root.after(0, lambda: self.log("failed to get match data.", "error"))
                return
                
            self.root.after(0, lambda: self.display_pregame(match_data))
            
        thread = threading.Thread(target=do_fetch, daemon=True)
        thread.start()
        
    def display_pregame(self, match_data: dict):
        """Display pre-game info."""
        self.clear_output()
        
        ally_team = match_data.get("AllyTeam", {})
        team_id = ally_team.get("TeamID", "Unknown")
        
        if team_id == "Blue":
            side = "defenders"
        elif team_id == "Red":
            side = "attackers"
        else:
            side = team_id
            
        map_name = match_data.get("MapID", "Unknown").split("/")[-1]
        
        self.log("pre-game", "header")
        self.log(f"map: {map_name}  •  side: {side}", "info")
        self.log("")
        
        players = ally_team.get("Players", [])
        puuids = [p.get("Subject") for p in players]
        player_names = self.core.get_player_names(puuids)
        
        self.log("your team", "highlight")
        
        for player in players:
            puuid = player.get("Subject")
            agent_id = player.get("CharacterID", "")
            is_locked = player.get("CharacterSelectionState") == "locked"
            
            name_info = player_names.get(puuid, {"full": "Unknown"})
            name = name_info.get("full", "Unknown")
            
            is_me = puuid == self.core.puuid
            me_tag = " (you)" if is_me else ""
            
            identity = player.get("PlayerIdentity", {})
            incognito = identity.get("Incognito", False)
            incog_tag = " [hidden]" if incognito else ""
            
            if agent_id:
                agent_name = self.core.get_agent_name(agent_id)
                status = "locked" if is_locked else "selecting"
                agent_info = f"  {agent_name} ({status})"
            else:
                agent_info = "  No agent"
                
            tag = "success" if is_me else None
            self.log(f"{name}{me_tag}{incog_tag}", tag)
            self.log(agent_info, "info")
            
    def view_current_game(self):
        """View current game players."""
        def do_fetch():
            match_id = self.core.get_current_game_player()
            if not match_id:
                self.root.after(0, lambda: self.log("not in a game.", "warning"))
                return
                
            match_data = self.core.get_current_game_match(match_id)
            if not match_data:
                self.root.after(0, lambda: self.log("failed to get match data.", "error"))
                return
                
            self.root.after(0, lambda: self.display_current_game(match_data))
            
        thread = threading.Thread(target=do_fetch, daemon=True)
        thread.start()
        
    def display_current_game(self, match_data: dict):
        """Display current game info."""
        self.clear_output()
        
        map_name = match_data.get("MapID", "Unknown").split("/")[-1]
        
        self.log("current game", "header")
        self.log(f"map: {map_name}", "info")
        self.log("")
        
        players = match_data.get("Players", [])
        all_puuids = [p.get("Subject") for p in players]
        player_names = self.core.get_player_names(all_puuids)
        
        my_team_id = None
        for p in players:
            if p.get("Subject") == self.core.puuid:
                my_team_id = p.get("TeamID")
                break
                
        my_team = [p for p in players if p.get("TeamID") == my_team_id]
        enemy_team = [p for p in players if p.get("TeamID") != my_team_id]
        
        def print_team(team_players, label, is_ally):
            self.log(label, "highlight" if is_ally else "error")
            
            for player in team_players:
                puuid = player.get("Subject")
                agent_id = player.get("CharacterID", "")
                
                name_info = player_names.get(puuid, {"full": "Unknown"})
                name = name_info.get("full", "Unknown")
                
                is_me = puuid == self.core.puuid
                me_tag = " (you)" if is_me else ""
                
                identity = player.get("PlayerIdentity", {})
                incognito = identity.get("Incognito", False)
                incog_tag = " [hidden]" if incognito else ""
                
                agent_name = self.core.get_agent_name(agent_id) if agent_id else "Unknown"
                
                player_tag = "success" if is_me else None
                self.log(f"{name}{me_tag}{incog_tag}", player_tag)
                self.log(f"  {agent_name}", "info")
            self.log("")
                
        print_team(my_team, "your team", True)
        print_team(enemy_team, "enemy team", False)
        
    def select_agent(self):
        """Select (hover) an agent."""
        agent_name = self.agent_var.get()
        if not agent_name:
            self.log("select an agent first.", "warning")
            return
            
        def do_select():
            agent_id = self.core.get_agent_id(agent_name)
            match_id = self.core.get_pregame_player()
            
            if not match_id:
                self.root.after(0, lambda: self.log("not in pre-game.", "warning"))
                return
                
            if self.core.select_agent(match_id, agent_id):
                self.root.after(0, lambda: self.log(f"hovering {agent_name}", "success"))
            else:
                self.root.after(0, lambda: self.log(f"failed to select {agent_name}", "error"))
                
        thread = threading.Thread(target=do_select, daemon=True)
        thread.start()
        
    def lock_agent(self):
        """Lock an agent immediately."""
        agent_name = self.agent_var.get()
        if not agent_name:
            self.log("select an agent first.", "warning")
            return
            
        def do_lock():
            agent_id = self.core.get_agent_id(agent_name)
            match_id = self.core.get_pregame_player()
            
            if not match_id:
                self.root.after(0, lambda: self.log("not in pre-game.", "warning"))
                return
                
            self.core.select_agent(match_id, agent_id)
            time.sleep(0.1)
            
            if self.core.lock_agent(match_id, agent_id):
                self.root.after(0, lambda: self.log(f"locked {agent_name}", "success"))
            else:
                self.root.after(0, lambda: self.log(f"failed to lock {agent_name}", "error"))
                
        thread = threading.Thread(target=do_lock, daemon=True)
        thread.start()
        
    def toggle_autolock(self):
        """Toggle auto-lock mode."""
        if self.auto_lock_running:
            self.auto_lock_running = False
            self.autolock_btn.configure(text="auto-lock")
            self.log("auto-lock off", "warning")
        else:
            agent_name = self.agent_var.get()
            if not agent_name:
                self.log("select an agent first.", "warning")
                return
                
            self.auto_lock_running = True
            self.autolock_btn.configure(text="stop")
            self.log(f"auto-lock on: {agent_name}", "success")
            self.log("waiting for pre-game...", "info")
            
            def auto_lock_loop():
                agent_id = self.core.get_agent_id(agent_name)
                
                while self.auto_lock_running:
                    match_id = self.core.get_pregame_player()
                    
                    if match_id:
                        self.root.after(0, lambda: self.log("pre-game found!", "success"))
                        
                        self.core.select_agent(match_id, agent_id)
                        time.sleep(0.1)
                        
                        if self.core.lock_agent(match_id, agent_id):
                            self.root.after(0, lambda: self.log(f"locked {agent_name}", "success"))
                        else:
                            self.root.after(0, lambda: self.log(f"failed - may be taken", "error"))
                            
                        self.auto_lock_running = False
                        self.root.after(0, lambda: self.autolock_btn.configure(text="auto-lock"))
                        break
                        
                    time.sleep(1)
                    
            self.auto_lock_thread = threading.Thread(target=auto_lock_loop, daemon=True)
            self.auto_lock_thread.start()
            
    def run(self):
        """Run the GUI main loop."""
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - self.root.winfo_width()) // 2
        y = (self.root.winfo_screenheight() - self.root.winfo_height()) // 2
        self.root.geometry(f"+{x}+{y}")
        
        self.log("tailwind", "header")
        self.log("connect to valorant to get started.", "info")
        self.log("")
        
        self.root.mainloop()


def main():
    app = tailwind()
    app.run()


if __name__ == "__main__":
    main()

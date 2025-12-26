"""
tailwind core
valorant api wrapper for player info and auto-lock.
"""

import requests
import urllib3
import base64
import json
import os
import time
import sys
from typing import Optional, Dict, Any, List

# Disable SSL warnings for local API
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class TailwindCore:
    def __init__(self):
        self.lockfile_path = os.path.join(
            os.environ.get("LOCALAPPDATA", ""),
            "Riot Games",
            "Riot Client",
            "Config",
            "lockfile"
        )
        self.local_port = None
        self.local_password = None
        self.local_headers = None
        self.puuid = None
        self.region = None
        self.shard = None
        self.entitlements_token = None
        self.access_token = None
        self.client_version = None
        
        # Agent UUID to name mapping
        self.agents = {
            "5f8d3a7f-467b-97f3-062c-13acf203c006": "Breach",
            "f94c3b30-42be-e959-889c-5aa313dba261": "Raze",
            "6f2a04ca-43e0-be17-7f36-b3908627744d": "Skye",
            "117ed9e3-49f3-6512-3ccf-0cada7e3823b": "Cypher",
            "320b2a48-4d9b-a075-30f1-1f93a9b638fa": "Sova",
            "1e58de9c-4950-5125-93e9-a0aee9f98746": "Killjoy",
            "707eab51-4836-f488-046a-cda6bf494f5a": "Viper",
            "eb93336a-449b-9c1b-0a54-a891f7921d69": "Phoenix",
            "41fb69c1-4189-7b37-f117-bcaf1e96f1bf": "Astra",
            "9f0d8ba9-4140-b941-57d3-a7ad57c6b417": "Brimstone",
            "7f94d92c-4234-0a36-9646-3a87eb8b5c89": "Yoru",
            "569fdd95-4d10-43ab-ca70-79becc718b46": "Sage",
            "a3bfb853-43b2-7238-a4f1-ad90e9e46bcc": "Reyna",
            "8e253930-4c05-31dd-1b6c-968525494517": "Omen",
            "add6443a-41bd-e414-f6ad-e58d267f4e95": "Jett",
            "601dbbe7-43ce-be57-2a40-4abd24953621": "KAY/O",
            "1dbf2edd-4729-0984-3115-daa5eed44993": "Clove",
            "bb2a4828-46eb-8cd1-e765-15848195d751": "Neon",
            "dade69b4-4f5a-8528-247b-219e5a1facd6": "Fade",
            "22697a3d-45bf-8dd7-4fec-84a9e28c69d7": "Chamber",
            "e370fa57-4757-3604-3648-499e1f642d3f": "Gekko",
            "cc8b64c8-4b25-4ff9-6e7f-37b4da43d235": "Deadlock",
            "0e38b510-41a8-5780-5e8f-568b2a4f2d6c": "Iso",
            "95b78ed7-4637-86d9-7e41-71ba8c293152": "Harbor",
            "efba5359-4016-a1e5-7626-b1ae76895940": "Vyse",
            "a]bd32a-4d47-bc17-ca5a-6e22e12fb1c2": "Tejo",
        }
        
    def read_lockfile(self) -> bool:
        """Read the Riot Client lockfile to get local API credentials."""
        try:
            with open(self.lockfile_path, "r") as f:
                data = f.read().split(":")
                self.local_port = data[2]
                self.local_password = data[3]
                
            auth_string = base64.b64encode(f"riot:{self.local_password}".encode()).decode()
            self.local_headers = {
                "Authorization": f"Basic {auth_string}",
                "Content-Type": "application/json"
            }
            return True
        except FileNotFoundError:
            print("\n[ERROR] Lockfile not found. Make sure Valorant is running!")
            return False
        except Exception as e:
            print(f"\n[ERROR] Failed to read lockfile: {e}")
            return False
    
    def get_local_api(self, endpoint: str) -> Optional[Dict]:
        """Make a GET request to the local Riot Client API."""
        try:
            url = f"https://127.0.0.1:{self.local_port}{endpoint}"
            response = requests.get(url, headers=self.local_headers, verify=False)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"[ERROR] Local API request failed: {e}")
            return None
    
    def get_entitlements(self) -> bool:
        """Get entitlements token and access token."""
        try:
            data = self.get_local_api("/entitlements/v1/token")
            if data:
                self.entitlements_token = data.get("token")
                self.access_token = data.get("accessToken")
                self.puuid = data.get("subject")
                return True
            return False
        except Exception as e:
            print(f"[ERROR] Failed to get entitlements: {e}")
            return False
    
    def get_region(self) -> bool:
        """Get player region from sessions."""
        try:
            data = self.get_local_api("/product-session/v1/external-sessions")
            if data:
                for key, value in data.items():
                    if value.get("productId") == "valorant":
                        launch_args = value.get("launchConfiguration", {}).get("arguments", [])
                        for arg in launch_args:
                            if "-ares-deployment=" in arg:
                                self.region = arg.split("=")[1]
                            if "-config-endpoint=" in arg:
                                # Extract shard from config endpoint
                                config = arg.split("=")[1]
                                if "pbe" in config:
                                    self.shard = "pbe"
                                elif "na." in config or "us-" in config:
                                    self.shard = "na"
                                elif "eu." in config or "eu-" in config:
                                    self.shard = "eu"
                                elif "ap." in config or "ap-" in config:
                                    self.shard = "ap"
                                elif "kr." in config or "kr-" in config:
                                    self.shard = "kr"
                                else:
                                    self.shard = self.region
                        return True
            return False
        except Exception as e:
            print(f"[ERROR] Failed to get region: {e}")
            return False
    
    def get_client_version(self) -> bool:
        """Get current client version."""
        try:
            # Try to get version from valorant-api.com
            response = requests.get("https://valorant-api.com/v1/version")
            if response.status_code == 200:
                data = response.json()
                self.client_version = data["data"]["riotClientVersion"]
                return True
        except:
            pass
        
        # Fallback version
        self.client_version = "release-09.00-shipping-20-2621717"
        return True
    
    def get_pd_headers(self) -> Dict[str, str]:
        """Get headers for PD (Player Data) API requests."""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "X-Riot-Entitlements-JWT": self.entitlements_token,
            "X-Riot-ClientVersion": self.client_version,
            "X-Riot-ClientPlatform": base64.b64encode(json.dumps({
                "platformType": "PC",
                "platformOS": "Windows",
                "platformOSVersion": "10.0.19042.1.256.64bit",
                "platformChipset": "Unknown"
            }).encode()).decode(),
            "Content-Type": "application/json"
        }
    
    def get_glz_headers(self) -> Dict[str, str]:
        """Get headers for GLZ (Game Logic Zone) API requests."""
        return self.get_pd_headers()
    
    def get_pd_url(self) -> str:
        """Get Player Data API base URL."""
        return f"https://pd.{self.shard}.a.pvp.net"
    
    def get_glz_url(self) -> str:
        """Get Game Logic Zone API base URL."""
        return f"https://glz-{self.region}-1.{self.shard}.a.pvp.net"
    
    def get_player_names(self, puuids: List[str]) -> Dict[str, Dict[str, str]]:
        """Get player names from their PUUIDs using Name Service."""
        try:
            url = f"{self.get_pd_url()}/name-service/v2/players"
            response = requests.put(
                url,
                headers=self.get_pd_headers(),
                json=puuids,
                verify=False
            )
            if response.status_code == 200:
                data = response.json()
                result = {}
                for player in data:
                    puuid = player.get("Subject")
                    game_name = player.get("GameName", "Unknown")
                    tag_line = player.get("TagLine", "")
                    result[puuid] = {
                        "name": game_name,
                        "tag": tag_line,
                        "full": f"{game_name}#{tag_line}" if tag_line else game_name
                    }
                return result
            return {}
        except Exception as e:
            print(f"[ERROR] Failed to get player names: {e}")
            return {}
    
    def get_pregame_player(self) -> Optional[str]:
        """Get current pre-game match ID."""
        try:
            url = f"{self.get_glz_url()}/pregame/v1/players/{self.puuid}"
            response = requests.get(url, headers=self.get_glz_headers(), verify=False)
            if response.status_code == 200:
                data = response.json()
                return data.get("MatchID")
            return None
        except Exception as e:
            return None
    
    def get_pregame_match(self, match_id: str) -> Optional[Dict]:
        """Get pre-game match details."""
        try:
            url = f"{self.get_glz_url()}/pregame/v1/matches/{match_id}"
            response = requests.get(url, headers=self.get_glz_headers(), verify=False)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"[ERROR] Failed to get pre-game match: {e}")
            return None
    
    def get_current_game_player(self) -> Optional[str]:
        """Get current in-game match ID."""
        try:
            url = f"{self.get_glz_url()}/core-game/v1/players/{self.puuid}"
            response = requests.get(url, headers=self.get_glz_headers(), verify=False)
            if response.status_code == 200:
                data = response.json()
                return data.get("MatchID")
            return None
        except Exception as e:
            return None
    
    def get_current_game_match(self, match_id: str) -> Optional[Dict]:
        """Get current game match details."""
        try:
            url = f"{self.get_glz_url()}/core-game/v1/matches/{match_id}"
            response = requests.get(url, headers=self.get_glz_headers(), verify=False)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"[ERROR] Failed to get current game match: {e}")
            return None
    
    def select_agent(self, match_id: str, agent_id: str) -> bool:
        """Select (hover) an agent in pre-game."""
        try:
            url = f"{self.get_glz_url()}/pregame/v1/matches/{match_id}/select/{agent_id}"
            response = requests.post(url, headers=self.get_glz_headers(), verify=False)
            return response.status_code == 200
        except Exception as e:
            print(f"[ERROR] Failed to select agent: {e}")
            return False
    
    def lock_agent(self, match_id: str, agent_id: str) -> bool:
        """Lock in an agent in pre-game."""
        try:
            url = f"{self.get_glz_url()}/pregame/v1/matches/{match_id}/lock/{agent_id}"
            response = requests.post(url, headers=self.get_glz_headers(), verify=False)
            return response.status_code == 200
        except Exception as e:
            print(f"[ERROR] Failed to lock agent: {e}")
            return False
    
    def get_agent_name(self, agent_id: str) -> str:
        """Get agent name from ID."""
        return self.agents.get(agent_id.lower(), "Unknown Agent")
    
    def get_agent_id(self, agent_name: str) -> Optional[str]:
        """Get agent ID from name."""
        agent_name_lower = agent_name.lower()
        for agent_id, name in self.agents.items():
            if name.lower() == agent_name_lower:
                return agent_id
        return None
    
    def initialize(self) -> bool:
        """Initialize the companion by reading lockfile and getting tokens."""
        print("\n[*] Initializing Valorant Companion...")
        
        if not self.read_lockfile():
            return False
        print("[+] Lockfile read successfully")
        
        if not self.get_entitlements():
            print("[ERROR] Failed to get entitlements. Is Valorant running?")
            return False
        print("[+] Got entitlements token")
        
        if not self.get_region():
            print("[WARNING] Could not determine region, defaulting to 'na'")
            self.region = "na"
            self.shard = "na"
        print(f"[+] Region: {self.region}, Shard: {self.shard}")
        
        if not self.get_client_version():
            print("[WARNING] Could not get client version")
        print(f"[+] Client Version: {self.client_version}")
        
        print(f"[+] Your PUUID: {self.puuid}")
        print("[+] Initialization complete!\n")
        return True
    
    def display_pregame_players(self):
        """Display all players in the pre-game lobby."""
        print("\n[*] Fetching pre-game players...")
        
        match_id = self.get_pregame_player()
        if not match_id:
            print("[!] You are not in a pre-game lobby.")
            return
        
        match_data = self.get_pregame_match(match_id)
        if not match_data:
            print("[ERROR] Failed to get match data.")
            return
        
        # Get team side
        ally_team = match_data.get("AllyTeam", {})
        team_id = ally_team.get("TeamID", "Unknown")
        
        # Determine side
        if team_id == "Blue":
            side = "DEFENDERS (Blue)"
        elif team_id == "Red":
            side = "ATTACKERS (Red)"
        else:
            side = f"Team: {team_id}"
        
        print(f"\n{'='*60}")
        print(f"  PRE-GAME LOBBY - {side}")
        print(f"  Map: {match_data.get('MapID', 'Unknown').split('/')[-1]}")
        print(f"{'='*60}")
        
        # Get all player PUUIDs
        players = ally_team.get("Players", [])
        puuids = [p.get("Subject") for p in players]
        
        # Get player names
        player_names = self.get_player_names(puuids)
        
        print(f"\n  YOUR TEAM ({len(players)} players):")
        print(f"  {'-'*50}")
        
        for player in players:
            puuid = player.get("Subject")
            agent_id = player.get("CharacterID", "")
            is_locked = player.get("CharacterSelectionState") == "locked"
            
            name_info = player_names.get(puuid, {"full": "Unknown Player"})
            name = name_info.get("full", "Unknown Player")
            
            # Check if this is the current player
            is_me = puuid == self.puuid
            me_indicator = " (YOU)" if is_me else ""
            
            # Get agent info
            if agent_id:
                agent_name = self.get_agent_name(agent_id)
                lock_status = "LOCKED" if is_locked else "selecting"
                agent_info = f"[{agent_name} - {lock_status}]"
            else:
                agent_info = "[No agent selected]"
            
            # Check for incognito (PlayerIdentity)
            identity = player.get("PlayerIdentity", {})
            incognito = identity.get("Incognito", False)
            hide_status = " [INCOGNITO - Real name shown]" if incognito else ""
            
            print(f"    {name}{me_indicator}{hide_status}")
            print(f"      {agent_info}")
            print()
        
        print(f"{'='*60}\n")
    
    def display_current_game_players(self):
        """Display all players in the current game."""
        print("\n[*] Fetching current game players...")
        
        match_id = self.get_current_game_player()
        if not match_id:
            print("[!] You are not in an active game.")
            return
        
        match_data = self.get_current_game_match(match_id)
        if not match_data:
            print("[ERROR] Failed to get match data.")
            return
        
        print(f"\n{'='*60}")
        print(f"  CURRENT GAME")
        print(f"  Map: {match_data.get('MapID', 'Unknown').split('/')[-1]}")
        print(f"{'='*60}")
        
        # Get all players
        players = match_data.get("Players", [])
        
        # Separate into teams
        my_team = []
        enemy_team = []
        
        for player in players:
            if player.get("TeamID") == match_data.get("AllyTeam", {}).get("TeamID"):
                my_team.append(player)
            else:
                enemy_team.append(player)
        
        # Get all PUUIDs
        all_puuids = [p.get("Subject") for p in players]
        player_names = self.get_player_names(all_puuids)
        
        def print_team(team_players: List[Dict], team_label: str):
            print(f"\n  {team_label} ({len(team_players)} players):")
            print(f"  {'-'*50}")
            
            for player in team_players:
                puuid = player.get("Subject")
                agent_id = player.get("CharacterID", "")
                
                name_info = player_names.get(puuid, {"full": "Unknown Player"})
                name = name_info.get("full", "Unknown Player")
                
                is_me = puuid == self.puuid
                me_indicator = " (YOU)" if is_me else ""
                
                agent_name = self.get_agent_name(agent_id) if agent_id else "Unknown"
                
                # Check for incognito
                identity = player.get("PlayerIdentity", {})
                incognito = identity.get("Incognito", False)
                hide_status = " [INCOGNITO - Real name shown]" if incognito else ""
                
                print(f"    {name}{me_indicator}{hide_status}")
                print(f"      Agent: {agent_name}")
                print()
        
        print_team(my_team, "YOUR TEAM")
        print_team(enemy_team, "ENEMY TEAM")
        
        print(f"{'='*60}\n")
    
    def auto_lock_agent(self, agent_name: str, wait_for_pregame: bool = True):
        """Auto-lock a specific agent when pre-game becomes available."""
        agent_id = self.get_agent_id(agent_name)
        if not agent_id:
            print(f"[ERROR] Unknown agent: {agent_name}")
            print("[*] Available agents:")
            for name in sorted(self.agents.values()):
                print(f"    - {name}")
            return
        
        print(f"\n[*] Auto-lock enabled for: {agent_name}")
        
        if wait_for_pregame:
            print("[*] Waiting for pre-game lobby...")
            while True:
                match_id = self.get_pregame_player()
                if match_id:
                    print(f"[+] Pre-game found! Match ID: {match_id}")
                    break
                time.sleep(1)
                sys.stdout.write(".")
                sys.stdout.flush()
        else:
            match_id = self.get_pregame_player()
            if not match_id:
                print("[!] You are not in a pre-game lobby.")
                return
        
        # Select the agent first
        print(f"[*] Selecting {agent_name}...")
        if self.select_agent(match_id, agent_id):
            print(f"[+] Selected {agent_name}")
        else:
            print(f"[!] Failed to select {agent_name} - might be taken or unavailable")
            return
        
        # Small delay then lock
        time.sleep(0.1)
        
        print(f"[*] Locking {agent_name}...")
        if self.lock_agent(match_id, agent_id):
            print(f"[+] Successfully locked {agent_name}!")
        else:
            print(f"[!] Failed to lock {agent_name} - might be taken or unavailable")
    
    def lock_agent_now(self, agent_name: str):
        """Lock an agent immediately (must be in pre-game)."""
        self.auto_lock_agent(agent_name, wait_for_pregame=False)
    
    def select_agent_without_lock(self, agent_name: str):
        """Select an agent without locking (hover)."""
        agent_id = self.get_agent_id(agent_name)
        if not agent_id:
            print(f"[ERROR] Unknown agent: {agent_name}")
            return
        
        match_id = self.get_pregame_player()
        if not match_id:
            print("[!] You are not in a pre-game lobby.")
            return
        
        print(f"[*] Selecting {agent_name} (without locking)...")
        if self.select_agent(match_id, agent_id):
            print(f"[+] Hovering on {agent_name}")
        else:
            print(f"[!] Failed to select {agent_name}")
    
    def list_agents(self):
        """List all available agents."""
        print("\n[*] Available Agents:")
        print("-" * 30)
        for name in sorted(self.agents.values()):
            print(f"  - {name}")
        print("-" * 30)
        print()


def print_menu():
    """Print the main menu."""
    print("\n" + "=" * 50)
    print("       VALORANT COMPANION")
    print("=" * 50)
    print("  1. View Pre-Game (Agent Select) Players")
    print("  2. View Current Game Players")
    print("  3. Auto-Lock Agent (waits for pre-game)")
    print("  4. Lock Agent Now (must be in pre-game)")
    print("  5. Select Agent without locking")
    print("  6. List all agents")
    print("  7. Exit")
    print("=" * 50)


def main():
    print("\n" + "=" * 50)
    print("  VALORANT COMPANION - Player Info & Auto-Lock")
    print("  Using unofficial Valorant API")
    print("=" * 50)
    
    companion = ValorantCompanion()
    
    if not companion.initialize():
        print("\n[!] Failed to initialize. Make sure:")
        print("    1. Valorant is running")
        print("    2. You are logged in")
        input("\nPress Enter to exit...")
        return
    
    while True:
        print_menu()
        choice = input("Select option (1-7): ").strip()
        
        if choice == "1":
            companion.display_pregame_players()
        
        elif choice == "2":
            companion.display_current_game_players()
        
        elif choice == "3":
            companion.list_agents()
            agent = input("Enter agent name to auto-lock: ").strip()
            if agent:
                companion.auto_lock_agent(agent)
        
        elif choice == "4":
            companion.list_agents()
            agent = input("Enter agent name to lock now: ").strip()
            if agent:
                companion.lock_agent_now(agent)
        
        elif choice == "5":
            companion.list_agents()
            agent = input("Enter agent name to select (hover): ").strip()
            if agent:
                companion.select_agent_without_lock(agent)
        
        elif choice == "6":
            companion.list_agents()
        
        elif choice == "7":
            print("\n[*] Goodbye!")
            break
        
        else:
            print("[!] Invalid option. Please try again.")
        
        input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()



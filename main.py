import os
import sys
import time
import shutil
import threading
import subprocess
import re
from datetime import datetime, timezone, timedelta

# --- Configuration ---
# Set to "Downloads" to create a subfolder, or "" to download directly to the script's directory.
DOWNLOAD_DIR = "Downloads"

# --- Dependency Imports ---
try:
    from kickapi import KickAPI
except ImportError:
    print("Error: Required library 'KickApi' not found. Run 'install.bat' or 'pip install KickApi'.")
    sys.exit(1)

try:
    import psutil

    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

try:
    import msvcrt

    HAS_MSVCRT = True
except ImportError:
    HAS_MSVCRT = False

# Force UTF-8 encoding for console compatibility
sys.stdout.reconfigure(encoding='utf-8')


class UI:
    """Console UI styling and utility functions."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

    @staticmethod
    def clear():
        os.system('cls' if os.name == 'nt' else 'clear')

    @staticmethod
    def divider(char='═', length=80):
        print(f"{UI.DIM}{char * length}{UI.RESET}")

    @staticmethod
    def print_header(text):
        print(f"\n{UI.HEADER}{UI.BOLD} {text} {UI.RESET}")
        UI.divider()


def format_vod_title(date_str, username, title, lang='en'):
    """Creates a clean, file-system filename."""
    if not title: title = "Untitled_Stream"

    date_formatted = "[No Date]"
    if date_str and date_str != "Unknown Date":
        try:
            clean_date = date_str.replace("T", " ").split(".")[0].replace("Z", "").strip()
            dt = datetime.strptime(clean_date, '%Y-%m-%d %H:%M:%S')
            date_formatted = dt.strftime('%d %B %Y')
        except Exception:
            date_formatted = str(date_str)[:10]

    filename = f"[{date_formatted}] {username} - {title}"
    return "".join(c for c in filename if c.isalnum() or c in (' ', '.', '_', '-', ',')).strip()


def format_duration(ms):
    """Converts milliseconds to HH:MM:SS string."""
    try:
        ts = int(float(ms)) // 1000
        return f"{ts // 3600:02d}:{(ts % 3600) // 60:02d}:{ts % 60:02d}"
    except (TypeError, ValueError):
        return "00:00:00"


def open_player(url):
    """Attempts to open the stream/video in a local media player."""
    if not url: return False
    player = shutil.which("vlc") or shutil.which("mpc-hc64") or shutil.which("mpc-hc")
    if not player and os.name == 'nt':
        for p in [r"C:\Program Files\VideoLAN\VLC\vlc.exe", r"C:\Program Files\MPC-HC\mpc-hc64.exe"]:
            if os.path.exists(p): player = p; break
    if player:
        try:
            subprocess.Popen([player, url])
            return True
        except Exception:
            return False
    return False


# ==========================================
# Download
# ==========================================

class DownloadManager:
    """Handles background downloads using yt-dlp."""

    def __init__(self, download_dir=DOWNLOAD_DIR):
        self.downloads = {}
        self.lock = threading.Lock()
        # Use absolute path of the script directory if no directory is specified
        self.base_path = os.path.abspath(download_dir) if download_dir else os.path.dirname(os.path.abspath(__file__))

    def start(self, url, filename):
        if not url:
            print(f"{UI.RED}❌ Error: Invalid URL provided.{UI.RESET}")
            return

        prog = shutil.which("yt-dlp") or os.path.join(os.getcwd(), ".venv", "Scripts", "yt-dlp.exe")

        # Combine base path with the filename (as a subfolder for temporary files)
        path = os.path.join(self.base_path, filename)
        os.makedirs(os.path.join(path, ".tmp"), exist_ok=True)

        cmd = [
            prog if os.path.exists(prog) else "yt-dlp",
            "--newline", "--progress", "--remux-video", "mp4",
            "-P", path,
            "--paths", f"temp:{os.path.join(path, '.tmp')}",
            "-o", f"{filename}.mp4",
            "--concurrent-fragments", "16",
            "--retries", "10",
            url
        ]

        try:
            flags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
                                    creationflags=flags)

            did = str(time.time())
            with self.lock:
                self.downloads[did] = {
                    "title": filename,
                    "progress": "0%",
                    "status": "downloading",
                    "proc": proc,
                    "speed": "N/A",
                    "eta": "N/A"
                }

            threading.Thread(target=self._monitor, args=(did, proc, path), daemon=True).start()
            print(f"{UI.GREEN}🟢 Download started: {filename}{UI.RESET}")
        except Exception as e:
            print(f"{UI.RED}❌ Failed to launch yt-dlp: {e}{UI.RESET}")

    def _monitor(self, did, proc, path):
        # yt-dlp progress patterns
        reg_p = re.compile(r"(\d+\.?\d*)%")
        reg_s = re.compile(r"at\s+([\d.]+[KMGTkKmgti]+[Bb]/s)")
        reg_e = re.compile(r"ETA\s+([\d:]+)")

        for line in iter(proc.stdout.readline, ''):
            mp, ms, me = reg_p.search(line), reg_s.search(line), reg_e.search(line)
            with self.lock:
                if did in self.downloads:
                    if mp: self.downloads[did]["progress"] = f"{mp.group(1)}%"
                    if ms: self.downloads[did]["speed"] = ms.group(1)
                    if me: self.downloads[did]["eta"] = me.group(1)

        proc.wait()
        with self.lock:
            if did in self.downloads:
                if proc.returncode == 0:
                    self.downloads[did]["status"] = "finished"
                    self.downloads[did]["progress"] = "100%"
                    self.downloads[did]["speed"] = "0B/s"
                    self.downloads[did]["eta"] = "00:00"
                    shutil.rmtree(os.path.join(path, ".tmp"), ignore_errors=True)
                elif self.downloads[did]["status"] != "cancelled":
                    self.downloads[did]["status"] = "failed"

    def status_monitor(self):
        """Interactive real-time download status viewer with cancellation control."""
        while True:
            UI.clear()
            UI.print_header("DOWNLOAD MONITOR")

            # Store the IDs here so we can match them to user cancellation choices
            keys_mapped = []
            with self.lock:
                if not self.downloads:
                    print("   No downloads in list.")
                    UI.divider('-')
                    input("\nPress Enter to return...")
                    break

                # Header for the table
                print(f" {'ID':<3} | {'TITLE':<30} | {'PROGRESS':<8} | {'SPEED':<10} | {'ETA':<8} | {'STATUS'}")
                UI.divider('-')

                for i, (k, v) in enumerate(self.downloads.items(), 1):
                    keys_mapped.append(k)
                    color = UI.GREEN if v['status'] == 'finished' else UI.YELLOW if v['status'] == 'paused' else UI.BLUE if v['status'] == 'downloading' else UI.RED
                    title = (v['title'][:27] + '...') if len(v['title']) > 30 else v['title']

                    print(f" [{i:02d}] | {title:<30} | {v['progress']:>8} | {v['speed']:<10} | {v['eta']:<8} | {color}{v['status'].upper()}{UI.RESET}")

            UI.divider('-')
            print(f"{UI.DIM}Commands: 'q' Back | 'c#' Cancel (e.g., c1) | Auto-refreshing...{UI.RESET}")

            # Read keyboard inputs
            cmd = ""
            try:
                if HAS_MSVCRT:
                    time.sleep(1)
                    if msvcrt.kbhit():
                        cmd = input(">>> ").strip().lower()
                else:
                    cmd = input(">>> (q to back, c# to cancel, Enter to refresh): ").strip().lower()
            except KeyboardInterrupt:
                break

            # Handle Actions
            if cmd == 'q':
                break
            elif cmd.startswith('c') and cmd[1:].isdigit():
                idx = int(cmd[1:]) - 1
                if 0 <= idx < len(keys_mapped):
                    target_key = keys_mapped[idx]
                    with self.lock:
                        v = self.downloads.get(target_key)
                        if v and v["status"] == "downloading":
                            v["status"] = "cancelled"
                            if v.get("proc"):
                                try:
                                    v["proc"].terminate()  # Forces the downloader to stop immediately
                                except Exception:
                                    pass
                            print(f"\n{UI.RED}⏹️ Cancelled download: {v['title']}{UI.RESET}")
                            time.sleep(1.5)

    def get_summary(self):
        with self.lock:
            active = [d for d in self.downloads.values() if d["status"] == "downloading"]
            if not active: return ""
            # Show progress of the first active download in the header
            return f" {UI.CYAN}({len(active)} active | {active[0]['progress']} @ {active[0]['speed']}){UI.RESET}"


# ==========================================
# Main Application
# ==========================================

api = KickAPI()
dl_mgr = DownloadManager()


def channel_dashboard(channel):
    """Sub-menu for channel specific actions."""
    while True:
        UI.clear()
        ls = getattr(channel, 'livestream', None)
        status_text = f"{UI.GREEN}● LIVE{UI.RESET}" if ls else f"{UI.RED}○ OFFLINE{UI.RESET}"

        UI.print_header(f"DASHBOARD: {channel.username.upper()} | {status_text}{dl_mgr.get_summary()}")

        if ls:
            cat = ls.get('categories', [{}])[0].get('name', 'N/A')
            print(f"  {UI.BOLD}Activity:{UI.RESET} {UI.GREEN}Streaming {cat}{UI.RESET}")
            print(f"  {UI.BOLD}Title:{UI.RESET} {ls.get('session_title')}")

        print(f"\n  1. Channel Information    4. VOD History")
        print(f"  2. Leaderboards           5. Clips List")
        print(f"  3. Socials & Avatar       6. Play Live/Recent")
        print(f"  7. Live Chat              0. Exit to Hub")
        UI.divider()

        cmd = input(f"[{channel.username}] >>> ").strip()

        if cmd == '0':
            break
        elif cmd == '1':
            UI.print_header("CHANNEL INFORMATION")
            is_banned = f"{UI.RED}Yes{UI.RESET}" if channel.is_banned else f"{UI.GREEN}No{UI.RESET}"
            verified = f"{UI.GREEN}Verified{UI.RESET}" if channel.verified else "Standard"
            print(f"  • ID: {channel.id} | UserID: {channel.user_id}")
            print(f"  • Followers: {channel.followers:,} | Subs: {channel.subscriber_count or 'N/A'}")
            print(f"  • Status: {verified} | Banned: {is_banned}")
            print(f"  • Bio: {channel.bio or '[No Bio]'}")
            
            # Last stream info
            vods = channel.videos
            if vods:
                last_v = vods[0]
                # Format date
                d_str = last_v.created_at[:10]
                try:
                    dt = datetime.strptime(last_v.created_at.replace("T", " ").split(".")[0].replace("Z", ""), '%Y-%m-%d %H:%M:%S')
                    d_str = dt.strftime('%d %b %Y')
                except: pass
                
                print(f"\n  {UI.BOLD}LAST STREAM:{UI.RESET}")
                print(f"  • Date: {d_str}")
                print(f"  • Title: {last_v.title}")
                print(f"  • Link: {UI.BLUE}https://kick.com/{channel.username}/videos/{last_v.uuid}{UI.RESET}")
            else:
                print(f"\n  • Last Stream: No VODs found.")

            input("\nPress Enter to return...")
        elif cmd == '2':
            UI.print_header("LEADERBOARDS")
            try:
                lb = channel.leaderboards
                if not lb.gifts:
                    print("  No leaderboard data available.")
                for i, u in enumerate(lb.gifts[:10], 1):
                    print(f"  {i:02d}. {u.username:<20} | {u.quantity}")
            except Exception:
                print("  [Error fetching leaderboards]")
            input("\nPress Enter to return...")
        elif cmd == '3':
            UI.print_header("SOCIAL LINKS & MEDIA")
            socials = [f"{s.capitalize()}: {getattr(channel, s)}" for s in
                       ['twitter', 'facebook', 'instagram', 'youtube', 'discord', 'tiktok'] if getattr(channel, s)]
            if not socials: print("  No social links found.")
            for s in socials: print(f"  • {s}")
            if channel.avatar: print(f"\n  • Avatar: {UI.BLUE}{channel.avatar}{UI.RESET}")
            input("\nPress Enter to return...")
        elif cmd == '4':
            UI.print_header("VOD HISTORY")
            print("  Fetching VOD list...")
            vods = channel.videos
            count = len(vods)
            if count == 0:
                print("  No VODs found.")
            else:
                print(f"  Found {count} VODs.")
                limit_input = input(f"  How many to display? (1-{count}, or Enter for all): ").strip()
                limit = count if not limit_input.isdigit() else min(int(limit_input), count)

                display_vods = vods[:limit]
                for i, v in enumerate(display_vods, 1):
                    print(f" [{i:02d}] {UI.CYAN}{v.title[:60]}{UI.RESET}")
                    print(f"      👁️  {v.views:,} | ⏳ {format_duration(v.duration)} | 📅 {v.created_at[:10]}")

                    # --- Direct Links Visualization ---
                    vod_web_url = getattr(v, 'url', None) or (
                        f"https://kick.com/{channel.username}/videos/{v.uuid}" if hasattr(v, 'uuid') else "N/A")
                    print(f"      🔗 VOD Link: {UI.BLUE}{vod_web_url}{UI.RESET}")
                    print(f"      📺 M3U8 Link: {UI.YELLOW}{v.stream}{UI.RESET}")

                sel = input("\nEnter # to Download, 'p#' to Play, or Enter to skip: ").lower()
                if sel.startswith('p') and sel[1:].isdigit():
                    idx = int(sel[1:]) - 1
                    if 0 <= idx < len(display_vods): open_player(display_vods[idx].stream)
                elif sel.isdigit() and 1 <= int(sel) <= len(display_vods):
                    v = display_vods[int(sel) - 1]
                    dl_mgr.start(v.stream, format_vod_title(v.created_at, channel.username, v.title))
        elif cmd == '5':
            UI.print_header("CLIPS LIST")
            print("  Fetching clips...")
            clips = channel.clips
            count = len(clips)
            if count == 0:
                print("  No clips found.")
            else:
                print(f"  Found {count} clips.")
                limit_input = input(f"  How many to display? (1-{count}, or Enter for all): ").strip()
                limit = count if not limit_input.isdigit() else min(int(limit_input), count)

                display_clips = clips[:limit]
                for i, c in enumerate(display_clips, 1):
                    print(f" [{i:02d}] {UI.CYAN}{c.title[:60]}{UI.RESET} (by {c.creator.username})")
                    print(f"      👁️  {c.views:,} | ⏳ {format_duration(c.duration)}")

                sel = input("\nEnter # to Download, 'p#' to Play, or Enter to skip: ").lower()
                if sel.startswith('p') and sel[1:].isdigit():
                    idx = int(sel[1:]) - 1
                    if 0 <= idx < len(display_clips): open_player(display_clips[idx].stream)
                elif sel.isdigit() and 1 <= int(sel) <= len(display_clips):
                    c = display_clips[int(sel) - 1]
                    dl_mgr.start(c.stream, f"Clip_{channel.username}_{c.id}")
        elif cmd == '6':
            if ls:
                print(f"{UI.GREEN}Opening Live Stream...{UI.RESET}")
                open_player(channel.playback)
            else:
                vods = channel.videos
                if vods:
                    print(f"{UI.YELLOW}Channel offline. Opening most recent VOD...{UI.RESET}")
                    open_player(vods[0].stream)
                else:
                    print(f"{UI.RED}No content found.{UI.RESET}")
                    time.sleep(1.5)
        elif cmd == '7':
            UI.print_header("LIVE CHAT (Ctrl+C to return)")
            try:
                # Start from now, without the Z or specific sub-second precision that might trip the API
                curr_time = datetime.now(timezone.utc) - timedelta(seconds=10)
                seen_ids = set()
                while True:
                    # Format as yyyy-mm-ddThh:mm:ss.000Z
                    time_str = curr_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')
                    data = api.chat(channel.id, time_str)
                    
                    if data and hasattr(data, 'messages') and data.messages:
                        for m in data.messages:
                            msg_id = getattr(m, 'id', f"{m.sender.username}_{m.date}")
                            if msg_id not in seen_ids:
                                print(f" {UI.BOLD}{m.sender.username}:{UI.RESET} {m.text}")
                                seen_ids.add(msg_id)
                                
                                # Try to parse message date to update curr_time if possible
                                # This helps in moving forward in time
                                try:
                                    # Example: 2023-10-27T12:34:56.000Z
                                    m_date = datetime.strptime(m.date.split('.')[0].replace('Z', ''), '%Y-%m-%dT%H:%M:%S').replace(tzinfo=timezone.utc)
                                    if m_date > curr_time:
                                        curr_time = m_date
                                except:
                                    pass
                        
                        # Clean seen_ids
                        if len(seen_ids) > 1000:
                            seen_ids = set(list(seen_ids)[-500:])
                    
                    # If no messages, just slightly advance curr_time to stay near "now"
                    curr_time += timedelta(seconds=1)
                    time.sleep(2)
            except KeyboardInterrupt:
                pass


def main_hub():
    """Application entry point."""
    while True:
        UI.clear()
        summary = dl_mgr.get_summary()
        UI.print_header(f"KICK-DOWNLOADER {summary}")

        print("   1. Search Channel        3. Download From Link")
        print("   2. Download Monitor      4. Exit")
        UI.divider()

        choice = input("\nSelect: ").strip()

        if choice == '4':
            print("Exiting...")
            break
        elif choice == '1':
            user = input("Username: ").strip()
            if user:
                print(f"Searching for {user}...")
                ch = api.channel(user)
                if ch and hasattr(ch, 'username'):
                    channel_dashboard(ch)
                else:
                    print(f"{UI.RED}❌ Channel not found.{UI.RESET}")
                    time.sleep(1.5)
        elif choice == '2':
            dl_mgr.status_monitor()
        elif choice == '3':
            UI.print_header("DOWNLOAD CUSTOM LINK")
            url = input("  Paste Kick URL or M3U8 Link: ").strip()
            if url:
                filename = input("  Give this file a name (or press Enter for automatic timestamp name): ").strip()
                if not filename:
                    # Fallback auto-name if user hits Enter without typing a name
                    filename = f"Custom_Download_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                else:
                    # Clean out illegal characters that can break file systems
                    filename = "".join(c for c in filename if c.isalnum() or c in (' ', '.', '_', '-', ',')).strip()

                dl_mgr.start(url, filename)
                time.sleep(2)


if __name__ == "__main__":
    if DOWNLOAD_DIR:
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    try:
        main_hub()
    except KeyboardInterrupt:
        sys.exit(0)

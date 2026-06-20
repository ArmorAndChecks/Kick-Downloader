## 🌐 Kick-Downloader

## ✨ Features

- **Channel Analytics**: View follower counts, bio ETC.
- **VOD & Clip Downloader**: Download VODs and clips.
- **Live Chat Monitor**: Real-time chat from your terminal.
- **Download Manager**: Track downloads.

## 🚀 Installation and Running

### Install with .Bat
1. **Download the Repository**: "Download ZIP" or
```bash
git clone https://github.com/ArmorAndChecks/Kick-Downloader.git
cd Kick-Downloader
```
3. **Run Installer**: Run `install.bat`. This will automatically install all required libraries.
4. **Start**: Run `start_tool.bat`. This will open the terminal and starts the app.

or

### 
1. **Install Python**: Make sure have Python 3.8+ installed.  [Python Download](https://www.python.org/downloads/). 
2. **Install Dependencies**:
```bash
pip install -r requirements.txt      
```

🗑 Uninstallation
Run uninstall.bat to remove the installed libraries, your Downloads/ folder will not be deleted.

🤝 Credits & Dependencies
- **[KickApi](https://github.com/Enmn/KickApi)** by Enmn
* **[KickApi](https://github.com/YourKickApiSource)** - The core wrapper used to communicate with Kick's internal API endpoints.
* **[yt-dlp](https://github.com/yt-dlp/yt-dlp)** - The powerful command-line media downloader engine handling background stream and VOD extraction.
* **[requests](https://pypi.org/project/requests/)** / **[curl_cffi](https://pypi.org/project/curl-cffi/)** - Advanced HTTP clients used to manage clean network connections and mimic browser handshakes.
* **[cloudscraper](https://pypi.org/project/cloudscraper/)** - Assists in bypassing standard bot-protection walls safely.
* **[ua-generator](https://pypi.org/project/ua-generator/)** - Dynamically generates browser user-agent profiles to ensure connection stability.
* **[psutil](https://pypi.org/project/psutil/)** - Monitors and manages background system processes when running downloads or media players.
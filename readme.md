# Git Repo Dashboard
This script is a persistent project launcher designed for high-speed navigation between Git repositories. It scans a designated parent directory, identifies Git-initialized folders, and displays them in a modern, dark-themed GUI.
Currently linux only

## Installation & Command Setup
To make the dashboard accessible from anywhere in your system without cluttering your terminal, simply run `./setup.sh`
Optionally: (add execution permission and reload shell)
```
chmod +x setup.sh
./setup.sh
source ~/.bashrc
```
This automates the environment configuration, allowing you to simply type repos in any terminal to launch the GUI.

What setup.sh does:
  - Dependency Check: Verifies python3-tk is installed via apt and installs Python dependencies from requirements.txt.
  - Permissions: Ensures the main script is executable: chmod +x /home/bvargo@corp.greenphire.net/Documents/git-dashboard/git-dashboard.py
  - Symbolic Link: Links the script to your local bin folder so it behaves like a system command: ln -s [Path/To/Repo]/git-dashboard.py ~/.local/bin/repos
  - Detached Alias: Adds a specialized alias to your ~/.bashrc to ensure the GUI runs independently of the terminal session: repos() { nohup ~/.local/bin/repos >/dev/null 2>&1 & }

# Usage
Simply type `repos` in any terminal window. The dashboard will launch independently, allowing you to search, sort, and open your projects with a double-click or by pressing Enter.


Editor setup:
- In Settings (⚙), Set the command to open your editor of choice in settings. (e.g., `code` for vscode, or `subl` for sublime text)

Directory setup:
- In Settings (⚙), Set the base directory to search for git repos in (e.g., documents)

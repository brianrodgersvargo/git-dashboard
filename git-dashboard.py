#!/usr/bin/env python3
import os
import subprocess
import sys
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk

from dotenv import load_dotenv, set_key

"""
GIT REPO DASHBOARD
==================
A lightweight, dark-themed GUI launcher for Git repositories.

DESCRIPTION:
    Scans a local directory for Git repositories and provides a searchable,
    sortable interface to launch them in a preferred code editor (default: Zed).

DEPENDENCIES:
    - python3-tk (Standard Library)
    - python-dotenv (pip install python-dotenv)

CONFIGURATION:
    Configuration is managed via a '.env' file in the script's directory.
    - BASE_PATH: The parent directory containing your Git repos.
    - EDITOR_COMMAND: The CLI command to open your editor (e.g., 'zed', 'code').

SETUP:
    Run the provided 'setup.sh' to create a system-wide 'repos' command.
"""

# --- LOAD CONFIGURATION ---
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
ENV_PATH = os.path.join(SCRIPT_DIR, ".env")
load_dotenv(ENV_PATH)

# Initial global configs
EDITOR_COMMAND = os.getenv("EDITOR_COMMAND", "code")
BASE_PATH = os.getenv("BASE_PATH", os.path.expanduser("~/Documents"))

# --- DARK THEME COLORS ---
BG_MAIN = "#1e1e1e"
BG_STRIPE = "#252526"
BG_HEADER = "#333333"
FG_TEXT = "#d4d4d4"
ACCENT = "#4fc1ff"
SELECTED = "#094771"
SUCCESS = "#2ea043"
HOVER = "#444444"


def get_time_ago(timestamp):
    if timestamp == 0:
        return "Never"
    diff = datetime.now() - datetime.fromtimestamp(timestamp)
    s = diff.total_seconds()
    if s < 60:
        return f"{int(s)}s ago"
    if s < 3600:
        return f"{int(s // 60)}m ago"
    if s < 86400:
        return f"{int(s // 3600)}h ago"
    return f"{int(s // 86400)}d ago"


def get_git_repos(path):
    repos = []
    try:
        expanded_path = os.path.expanduser(path)
        if not os.path.exists(expanded_path):
            return []
        with os.scandir(expanded_path) as entries:
            for entry in entries:
                git_dir = os.path.join(entry.path, ".git")
                if entry.is_dir() and os.path.exists(git_dir):
                    msg_file = os.path.join(git_dir, "COMMIT_EDITMSG")
                    mtime = (
                        os.path.getmtime(msg_file)
                        if os.path.exists(msg_file)
                        else os.path.getmtime(git_dir)
                    )
                    repos.append(
                        {
                            "name": entry.name,
                            "path": entry.path,
                            "mtime": mtime,
                            "time_ago": get_time_ago(mtime),
                        }
                    )
        return repos
    except Exception as e:
        print(f"Error: {e}")
        return []


# --- CUSTOM DARK FOLDER BROWSER ---
class DarkFolderBrowser(tk.Toplevel):
    def __init__(self, parent, initial_dir):
        super().__init__(parent)
        self.title("Select Directory")
        self.geometry("500x500")
        self.configure(bg=BG_MAIN)
        self.result = None
        self.current_dir = os.path.abspath(os.path.expanduser(initial_dir or "~"))

        self.transient(parent)
        self.grab_set()

        # Header with Path
        self.path_label = tk.Label(
            self,
            text=self.current_dir,
            bg=BG_MAIN,
            fg=ACCENT,
            font=("Segoe UI", 9),
            anchor="w",
        )
        self.path_label.pack(fill=tk.X, padx=15, pady=10)

        # Folder List (Treeview)
        self.tree = ttk.Treeview(self, columns=("Name"), show="headings")
        self.tree.heading("Name", text="FOLDERS", anchor="w")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=15)
        self.tree.bind("<Double-1>", self.on_double_click)

        # Navigation Buttons
        btn_frame = tk.Frame(self, bg=BG_MAIN)
        btn_frame.pack(fill=tk.X, padx=15, pady=15)

        tk.Button(
            btn_frame,
            text="UP",
            command=self.go_up,
            bg=BG_HEADER,
            fg=FG_TEXT,
            relief="flat",
            width=10,
        ).pack(side=tk.LEFT)
        tk.Button(
            btn_frame,
            text="SELECT THIS FOLDER",
            command=self.select,
            bg=SUCCESS,
            fg="white",
            relief="flat",
            font=("Segoe UI", 9, "bold"),
        ).pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))

        self.load_dir()

    def load_dir(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.path_label.config(text=self.current_dir)
        try:
            entries = sorted(
                [
                    f.name
                    for f in os.scandir(self.current_dir)
                    if f.is_dir() and not f.name.startswith(".")
                ],
                key=str.lower,
            )
            for entry in entries:
                self.tree.insert("", tk.END, values=(entry,))
        except PermissionError:
            messagebox.showerror("Error", "Permission Denied")
            self.go_up()

    def go_up(self):
        self.current_dir = os.path.dirname(self.current_dir)
        self.load_dir()

    def on_double_click(self, event):
        sel = self.tree.selection()
        if sel:
            folder_name = self.tree.item(sel[0])["values"][0]
            self.current_dir = os.path.join(self.current_dir, folder_name)
            self.load_dir()

    def select(self):
        self.result = self.current_dir
        self.destroy()


# --- SETTINGS WINDOW ---
class SettingsWindow(tk.Toplevel):
    def __init__(self, launcher_instance):
        super().__init__(launcher_instance.root)
        self.launcher = launcher_instance
        self.title("Settings")
        self.geometry("500x320")
        self.configure(bg=BG_MAIN)
        self.transient(launcher_instance.root)
        self.grab_set()

        tk.Label(
            self,
            text="Application Settings",
            bg=BG_MAIN,
            fg=ACCENT,
            font=("Segoe UI", 12, "bold"),
        ).pack(pady=15)

        # Editor Row
        tk.Label(
            self, text="Editor Command (e.g., code, zed):", bg=BG_MAIN, fg=FG_TEXT
        ).pack(anchor="w", padx=20)
        self.ed_entry = tk.Entry(
            self, bg=BG_STRIPE, fg=FG_TEXT, insertbackground=FG_TEXT, borderwidth=0
        )
        self.ed_entry.insert(0, EDITOR_COMMAND)
        self.ed_entry.pack(fill=tk.X, padx=20, pady=5, ipady=4)

        # Path Row
        tk.Label(self, text="Search Path:", bg=BG_MAIN, fg=FG_TEXT).pack(
            anchor="w", padx=20, pady=(10, 0)
        )
        path_frame = tk.Frame(self, bg=BG_MAIN)
        path_frame.pack(fill=tk.X, padx=20, pady=5)

        self.path_entry = tk.Entry(
            path_frame,
            bg=BG_STRIPE,
            fg=FG_TEXT,
            insertbackground=FG_TEXT,
            borderwidth=0,
        )
        self.path_entry.insert(0, BASE_PATH)
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)

        tk.Button(
            path_frame,
            text="Browse...",
            command=self.browse_folder,
            bg=BG_HEADER,
            fg=FG_TEXT,
            relief="flat",
            padx=10,
        ).pack(side=tk.LEFT, padx=(5, 0))

        # Save
        tk.Button(
            self,
            text="SAVE & REFRESH",
            command=self.save,
            bg=SUCCESS,
            fg="white",
            relief="flat",
            font=("Segoe UI", 9, "bold"),
        ).pack(pady=25, padx=20, fill=tk.X, ipady=8)

    def browse_folder(self):
        browser = DarkFolderBrowser(self, self.path_entry.get())
        self.wait_window(browser)  # Wait for browser to close
        if browser.result:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, browser.result)

    def save(self):
        new_editor = self.ed_entry.get().strip()
        new_path = self.path_entry.get().strip()
        if not os.path.isdir(os.path.expanduser(new_path)):
            messagebox.showerror("Error", "Invalid path.")
            return

        set_key(ENV_PATH, "EDITOR_COMMAND", new_editor)
        set_key(ENV_PATH, "BASE_PATH", new_path)
        global EDITOR_COMMAND, BASE_PATH
        EDITOR_COMMAND, BASE_PATH = new_editor, new_path
        self.launcher.refresh_data()
        self.destroy()


class DarkRepoLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("Git Repo Dashboard")
        self.root.geometry("550x650")
        self.root.configure(bg=BG_MAIN)

        # CLEAN EXIT PROTOCOLS
        self.root.protocol("WM_DELETE_WINDOW", self.quit_app)
        self.root.bind("<Escape>", self.quit_app)

        self.sort_reverse = {"Name": False, "Last Commit": True}
        self.all_repos = []

        # Style Configuration
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure(
            "Treeview",
            background=BG_MAIN,
            foreground=FG_TEXT,
            fieldbackground=BG_MAIN,
            borderwidth=0,
            font=("Segoe UI", 10),
        )
        self.style.map(
            "Treeview",
            background=[("selected", SELECTED)],
            foreground=[("selected", "white")],
        )
        self.style.configure(
            "Treeview.Heading",
            background=BG_HEADER,
            foreground=ACCENT,
            relief="flat",
            font=("Segoe UI", 10, "bold"),
        )
        self.style.map("Treeview.Heading", background=[("active", HOVER)])

        # Top Bar
        top_frame = tk.Frame(root, bg=BG_MAIN)
        top_frame.pack(fill=tk.X, padx=15, pady=(15, 5))
        tk.Label(
            top_frame,
            text="SEARCH",
            bg=BG_MAIN,
            fg=ACCENT,
            font=("Segoe UI", 8, "bold"),
        ).pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.update_list)
        self.search_entry = tk.Entry(
            top_frame,
            textvariable=self.search_var,
            bg=BG_STRIPE,
            fg=FG_TEXT,
            insertbackground=FG_TEXT,
            borderwidth=0,
            font=("Segoe UI", 11),
        )
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, ipady=4)
        self.search_entry.focus_set()

        # Refresh & Settings Buttons
        self.btn_refresh = tk.Button(
            top_frame,
            text="↻",
            command=self.refresh_data,
            bg=BG_HEADER,
            fg=FG_TEXT,
            font=("Segoe UI", 12, "bold"),
            relief="flat",
            padx=8,
        )
        self.btn_refresh.pack(side=tk.LEFT, padx=2)

        self.btn_settings = tk.Button(
            top_frame,
            text="⚙",
            command=self.open_settings,
            bg=BG_HEADER,
            fg=FG_TEXT,
            font=("Segoe UI", 12),
            relief="flat",
            padx=8,
        )
        self.btn_settings.pack(side=tk.LEFT, padx=2)

        # Table
        self.tree_frame = tk.Frame(root, bg=BG_MAIN)
        self.tree_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        self.tree = ttk.Treeview(
            self.tree_frame, columns=("Name", "Last Commit"), show="headings"
        )
        self.tree.heading(
            "Name", text=" NAME", command=lambda: self.sort_column("Name")
        )
        self.tree.heading(
            "Last Commit",
            text=" LAST COMMIT",
            command=lambda: self.sort_column("Last Commit"),
        )
        self.tree.column("Name", width=300)
        self.tree.column("Last Commit", width=100, anchor="center")
        self.tree.tag_configure("oddrow", background=BG_MAIN)
        self.tree.tag_configure("evenrow", background=BG_STRIPE)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tree.bind("<Double-1>", self.open_repo)
        self.tree.bind("<Return>", self.open_repo)

        # Status & Button
        self.status_var = tk.StringVar()
        tk.Label(
            root,
            textvariable=self.status_var,
            bg=BG_MAIN,
            fg="#666666",
            font=("Segoe UI", 9),
        ).pack(anchor="w", padx=15)

        self.btn_open = tk.Button(
            root,
            text=f"OPEN IN {EDITOR_COMMAND.upper()}",
            command=self.open_repo,
            bg=SUCCESS,
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            activebackground="#3fb950",
            cursor="hand2",
        )
        self.btn_open.pack(fill=tk.X, padx=15, pady=15, ipady=8)

        self.refresh_data()

    def open_settings(self):
        SettingsWindow(self)

    def quit_app(self, event=None):
        # This breaks the mainloop AND kills the underlying Tcl interpreter
        self.root.quit()
        self.root.destroy()
        os._exit(0)  # The most "forceful" exit available in Python

    def refresh_data(self):
        self.all_repos = get_git_repos(BASE_PATH)
        col = "Last Commit" if self.sort_reverse["Last Commit"] else "Name"
        self.sort_column(col, toggle=False)
        self.btn_open.config(text=f"OPEN IN {EDITOR_COMMAND.upper()}")

    def sort_column(self, col, toggle=True):
        reverse = self.sort_reverse[col]
        self.all_repos.sort(
            key=lambda x: x["name"].lower() if col == "Name" else x["mtime"],
            reverse=reverse,
        )
        if toggle:
            self.sort_reverse[col] = not reverse
        self.update_list()

    def update_list(self, *args):
        search_term = self.search_var.get().lower()
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.displayed_paths = []
        count = 0
        for repo in self.all_repos:
            if search_term in repo["name"].lower():
                tag = "evenrow" if count % 2 == 0 else "oddrow"
                self.tree.insert(
                    "",
                    tk.END,
                    values=(f"  {repo['name']}", repo["time_ago"]),
                    tags=(tag,),
                )
                self.displayed_paths.append(repo["path"])
                count += 1
        self.status_var.set(f"Found {count} repositories")

    def open_repo(self, event=None):
        selection = self.tree.selection()
        if selection:
            index = self.tree.index(selection[0])
            # Popen starts Zed and lets Python continue/exit immediately
            subprocess.Popen(
                [EDITOR_COMMAND, self.displayed_paths[index]],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )


if __name__ == "__main__":
    root = tk.Tk()
    try:
        app = DarkRepoLauncher(root)
        root.mainloop()
    except KeyboardInterrupt:
        sys.exit(0)

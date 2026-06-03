"""
╔══════════════════════════════════════════════════════════════╗
║   Facebook Toolkit — UID Converter & 2FA Code Extractor     ║
╚══════════════════════════════════════════════════════════════╝

Main entry point.  Presents a menu and delegates to the
selected tool module.

Tools:
  1. Facebook Link → UID / Phone Number Converter
  2. 2FA Code Extractor  (drop 6-digit codes from text)

Run:  python main.py
"""

import sys
import os

# Ensure the script directory is on the path so sibling modules import cleanly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tool_fb_to_uid   import run_tool1
from tool_2fa_extractor import run_tool2


# ──────────────────────────────────────────────
#  ASCII Art / Branding
# ──────────────────────────────────────────────

LOGO = r"""
  ╔══════════════════════════════════════════════════════════════╗
  ║                                                              ║
  ║      ███████╗ █████╗  ██████╗████████╗██╗  ██╗             ║
  ║      ██╔════╝██╔══██╗██╔════╝╚══██╔══╝██║  ██║             ║
  ║      █████╗  ███████║██║        ██║   ███████║             ║
  ║      ██╔══╝  ██╔══██║██║        ██║   ██╔══██║             ║
  ║      ██║     ██║  ██║╚██████╗   ██║   ██║  ██║             ║
  ║      ╚═╝     ╚═╝  ╚═╝ ╚═════╝   ╚═╝   ╚═╝  ╚═╝             ║
  ║                                                              ║
  ║          Toolkit  —  UID Converter  &  2FA Extractor        ║
  ╚══════════════════════════════════════════════════════════════╝
"""

MENU = """
  ┌─────────────────────────────────────────────┐
  │             M A I N   M E N U               │
  ├─────────────────────────────────────────────┤
  │                                             │
  │   [1]  Facebook Link → UID / Phone Number  │
  │                                             │
  │   [2]  2FA Code Extractor (drop 6 digits)  │
  │                                             │
  │   [3]  Launch GUI  (desktop window)        │
  │                                             │
  │   [4]  About / Help                        │
  │                                             │
  │   [0]  Exit                                │
  │                                             │
  └─────────────────────────────────────────────┘
"""


# ──────────────────────────────────────────────
#  About / Help
# ──────────────────────────────────────────────

def show_about():
    print()
    print("=" * 62)
    print("  ABOUT / HELP")
    print("=" * 62)
    print("""
  TOOL 1 — Facebook Link → UID / Phone Number Converter
  ──────────────────────────────────────────────────────
  Converts Facebook profile URLs into numeric UIDs or usernames.

  Supported URL formats:
    • https://www.facebook.com/profile.php?id=100012345678901
    • https://www.facebook.com/100012345678901
    • https://www.facebook.com/username
    • https://fb.com/username
    • https://m.facebook.com/username
    • https://www.facebook.com/people/name/100012345678901

  Batch mode lets you paste many links at once and export to JSON.
  With a Facebook Graph API access token you can also resolve
  usernames → numeric UIDs.

  Phone-number extraction scans the input text for phone numbers
  that may appear alongside the link.

  TOOL 2 — 2FA Code Extractor (drop 6-digit codes)
  ─────────────────────────────────────────────────
  Detects and extracts 6-digit Two-Factor Authentication codes
  from SMS messages, emails, notifications, logs, or any text.

  Modes:
    • Single extract  — paste one message
    • Batch extract   — paste multiple messages separated by '---'
    • Drop / remove   — strip 2FA codes out of text
    • Clipboard monitor — auto-extract codes as you copy them
      (requires: pip install pyperclip)
    • File scan       — scan an entire file for 2FA codes

  Confidence levels:
    HIGH   → code found near a known 2FA keyword (e.g. "Facebook")
    MEDIUM → code found as a standalone 6-digit number
    LOW    → any 6-digit number in the text

  Dependencies (optional):
    pip install requests pyperclip
""")
    print("=" * 62)
    input("  Press Enter to continue...")


# ──────────────────────────────────────────────
#  Launch GUI
# ──────────────────────────────────────────────

def launch_gui():
    print()
    print("  Launching GUI…")
    try:
        from gui import FacebookToolkitApp
        app = FacebookToolkitApp()
        app.mainloop()
    except ImportError as e:
        print(f"  [!] Could not launch GUI: {e}")
        print("      Make sure customtkinter is installed:  pip install customtkinter")
        input("  Press Enter to continue…")


# ──────────────────────────────────────────────
#  Main Loop
# ──────────────────────────────────────────────

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def main():
    while True:
        clear_screen()
        print(LOGO)
        print(MENU)

        choice = input("  ► Select an option: ").strip()

        if choice == "1":
            clear_screen()
            run_tool1()
        elif choice == "2":
            clear_screen()
            run_tool2()
        elif choice == "3":
            launch_gui()
        elif choice == "4":
            show_about()
        elif choice in ("0", "q", "quit", "exit"):
            print()
            print("  Goodbye!")
            print()
            sys.exit(0)
        else:
            print("  [!] Invalid option. Please try again.")
            input("  Press Enter to continue...")


if __name__ == "__main__":
    main()

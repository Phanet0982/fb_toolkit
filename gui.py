"""
╔══════════════════════════════════════════════════════════════╗
║   Facebook Toolkit — Dashboard GUI                          ║
║   Modern tool-directory UI built with CustomTkinter         ║
╚══════════════════════════════════════════════════════════════╝

Run:  python gui.py
"""

import sys, os, json, threading, time, hmac, hashlib, struct
from datetime import datetime
from tkinter import filedialog, messagebox
import customtkinter as ctk

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tool_fb_to_uid      import (extract_uid_from_url, extract_phone_from_text,
                                  resolve_username_to_uid)
from tool_2fa_extractor  import (extract_2fa_codes, extract_latest_code,
                                  drop_2fa_code)
from tool_modals         import (FakeIDModal, HotmailModal, CronJobsModal,
                                  CheckLiveBMModal, CheckBMVerifiedModal,
                                  CheckLinkBMModal, CheckBMNameModal,
                                  CheckLiveIGModal, DownloadIGModal)

# ──────────────────────────────────────────────────────────────
#  Theme
# ──────────────────────────────────────────────────────────────
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

LIGHT = {
    "bg":          "#f8f9fa",
    "bg_header":   "#ffffff",
    "bg_card":     "#ffffff",
    "bg_input":    "#f1f3f5",
    "bg_modal":    "#ffffff",
    "accent":      "#3b82f6",
    "accent_hov":  "#2563eb",
    "text":        "#1a1a2e",
    "text_dim":    "#6b7280",
    "text_muted":  "#9ca3af",
    "border":      "#e5e7eb",
    "border_card": "#e2e5e9",
    "section_bg":  "#f1f3f5",
    "shadow":      "#d1d5db",
    "success":     "#16a34a",
    "warning":     "#d97706",
    "error":       "#dc2626",
    "icon_color":  "#374151",
}

DARK = {
    "bg":          "#0f172a",
    "bg_header":   "#1e293b",
    "bg_card":     "#1e293b",
    "bg_input":    "#334155",
    "bg_modal":    "#1e293b",
    "accent":      "#3b82f6",
    "accent_hov":  "#60a5fa",
    "text":        "#f1f5f9",
    "text_dim":    "#94a3b8",
    "text_muted":  "#64748b",
    "border":      "#334155",
    "border_card": "#475569",
    "section_bg":  "#0f172a",
    "shadow":      "#000000",
    "success":     "#22c55e",
    "warning":     "#f59e0b",
    "error":       "#ef4444",
    "icon_color":  "#cbd5e1",
}

CLR = dict(LIGHT)
IS_DARK = False

# Fonts
F_TITLE      = ("Segoe UI", 14, "bold")
F_SECTION    = ("Segoe UI", 11, "bold")
F_CARD_TITLE = ("Segoe UI", 11, "bold")
F_CARD_SUB   = ("Segoe UI", 9)
F_BODY       = ("Segoe UI", 11)
F_SMALL      = ("Segoe UI", 9)
F_MONO       = ("Consolas", 11)
F_MONO_SM    = ("Consolas", 10)
F_HEADER     = ("Segoe UI", 10)

# Layout (responsive — columns auto-adjust)
CARD_W = 200
CARD_H = 72
CARD_RADIUS = 10
CARD_BORDER = 1
GRID_PAD_X = 16
GRID_PAD_Y = 14
SECTION_GAP = 28
CARD_MIN_W = 200  # minimum card width for column calculation


# ──────────────────────────────────────────────────────────────
#  TOTP Generator (RFC 6238 — pure Python, no pyotp needed)
# ──────────────────────────────────────────────────────────────

def _base32_decode(secret: str) -> bytes:
    """Decode a base32 secret (with or without spaces/padding)."""
    s = secret.upper().replace(" ", "").replace("-", "")
    # Add padding if needed
    pad = (8 - len(s) % 8) % 8
    s += "=" * pad
    import base64
    return base64.b32decode(s)


def generate_totp(secret: str, digits: int = 6, period: int = 30) -> str:
    """Generate a TOTP code from a base32-encoded secret."""
    try:
        key = _base32_decode(secret)
        t = int(time.time()) // period
        msg = struct.pack(">Q", t)
        h = hmac.new(key, msg, hashlib.sha1).digest()
        offset = h[-1] & 0x0F
        code = struct.unpack(">I", h[offset:offset+4])[0] & 0x7FFFFFFF
        return str(code % 10**digits).zfill(digits)
    except Exception:
        return ""


def time_remaining(period: int = 30) -> int:
    """Seconds remaining in the current TOTP window."""
    return period - (int(time.time()) % period)


# ──────────────────────────────────────────────────────────────
#  Tool data  (each entry becomes a card)
# ──────────────────────────────────────────────────────────────
TOOLS = {
    "POPULAR TOOLS": [
        {"id": "2fa",      "icon": "\U0001F512", "title": "Two-Factor\nAuthentication"},
        {"id": "fakeid",   "icon": "\U0001F4C7", "title": "Create Fake\nID Card"},
        {"id": "hotmail",  "icon": "\u2709\uFE0F",  "title": "Quick Read\nHotmail"},
        {"id": "cron",     "icon": "\u23F0",     "title": "Cron Jobs\nManager"},
    ],
    "FACEBOOK TOOLS": [
        {"id": "fb_uid",   "icon": "\U0001F464", "title": "Check Live UID",   "sub": "Facebook"},
        {"id": "fb_bm",    "icon": "\U0001F4BC", "title": "Check Live BM"},
        {"id": "fb_bmv",   "icon": "\u2705",     "title": "Check BM Verified"},
        {"id": "fb_link",  "icon": "\U0001F517", "title": "Check Link BM"},
        {"id": "fb_name",  "icon": "\U0001F465", "title": "Check BM Name"},
        {"id": "fb_find",  "icon": "\U0001F50D", "title": "Find Facebook ID"},
    ],
    "INSTAGRAM TOOLS": [
        {"id": "ig_live",  "icon": "\U0001F4F7", "title": "Check Live\nInstagram"},
        {"id": "ig_dl",    "icon": "\u2B07\uFE0F",  "title": "Download Instagram", "sub": "Reels/Stories/Videos"},
    ],
}


# ══════════════════════════════════════════════════════════════
#  Tool Card Widget
# ══════════════════════════════════════════════════════════════

class ToolCard(ctk.CTkFrame):
    """A single dashboard tool card (icon + title + optional subtitle)."""

    def __init__(self, parent, icon: str, title: str, sub: str = "",
                 on_click=None):
        super().__init__(
            parent, height=CARD_H,
            corner_radius=CARD_RADIUS,
            fg_color=CLR["bg_card"],
            border_color=CLR["border_card"],
            border_width=CARD_BORDER,
        )
        self.grid_propagate(False)
        self.grid_columnconfigure(1, weight=1)

        # Icon label (left)
        self.icon_lbl = ctk.CTkLabel(
            self, text=icon, font=("Segoe UI Emoji", 22),
            text_color=CLR["icon_color"], width=46)
        self.icon_lbl.grid(row=0, column=0, padx=(14, 0), pady=0, sticky="w")

        # Text frame (right)
        txt_frame = ctk.CTkFrame(self, fg_color="transparent")
        txt_frame.grid(row=0, column=1, sticky="w", padx=(6, 10), pady=10)

        self.title_lbl = ctk.CTkLabel(
            txt_frame, text=title, font=F_CARD_TITLE,
            text_color=CLR["text"], anchor="w", justify="left")
        self.title_lbl.pack(anchor="w")

        if sub:
            self.sub_lbl = ctk.CTkLabel(
                txt_frame, text=sub, font=F_CARD_SUB,
                text_color=CLR["text_dim"], anchor="w")
            self.sub_lbl.pack(anchor="w")

        # Click binding on all child widgets
        for widget in (self, self.icon_lbl, self.title_lbl, txt_frame):
            widget.bind("<Button-1>", self._on_click)
            if hasattr(widget, "winfo_children"):
                for child in widget.winfo_children():
                    child.bind("<Button-1>", self._on_click)

        self._on_click_cb = on_click

    def _on_click(self, event=None):
        if self._on_click_cb:
            self._on_click_cb()

    def retheme(self):
        """Update colors when theme changes."""
        self.configure(fg_color=CLR["bg_card"], border_color=CLR["border_card"])
        self.icon_lbl.configure(text_color=CLR["icon_color"])
        self.title_lbl.configure(text_color=CLR["text"])
        if hasattr(self, "sub_lbl"):
            self.sub_lbl.configure(text_color=CLR["text_dim"])


# ══════════════════════════════════════════════════════════════
#  Main Dashboard Window
# ══════════════════════════════════════════════════════════════

class DashboardApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("FB Toolkit — Dashboard")
        self.geometry("1060x720")
        self.minsize(900, 580)
        self.configure(fg_color=CLR["bg"])

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # ── Handle clean window close ──────────────────────────────
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # ── Card references (init before _build_body) ─────────────
        self.all_cards: list[ToolCard] = []

        # ── Header bar (row 0) ────────────────────────────────────
        self.header = ctk.CTkFrame(self, height=56, corner_radius=0,
                                   fg_color=CLR["bg_header"])
        self.header.grid(row=0, column=0, sticky="new")
        self.header.grid_columnconfigure(0, weight=1)
        self.header.grid_propagate(False)
        self._build_header()

        # ── Scrollable body (row 1) ───────────────────────────────
        self.body = ctk.CTkScrollableFrame(self, fg_color=CLR["bg"])
        self.body.grid(row=1, column=0, sticky="nsew")
        self.body.grid_columnconfigure(0, weight=1)
        self._section_grids: list[ctk.CTkFrame] = []
        self._build_body()
        # Bind resize for responsive card reflow
        self.bind("<Configure>", self._on_resize)

    # ── Header ────────────────────────────────────────────────────
    def _build_header(self):
        inner = ctk.CTkFrame(self.header, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=28, pady=0)

        # Left: Search (responsive — stretches with window)
        search_frame = ctk.CTkFrame(inner, fg_color=CLR["bg_input"],
                                    corner_radius=8, height=36,
                                    border_color=CLR["border"], border_width=1)
        search_frame.pack(side="left", fill="x", expand=True, padx=(0, 12), pady=10)
        search_frame.pack_propagate(False)

        ctk.CTkLabel(search_frame, text="\U0001F50D", font=("Segoe UI Emoji", 12),
                     text_color=CLR["text_muted"]).pack(side="left", padx=(10, 6))
        ctk.CTkLabel(search_frame, text="Search Tools", font=F_HEADER,
                     text_color=CLR["text_muted"]).pack(side="left")
        # Ctrl+K badge
        badge = ctk.CTkLabel(search_frame, text="Ctrl+K", font=("Segoe UI", 8),
                             text_color=CLR["text_muted"], fg_color=CLR["border"],
                             corner_radius=4, width=42, height=20)
        badge.pack(side="right", padx=(0, 10))

        # Right: controls
        right = ctk.CTkFrame(inner, fg_color="transparent")
        right.pack(side="right")

        # Theme toggle (moon)
        self.theme_btn = ctk.CTkButton(
            right, text="\u263E", width=36, height=36, corner_radius=8,
            font=("Segoe UI", 16), fg_color="transparent",
            text_color=CLR["icon_color"], hover_color=CLR["bg_input"],
            command=self._toggle_theme)
        self.theme_btn.pack(side="left", padx=(0, 4), pady=10)

        # Language (flag)
        ctk.CTkButton(
            right, text="\U0001F1EC\U0001F1E7", width=36, height=36,
            corner_radius=8, font=("Segoe UI Emoji", 13),
            fg_color="transparent", hover_color=CLR["bg_input"],
            command=lambda: None
        ).pack(side="left", padx=(0, 8), pady=10)

        # Sign In
        ctk.CTkButton(
            right, text="Sign In", width=64, height=36, corner_radius=8,
            font=F_HEADER, fg_color="transparent",
            text_color=CLR["text_dim"], hover_color=CLR["bg_input"],
            command=lambda: None
        ).pack(side="left", padx=(0, 6), pady=10)

        # Sign Up
        ctk.CTkButton(
            right, text="Sign Up", width=80, height=36, corner_radius=8,
            font=F_HEADER, fg_color=CLR["accent"],
            text_color="white", hover_color=CLR["accent_hov"],
            command=lambda: None
        ).pack(side="left", pady=10)

    # ── Body (tool sections) ──────────────────────────────────────
    def _build_body(self):
        wrapper = ctk.CTkFrame(self.body, fg_color="transparent")
        wrapper.pack(fill="both", expand=True, padx=40, pady=(24, 40))
        wrapper.grid_columnconfigure(0, weight=1)

        section_row = 0
        for section_name, tools in TOOLS.items():
            # Section label
            ctk.CTkLabel(
                wrapper, text=section_name, font=F_SECTION,
                text_color=CLR["text_dim"], anchor="w"
            ).grid(row=section_row, column=0, sticky="w",
                   pady=(0 if section_row == 0 else SECTION_GAP, 12))
            section_row += 1

            # Card grid frame (responsive)
            grid = ctk.CTkFrame(wrapper, fg_color="transparent")
            grid.grid(row=section_row, column=0, sticky="ew")
            grid._tools = tools  # store for reflow
            self._section_grids.append(grid)

            for i, tool in enumerate(tools):
                card = ToolCard(
                    grid,
                    icon=tool["icon"],
                    title=tool["title"],
                    sub=tool.get("sub", ""),
                    on_click=lambda tid=tool["id"]: self._open_tool(tid),
                )
                card._tool_idx = i
                card.grid(row=0, column=i, padx=(0, GRID_PAD_X),
                          pady=(0, GRID_PAD_Y))
                self.all_cards.append(card)

            section_row += 1

        # Initial layout
        self.after(50, self._reflow_cards)

    # ── Responsive card reflow ────────────────────────────────────
    def _on_resize(self, event=None):
        if event and event.widget == self:
            self._reflow_cards()

    def _reflow_cards(self):
        """Recalculate card columns based on available width."""
        avail_w = self.winfo_width() - 120  # account for padding + scrollbar
        if avail_w < 200:
            return
        cols = max(1, avail_w // (CARD_MIN_W + GRID_PAD_X))
        cols = min(cols, 6)  # cap at 6 columns

        for grid in self._section_grids:
            # Reconfigure columns
            for c in range(cols):
                grid.grid_columnconfigure(c, weight=1, minsize=0)

            # Reposition cards
            for card in grid.winfo_children():
                if hasattr(card, '_tool_idx'):
                    r, c = divmod(card._tool_idx, cols)
                    card.grid(row=r, column=c, padx=(0, GRID_PAD_X),
                              pady=(0, GRID_PAD_Y), sticky="ew")

    # ── Theme toggle ──────────────────────────────────────────────
    def _toggle_theme(self):
        global CLR, IS_DARK
        IS_DARK = not IS_DARK
        if IS_DARK:
            ctk.set_appearance_mode("dark")
            CLR.update(DARK)
            self.theme_btn.configure(text="\u2600")  # sun
        else:
            ctk.set_appearance_mode("light")
            CLR.update(LIGHT)
            self.theme_btn.configure(text="\u263E")  # moon

        # Re-theme core widgets
        self.configure(fg_color=CLR["bg"])
        self.header.configure(fg_color=CLR["bg_header"])
        self.body.configure(fg_color=CLR["bg"])
        for card in self.all_cards:
            card.retheme()

    # ── Clean shutdown ────────────────────────────────────────────
    def _on_close(self):
        """Cleanly destroy the app and all child windows."""
        # Destroy all Toplevel windows first
        for child in self.winfo_children():
            if isinstance(child, ctk.CTkToplevel):
                child.destroy()
        self.destroy()

    # ── Open tool ─────────────────────────────────────────────────
    def _open_tool(self, tool_id: str):
        """Open a modal Toplevel window for the selected tool."""
        dispatch = {
            "2fa":       lambda: TwoFAModal(self),
            "fb_uid":    lambda: FBUidModal(self),
            "fb_find":   lambda: FindFBIdModal(self),
            "fakeid":    lambda: FakeIDModal(self),
            "hotmail":   lambda: HotmailModal(self),
            "cron":      lambda: CronJobsModal(self),
            "fb_bm":     lambda: CheckLiveBMModal(self),
            "fb_bmv":    lambda: CheckBMVerifiedModal(self),
            "fb_link":   lambda: CheckLinkBMModal(self),
            "fb_name":   lambda: CheckBMNameModal(self),
            "ig_live":   lambda: CheckLiveIGModal(self),
            "ig_dl":     lambda: DownloadIGModal(self),
        }
        factory = dispatch.get(tool_id)
        if factory:
            factory().grab_set()
        else:
            ComingSoonModal(self, tool_id).grab_set()


# ══════════════════════════════════════════════════════════════
#  Modal base
# ══════════════════════════════════════════════════════════════

class ToolModal(ctk.CTkToplevel):
    """Base modal dialog for a tool."""

    def __init__(self, parent, title: str, width=640, height=560):
        super().__init__(parent)
        self.title(title)
        self.geometry(f"{width}x{height}")
        self.minsize(500, 400)
        self.configure(fg_color=CLR["bg_modal"])
        self.resizable(True, True)

        # Centre on parent
        self.update_idletasks()
        px = parent.winfo_x() + (parent.winfo_width() - width) // 2
        py = parent.winfo_y() + (parent.winfo_height() - height) // 2
        self.geometry(f"+{max(0, px)}+{max(0, py)}")

    def _make_textbox(self, parent, *, height=100, state="normal"):
        return ctk.CTkTextbox(
            parent, height=height, font=F_MONO_SM, corner_radius=8,
            fg_color=CLR["bg_input"], border_color=CLR["border"],
            border_width=1, state=state, text_color=CLR["text"])

    def _make_entry(self, parent, *, placeholder="", show=None, height=38):
        kw = dict(placeholder_text=placeholder, font=F_MONO, height=height,
                  corner_radius=8, border_color=CLR["border"],
                  fg_color=CLR["bg_input"], text_color=CLR["text"])
        if show:
            kw["show"] = show
        return ctk.CTkEntry(parent, **kw)

    def _make_button(self, parent, *, text, command, width=120, style="primary"):
        colors = {
            "primary":   (CLR["accent"], CLR["accent_hov"], "white"),
            "secondary": ("#8b5cf6", "#7c3aed", "white"),
            "success":   (CLR["success"], "#15803d", "white"),
            "danger":    (CLR["error"], "#b91c1c", "white"),
        }
        fg, hov, tc = colors.get(style, colors["primary"])
        return ctk.CTkButton(parent, text=text, width=width, height=38,
                             corner_radius=8, font=F_BODY,
                             fg_color=fg, hover_color=hov, text_color=tc,
                             command=command)

    def _write_box(self, widget, text):
        st = widget.cget("state")
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", text)
        widget.configure(state=st)


# ──────────────────────────────────────────────────────────────
#  Modal: 2FA — Google Authenticator Style
# ──────────────────────────────────────────────────────────────

class TwoFAModal(ToolModal):
    def __init__(self, parent):
        super().__init__(parent, "Two-Factor Authentication", width=760, height=700)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._auto_timer = None   # for auto-refresh

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew", padx=32, pady=24)
        scroll.grid_columnconfigure(0, weight=1)
        r = 0

        # ═══════════════════════════════════════════════════════════
        #  SECTION 1 — Title
        # ═══════════════════════════════════════════════════════════
        title_row = ctk.CTkFrame(scroll, fg_color="transparent")
        title_row.grid(row=r, column=0, sticky="ew", pady=(0, 4)); r += 1

        # Lock icon badge
        badge = ctk.CTkFrame(title_row, width=42, height=42, corner_radius=10,
                             fg_color="#dbeafe")
        badge.pack(side="left", padx=(0, 12))
        badge.pack_propagate(False)
        ctk.CTkLabel(badge, text="\U0001F512", font=("Segoe UI Emoji", 20)).pack(
            expand=True)

        title_text = ctk.CTkFrame(title_row, fg_color="transparent")
        title_text.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(title_text,
                     text="Two-Factor Authentication - Google Authenticator",
                     font=("Segoe UI", 16, "bold"),
                     text_color=CLR["text"], anchor="w").pack(anchor="w")
        ctk.CTkLabel(title_text,
                     text="Generate 2FA codes for authentication",
                     font=F_BODY, text_color=CLR["text_dim"],
                     anchor="w").pack(anchor="w", pady=(2, 0))

        # ═══════════════════════════════════════════════════════════
        #  SECTION 2 — Secret Key Input
        # ═══════════════════════════════════════════════════════════
        ctk.CTkLabel(scroll, text="Secret Key", font=F_BODY,
                     text_color=CLR["text_dim"]).grid(
            row=r, column=0, sticky="w", pady=(16, 6)); r += 1

        key_row = ctk.CTkFrame(scroll, fg_color="transparent")
        key_row.grid(row=r, column=0, sticky="ew", pady=(0, 6)); r += 1
        key_row.grid_columnconfigure(0, weight=1)

        self.secret_entry = ctk.CTkEntry(
            key_row, placeholder_text="Enter your base32 secret key (e.g. JBSWY3DPEHPK3PXP)",
            font=F_MONO, height=42, corner_radius=8,
            border_color=CLR["border"], fg_color=CLR["bg_input"],
            text_color=CLR["text"])
        self.secret_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        ctk.CTkButton(key_row, text="\U0001F4C4  Bulk Mode", width=120, height=42,
                      corner_radius=8, font=F_BODY,
                      fg_color=CLR["bg_input"], border_color=CLR["border"],
                      border_width=1, text_color=CLR["text"],
                      hover_color=CLR["border"],
                      command=self._bulk_mode).pack(side="right")

        # Powered by label
        ctk.CTkLabel(scroll, text="Powered by Google Authenticator",
                     font=F_SMALL, text_color=CLR["text_muted"]).grid(
            row=r, column=0, pady=(4, 16)); r += 1

        # ═══════════════════════════════════════════════════════════
        #  SECTION 3 — Generate Button
        # ═══════════════════════════════════════════════════════════
        self.gen_btn = ctk.CTkButton(
            scroll, text="\U0001F511  Generate 2FA Code",
            font=("Segoe UI", 13, "bold"), height=48, corner_radius=10,
            fg_color=CLR["accent"], hover_color=CLR["accent_hov"],
            text_color="white", command=self._generate)
        self.gen_btn.grid(row=r, column=0, sticky="ew", pady=(0, 16)); r += 1

        # ═══════════════════════════════════════════════════════════
        #  SECTION 4 — Result Display (hidden until generated)
        # ═══════════════════════════════════════════════════════════
        self.result_card = ctk.CTkFrame(scroll, corner_radius=12,
                                        fg_color=CLR["bg_card"],
                                        border_color=CLR["border"],
                                        border_width=1)
        self.result_card.grid(row=r, column=0, sticky="ew", pady=(0, 8))
        self.result_card.grid_columnconfigure(1, weight=1)

        inner = ctk.CTkFrame(self.result_card, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=16)

        code_row = ctk.CTkFrame(inner, fg_color="transparent")
        code_row.pack(fill="x")

        ctk.CTkLabel(code_row, text="Current Code:", font=F_BODY,
                     text_color=CLR["text_dim"]).pack(side="left")

        self.code_label = ctk.CTkLabel(
            code_row, text="------", font=("Consolas", 28, "bold"),
            text_color=CLR["accent"])
        self.code_label.pack(side="left", padx=(12, 0))

        self.timer_label = ctk.CTkLabel(
            code_row, text="", font=("Segoe UI", 11),
            text_color=CLR["text_muted"])
        self.timer_label.pack(side="right")

        # Timer progress bar
        self.timer_bar = ctk.CTkProgressBar(inner, height=4, corner_radius=2,
                                            fg_color=CLR["border"],
                                            progress_color=CLR["accent"])
        self.timer_bar.pack(fill="x", pady=(10, 0))
        self.timer_bar.set(1.0)

        # Copy button
        ctk.CTkButton(inner, text="\U0001F4CB  Copy Code", width=120, height=32,
                      corner_radius=6, font=F_SMALL,
                      fg_color=CLR["bg_input"], border_color=CLR["border"],
                      border_width=1, text_color=CLR["text"],
                      hover_color=CLR["border"],
                      command=self._copy_code).pack(anchor="w", pady=(8, 0))

        # Initially hide result card
        self.result_card.grid_remove()
        r += 1

        # ═══════════════════════════════════════════════════════════
        #  SECTION 5 — Extract 2FA from text (compact)
        # ═══════════════════════════════════════════════════════════
        extract_frame = ctk.CTkFrame(scroll, corner_radius=12,
                                     fg_color=CLR["bg_card"],
                                     border_color=CLR["border"],
                                     border_width=1)
        extract_frame.grid(row=r, column=0, sticky="ew", pady=(16, 8)); r += 1
        ext_inner = ctk.CTkFrame(extract_frame, fg_color="transparent")
        ext_inner.pack(fill="x", padx=20, pady=16)

        ctk.CTkLabel(ext_inner, text="\u2702\uFE0F  Extract / Drop 2FA Codes from Text",
                     font=F_TITLE, text_color=CLR["text"]).pack(anchor="w",
                                                                  pady=(0, 10))

        self.extract_box = ctk.CTkTextbox(
            ext_inner, height=70, font=F_MONO_SM, corner_radius=8,
            fg_color=CLR["bg_input"], border_color=CLR["border"],
            border_width=1, text_color=CLR["text"])
        self.extract_box.pack(fill="x", pady=(0, 8))
        self.extract_box.insert("1.0", "Paste SMS / email text here\u2026")

        ext_btn_row = ctk.CTkFrame(ext_inner, fg_color="transparent")
        ext_btn_row.pack(fill="x")
        self._make_button(ext_btn_row, text="Extract Codes", width=130,
                          command=self._extract).pack(side="left")
        self._make_button(ext_btn_row, text="Drop Codes", width=110,
                          style="danger",
                          command=self._drop).pack(side="left", padx=(8, 0))

        self.extract_result = ctk.CTkLabel(ext_inner, text="", font=F_MONO_SM,
                                           text_color=CLR["success"], anchor="w",
                                           justify="left")
        self.extract_result.pack(fill="x", pady=(8, 0))

        # ═══════════════════════════════════════════════════════════
        #  SECTION 6 — Saved Secret Keys + Guide Tabs
        # ═══════════════════════════════════════════════════════════
        saved_frame = ctk.CTkFrame(scroll, corner_radius=12,
                                   fg_color=CLR["bg_card"],
                                   border_color=CLR["border"],
                                   border_width=1)
        saved_frame.grid(row=r, column=0, sticky="ew", pady=(16, 8)); r += 1
        sv_inner = ctk.CTkFrame(saved_frame, fg_color="transparent")
        sv_inner.pack(fill="x", padx=20, pady=16)

        # Header row
        sv_header = ctk.CTkFrame(sv_inner, fg_color="transparent")
        sv_header.pack(fill="x", pady=(0, 6))

        sv_title = ctk.CTkFrame(sv_header, fg_color="transparent")
        sv_title.pack(side="left")
        ctk.CTkLabel(sv_title, text="\U0001F511  Saved Secret Keys",
                     font=("Segoe UI", 13, "bold"),
                     text_color=CLR["text"]).pack(anchor="w")
        ctk.CTkLabel(sv_title,
                     text="Login to save and manage your secret keys.",
                     font=F_SMALL, text_color=CLR["text_dim"]).pack(anchor="w")

        ctk.CTkButton(sv_header, text="\U0001F511  Save Your Secret Key",
                      width=180, height=36, corner_radius=8, font=F_BODY,
                      fg_color=CLR["accent"], hover_color=CLR["accent_hov"],
                      text_color="white",
                      command=lambda: messagebox.showinfo(
                          "Save", "Login to save your secret key.")
                      ).pack(side="right")

        # ── Tab bar ───────────────────────────────────────────────
        tab_frame = ctk.CTkFrame(sv_inner, fg_color="transparent")
        tab_frame.pack(fill="x", pady=(14, 10))

        self._active_tab = "Guide"
        self._tab_btns = {}
        for tab_name in ["Guide", "About", "FAQ", "Review"]:
            btn = ctk.CTkButton(
                tab_frame, text=tab_name, width=80, height=32,
                corner_radius=6, font=F_SMALL,
                fg_color=CLR["accent"] if tab_name == "Guide" else "transparent",
                text_color="white" if tab_name == "Guide" else CLR["text_dim"],
                hover_color=CLR["accent_hov"],
                command=lambda t=tab_name: self._switch_tab(t))
            btn.pack(side="left", padx=(0, 6))
            self._tab_btns[tab_name] = btn

        # ── Tab content container ─────────────────────────────────
        self._tab_content = ctk.CTkFrame(sv_inner, fg_color="transparent")
        self._tab_content.pack(fill="x")

        # Guide content (4 steps)
        self._guide_frame = ctk.CTkFrame(self._tab_content, fg_color="transparent")
        self._guide_frame.pack(fill="x")

        steps = [
            ("1", "Login & Add",
             "Login and click the 'Add Secret\nKey' button to start saving\nyour keys."),
            ("2", "Enter Secret Key",
             "Enter your Secret Key and click\nthe 'Add Key' button to save."),
            ("3", "Saved to System",
             "After adding, your Secret Key will\nbe securely saved and auto-\ngenerate 2FA codes."),
            ("4", "Password Protected",
             "Editing or deleting saved secret\nkeys requires password\nverification for security."),
        ]

        steps_row = ctk.CTkFrame(self._guide_frame, fg_color="transparent")
        steps_row.pack(fill="x")
        for i, (num, title, desc) in enumerate(steps):
            steps_row.grid_columnconfigure(i, weight=1, uniform="step")
            step_card = ctk.CTkFrame(steps_row, corner_radius=8,
                                     fg_color=CLR["bg_input"],
                                     border_color=CLR["border"],
                                     border_width=1)
            step_card.grid(row=0, column=i, padx=(0, 8 if i < 3 else 0),
                           pady=(0, 4), sticky="nsew")

            si = ctk.CTkFrame(step_card, fg_color="transparent")
            si.pack(fill="x", padx=12, pady=12)

            # Number circle
            circle = ctk.CTkLabel(si, text=num, width=28, height=28,
                                  corner_radius=14,
                                  font=("Segoe UI", 11, "bold"),
                                  fg_color=CLR["accent"],
                                  text_color="white")
            circle.pack(anchor="w")

            ctk.CTkLabel(si, text=title, font=("Segoe UI", 10, "bold"),
                         text_color=CLR["text"]).pack(anchor="w", pady=(8, 4))
            ctk.CTkLabel(si, text=desc, font=("Segoe UI", 8),
                         text_color=CLR["text_dim"],
                         justify="left", anchor="w").pack(anchor="w")

        # About content
        self._about_frame = ctk.CTkFrame(self._tab_content, fg_color="transparent")
        ctk.CTkLabel(self._about_frame,
                     text="This tool generates Time-based One-Time Passwords (TOTP)\n"
                          "compatible with Google Authenticator, Authy, and other\n"
                          "authenticator apps.\n\n"
                          "Enter your base32-encoded secret key to generate a\n"
                          "6-digit code that refreshes every 30 seconds.",
                     font=F_BODY, text_color=CLR["text"],
                     justify="left").pack(anchor="w", pady=(10, 0))

        # FAQ content
        self._faq_frame = ctk.CTkFrame(self._tab_content, fg_color="transparent")
        ctk.CTkLabel(self._faq_frame,
                     text="Q: What is a Secret Key?\n"
                          "A: A base32-encoded string provided by the service\n"
                          "    when you enable 2FA.\n\n"
                          "Q: Why does the code change?\n"
                          "A: TOTP codes rotate every 30 seconds for security.\n\n"
                          "Q: Can I use spaces in the key?\n"
                          "A: Yes, spaces and dashes are automatically stripped.",
                     font=F_BODY, text_color=CLR["text"],
                     justify="left").pack(anchor="w", pady=(10, 0))

        # Review content
        self._review_frame = ctk.CTkFrame(self._tab_content, fg_color="transparent")
        ctk.CTkLabel(self._review_frame,
                     text="\u2B50\u2B50\u2B50\u2B50\u2B50  No reviews yet.\n\n"
                          "Be the first to review this tool!",
                     font=F_BODY, text_color=CLR["text_dim"],
                     justify="left").pack(anchor="w", pady=(10, 0))

        self._switch_tab("Guide")

    # ── TOTP Generation ──────────────────────────────────────────
    def _generate(self):
        secret = self.secret_entry.get().strip()
        if not secret:
            messagebox.showwarning("Error", "Please enter a Secret Key.")
            return
        code = generate_totp(secret)
        if not code:
            messagebox.showerror("Error",
                                 "Invalid secret key. Make sure it is base32-encoded.")
            return
        self.code_label.configure(text=code)
        self.result_card.grid()
        self._start_auto_refresh(secret)

    def _start_auto_refresh(self, secret):
        """Auto-refresh the code every second."""
        if self._auto_timer:
            self.after_cancel(self._auto_timer)

        def tick():
            remaining = time_remaining()
            self.timer_label.configure(text=f"\u23F1 {remaining}s")
            self.timer_bar.set(remaining / 30.0)
            if remaining <= 5:
                self.timer_bar.configure(progress_color=CLR["error"])
            else:
                self.timer_bar.configure(progress_color=CLR["accent"])
            # Regenerate code when window resets
            if remaining == 30:
                code = generate_totp(secret)
                if code:
                    self.code_label.configure(text=code)
            self._auto_timer = self.after(1000, tick)

        tick()

    def _copy_code(self):
        code = self.code_label.cget("text")
        if code and code != "------":
            self.clipboard_clear()
            self.clipboard_append(code)
            messagebox.showinfo("Copied", f"Code {code} copied to clipboard!")

    def _bulk_mode(self):
        """Open a window to generate codes for multiple secrets."""
        bulk = ctk.CTkToplevel(self)
        bulk.title("Bulk Mode — Multiple Secret Keys")
        bulk.geometry("520x400")
        bulk.configure(fg_color=CLR["bg_modal"])

        frame = ctk.CTkFrame(bulk, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(frame, text="Bulk Mode", font=F_TITLE,
                     text_color=CLR["text"]).pack(anchor="w", pady=(0, 8))
        ctk.CTkLabel(frame,
                     text="Enter one secret key per line.\nGenerated codes will appear below.",
                     font=F_BODY, text_color=CLR["text_dim"],
                     justify="left").pack(anchor="w", pady=(0, 10))

        tb = ctk.CTkTextbox(frame, height=120, font=F_MONO_SM, corner_radius=8,
                            fg_color=CLR["bg_input"], border_color=CLR["border"],
                            border_width=1, text_color=CLR["text"])
        tb.pack(fill="x", pady=(0, 10))
        tb.insert("1.0", "JBSWY3DPEHPK3PXP\nHXDM72KGGY3TCMJG")

        result_tb = ctk.CTkTextbox(frame, height=120, font=F_MONO_SM, corner_radius=8,
                                   fg_color=CLR["bg_input"], border_color=CLR["border"],
                                   border_width=1, state="disabled",
                                   text_color=CLR["text"])
        result_tb.pack(fill="x")

        def do_bulk():
            lines = tb.get("1.0", "end").strip().splitlines()
            results = []
            for i, secret in enumerate(lines, 1):
                secret = secret.strip()
                if secret:
                    code = generate_totp(secret)
                    results.append(f"  [{i}]  {secret[:16]:<16}  \u2192  {code or 'INVALID'}")
            result_tb.configure(state="normal")
            result_tb.delete("1.0", "end")
            result_tb.insert("1.0", "\n".join(results))
            result_tb.configure(state="disabled")

        ctk.CTkButton(frame, text="Generate All Codes", width=160, height=38,
                      corner_radius=8, font=F_BODY,
                      fg_color=CLR["accent"], hover_color=CLR["accent_hov"],
                      text_color="white", command=do_bulk).pack(anchor="w", pady=(10, 0))

    # ── Tab switching ─────────────────────────────────────────────
    def _switch_tab(self, name):
        self._active_tab = name
        for key, btn in self._tab_btns.items():
            if key == name:
                btn.configure(fg_color=CLR["accent"], text_color="white")
            else:
                btn.configure(fg_color="transparent", text_color=CLR["text_dim"])
        # Clear and repack
        for child in self._tab_content.winfo_children():
            child.pack_forget()
        frames = {
            "Guide": self._guide_frame,
            "About": self._about_frame,
            "FAQ": self._faq_frame,
            "Review": self._review_frame,
        }
        f = frames.get(name)
        if f:
            f.pack(fill="x")

    # ── Extract / Drop from text ─────────────────────────────────
    def _extract(self):
        raw = self.extract_box.get("1.0", "end").strip()
        if not raw or raw.startswith("Paste"):
            self.extract_result.configure(
                text="\u26A0  No text provided.", text_color=CLR["warning"]); return
        codes = extract_2fa_codes(raw, mode="smart")
        if codes:
            entries = [f"{c['code']} ({c['confidence']})" for c in codes]
            latest = extract_latest_code(raw)
            self.extract_result.configure(
                text=f"\u2713  Codes: {', '.join(entries)}   \u25B6 Best: {latest}",
                text_color=CLR["success"])
        else:
            self.extract_result.configure(
                text="\u2717  No 6-digit 2FA codes detected.",
                text_color=CLR["error"])

    def _drop(self):
        raw = self.extract_box.get("1.0", "end").strip()
        if not raw or raw.startswith("Paste"):
            self.extract_result.configure(
                text="\u26A0  No text provided.", text_color=CLR["warning"]); return
        res = drop_2fa_code(raw)
        removed = ", ".join(res["removed_codes"]) if res["removed_codes"] else "None"
        self.extract_result.configure(
            text=f"\u2713  Removed: {removed}\n     Cleaned: {res['cleaned_text'][:80]}",
            text_color=CLR["success"])

    def destroy(self):
        if self._auto_timer:
            self.after_cancel(self._auto_timer)
        super().destroy()


# ──────────────────────────────────────────────────────────────
#  Modal: FB UID Converter
# ──────────────────────────────────────────────────────────────

class FBUidModal(ToolModal):
    def __init__(self, parent):
        super().__init__(parent, "Facebook Link \u2192 UID / Phone Converter",
                         width=700, height=620)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew", padx=24, pady=20)
        scroll.grid_columnconfigure(0, weight=1)
        r = 0

        # ── Single link ───────────────────────────────────────────
        ctk.CTkLabel(scroll, text="\U0001F517  Single Link Converter",
                     font=F_TITLE, text_color=CLR["text"]).grid(
            row=r, column=0, sticky="w", pady=(0, 12)); r += 1

        link_row = ctk.CTkFrame(scroll, fg_color="transparent")
        link_row.grid(row=r, column=0, sticky="ew", pady=(0, 10)); r += 1
        link_row.grid_columnconfigure(0, weight=1)

        self.url_entry = self._make_entry(link_row,
            placeholder="https://www.facebook.com/profile.php?id=\u2026")
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self._make_button(link_row, text="Convert", width=110,
                          command=self._convert_single).pack(side="right")

        self.single_result = ctk.CTkLabel(scroll, text="Result will appear here\u2026",
                                          font=F_MONO, text_color=CLR["text_dim"],
                                          anchor="w", justify="left")
        self.single_result.grid(row=r, column=0, sticky="w", pady=(0, 20)); r += 1

        # ── Batch ─────────────────────────────────────────────────
        ctk.CTkLabel(scroll, text="\U0001F4CB  Batch Convert (multiple links)",
                     font=F_TITLE, text_color=CLR["text"]).grid(
            row=r, column=0, sticky="w", pady=(0, 12)); r += 1

        self.batch_box = self._make_textbox(scroll, height=110)
        self.batch_box.grid(row=r, column=0, sticky="ew", pady=(0, 10)); r += 1
        self.batch_box.insert("1.0", "Paste one Facebook link per line\u2026")

        btn_row = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_row.grid(row=r, column=0, sticky="ew", pady=(0, 10)); r += 1
        self._make_button(btn_row, text="Convert All", width=130,
                          command=self._convert_batch).pack(side="left")
        self._make_button(btn_row, text="\U0001F4BE Export JSON", width=150,
                          style="secondary",
                          command=self._export_json).pack(side="left", padx=(10, 0))

        self.batch_result = self._make_textbox(scroll, height=130, state="disabled")
        self.batch_result.grid(row=r, column=0, sticky="ew", pady=(0, 20)); r += 1
        self._batch_data: list = []

        # ── Phone extraction ──────────────────────────────────────
        ctk.CTkLabel(scroll, text="\U0001F4F1  Extract Phone Numbers",
                     font=F_TITLE, text_color=CLR["text"]).grid(
            row=r, column=0, sticky="w", pady=(0, 12)); r += 1

        self.phone_box = self._make_textbox(scroll, height=70)
        self.phone_box.grid(row=r, column=0, sticky="ew", pady=(0, 10)); r += 1
        self.phone_box.insert("1.0", "Paste text that may contain phone numbers\u2026")

        self._make_button(scroll, text="Extract Phones", width=150,
                          command=self._extract_phones).grid(
            row=r, column=0, sticky="w", pady=(0, 8)); r += 1

        self.phone_result = ctk.CTkLabel(scroll, text="", font=F_MONO,
                                         text_color=CLR["success"], anchor="w")
        self.phone_result.grid(row=r, column=0, sticky="w"); r += 1

    def _convert_single(self):
        url = self.url_entry.get().strip()
        if not url:
            self.single_result.configure(text="\u26A0  Enter a URL",
                                         text_color=CLR["warning"]); return
        res = extract_uid_from_url(url)
        if res["error"]:
            self.single_result.configure(text=f"\u2717  {res['error']}",
                                         text_color=CLR["error"])
        else:
            uid = res["uid"] or "\u2014"
            uname = res["username"] or "\u2014"
            self.single_result.configure(
                text=f"\u2713  UID: {uid}   Username: {uname}   Type: {res['type']}",
                text_color=CLR["success"])

    def _convert_batch(self):
        raw = self.batch_box.get("1.0", "end").strip()
        urls = [l.strip() for l in raw.splitlines()
                if l.strip() and not l.strip().startswith("Paste")]
        if not urls:
            self._write_box(self.batch_result, "\u26A0  No URLs found."); return
        results = []
        lines = [f"  {'#':<4} {'URL':<48} {'UID/User':<22} {'Status'}",
                 "  " + "\u2500" * 86]
        for idx, url in enumerate(urls, 1):
            res = extract_uid_from_url(url)
            disp = res["uid"] or res["username"] or "\u2014" if not res["error"] else "\u2014"
            status = res["type"] if not res["error"] else f"ERR"
            short = url[:45] + "..." if len(url) > 48 else url
            lines.append(f"  {idx:<4} {short:<48} {disp:<22} {status}")
            results.append(res)
        self._batch_data = results
        self._write_box(self.batch_result, "\n".join(lines))

    def _export_json(self):
        if not self._batch_data:
            messagebox.showinfo("Export", "Run Convert All first."); return
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json")], initialfile="fb_uid_results.json")
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self._batch_data, f, indent=2, ensure_ascii=False)
        messagebox.showinfo("Export", f"Saved to:\n{path}")

    def _extract_phones(self):
        raw = self.phone_box.get("1.0", "end").strip()
        if not raw or raw.startswith("Paste"):
            self.phone_result.configure(text="\u26A0  Paste text first",
                                        text_color=CLR["warning"]); return
        phones = extract_phone_from_text(raw)
        if phones:
            self.phone_result.configure(text="\u2713  " + "  |  ".join(phones),
                                        text_color=CLR["success"])
        else:
            self.phone_result.configure(text="\u2717  No phones found",
                                        text_color=CLR["error"])


# ──────────────────────────────────────────────────────────────
#  Modal: Find Facebook ID
# ──────────────────────────────────────────────────────────────

class FindFBIdModal(ToolModal):
    def __init__(self, parent):
        super().__init__(parent, "Find Facebook ID", width=780, height=680)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew", padx=32, pady=24)
        scroll.grid_columnconfigure(0, weight=1)
        r = 0

        # ═══════════════════════════════════════════════════════════
        #  SECTION 1 — Title
        # ═══════════════════════════════════════════════════════════
        title_row = ctk.CTkFrame(scroll, fg_color="transparent")
        title_row.grid(row=r, column=0, sticky="ew", pady=(0, 4)); r += 1

        # Icon badge
        badge = ctk.CTkFrame(title_row, width=42, height=42, corner_radius=10,
                             fg_color="#dbeafe")
        badge.pack(side="left", padx=(0, 12))
        badge.pack_propagate(False)
        ctk.CTkLabel(badge, text="\U0001F50D", font=("Segoe UI Emoji", 20)).pack(
            expand=True)

        title_text = ctk.CTkFrame(title_row, fg_color="transparent")
        title_text.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(title_text, text="Find Facebook ID",
                     font=("Segoe UI", 16, "bold"),
                     text_color=CLR["text"], anchor="w").pack(anchor="w")
        ctk.CTkLabel(title_text,
                     text="Find Facebook IDs from profile, group, post, and page URLs",
                     font=F_BODY, text_color=CLR["text_dim"],
                     anchor="w").pack(anchor="w", pady=(2, 0))

        # ═══════════════════════════════════════════════════════════
        #  SECTION 2 — Input
        # ═══════════════════════════════════════════════════════════
        input_header = ctk.CTkFrame(scroll, fg_color="transparent")
        input_header.grid(row=r, column=0, sticky="ew", pady=(20, 6)); r += 1

        ctk.CTkLabel(input_header, text="Facebook URL or Username",
                     font=F_BODY, text_color=CLR["text_dim"]).pack(side="left")

        self.bulk_btn = ctk.CTkButton(
            input_header, text="\U0001F4C4  Bulk Mode", width=120, height=32,
            corner_radius=8, font=F_SMALL,
            fg_color=CLR["bg_input"], border_color=CLR["border"],
            border_width=1, text_color=CLR["text"],
            hover_color=CLR["border"],
            command=self._toggle_bulk)
        self.bulk_btn.pack(side="right")

        # URL entry
        self.url_entry = ctk.CTkEntry(
            scroll,
            placeholder_text="Enter URL or username (e.g., cristiano or https://facebook.com/cristiano)",
            font=F_MONO, height=44, corner_radius=8,
            border_color=CLR["border"], fg_color=CLR["bg_input"],
            text_color=CLR["text"])
        self.url_entry.grid(row=r, column=0, sticky="ew", pady=(0, 12)); r += 1

        # Bulk textarea (hidden by default)
        self.bulk_box = ctk.CTkTextbox(
            scroll, height=120, font=F_MONO_SM, corner_radius=8,
            fg_color=CLR["bg_input"], border_color=CLR["border"],
            border_width=1, text_color=CLR["text"])
        self.bulk_box.insert("1.0", "Paste one Facebook URL per line\u2026")
        self._bulk_active = False

        # ═══════════════════════════════════════════════════════════
        #  SECTION 3 — Buttons
        # ═══════════════════════════════════════════════════════════
        btn_row = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_row.grid(row=r, column=0, sticky="ew", pady=(0, 16)); r += 1

        self.find_btn = ctk.CTkButton(
            btn_row, text="\U0001F50D  Find Facebook ID",
            font=("Segoe UI", 13, "bold"), height=48, corner_radius=10,
            fg_color=CLR["accent"], hover_color=CLR["accent_hov"],
            text_color="white", command=self._find_id)
        self.find_btn.pack(side="left", fill="x", expand=True, padx=(0, 10))

        ctk.CTkButton(
            btn_row, text="\u21BA  Reset", width=90, height=48,
            corner_radius=10, font=F_BODY,
            fg_color=CLR["bg_input"], border_color=CLR["border"],
            border_width=1, text_color=CLR["text"],
            hover_color=CLR["border"],
            command=self._reset).pack(side="right")

        # ═══════════════════════════════════════════════════════════
        #  SECTION 4 — Result Card (hidden until search)
        # ═══════════════════════════════════════════════════════════
        self.result_card = ctk.CTkFrame(scroll, corner_radius=12,
                                        fg_color=CLR["bg_card"],
                                        border_color=CLR["border"],
                                        border_width=1)
        self.result_card.grid(row=r, column=0, sticky="ew", pady=(0, 8))

        res_inner = ctk.CTkFrame(self.result_card, fg_color="transparent")
        res_inner.pack(fill="x", padx=20, pady=16)

        self.result_title = ctk.CTkLabel(res_inner, text="Result",
                                         font=F_SECTION,
                                         text_color=CLR["text"])
        self.result_title.pack(anchor="w", pady=(0, 8))

        self.result_box = ctk.CTkTextbox(
            res_inner, height=100, font=F_MONO_SM, corner_radius=8,
            fg_color=CLR["bg_input"], border_color=CLR["border"],
            border_width=1, state="disabled", text_color=CLR["text"])
        self.result_box.pack(fill="x")

        # Copy button
        ctk.CTkButton(res_inner, text="\U0001F4CB  Copy Result", width=120, height=32,
                      corner_radius=6, font=F_SMALL,
                      fg_color=CLR["bg_input"], border_color=CLR["border"],
                      border_width=1, text_color=CLR["text"],
                      hover_color=CLR["border"],
                      command=self._copy_result).pack(anchor="w", pady=(8, 0))

        self.result_card.grid_remove()
        r += 1

        # ═══════════════════════════════════════════════════════════
        #  SECTION 5 — Guide Tabs
        # ═══════════════════════════════════════════════════════════
        guide_frame = ctk.CTkFrame(scroll, corner_radius=12,
                                   fg_color=CLR["bg_card"],
                                   border_color=CLR["border"],
                                   border_width=1)
        guide_frame.grid(row=r, column=0, sticky="ew", pady=(16, 8)); r += 1
        g_inner = ctk.CTkFrame(guide_frame, fg_color="transparent")
        g_inner.pack(fill="x", padx=20, pady=16)

        # Tab bar
        tab_frame = ctk.CTkFrame(g_inner, fg_color="transparent")
        tab_frame.pack(fill="x", pady=(0, 12))

        self._tab_btns = {}
        for tab_name in ["Guide", "About", "FAQ", "Review"]:
            btn = ctk.CTkButton(
                tab_frame, text=tab_name, width=80, height=32,
                corner_radius=6, font=F_SMALL,
                fg_color=CLR["accent"] if tab_name == "Guide" else "transparent",
                text_color="white" if tab_name == "Guide" else CLR["text_dim"],
                hover_color=CLR["accent_hov"],
                command=lambda t=tab_name: self._switch_tab(t))
            btn.pack(side="left", padx=(0, 6))
            self._tab_btns[tab_name] = btn

        # Tab content container
        self._tab_content = ctk.CTkFrame(g_inner, fg_color="transparent")
        self._tab_content.pack(fill="x")

        # ── Guide (4 steps) ───────────────────────────────────────
        self._guide_frame = ctk.CTkFrame(self._tab_content, fg_color="transparent")

        steps = [
            ("1", "Copy",
             "Copy Facebook Profile URL,\nFacebook Group URL,\nFacebook Post URL, and\nFacebook Page URL."),
            ("2", "Paste",
             "Paste the copied Facebook\nlink into the URL input field."),
            ("3", "Bulk Search",
             "You can look up multiple\nIDs at once in Bulk mode\nby entering one URL\nper line."),
            ("4", "Search",
             "Click \u201CFind Facebook ID\u201D\nand the ID you need\nwill be displayed."),
        ]

        steps_row = ctk.CTkFrame(self._guide_frame, fg_color="transparent")
        steps_row.pack(fill="x")
        for i, (num, title, desc) in enumerate(steps):
            steps_row.grid_columnconfigure(i, weight=1, uniform="fbstep")
            step_card = ctk.CTkFrame(steps_row, corner_radius=8,
                                     fg_color=CLR["bg_input"],
                                     border_color=CLR["border"],
                                     border_width=1)
            step_card.grid(row=0, column=i, padx=(0, 8 if i < 3 else 0),
                           pady=(0, 4), sticky="nsew")

            si = ctk.CTkFrame(step_card, fg_color="transparent")
            si.pack(fill="x", padx=12, pady=12)

            circle = ctk.CTkLabel(si, text=num, width=28, height=28,
                                  corner_radius=14,
                                  font=("Segoe UI", 11, "bold"),
                                  fg_color=CLR["accent"],
                                  text_color="white")
            circle.pack(anchor="w")
            ctk.CTkLabel(si, text=title, font=("Segoe UI", 10, "bold"),
                         text_color=CLR["text"]).pack(anchor="w", pady=(8, 4))
            ctk.CTkLabel(si, text=desc, font=("Segoe UI", 8),
                         text_color=CLR["text_dim"],
                         justify="left", anchor="w").pack(anchor="w")

        self._guide_frame.pack(fill="x")

        # ── About ─────────────────────────────────────────────────
        self._about_frame = ctk.CTkFrame(self._tab_content, fg_color="transparent")
        ctk.CTkLabel(self._about_frame,
                     text="This tool extracts the numeric Facebook ID from\n"
                          "any Facebook profile, group, post, or page URL.\n\n"
                          "It supports all common URL formats:\n"
                          "  \u2022 facebook.com/profile.php?id=12345\n"
                          "  \u2022 facebook.com/12345\n"
                          "  \u2022 facebook.com/username\n"
                          "  \u2022 facebook.com/people/name/12345\n\n"
                          "For username-based URLs, the username is extracted\n"
                          "directly. Use the Graph API to resolve it to a numeric ID.",
                     font=F_BODY, text_color=CLR["text"],
                     justify="left").pack(anchor="w", pady=(10, 0))

        # ── FAQ ───────────────────────────────────────────────────
        self._faq_frame = ctk.CTkFrame(self._tab_content, fg_color="transparent")
        ctk.CTkLabel(self._faq_frame,
                     text="Q: What is a Facebook UID?\n"
                          "A: A unique numeric identifier assigned by Facebook\n"
                          "    to every profile, page, group, or post.\n\n"
                          "Q: Why do I get a username instead of a number?\n"
                          "A: Some URLs use vanity usernames. Use the Graph API\n"
                          "    to resolve a username to a numeric UID.\n\n"
                          "Q: Can I paste multiple URLs?\n"
                          "A: Yes! Click \u201CBulk Mode\u201D to enter one URL per line.",
                     font=F_BODY, text_color=CLR["text"],
                     justify="left").pack(anchor="w", pady=(10, 0))

        # ── Review ────────────────────────────────────────────────
        self._review_frame = ctk.CTkFrame(self._tab_content, fg_color="transparent")
        ctk.CTkLabel(self._review_frame,
                     text="\u2B50\u2B50\u2B50\u2B50\u2B50  No reviews yet.\n\n"
                          "Be the first to review this tool!",
                     font=F_BODY, text_color=CLR["text_dim"],
                     justify="left").pack(anchor="w", pady=(10, 0))

        scroll.grid_rowconfigure(r, weight=1)

    # ── Actions ───────────────────────────────────────────────────
    def _find_id(self):
        if self._bulk_active:
            self._find_bulk()
            return

        raw = self.url_entry.get().strip()
        if not raw:
            messagebox.showwarning("Error", "Please enter a Facebook URL or username.")
            return

        # If it looks like a bare username, wrap it
        if "/" not in raw and "." not in raw.split("/")[-1] if "/" in raw else "https://" not in raw:
            if not raw.startswith("http"):
                raw = f"https://www.facebook.com/{raw}"

        res = extract_uid_from_url(raw)
        phones = extract_phone_from_text(raw)

        self.result_card.grid()
        self.result_box.configure(state="normal")
        self.result_box.delete("1.0", "end")

        if res["error"]:
            self.result_title.configure(text="Result",
                                        text_color=CLR["error"])
            self.result_box.insert("1.0", f"\u2717  Error: {res['error']}")
        else:
            self.result_title.configure(text="\u2713  Facebook ID Found",
                                        text_color=CLR["success"])
            lines = []
            if res["uid"]:
                lines.append(f"  UID:       {res['uid']}")
            if res["username"]:
                lines.append(f"  Username:  {res['username']}")
            lines.append(f"  Type:      {res['type']}")
            lines.append(f"  URL:       {res['url']}")
            if phones:
                lines.append(f"  Phones:    {', '.join(phones)}")
            self.result_box.insert("1.0", "\n".join(lines))
        self.result_box.configure(state="disabled")

    def _find_bulk(self):
        raw = self.bulk_box.get("1.0", "end").strip()
        urls = [l.strip() for l in raw.splitlines()
                if l.strip() and not l.strip().startswith("Paste")]
        if not urls:
            messagebox.showwarning("Error", "No URLs found. Paste one URL per line.")
            return

        self.result_card.grid()
        self.result_box.configure(state="normal")
        self.result_box.delete("1.0", "end")

        lines = [f"  {'#':<4} {'Input':<48} {'UID / Username':<22} {'Type'}",
                 "  " + "\u2500" * 88]
        for idx, url in enumerate(urls, 1):
            # Auto-wrap bare usernames
            if not url.startswith("http") and "/" not in url:
                url = f"https://www.facebook.com/{url}"
            res = extract_uid_from_url(url)
            if res["error"]:
                disp, status = "\u2014", "ERROR"
            else:
                disp = res["uid"] or res["username"] or "\u2014"
                status = res["type"]
            short = url[:45] + "..." if len(url) > 48 else url
            lines.append(f"  {idx:<4} {short:<48} {disp:<22} {status}")

        self.result_title.configure(text=f"\u2713  Bulk Results ({len(urls)} URLs)",
                                    text_color=CLR["success"])
        self.result_box.insert("1.0", "\n".join(lines))
        self.result_box.configure(state="disabled")

    def _reset(self):
        self.url_entry.delete(0, "end")
        self.result_card.grid_remove()
        if self._bulk_active:
            self._toggle_bulk()  # switch back to single mode

    def _toggle_bulk(self):
        if not self._bulk_active:
            self._bulk_active = True
            self.url_entry.grid_remove()
            self.bulk_box.grid(row=3, column=0, sticky="ew", pady=(0, 12))
            self.bulk_btn.configure(text="\U0001F4DD  Single Mode",
                                    fg_color=CLR["accent"],
                                    text_color="white")
            self.find_btn.configure(text="\U0001F50D  Find All IDs")
        else:
            self._bulk_active = False
            self.bulk_box.grid_remove()
            self.url_entry.grid(row=3, column=0, sticky="ew", pady=(0, 12))
            self.bulk_btn.configure(text="\U0001F4C4  Bulk Mode",
                                    fg_color=CLR["bg_input"],
                                    text_color=CLR["text"])
            self.find_btn.configure(text="\U0001F50D  Find Facebook ID")

    def _copy_result(self):
        text = self.result_box.get("1.0", "end").strip()
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            messagebox.showinfo("Copied", "Result copied to clipboard!")

    def _switch_tab(self, name):
        for key, btn in self._tab_btns.items():
            if key == name:
                btn.configure(fg_color=CLR["accent"], text_color="white")
            else:
                btn.configure(fg_color="transparent", text_color=CLR["text_dim"])
        for child in self._tab_content.winfo_children():
            child.pack_forget()
        frames = {
            "Guide": self._guide_frame,
            "About": self._about_frame,
            "FAQ": self._faq_frame,
            "Review": self._review_frame,
        }
        f = frames.get(name)
        if f:
            f.pack(fill="x")


# ──────────────────────────────────────────────────────────────
#  Modal: Coming Soon
# ──────────────────────────────────────────────────────────────

class ComingSoonModal(ToolModal):
    def __init__(self, parent, tool_id: str):
        super().__init__(parent, f"Tool: {tool_id}", width=420, height=220)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=0, column=0)

        ctk.CTkLabel(frame, text="\U0001F6A7", font=("Segoe UI Emoji", 40)).pack(
            pady=(10, 6))
        ctk.CTkLabel(frame, text="Coming Soon", font=("Segoe UI", 18, "bold"),
                     text_color=CLR["text"]).pack()
        ctk.CTkLabel(frame,
                     text=f"The \"{tool_id}\" tool is under development.",
                     font=F_BODY, text_color=CLR["text_dim"]).pack(pady=(6, 0))
        ctk.CTkButton(frame, text="Close", width=100, height=34, corner_radius=8,
                      font=F_BODY, fg_color=CLR["accent"],
                      command=self.destroy).pack(pady=(18, 10))


# ══════════════════════════════════════════════════════════════
#  Entry Point
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = DashboardApp()
    try:
        app.mainloop()
    except KeyboardInterrupt:
        app.destroy()

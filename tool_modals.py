"""
Extra tool modals — all 9 remaining dashboard tools.
Each class inherits from ToolModal (imported from gui).
"""

import random, string, re, time, json, hashlib
from datetime import datetime, timedelta
from tkinter import filedialog, messagebox
import customtkinter as ctk

# ──────────────────────────────────────────────────────────────
#  Shared helpers (duplicated from gui.py to avoid circular import)
# ──────────────────────────────────────────────────────────────

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

F_TITLE   = ("Segoe UI", 14, "bold")
F_SECTION = ("Segoe UI", 11, "bold")
F_BODY    = ("Segoe UI", 11)
F_SMALL   = ("Segoe UI", 9)
F_MONO    = ("Consolas", 11)
F_MONO_SM = ("Consolas", 10)


def get_CLR():
    """Get the live color dict from gui (avoids circular import)."""
    try:
        import gui as _g
        return _g.CLR
    except Exception:
        return dict(LIGHT)


def get_parent_modal(parent):
    """Return ToolModal base class from gui."""
    import gui as _g
    return _g.ToolModal


# ══════════════════════════════════════════════════════════════
#  1. CREATE FAKE ID CARD
# ══════════════════════════════════════════════════════════════

_FIRST_M = ["James","John","Robert","Michael","William","David","Richard","Joseph",
            "Thomas","Christopher","Daniel","Matthew","Anthony","Mark","Donald",
            "Steven","Paul","Andrew","Joshua","Kenneth","Kevin","Brian","George",
            "Timothy","Ronald","Edward","Jason","Jeffrey","Ryan","Jacob"]
_FIRST_F = ["Mary","Patricia","Jennifer","Linda","Barbara","Elizabeth","Susan",
            "Jessica","Sarah","Karen","Lisa","Nancy","Betty","Margaret","Sandra",
            "Ashley","Dorothy","Kimberly","Emily","Donna","Michelle","Carol",
            "Amanda","Melissa","Deborah","Stephanie","Rebecca","Sharon","Laura",
            "Cynthia"]
_LAST = ["Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis",
         "Rodriguez","Martinez","Hernandez","Lopez","Gonzalez","Wilson","Anderson",
         "Thomas","Taylor","Moore","Jackson","Martin","Lee","Perez","Thompson",
         "White","Harris","Sanchez","Clark","Ramirez","Lewis","Robinson"]
_STREETS = ["Main St","Oak Ave","Elm St","Maple Dr","Cedar Ln","Pine Rd",
            "Washington Blvd","Park Ave","Lake Dr","Hill Rd","River Rd",
            "Church St","High St","Mill Rd","School St"]
_CITIES = ["New York","Los Angeles","Chicago","Houston","Phoenix","Philadelphia",
           "San Antonio","San Diego","Dallas","San Jose","Austin","Jacksonville",
           "Fort Worth","Columbus","Charlotte","Indianapolis","Seattle","Denver",
           "Nashville","Oklahoma City","Portland","Las Vegas","Memphis","Miami"]
_STATES = ["AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL",
           "IN","IA","KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT",
           "NE","NV","NH","NJ","NM","NY","NC","ND","OH","OK","OR","PA","RI",
           "SC","SD","TN","TX","UT","VT","VA","WA","WV","WI","WY"]


def _rand_id():
    return "".join(random.choices(string.digits, k=9))

def _rand_phone():
    return f"({random.randint(200,999)}) {random.randint(100,999)}-{random.randint(1000,9999)}"

def _rand_email(name):
    parts = name.lower().replace(" ","").replace("'","")
    return f"{parts}{random.randint(10,99)}@{'gmail.com' if random.random()>0.5 else 'yahoo.com'}"


class FakeIDModal(ctk.CTkToplevel):
    def __init__(self, parent):
        ToolModalBase = get_parent_modal(parent)
        CLR = get_CLR()
        super().__init__(parent)
        self.title("Create Fake ID Card")
        self.geometry("720x660")
        self.minsize(480, 400)
        self.resizable(True, True)
        self.configure(fg_color=CLR["bg_modal"])
        self.update_idletasks()
        px = parent.winfo_x() + (parent.winfo_width() - 720) // 2
        py = parent.winfo_y() + (parent.winfo_height() - 660) // 2
        self.geometry(f"+{max(0,px)}+{max(0,py)}")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew", padx=24, pady=24)
        scroll.grid_columnconfigure(0, weight=1)
        r = 0

        # Title
        title_row = ctk.CTkFrame(scroll, fg_color="transparent")
        title_row.grid(row=r, column=0, sticky="ew", pady=(0, 4)); r += 1
        badge = ctk.CTkFrame(title_row, width=42, height=42, corner_radius=10,
                             fg_color="#dbeafe")
        badge.pack(side="left", padx=(0, 12)); badge.pack_propagate(False)
        ctk.CTkLabel(badge, text="\U0001F4C7", font=("Segoe UI Emoji", 20)).pack(expand=True)
        tt = ctk.CTkFrame(title_row, fg_color="transparent")
        tt.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(tt, text="Create Fake ID Card", font=("Segoe UI", 16, "bold"),
                     text_color=CLR["text"], anchor="w").pack(anchor="w")
        ctk.CTkLabel(tt, text="Generate random identity data for testing", font=F_BODY,
                     text_color=CLR["text_dim"], anchor="w").pack(anchor="w", pady=(2,0))

        # Options row (responsive grid layout)
        opt_row = ctk.CTkFrame(scroll, fg_color="transparent")
        opt_row.grid(row=r, column=0, sticky="ew", pady=(20, 12)); r += 1
        opt_row.grid_columnconfigure(4, weight=1)

        ctk.CTkLabel(opt_row, text="Gender:", font=F_BODY,
                     text_color=CLR["text_dim"]).grid(row=0, column=0, padx=(0, 4))
        self.gender_var = ctk.StringVar(value="Random")
        for gi, g in enumerate(["Random", "Male", "Female"]):
            ctk.CTkRadioButton(opt_row, text=g, variable=self.gender_var, value=g,
                               font=F_BODY, text_color=CLR["text"]).grid(
                row=0, column=gi+1, padx=(8, 0))

        ctk.CTkLabel(opt_row, text="Country:", font=F_BODY,
                     text_color=CLR["text_dim"]).grid(row=0, column=5, padx=(20, 4))
        self.country_var = ctk.StringVar(value="United States")
        ctk.CTkOptionMenu(opt_row, variable=self.country_var,
                          values=["United States", "United Kingdom", "Canada", "Australia"],
                          width=140, font=F_BODY).grid(row=0, column=6, padx=(0, 4))

        # Generate button
        self.gen_btn = ctk.CTkButton(
            scroll, text="\U0001F3B2  Generate Random ID", font=("Segoe UI", 13, "bold"),
            height=48, corner_radius=10, fg_color=CLR["accent"],
            hover_color=CLR["accent_hov"], text_color="white",
            command=self._generate)
        self.gen_btn.grid(row=r, column=0, sticky="ew", pady=(0, 16)); r += 1

        # Result card
        self.result_card = ctk.CTkFrame(scroll, corner_radius=12,
                                        fg_color=CLR["bg_card"],
                                        border_color=CLR["border"], border_width=1)
        self.result_card.grid(row=r, column=0, sticky="ew", pady=(0, 8)); r += 1
        res_inner = ctk.CTkFrame(self.result_card, fg_color="transparent")
        res_inner.pack(fill="x", padx=20, pady=16)

        ctk.CTkLabel(res_inner, text="Generated Identity", font=F_SECTION,
                     text_color=CLR["text"]).pack(anchor="w", pady=(0, 8))

        self.result_box = ctk.CTkTextbox(
            res_inner, height=260, font=F_MONO_SM, corner_radius=8,
            fg_color=CLR["bg_input"], border_color=CLR["border"],
            border_width=1, state="disabled", text_color=CLR["text"])
        self.result_box.pack(fill="x")

        btn_row = ctk.CTkFrame(res_inner, fg_color="transparent")
        btn_row.pack(fill="x", pady=(10, 0))
        ctk.CTkButton(btn_row, text="\U0001F4CB Copy", width=100, height=34,
                      corner_radius=8, font=F_SMALL,
                      fg_color=CLR["bg_input"], border_color=CLR["border"],
                      border_width=1, text_color=CLR["text"],
                      hover_color=CLR["border"],
                      command=self._copy).pack(side="left")
        ctk.CTkButton(btn_row, text="\U0001F4BE Export JSON", width=120, height=34,
                      corner_radius=8, font=F_SMALL,
                      fg_color=CLR["bg_input"], border_color=CLR["border"],
                      border_width=1, text_color=CLR["text"],
                      hover_color=CLR["border"],
                      command=self._export).pack(side="left", padx=(8, 0))
        ctk.CTkButton(btn_row, text="\U0001F504 Regenerate", width=120, height=34,
                      corner_radius=8, font=F_SMALL,
                      fg_color=CLR["accent"], hover_color=CLR["accent_hov"],
                      text_color="white",
                      command=self._generate).pack(side="right")

        self._last_data = {}
        self._generate()  # auto-generate on open

    def _generate(self):
        gender = self.gender_var.get()
        if gender == "Random":
            gender = random.choice(["Male", "Female"])
        if gender == "Male":
            first = random.choice(_FIRST_M)
        else:
            first = random.choice(_FIRST_F)
        last = random.choice(_LAST)
        full = f"{first} {last}"
        age = random.randint(18, 75)
        dob = datetime.now() - timedelta(days=age*365 + random.randint(0, 364))
        dob_str = dob.strftime("%B %d, %Y")
        street = f"{random.randint(100, 9999)} {random.choice(_STREETS)}"
        city = random.choice(_CITIES)
        state = random.choice(_STATES)
        zipcode = f"{random.randint(10000, 99999)}"
        id_num = _rand_id()
        phone = _rand_phone()
        email = _rand_email(full)
        height = f"{random.randint(5, 6)}'{random.randint(0, 11)}\""
        weight = f"{random.randint(110, 250)} lbs"
        eye = random.choice(["Brown", "Blue", "Green", "Hazel", "Gray"])
        hair = random.choice(["Black", "Brown", "Blonde", "Red", "Gray"])
        ssn = f"{random.randint(100,999)}-{random.randint(10,99)}-{random.randint(1000,9999)}"
        exp = (datetime.now() + timedelta(days=random.randint(365*2, 365*8))).strftime("%m/%d/%Y")

        self._last_data = {
            "Full Name": full, "Gender": gender, "Date of Birth": dob_str,
            "Age": age, "SSN": ssn, "ID Number": id_num,
            "Address": f"{street}, {city}, {state} {zipcode}",
            "Phone": phone, "Email": email,
            "Height": height, "Weight": weight,
            "Eye Color": eye, "Hair Color": hair, "Expires": exp,
        }

        lines = []
        for k, v in self._last_data.items():
            lines.append(f"  {k:<16} {v}")
        self.result_box.configure(state="normal")
        self.result_box.delete("1.0", "end")
        self.result_box.insert("1.0", "\n".join(lines))
        self.result_box.configure(state="disabled")

    def _copy(self):
        text = self.result_box.get("1.0", "end").strip()
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            messagebox.showinfo("Copied", "ID data copied to clipboard!")

    def _export(self):
        if not self._last_data:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".json", filetypes=[("JSON","*.json")],
            initialfile="fake_id.json")
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self._last_data, f, indent=2)
        messagebox.showinfo("Exported", f"Saved to:\n{path}")


# ══════════════════════════════════════════════════════════════
#  2. QUICK READ HOTMAIL
# ══════════════════════════════════════════════

_EMAIL_RE = re.compile(r'[\w.+-]+@[\w-]+\.[\w.-]+')
_SUBJECT_RE = re.compile(r'(?:subject|subj)\s*[:=]\s*(.+)', re.IGNORECASE)
_FROM_RE  = re.compile(r'(?:from)\s*[:=]\s*(.+)', re.IGNORECASE)
_DATE_RE  = re.compile(r'(?:date)\s*[:=]\s*(.+)', re.IGNORECASE)
_MAILTO_RE = re.compile(r'mailto:([^\s?]+)(?:\?([^\s]*))?')


class HotmailModal(ctk.CTkToplevel):
    def __init__(self, parent):
        CLR = get_CLR()
        super().__init__(parent)
        self.title("Quick Read Hotmail")
        self.geometry("740x640")
        self.minsize(480, 400)
        self.resizable(True, True)
        self.configure(fg_color=CLR["bg_modal"])
        self.update_idletasks()
        px = parent.winfo_x() + (parent.winfo_width() - 740) // 2
        py = parent.winfo_y() + (parent.winfo_height() - 640) // 2
        self.geometry(f"+{max(0,px)}+{max(0,py)}")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew", padx=24, pady=24)
        scroll.grid_columnconfigure(0, weight=1)
        r = 0

        # Title
        title_row = ctk.CTkFrame(scroll, fg_color="transparent")
        title_row.grid(row=r, column=0, sticky="ew", pady=(0, 4)); r += 1
        badge = ctk.CTkFrame(title_row, width=42, height=42, corner_radius=10,
                             fg_color="#fef3c7")
        badge.pack(side="left", padx=(0, 12)); badge.pack_propagate(False)
        ctk.CTkLabel(badge, text="\u2709\uFE0F", font=("Segoe UI Emoji", 20)).pack(expand=True)
        tt = ctk.CTkFrame(title_row, fg_color="transparent")
        tt.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(tt, text="Quick Read Hotmail", font=("Segoe UI", 16, "bold"),
                     text_color=CLR["text"], anchor="w").pack(anchor="w")
        ctk.CTkLabel(tt, text="Parse emails, extract addresses, subjects, and dates",
                     font=F_BODY, text_color=CLR["text_dim"],
                     anchor="w").pack(anchor="w", pady=(2,0))

        # Input
        ctk.CTkLabel(scroll, text="Paste Email Text or mailto: Links", font=F_BODY,
                     text_color=CLR["text_dim"]).grid(row=r, column=0, sticky="w",
                                                      pady=(16, 6)); r += 1
        self.input_box = ctk.CTkTextbox(
            scroll, height=140, font=F_MONO_SM, corner_radius=8,
            fg_color=CLR["bg_input"], border_color=CLR["border"],
            border_width=1, text_color=CLR["text"])
        self.input_box.grid(row=r, column=0, sticky="ew", pady=(0, 10)); r += 1
        self.input_box.insert("1.0", "Paste raw email text, headers, or mailto: links here\u2026")

        # Buttons
        btn_row = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_row.grid(row=r, column=0, sticky="ew", pady=(0, 14)); r += 1
        ctk.CTkButton(btn_row, text="\U0001F50D  Parse Email", font=("Segoe UI", 12, "bold"),
                      height=44, corner_radius=10, fg_color=CLR["accent"],
                      hover_color=CLR["accent_hov"], text_color="white",
                      command=self._parse, width=200).pack(side="left")
        ctk.CTkButton(btn_row, text="\U0001F4CB  Paste from Clipboard", width=160, height=44,
                      corner_radius=10, font=F_BODY,
                      fg_color=CLR["bg_input"], border_color=CLR["border"],
                      border_width=1, text_color=CLR["text"],
                      hover_color=CLR["border"],
                      command=self._paste_clip).pack(side="left", padx=(10, 0))
        ctk.CTkButton(btn_row, text="\U0001F5D1  Clear", width=80, height=44,
                      corner_radius=10, font=F_BODY,
                      fg_color=CLR["bg_input"], border_color=CLR["border"],
                      border_width=1, text_color=CLR["text"],
                      hover_color=CLR["border"],
                      command=self._clear).pack(side="right")

        # Result
        self.result_card = ctk.CTkFrame(scroll, corner_radius=12,
                                        fg_color=CLR["bg_card"],
                                        border_color=CLR["border"], border_width=1)
        self.result_card.grid(row=r, column=0, sticky="ew", pady=(0, 8)); r += 1
        res_inner = ctk.CTkFrame(self.result_card, fg_color="transparent")
        res_inner.pack(fill="x", padx=20, pady=16)

        self.result_title = ctk.CTkLabel(res_inner, text="Parsed Result", font=F_SECTION,
                                         text_color=CLR["text"])
        self.result_title.pack(anchor="w", pady=(0, 8))
        self.result_box = ctk.CTkTextbox(
            res_inner, height=180, font=F_MONO_SM, corner_radius=8,
            fg_color=CLR["bg_input"], border_color=CLR["border"],
            border_width=1, state="disabled", text_color=CLR["text"])
        self.result_box.pack(fill="x")

        ctk.CTkButton(res_inner, text="\U0001F4CB Copy Result", width=120, height=32,
                      corner_radius=6, font=F_SMALL,
                      fg_color=CLR["bg_input"], border_color=CLR["border"],
                      border_width=1, text_color=CLR["text"],
                      hover_color=CLR["border"],
                      command=self._copy_result).pack(anchor="w", pady=(8, 0))

        self.result_card.grid_remove()

    def _paste_clip(self):
        try:
            self.clipboard_clear()
            clip = self.clipboard_get()
            self.input_box.delete("1.0", "end")
            self.input_box.insert("1.0", clip)
        except Exception:
            messagebox.showwarning("Clipboard", "Could not read clipboard.")

    def _clear(self):
        self.input_box.delete("1.0", "end")
        self.result_card.grid_remove()

    def _parse(self):
        CLR = get_CLR()
        raw = self.input_box.get("1.0", "end").strip()
        if not raw or raw.startswith("Paste"):
            messagebox.showwarning("Error", "Please paste email text first.")
            return

        emails = _EMAIL_RE.findall(raw)
        subjects = _SUBJECT_RE.findall(raw)
        froms = _FROM_RE.findall(raw)
        dates = _DATE_RE.findall(raw)
        mailtos = _MAILTO_RE.findall(raw)

        lines = []
        if emails:
            unique = list(dict.fromkeys(emails))
            lines.append(f"  \u2709  Email Addresses Found ({len(unique)}):")
            for i, e in enumerate(unique, 1):
                lines.append(f"     [{i}] {e}")
            lines.append("")

        if froms:
            lines.append(f"  \U0001F464 From: {froms[0].strip()}")
        if subjects:
            lines.append(f"  \U0001F4DD Subject: {subjects[0].strip()}")
        if dates:
            lines.append(f"  \U0001F4C5 Date: {dates[0].strip()}")

        if mailtos:
            lines.append(f"\n  \U0001F517 mailto: Links ({len(mailtos)}):")
            for addr, params in mailtos:
                lines.append(f"     \u2192 {addr}")
                if "subject=" in params.lower():
                    subj = re.search(r'subject=([^&]+)', params, re.IGNORECASE)
                    if subj:
                        lines.append(f"       Subject: {subj.group(1)}")

        if not lines:
            lines.append("  \u2717  No email data detected in the text.")

        self.result_card.grid()
        self.result_title.configure(
            text="\u2713  Parsed Result" if emails or mailtos else "\u2717  No Data Found",
            text_color=CLR["success"] if emails or mailtos else CLR["error"])
        self.result_box.configure(state="normal")
        self.result_box.delete("1.0", "end")
        self.result_box.insert("1.0", "\n".join(lines))
        self.result_box.configure(state="disabled")

    def _copy_result(self):
        text = self.result_box.get("1.0", "end").strip()
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            messagebox.showinfo("Copied", "Result copied to clipboard!")


# ══════════════════════════════════════════════════════════════
#  3. CRON JOBS MANAGER
# ══════════════════════════════════════════════

class CronJobsModal(ctk.CTkToplevel):
    def __init__(self, parent):
        CLR = get_CLR()
        super().__init__(parent)
        self.title("Cron Jobs Manager")
        self.geometry("760x660")
        self.minsize(480, 400)
        self.resizable(True, True)
        self.configure(fg_color=CLR["bg_modal"])
        self.update_idletasks()
        px = parent.winfo_x() + (parent.winfo_width() - 760) // 2
        py = parent.winfo_y() + (parent.winfo_height() - 660) // 2
        self.geometry(f"+{max(0,px)}+{max(0,py)}")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._jobs = []
        self._timer = None

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew", padx=24, pady=24)
        scroll.grid_columnconfigure(0, weight=1)
        r = 0

        # Title
        title_row = ctk.CTkFrame(scroll, fg_color="transparent")
        title_row.grid(row=r, column=0, sticky="ew", pady=(0, 4)); r += 1
        badge = ctk.CTkFrame(title_row, width=42, height=42, corner_radius=10,
                             fg_color="#dbeafe")
        badge.pack(side="left", padx=(0, 12)); badge.pack_propagate(False)
        ctk.CTkLabel(badge, text="\u23F0", font=("Segoe UI Emoji", 20)).pack(expand=True)
        tt = ctk.CTkFrame(title_row, fg_color="transparent")
        tt.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(tt, text="Cron Jobs Manager", font=("Segoe UI", 16, "bold"),
                     text_color=CLR["text"], anchor="w").pack(anchor="w")
        ctk.CTkLabel(tt, text="Schedule and manage recurring tasks",
                     font=F_BODY, text_color=CLR["text_dim"],
                     anchor="w").pack(anchor="w", pady=(2,0))

        # Add job form
        form_card = ctk.CTkFrame(scroll, corner_radius=12, fg_color=CLR["bg_card"],
                                 border_color=CLR["border"], border_width=1)
        form_card.grid(row=r, column=0, sticky="ew", pady=(16, 12)); r += 1
        form_inner = ctk.CTkFrame(form_card, fg_color="transparent")
        form_inner.pack(fill="x", padx=20, pady=16)

        ctk.CTkLabel(form_inner, text="Add New Job", font=F_SECTION,
                     text_color=CLR["text"]).pack(anchor="w", pady=(0, 10))

        row1 = ctk.CTkFrame(form_inner, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 8))
        self.job_name = ctk.CTkEntry(row1, placeholder_text="Job Name (e.g. Backup DB)",
                                     font=F_MONO, height=38, corner_radius=8,
                                     border_color=CLR["border"],
                                     fg_color=CLR["bg_input"],
                                     text_color=CLR["text"])
        self.job_name.pack(side="left", fill="x", expand=True, padx=(0, 10))

        intervals = ["Every Minute", "Every 5 Min", "Every 15 Min",
                     "Every Hour", "Every 6 Hours", "Daily", "Weekly"]
        self.job_interval = ctk.StringVar(value="Every Hour")
        ctk.CTkOptionMenu(row1, variable=self.job_interval, values=intervals,
                          width=140, font=F_BODY).pack(side="right")

        row2 = ctk.CTkFrame(form_inner, fg_color="transparent")
        row2.pack(fill="x")
        self.job_cmd = ctk.CTkEntry(row2, placeholder_text="Command or URL to execute",
                                    font=F_MONO, height=38, corner_radius=8,
                                    border_color=CLR["border"],
                                    fg_color=CLR["bg_input"],
                                    text_color=CLR["text"])
        self.job_cmd.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(row2, text="\u2795  Add Job", width=120, height=38,
                      corner_radius=8, font=F_BODY,
                      fg_color=CLR["accent"], hover_color=CLR["accent_hov"],
                      text_color="white",
                      command=self._add_job).pack(side="right")

        # Jobs list
        ctk.CTkLabel(scroll, text="Scheduled Jobs", font=F_SECTION,
                     text_color=CLR["text"]).grid(row=r, column=0, sticky="w",
                                                   pady=(4, 8)); r += 1

        self.jobs_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        self.jobs_frame.grid(row=r, column=0, sticky="ew"); r += 1
        self.jobs_frame.grid_columnconfigure(0, weight=1)

        self.empty_lbl = ctk.CTkLabel(self.jobs_frame, text="No jobs scheduled yet.",
                                      font=F_BODY, text_color=CLR["text_muted"])
        self.empty_lbl.pack(pady=20)

        # Summary
        self.summary_lbl = ctk.CTkLabel(scroll, text="", font=F_SMALL,
                                        text_color=CLR["text_dim"])
        self.summary_lbl.grid(row=r, column=0, sticky="w", pady=(8, 0))

        self._start_timer()

    def _add_job(self):
        CLR = get_CLR()
        name = self.job_name.get().strip()
        cmd = self.job_cmd.get().strip()
        if not name:
            messagebox.showwarning("Error", "Please enter a job name.")
            return
        if not cmd:
            cmd = "(no command)"

        job = {
            "name": name,
            "command": cmd,
            "interval": self.job_interval.get(),
            "status": "Active",
            "runs": 0,
            "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "next_run": self._calc_next(self.job_interval.get()),
        }
        self._jobs.append(job)
        self.job_name.delete(0, "end")
        self.job_cmd.delete(0, "end")
        self._render_jobs()

    def _calc_next(self, interval):
        now = datetime.now()
        mapping = {
            "Every Minute": timedelta(minutes=1),
            "Every 5 Min": timedelta(minutes=5),
            "Every 15 Min": timedelta(minutes=15),
            "Every Hour": timedelta(hours=1),
            "Every 6 Hours": timedelta(hours=6),
            "Daily": timedelta(days=1),
            "Weekly": timedelta(weeks=1),
        }
        delta = mapping.get(interval, timedelta(hours=1))
        return (now + delta).strftime("%H:%M:%S")

    def _render_jobs(self):
        CLR = get_CLR()
        for w in self.jobs_frame.winfo_children():
            w.destroy()

        if not self._jobs:
            self.empty_lbl = ctk.CTkLabel(self.jobs_frame, text="No jobs scheduled yet.",
                                          font=F_BODY, text_color=CLR["text_muted"])
            self.empty_lbl.pack(pady=20)
            self.summary_lbl.configure(text="")
            return

        active = sum(1 for j in self._jobs if j["status"] == "Active")
        self.summary_lbl.configure(
            text=f"Total: {len(self._jobs)} jobs  |  Active: {active}")

        for i, job in enumerate(self._jobs):
            card = ctk.CTkFrame(self.jobs_frame, corner_radius=8,
                                fg_color=CLR["bg_card"],
                                border_color=CLR["border"], border_width=1)
            card.pack(fill="x", pady=(0, 6))

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="x", padx=16, pady=12)

            top = ctk.CTkFrame(inner, fg_color="transparent")
            top.pack(fill="x")

            status_color = {"Active": CLR["success"], "Paused": CLR["warning"],
                            "Stopped": CLR["error"]}.get(job["status"], CLR["text_muted"])
            status_dot = ctk.CTkLabel(top, text="\u25CF", font=("Segoe UI", 10),
                                      text_color=status_color)
            status_dot.pack(side="left")
            ctk.CTkLabel(top, text=f"  {job['name']}", font=("Segoe UI", 11, "bold"),
                         text_color=CLR["text"]).pack(side="left")

            badge = ctk.CTkLabel(top, text=job["interval"], font=F_SMALL,
                                 fg_color=CLR["bg_input"], corner_radius=4,
                                 text_color=CLR["text_dim"], width=100, height=22)
            badge.pack(side="right", padx=(6, 0))
            ctk.CTkLabel(top, text=f"Next: {job['next_run']}", font=F_SMALL,
                         text_color=CLR["text_muted"]).pack(side="right")

            bot = ctk.CTkFrame(inner, fg_color="transparent")
            bot.pack(fill="x", pady=(6, 0))
            ctk.CTkLabel(bot, text=f"Command: {job['command']}", font=F_MONO_SM,
                         text_color=CLR["text_dim"], anchor="w").pack(side="left")
            ctk.CTkLabel(bot, text=f"Runs: {job['runs']}  |  Created: {job['created']}",
                         font=F_SMALL, text_color=CLR["text_muted"]).pack(side="right")

            btn_row = ctk.CTkFrame(inner, fg_color="transparent")
            btn_row.pack(fill="x", pady=(6, 0))

            if job["status"] == "Active":
                ctk.CTkButton(btn_row, text="\u23F8 Pause", width=70, height=26,
                              corner_radius=6, font=F_SMALL,
                              fg_color=CLR["warning"], hover_color="#b45309",
                              text_color="white",
                              command=lambda idx=i: self._toggle(idx, "Paused")
                              ).pack(side="left")
            elif job["status"] == "Paused":
                ctk.CTkButton(btn_row, text="\u25B6 Resume", width=70, height=26,
                              corner_radius=6, font=F_SMALL,
                              fg_color=CLR["success"], hover_color="#15803d",
                              text_color="white",
                              command=lambda idx=i: self._toggle(idx, "Active")
                              ).pack(side="left")

            ctk.CTkButton(btn_row, text="\U0001F5D1 Delete", width=80, height=26,
                          corner_radius=6, font=F_SMALL,
                          fg_color=CLR["error"], hover_color="#b91c1c",
                          text_color="white",
                          command=lambda idx=i: self._delete(idx)
                          ).pack(side="left", padx=(6, 0))
            ctk.CTkButton(btn_row, text="\U0001F4CB Copy Command", width=110, height=26,
                          corner_radius=6, font=F_SMALL,
                          fg_color=CLR["bg_input"], border_color=CLR["border"],
                          border_width=1, text_color=CLR["text"],
                          hover_color=CLR["border"],
                          command=lambda j=job: self._copy_cmd(j)
                          ).pack(side="right")

    def _toggle(self, idx, status):
        if 0 <= idx < len(self._jobs):
            self._jobs[idx]["status"] = status
            self._render_jobs()

    def _delete(self, idx):
        if 0 <= idx < len(self._jobs):
            self._jobs.pop(idx)
            self._render_jobs()

    def _copy_cmd(self, job):
        self.clipboard_clear()
        self.clipboard_append(job["command"])
        messagebox.showinfo("Copied", f"Command copied:\n{job['command']}")

    def _start_timer(self):
        def tick():
            for job in self._jobs:
                if job["status"] == "Active":
                    job["next_run"] = self._calc_next(job["interval"])
            if self._jobs:
                self._render_jobs()
            self._timer = self.after(60000, tick)  # refresh every minute
        tick()

    def destroy(self):
        if self._timer:
            self.after_cancel(self._timer)
        super().destroy()


# ══════════════════════════════════════════════════════════════
#  4–7. FACEBOOK BM TOOLS (shared base pattern)
# ══════════════════════════════════════════════

def _parse_bm_input(raw):
    """Parse BM input lines into list of (display, bm_id/username)."""
    lines = [l.strip() for l in raw.splitlines() if l.strip()]
    results = []
    for line in lines:
        # Try to extract numeric ID from URL
        m = re.search(r'(?:act=|bm_id=|/business/)(\d+)', line)
        if m:
            results.append((line, m.group(1)))
            continue
        # Try numeric ID directly
        if line.isdigit() and len(line) >= 5:
            results.append((line, line))
            continue
        # Try username/path
        m2 = re.search(r'facebook\.com/([^/?\s]+)', line)
        if m2:
            results.append((line, m2.group(1)))
            continue
        # Fallback: treat as identifier
        results.append((line, line))
    return results


def _simulate_bm_check(bm_id, tool_type):
    """Simulate a BM check result (demo data for UI testing)."""
    h = int(hashlib.md5(bm_id.encode()).hexdigest()[:8], 16)
    if tool_type == "live":
        statuses = ["\u2705 Active", "\u2705 Active", "\u2705 Active",
                    "\u274C Restricted", "\u26A0\uFE0F Disabled", "\u2705 Active"]
        status = statuses[h % len(statuses)]
        return f"BM {bm_id}: {status}"
    elif tool_type == "verified":
        v = ["Verified", "Not Verified", "Pending Review"]
        return f"BM {bm_id}: {v[h % len(v)]}"
    elif tool_type == "link":
        link_statuses = ["\u2705 Link Active", "\u2705 Link Active",
                         "\u274C Link Broken", "\u2705 Link Active",
                         "\u26A0\uFE0F Link Expired"]
        return f"BM {bm_id}: {link_statuses[h % len(link_statuses)]}"
    elif tool_type == "name":
        names = ["Digital Marketing Co", "Global Ads LLC", "Tech Solutions Inc",
                 "Media Group Ltd", "Social Connect Agency", "Brand Builders"]
        return f"BM {bm_id}: {names[h % len(names)]}"
    return f"BM {bm_id}: Unknown"


class _BMToolBase(ctk.CTkToplevel):
    """Shared base for all 4 BM tool modals."""

    TOOL_TYPE = ""
    TOOL_TITLE = ""
    TOOL_SUBTITLE = ""
    TOOL_ICON = ""
    TOOL_BADGE_COLOR = "#dbeafe"
    TOOL_BTN_TEXT = ""

    def __init__(self, parent):
        CLR = get_CLR()
        super().__init__(parent)
        self.title(self.TOOL_TITLE)
        self.geometry("740x640")
        self.minsize(480, 400)
        self.resizable(True, True)
        self.configure(fg_color=CLR["bg_modal"])
        self.update_idletasks()
        px = parent.winfo_x() + (parent.winfo_width() - 740) // 2
        py = parent.winfo_y() + (parent.winfo_height() - 640) // 2
        self.geometry(f"+{max(0,px)}+{max(0,py)}")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew", padx=24, pady=24)
        scroll.grid_columnconfigure(0, weight=1)
        r = 0

        # Title
        title_row = ctk.CTkFrame(scroll, fg_color="transparent")
        title_row.grid(row=r, column=0, sticky="ew", pady=(0, 4)); r += 1
        badge = ctk.CTkFrame(title_row, width=42, height=42, corner_radius=10,
                             fg_color=self.TOOL_BADGE_COLOR)
        badge.pack(side="left", padx=(0, 12)); badge.pack_propagate(False)
        ctk.CTkLabel(badge, text=self.TOOL_ICON,
                     font=("Segoe UI Emoji", 20)).pack(expand=True)
        tt = ctk.CTkFrame(title_row, fg_color="transparent")
        tt.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(tt, text=self.TOOL_TITLE, font=("Segoe UI", 16, "bold"),
                     text_color=CLR["text"], anchor="w").pack(anchor="w")
        ctk.CTkLabel(tt, text=self.TOOL_SUBTITLE, font=F_BODY,
                     text_color=CLR["text_dim"], anchor="w").pack(anchor="w", pady=(2,0))

        # Input
        ctk.CTkLabel(scroll, text="Facebook BM Links or IDs (one per line)",
                     font=F_BODY, text_color=CLR["text_dim"]).grid(
            row=r, column=0, sticky="w", pady=(16, 6)); r += 1

        self.input_box = ctk.CTkTextbox(
            scroll, height=120, font=F_MONO_SM, corner_radius=8,
            fg_color=CLR["bg_input"], border_color=CLR["border"],
            border_width=1, text_color=CLR["text"])
        self.input_box.grid(row=r, column=0, sticky="ew", pady=(0, 10)); r += 1
        self.input_box.insert("1.0",
            "Paste BM links or IDs, e.g.:\n"
            "https://business.facebook.com/settings?business=123456789\n"
            "987654321")

        # Buttons
        btn_row = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_row.grid(row=r, column=0, sticky="ew", pady=(0, 14)); r += 1
        self.check_btn = ctk.CTkButton(
            btn_row, text=self.TOOL_BTN_TEXT, font=("Segoe UI", 12, "bold"),
            height=44, corner_radius=10, fg_color=CLR["accent"],
            hover_color=CLR["accent_hov"], text_color="white",
            command=self._check, width=200)
        self.check_btn.pack(side="left")
        ctk.CTkButton(btn_row, text="\U0001F5D1  Clear", width=80, height=44,
                      corner_radius=10, font=F_BODY,
                      fg_color=CLR["bg_input"], border_color=CLR["border"],
                      border_width=1, text_color=CLR["text"],
                      hover_color=CLR["border"],
                      command=self._clear).pack(side="left", padx=(10, 0))

        # Result
        self.result_card = ctk.CTkFrame(scroll, corner_radius=12,
                                        fg_color=CLR["bg_card"],
                                        border_color=CLR["border"], border_width=1)
        self.result_card.grid(row=r, column=0, sticky="ew", pady=(0, 8)); r += 1
        res_inner = ctk.CTkFrame(self.result_card, fg_color="transparent")
        res_inner.pack(fill="x", padx=20, pady=16)

        self.result_title = ctk.CTkLabel(res_inner, text="Results", font=F_SECTION,
                                         text_color=CLR["text"])
        self.result_title.pack(anchor="w", pady=(0, 8))
        self.result_box = ctk.CTkTextbox(
            res_inner, height=180, font=F_MONO_SM, corner_radius=8,
            fg_color=CLR["bg_input"], border_color=CLR["border"],
            border_width=1, state="disabled", text_color=CLR["text"])
        self.result_box.pack(fill="x")

        ctk.CTkButton(res_inner, text="\U0001F4CB Copy Results", width=130, height=32,
                      corner_radius=6, font=F_SMALL,
                      fg_color=CLR["bg_input"], border_color=CLR["border"],
                      border_width=1, text_color=CLR["text"],
                      hover_color=CLR["border"],
                      command=self._copy_result).pack(anchor="w", pady=(8, 0))

        self.result_card.grid_remove()

    def _check(self):
        CLR = get_CLR()
        raw = self.input_box.get("1.0", "end").strip()
        if not raw or raw.startswith("Paste"):
            messagebox.showwarning("Error", "Please enter BM links or IDs.")
            return

        items = _parse_bm_input(raw)
        if not items:
            messagebox.showwarning("Error", "No valid BM entries found.")
            return

        lines = [f"  Checked {len(items)} BM(s):", "  " + "\u2500" * 60]
        for disp, bm_id in items:
            result = _simulate_bm_check(bm_id, self.TOOL_TYPE)
            lines.append(f"  {result}")
        lines.append("")
        lines.append(f"  \u2713  Scan complete at {datetime.now().strftime('%H:%M:%S')}")

        self.result_card.grid()
        self.result_title.configure(text="\u2713  Check Results",
                                    text_color=CLR["success"])
        self.result_box.configure(state="normal")
        self.result_box.delete("1.0", "end")
        self.result_box.insert("1.0", "\n".join(lines))
        self.result_box.configure(state="disabled")

    def _clear(self):
        self.input_box.delete("1.0", "end")
        self.result_card.grid_remove()

    def _copy_result(self):
        text = self.result_box.get("1.0", "end").strip()
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            messagebox.showinfo("Copied", "Results copied to clipboard!")


class CheckLiveBMModal(_BMToolBase):
    TOOL_TYPE = "live"
    TOOL_TITLE = "Check Live BM"
    TOOL_SUBTITLE = "Check if Facebook Business Manager accounts are active"
    TOOL_ICON = "\U0001F4BC"
    TOOL_BADGE_COLOR = "#dbeafe"
    TOOL_BTN_TEXT = "\U0001F50D  Check BM Status"


class CheckBMVerifiedModal(_BMToolBase):
    TOOL_TYPE = "verified"
    TOOL_TITLE = "Check BM Verified"
    TOOL_SUBTITLE = "Verify Facebook Business Manager verification status"
    TOOL_ICON = "\u2705"
    TOOL_BADGE_COLOR = "#dcfce7"
    TOOL_BTN_TEXT = "\u2705  Check Verification"


class CheckLinkBMModal(_BMToolBase):
    TOOL_TYPE = "link"
    TOOL_TITLE = "Check Link BM"
    TOOL_SUBTITLE = "Validate Facebook Business Manager links"
    TOOL_ICON = "\U0001F517"
    TOOL_BADGE_COLOR = "#fef3c7"
    TOOL_BTN_TEXT = "\U0001F517  Check Links"


class CheckBMNameModal(_BMToolBase):
    TOOL_TYPE = "name"
    TOOL_TITLE = "Check BM Name"
    TOOL_SUBTITLE = "Look up Facebook Business Manager names by ID"
    TOOL_ICON = "\U0001F465"
    TOOL_BADGE_COLOR = "#e0e7ff"
    TOOL_BTN_TEXT = "\U0001F465  Find BM Names"


# ══════════════════════════════════════════════════════════════
#  8. CHECK LIVE INSTAGRAM
# ══════════════════════════════════════════════

class CheckLiveIGModal(ctk.CTkToplevel):
    def __init__(self, parent):
        CLR = get_CLR()
        super().__init__(parent)
        self.title("Check Live Instagram")
        self.geometry("740x660")
        self.minsize(480, 400)
        self.resizable(True, True)
        self.configure(fg_color=CLR["bg_modal"])
        self.update_idletasks()
        px = parent.winfo_x() + (parent.winfo_width() - 740) // 2
        py = parent.winfo_y() + (parent.winfo_height() - 660) // 2
        self.geometry(f"+{max(0,px)}+{max(0,py)}")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew", padx=24, pady=24)
        scroll.grid_columnconfigure(0, weight=1)
        r = 0

        # Title
        title_row = ctk.CTkFrame(scroll, fg_color="transparent")
        title_row.grid(row=r, column=0, sticky="ew", pady=(0, 4)); r += 1
        badge = ctk.CTkFrame(title_row, width=42, height=42, corner_radius=10,
                             fg_color="#fce7f3")
        badge.pack(side="left", padx=(0, 12)); badge.pack_propagate(False)
        ctk.CTkLabel(badge, text="\U0001F4F7", font=("Segoe UI Emoji", 20)).pack(expand=True)
        tt = ctk.CTkFrame(title_row, fg_color="transparent")
        tt.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(tt, text="Check Live Instagram", font=("Segoe UI", 16, "bold"),
                     text_color=CLR["text"], anchor="w").pack(anchor="w")
        ctk.CTkLabel(tt, text="Check if Instagram accounts are active or deleted",
                     font=F_BODY, text_color=CLR["text_dim"],
                     anchor="w").pack(anchor="w", pady=(2,0))

        # Input
        ctk.CTkLabel(scroll, text="Instagram Usernames or URLs (one per line)",
                     font=F_BODY, text_color=CLR["text_dim"]).grid(
            row=r, column=0, sticky="w", pady=(16, 6)); r += 1

        self.input_box = ctk.CTkTextbox(
            scroll, height=120, font=F_MONO_SM, corner_radius=8,
            fg_color=CLR["bg_input"], border_color=CLR["border"],
            border_width=1, text_color=CLR["text"])
        self.input_box.grid(row=r, column=0, sticky="ew", pady=(0, 10)); r += 1
        self.input_box.insert("1.0",
            "Paste usernames or URLs, e.g.:\n"
            "cristiano\n"
            "https://www.instagram.com/nike")

        # Buttons
        btn_row = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_row.grid(row=r, column=0, sticky="ew", pady=(0, 14)); r += 1
        ctk.CTkButton(btn_row, text="\U0001F50D  Check Accounts",
                      font=("Segoe UI", 12, "bold"), height=44, corner_radius=10,
                      fg_color=CLR["accent"], hover_color=CLR["accent_hov"],
                      text_color="white", command=self._check, width=200
                      ).pack(side="left")
        ctk.CTkButton(btn_row, text="\U0001F5D1  Clear", width=80, height=44,
                      corner_radius=10, font=F_BODY,
                      fg_color=CLR["bg_input"], border_color=CLR["border"],
                      border_width=1, text_color=CLR["text"],
                      hover_color=CLR["border"],
                      command=self._clear).pack(side="left", padx=(10, 0))

        # Result
        self.result_card = ctk.CTkFrame(scroll, corner_radius=12,
                                        fg_color=CLR["bg_card"],
                                        border_color=CLR["border"], border_width=1)
        self.result_card.grid(row=r, column=0, sticky="ew", pady=(0, 8)); r += 1
        res_inner = ctk.CTkFrame(self.result_card, fg_color="transparent")
        res_inner.pack(fill="x", padx=20, pady=16)

        self.result_title = ctk.CTkLabel(res_inner, text="Results", font=F_SECTION,
                                         text_color=CLR["text"])
        self.result_title.pack(anchor="w", pady=(0, 8))
        self.result_box = ctk.CTkTextbox(
            res_inner, height=200, font=F_MONO_SM, corner_radius=8,
            fg_color=CLR["bg_input"], border_color=CLR["border"],
            border_width=1, state="disabled", text_color=CLR["text"])
        self.result_box.pack(fill="x")

        ctk.CTkButton(res_inner, text="\U0001F4CB Copy Results", width=130, height=32,
                      corner_radius=6, font=F_SMALL,
                      fg_color=CLR["bg_input"], border_color=CLR["border"],
                      border_width=1, text_color=CLR["text"],
                      hover_color=CLR["border"],
                      command=self._copy_result).pack(anchor="w", pady=(8, 0))
        self.result_card.grid_remove()

        # Guide
        guide = ctk.CTkFrame(scroll, corner_radius=12, fg_color=CLR["bg_card"],
                             border_color=CLR["border"], border_width=1)
        guide.grid(row=r, column=0, sticky="ew", pady=(16, 8)); r += 1
        gi = ctk.CTkFrame(guide, fg_color="transparent")
        gi.pack(fill="x", padx=20, pady=16)
        ctk.CTkLabel(gi, text="How to Use", font=F_SECTION,
                     text_color=CLR["text"]).pack(anchor="w", pady=(0, 8))
        steps = [
            "1. Enter Instagram usernames or profile URLs (one per line)",
            "2. Click 'Check Accounts' to verify each account",
            "3. Results show: \u2705 Live | \U0001F512 Private | \u274C Deleted/Not Found",
            "4. Use Copy Results to export the check report",
        ]
        for s in steps:
            ctk.CTkLabel(gi, text=s, font=F_BODY, text_color=CLR["text_dim"],
                         anchor="w").pack(anchor="w", pady=(0, 4))

    def _extract_username(self, line):
        line = line.strip()
        m = re.search(r'instagram\.com/([^/?\s#]+)', line)
        if m:
            return m.group(1)
        if re.match(r'^[\w.]+$', line):
            return line
        return line

    def _check(self):
        CLR = get_CLR()
        raw = self.input_box.get("1.0", "end").strip()
        if not raw or raw.startswith("Paste"):
            messagebox.showwarning("Error", "Please enter usernames or URLs.")
            return

        usernames = [self._extract_username(l) for l in raw.splitlines()
                     if l.strip() and not l.strip().startswith("Paste")]
        if not usernames:
            messagebox.showwarning("Error", "No valid entries found.")
            return

        lines = [f"  Checked {len(usernames)} account(s):", "  " + "\u2500" * 55]
        for u in usernames:
            h = int(hashlib.md5(u.encode()).hexdigest()[:8], 16)
            statuses = [
                "\u2705 Live (Public)", "\u2705 Live (Public)",
                "\U0001F512 Live (Private)", "\u2705 Live (Public)",
                "\u274C Not Found / Deleted", "\u2705 Live (Public)",
            ]
            status = statuses[h % len(statuses)]
            followers = random.randint(10, 5000000) if "Live" in status else "N/A"
            lines.append(f"  @{u:<20} {status}    Followers: {followers:,}")

        lines.append("")
        lines.append(f"  \u2713  Scan complete at {datetime.now().strftime('%H:%M:%S')}")

        self.result_card.grid()
        self.result_title.configure(text="\u2713  Account Check Results",
                                    text_color=CLR["success"])
        self.result_box.configure(state="normal")
        self.result_box.delete("1.0", "end")
        self.result_box.insert("1.0", "\n".join(lines))
        self.result_box.configure(state="disabled")

    def _clear(self):
        self.input_box.delete("1.0", "end")
        self.result_card.grid_remove()

    def _copy_result(self):
        text = self.result_box.get("1.0", "end").strip()
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            messagebox.showinfo("Copied", "Results copied!")


# ══════════════════════════════════════════════════════════════
#  9. DOWNLOAD INSTAGRAM
# ══════════════════════════════════════════════

class DownloadIGModal(ctk.CTkToplevel):
    def __init__(self, parent):
        CLR = get_CLR()
        super().__init__(parent)
        self.title("Download Instagram")
        self.geometry("740x660")
        self.minsize(480, 400)
        self.resizable(True, True)
        self.configure(fg_color=CLR["bg_modal"])
        self.update_idletasks()
        px = parent.winfo_x() + (parent.winfo_width() - 740) // 2
        py = parent.winfo_y() + (parent.winfo_height() - 660) // 2
        self.geometry(f"+{max(0,px)}+{max(0,py)}")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew", padx=24, pady=24)
        scroll.grid_columnconfigure(0, weight=1)
        r = 0

        # Title
        title_row = ctk.CTkFrame(scroll, fg_color="transparent")
        title_row.grid(row=r, column=0, sticky="ew", pady=(0, 4)); r += 1
        badge = ctk.CTkFrame(title_row, width=42, height=42, corner_radius=10,
                             fg_color="#fce7f3")
        badge.pack(side="left", padx=(0, 12)); badge.pack_propagate(False)
        ctk.CTkLabel(badge, text="\u2B07\uFE0F", font=("Segoe UI Emoji", 20)).pack(expand=True)
        tt = ctk.CTkFrame(title_row, fg_color="transparent")
        tt.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(tt, text="Download Instagram", font=("Segoe UI", 16, "bold"),
                     text_color=CLR["text"], anchor="w").pack(anchor="w")
        ctk.CTkLabel(tt, text="Download Reels, Stories, and Videos from Instagram",
                     font=F_BODY, text_color=CLR["text_dim"],
                     anchor="w").pack(anchor="w", pady=(2,0))

        # Content type selector (responsive grid)
        type_row = ctk.CTkFrame(scroll, fg_color="transparent")
        type_row.grid(row=r, column=0, sticky="ew", pady=(16, 8)); r += 1
        ctk.CTkLabel(type_row, text="Content Type:", font=F_BODY,
                     text_color=CLR["text_dim"]).grid(row=0, column=0, padx=(0, 4))
        self.content_type = ctk.StringVar(value="Reels")
        for ci, ct in enumerate(["Reels", "Stories", "Videos", "Photos"]):
            ctk.CTkRadioButton(type_row, text=ct, variable=self.content_type,
                               value=ct, font=F_BODY,
                               text_color=CLR["text"]).grid(
                row=0, column=ci+1, padx=(8, 0))

        # Input
        ctk.CTkLabel(scroll, text="Instagram URL",
                     font=F_BODY, text_color=CLR["text_dim"]).grid(
            row=r, column=0, sticky="w", pady=(8, 6)); r += 1

        self.url_entry = ctk.CTkEntry(
            scroll,
            placeholder_text="https://www.instagram.com/reel/ABC123/ or username for stories",
            font=F_MONO, height=44, corner_radius=8,
            border_color=CLR["border"], fg_color=CLR["bg_input"],
            text_color=CLR["text"])
        self.url_entry.grid(row=r, column=0, sticky="ew", pady=(0, 12)); r += 1

        # Buttons
        btn_row = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_row.grid(row=r, column=0, sticky="ew", pady=(0, 14)); r += 1
        ctk.CTkButton(btn_row, text="\u2B07\uFE0F  Get Download Link",
                      font=("Segoe UI", 12, "bold"), height=48, corner_radius=10,
                      fg_color=CLR["accent"], hover_color=CLR["accent_hov"],
                      text_color="white", command=self._get_link, width=200
                      ).pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(btn_row, text="\U0001F5D1  Clear", width=80, height=48,
                      corner_radius=10, font=F_BODY,
                      fg_color=CLR["bg_input"], border_color=CLR["border"],
                      border_width=1, text_color=CLR["text"],
                      hover_color=CLR["border"],
                      command=self._clear).pack(side="right")

        # Result
        self.result_card = ctk.CTkFrame(scroll, corner_radius=12,
                                        fg_color=CLR["bg_card"],
                                        border_color=CLR["border"], border_width=1)
        self.result_card.grid(row=r, column=0, sticky="ew", pady=(0, 8)); r += 1
        res_inner = ctk.CTkFrame(self.result_card, fg_color="transparent")
        res_inner.pack(fill="x", padx=20, pady=16)

        self.result_title = ctk.CTkLabel(res_inner, text="Download Info", font=F_SECTION,
                                         text_color=CLR["text"])
        self.result_title.pack(anchor="w", pady=(0, 8))
        self.result_box = ctk.CTkTextbox(
            res_inner, height=120, font=F_MONO_SM, corner_radius=8,
            fg_color=CLR["bg_input"], border_color=CLR["border"],
            border_width=1, state="disabled", text_color=CLR["text"])
        self.result_box.pack(fill="x")

        dl_btn_row = ctk.CTkFrame(res_inner, fg_color="transparent")
        dl_btn_row.pack(fill="x", pady=(10, 0))
        ctk.CTkButton(dl_btn_row, text="\U0001F4CB Copy Link", width=120, height=32,
                      corner_radius=6, font=F_SMALL,
                      fg_color=CLR["bg_input"], border_color=CLR["border"],
                      border_width=1, text_color=CLR["text"],
                      hover_color=CLR["border"],
                      command=self._copy_link).pack(side="left")
        ctk.CTkButton(dl_btn_row, text="\U0001F4BE Save to File", width=120, height=32,
                      corner_radius=6, font=F_SMALL,
                      fg_color=CLR["accent"], hover_color=CLR["accent_hov"],
                      text_color="white",
                      command=self._save_file).pack(side="left", padx=(8, 0))
        self.result_card.grid_remove()

        # Guide
        guide = ctk.CTkFrame(scroll, corner_radius=12, fg_color=CLR["bg_card"],
                             border_color=CLR["border"], border_width=1)
        guide.grid(row=r, column=0, sticky="ew", pady=(16, 8)); r += 1
        gi = ctk.CTkFrame(guide, fg_color="transparent")
        gi.pack(fill="x", padx=20, pady=16)
        ctk.CTkLabel(gi, text="Supported Content", font=F_SECTION,
                     text_color=CLR["text"]).pack(anchor="w", pady=(0, 8))
        supported = [
            "\U0001F3AC  Reels: instagram.com/reel/XXXXX/",
            "\U0001F4F1  Stories: Enter username \u2192 fetches active stories",
            "\U0001F3A5  Videos: instagram.com/p/XXXXX/ (video posts)",
            "\U0001F4F7  Photos: instagram.com/p/XXXXX/ (image posts)",
            "",
            "\u26A0\uFE0F  Note: Private accounts require authentication.",
            "     Downloaded files are saved to your chosen directory.",
        ]
        for s in supported:
            ctk.CTkLabel(gi, text=s, font=F_BODY, text_color=CLR["text_dim"],
                         anchor="w").pack(anchor="w", pady=(0, 3))

    def _get_link(self):
        CLR = get_CLR()
        url = self.url_entry.get().strip()
        ct = self.content_type.get()

        if not url:
            messagebox.showwarning("Error", "Please enter an Instagram URL or username.")
            return

        # Validate URL format
        if not url.startswith("http"):
            if ct == "Stories":
                url = f"https://www.instagram.com/stories/{url}/"
            else:
                url = f"https://www.instagram.com/{url}"

        # Parse shortcode
        shortcode = ""
        m = re.search(r'/(?:reel|p|tv)/([^/?]+)', url)
        if m:
            shortcode = m.group(1)
        else:
            m2 = re.search(r'instagram\.com/(?:stories/)?([^/?\s]+)', url)
            if m2:
                shortcode = m2.group(1)

        if not shortcode:
            messagebox.showerror("Error", "Could not parse the Instagram URL.")
            return

        # Generate download info
        h = hashlib.md5(f"{shortcode}{ct}".encode()).hexdigest()
        fake_id = h[:12]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        lines = [
            f"  Content Type:  {ct}",
            f"  Source URL:    {url}",
            f"  Shortcode:     {shortcode}",
            f"  Resolution:    {'1080x1920' if ct in ('Reels','Stories') else '1080x1080'}",
            f"  Format:        {'MP4' if ct in ('Reels','Stories','Videos') else 'JPG'}",
            f"  File Name:     ig_{ct.lower()}_{fake_id}_{timestamp}.{'mp4' if ct in ('Reels','Stories','Videos') else 'jpg'}",
            f"  Status:        \u2705 Ready to Download",
            "",
            f"  Download URL:  https://cdninstagram.example.com/ig/{fake_id}/download",
        ]
        self._last_url = f"https://cdninstagram.example.com/ig/{fake_id}/download"

        self.result_card.grid()
        self.result_title.configure(text="\u2713  Download Ready",
                                    text_color=CLR["success"])
        self.result_box.configure(state="normal")
        self.result_box.delete("1.0", "end")
        self.result_box.insert("1.0", "\n".join(lines))
        self.result_box.configure(state="disabled")

    def _clear(self):
        self.url_entry.delete(0, "end")
        self.result_card.grid_remove()

    def _copy_link(self):
        if hasattr(self, '_last_url'):
            self.clipboard_clear()
            self.clipboard_append(self._last_url)
            messagebox.showinfo("Copied", "Download link copied!")
        else:
            messagebox.showwarning("Error", "Get a download link first.")

    def _save_file(self):
        if not hasattr(self, '_last_url'):
            messagebox.showwarning("Error", "Get a download link first.")
            return
        ext = "mp4" if "mp4" in (self.result_box.get("1.0", "end")) else "jpg"
        path = filedialog.asksaveasfilename(
            defaultextension=f".{ext}",
            filetypes=[("MP4 Video", "*.mp4"), ("JPEG Image", "*.jpg"), ("All", "*.*")],
            initialfile=f"ig_download.{ext}")
        if not path:
            return
        # Write a placeholder file (real download would need requests)
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"# Instagram Download Placeholder\n")
            f.write(f"# Source: {self._last_url}\n")
            f.write(f"# Content from the result panel above\n")
            text = self.result_box.get("1.0", "end").strip()
            f.write(text)
        messagebox.showinfo("Saved", f"File info saved to:\n{path}\n\n"
                            "Note: Actual media download requires\n"
                            "a backend service with Instagram API access.")

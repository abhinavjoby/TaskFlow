"""
Phase 4: GUI Dashboard — Smart Study Planner
Liquid Glass · Monospace · Red Accent · Professional
--------------------------------------------------------------
python main.py
"""

import customtkinter as ctk
import tkinter as tk
import threading
import time
import os
import json
import pickle
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from session_logger import save_session, setup_csv, CSV_FILE
from webcam_monitor import WebcamMonitor
from circular_buffer import CircularBuffer
from ml_model import auto_retrain, get_subject_recommendations, get_smart_insights

# ─────────────────────────────────────────────
# THEME
# ─────────────────────────────────────────────
THEMES = {
    "dark": {
        "BG":           "#0A0A0A",
        "BG2":          "#0F0F0F",
        "CARD":         "#131313",
        "CARD2":        "#1A1A1A",
        "BORDER":       "#2A2A2A",
        "GLOW":         "#2A1515",
        "GLASS":        "#1A1A1A",
        "GLASS_BORDER": "#FDF6F6",
        "TEXT":         "#F0F0F0",
        "SUBTEXT":      "#F5F0F0",
        "DIM":          "#333333",
        "RED":          "#FF3B30",
        "RED_DIM":      "#2A1515",
        "GREEN":        "#30D158",
        "ORANGE":       "#FF9F0A",
        "BLUE":         "#0A84FF",
        "WHITE":        "#FFFFFF",
        "PLOT_BG":      "#0A0A0A",
        "GRID":         "#1A1A1A",
        "mode":         "dark",
    },
    "light": {
        "BG":           "#F5F5F5",
        "BG2":          "#EFEFEF",
        "CARD":         "#FFFFFF",
        "CARD2":        "#F8F8F8",
        "BORDER":       "#E0E0E0",
        "GLOW":         "#F5E6E6",
        "GLASS":        "#F0F0F0",
        "GLASS_BORDER": "#E0E0E0",
        "TEXT":         "#111111",
        "SUBTEXT":      "#999999",
        "DIM":          "#CCCCCC",
        "RED":          "#FF3B30",
        "RED_DIM":      "#2A1515",
        "GREEN":        "#28A745",
        "ORANGE":       "#FF9500",
        "BLUE":         "#007AFF",
        "WHITE":        "#111111",
        "PLOT_BG":      "#FFFFFF",
        "GRID":         "#EEEEEE",
        "mode":         "light",
    }
}

_theme = "dark"

def T(k): return THEMES[_theme][k]

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
SUBJECTS = ["EOC", "MFC", "OOP", "UID", "DSA", "EEE"]
SUBJECT_DIFFICULTY = {
    "DSA": 5, "OOP": 4, "EEE": 4,
    "MFC": 3, "UID": 3, "EOC": 2,
}

STATUS_COLOR_KEY = {
    "FOCUSED":    "GREEN",
    "DROWSY":     "ORANGE",
    "DISTRACTED": "RED",
    "WAITING...": "SUBTEXT",
}

MODEL_FILE  = "models/model.pkl"
NOTES_FILE  = "data/notes.json"
BUFFER_SIZE = 300
TIME_SLOTS  = [8, 9, 10, 11, 14, 15, 16, 19, 20, 21]
MONO        = "Courier New"
SANS        = "Helvetica Neue"


def format_hour(h):
    if h == 12:  return "12:00 PM"
    elif h > 12: return f"{h-12:02d}:00 PM"
    else:        return f"{h:02d}:00 AM"

def load_notes():
    if os.path.exists(NOTES_FILE):
        with open(NOTES_FILE) as f:
            return json.load(f)
    return []

def save_notes_file(notes):
    os.makedirs("data", exist_ok=True)
    with open(NOTES_FILE, "w") as f:
        json.dump(notes, f)


# ─────────────────────────────────────────────
# GLASS CARD WIDGET
# ─────────────────────────────────────────────
def glass_card(parent, glow=False, **kwargs):
    kwargs.setdefault("corner_radius", 12)
    kwargs.setdefault("border_width", 1)
    kwargs.setdefault("fg_color", T("CARD"))
    kwargs.setdefault("border_color", T("RED") if glow else T("GLASS_BORDER"))
    return ctk.CTkFrame(parent, **kwargs)


# ═══════════════════════════════════════════════
# INTRO SCREEN
# ═══════════════════════════════════════════════
class IntroScreen(ctk.CTkFrame):
    def __init__(self, master, on_start):
        super().__init__(master, fg_color=T("BG"), corner_radius=0)
        self.on_start = on_start
        self._build()

    def _build(self):
        wrap = ctk.CTkFrame(self, fg_color="transparent")
        wrap.place(relx=0.5, rely=0.5, anchor="center")

        # Header
        ctk.CTkLabel(wrap,
                     text="STUDY_PLANNER",
                     font=ctk.CTkFont(MONO, 32, "bold"),
                     text_color=T("TEXT")).pack(pady=(0, 4))

        ctk.CTkLabel(wrap,
                     text="FOCUS  ·  TRACK  ·  IMPROVE",
                     font=ctk.CTkFont(MONO, 11),
                     text_color=T("RED")).pack(pady=(0, 40))

        # Glass card
        card = ctk.CTkFrame(wrap,
                            fg_color=T("CARD"),
                            corner_radius=16,
                            border_width=1,
                            border_color=T("GLASS_BORDER"))
        card.pack()

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(padx=52, pady=44)

        ctk.CTkLabel(inner,
                     text="ENTER DETAILS",
                     font=ctk.CTkFont(MONO, 13, "bold"),
                     text_color=T("RED")).pack(anchor="w", pady=(0, 24))

        # Name
        ctk.CTkLabel(inner, text="NAME",
                     font=ctk.CTkFont(MONO, 10),
                     text_color=T("SUBTEXT")).pack(anchor="w")
        self.name_entry = ctk.CTkEntry(inner,
                                        width=340, height=46,
                                        placeholder_text="your name",
                                        font=ctk.CTkFont(MONO, 13),
                                        corner_radius=8,
                                        border_color=T("BORDER"),
                                        border_width=1,
                                        fg_color=T("CARD2"),
                                        text_color=T("TEXT"),
                                        placeholder_text_color=T("SUBTEXT"))
        self.name_entry.pack(pady=(4, 18))

        # Subject
        ctk.CTkLabel(inner, text="SUBJECT",
                     font=ctk.CTkFont(MONO, 10),
                     text_color=T("SUBTEXT")).pack(anchor="w")
        self.subject_var = ctk.StringVar(value="DSA")
        ctk.CTkOptionMenu(inner,
                          values=SUBJECTS,
                          variable=self.subject_var,
                          width=340, height=46,
                          font=ctk.CTkFont(MONO, 13),
                          corner_radius=8,
                          fg_color=T("CARD2"),
                          button_color=T("RED"),
                          button_hover_color="#CC2E25",
                          text_color=T("TEXT"),
                          dropdown_fg_color=T("CARD"),
                          dropdown_text_color=T("TEXT"),
                          dropdown_hover_color=T("BORDER")).pack(pady=(4, 24))

        self.err = ctk.CTkLabel(inner, text="",
                                 font=ctk.CTkFont(MONO, 10),
                                 text_color=T("RED"))
        self.err.pack(pady=(0, 10))

        ctk.CTkButton(inner,
                      text="CONTINUE  →",
                      width=340, height=48,
                      font=ctk.CTkFont(MONO, 13, "bold"),
                      corner_radius=8,
                      fg_color=T("RED"),
                      hover_color="#CC2E25",
                      text_color=T("WHITE"),
                      command=self._go).pack()

        ctk.CTkLabel(wrap,
                     text="you can change subject anytime",
                     font=ctk.CTkFont(MONO, 9),
                     text_color=T("SUBTEXT")).pack(pady=(18, 0))

    def _go(self):
        name = self.name_entry.get().strip()
        if not name:
            self.err.configure(text="! PLEASE ENTER YOUR NAME")
            return
        self.on_start(name, self.subject_var.get())


# ═══════════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════════
class Dashboard(ctk.CTkFrame):
    def __init__(self, master, name, subject, app_ref):
        super().__init__(master, fg_color=T("BG"), corner_radius=0)
        self.user_name  = name
        self.subject    = subject
        self.app_ref    = app_ref
        self.monitor    = None
        self.buffer     = None
        self.running    = False
        self.start_time = None
        self.elapsed    = 0
        self.current_status = "WAITING..."
        self.notes      = load_notes()

        setup_csv()
        self._build()
        self._refresh_recs()
        self._load_history()

    # ─────────────────────────────────────────
    # BUILD
    # ─────────────────────────────────────────
    def _build(self):
        # ── Top bar ──
        top = ctk.CTkFrame(self, height=50, corner_radius=0,
                            fg_color=T("CARD"), border_width=0)
        top.pack(fill="x")
        top.pack_propagate(False)

        ctk.CTkLabel(top,
                     text="STUDY_PLANNER",
                     font=ctk.CTkFont(MONO, 14, "bold"),
                     text_color=T("TEXT")).pack(side="left", padx=24)

        # Theme toggle
        self.theme_btn = ctk.CTkButton(top,
                                        text="◐",
                                        width=36, height=32,
                                        font=ctk.CTkFont(SANS, 15),
                                        corner_radius=8,
                                        fg_color=T("CARD2"),
                                        hover_color=T("BORDER"),
                                        text_color=T("TEXT"),
                                        border_width=1,
                                        border_color=T("BORDER"),
                                        command=self.app_ref.toggle_theme)
        self.theme_btn.pack(side="right", padx=12)

        ctk.CTkLabel(top,
                     text=self.user_name.upper(),
                     font=ctk.CTkFont(MONO, 11),
                     text_color=T("SUBTEXT")).pack(side="right", padx=8)

        ctk.CTkFrame(self, height=1, fg_color=T("BORDER"), corner_radius=0).pack(fill="x")

        # ── Body ──
        body = ctk.CTkFrame(self, fg_color=T("BG"), corner_radius=0)
        body.pack(fill="both", expand=True, padx=20, pady=20)

        # Sidebar
        sidebar = ctk.CTkFrame(body, width=248,
                                fg_color=T("CARD"),
                                corner_radius=12,
                                border_width=1,
                                border_color=T("GLASS_BORDER"))
        sidebar.pack(side="left", fill="y", padx=(0, 16))
        sidebar.pack_propagate(False)
        self._sidebar(sidebar)

        # Main
        main = ctk.CTkFrame(body, fg_color="transparent")
        main.pack(side="left", fill="both", expand=True)
        self._main(main)

    # ─────────────────────────────────────────
    # SIDEBAR
    # ─────────────────────────────────────────
    def _sidebar(self, p):
        P = {"padx": 20}

        self._slabel(p, "// SESSION")
        self._slbl(p, "SUBJECT")

        self.subject_var = ctk.StringVar(value=self.subject)
        ctk.CTkOptionMenu(p,
                          values=SUBJECTS,
                          variable=self.subject_var,
                          width=208, height=38,
                          font=ctk.CTkFont(MONO, 12),
                          corner_radius=8,
                          fg_color=T("CARD2"),
                          button_color=T("RED"),
                          button_hover_color="#CC2E25",
                          text_color=T("TEXT"),
                          dropdown_fg_color=T("CARD"),
                          dropdown_text_color=T("TEXT"),
                          dropdown_hover_color=T("BORDER")).pack(**P, pady=(4, 12))

        self.start_btn = ctk.CTkButton(p,
                                        text="▶  START SESSION",
                                        width=208, height=42,
                                        font=ctk.CTkFont(MONO, 12, "bold"),
                                        corner_radius=8,
                                        fg_color=T("RED"),
                                        hover_color="#CC2E25",
                                        text_color=T("WHITE"),
                                        command=self._toggle)
        self.start_btn.pack(**P, pady=(0, 20))

        self._div(p)
        self._slabel(p, "// ATTENTION")

        self.status_lbl = ctk.CTkLabel(p,
                                        text="WAITING...",
                                        font=ctk.CTkFont(MONO, 20, "bold"),
                                        text_color=T("SUBTEXT"))
        self.status_lbl.pack(anchor="w", **P, pady=(6, 2))

        self.timer_lbl = ctk.CTkLabel(p,
                                       text="00:00:00",
                                       font=ctk.CTkFont(MONO, 16),
                                       text_color=T("DIM"))
        self.timer_lbl.pack(anchor="w", **P, pady=(0, 18))

        self._div(p)
        self._slabel(p, "// FOCUS")

        self.focus_pct = ctk.CTkLabel(p,
                                       text="0%",
                                       font=ctk.CTkFont(MONO, 36, "bold"),
                                       text_color=T("TEXT"))
        self.focus_pct.pack(anchor="w", **P, pady=(6, 6))

        self.focus_bar = ctk.CTkProgressBar(p,
                                             width=208, height=4,
                                             corner_radius=2,
                                             progress_color=T("RED"),
                                             fg_color=T("BORDER"))
        self.focus_bar.pack(**P, pady=(0, 18))
        self.focus_bar.set(0)

        self._div(p)
        self._slabel(p, "// EVENTS")

        self.drowsy_lbl = ctk.CTkLabel(p,
                                        text="DROWSY      0",
                                        font=ctk.CTkFont(MONO, 11),
                                        text_color=T("ORANGE"))
        self.drowsy_lbl.pack(anchor="w", **P, pady=(6, 2))

        self.dist_lbl = ctk.CTkLabel(p,
                                      text="DISTRACTED  0",
                                      font=ctk.CTkFont(MONO, 11),
                                      text_color=T("RED"))
        self.dist_lbl.pack(anchor="w", **P, pady=(0, 20))

    # ─────────────────────────────────────────
    # MAIN TABS
    # ─────────────────────────────────────────
    def _main(self, p):
        tabs = ctk.CTkTabview(p,
                               fg_color=T("CARD"),
                               corner_radius=12,
                               border_width=1,
                               border_color=T("GLASS_BORDER"),
                               segmented_button_fg_color=T("CARD"),
                               segmented_button_selected_color=T("RED"),
                               segmented_button_selected_hover_color="#CC2E25",
                               segmented_button_unselected_color=T("CARD"),
                               segmented_button_unselected_hover_color=T("CARD2"),
                               text_color=T("SUBTEXT"),
                               text_color_disabled=T("SUBTEXT"))
        tabs.pack(fill="both", expand=True)

        for t in ["RECOMMEND", "INSIGHTS", "HISTORY", "TREND", "NOTES"]:
            tabs.add(t)

        self._tab_recs(tabs.tab("RECOMMEND"))
        self._tab_insights(tabs.tab("INSIGHTS"))
        self._tab_history(tabs.tab("HISTORY"))
        self._tab_chart(tabs.tab("TREND"))
        self._tab_notes(tabs.tab("NOTES"))

    # ─────────────────────────────────────────
    # TABS
    # ─────────────────────────────────────────
    def _tab_recs(self, p):
        self._thdr(p, "RECOMMENDATIONS", "ML-powered best time for each subject")
        self.rec_frame = ctk.CTkScrollableFrame(p, fg_color="transparent")
        self.rec_frame.pack(fill="both", expand=True, padx=20, pady=(0, 16))

    def _tab_insights(self, p):
        self._thdr(p, "INSIGHTS", "Personalised tips based on your data")
        self.ins_frame = ctk.CTkScrollableFrame(p, fg_color="transparent")
        self.ins_frame.pack(fill="both", expand=True, padx=20, pady=(0, 16))

    def _tab_history(self, p):
        self._thdr(p, "HISTORY", "Your recent study sessions")
        self.hist_frame = ctk.CTkScrollableFrame(p, fg_color="transparent")
        self.hist_frame.pack(fill="both", expand=True, padx=20, pady=(0, 16))

    def _tab_chart(self, p):
        self._thdr(p, "FOCUS TREND", "How your focus has changed over sessions")
        self.chart_frame = ctk.CTkFrame(p, fg_color="transparent")
        self.chart_frame.pack(fill="both", expand=True, padx=20, pady=(0, 16))
        self._draw_chart()

    def _tab_notes(self, p):
        self._thdr(p, "NOTES & TASKS", "Your study tasks and quick notes")

        row = ctk.CTkFrame(p, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=(0, 12))

        self.note_entry = ctk.CTkEntry(row,
                                        height=42,
                                        placeholder_text="add a note or task...",
                                        font=ctk.CTkFont(MONO, 12),
                                        corner_radius=8,
                                        border_color=T("BORDER"),
                                        border_width=1,
                                        fg_color=T("CARD2"),
                                        text_color=T("TEXT"),
                                        placeholder_text_color=T("SUBTEXT"))
        self.note_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.note_entry.bind("<Return>", lambda e: self._add_note())

        ctk.CTkButton(row,
                      text="ADD",
                      width=64, height=42,
                      font=ctk.CTkFont(MONO, 12, "bold"),
                      corner_radius=8,
                      fg_color=T("RED"),
                      hover_color="#CC2E25",
                      text_color=T("WHITE"),
                      command=self._add_note).pack(side="left")

        self.notes_frame = ctk.CTkScrollableFrame(p, fg_color="transparent")
        self.notes_frame.pack(fill="both", expand=True, padx=20, pady=(0, 16))
        self._render_notes()

    # ─────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────
    def _slabel(self, p, t):
        ctk.CTkLabel(p, text=t,
                     font=ctk.CTkFont(MONO, 9, "bold"),
                     text_color=T("RED")).pack(anchor="w", padx=20, pady=(16, 2))

    def _slbl(self, p, t):
        ctk.CTkLabel(p, text=t,
                     font=ctk.CTkFont(MONO, 10),
                     text_color=T("SUBTEXT")).pack(anchor="w", padx=20)

    def _div(self, p):
        ctk.CTkFrame(p, height=1, fg_color=T("BORDER")).pack(fill="x", padx=16, pady=2)

    def _thdr(self, p, title, sub):
        ctk.CTkLabel(p, text=title,
                     font=ctk.CTkFont(MONO, 15, "bold"),
                     text_color=T("TEXT")).pack(anchor="w", padx=20, pady=(16, 2))
        ctk.CTkLabel(p, text=sub,
                     font=ctk.CTkFont(MONO, 10),
                     text_color=T("SUBTEXT")).pack(anchor="w", padx=20, pady=(0, 10))

    def _gcard(self, parent, glow=False):
        return ctk.CTkFrame(parent,
                            fg_color=T("CARD2"),
                            corner_radius=10,
                            border_width=1,
                            border_color=T("RED") if glow else T("GLASS_BORDER"))

    # ─────────────────────────────────────────
    # SESSION
    # ─────────────────────────────────────────
    def _toggle(self):
        if not self.running: self._start()
        else: self._stop()

    def _start(self):
        self.subject    = self.subject_var.get()
        self.running    = True
        self.start_time = time.time()
        self.elapsed    = 0
        self.buffer     = CircularBuffer(size=BUFFER_SIZE)
        self.monitor    = WebcamMonitor()
        self.start_btn.configure(text="■  STOP SESSION",
                                  fg_color=T("CARD2"),
                                  hover_color=T("BORDER"),
                                  text_color=T("RED"),
                                  border_width=1,
                                  border_color=T("RED"))
        threading.Thread(target=self.monitor.run, daemon=True).start()
        threading.Thread(target=self._log_loop, daemon=True).start()
        self._update_ui()

    def _stop(self):
        self.running = False
        self.start_btn.configure(text="▶  START SESSION",
                                  fg_color=T("RED"),
                                  hover_color="#CC2E25",
                                  text_color=T("WHITE"),
                                  border_width=0)
        if self.buffer and self.start_time:
            save_session(self.subject, self.start_time, self.buffer)
        threading.Thread(target=self._retrain_bg, daemon=True).start()
        self.status_lbl.configure(text="WAITING...", text_color=T("SUBTEXT"))
        self.timer_lbl.configure(text="00:00:00", text_color=T("DIM"))
        self.focus_bar.set(0)
        self.focus_pct.configure(text="0%", text_color=T("TEXT"))
        self.drowsy_lbl.configure(text="DROWSY      0")
        self.dist_lbl.configure(text="DISTRACTED  0")
        self._load_history()
        self._draw_chart()

    def _retrain_bg(self):
        result = auto_retrain()
        if result:
            self.after(0, self._refresh_recs)

    def _log_loop(self):
        while self.running:
            if self.monitor:
                status = self.monitor.get_status()
                self.buffer.add(status)
                self.current_status = status
                if status == "DROWSY":
                    self.after(0, self._toast)
            time.sleep(1)

    def _update_ui(self):
        if not self.running:
            return
        status = self.current_status
        c      = T(STATUS_COLOR_KEY.get(status, "SUBTEXT"))
        self.status_lbl.configure(text=status, text_color=c)
        self.elapsed += 1
        h = self.elapsed // 3600
        m = (self.elapsed % 3600) // 60
        s = self.elapsed % 60
        self.timer_lbl.configure(text=f"{h:02d}:{m:02d}:{s:02d}",
                                  text_color=T("TEXT"))
        if self.buffer and self.buffer.count > 0:
            pct  = self.buffer.focus_percentage()
            bc   = T("GREEN") if pct >= 70 else T("ORANGE") if pct >= 50 else T("RED")
            self.focus_bar.set(pct / 100)
            self.focus_bar.configure(progress_color=bc)
            self.focus_pct.configure(text=f"{pct:.0f}%", text_color=bc)
            self.drowsy_lbl.configure(
                text=f"DROWSY      {self.buffer.drowsy_count()}")
            self.dist_lbl.configure(
                text=f"DISTRACTED  {self.buffer.distracted_count()}")
        self.after(1000, self._update_ui)

    def _toast(self):
        t = ctk.CTkToplevel(self)
        t.geometry("300x54+730+16")
        t.title("")
        t.attributes("-topmost", True)
        t.resizable(False, False)
        t.configure(fg_color=T("CARD"))
        ctk.CTkFrame(t, height=2, fg_color=T("ORANGE"),
                     corner_radius=0).pack(fill="x")
        ctk.CTkLabel(t,
                     text="! TAKE A BREAK  ·  DROWSINESS DETECTED",
                     font=ctk.CTkFont(MONO, 11, "bold"),
                     text_color=T("ORANGE")).pack(expand=True)
        self.after(3500, t.destroy)

    # ─────────────────────────────────────────
    # RECOMMENDATIONS
    # ─────────────────────────────────────────
    def _refresh_recs(self):
        for w in self.rec_frame.winfo_children():
            w.destroy()
        for w in self.ins_frame.winfo_children():
            w.destroy()

        if not os.path.exists(MODEL_FILE):
            ctk.CTkLabel(self.rec_frame,
                         text="! RUN ml_model.py FIRST",
                         text_color=T("RED"),
                         font=ctk.CTkFont(MONO, 12)).pack(pady=20)
            return

        try:
            with open(MODEL_FILE, "rb") as f:
                model = pickle.load(f)["model"]

            df = pd.read_csv(CSV_FILE)
            df["Start_Time"] = pd.to_datetime(df["Start_Time"])
            hr = df["Start_Time"].dt.hour
            df["hour_sin"]             = np.sin(2*np.pi*hr/24)
            df["hour_cos"]             = np.cos(2*np.pi*hr/24)
            df["subject_difficulty"]   = df["Subject"].map(SUBJECT_DIFFICULTY).fillna(3)
            df["drowsy_rate"]          = df["Drowsy_Count"] / (df["Duration_Minutes"] + 0.1)
            df["distracted_rate"]      = df["Distracted_Count"] / (df["Duration_Minutes"] + 0.1)
            df["historical_avg_focus"] = df.groupby("Subject")["Focus_Percentage"].transform("mean")

            recs = get_subject_recommendations(model, df)

            ranks = ["#1", "#2", "#3"]
            for i, (sub, t, sc) in enumerate(recs):
                top  = i == 0
                card = self._gcard(self.rec_frame, glow=top)
                card.pack(fill="x", pady=4)

                left = ctk.CTkFrame(card, fg_color="transparent")
                left.pack(side="left", padx=16, pady=14)

                if i < 3:
                    ctk.CTkLabel(left, text=ranks[i],
                                 font=ctk.CTkFont(MONO, 9),
                                 text_color=T("RED")).pack(anchor="w")

                ctk.CTkLabel(left, text=sub,
                             font=ctk.CTkFont(MONO, 16, "bold"),
                             text_color=T("TEXT")).pack(anchor="w")
                ctk.CTkLabel(left, text=t,
                             font=ctk.CTkFont(MONO, 10),
                             text_color=T("SUBTEXT")).pack(anchor="w")

                sc_c = T("GREEN") if sc >= 70 else T("ORANGE") if sc >= 50 else T("RED")
                right = ctk.CTkFrame(card, fg_color="transparent")
                right.pack(side="right", padx=20, pady=14)
                ctk.CTkLabel(right, text=f"{sc}",
                             font=ctk.CTkFont(MONO, 24, "bold"),
                             text_color=sc_c).pack()
                ctk.CTkLabel(right, text="/ 100",
                             font=ctk.CTkFont(MONO, 9),
                             text_color=T("SUBTEXT")).pack()

            # Insights
            insights = get_smart_insights(df)
            for ins in insights:
                card = self._gcard(self.ins_frame)
                card.pack(fill="x", pady=4)
                inner = ctk.CTkFrame(card, fg_color="transparent")
                inner.pack(fill="x", padx=16, pady=14)
                ctk.CTkLabel(inner,
                             text=f"{ins['icon']}  {ins['title'].upper()}",
                             font=ctk.CTkFont(MONO, 12, "bold"),
                             text_color=T("TEXT")).pack(anchor="w")
                ctk.CTkLabel(inner,
                             text=ins["text"],
                             font=ctk.CTkFont(MONO, 10),
                             text_color=T("SUBTEXT"),
                             wraplength=480,
                             justify="left").pack(anchor="w", pady=(4, 0))

        except Exception as e:
            ctk.CTkLabel(self.rec_frame,
                         text=f"! ERROR: {e}",
                         text_color=T("RED")).pack(pady=10)

    # ─────────────────────────────────────────
    # HISTORY
    # ─────────────────────────────────────────
    def _load_history(self):
        for w in self.hist_frame.winfo_children():
            w.destroy()
        if not os.path.exists(CSV_FILE):
            ctk.CTkLabel(self.hist_frame,
                         text="NO SESSIONS YET",
                         text_color=T("SUBTEXT"),
                         font=ctk.CTkFont(MONO, 12)).pack(pady=20)
            return
        try:
            df = pd.read_csv(CSV_FILE).tail(15).iloc[::-1]

            hdr = ctk.CTkFrame(self.hist_frame, fg_color="transparent")
            hdr.pack(fill="x", pady=(0, 6))
            for col, w in [("SUBJECT",130),("DATE",110),("DURATION",90),("FOCUS",75),("SCORE",65)]:
                ctk.CTkLabel(hdr, text=col, width=w,
                             font=ctk.CTkFont(MONO, 9),
                             text_color=T("RED")).pack(side="left", padx=4)

            for _, row in df.iterrows():
                r  = self._gcard(self.hist_frame)
                r.pack(fill="x", pady=3)
                sc = float(row["Quality_Label"])
                c  = T("GREEN") if sc >= 70 else T("ORANGE") if sc >= 50 else T("RED")
                for val, w, tc in [
                    (str(row["Subject"]), 130, T("TEXT")),
                    (str(row["Start_Time"])[:10], 110, T("SUBTEXT")),
                    (f"{row['Duration_Minutes']}m", 90, T("SUBTEXT")),
                    (f"{row['Focus_Percentage']}%", 75, T("GREEN")),
                    (f"{sc:.0f}", 65, c),
                ]:
                    ctk.CTkLabel(r, text=val, width=w,
                                 font=ctk.CTkFont(MONO, 11),
                                 text_color=tc).pack(side="left", padx=4, pady=10)

        except Exception as e:
            ctk.CTkLabel(self.hist_frame,
                         text=f"! ERROR: {e}",
                         text_color=T("RED")).pack(pady=10)

    # ─────────────────────────────────────────
    # CHART
    # ─────────────────────────────────────────
    def _draw_chart(self):
        for w in self.chart_frame.winfo_children():
            w.destroy()
        try:
            if not os.path.exists(CSV_FILE): raise Exception()
            df = pd.read_csv(CSV_FILE).tail(20)
            if len(df) < 2: raise Exception()

            fig, ax = plt.subplots(figsize=(7.2, 3.4))
            fig.patch.set_facecolor(T("PLOT_BG"))
            ax.set_facecolor(T("PLOT_BG"))

            x    = np.arange(len(df))
            vals = df["Focus_Percentage"].values
            subs = [str(r["Subject"])[:3] for _, r in df.iterrows()]

            # Try smooth line
            try:
                from scipy.interpolate import make_interp_spline
                xs = np.linspace(x.min(), x.max(), 300)
                ys = np.clip(make_interp_spline(x, vals, k=min(3, len(x)-1))(xs), 0, 100)
            except Exception:
                xs, ys = x, vals

            # Gradient fill
            ax.fill_between(xs, ys, alpha=0.08, color="#FF3B30", zorder=1)

            # Line
            ax.plot(xs, ys, color="#FF3B30", linewidth=1.8, zorder=3)

            # Dots
            dot_c = [T("GREEN") if v >= 70 else T("ORANGE") if v >= 50 else T("RED")
                     for v in vals]
            ax.scatter(x, vals, c=dot_c, s=50, zorder=5,
                       edgecolors=T("PLOT_BG"), linewidths=1.5)

            # 70% target line
            ax.axhline(y=70, color=T("GREEN"), linestyle="--",
                       linewidth=0.7, alpha=0.4)

            # Labels
            ax.set_xticks(x)
            ax.set_xticklabels(subs, fontsize=8,
                               color=T("SUBTEXT"), fontfamily="monospace")
            ax.set_ylabel("FOCUS %", color=T("SUBTEXT"), fontsize=8,
                          fontfamily="monospace")
            ax.set_ylim(0, 108)
            ax.tick_params(colors=T("SUBTEXT"), length=0)
            for sp in ax.spines.values(): sp.set_color(T("GRID"))
            ax.yaxis.grid(True, color=T("GRID"), linestyle="-",
                          linewidth=0.5, zorder=0)
            ax.set_axisbelow(True)

            # Value labels
            for xi, val in zip(x, vals):
                ax.annotate(f"{val:.0f}",
                            xy=(xi, val), xytext=(0, 9),
                            textcoords="offset points",
                            ha="center", fontsize=7.5,
                            color=T("TEXT"),
                            fontfamily="monospace")

            # Legend
            patches = [
                mpatches.Patch(color=T("GREEN"),  label="FOCUSED  ≥70"),
                mpatches.Patch(color=T("ORANGE"), label="MODERATE ≥50"),
                mpatches.Patch(color=T("RED"),    label="LOW      <50"),
            ]
            ax.legend(handles=patches, loc="lower right",
                      fontsize=7.5, framealpha=0,
                      labelcolor=T("SUBTEXT"))

            plt.tight_layout(pad=1.2)
            canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
            plt.close(fig)

        except Exception:
            ctk.CTkLabel(self.chart_frame,
                         text="RUN A FEW SESSIONS TO SEE TREND",
                         text_color=T("SUBTEXT"),
                         font=ctk.CTkFont(MONO, 12)).pack(expand=True)

    # ─────────────────────────────────────────
    # NOTES
    # ─────────────────────────────────────────
    def _add_note(self):
        text = self.note_entry.get().strip()
        if not text: return
        self.notes.append({"text": text, "done": False})
        save_notes_file(self.notes)
        self.note_entry.delete(0, "end")
        self._render_notes()

    def _toggle_note(self, idx):
        self.notes[idx]["done"] = not self.notes[idx]["done"]
        save_notes_file(self.notes)
        self._render_notes()

    def _delete_note(self, idx):
        self.notes.pop(idx)
        save_notes_file(self.notes)
        self._render_notes()

    def _render_notes(self):
        for w in self.notes_frame.winfo_children():
            w.destroy()
        if not self.notes:
            ctk.CTkLabel(self.notes_frame,
                         text="NO NOTES YET  ·  ADD ONE ABOVE",
                         text_color=T("SUBTEXT"),
                         font=ctk.CTkFont(MONO, 11)).pack(pady=20)
            return
        for i, note in enumerate(self.notes):
            row  = self._gcard(self.notes_frame)
            row.pack(fill="x", pady=3)
            inner = ctk.CTkFrame(row, fg_color="transparent")
            inner.pack(fill="x", padx=12, pady=8)
            done = note["done"]
            tc   = T("SUBTEXT") if done else T("TEXT")
            ct   = "✓" if done else "○"
            cc   = T("GREEN") if done else T("SUBTEXT")
            ctk.CTkButton(inner, text=ct, width=30, height=30,
                          font=ctk.CTkFont(MONO, 13),
                          corner_radius=15,
                          fg_color="transparent",
                          hover_color=T("BORDER"),
                          text_color=cc,
                          border_width=1,
                          border_color=T("BORDER"),
                          command=lambda idx=i: self._toggle_note(idx)).pack(side="left", padx=(0, 12))
            ctk.CTkLabel(inner, text=note["text"],
                         font=ctk.CTkFont(MONO, 11),
                         text_color=tc).pack(side="left", fill="x", expand=True)
            ctk.CTkButton(inner, text="×", width=28, height=28,
                          font=ctk.CTkFont(MONO, 15),
                          corner_radius=14,
                          fg_color="transparent",
                          hover_color=T("BORDER"),
                          text_color=T("SUBTEXT"),
                          command=lambda idx=i: self._delete_note(idx)).pack(side="right")


# ═══════════════════════════════════════════════
# APP
# ═══════════════════════════════════════════════
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("STUDY_PLANNER")
        self.geometry("1060x680")
        self.resizable(False, False)
        self.configure(fg_color=T("BG"))
        self.dashboard = None
        self.intro = IntroScreen(self, on_start=self._launch)
        self.intro.pack(fill="both", expand=True)

    def _launch(self, name, subject):
        self.intro.destroy()
        self.dashboard = Dashboard(self, name=name,
                                    subject=subject, app_ref=self)
        self.dashboard.pack(fill="both", expand=True)

    def toggle_theme(self):
        global _theme
        _theme = "light" if _theme == "dark" else "dark"
        ctk.set_appearance_mode(T("mode"))
        if self.dashboard:
            name    = self.dashboard.user_name
            subject = self.dashboard.subject
            self.dashboard.destroy()
            self.configure(fg_color=T("BG"))
            self.dashboard = Dashboard(self, name=name,
                                        subject=subject, app_ref=self)
            self.dashboard.pack(fill="both", expand=True)


if __name__ == "__main__":
    try:
        import scipy
    except ImportError:
        print("TIP: pip install scipy for smooth focus trend chart")
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    App().mainloop()
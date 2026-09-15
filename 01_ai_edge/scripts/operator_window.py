"""Desktop video, shared dashboard and authorized issue resolution."""
from datetime import datetime
from queue import Empty, Queue
import time
import tkinter as tk
from tkinter import ttk

from PIL import Image, ImageTk
from operator_client import OperatorClient, OperatorSync


class OperatorWindow:
    def __init__(self, backend_url):
        self.root = tk.Tk()
        self.root.title("CODYSSEY - CCTV, Alerts and Dashboard")
        width = min(1280, self.root.winfo_screenwidth() - 50)
        height = min(800, self.root.winfo_screenheight() - 90)
        self.root.geometry(f"{width}x{height}+20+20")
        self.root.minsize(min(1050, width), min(620, height))
        self.closed = False
        self.keys = Queue()
        self.authenticated = False
        self.busy = False
        self.selected_id = None
        self.issues = {}
        self.detail_record = None
        self.confirmed_id = None
        self.confirmed_status = "resolved"
        self.confirmed_from = "open"
        self.evidence_id = None
        self.page, self.total, self.version = 1, 0, 0
        self.login_window = None
        self.sync = OperatorSync(OperatorClient(backend_url))
        self._build()
        self.root.update_idletasks()
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.sync.start()
        self.refresh()

    def _build(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("TFrame", background="#101b29")
        style.configure("TLabel", background="#101b29", foreground="#e8f1f8", font=("Segoe UI", 10))
        style.configure("Title.TLabel", font=("Segoe UI", 18, "bold"), foreground="#8ee6dd")
        style.configure("Value.TLabel", font=("Segoe UI", 25, "bold"), foreground="#8ee6dd")
        style.configure("TButton", padding=7, font=("Segoe UI", 10))
        style.configure("TNotebook", background="#101b29", borderwidth=0)
        style.configure("TNotebook.Tab", padding=(20, 9), font=("Segoe UI", 11))
        style.configure("Treeview", rowheight=29, font=("Segoe UI", 9))
        self.root.configure(background="#101b29")
        outer = ttk.Frame(self.root, padding=16)
        outer.pack(fill="both", expand=True)
        header = ttk.Frame(outer)
        header.pack(fill="x", pady=(0, 12))
        ttk.Label(header, text="CODYSSEY | CCTV operations", style="Title.TLabel").pack(side="left")
        self.login_button = ttk.Button(header, text="Operator sign in", command=self.auth_action)
        self.login_button.pack(side="right")
        ttk.Button(header, text="Refresh", command=self.refresh).pack(side="right", padx=8)
        body = ttk.Frame(outer)
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=2)
        body.columnconfigure(1, weight=3)
        body.rowconfigure(0, weight=1)
        left = ttk.Frame(body, padding=(0, 0, 16, 0))
        left.grid(row=0, column=0, sticky="nsew")
        left.columnconfigure(0, weight=1)
        left.rowconfigure(1, weight=1)
        self.video_caption = tk.StringVar(value="Starting recorded video...")
        ttk.Label(left, textvariable=self.video_caption).grid(row=0, column=0, sticky="w", pady=(0, 8))
        self.video = tk.Label(left, background="#080e15")
        self.video.grid(row=1, column=0, sticky="nsew")
        self.location = tk.StringVar(value="Location: simulated route")
        self.delivery = tk.StringVar(value="Waiting for pothole detections")
        ttk.Label(left, textvariable=self.location, wraplength=410).grid(row=2, column=0, sticky="w", pady=(10, 3))
        ttk.Label(left, textvariable=self.delivery, wraplength=410).grid(row=3, column=0, sticky="w", pady=(3, 8))
        controls = ttk.Frame(left)
        controls.grid(row=4, column=0, sticky="ew")
        self.pause_button = ttk.Button(controls, text="Pause video", command=lambda: self.keys.put(ord(" ")))
        self.pause_button.pack(side="left")
        ttk.Button(controls, text="Close player", command=self.close).pack(side="right")

        self.notebook = ttk.Notebook(body)
        self.notebook.grid(row=0, column=1, sticky="nsew")
        dashboard = ttk.Frame(self.notebook, padding=16)
        alerts = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(dashboard, text="Dashboard")
        self.notebook.add(alerts, text="Alerts")
        self.notebook.select(alerts)
        self.alerts_tab = alerts
        alerts.columnconfigure(0, weight=1)
        alerts.rowconfigure(1, weight=2)
        alerts.rowconfigure(4, weight=1)
        self.counts = {}
        for index, (key, title) in enumerate((("total", "Total issues"), ("open", "Open issues"), ("resolved", "Resolved issues"), ("buses", "Active buses"))):
            card = ttk.Frame(dashboard, padding=10)
            card.grid(row=index // 2, column=index % 2, sticky="nsew", padx=4, pady=4)
            ttk.Label(card, text=title).pack(anchor="w")
            self.counts[key] = tk.StringVar(value="—")
            ttk.Label(card, textvariable=self.counts[key], style="Value.TLabel").pack(anchor="w", pady=6)
        dashboard.columnconfigure(0, weight=1)
        dashboard.columnconfigure(1, weight=1)
        ttk.Label(dashboard, text="Where your alerts go", style="Title.TLabel").grid(row=2, column=0, columnspan=2, sticky="w", pady=(12, 8))
        ttk.Label(dashboard, text="Video detections → backend → shared Alerts and Dashboard.\n\nNearby observations are grouped into one issue. Open the Alerts tab, select an issue and mark it resolved. The Python and web dashboards use the same saved status.\n\nThe bundled video uses simulated GPS. Physical damage severity is unassessed.", wraplength=490, justify="left").grid(row=3, column=0, columnspan=2, sticky="nw")
        ttk.Button(dashboard, text="Review and resolve alerts", command=lambda: self.notebook.select(alerts)).grid(row=4, column=0, columnspan=2, sticky="w", pady=12)

        filters = ttk.Frame(alerts)
        filters.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ttk.Label(filters, text="Status").pack(side="left", padx=(0, 8))
        self.filter = tk.StringVar(value="All")
        combo = ttk.Combobox(filters, textvariable=self.filter, values=("All", "Open", "Resolved", "Dismissed"), state="readonly", width=12)
        combo.pack(side="left")
        combo.bind("<<ComboboxSelected>>", lambda _: self.change_filter())
        self.tree = ttk.Treeview(alerts, columns=("issue", "status", "priority", "reports"), show="headings", height=5, selectmode="browse")
        for key, title, width in (("issue", "Issue", 145), ("status", "Status", 85), ("priority", "Priority", 85), ("reports", "Reports", 65)):
            self.tree.heading(key, text=title)
            self.tree.column(key, width=width, minwidth=60, stretch=True)
        self.tree.grid(row=1, column=0, sticky="nsew")
        self.tree.bind("<<TreeviewSelect>>", self.select_issue)
        pages = ttk.Frame(alerts)
        pages.grid(row=2, column=0, sticky="ew", pady=5)
        self.page_label = tk.StringVar(value="Loading issues...")
        ttk.Label(pages, textvariable=self.page_label).pack(side="left")
        self.next_button = ttk.Button(pages, text="Next", command=lambda: self.change_page(1))
        self.next_button.pack(side="right")
        self.previous_button = ttk.Button(pages, text="Previous", command=lambda: self.change_page(-1))
        self.previous_button.pack(side="right", padx=5)
        self.details = tk.StringVar(value="Select an issue to view its location and observations.")
        ttk.Label(alerts, textvariable=self.details, wraplength=520, justify="left").grid(row=3, column=0, sticky="w", pady=5)
        evidence_tabs = ttk.Notebook(alerts)
        evidence_tabs.grid(row=4, column=0, sticky="nsew", pady=5)
        self.observations = ttk.Treeview(evidence_tabs, columns=("bus", "confidence", "time"), show="headings", height=3)
        for key, title, width in (("bus", "Bus", 100), ("confidence", "Confidence", 90), ("time", "Detection time (local)", 220)):
            self.observations.heading(key, text=title)
            self.observations.column(key, width=width, minwidth=70)
        evidence_tabs.add(self.observations, text="Observations")
        self.history = ttk.Treeview(evidence_tabs, columns=("time", "status", "note"), show="headings", height=3)
        for key, title, width in (("time", "Changed (local)", 135), ("status", "Status change", 150), ("note", "Operator note", 240)):
            self.history.heading(key, text=title)
            self.history.column(key, width=width, minwidth=70)
        evidence_tabs.add(self.history, text="Status history")
        self.evidence_label = ttk.Label(evidence_tabs, text="Select an observation with saved evidence.", anchor="center")
        evidence_tabs.add(self.evidence_label, text="Saved evidence")
        self.observations.bind("<<TreeviewSelect>>", lambda _: self.select_evidence())
        action_row = ttk.Frame(alerts)
        action_row.grid(row=5, column=0, sticky="ew", pady=5)
        self.review_action = tk.StringVar(value="Resolve")
        action = ttk.Combobox(action_row, textvariable=self.review_action, values=("Resolve", "False detection", "Reopen"), state="readonly", width=15)
        action.pack(side="left", padx=(0, 8))
        action.bind("<<ComboboxSelected>>", lambda _: self._buttons())
        self.resolve_button = ttk.Button(action_row, text="Mark selected issue resolved", command=self.request_resolution, state="disabled")
        self.resolve_button.pack(side="left")
        self.confirm_frame = ttk.Frame(alerts)
        self.confirm_label = tk.StringVar()
        ttk.Label(self.confirm_frame, textvariable=self.confirm_label, wraplength=500).pack(anchor="w")
        note_row = ttk.Frame(self.confirm_frame)
        note_row.pack(fill="x", pady=3)
        ttk.Label(note_row, text="Note / reason: ").pack(side="left")
        self.resolution_note = tk.StringVar()
        ttk.Entry(note_row, textvariable=self.resolution_note, validate="key", validatecommand=(self.root.register(lambda value: len(value) <= 500), "%P")).pack(side="left", fill="x", expand=True)
        self.confirm_button = ttk.Button(self.confirm_frame, text="Confirm resolution", command=self.confirm_resolution)
        self.confirm_button.pack(side="left", pady=7)
        ttk.Button(self.confirm_frame, text="Cancel", command=self.cancel_resolution).pack(side="left", padx=8)
        self.connection = tk.StringVar(value="Connecting to the shared backend...")
        self.message = tk.StringVar(value="")
        ttk.Label(outer, textvariable=self.connection, wraplength=1150).pack(anchor="w", pady=(12, 3))
        ttk.Label(outer, textvariable=self.message, wraplength=1150).pack(anchor="w")

    def refresh(self):
        self.version += 1
        self.sync.submit("refresh", status="" if self.filter.get() == "All" else self.filter.get().lower(), page=self.page, version=self.version)

    def change_filter(self):
        self.page = 1
        self.refresh()

    def change_page(self, delta):
        self.page = max(1, self.page + delta)
        self.refresh()

    def select_issue(self, _=None):
        selection = self.tree.selection()
        issue_id = selection[0] if selection else None
        if issue_id != self.selected_id:
            self.cancel_resolution()
            self.selected_id = issue_id
            self.detail_record = None
            self.observations.delete(*self.observations.get_children())
            self.history.delete(*self.history.get_children())
            self.evidence_id = None
            self.evidence_label.configure(image="", text="No saved evidence selected.")
        issue = self.issues.get(issue_id)
        if issue:
            self.details.set(f"{issue_id}\nStatus: {issue['status']} | Priority: {issue['priority']} | Reports: {issue['report_count']}\nLocation: {issue['latitude']:.6f}, {issue['longitude']:.6f} ({issue['location_source']})")
            if not self.detail_record:
                self.sync.submit("details", issue_id=issue_id)
        else:
            self.details.set("Select an issue to view its location and observations.")
        self._buttons()

    def _buttons(self):
        issue = self.issues.get(self.selected_id)
        target = {"Resolve": "resolved", "False detection": "dismissed", "Reopen": "open"}[self.review_action.get()]
        self.resolve_button.configure(state="normal" if issue and issue["status"] != target and not self.busy else "disabled",
                                      text="Saving..." if self.busy else self.review_action.get() + " selected issue" if self.authenticated else "Sign in to review selected issue")
        self.login_button.configure(text="Sign out" if self.authenticated else "Operator sign in")
        self.previous_button.configure(state="normal" if self.page > 1 else "disabled")
        self.next_button.configure(state="normal" if self.page * 10 < self.total else "disabled")

    def auth_action(self):
        if self.authenticated:
            self.sync.submit("logout")
            return
        if self.login_window and self.login_window.winfo_exists():
            self.login_window.lift()
            return
        dialog = self.login_window = tk.Toplevel(self.root)
        dialog.title("Operator sign in")
        dialog.transient(self.root)
        form = ttk.Frame(dialog, padding=20)
        form.pack(fill="both", expand=True)
        ttk.Label(form, text="Use your existing operator password.\nIt is stored in the backend's operator-password.txt.", wraplength=360).pack(anchor="w", pady=(0, 12))
        entry = ttk.Entry(form, show="*", width=36)
        entry.pack(fill="x")
        entry.focus_set()

        def submit():
            password = entry.get()
            if not password:
                return
            self.sync.submit("login", password=password)
            entry.delete(0, "end")
            dialog.destroy()
            self.login_window = None
            self.message.set("Signing in...")

        ttk.Button(form, text="Sign in", command=submit).pack(anchor="e", pady=(12, 0))
        entry.bind("<Return>", lambda _: submit())

    def request_resolution(self):
        if not self.authenticated:
            self.auth_action()
            return
        issue = self.issues.get(self.selected_id)
        target = {"Resolve": "resolved", "False detection": "dismissed", "Reopen": "open"}[self.review_action.get()]
        if not issue or issue["status"] == target or self.busy:
            return
        self.confirmed_id = self.selected_id
        self.confirmed_status, self.confirmed_from = target, issue["status"]
        self.confirm_label.set(f"{self.review_action.get()}: {self.selected_id[-10:]}? Reports are retained." + (" A reason is required." if target == "dismissed" else ""))
        self.confirm_button.configure(text="Confirm " + self.review_action.get().lower())
        self.confirm_frame.grid(row=6, column=0, sticky="ew")

    def cancel_resolution(self):
        self.confirmed_id = None
        self.confirm_frame.grid_remove()
        self.resolution_note.set("")

    def confirm_resolution(self):
        if self.confirmed_id and not self.busy:
            issue_id = self.confirmed_id
            note = self.resolution_note.get().strip()
            if self.confirmed_status == "dismissed" and not note:
                self.message.set("Enter a reason before marking a false detection.")
                return
            self.cancel_resolution()
            self.busy = True
            self.sync.submit("resolve", issue_id=issue_id, note=note, status=self.confirmed_status, expected_status=self.confirmed_from)
            self.message.set("Saving the review decision to the shared backend...")
            self._buttons()

    def _messages(self):
        while True:
            try:
                event = self.sync.messages.get_nowait()
            except Empty:
                break
            kind = event["kind"]
            if kind == "snapshot":
                if event["view"]["version"] != self.version:
                    continue
                data = event["data"]
                statistics = data["statistics"]
                values = {"total": statistics["total_issues"], "open": statistics.get("open_issues", statistics["total_issues"] - statistics["resolved_issues"] - statistics.get("dismissed_issues", 0)),
                          "resolved": statistics["resolved_issues"], "buses": statistics["active_buses"]}
                for key, value in values.items():
                    self.counts[key].set(str(value))
                self.authenticated = data["authenticated"]
                records = data["alerts"]
                self.total = records["total"]
                self.issues = {issue["issue_id"]: issue for issue in records["items"]}
                for item in self.tree.get_children():
                    if item not in self.issues:
                        self.tree.delete(item)
                for position, (issue_id, issue) in enumerate(self.issues.items()):
                    values = (issue_id[-10:].upper(), issue["status"], issue["priority"], issue["report_count"])
                    if self.tree.exists(issue_id):
                        self.tree.item(issue_id, values=values)
                        self.tree.move(issue_id, "", position)
                    else:
                        self.tree.insert("", position, iid=issue_id, values=values)
                self.page_label.set(f"{self.total} issues | Page {self.page} of {max(1, (self.total + 9) // 10)}")
                if not self.issues and self.page > 1:
                    self.page = max(1, (self.total + 9) // 10)
                    self.refresh()
                if not self.selected_id and self.issues:
                    self.tree.selection_set(next(iter(self.issues)))
                self.select_issue()
                if self.selected_id:
                    self.sync.submit("details", issue_id=self.selected_id)
                self.connection.set("Connected to the shared backend | Updates every 2 seconds | Resolution is shared with web Alerts and Dashboard.")
            elif kind == "details" and event["issue_id"] == self.selected_id:
                self.detail_record = event["data"]
                selected_report = self.observations.selection()
                self.observations.delete(*self.observations.get_children())
                for report in self.detail_record["observations"]:
                    stamp = datetime.fromisoformat(report["timestamp"].replace("Z", "+00:00")).astimezone().strftime("%d %b %H:%M:%S")
                    self.observations.insert("", "end", iid=report["event_id"], values=(report["bus_id"], f"{report['confidence']:.1%}", stamp + (" | image" if report.get("evidence") else "")))
                if selected_report and self.observations.exists(selected_report[0]):
                    self.observations.selection_set(selected_report[0])
                elif self.detail_record["observations"]:
                    first = next((report for report in self.detail_record["observations"] if report.get("evidence")), self.detail_record["observations"][0])
                    self.observations.selection_set(first["event_id"])
                self.history.delete(*self.history.get_children())
                for activity in self.detail_record.get("activity", []):
                    stamp = datetime.fromisoformat(activity["timestamp"].replace("Z", "+00:00")).astimezone().strftime("%d %b %H:%M:%S")
                    self.history.insert("", "end", values=(stamp, f"{activity['previous_status']} → {activity['status']}", activity["note"] or "No note"))
            elif kind in ("login", "logout"):
                self.authenticated = event["data"]["authenticated"]
                self.message.set("Signed in. Select an open issue and choose Mark resolved." if self.authenticated else "Signed out.")
            elif kind == "resolve":
                self.busy = False
                issue_id = event["issue_id"]
                if issue_id in self.issues:
                    self.issues[issue_id] = event["data"]
                    self.tree.set(issue_id, "status", event["data"]["status"])
                self.message.set(f"Issue {issue_id[-10:]} saved as {event['data']['status']}. The web dashboard will show the same status.")
                self.select_issue()
            elif kind == "evidence" and event["event_id"] == self.evidence_id:
                from io import BytesIO
                try:
                    with Image.open(BytesIO(event["data"])) as image:
                        image.thumbnail((380, 135))
                        self.evidence_photo = ImageTk.PhotoImage(image)
                    self.evidence_label.configure(image=self.evidence_photo, text="")
                except (OSError, ValueError):
                    self.evidence_label.configure(image="", text="Could not display this evidence image.")
            elif kind == "action_error":
                if event["action"] == "evidence":
                    self.evidence_id = None
                    self.evidence_label.configure(image="", text="Image unavailable; retrying with the next refresh.")
                if event["action"] == "resolve":
                    self.busy = False
                if event.get("status") == 401:
                    self.authenticated = False
                self.message.set(event["error"])
            elif kind == "poll_error":
                self.connection.set("Updates interrupted; showing last received data. " + event["error"])
            self._buttons()

    def select_evidence(self):
        selected = self.observations.selection()
        if not selected or not self.detail_record:
            return
        report = next((item for item in self.detail_record["observations"] if item["event_id"] == selected[0]), None)
        if not report or report["event_id"] == self.evidence_id:
            return
        self.evidence_id = report["event_id"]
        self.evidence_label.configure(image="", text="Loading saved crop..." if report.get("evidence") else "No image saved for this observation.")
        if report.get("evidence"):
            self.sync.submit("evidence", event_id=report["event_id"])

    def show(self, frame, detections, location, event_ids, states, latest_alert, video_time, duration, pass_number, confidence, offline, performance=None):
        import cv2
        annotated = frame.copy()
        for detection in detections:
            x1, y1, x2, y2 = detection["bbox"]
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 180, 255), 2)
            cv2.putText(annotated, f"Pothole {detection['confidence']:.0%}", (x1, max(20, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, .5, (0, 180, 255), 1)
        image = Image.fromarray(cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB))
        image.thumbnail((max(1, self.video.winfo_width()), max(1, self.video.winfo_height())))
        self.photo = ImageTk.PhotoImage(image)
        self.video.configure(image=self.photo)
        mode = "Recording: sending alerts" if pass_number == 1 else "Replay: first-pass alerts preserved"
        self.video_caption.set(f"{mode} | {video_time:.1f}s" + (f" / {duration:.1f}s" if duration else ""))
        metrics_text = f" | Inference {performance['mean_inference_ms']} ms | {performance['recent_frame_rate']} frames/s" if performance else ""
        self.location.set(f"SIMULATED GPS: {location['latitude']:.6f}, {location['longitude']:.6f}\nThreshold: {confidence:.0%}{metrics_text}")
        sent = sum(state == "sent" for state in states.values())
        pending = sum(states.get(event_id, "pending") == "pending" for event_id in event_ids)
        status = f"This run: {len(event_ids)} confirmed | {sent} sent | {pending} queued"
        if latest_alert:
            status += f"\nLatest: {states.get(latest_alert['event_id'], 'pending').upper()} | GPS {latest_alert['latitude']:.6f}, {latest_alert['longitude']:.6f}"
        self.delivery.set(status)

    def set_paused(self, paused):
        self.pause_button.configure(text="Resume video" if paused else "Pause video")

    def finish(self):
        self.video_caption.set("Recording finished | Alerts and resolution remain available")
        self.pause_button.configure(text="Recording finished", state="disabled")

    def wait_key(self, delay):
        deadline = time.monotonic() + delay / 1000
        while not self.closed:
            self._messages()
            try:
                self.root.update_idletasks()
                self.root.update()
            except tk.TclError:
                self.closed = True
                break
            try:
                return self.keys.get_nowait()
            except Empty:
                pass
            if time.monotonic() >= deadline:
                return -1
            time.sleep(min(.01, max(0, deadline - time.monotonic())))
        return ord("q")

    def close(self):
        if not self.closed:
            self.closed = True
            self.root.destroy()

    def stop(self):
        self.close()
        self.sync.stop()

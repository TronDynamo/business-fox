#!/usr/bin/env python3
"""Generate the Business Fox printable products (US Letter PDFs)."""
import os, sys
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, white

W, H = letter
M = 0.6 * 72                      # margin
NAVY, ORANGE, GOLD = HexColor("#121630"), HexColor("#fc812b"), HexColor("#d4af37")
INK, MUTED, LINE, TINT = HexColor("#121630"), HexColor("#5b6080"), HexColor("#c9c3b6"), HexColor("#f7f4ee")
FOX = os.environ.get("FOX_IMG", "img/fox.png")
OUT = os.environ.get("OUT_DIR", "build/products")


class Doc:
    def __init__(self, pid, title, subtitle):
        self.pid, self.title, self.subtitle = pid, title, subtitle
        os.makedirs(OUT, exist_ok=True)
        self.path = os.path.join(OUT, f"{pid}.pdf")
        self.c = canvas.Canvas(self.path, pagesize=letter)
        self.c.setTitle(title); self.c.setAuthor("Business Fox"); self.c.setSubject(subtitle)
        self.page = 0

    # -------------------------------------------------- chrome
    def _header(self, heading, sub=None):
        c = self.c
        self.page += 1
        c.setFillColor(NAVY); c.rect(0, H - 62, W, 62, fill=1, stroke=0)
        c.setFillColor(ORANGE); c.rect(0, H - 66, W, 4, fill=1, stroke=0)
        c.setFillColor(white); c.setFont("Helvetica-Bold", 17); c.drawString(M, H - 38, heading)
        c.setFillColor(GOLD); c.setFont("Helvetica", 8.5)
        c.drawRightString(W - M, H - 38, self.title.upper()[:70])
        y = H - 90
        if sub:
            c.setFillColor(MUTED); c.setFont("Helvetica", 9.5); c.drawString(M, y, sub); y -= 18
        c.setFillColor(MUTED); c.setFont("Helvetica", 7.5)
        c.drawString(M, 0.38 * 72, f"Business Fox  |  {self.title}  |  Personal-use licence")
        c.drawRightString(W - M, 0.38 * 72, f"Page {self.page}")
        return y

    def _end(self):
        self.c.showPage()

    def _fields(self, y, labels, cols=2, gap=22):
        c = self.c; cw = (W - 2 * M) / cols
        for i, lab in enumerate(labels):
            x = M + (i % cols) * cw
            if i and i % cols == 0: y -= gap
            c.setFillColor(INK); c.setFont("Helvetica-Bold", 8.5); c.drawString(x, y, lab)
            tw = c.stringWidth(lab, "Helvetica-Bold", 8.5) + 6
            c.setStrokeColor(LINE); c.setLineWidth(0.7); c.line(x + tw, y - 2, x + cw - 12, y - 2)
        return y - gap - 4

    # -------------------------------------------------- page types
    def cover(self, steps):
        c = self.c; self.page += 1
        c.setFillColor(NAVY); c.rect(0, 0, W, H, fill=1, stroke=0)
        c.setStrokeColor(GOLD); c.setLineWidth(5); c.rect(18, 18, W - 36, H - 36, fill=0, stroke=1)
        c.setLineWidth(1.2); c.rect(30, 30, W - 60, H - 60, fill=0, stroke=1)
        try:
            c.drawImage(FOX, W - M - 120, 70, width=120, height=260, mask="auto", preserveAspectRatio=True)
        except Exception:
            pass
        c.setFillColor(ORANGE); c.setFont("Helvetica-Bold", 11); c.drawString(M + 10, H - 120, "BUSINESS FOX PRINTABLES")
        c.setFillColor(HexColor("#ffd75a")); c.setFont("Helvetica-Bold", 30)
        words, line, y = self.title.split(), "", H - 165
        for w in words:
            if c.stringWidth(line + " " + w, "Helvetica-Bold", 30) > W - 2 * M - 30:
                c.drawString(M + 10, y, line.strip()); y -= 38; line = w
            else:
                line += " " + w
        c.drawString(M + 10, y, line.strip()); y -= 30
        c.setFillColor(HexColor("#8f9bd0")); c.setFont("Helvetica", 12.5); c.drawString(M + 10, y, self.subtitle); y -= 50
        c.setFillColor(white); c.setFont("Helvetica-Bold", 12); c.drawString(M + 10, y, "How to use this pack"); y -= 22
        c.setFont("Helvetica", 10.5)
        for i, s in enumerate(steps, 1):
            c.setFillColor(ORANGE); c.drawString(M + 10, y, f"{i}.")
            c.setFillColor(white); c.drawString(M + 28, y, s); y -= 19
        c.setFillColor(HexColor("#8f9bd0")); c.setFont("Helvetica", 8)
        c.drawString(M + 10, 52, "US Letter. Print at home as often as you like. Personal-use licence. Made with AI tools and checked before delivery.")
        self._end()

    def table(self, heading, cols, rows=18, sub=None, fields=None, row_h=None, check_first=False):
        c = self.c
        y = self._header(heading, sub)
        if fields: y = self._fields(y - 4, fields)
        total = sum(w for _, w in cols); tw = W - 2 * M
        bottom = 0.7 * 72
        rh = row_h or min(26, (y - 22 - bottom) / rows)
        rows = int((y - 22 - bottom) // rh) if row_h is None else rows
        rows = max(1, rows)
        c.setFillColor(NAVY); c.rect(M, y - 20, tw, 20, fill=1, stroke=0)
        x = M; c.setFillColor(white); c.setFont("Helvetica-Bold", 8)
        xs = []
        for name, w in cols:
            cw = tw * w / total; xs.append((x, cw))
            c.drawString(x + 4, y - 13.5, name[: int(cw / 4.4)]); x += cw
        y -= 20
        for r in range(rows):
            if r % 2: c.setFillColor(TINT); c.rect(M, y - rh, tw, rh, fill=1, stroke=0)
            if check_first:
                c.setStrokeColor(MUTED); c.setLineWidth(0.8); c.rect(xs[0][0] + 5, y - rh / 2 - 4.5, 9, 9)
            y -= rh
        c.setStrokeColor(LINE); c.setLineWidth(0.6)
        top = y + rh * rows
        for r in range(rows + 1): c.line(M, top - r * rh, M + tw, top - r * rh)
        for x, cw in xs + [(M + tw, 0)]: c.line(x, top + 20, x, y)
        self._end()

    def checklist(self, heading, sections, sub=None, fields=None):
        c = self.c
        y = self._header(heading, sub)
        if fields: y = self._fields(y - 4, fields)
        for title, items in sections:
            if y < 120: break
            c.setFillColor(ORANGE); c.rect(M, y - 3, 4, 14, fill=1, stroke=0)
            c.setFillColor(INK); c.setFont("Helvetica-Bold", 11); c.drawString(M + 10, y, title); y -= 20
            c.setFont("Helvetica", 9.5)
            for it in items:
                c.setStrokeColor(MUTED); c.setLineWidth(0.8); c.rect(M + 10, y - 2, 10, 10)
                c.setFillColor(INK); c.drawString(M + 28, y, it)
                c.setStrokeColor(LINE); c.setLineWidth(0.5); c.line(W - M - 150, y - 2, W - M, y - 2)
                y -= 19
            y -= 8
        c.setFillColor(MUTED); c.setFont("Helvetica", 7.5); c.drawRightString(W - M, y + 6 if y > 80 else 80, "Notes / initials")
        self._lines(y - 6, label="Notes")
        self._end()

    def _lines(self, y, label=None, step=20):
        c = self.c
        if label and y > 90:
            c.setFillColor(INK); c.setFont("Helvetica-Bold", 10); c.drawString(M, y, label); y -= 16
        c.setStrokeColor(LINE); c.setLineWidth(0.6)
        while y > 0.75 * 72:
            c.line(M, y, W - M, y); y -= step

    def form(self, heading, blocks, sub=None):
        """blocks: list of ('fields', [labels]) | ('box', title, height) | ('lines', title, n) | ('table', cols, rows)"""
        c = self.c
        y = self._header(heading, sub)
        for b in blocks:
            if b[0] == "fields":
                y = self._fields(y - 4, b[1], cols=b[2] if len(b) > 2 else 2)
            elif b[0] == "box":
                c.setFillColor(INK); c.setFont("Helvetica-Bold", 10); c.drawString(M, y, b[1]); y -= 8
                c.setStrokeColor(LINE); c.setLineWidth(0.8); c.roundRect(M, y - b[2], W - 2 * M, b[2], 6); y -= b[2] + 20
            elif b[0] == "lines":
                c.setFillColor(INK); c.setFont("Helvetica-Bold", 10); c.drawString(M, y, b[1]); y -= 20
                c.setStrokeColor(LINE); c.setLineWidth(0.6)
                for _ in range(b[2]): c.line(M, y, W - M, y); y -= 20
                y -= 4
            elif b[0] == "table":
                cols, rows = b[1], b[2]; total = sum(w for _, w in cols); tw = W - 2 * M; rh = 20
                c.setFillColor(NAVY); c.rect(M, y - 18, tw, 18, fill=1, stroke=0)
                x = M; c.setFillColor(white); c.setFont("Helvetica-Bold", 8); xs = []
                for n, w in cols:
                    cw = tw * w / total; xs.append(x); c.drawString(x + 4, y - 12.5, n); x += cw
                top = y - 18
                c.setStrokeColor(LINE); c.setLineWidth(0.6)
                for r in range(rows + 1): c.line(M, top - r * rh, M + tw, top - r * rh)
                for x in xs + [M + tw]: c.line(x, y, x, top - rows * rh)
                y = top - rows * rh - 22
            elif b[0] == "totals":
                for lab in b[1]:
                    c.setFillColor(INK); c.setFont("Helvetica-Bold", 9); c.drawRightString(W - M - 130, y, lab)
                    c.setStrokeColor(LINE); c.line(W - M - 120, y - 2, W - M, y - 2); y -= 20
                y -= 6
            elif b[0] == "sign":
                y = self._fields(y - 6, b[1], cols=2, gap=30)
        self._end()

    def grid(self, heading, row_label, rows, days=31, sub=None, extra_cols=None):
        """habit-style tracker: rows x day columns"""
        c = self.c
        y = self._header(heading, sub)
        y = self._fields(y - 4, ["Month:", "Focus:"])
        lab_w = 150; extra = extra_cols or []; ex_w = 34 * len(extra)
        dw = (W - 2 * M - lab_w - ex_w) / days; rh = min(24, (y - 30 - 0.75 * 72) / rows)
        c.setFillColor(NAVY); c.rect(M, y - 18, W - 2 * M, 18, fill=1, stroke=0)
        c.setFillColor(white); c.setFont("Helvetica-Bold", 8); c.drawString(M + 4, y - 12.5, row_label)
        c.setFont("Helvetica-Bold", 6.5)
        for d in range(days): c.drawCentredString(M + lab_w + dw * d + dw / 2, y - 12.5, str(d + 1))
        for i, e in enumerate(extra): c.drawCentredString(W - M - ex_w + 34 * i + 17, y - 12.5, e)
        y -= 18; top = y
        for r in range(rows):
            if r % 2: c.setFillColor(TINT); c.rect(M, y - rh, W - 2 * M, rh, fill=1, stroke=0)
            y -= rh
        c.setStrokeColor(LINE); c.setLineWidth(0.5)
        for r in range(rows + 1): c.line(M, top - r * rh, W - M, top - r * rh)
        c.line(M, top + 18, M, y); c.line(M + lab_w, top + 18, M + lab_w, y)
        for d in range(1, days + 1): c.line(M + lab_w + dw * d, top, M + lab_w + dw * d, y)
        for i in range(len(extra)): c.line(W - M - ex_w + 34 * i, top, W - M - ex_w + 34 * i, y)
        c.line(W - M, top + 18, W - M, y)
        self._end()

    def week(self, heading, sub=None, rows=("Jobs / appointments", "Client calls", "Crew / staff", "Priorities")):
        c = self.c
        y = self._header(heading, sub)
        y = self._fields(y - 4, ["Week of:", "Top goal this week:"])
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        lab = 92; dw = (W - 2 * M - lab) / 7; rh = (y - 22 - 0.75 * 72) / len(rows)
        c.setFillColor(NAVY); c.rect(M, y - 18, W - 2 * M, 18, fill=1, stroke=0)
        c.setFillColor(white); c.setFont("Helvetica-Bold", 8.5)
        for i, d in enumerate(days): c.drawCentredString(M + lab + dw * i + dw / 2, y - 12.5, d)
        y -= 18; top = y
        for i, r in enumerate(rows):
            c.setFillColor(TINT); c.rect(M, y - rh, lab, rh, fill=1, stroke=0)
            c.setFillColor(INK); c.setFont("Helvetica-Bold", 8)
            for j, part in enumerate(r.split(" / ")): c.drawString(M + 5, y - 14 - j * 11, part + (" /" if j < len(r.split(" / ")) - 1 else ""))
            y -= rh
        c.setStrokeColor(LINE); c.setLineWidth(0.6)
        for i in range(len(rows) + 1): c.line(M, top - i * rh, W - M, top - i * rh)
        c.line(M, top + 18, M, y)
        for i in range(8): c.line(M + lab + dw * i, top + (18 if i in (0, 7) else 0), M + lab + dw * i, y)
        self._end()

    def notes(self, heading="Notes", sub=None):
        y = self._header(heading, sub); self._lines(y - 6); self._end()

    def save(self):
        self.c.save()
        return self.path


# ======================================================== product specs
def build_all():
    made = []

    d = Doc("BF-PRI-3D4FB4", "Daily Habit Tracker", "See your streaks. Spot the missed days.")
    d.cover(["Pick up to 12 habits you want to build.", "Write them on the monthly tracker.", "Check one box each day you do the habit.",
             "Review your streaks every Sunday.", "Print a fresh copy each month."])
    d.checklist("Choose your habits", [("Habits I want to build", ["Habit 1", "Habit 2", "Habit 3", "Habit 4", "Habit 5", "Habit 6"]),
                                       ("Why each one matters to me", ["Health", "Work", "Money", "Relationships", "Learning"])])
    d.grid("Monthly habit tracker", "Habit", 12, extra_cols=["Total"])
    d.grid("Monthly habit tracker", "Habit", 12, extra_cols=["Total"])
    d.table("Weekly habit check-in", [("Week", 1), ("Wins", 3), ("Missed days and why", 3), ("Adjustment for next week", 3)], sub="Five minutes every Sunday.")
    d.table("Streak log", [("Habit", 3), ("Start date", 1.4), ("Longest streak", 1.4), ("Current streak", 1.4), ("Reward", 2)])
    d.notes("Reflection notes", "What made this month easier or harder?")
    made.append(d.save())

    d = Doc("BF-PRI-B91493", "Simple Morning Routine Tracker", "Write it down once. Tick it off daily.")
    d.cover(["Design your ideal morning on the planning page.", "Keep it to 5-8 steps.", "Tick each step on the 31-day tracker.",
             "Note how the day started.", "Adjust the routine at month end."])
    d.form("Design your ideal morning", [("fields", ["Wake-up time:", "Out the door / start work:", "Hours of sleep goal:", "Phone-free until:"]),
                                         ("table", [("#", 0.4), ("Step", 4), ("Minutes", 1), ("Why it matters", 3)], 8),
                                         ("lines", "My morning in one sentence", 2)])
    d.grid("31-day morning tracker", "Routine step", 10, extra_cols=["Done"])
    d.grid("31-day morning tracker", "Routine step", 10, extra_cols=["Done"])
    d.table("How did the day start?", [("Date", 1.2), ("Wake time", 1.1), ("Energy 1-5", 1.1), ("Mood 1-5", 1.1), ("One note", 4)])
    d.table("Weekly review", [("Week", 1), ("Days completed", 1.4), ("What helped", 3), ("What got in the way", 3)], rows=12)
    d.checklist("Evening prep for a better morning", [("Night before", ["Clothes laid out", "Bag packed", "Tomorrow's top 3 written", "Alarm set", "Screens off 30 min before bed"]),
                                                     ("Kitchen", ["Coffee / breakfast ready", "Water bottle filled", "Lunch packed"])])
    d.notes("Notes and adjustments")
    made.append(d.save())

    d = Doc("BF-PRI-866B87", "Weekly Email Newsletter Planner", "Pick it. Outline it. Send it. Track it.")
    d.cover(["Brainstorm topics on the idea bank.", "Plan each issue on a weekly planner page.", "Use the pre-send checklist.",
             "Log every send and its results.", "Reuse winners on the 12-week calendar."])
    d.table("Topic idea bank", [("Idea", 4), ("Customer question it answers", 3.5), ("Offer / CTA", 2), ("Used", 0.7)])
    d.table("12-week newsletter calendar", [("Week", 0.8), ("Send date", 1.2), ("Topic", 3.5), ("Offer / call to action", 3), ("Status", 1)], rows=12, row_h=34)
    d.form("Weekly issue planner", [("fields", ["Issue #:", "Send date:", "Subject line:", "Preview text:"]),
                                     ("box", "Opening (1-2 sentences)", 60), ("box", "Main story / tip", 140), ("box", "Offer or call to action", 50),
                                     ("fields", ["CTA link:", "P.S. line:"])])
    d.form("Weekly issue planner", [("fields", ["Issue #:", "Send date:", "Subject line:", "Preview text:"]),
                                     ("box", "Opening (1-2 sentences)", 60), ("box", "Main story / tip", 140), ("box", "Offer or call to action", 50),
                                     ("fields", ["CTA link:", "P.S. line:"])])
    d.checklist("Pre-send checklist", [("Content", ["Subject line under 50 characters", "One clear main idea", "One call to action", "Links tested", "Images have alt text"]),
                                       ("Before you hit send", ["Sent a test to yourself", "Read it on your phone", "Correct list / segment selected", "Unsubscribe link present", "Scheduled for the best time"])])
    d.table("Send and results log", [("Date", 1), ("Subject", 3.5), ("Sent to", 1), ("Open %", 0.9), ("Click %", 0.9), ("Replies / sales", 1.5)])
    made.append(d.save())

    d = Doc("BF-PRI-C9CED6", "Local Contractor Client Project Tracker", "Every job from first call to final sign-off.")
    d.cover(["Log every inquiry on the lead page.", "Open a project sheet when a job is booked.", "Track milestones and change orders.",
             "Record follow-ups so nothing slips.", "Close out with the sign-off page."])
    d.table("Inquiry and lead log", [("Date", 1), ("Client", 2), ("Phone / email", 2.2), ("Job type", 2), ("Source", 1.2), ("Next step", 2)])
    d.table("Active projects at a glance", [("Project", 2.4), ("Client", 2), ("Start", 1), ("Due", 1), ("Value $", 1.1), ("Status", 1.4)])
    d.form("Project sheet", [("fields", ["Client:", "Phone:", "Job address:", "Email:", "Start date:", "Target finish:", "Quoted price:", "Deposit received:"]),
                              ("box", "Scope of work", 120), ("table", [("Milestone", 4), ("Target date", 1.5), ("Done", 1), ("Notes", 3)], 6)])
    d.form("Project sheet", [("fields", ["Client:", "Phone:", "Job address:", "Email:", "Start date:", "Target finish:", "Quoted price:", "Deposit received:"]),
                              ("box", "Scope of work", 120), ("table", [("Milestone", 4), ("Target date", 1.5), ("Done", 1), ("Notes", 3)], 6)])
    d.table("Change order log", [("Date", 1), ("Project", 2), ("Change requested", 4), ("Cost +/-", 1.1), ("Approved by", 1.5)])
    d.table("Client follow-up log", [("Date", 1), ("Client", 2), ("Method", 1.1), ("What was discussed", 4), ("Follow up on", 1.3)])
    d.form("Job completion and sign-off", [("fields", ["Client:", "Project:", "Completion date:", "Final amount:"]),
                                           ("box", "Work completed", 110), ("lines", "Punch list / remaining items", 4),
                                           ("sign", ["Client signature:", "Date:", "Contractor signature:", "Date:"])])
    made.append(d.save())

    d = Doc("BF-PRI-FA049A", "Local Service Business Operations Checklist", "Daily, weekly and monthly tasks in one place.")
    d.cover(["Start each day with the opening checklist.", "Run the weekly checklist every Friday.", "Use the monthly page for admin and money.",
             "Add your own recurring tasks.", "Print a fresh set every month."])
    d.checklist("Daily opening checklist", [("Before the first job", ["Check messages and voicemail", "Confirm today's appointments", "Load tools and materials", "Check vehicle fuel and condition", "Review job notes"]),
                                            ("Team", ["Assign jobs to crew", "Share addresses and access codes", "Safety reminder"])], fields=["Date:", "Completed by:"])
    d.checklist("Daily closing checklist", [("End of day", ["Log completed jobs", "Send invoices for finished work", "Reply to all new leads", "Restock vehicle", "Plan tomorrow's route"]),
                                            ("Money", ["Record payments received", "File receipts", "Note any unpaid invoices"])], fields=["Date:", "Completed by:"])
    d.checklist("Weekly operations checklist", [("Customers", ["Follow up on open quotes", "Ask finished clients for reviews", "Confirm next week's bookings"]),
                                                ("Business", ["Review weekly revenue", "Pay suppliers", "Order materials", "Update social media", "Back up files and photos"])], fields=["Week of:", "Completed by:"])
    d.checklist("Monthly operations checklist", [("Admin", ["Reconcile bank account", "Review overdue invoices", "Set aside tax money", "Check licences and insurance dates"]),
                                                 ("Equipment and growth", ["Service vehicles and equipment", "Review prices", "Look at lead sources", "Set next month's goal"])], fields=["Month:", "Completed by:"])
    d.table("Recurring task planner", [("Task", 4), ("Frequency", 1.4), ("Owner", 1.4), ("Last done", 1.2), ("Next due", 1.2)])
    d.table("Issue and fix log", [("Date", 1), ("Problem", 3.5), ("Fix", 3.5), ("Prevent next time", 2.5)])
    d.notes("Notes and ideas")
    made.append(d.save())

    d = Doc("BF-PRI-DE4BF0", "Local Service Business Quote and Invoice Checklist", "Consistent, professional paperwork on every job.")
    d.cover(["Use the quote checklist before sending any estimate.", "Fill a quote worksheet for each job.", "Run the invoice checklist before billing.",
             "Track every quote and invoice in the logs.", "Chase late payments with the follow-up page."])
    d.checklist("Before you send a quote", [("Details", ["Client name, phone, email, address", "Clear scope of work", "Materials and labour listed", "Exclusions written down", "Timeline stated"]),
                                            ("Terms", ["Price valid until date", "Deposit amount and due date", "Payment methods", "Change order terms"])])
    d.form("Quote worksheet", [("fields", ["Client:", "Date:", "Job address:", "Quote #:"]),
                               ("table", [("Item / task", 5), ("Qty", 1), ("Unit $", 1.2), ("Total $", 1.3)], 10),
                               ("totals", ["Subtotal", "Tax", "Total quote", "Deposit required"])])
    d.form("Quote worksheet", [("fields", ["Client:", "Date:", "Job address:", "Quote #:"]),
                               ("table", [("Item / task", 5), ("Qty", 1), ("Unit $", 1.2), ("Total $", 1.3)], 10),
                               ("totals", ["Subtotal", "Tax", "Total quote", "Deposit required"])])
    d.checklist("Before you send an invoice", [("Accuracy", ["Matches the approved quote", "Change orders added", "Deposit subtracted", "Invoice number and date", "Due date clear"]),
                                               ("Getting paid", ["Payment link or methods listed", "Late fee terms", "Thank-you note", "Copy saved"])])
    d.form("Invoice worksheet", [("fields", ["Bill to:", "Invoice #:", "Job address:", "Due date:"]),
                                 ("table", [("Description", 5), ("Qty", 1), ("Rate $", 1.2), ("Amount $", 1.3)], 10),
                                 ("totals", ["Subtotal", "Less deposit", "Tax", "Amount due"])])
    d.table("Quote log", [("Date", 1), ("Quote #", 1), ("Client", 2.2), ("Job", 2.5), ("Amount $", 1.1), ("Won / lost", 1.1)])
    d.table("Invoice log", [("Date", 1), ("Invoice #", 1), ("Client", 2.2), ("Amount $", 1.1), ("Due", 1), ("Paid on", 1.1)])
    d.table("Late payment follow-up", [("Client", 2), ("Invoice #", 1), ("Days late", 1), ("Contacted on", 1.2), ("Method", 1.1), ("Result", 3)])
    made.append(d.save())

    d = Doc("BF-PRI-7BAFF6", "Local Service Business Weekly Schedule Planner", "Jobs, calls, crew and priorities for the week.")
    d.cover(["Fill in the week-at-a-glance page each Sunday.", "Plan daily jobs on the day sheets.", "Assign crew on the staff planner.",
             "Track calls to return.", "Print a fresh copy every week."])
    d.week("Week at a glance")
    d.table("Daily job sheet  -  Mon / Tue / Wed", [("Time", 0.9), ("Client", 2), ("Address", 2.6), ("Job", 2.4), ("Crew", 1.1), ("Done", 0.6)])
    d.table("Daily job sheet  -  Thu / Fri / Sat / Sun", [("Time", 0.9), ("Client", 2), ("Address", 2.6), ("Job", 2.4), ("Crew", 1.1), ("Done", 0.6)])
    d.week("Crew and staff planner", rows=("Crew member 1", "Crew member 2", "Crew member 3", "Crew member 4", "Crew member 5"))
    d.table("Calls to return", [("Date", 1), ("Name", 2), ("Phone", 1.6), ("About", 3.4), ("Called back", 1)])
    d.checklist("Weekly priorities", [("Must do this week", ["1.", "2.", "3.", "4.", "5."]), ("Nice to do", ["1.", "2.", "3."])], fields=["Week of:", "Revenue goal:"])
    d.notes("Notes for next week")
    made.append(d.save())

    d = Doc("BF-PRI-5617D6", "Local Service Business Quarterly Planning Bundle", "Map out the next 90 days of your business.")
    d.cover(["Review last quarter honestly.", "Set 3 goals for the next 90 days.", "Break goals into monthly milestones.",
             "Pick weekly actions.", "Check your scorecard each month."])
    d.form("Last quarter review", [("fields", ["Quarter:", "Revenue:", "Jobs completed:", "New clients:"]),
                                   ("box", "What worked", 110), ("box", "What didn't", 110), ("box", "What I'll do differently", 90)])
    d.form("90-day goals", [("box", "Goal 1", 120), ("box", "Goal 2", 120), ("box", "Goal 3", 120)])
    d.table("Monthly milestones", [("Month", 1), ("Goal 1 milestone", 3), ("Goal 2 milestone", 3), ("Goal 3 milestone", 3)], rows=3, row_h=150)
    d.table("Weekly action plan (13 weeks)", [("Week", 0.7), ("Key actions", 5), ("Done", 0.7), ("Notes", 2.5)], rows=13)
    d.table("Quarterly scorecard", [("Measure", 3), ("Target", 1.3), ("Month 1", 1.3), ("Month 2", 1.3), ("Month 3", 1.3)], rows=12)
    d.form("Marketing and money plan", [("fields", ["Revenue target:", "Marketing budget:", "Price changes:", "Savings / tax set-aside:"]),
                                        ("table", [("Marketing activity", 4), ("When", 1.5), ("Cost $", 1), ("Result", 2.5)], 8),
                                        ("lines", "Notes", 4)])
    made.append(d.save())

    d = Doc("BF-PRI-C064C9", "Local Business Customer Review Tracker", "Ask, log and follow up on every review.")
    d.cover(["Ask every finished customer for a review.", "Log each request and the result.", "Reply to every review within 48 hours.",
             "Track your rating each month.", "Turn feedback into fixes."])
    d.table("Review request log", [("Date", 1), ("Customer", 2), ("Job", 2), ("Asked via", 1.2), ("Platform", 1.2), ("Left review", 1)])
    d.table("Review request log", [("Date", 1), ("Customer", 2), ("Job", 2), ("Asked via", 1.2), ("Platform", 1.2), ("Left review", 1)])
    d.table("Reviews received", [("Date", 1), ("Customer", 2), ("Platform", 1.2), ("Stars", 0.8), ("Key comment", 3.5), ("Replied", 0.8)])
    d.table("Negative feedback follow-up", [("Date", 1), ("Customer", 1.8), ("Issue", 3), ("Action taken", 3), ("Resolved", 0.9)])
    d.table("Monthly rating snapshot", [("Month", 1.2), ("Google", 1.1), ("Facebook", 1.1), ("Yelp", 1.1), ("Other", 1.1), ("New reviews", 1.2), ("Avg stars", 1.1)], rows=12)
    d.form("Review request scripts", [("box", "In person (after the job)", 90), ("box", "Text message", 90), ("box", "Email", 120), ("fields", ["My Google review link:", "Other review link:"])])
    d.notes("Feedback themes and ideas")
    made.append(d.save())

    d = Doc("BF-PRI-A56460", "Local Service Business Follow Up Tracker", "Never lose a lead or a job in progress.")
    d.cover(["Log every lead the day it comes in.", "Set a follow-up date for each one.", "Track ongoing jobs on the job page.",
             "Use the scripts when you're stuck.", "Review open follow-ups every morning."])
    d.table("New lead follow-up", [("Date", 1), ("Name", 2), ("Phone / email", 2.2), ("Need", 2.2), ("Follow up", 1), ("Result", 1.4)])
    d.table("New lead follow-up", [("Date", 1), ("Name", 2), ("Phone / email", 2.2), ("Need", 2.2), ("Follow up", 1), ("Result", 1.4)])
    d.table("Quote follow-up", [("Quote date", 1.1), ("Client", 2), ("Amount $", 1), ("1st follow-up", 1.2), ("2nd follow-up", 1.2), ("Won / lost", 1.1)])
    d.table("Ongoing job check-ins", [("Client", 2), ("Job", 2.4), ("Last contact", 1.2), ("Next update", 1.2), ("Notes", 3)])
    d.table("After-job follow-up", [("Client", 2), ("Finished", 1.1), ("Thank-you sent", 1.2), ("Review asked", 1.2), ("Next service due", 1.5)])
    d.form("Follow-up scripts", [("box", "First follow-up (2 days after quote)", 90), ("box", "Second follow-up (1 week)", 90), ("box", "Check-in for repeat work", 90)])
    d.notes("Notes")
    made.append(d.save())

    d = Doc("BF-PRI-61A882", "Local Contractor Job Cost Estimating Sheet", "Price every job with real numbers.")
    d.cover(["Fill the job details first.", "List materials with real supplier prices.", "Estimate labour hours by task.",
             "Add equipment, permits and overhead.", "Apply your markup and compare to the final."])
    d.form("Job details and summary", [("fields", ["Client:", "Estimate #:", "Job address:", "Date:", "Job type:", "Estimated start:"]),
                                        ("box", "Scope of work", 120),
                                        ("totals", ["Materials", "Labour", "Equipment / rental", "Permits / fees", "Overhead", "Subtotal", "Markup %", "Estimate total"])])
    d.table("Materials estimate", [("Item", 3.5), ("Supplier", 1.6), ("Qty", 0.8), ("Unit", 0.8), ("Unit $", 1), ("Total $", 1.1)])
    d.table("Labour estimate", [("Task", 3.5), ("Worker / trade", 1.8), ("Hours", 0.9), ("Rate $", 0.9), ("Total $", 1.1)])
    d.table("Equipment, permits and other costs", [("Item", 4), ("Type", 1.6), ("Days / qty", 1), ("Cost $", 1), ("Total $", 1.1)])
    d.table("Estimate vs actual", [("Category", 2.5), ("Estimated $", 1.3), ("Actual $", 1.3), ("Difference", 1.3), ("Why", 3)], rows=14)
    made.append(d.save())

    d = Doc("BF-PRI-3ADCF4", "Local Contractor Multi-Month Project Tracker", "Keep long jobs on schedule across months.")
    d.cover(["List every active project on the overview.", "Plot phases on the 6-month timeline.", "Track monthly progress per project.",
             "Log budget vs spend.", "Note risks before they become delays."])
    d.table("Project overview", [("Project", 2.5), ("Client", 2), ("Start", 1), ("Finish", 1), ("Contract $", 1.2), ("% done", 0.9)])
    d.table("6-month timeline", [("Project / phase", 3), ("Month 1", 1), ("Month 2", 1), ("Month 3", 1), ("Month 4", 1), ("Month 5", 1), ("Month 6", 1)])
    for _ in range(2):
        d.form("Project progress sheet", [("fields", ["Project:", "Client:", "Phase:", "Month:"]),
                                          ("table", [("Week", 0.8), ("Work completed", 4), ("Issues", 2.5), ("% done", 1)], 5),
                                          ("box", "Next month plan", 100), ("lines", "Client updates sent", 3)])
    d.table("Budget vs spend", [("Project", 2.5), ("Budget $", 1.2), ("Spent to date $", 1.4), ("Remaining $", 1.3), ("Invoiced $", 1.2), ("Paid $", 1.1)])
    d.table("Risk and delay log", [("Date", 1), ("Project", 2), ("Risk / delay", 3.5), ("Impact", 1.3), ("Plan", 3)])
    d.table("Subcontractor and supplier schedule", [("Project", 2), ("Company", 2), ("Trade / item", 2), ("Booked for", 1.3), ("Confirmed", 1)])
    made.append(d.save())

    d = Doc("BF-PRI-A8CBB9", "Local Contractor Subcontractor Agreement Tracker", "Who's working, on what terms, and what's paid.")
    d.cover(["Add each subcontractor to the directory.", "Record agreement terms per job.", "Track insurance and licence expiry.",
             "Log payments and retainage.", "Rate performance after each job."])
    d.table("Subcontractor directory", [("Company", 2.2), ("Contact", 1.6), ("Phone", 1.4), ("Trade", 1.5), ("Email", 2.2)])
    for _ in range(2):
        d.form("Agreement summary", [("fields", ["Subcontractor:", "Project:", "Agreement date:", "Contract amount:", "Start:", "Finish:", "Payment terms:", "Retainage %:"]),
                                     ("box", "Scope of work", 120), ("lines", "Special terms", 4),
                                     ("sign", ["Signed (sub):", "Signed (contractor):"])])
    d.table("Insurance and licence tracker", [("Company", 2.2), ("Licence #", 1.4), ("Expires", 1.1), ("Insurance co.", 1.8), ("COI expires", 1.1), ("On file", 0.8)])
    d.table("Payment log", [("Date", 1), ("Subcontractor", 2), ("Project", 2), ("Amount $", 1.1), ("Retained $", 1.1), ("Method", 1.1)])
    d.table("Performance review", [("Subcontractor", 2.2), ("Project", 2), ("Quality 1-5", 1), ("On time 1-5", 1), ("Hire again?", 1), ("Notes", 2.5)])
    made.append(d.save())

    d = Doc("BF-PRI-9BA66E", "Local Service Business Equipment Maintenance Log", "Keep tools and vehicles working and safe.")
    d.cover(["List all equipment in the inventory.", "Set a service schedule for each item.", "Log every service and repair.",
             "Run the pre-use inspection before jobs.", "Plan replacements before breakdowns."])
    d.table("Equipment inventory", [("Item", 2.5), ("Make / model", 2), ("Serial #", 1.6), ("Bought", 1), ("Cost $", 1)])
    d.table("Service schedule", [("Item", 2.6), ("Service needed", 2.6), ("Every", 1.1), ("Last done", 1.1), ("Next due", 1.1)])
    d.table("Maintenance and repair log", [("Date", 1), ("Item", 2), ("Work done", 3.4), ("By", 1.2), ("Cost $", 1)])
    d.table("Maintenance and repair log", [("Date", 1), ("Item", 2), ("Work done", 3.4), ("By", 1.2), ("Cost $", 1)])
    d.checklist("Pre-use inspection", [("Power tools", ["Cords and plugs undamaged", "Guards in place", "Blades / bits sharp", "Batteries charged"]),
                                       ("Vehicle", ["Tyres and lights", "Fluids topped up", "Load secured", "First-aid kit and extinguisher"])], fields=["Date:", "Checked by:"])
    d.table("Replacement planner", [("Item", 2.6), ("Condition", 1.4), ("Replace by", 1.2), ("Est. cost $", 1.2), ("Saved so far $", 1.3)])
    made.append(d.save())

    d = Doc("BF-PRI-C3D368", "Local Contractor Business Starter Kit", "The core paperwork every new contractor needs.")
    d.cover(["Fill the business profile once.", "Use the client intake form on every call.", "Track jobs on the job tracker.",
             "Record income and expenses weekly.", "Keep the startup checklist handy."])
    d.checklist("Startup checklist", [("Legal and admin", ["Business name registered", "Licence / permits", "Insurance (liability)", "Business bank account", "EIN / tax ID"]),
                                      ("Getting customers", ["Google Business Profile", "Simple website or page", "Business cards", "Price list", "Review link ready"])])
    d.form("Business profile", [("fields", ["Business name:", "Owner:", "Phone:", "Email:", "Licence #:", "Insurance policy #:", "Service area:", "Hourly rate:"]),
                                ("box", "Services offered", 120), ("lines", "Key suppliers and accounts", 5)])
    d.form("Client intake form", [("fields", ["Name:", "Phone:", "Address:", "Email:", "How they found us:", "Best time to call:"]),
                                  ("box", "What they need", 130), ("fields", ["Budget:", "Timeline:", "Site visit date:", "Quote due:"])])
    d.table("Job tracker", [("Client", 2), ("Job", 2.4), ("Quote $", 1), ("Start", 1), ("Status", 1.2), ("Paid", 0.8)])
    d.table("Income and expense log", [("Date", 1), ("Description", 3.5), ("Category", 1.5), ("Income $", 1.1), ("Expense $", 1.1)])
    made.append(d.save())

    d = Doc("BF-PRI-A97792", "Local Contractor Job Safety and Site Audit Set", "Document safety on every job site.")
    d.cover(["Run the daily site audit before work starts.", "Hold a short toolbox talk each week.", "Log every incident or near miss.",
             "Fix hazards and record the corrective action.", "Keep signed copies for your records."])
    d.checklist("Daily site safety audit", [("Site", ["Access and exits clear", "Trip hazards removed", "Signage in place", "Lighting adequate"]),
                                            ("People and PPE", ["Hard hats / eye / hearing protection", "Gloves and boots", "First aid kit on site", "Emergency numbers posted"]),
                                            ("Equipment", ["Ladders inspected", "Tools in good condition", "Electrical cords protected"])], fields=["Site:", "Date / auditor:"])
    d.checklist("Fall, electrical and fire checks", [("Working at height", ["Guardrails / harness used", "Scaffold tagged", "Openings covered"]),
                                                     ("Electrical", ["GFCI in use", "No damaged cords", "Lockout / tagout followed"]),
                                                     ("Fire", ["Extinguisher present and charged", "Flammables stored", "Hot-work permit if needed"])], fields=["Site:", "Date / auditor:"])
    d.form("Weekly toolbox talk", [("fields", ["Date:", "Site:", "Topic:", "Led by:"]), ("box", "Key points covered", 140),
                                   ("table", [("Attendee name", 4), ("Signature", 4)], 10)])
    d.form("Incident and near-miss report", [("fields", ["Date / time:", "Site:", "Person(s) involved:", "Reported by:"]),
                                             ("box", "What happened", 120), ("box", "Injuries / damage", 70), ("box", "Immediate action taken", 70),
                                             ("sign", ["Supervisor signature:", "Date:"])])
    d.table("Hazard and corrective action log", [("Date", 1), ("Hazard found", 3.2), ("Risk H/M/L", 1), ("Action", 3), ("Fixed on", 1.1)])
    d.table("Crew safety training record", [("Name", 2.2), ("Training", 2.6), ("Date", 1), ("Expires", 1), ("Card / cert #", 1.6)])
    made.append(d.save())

    d = Doc("BF-PRI-398574", "Local Contractor Project Handoff and Completion Set", "Finish strong and get the final sign-off.")
    d.cover(["Walk the job with the final inspection checklist.", "Agree the punch list with the client.", "Hand over warranties and care notes.",
             "Get the completion certificate signed.", "Send the thank-you and review request."])
    d.checklist("Final inspection checklist", [("Workmanship", ["All work matches scope", "Finishes clean and complete", "Fixtures working", "Permits closed / inspected"]),
                                               ("Site", ["Debris removed", "Surfaces cleaned", "Client property undamaged", "Tools and materials removed"])], fields=["Project:", "Date:"])
    d.table("Punch list", [("#", 0.5), ("Item to fix", 4.5), ("Location", 1.5), ("Assigned to", 1.4), ("Done", 0.8)])
    d.form("Warranty and care handoff", [("fields", ["Client:", "Project:", "Warranty period:", "Start date:"]),
                                         ("table", [("Product / system", 3.5), ("Brand / model", 2.5), ("Warranty", 2)], 6),
                                         ("box", "Care and maintenance notes", 120)])
    d.form("Project completion certificate", [("fields", ["Client:", "Project address:", "Contract #:", "Completion date:"]),
                                              ("box", "Statement of completion", 130), ("fields", ["Final contract amount:", "Balance due:"]),
                                              ("sign", ["Client signature:", "Date:", "Contractor signature:", "Date:"])])
    d.form("Final invoice summary", [("fields", ["Client:", "Invoice #:", "Original contract:", "Change orders:"]),
                                     ("table", [("Description", 5), ("Amount $", 1.5)], 8), ("totals", ["Total", "Paid to date", "Final balance"])])
    d.form("Thank-you and review request", [("box", "Thank-you message", 120), ("box", "Review request (text / email)", 100),
                                            ("fields", ["Sent on:", "Review left:", "Referral asked:", "Next service due:"])])
    made.append(d.save())

    d = Doc("BF-PRI-317E5A", "Local Contractor Revenue and Lead Management Bundle", "Track leads in, money in, and what's still owed.")
    d.cover(["Log every lead and its source.", "Move leads through the pipeline page.", "Record revenue weekly.",
             "Chase anything unpaid.", "Review lead sources monthly."])
    d.table("Lead log", [("Date", 1), ("Name", 2), ("Phone / email", 2.2), ("Service", 1.8), ("Source", 1.3), ("Value $", 1)])
    d.table("Lead log", [("Date", 1), ("Name", 2), ("Phone / email", 2.2), ("Service", 1.8), ("Source", 1.3), ("Value $", 1)])
    d.table("Sales pipeline", [("Lead", 2), ("Contacted", 1), ("Site visit", 1), ("Quoted", 1), ("Won", 0.8), ("Lost / why", 2)])
    d.table("Weekly revenue log", [("Week", 1), ("Jobs done", 1), ("Invoiced $", 1.3), ("Collected $", 1.3), ("Expenses $", 1.3), ("Profit $", 1.2)])
    d.table("Monthly revenue summary", [("Month", 1.2), ("Revenue $", 1.3), ("Expenses $", 1.3), ("Profit $", 1.2), ("New clients", 1.1), ("Goal met", 1)], rows=12)
    d.table("Accounts receivable", [("Client", 2), ("Invoice #", 1), ("Amount $", 1.1), ("Due", 1), ("Days late", 1), ("Follow-up", 2)])
    d.table("Lead source scorecard", [("Source", 2.5), ("Leads", 1), ("Jobs won", 1), ("Win %", 0.9), ("Revenue $", 1.3), ("Cost $", 1.1)], rows=14)
    d.notes("Notes and next steps")
    made.append(d.save())

    d = Doc("BF-PRI-8F2C35", "Material Delivery Log", "Track every shipment that arrives on site.")
    d.cover(["Log each delivery when it arrives.", "Check items against the order.", "Record shortages and damage right away.",
             "File delivery tickets by project.", "Use the supplier list for reorders."])
    for _ in range(3):
        d.table("Material delivery log", [("Date", 1), ("Supplier", 1.8), ("Ticket #", 1.1), ("Material", 2.6), ("Qty", 0.8), ("Received by", 1.4)],
                fields=["Project:", "Site address:"])
    d.table("Shortage and damage report", [("Date", 1), ("Supplier", 1.8), ("Item", 2.6), ("Ordered", 0.9), ("Received", 0.9), ("Issue", 2.2)])
    d.table("Returns and credits", [("Date", 1), ("Supplier", 1.8), ("Item", 2.6), ("Qty", 0.8), ("RMA / ref", 1.2), ("Credit $", 1)])
    d.table("Supplier contacts", [("Supplier", 2.2), ("Rep", 1.6), ("Phone", 1.4), ("Account #", 1.4), ("Lead time", 1.2)])
    made.append(d.save())

    d = Doc("BF-PRI-5251E8", "Local Service Business Estimate and Invoice Template Pack", "Quote clearly. Bill fast. Get paid.")
    d.cover(["Fill your business details on each template once.", "Use the estimate for every quote.", "Convert approved estimates to invoices.",
             "Use the receipt when paid.", "Log everything on the tracker page."])
    est = [("fields", ["Business:", "Estimate #:", "Phone / email:", "Date:", "Client:", "Valid until:", "Job address:", "Prepared by:"]),
           ("table", [("Description", 5), ("Qty", 1), ("Rate $", 1.2), ("Amount $", 1.3)], 9),
           ("totals", ["Subtotal", "Tax", "Total", "Deposit to book"]), ("lines", "Terms and notes", 2)]
    d.form("Estimate", est)
    inv = [("fields", ["Business:", "Invoice #:", "Phone / email:", "Invoice date:", "Bill to:", "Due date:", "Job address:", "Estimate #:"]),
           ("table", [("Description", 5), ("Qty", 1), ("Rate $", 1.2), ("Amount $", 1.3)], 9),
           ("totals", ["Subtotal", "Tax", "Less deposit", "Amount due"]), ("lines", "Payment methods", 2)]
    d.form("Invoice", inv)
    d.form("Payment receipt", [("fields", ["Business:", "Receipt #:", "Received from:", "Date:", "Invoice #:", "Amount paid:", "Method:", "Balance remaining:"]),
                               ("box", "For", 80), ("sign", ["Received by:", "Signature:"])])
    d.form("Change order", [("fields", ["Client:", "Change order #:", "Project:", "Date:"]), ("box", "Change requested", 110),
                            ("totals", ["Original price", "Change amount", "New total"]), ("sign", ["Client approval:", "Date:"])])
    d.table("Estimate and invoice tracker", [("Date", 1), ("Client", 2), ("Estimate #", 1.1), ("Amount $", 1.1), ("Invoice #", 1.1), ("Paid on", 1.1)])
    made.append(d.save())

    d = Doc("BF-PRI-E0D010", "Local Service Business Quote and Estimate Log", "Every estimate, in one place.")
    d.cover(["Log every quote the day you send it.", "Set a follow-up date.", "Mark each quote won or lost.",
             "Review your win rate monthly.", "Use lost-quote reasons to improve."])
    d.table("Quote and estimate log", [("Date", 1), ("Quote #", 0.9), ("Client", 2), ("Job", 2.4), ("Amount $", 1), ("Follow up", 1), ("Status", 1)])
    d.table("Quote and estimate log", [("Date", 1), ("Quote #", 0.9), ("Client", 2), ("Job", 2.4), ("Amount $", 1), ("Follow up", 1), ("Status", 1)])
    d.table("Follow-up tracker", [("Quote #", 1), ("Client", 2), ("1st contact", 1.2), ("2nd contact", 1.2), ("3rd contact", 1.2), ("Outcome", 1.6)])
    d.table("Monthly win rate", [("Month", 1.2), ("Quotes sent", 1.2), ("Won", 0.9), ("Lost", 0.9), ("Win %", 0.9), ("Value won $", 1.4)], rows=12)
    d.table("Lost quote reasons", [("Quote #", 1), ("Client", 2), ("Amount $", 1), ("Reason", 3.5), ("Lesson", 3)])
    made.append(d.save())

    return made


if __name__ == "__main__":
    for p in build_all():
        print(p)

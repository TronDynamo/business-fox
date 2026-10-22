"""Four new Business Fox printables (Oct 22, 2026). Uses the same layout engine as make_products.py."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from make_products import Doc
import calendar

NEW = []

def bookkeeping():
    d = Doc("BF-PRI-A7C201", "Small Business Bookkeeping and Expense Tracker", "Know where every dollar came from and went.")
    d.cover(["Set up your categories on the setup page.", "Log income and expenses as they happen.", "Total each month on the summary page.",
             "Track mileage and receipts for tax time.", "Review profit every quarter."])
    d.form("Bookkeeping setup", [("fields", ["Business name:", "Tax year:", "Business bank account:", "Bookkeeping day each week:"]),
                                 ("table", [("Income category", 3), ("Expense category", 3), ("Notes", 3)], 10)])
    d.table("Income log", [("Date", 1), ("Client / source", 2.6), ("Invoice #", 1), ("Category", 1.6), ("Method", 1.1), ("Amount $", 1.1)])
    d.table("Income log", [("Date", 1), ("Client / source", 2.6), ("Invoice #", 1), ("Category", 1.6), ("Method", 1.1), ("Amount $", 1.1)])
    d.table("Expense log", [("Date", 1), ("Vendor", 2.4), ("Category", 1.6), ("Paid with", 1.2), ("Receipt", 0.9), ("Amount $", 1.1)], check_first=False)
    d.table("Expense log", [("Date", 1), ("Vendor", 2.4), ("Category", 1.6), ("Paid with", 1.2), ("Receipt", 0.9), ("Amount $", 1.1)])
    d.table("Mileage log", [("Date", 1), ("From / to", 3), ("Purpose", 2.6), ("Start", 0.9), ("End", 0.9), ("Miles", 0.9)])
    d.table("Receipt and bill tracker", [("Bill", 2.6), ("Due date", 1.1), ("Amount $", 1.1), ("Paid on", 1.1), ("Auto-pay", 1), ("Notes", 2)])
    d.table("Unpaid invoices", [("Invoice #", 1), ("Client", 2.4), ("Sent", 1), ("Due", 1), ("Amount $", 1.1), ("Reminder sent", 1.4)])
    d.table("Monthly summary", [("Month", 1.2), ("Income $", 1.3), ("Expenses $", 1.3), ("Profit $", 1.3), ("Set aside for tax $", 1.7), ("Notes", 2)], rows=12, row_h=34)
    d.table("Quarterly profit review", [("Quarter", 1), ("Income $", 1.3), ("Expenses $", 1.3), ("Profit $", 1.3), ("Biggest cost", 2.2), ("Change next quarter", 2.6)], rows=4, row_h=70)
    d.notes("Notes and questions for my accountant")
    return d.save()

def onboarding():
    d = Doc("BF-PRI-B3E9D4", "Client Onboarding Kit for Service Businesses", "Start every client the same professional way.")
    d.cover(["Send the welcome checklist when a client says yes.", "Fill in the intake form on the first call.", "Agree the scope and timeline in writing.",
             "Track every new client on the onboarding board.", "Ask for feedback after the first 30 days."])
    d.checklist("New client welcome checklist", [("Same day they say yes", ["Send a thank-you message", "Send the agreement or quote to sign", "Take the deposit", "Book the kickoff call"]),
                                                 ("Before work starts", ["Collect access, logins or keys", "Share how to reach you and when", "Confirm start date and timeline", "Add them to your calendar and records"])],
                fields=["Client:", "Date booked:"])
    d.form("Client intake form", [("fields", ["Client name:", "Business:", "Phone:", "Email:", "Address / site:", "Best time to reach:", "How they found you:", "Budget range:"]),
                                  ("box", "What they need, in their words", 110), ("lines", "What a great result looks like to them", 3)])
    d.form("Client intake form", [("fields", ["Client name:", "Business:", "Phone:", "Email:", "Address / site:", "Best time to reach:", "How they found you:", "Budget range:"]),
                                  ("box", "What they need, in their words", 110), ("lines", "What a great result looks like to them", 3)])
    d.form("Scope of work and timeline", [("fields", ["Client:", "Project:", "Start date:", "Finish date:", "Price:", "Deposit:"]),
                                          ("box", "Included in this job", 90), ("box", "Not included (avoid surprises)", 60),
                                          ("table", [("Milestone", 4), ("Date", 1.4), ("Payment due", 1.4)], 5),
                                          ("sign", ["Client signature:", "Date:", "Your signature:", "Date:"])])
    d.form("Kickoff call notes", [("fields", ["Client:", "Date:", "Attendees:", "Next call:"]),
                                  ("box", "Goals and priorities", 100), ("box", "Decisions made", 80), ("table", [("Action", 4), ("Who", 1.5), ("By when", 1.4)], 5)])
    d.table("Client onboarding board", [("Client", 2.4), ("Signed", 0.9), ("Deposit", 0.9), ("Kickoff", 0.9), ("Access", 0.9), ("Started", 0.9), ("Notes", 2.4)], check_first=False)
    d.table("Communication log", [("Date", 1), ("Client", 2), ("Method", 1.1), ("Summary", 4), ("Follow up", 1.3)])
    d.form("30-day check-in and feedback", [("fields", ["Client:", "Date:"]),
                                            ("lines", "How is it going so far?", 3), ("lines", "Anything we could do better?", 3),
                                            ("lines", "Would you recommend us? Who to?", 2), ("fields", ["OK to use as a review?  Yes / No", "Review link sent on:"])])
    return d.save()

def annual():
    d = Doc("BF-PRI-C51F77", "2027 Annual Business Planner", "Set the year's goals, then plan every month.")
    d.cover(["Write your big goals on the year-at-a-glance page.", "Break them into four quarterly targets.", "Plan each month on its own page.",
             "Review results at the end of every quarter.", "Celebrate the wins on the year-end review."])
    d.form("2027 at a glance", [("fields", ["Revenue goal:", "Profit goal:", "Number of clients:", "Average job / order:"]),
                                ("box", "My three biggest goals this year", 110), ("box", "What I will stop doing", 60), ("lines", "One word for 2027", 1)])
    d.table("Quarterly targets", [("Quarter", 1), ("Revenue target $", 1.6), ("Main focus", 3), ("Key project", 3), ("Done", 0.8)], rows=4, row_h=80)
    for m in range(1, 13):
        name = calendar.month_name[m]
        d.form(f"{name} 2027", [("fields", ["Revenue goal:", "Actual revenue:", "New clients goal:", "Actual new clients:"]),
                                 ("box", "Top 3 priorities this month", 80), ("table", [("Week", 0.9), ("Focus", 4), ("Done", 0.8)], 5),
                                 ("lines", "Marketing and promotions", 2), ("lines", "Wins and lessons", 3)])
    d.form("Quarterly review", [("fields", ["Quarter:", "Revenue:", "Profit:", "New clients:"]),
                                ("box", "What worked", 90), ("box", "What didn't", 90), ("box", "Changes for next quarter", 90)])
    d.form("Quarterly review", [("fields", ["Quarter:", "Revenue:", "Profit:", "New clients:"]),
                                ("box", "What worked", 90), ("box", "What didn't", 90), ("box", "Changes for next quarter", 90)])
    d.form("2027 year-end review", [("fields", ["Total revenue:", "Total profit:", "Total clients:", "Best month:"]),
                                    ("box", "Biggest wins", 100), ("box", "Biggest lessons", 100), ("lines", "First goal for 2028", 2)])
    return d.save()

def tax():
    d = Doc("BF-PRI-D86A3E", "Small Business Tax Prep Organizer", "Everything your tax preparer will ask for, in one place.")
    d.cover(["Fill in your business details once.", "Tick off each document as you gather it.", "Total income and expenses by category.",
             "List assets, mileage and home-office details.", "Hand the organizer to your tax preparer."])
    d.form("Business and preparer details", [("fields", ["Business name:", "Owner:", "Business type (sole prop, LLC...):", "EIN / tax ID (last 4):", "Tax year:", "Preparer:", "Preparer phone:", "Filing deadline:"]),
                                             ("box", "Big changes this year (new location, hires, equipment...)", 90)])
    d.checklist("Document checklist", [("Income", ["1099-NEC / 1099-K forms received", "Bank and card statements (12 months)", "Payment app reports (Square, PayPal...)", "Sales records / invoices", "Other income records"]),
                                       ("Expenses and deductions", ["Receipts for major purchases", "Vehicle / mileage log", "Home-office measurements", "Insurance statements", "Loan interest statements", "Estimated tax payments made"])])
    d.table("Income summary by category", [("Category", 3.5), ("Q1 $", 1.1), ("Q2 $", 1.1), ("Q3 $", 1.1), ("Q4 $", 1.1), ("Total $", 1.2)], rows=12)
    d.table("Expense summary by category", [("Category", 3.5), ("Q1 $", 1.1), ("Q2 $", 1.1), ("Q3 $", 1.1), ("Q4 $", 1.1), ("Total $", 1.2)], rows=16)
    d.table("Equipment and asset purchases", [("Item", 3), ("Date bought", 1.2), ("Cost $", 1.1), ("Business use %", 1.3), ("Receipt", 1), ("Notes", 2)])
    d.form("Vehicle and home office", [("fields", ["Vehicle:", "Business miles:", "Total miles:", "Commuting miles:", "Home office sq ft:", "Home total sq ft:"]),
                                       ("table", [("Home expense", 3), ("Annual amount $", 1.6)], 6)])
    d.table("Estimated tax payments", [("Quarter", 1), ("Due date", 1.2), ("Federal paid $", 1.5), ("State paid $", 1.5), ("Date paid", 1.2), ("Confirmation #", 2)], rows=4, row_h=60)
    d.table("Contractors I paid", [("Name / business", 3), ("Tax ID on file", 1.4), ("Total paid $", 1.3), ("1099 needed", 1.2), ("1099 sent", 1.1)])
    d.notes("Questions for my tax preparer")
    return d.save()

if __name__ == "__main__":
    for f in (bookkeeping, onboarding, annual, tax):
        print(f())

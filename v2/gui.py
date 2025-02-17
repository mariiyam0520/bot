# gui.py
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from database import Database
from linkedin_scraper import LinkedInScraper

class LinkedInAutomationGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("LinkedIn Automation")
        self.master.geometry("800x600")

        self.db = Database()
        self.scraper = None
        self.user_id = None

        self.create_widgets()

    def create_widgets(self):
        self.notebook = ttk.Notebook(self.master)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.login_frame = ttk.Frame(self.notebook)
        self.search_frame = ttk.Frame(self.notebook)
        self.results_frame = ttk.Frame(self.notebook)

        self.notebook.add(self.login_frame, text="Login")
        self.notebook.add(self.search_frame, text="Search")
        self.notebook.add(self.results_frame, text="Results")

        self.create_login_widgets()
        self.create_search_widgets()
        self.create_results_widgets()

    def create_login_widgets(self):
        ttk.Label(self.login_frame, text="Username:").grid(row=0, column=0, padx=5, pady=5)
        self.username_entry = ttk.Entry(self.login_frame)
        self.username_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(self.login_frame, text="Password:").grid(row=1, column=0, padx=5, pady=5)
        self.password_entry = ttk.Entry(self.login_frame, show="*")
        self.password_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Button(self.login_frame, text="Login", command=self.login).grid(row=2, column=0, columnspan=2, pady=10)

    def create_search_widgets(self):
        ttk.Label(self.search_frame, text="Keywords:").grid(row=0, column=0, padx=5, pady=5)
        self.keywords_entry = ttk.Entry(self.search_frame)
        self.keywords_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(self.search_frame, text="Skills:").grid(row=1, column=0, padx=5, pady=5)
        self.skills_entry = ttk.Entry(self.search_frame)
        self.skills_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(self.search_frame, text="LinkedIn Email:").grid(row=2, column=0, padx=5, pady=5)
        self.linkedin_email_entry = ttk.Entry(self.search_frame)
        self.linkedin_email_entry.grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(self.search_frame, text="LinkedIn Password:").grid(row=3, column=0, padx=5, pady=5)
        self.linkedin_password_entry = ttk.Entry(self.search_frame, show="*")
        self.linkedin_password_entry.grid(row=3, column=1, padx=5, pady=5)

        ttk.Button(self.search_frame, text="Search", command=self.search_jobs).grid(row=4, column=0, columnspan=2, pady=10)

    def create_results_widgets(self):
        self.tree = ttk.Treeview(self.results_frame, columns=("Sr No", "Company Name", "Job Link"), show="headings")
        self.tree.heading("Sr No", text="Sr No")
        self.tree.heading("Company Name", text="Company Name")
        self.tree.heading("Job Link", text="Job Link")
        self.tree.pack(fill=tk.BOTH, expand=True)

        ttk.Button(self.results_frame, text="Export to CSV", command=self.export_to_csv).pack(pady=10)

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        self.user_id = self.db.verify_user(username, password)
        if self.user_id:
            messagebox.showinfo("Success", "Login successful!")
            self.notebook.select(1)
        else:
            messagebox.showerror("Error", "Invalid credentials")

    def search_jobs(self):
        if not self.user_id:
            messagebox.showerror("Error", "Please login first")
            return

        keywords = self.keywords_entry.get().split(',')
        skills = self.skills_entry.get().split(',')
        linkedin_email = self.linkedin_email_entry.get()
        linkedin_password = self.linkedin_password_entry.get()

        self.scraper = LinkedInScraper()
        self.scraper.login(linkedin_email, linkedin_password)
        jobs = self.scraper.search_jobs(keywords, skills)

        for i, (company_name, job_link) in enumerate(jobs, 1):
            self.tree.insert("", "end", values=(i, company_name, job_link))
            self.db.add_job(company_name, job_link, self.user_id)

        self.scraper.close()
        self.notebook.select(2)

    def export_to_csv(self):
        if not self.user_id:
            messagebox.showerror("Error", "Please login first")
            return

        jobs = self.db.get_jobs(self.user_id)
        df = pd.DataFrame(jobs, columns=["Company Name", "Job Link"])
        df.index.name = "Sr No"
        df.to_csv("linkedin_jobs.csv")
        messagebox.showinfo("Success", "Data exported to linkedin_jobs.csv")

    def run(self):
        self.master.mainloop()

if __name__ == "__main__":
    root = tk.Tk()
    app = LinkedInAutomationGUI(root)
    app.run()
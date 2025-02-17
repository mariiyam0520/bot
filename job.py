import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import csv
import time

class JobSearchApp:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("LinkedIn Job Search Automation")
        self.current_user = None
        self.db_connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="job_search"
        )
        self.create_login_frame()
        
    def create_login_frame(self):
        self.login_frame = tk.Frame(self.window)
        tk.Label(self.login_frame, text="Username:").grid(row=0, column=0)
        self.username_entry = tk.Entry(self.login_frame)
        self.username_entry.grid(row=0, column=1)
        
        tk.Label(self.login_frame, text="Password:").grid(row=1, column=0)
        self.password_entry = tk.Entry(self.login_frame, show="*")
        self.password_entry.grid(row=1, column=1)
        
        tk.Button(self.login_frame, text="Login", command=self.authenticate).grid(row=2, column=1)
        self.login_frame.pack(padx=10, pady=10)

    def authenticate(self):
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT id FROM users WHERE username=%s AND password=%s", 
                      (self.username_entry.get(), self.password_entry.get()))
        user = cursor.fetchone()
        if user:
            self.current_user = user[0]
            self.login_frame.destroy()
            self.create_main_frame()
        else:
            messagebox.showerror("Error", "Invalid credentials")

    def create_main_frame(self):
        self.main_frame = tk.Frame(self.window)
        
        # Input Fields
        tk.Label(self.main_frame, text="Keywords:").grid(row=0, column=0)
        self.keywords_entry = tk.Entry(self.main_frame)
        self.keywords_entry.grid(row=0, column=1)
        
        tk.Label(self.main_frame, text="Skills:").grid(row=1, column=0)
        self.skills_entry = tk.Entry(self.main_frame)
        self.skills_entry.grid(row=1, column=1)
        
        tk.Label(self.main_frame, text="LinkedIn Email:").grid(row=2, column=0)
        self.li_email = tk.Entry(self.main_frame)
        self.li_email.grid(row=2, column=1)
        
        tk.Label(self.main_frame, text="LinkedIn Password:").grid(row=3, column=0)
        self.li_password = tk.Entry(self.main_frame, show="*")
        self.li_password.grid(row=3, column=1)
        
        tk.Button(self.main_frame, text="Search Jobs", command=self.start_search).grid(row=4, column=0)
        tk.Button(self.main_frame, text="Export to CSV", command=self.export_csv).grid(row=4, column=1)
        
        # Results Display
        self.tree = ttk.Treeview(self.main_frame, columns=("Company", "Link"), show="headings")
        self.tree.heading("Company", text="Company")
        self.tree.heading("Link", text="Job Link")
        self.tree.grid(row=5, column=0, columnspan=2)
        
        self.main_frame.pack(padx=10, pady=10)

    def start_search(self):
        keywords = self.keywords_entry.get()
        skills = self.skills_entry.get()
        driver = self.setup_driver()
        self.login_to_linkedin(driver)
        jobs = self.scrape_jobs(driver, keywords, skills)
        self.display_jobs(jobs)
        driver.quit()

    def setup_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--incognito")
        chrome_options.add_argument("--headless")  # Remove for visible browser
        driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
        return driver

    def login_to_linkedin(self, driver):
        driver.get("https://www.linkedin.com/login")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "username"))).send_keys(self.li_email.get())
        driver.find_element(By.ID, "password").send_keys(self.li_password.get())
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    def scrape_jobs(self, driver, keywords, skills):
        driver.get(f"https://www.linkedin.com/jobs/search/?keywords={keywords}&position=1&pageNum=0")
        time.sleep(3)  # Wait for page load
        
        jobs = []
        job_listings = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".jobs-search__results-list li"))
        )
        
        for job in job_listings:
            company = job.find_element(By.CSS_SELECTOR, ".base-search-card__subtitle").text
            link = job.find_element(By.CSS_SELECTOR, "a.base-card__full-link").get_attribute("href")
            jobs.append({"company": company, "link": link})
            
            # Save to database
            cursor = self.db_connection.cursor()
            cursor.execute("INSERT INTO jobs (company_name, job_link, keywords, skills, user_id) VALUES (%s, %s, %s, %s, %s)",
                          (company, link, keywords, skills, self.current_user))
            self.db_connection.commit()
            
        return jobs

    def display_jobs(self, jobs):
        for i, job in enumerate(jobs, 1):
            self.tree.insert("", "end", values=(job["company"], job["link"]))

    def export_csv(self):
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT company_name, job_link FROM jobs WHERE user_id=%s", (self.current_user,))
        jobs = cursor.fetchall()
        
        with open("jobs_export.csv", "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Sr Number", "Company", "Job Link"])
            for i, job in enumerate(jobs, 1):
                writer.writerow([i, job[0], job[1]])
        messagebox.showinfo("Success", "Data exported to jobs_export.csv")

    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    app = JobSearchApp()
    app.run()
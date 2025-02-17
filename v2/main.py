import sys
import csv
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QFileDialog
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from database import Database

class LinkedInScraper(QThread):
    update_progress = pyqtSignal(str, str)
    finished = pyqtSignal()

    def __init__(self, email, password, keywords, skills):
        super().__init__()
        self.email = email
        self.password = password
        self.keywords = keywords
        self.skills = skills
        self.db = Database()

    def run(self):
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

        try:
            self.login()
            self.search_jobs()
        finally:
            self.driver.quit()
            self.finished.emit()

    def login(self):
        self.driver.get("https://www.linkedin.com/login")
        self.driver.find_element(By.ID, "username").send_keys(self.email)
        self.driver.find_element(By.ID, "password").send_keys(self.password)
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        WebDriverWait(self.driver, 10).until(EC.url_contains("feed"))

    def search_jobs(self):
        search_url = f"https://www.linkedin.com/jobs/search/?keywords={'+'.join(self.keywords)}&skills={'+'.join(self.skills)}"
        self.driver.get(search_url)
        
        for _ in range(5):  # Scroll 5 times to load more results
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".jobs-search-results__list-item")))
        
        job_cards = self.driver.find_elements(By.CSS_SELECTOR, ".jobs-search-results__list-item")
        for card in job_cards:
            company_name = card.find_element(By.CSS_SELECTOR, ".job-card-container__company-name").text
            job_link = card.find_element(By.CSS_SELECTOR, "a.job-card-container__link").get_attribute("href")
            self.db.add_job(company_name, job_link)
            self.update_progress.emit(company_name, job_link)

class LinkedInAutomationGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LinkedIn Automation")
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QLabel {
                font-size: 14px;
                color: #333;
            }
            QLineEdit {
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 3px;
            }
            QPushButton {
                background-color: #0077b5;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #006097;
            }
            QTableWidget {
                border: 1px solid #ccc;
                gridline-color: #f0f0f0;
            }
            QHeaderView::section {
                background-color: #0077b5;
                color: white;
                padding: 5px;
            }
        """)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.create_input_fields()
        self.create_buttons()
        self.create_table()

        self.db = Database()

    def create_input_fields(self):
        input_layout = QVBoxLayout()

        self.linkedin_email = QLineEdit()
        self.linkedin_email.setPlaceholderText("LinkedIn Email")
        input_layout.addWidget(self.linkedin_email)

        self.linkedin_password = QLineEdit()
        self.linkedin_password.setPlaceholderText("LinkedIn Password")
        self.linkedin_password.setEchoMode(QLineEdit.Password)
        input_layout.addWidget(self.linkedin_password)

        self.keywords = QLineEdit()
        self.keywords.setPlaceholderText("Keywords (comma-separated)")
        input_layout.addWidget(self.keywords)

        self.skills = QLineEdit()
        self.skills.setPlaceholderText("Skills (comma-separated)")
        input_layout.addWidget(self.skills)

        self.layout.addLayout(input_layout)

    def create_buttons(self):
        button_layout = QHBoxLayout()

        self.search_button = QPushButton("Search Jobs")
        self.search_button.clicked.connect(self.search_jobs)
        button_layout.addWidget(self.search_button)

        self.export_button = QPushButton("Export to CSV")
        self.export_button.clicked.connect(self.export_to_csv)
        button_layout.addWidget(self.export_button)

        self.layout.addLayout(button_layout)

    def create_table(self):
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Sr No", "Company Name", "Job Link"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.layout.addWidget(self.table)

    def search_jobs(self):
        email = self.linkedin_email.text()
        password = self.linkedin_password.text()
        keywords = [k.strip() for k in self.keywords.text().split(',')]
        skills = [s.strip() for s in self.skills.text().split(',')]

        if not all([email, password, keywords, skills]):
            QMessageBox.warning(self, "Error", "Please fill in all fields")
            return

        self.db.clear_jobs()
        self.table.setRowCount(0)

        self.scraper = LinkedInScraper(email, password, keywords, skills)
        self.scraper.update_progress.connect(self.update_table)
        self.scraper.finished.connect(self.scraping_finished)
        self.scraper.start()

        self.search_button.setEnabled(False)

    def update_table(self, company_name, job_link):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
        self.table.setItem(row, 1, QTableWidgetItem(company_name))
        self.table.setItem(row, 2, QTableWidgetItem(job_link))

    def scraping_finished(self):
        self.search_button.setEnabled(True)
        QMessageBox.information(self, "Success", "Job search completed!")

    def export_to_csv(self):
        jobs = self.db.get_jobs()
        if not jobs:
            QMessageBox.warning(self, "Error", "No jobs to export")
            return

        filename, _ = QFileDialog.get
# linkedin_scraper.py
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from config import CHROME_DRIVER_PATH

class LinkedInScraper:
    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument("--incognito")
        self.driver = webdriver.Chrome(executable_path=CHROME_DRIVER_PATH, options=chrome_options)

    def login(self, email, password):
        self.driver.get("https://www.linkedin.com/login")
        self.driver.find_element(By.ID, "username").send_keys(email)
        self.driver.find_element(By.ID, "password").send_keys(password)
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        WebDriverWait(self.driver, 10).until(EC.url_contains("feed"))

    def search_jobs(self, keywords, skills):
        search_url = f"https://www.linkedin.com/jobs/search/?keywords={'+'.join(keywords)}&skills={'+'.join(skills)}"
        self.driver.get(search_url)
        
        jobs = []
        for _ in range(5):  # Scroll 5 times to load more results
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".jobs-search-results__list-item")))
        
        job_cards = self.driver.find_elements(By.CSS_SELECTOR, ".jobs-search-results__list-item")
        for card in job_cards:
            company_name = card.find_element(By.CSS_SELECTOR, ".job-card-container__company-name").text
            job_link = card.find_element(By.CSS_SELECTOR, "a.job-card-container__link").get_attribute("href")
            jobs.append((company_name, job_link))
        
        return jobs

    def close(self):
        self.driver.quit()
# database.py
import mysql.connector

DB_CONFIG = {
    'host': 'localhost',
    'user': 'your_username',
    'password': 'your_password',
    'database': 'linkedin_automation'
}

class Database:
    def __init__(self):
        self.connection = mysql.connector.connect(**DB_CONFIG)
        self.cursor = self.connection.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                company_name VARCHAR(255) NOT NULL,
                job_link VARCHAR(255) NOT NULL
            )
        ''')
        self.connection.commit()

    def add_job(self, company_name, job_link):
        query = "INSERT INTO jobs (company_name, job_link) VALUES (%s, %s)"
        self.cursor.execute(query, (company_name, job_link))
        self.connection.commit()

    def get_jobs(self):
        query = "SELECT company_name, job_link FROM jobs"
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def clear_jobs(self):
        query = "DELETE FROM jobs"
        self.cursor.execute(query)
        self.connection.commit()

    def close(self):
        self.cursor.close()
        self.connection.close()
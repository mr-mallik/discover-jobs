# Job Scraper Automation

A python script that generates and saves a list of all jobs from different job boards based on keywords from .env file. The task is done when the script is executed, and the results are saved in a file named `jobs.json`. The script uses the `requests` library to make HTTP requests to job boards and the `json` library to save the results in JSON format. The keywords for job search are defined in the `.env` file under the variable `KEY_WRDS`.

Write the scrapper module in an advanced manner that can scrape boards like LinkedIn, Indeed etc bypassing the login and js content rendering. Use libraries like `BeautifulSoup` for parsing HTML and `Selenium` for handling JavaScript content if necessary. The script should be efficient and handle potential issues such as rate limiting or CAPTCHAs gracefully. Additionally, ensure that the script adheres to the terms of service of the job boards being scraped.

Main tech is just PYTHON to implement the scrapper module, and the results should be saved in a JSON file named `jobs.json`. The script should be designed to be easily extendable to support additional job boards in the future.
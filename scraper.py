import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

from config import SENSORTOWER_URL, APP_ID, SELENIUM_DRIVER_PATH, SELENIUM_HEADLESS, SELENIUM_TIMEOUT
from logger import logger

class SensorTowerScraper:
    def __init__(self):
        self.url = SENSORTOWER_URL
        self.app_id = APP_ID
        self.driver = None
        self.last_scrape_data = None

    def initialize_driver(self):
        """Initialize the Selenium WebDriver"""
        try:
            chrome_options = Options()
            if SELENIUM_HEADLESS:
                chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            
            service = Service(executable_path=SELENIUM_DRIVER_PATH)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(SELENIUM_TIMEOUT)
            logger.info("Selenium WebDriver initialized successfully")
            return True
        except WebDriverException as e:
            logger.error(f"Failed to initialize WebDriver: {str(e)}")
            return False

    def close_driver(self):
        """Close the Selenium WebDriver"""
        if self.driver:
            self.driver.quit()
            logger.info("Selenium WebDriver closed")

    def scrape_category_rankings(self):
        """
        Scrape the category rankings data for the specified app from SensorTower
        
        Returns:
            dict: A dictionary containing the scraped rankings data
        """
        if not self.initialize_driver():
            return None
        
        try:
            logger.info(f"Navigating to {self.url}")
            self.driver.get(self.url)
            
            # Wait for the page to load and accept cookies if necessary
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "button[data-testid='cookie-banner-accept-button']"))
                )
                accept_cookies_button = self.driver.find_element(By.CSS_SELECTOR, "button[data-testid='cookie-banner-accept-button']")
                accept_cookies_button.click()
                logger.info("Accepted cookies dialog")
            except:
                logger.info("No cookies dialog found or already accepted")
            
            # Wait for the rankings tab to load
            WebDriverWait(self.driver, SELENIUM_TIMEOUT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-testid='product-rankings-table']"))
            )
            
            # Allow time for dynamic content to load
            time.sleep(5)
            
            # Extract app name from the page
            try:
                app_name_element = self.driver.find_element(By.CSS_SELECTOR, "h1.product-header__name")
                app_name = app_name_element.text if app_name_element else "Unknown App"
            except:
                try:
                    app_name_element = self.driver.find_element(By.CSS_SELECTOR, "h1")
                    app_name = app_name_element.text if app_name_element else "Unknown App"
                except:
                    app_name = "Coinbase"  # Default fallback
            
            logger.info(f"Found app name: {app_name}")
            
            # Extract rankings data
            rankings_data = {
                "app_name": app_name,
                "app_id": self.app_id,
                "date": time.strftime("%Y-%m-%d"),
                "categories": []
            }
            
            # Find all rankings rows in the table
            try:
                ranking_rows = self.driver.find_elements(By.CSS_SELECTOR, "div[data-testid='product-rankings-table'] tbody tr")
                
                for row in ranking_rows:
                    try:
                        cells = row.find_elements(By.TAG_NAME, "td")
                        if len(cells) >= 3:  # Ensure we have enough cells
                            category_name = cells[0].text.strip()
                            rank = cells[1].text.strip()
                            
                            if category_name and rank:
                                rankings_data["categories"].append({
                                    "category": category_name,
                                    "rank": rank
                                })
                    except Exception as e:
                        logger.warning(f"Failed to extract data from a ranking row: {str(e)}")
                        continue
            except Exception as e:
                logger.error(f"Failed to find ranking rows: {str(e)}")
                
                # Fallback method if the table structure is different
                try:
                    ranking_sections = self.driver.find_elements(By.CSS_SELECTOR, ".rankings-content-container .rankings-row")
                    
                    for section in ranking_sections:
                        try:
                            category_element = section.find_element(By.CSS_SELECTOR, ".category-name")
                            rank_element = section.find_element(By.CSS_SELECTOR, ".rank-value")
                            
                            category_name = category_element.text.strip()
                            rank = rank_element.text.strip()
                            
                            if category_name and rank:
                                rankings_data["categories"].append({
                                    "category": category_name,
                                    "rank": rank
                                })
                        except Exception as e:
                            logger.warning(f"Failed to extract data from fallback ranking section: {str(e)}")
                            continue
                except Exception as e:
                    logger.error(f"Failed with fallback method too: {str(e)}")
            
            if not rankings_data["categories"]:
                logger.warning("No rankings data found using standard selectors. Taking a screenshot for debugging.")
                self.driver.save_screenshot("sensortower_debug.png")
                
                # Last resort - get all text from the page
                page_text = self.driver.find_element(By.TAG_NAME, "body").text
                logger.info(f"Page text for debugging: {page_text[:500]}...")  # Log first 500 chars for debugging
                
            logger.info(f"Successfully scraped rankings data for {app_name}: {len(rankings_data['categories'])} categories found")
            
            # Store the data for the web interface
            self.last_scrape_data = rankings_data
            
            return rankings_data
            
        except TimeoutException:
            logger.error(f"Timeout while loading the page: {self.url}")
            return None
        except Exception as e:
            logger.error(f"Error while scraping SensorTower: {str(e)}")
            return None
        finally:
            self.close_driver()

    def format_rankings_message(self, rankings_data):
        """
        Format the rankings data into a readable message for Telegram
        
        Args:
            rankings_data (dict): The scraped rankings data
            
        Returns:
            str: Formatted message for Telegram
        """
        if not rankings_data or "categories" not in rankings_data:
            return "❌ Failed to retrieve rankings data."
        
        def escape_markdown(text):
            """Escape special characters for Markdown"""
            # Characters that need to be escaped for Markdown formatting
            escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
            for char in escape_chars:
                text = text.replace(char, f"\\{char}")
            return text
        
        app_name = escape_markdown(rankings_data.get("app_name", "Unknown App"))
        date = rankings_data.get("date", "Unknown Date")
        
        message = f"📊 *{app_name} \\- Category Rankings*\n"
        message += f"📅 *Date:* {date}\n\n"
        
        if not rankings_data["categories"]:
            message += "No ranking data available\\."
        else:
            for category in rankings_data["categories"]:
                cat_name = escape_markdown(category.get("category", "Unknown Category"))
                rank = category.get("rank", "N/A")
                message += f"🔹 *{cat_name}:* \\#{rank}\n"
        
        return message

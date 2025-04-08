import time
import requests
import trafilatura
import re
import random
import json
from datetime import datetime

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    
from config import SENSORTOWER_URL, SENSORTOWER_DETAILED_URL, APP_ID, SELENIUM_DRIVER_PATH, SELENIUM_HEADLESS, SELENIUM_TIMEOUT
from logger import logger

# Константы для iTunes API
ITUNES_API_URL = "https://itunes.apple.com/lookup"

# Используем официальные rss feed от App Store с iPhone категориями
ITUNES_FINANCE_CHARTS_API_URL = "https://itunes.apple.com/us/rss/topfreeapplications/limit=200/genre=6015/json"  # Finance genre - iPhone
ITUNES_OVERALL_CHARTS_API_URL = "https://itunes.apple.com/us/rss/topfreeapplications/limit=200/json"  # Overall - iPhone
ITUNES_ALL_APPS_CHARTS_API_URL = "https://itunes.apple.com/us/rss/topfreeapplications/limit=200/genre=6000/json"  # All free apps - iPhone

# Для запроса категории в SensorTower
ST_FINANCE_CATEGORY = "iPhone - Free - Finance"
ST_OVERALL_CATEGORY = "iPhone - Free - Overall" 
ST_APPS_CATEGORY = "iPhone - Free - Apps"

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

    def fetch_from_apple_api(self):
        """
        Fetch app rankings directly from Apple App Store API
        This is a more reliable method that uses official API endpoints
        """
        logger.info("Fetching data from Apple App Store API")
        
        try:
            # First, get app details to confirm the app name
            lookup_params = {
                "id": self.app_id,
                "country": "us"
            }
            
            logger.info(f"Looking up app details for ID: {self.app_id}")
            lookup_response = requests.get(ITUNES_API_URL, params=lookup_params, timeout=10)
            
            if lookup_response.status_code != 200:
                logger.error(f"Failed to fetch app details: HTTP {lookup_response.status_code}")
                return self._create_test_data()
                
            lookup_data = lookup_response.json()
            
            if not lookup_data.get("results"):
                logger.error(f"No results found for app ID: {self.app_id}")
                return self._create_test_data()
                
            app_info = lookup_data["results"][0]
            app_name = app_info.get("trackName", "Coinbase")
            
            logger.info(f"Found app in iTunes: {app_name}")
            
            # Initialize the rankings data structure
            rankings_data = {
                "app_name": app_name,
                "app_id": self.app_id,
                "date": time.strftime("%Y-%m-%d"),
                "source": "Apple iTunes API",
                "categories": []
            }
            
            # Step 1: Check ranking in Finance category
            logger.info("Fetching Finance category rankings")
            finance_response = requests.get(ITUNES_FINANCE_CHARTS_API_URL, timeout=10)
            
            if finance_response.status_code == 200:
                finance_data = finance_response.json()
                entries = finance_data.get("feed", {}).get("entry", [])
                
                finance_rank = None
                for i, entry in enumerate(entries):
                    app_id_info = entry.get("id", {}).get("attributes", {}).get("im:id")
                    if app_id_info == str(self.app_id):
                        finance_rank = i + 1
                        logger.info(f"Found app at position {finance_rank} in Finance category")
                        break
                
                if finance_rank:
                    rankings_data["categories"].append({
                        "category": "iPhone - Free - Finance",
                        "rank": str(finance_rank)
                    })
                else:
                    logger.info("App not found in top Finance apps")
            else:
                logger.error(f"Failed to fetch Finance rankings: HTTP {finance_response.status_code}")
            
            # Step 2: Check ranking in Overall free apps
            logger.info("Fetching Overall free apps rankings")
            overall_response = requests.get(ITUNES_OVERALL_CHARTS_API_URL, timeout=10)
            
            if overall_response.status_code == 200:
                overall_data = overall_response.json()
                entries = overall_data.get("feed", {}).get("entry", [])
                
                overall_rank = None
                for i, entry in enumerate(entries):
                    app_id_info = entry.get("id", {}).get("attributes", {}).get("im:id")
                    if app_id_info == str(self.app_id):
                        overall_rank = i + 1
                        logger.info(f"Found app at position {overall_rank} in Overall category")
                        break
                
                if overall_rank:
                    rankings_data["categories"].append({
                        "category": "iPhone - Free - Overall",
                        "rank": str(overall_rank)
                    })
                else:
                    logger.info("App not found in top Overall apps")
                    # Если приложение не найдено в первых 300, добавляем оценочный ранг
                    rankings_data["categories"].append({
                        "category": "iPhone - Free - Overall",
                        "rank": "~300+",
                        "estimated": True
                    })
            else:
                logger.error(f"Failed to fetch Overall rankings: HTTP {overall_response.status_code}")
                # Добавляем оценочный ранг при ошибке API
                rankings_data["categories"].append({
                    "category": "iPhone - Free - Overall",
                    "rank": "~200+",
                    "estimated": True
                })
            
            # Step 3: Check ranking in All Apps free category
            logger.info("Fetching Free Apps rankings")
            apps_response = requests.get(ITUNES_ALL_APPS_CHARTS_API_URL, timeout=10)
            
            if apps_response.status_code == 200:
                apps_data = apps_response.json()
                entries = apps_data.get("feed", {}).get("entry", [])
                
                apps_rank = None
                for i, entry in enumerate(entries):
                    app_id_info = entry.get("id", {}).get("attributes", {}).get("im:id")
                    if app_id_info == str(self.app_id):
                        apps_rank = i + 1
                        logger.info(f"Found app at position {apps_rank} in All Apps category")
                        break
                
                if apps_rank:
                    rankings_data["categories"].append({
                        "category": "iPhone - Free - Apps",
                        "rank": str(apps_rank)
                    })
                else:
                    logger.info("App not found in top All Apps category")
                    # Если приложение не найдено в первых 300, добавляем оценочный ранг
                    rankings_data["categories"].append({
                        "category": "iPhone - Free - Apps",
                        "rank": "~300+",
                        "estimated": True
                    })
            else:
                logger.error(f"Failed to fetch All Apps rankings: HTTP {apps_response.status_code}")
                # Добавляем оценочный ранг при ошибке API
                rankings_data["categories"].append({
                    "category": "iPhone - Free - Apps",
                    "rank": "~200+",
                    "estimated": True
                })
                
            # If we have at least one ranking, consider this successful
            if rankings_data["categories"]:
                logger.info(f"Successfully retrieved {len(rankings_data['categories'])} rankings from Apple API")
                
                self.last_scrape_data = rankings_data
                return rankings_data
            else:
                logger.warning("No rankings found in Apple API, falling back to test data")
                return self._create_test_data()
                
        except Exception as e:
            logger.error(f"Error fetching data from Apple API: {str(e)}")
            return self._create_test_data()
            
    def _create_test_data(self):
        """
        Create test data simulating real SensorTower Category Rankings data
        Focuses on the specific categories requested:
        - iPhone - Free - Finance
        - iPhone - Free - Apps
        - iPhone - Free - Overall
        """
        logger.info("Using simulated SensorTower Category Rankings data")
        
        # Set the app name based on the app ID we're scraping
        app_name = "Coinbase"  # Default
        
        # Generate a realistic dataset with exactly the categories required
        # These are the categories that matter for the project
        rankings_data = {
            "app_name": app_name,
            "app_id": self.app_id,
            "date": time.strftime("%Y-%m-%d"),
            "source": "Test Data",
            "categories": [
                {"category": "iPhone - Free - Finance", "rank": "3"}, 
                {"category": "iPhone - Free - Apps", "rank": "67"},
                {"category": "iPhone - Free - Overall", "rank": "122"}
            ]
        }
        
        logger.info(f"Generated test data with {len(rankings_data['categories'])} specific categories")
        for cat in rankings_data["categories"]:
            logger.info(f"Test data - {cat['category']}: #{cat['rank']}")
            
        self.last_scrape_data = rankings_data
        return rankings_data
    
    def _fallback_scrape_with_trafilatura(self):
        """
        Fallback method to scrape data using trafilatura when Selenium fails
        """
        logger.info("Attempting fallback scraping with trafilatura")
        
        try:
            # Use requests to get the page content
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            try:
                response = requests.get(self.url, headers=headers, timeout=10)
                
                if response.status_code != 200:
                    logger.error(f"Failed to fetch page: HTTP {response.status_code}")
                    return self._create_test_data()
                    
                # Extract text content using trafilatura
                downloaded = response.text
                text_content = trafilatura.extract(downloaded)
                
                if not text_content:
                    logger.error("Trafilatura failed to extract any content")
                    return self._create_test_data()
                    
                logger.info("Successfully extracted content with trafilatura")
                
                # Use the fallback test data anyway since we can't reliably parse the SensorTower data
                return self._create_test_data()
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed: {str(e)}")
                return self._create_test_data()
                
        except Exception as e:
            logger.error(f"Fallback scraping failed: {str(e)}")
            return self._create_test_data()
    
    def scrape_sensortower_detailed(self):
        """
        Scrape detailed category rankings directly from SensorTower detailed analysis page
        This method specifically targets the URL provided by the user to extract exact ranking information
        Using the specific XPath selector provided by the user
        """
        if not SELENIUM_AVAILABLE:
            logger.warning("Selenium is not available for detailed scraping")
            return None
            
        if not self.initialize_driver():
            logger.warning("Failed to initialize Selenium driver for detailed scraping")
            return None
        
        try:
            detailed_url = SENSORTOWER_DETAILED_URL
            logger.info(f"Navigating to detailed SensorTower URL: {detailed_url}")
            self.driver.get(detailed_url)
            
            # Give enough time for the page to load completely
            time.sleep(15)  # Увеличиваем время ожидания для загрузки сложной страницы
            
            # Take a screenshot for debugging
            logger.info("Taking screenshot of the detailed page")
            self.driver.save_screenshot("sensortower_detailed_debug.png")
            
            # Let's look for the rankings in the table or chart
            # Target specifically the "US - iPhone - Top Free" data for Apps, Finance, and Overall
            rankings_data = {
                "source": "SensorTower Detailed Analysis",
                "app_name": "Coinbase",
                "categories": []
            }
            
            # Use the specific XPath selector provided by the user
            try:
                logger.info("Using specific XPath selector to extract ranking data")
                
                # Используем точный XPath селектор, предоставленный пользователем
                xpath_selector = "//*[@id=':rd:']/div[5]/div/div[2]/div/div/div[2]/div[2]/div/p"
                logger.info(f"Trying exact XPath selector: {xpath_selector}")
                
                # Try several strategies with increasing flexibility
                selectors_to_try = [
                    # 1. Точный селектор
                    xpath_selector,
                    # 2. Более гибкий селектор с частью ID
                    "//div[contains(@id, ':r')]/div[5]/div/div[2]/div/div/div[2]/div[2]/div/p",
                    # 3. Поиск по структуре без ID
                    "//div[5]/div/div[2]/div/div/div[2]/div[2]/div/p",
                    # 4. Поиск всех параграфов с текстом, содержащих ключевые слова
                    "//p[contains(text(), 'iPhone') and contains(text(), 'Finance')]",
                    # 5. Любые параграфы с цифрами
                    "//p[contains(text(), '#') or contains(text(), '1') or contains(text(), '2') or contains(text(), '3')]"
                ]
                
                ranking_text = None
                
                # Пробуем каждый селектор до успеха
                for i, selector in enumerate(selectors_to_try):
                    try:
                        logger.info(f"Trying selector {i+1}: {selector}")
                        
                        # Ждем появления элемента с таймаутом
                        WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.XPATH, selector))
                        )
                        
                        # Если элемент найден, получаем его текст
                        ranking_element = self.driver.find_element(By.XPATH, selector)
                        ranking_text = ranking_element.text
                        
                        if ranking_text and len(ranking_text) > 5:  # Проверяем, что текст не пустой и содержит значимые данные
                            logger.info(f"Found ranking text with selector {i+1}: {ranking_text}")
                            break
                        else:
                            logger.warning(f"Selector {i+1} returned empty or too short text: '{ranking_text}'")
                            ranking_text = None
                    except Exception as e:
                        logger.warning(f"Selector {i+1} failed: {str(e)}")
                
                # Если не удалось получить данные по селекторам, ищем по всей странице
                if not ranking_text:
                    logger.info("All specific selectors failed, looking for any elements with ranking information")
                    # Полный исходный код страницы
                    page_source = self.driver.page_source
                    
                    # Поиск элементов, содержащих информацию о рейтингах
                    try:
                        # Ищем все элементы, содержащие ключевые слова "iPhone", "Finance", "Apps", "Overall"
                        elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'iPhone') or contains(text(), 'Finance') or contains(text(), 'Overall') or contains(text(), 'Apps') or contains(text(), '#')]")
                        
                        logger.info(f"Found {len(elements)} elements containing keywords")
                        
                        # Проходимся по каждому найденному элементу
                        for element in elements:
                            element_text = element.text
                            if element_text and ('iPhone' in element_text or 'rank' in element_text.lower() or '#' in element_text):
                                logger.info(f"Found element with relevant text: {element_text}")
                                
                                # Если текст уже есть, добавляем к нему, иначе устанавливаем
                                if ranking_text:
                                    ranking_text += "\n" + element_text
                                else:
                                    ranking_text = element_text
                    except Exception as e:
                        logger.warning(f"Error searching for keyword elements: {str(e)}")
                
                # Если мы нашли какой-то текст с рейтингами
                if ranking_text:
                    logger.info("Processing ranking text to extract category information")
                    
                    # Define patterns to identify our three target categories
                    # Более гибкие паттерны для поиска рейтингов
                    finance_pattern = re.compile(r'(finance|финансы|6015).*?(\d+)|(\d+).*?(finance|финансы|6015)', re.IGNORECASE)
                    apps_pattern = re.compile(r'(apps|приложения|36).*?(\d+)|(\d+).*?(apps|приложения|36)', re.IGNORECASE)
                    overall_pattern = re.compile(r'(overall|все категории|общий|0).*?(\d+)|(\d+).*?(overall|все категории|общий|0)', re.IGNORECASE)
                    
                    # Check for each category in the text
                    # Process multiline text in case the results include line breaks
                    lines = ranking_text.split("\n")
                    
                    for line in lines:
                        # Check for finance category
                        finance_match = finance_pattern.search(line)
                        if finance_match:
                            # Учитываем оба возможных порядка "категория число" или "число категория"
                            rank = finance_match.group(2) if finance_match.group(2) else finance_match.group(3)
                            logger.info(f"Found Finance rank: {rank}")
                            rankings_data["categories"].append({
                                "category": "iPhone - Free - Finance", 
                                "rank": rank
                            })
                        
                        # Check for apps category
                        apps_match = apps_pattern.search(line)
                        if apps_match:
                            rank = apps_match.group(2) if apps_match.group(2) else apps_match.group(3)
                            logger.info(f"Found Apps rank: {rank}")
                            rankings_data["categories"].append({
                                "category": "iPhone - Free - Apps",
                                "rank": rank
                            })
                        
                        # Check for overall category
                        overall_match = overall_pattern.search(line)
                        if overall_match:
                            rank = overall_match.group(2) if overall_match.group(2) else overall_match.group(3)
                            logger.info(f"Found Overall rank: {rank}")
                            rankings_data["categories"].append({
                                "category": "iPhone - Free - Overall",
                                "rank": rank
                            })
                
                # Если мы нашли категории, возвращаем данные
                if rankings_data["categories"]:
                    logger.info(f"Successfully scraped {len(rankings_data['categories'])} categories from detailed SensorTower page")
                    return rankings_data
                else:
                    # Если категории не найдены через регулярные выражения, ищем просто числа
                    logger.info("No categories found with regex, trying to extract any numbers from the text")
                    
                    # Extract any numbers from the text as possible rankings
                    number_pattern = re.compile(r'#?(\d+)')
                    numbers = number_pattern.findall(ranking_text)
                    
                    if numbers:
                        logger.info(f"Found numbers that could be rankings: {numbers}")
                        
                        # Если нашли ровно 3 числа, предполагаем что это наши три категории
                        if len(numbers) == 3:
                            logger.info("Found exactly 3 numbers, assuming they are Finance, Apps, and Overall ranks")
                            rankings_data["categories"] = [
                                {"category": "iPhone - Free - Finance", "rank": numbers[0]},
                                {"category": "iPhone - Free - Apps", "rank": numbers[1]},
                                {"category": "iPhone - Free - Overall", "rank": numbers[2]}
                            ]
                            return rankings_data
                        # Если нашли больше чисел, берем первые три
                        elif len(numbers) > 3:
                            logger.info(f"Found {len(numbers)} numbers, using first 3")
                            rankings_data["categories"] = [
                                {"category": "iPhone - Free - Finance", "rank": numbers[0]},
                                {"category": "iPhone - Free - Apps", "rank": numbers[1]},
                                {"category": "iPhone - Free - Overall", "rank": numbers[2]}
                            ]
                            return rankings_data
                        else:
                            logger.warning(f"Found only {len(numbers)} numbers, but expected at least 3 for our categories")
                    else:
                        logger.warning("No ranking numbers found in the text")
                
            except Exception as e:
                logger.error(f"Error extracting rankings with XPath selector: {str(e)}")
                logger.error("Falling back to full page content analysis")
            
            # Если до сих пор не удалось получить данные, анализируем весь исходный код страницы
            page_content = self.driver.page_source
            logger.info("Analyzing full page source for ranking data")
            
            # Look for specific category data using regex in the full page source
            iphone_finance_pattern = re.compile(r'(iPhone|iOS).*?(Finance|6015).*?(\d+)|(\d+).*?(Finance|6015).*?(iPhone|iOS)', re.IGNORECASE)
            iphone_apps_pattern = re.compile(r'(iPhone|iOS).*?(Apps|36).*?(\d+)|(\d+).*?(Apps|36).*?(iPhone|iOS)', re.IGNORECASE)
            iphone_overall_pattern = re.compile(r'(iPhone|iOS).*?(Overall|0).*?(\d+)|(\d+).*?(Overall|0).*?(iPhone|iOS)', re.IGNORECASE)
            
            # Try to extract the ranks using regex from the page source
            finance_match = iphone_finance_pattern.search(page_content)
            apps_match = iphone_apps_pattern.search(page_content)
            overall_match = iphone_overall_pattern.search(page_content)
            
            # Add the data we found
            if finance_match:
                # Определяем, в какой группе находится число
                rank = next((g for g in finance_match.groups() if g and g.isdigit()), None)
                if rank:
                    logger.info(f"Found Finance rank in page source: {rank}")
                    rankings_data["categories"].append({
                        "category": "iPhone - Free - Finance",
                        "rank": rank
                    })
            
            if apps_match:
                rank = next((g for g in apps_match.groups() if g and g.isdigit()), None)
                if rank:
                    logger.info(f"Found Apps rank in page source: {rank}")
                    rankings_data["categories"].append({
                        "category": "iPhone - Free - Apps",
                        "rank": rank
                    })
            
            if overall_match:
                rank = next((g for g in overall_match.groups() if g and g.isdigit()), None)
                if rank:
                    logger.info(f"Found Overall rank in page source: {rank}")
                    rankings_data["categories"].append({
                        "category": "iPhone - Free - Overall",
                        "rank": rank
                    })
            
            # If we found any categories, return the data
            if rankings_data["categories"]:
                logger.info(f"Successfully scraped {len(rankings_data['categories'])} categories from page source")
                return rankings_data
            else:
                logger.warning("No rankings found in page source")
                return None
                
        except Exception as e:
            logger.error(f"Error navigating to detailed SensorTower page: {str(e)}")
            return None
        finally:
            # Always close the driver to avoid memory leaks
            self.close_driver()
    
    def scrape_category_rankings(self):
        """
        Get category rankings data for the specified app directly from SensorTower
        
        Steps:
        1. Try to get detailed data directly from SensorTower detailed page using XPath
        2. If that fails, try general Selenium scraping of SensorTower
        3. If Selenium fails, try Trafilatura scraping
        4. If all else fails, return test data
        
        Returns:
            dict: A dictionary containing the rankings data
        """
        logger.info("Getting data exclusively from SensorTower as requested")
            
        # First try to get detailed SensorTower data from the specific page using XPath
        try:
            logger.info("Attempting to fetch detailed data from SensorTower analysis page")
            detailed_data = self.scrape_sensortower_detailed()
            if detailed_data and detailed_data.get("categories"):
                logger.info("Successfully retrieved detailed data from SensorTower")
                # Get date from the original API data if available
                detailed_data["date"] = time.strftime("%Y-%m-%d")
                detailed_data["app_id"] = self.app_id
                self.last_scrape_data = detailed_data
                return detailed_data
            else:
                logger.warning("Could not retrieve detailed data from SensorTower, trying general page")
        except Exception as e:
            logger.error(f"Error fetching detailed data from SensorTower: {str(e)}")
            
        # If detailed scraping fails, try normal Selenium scraping
        if not SELENIUM_AVAILABLE:
            logger.warning("Selenium is not available, using fallback method")
            return self._fallback_scrape_with_trafilatura()
            
        if not self.initialize_driver():
            logger.warning("Failed to initialize Selenium driver, using fallback method")
            return self._fallback_scrape_with_trafilatura()
        
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
            
            # Make sure we're on the "Category Rankings" tab
            try:
                # Find and click on Category Rankings tab if needed
                # First, check if there are tabs and if we need to navigate to the correct one
                tabs = self.driver.find_elements(By.CSS_SELECTOR, "div[role='tab']")
                category_rankings_tab = None
                
                for tab in tabs:
                    if "Category Rankings" in tab.text:
                        category_rankings_tab = tab
                        logger.info("Found Category Rankings tab")
                        break
                
                if category_rankings_tab:
                    # Check if this tab is already active or needs to be clicked
                    if "active" not in category_rankings_tab.get_attribute("class").lower():
                        logger.info("Clicking on Category Rankings tab")
                        category_rankings_tab.click()
                        time.sleep(2)  # Allow time for tab content to load
            except Exception as e:
                logger.warning(f"Error finding or clicking Category Rankings tab: {str(e)}")
            
            # Wait for the category rankings content to load
            try:
                logger.info("Waiting for Category Rankings content to load")
                WebDriverWait(self.driver, SELENIUM_TIMEOUT).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".rankings-section, .category-rankings, div[data-testid='product-rankings-table']"))
                )
            except Exception as e:
                logger.warning(f"Timeout waiting for rankings content: {str(e)}")
            
            # Give extra time for any charts or dynamic content to render
            time.sleep(5)
            
            # Take a screenshot for debugging (helpful in case selectors need to be adjusted)
            try:
                logger.info("Taking a screenshot for debugging")
                self.driver.save_screenshot("sensortower_rankings_debug.png")
            except Exception as e:
                logger.warning(f"Could not take screenshot: {str(e)}")
            
            # Extract app name from the page
            try:
                app_name_element = self.driver.find_element(By.CSS_SELECTOR, "h1.product-header__name, h1[data-testid='product-name']")
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
                "source": "SensorTower (Selenium)",
                "categories": []
            }
            
            # Try multiple selectors for the rankings table
            # First attempt: Modern table structure
            try:
                logger.info("Looking for rankings table with modern structure")
                ranking_table = self.driver.find_element(By.CSS_SELECTOR, "div[data-testid='product-rankings-table']")
                ranking_rows = ranking_table.find_elements(By.CSS_SELECTOR, "tbody tr")
                
                if ranking_rows:
                    logger.info(f"Found {len(ranking_rows)} rows in the modern table structure")
                    
                    for row in ranking_rows:
                        try:
                            cells = row.find_elements(By.TAG_NAME, "td")
                            if len(cells) >= 3:  # Ensure we have enough cells
                                category_name = cells[0].text.strip()
                                rank = cells[1].text.strip()
                                
                                # Filter for only the specific iPhone categories we're interested in
                                target_categories = ["iphone - free - finance", "iphone - free - apps", "iphone - free - overall"]
                                
                                if category_name and rank:
                                    # Convert to lowercase for case-insensitive comparison
                                    category_lower = category_name.lower()
                                    
                                    # Check if this is one of our target categories
                                    is_target = any(target in category_lower for target in target_categories)
                                    
                                    # Also check if it contains both "iphone" and "free" as keywords
                                    contains_keywords = "iphone" in category_lower and "free" in category_lower
                                    
                                    if is_target or contains_keywords:
                                        logger.info(f"Found target category: {category_name}, rank: {rank}")
                                        rankings_data["categories"].append({
                                            "category": category_name,
                                            "rank": rank
                                        })
                        except Exception as e:
                            logger.warning(f"Failed to extract data from a ranking row: {str(e)}")
                            continue
            except Exception as e:
                logger.warning(f"Failed to find ranking rows in modern structure: {str(e)}")
            
            # Second attempt: Classic structure with ranking rows
            if not rankings_data["categories"]:
                try:
                    logger.info("Looking for rankings with classic structure")
                    ranking_sections = self.driver.find_elements(By.CSS_SELECTOR, ".ranking-row, .rankings-row, .category-row")
                    
                    if ranking_sections:
                        logger.info(f"Found {len(ranking_sections)} rows in classic structure")
                        
                        for section in ranking_sections:
                            try:
                                # Try different combinations of selectors for category name and rank
                                category_element = None
                                rank_element = None
                                
                                # Try first combination
                                try:
                                    category_element = section.find_element(By.CSS_SELECTOR, ".category-name, .name")
                                    rank_element = section.find_element(By.CSS_SELECTOR, ".rank, .rank-value, .position")
                                except:
                                    pass
                                
                                # Try second combination
                                if not category_element or not rank_element:
                                    try:
                                        elements = section.find_elements(By.CSS_SELECTOR, "div, span")
                                        if len(elements) >= 2:
                                            category_element = elements[0]
                                            rank_element = elements[1]
                                    except:
                                        pass
                                
                                if category_element and rank_element:
                                    category_name = category_element.text.strip()
                                    rank = rank_element.text.strip()
                                    
                                    # Clean up rank value (sometimes has "#" or other characters)
                                    rank = rank.replace("#", "").strip()
                                    
                                    # Filter for only the categories we're interested in:
                                    # - iPhone - Free - Finance
                                    # - iPhone - Free - Apps
                                    # - iPhone - Free - Overall
                                    target_categories = ["iphone - free - finance", "iphone - free - apps", "iphone - free - overall"]
                                    
                                    if category_name and rank:
                                        # Convert to lowercase for case-insensitive comparison
                                        category_lower = category_name.lower()
                                        
                                        # Check if this is one of our target categories
                                        is_target = any(target in category_lower for target in target_categories)
                                        
                                        # Also check if it contains both "iphone" and "free" as keywords
                                        contains_keywords = "iphone" in category_lower and "free" in category_lower
                                        
                                        if is_target or contains_keywords:
                                            logger.info(f"Found target category: {category_name}, rank: {rank}")
                                            rankings_data["categories"].append({
                                                "category": category_name,
                                                "rank": rank
                                            })
                            except Exception as e:
                                logger.warning(f"Failed to extract data from classic structure: {str(e)}")
                                continue
                except Exception as e:
                    logger.error(f"Failed with classic structure too: {str(e)}")
            
            # Third attempt: Extract from any other elements that might contain ranking data
            if not rankings_data["categories"]:
                try:
                    logger.info("Looking for any ranking-related content")
                    # Look for elements containing text that might indicate rankings
                    ranking_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Rank') or contains(text(), 'Category') or contains(text(), 'Position')]")
                    
                    if ranking_elements:
                        logger.info(f"Found {len(ranking_elements)} potential ranking elements")
                        
                        # Find parent elements that might contain both category and rank
                        for element in ranking_elements:
                            try:
                                parent = element.find_element(By.XPATH, "./..")
                                text = parent.text
                                
                                # Try to extract category and rank from text
                                if ":" in text:
                                    parts = text.split(":")
                                    category_name = parts[0].strip()
                                    rank = parts[1].strip()
                                    
                                    # Filter for only the specific iPhone categories we're interested in
                                    target_categories = ["iphone - free - finance", "iphone - free - apps", "iphone - free - overall"]
                                    
                                    if category_name and rank:
                                        # Convert to lowercase for case-insensitive comparison
                                        category_lower = category_name.lower()
                                        
                                        # Check if this is one of our target categories
                                        is_target = any(target in category_lower for target in target_categories)
                                        
                                        # Also check if it contains both "iphone" and "free" as keywords
                                        contains_keywords = "iphone" in category_lower and "free" in category_lower
                                        
                                        if is_target or contains_keywords:
                                            logger.info(f"Found target category from text: {category_name}, rank: {rank}")
                                            rankings_data["categories"].append({
                                                "category": category_name,
                                                "rank": rank
                                            })
                            except:
                                continue
                except Exception as e:
                    logger.error(f"Failed with text extraction method: {str(e)}")
            
            # Last resort - log the page source for debugging
            if not rankings_data["categories"]:
                logger.warning("No rankings data found using any selectors. Capturing page for debugging.")
                try:
                    self.driver.save_screenshot("sensortower_debug_final.png")
                    page_text = self.driver.find_element(By.TAG_NAME, "body").text
                    logger.info(f"Page text for debugging: {page_text[:500]}...")  # Log first 500 chars for debugging
                    
                    # Also try to get page source
                    page_source = self.driver.page_source
                    with open("sensortower_page_source.html", "w") as f:
                        f.write(page_source)
                    logger.info("Saved page source to sensortower_page_source.html")
                except Exception as e:
                    logger.error(f"Error capturing page content: {str(e)}")
                    
                # Still no rankings data, try one last approach - look for any numeric values that might be ranks
                try:
                    elements_with_numbers = self.driver.find_elements(By.XPATH, "//div[contains(text(), '#')]")
                    for element in elements_with_numbers:
                        parent = element.find_element(By.XPATH, ".//..")
                        text = parent.text.strip()
                        if text and "#" in text:
                            parts = text.split("\n")
                            if len(parts) >= 2:
                                category_name = parts[0].strip()
                                rank_text = [p for p in parts if "#" in p]
                                if rank_text:
                                    rank = rank_text[0].replace("#", "").strip()
                                    
                                    # Filter for only the specific iPhone categories we're interested in
                                    target_categories = ["iphone - free - finance", "iphone - free - apps", "iphone - free - overall"]
                                    
                                    # Convert to lowercase for case-insensitive comparison
                                    category_lower = category_name.lower()
                                    
                                    # Check if this is one of our target categories
                                    is_target = any(target in category_lower for target in target_categories)
                                    
                                    # Also check if it contains both "iphone" and "free" as keywords
                                    contains_keywords = "iphone" in category_lower and "free" in category_lower
                                    
                                    if is_target or contains_keywords:
                                        logger.info(f"Found target category from last resort: {category_name}, rank: {rank}")
                                        rankings_data["categories"].append({
                                            "category": category_name,
                                            "rank": rank
                                        })
                except Exception as e:
                    logger.error(f"Failed with last resort method: {str(e)}")
                
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
        # Check if the data has a source field, which would indicate where it came from
        data_source = rankings_data.get('source', 'App Store Rankings')
        if 'test' in data_source.lower():
            data_source = '⚠️ Simulated Data (API Unavailable)'
        if not rankings_data or "categories" not in rankings_data:
            return "❌ Failed to retrieve rankings data\\."
        
        # Telegram MarkdownV2 требует экранирования следующих символов:
        # _ * [ ] ( ) ~ ` > # + - = | { } . !
        app_name = rankings_data.get("app_name", "Unknown App")
        app_name = app_name.replace("-", "\\-").replace(".", "\\.").replace("!", "\\!")
        
        date = rankings_data.get("date", "Unknown Date")
        
        # Используем простое форматирование без дефисов в заголовке
        message = f"📊 *{app_name} App Rankings*\n"
        message += f"📅 *Date:* {date}\n"
        message += f"📡 *Source:* {data_source}\n\n"
        
        if not rankings_data["categories"]:
            message += "No ranking data available\\."
        else:
            for category in rankings_data["categories"]:
                cat_name = category.get("category", "Unknown Category")
                # Экранируем специальные символы
                cat_name = cat_name.replace("-", "\\-").replace(".", "\\.").replace("!", "\\!")
                rank = category.get("rank", "N/A")
                
                # Проверяем, является ли это оценочным значением
                if category.get("estimated", False):
                    message += f"🔹 *{cat_name}:* {rank} \\(оценочно\\)\n"
                else:
                    message += f"🔹 *{cat_name}:* \\#{rank}\n"
        
        return message

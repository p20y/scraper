from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import html2text
import time
import random
from datetime import datetime
import logging
import os
import asyncio
import json
import platform
import re
import uuid
import traceback

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for session management
current_driver = None
last_search_time = None
current_session_id = None
SEARCH_TIMEOUT = 300  # 5 minutes timeout for search session
driver_lock = False  # Lock to prevent multiple browser instances

# Configure html2text
text_maker = html2text.HTML2Text()
text_maker.ignore_links = True  # Ignore links to reduce output size
text_maker.ignore_images = True  # Ignore images to reduce output size
text_maker.ignore_emphasis = False
text_maker.body_width = 0  # Don't wrap text
text_maker.protect_links = True  # Don't wrap links
text_maker.unicode_snob = True  # Use Unicode characters

def get_random_user_agent():
    """Return a random modern user agent"""
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
    ]
    return random.choice(user_agents)

def setup_driver():
    """Set up and configure Chrome WebDriver with human-like behavior"""
    global current_driver, current_session_id, driver_lock
    
    # If we already have a valid driver, return it
    if current_driver:
        try:
            # Test if driver is still responsive
            current_driver.current_url
            logger.info(f"Reusing existing browser session {current_session_id}")
            return current_driver
        except Exception as e:
            logger.warning(f"Existing driver not responsive: {str(e)}")
            cleanup_driver()
    
    if driver_lock:
        logger.warning("Browser setup already in progress")
        return None
        
    try:
        driver_lock = True
        logger.info("Setting up Chrome WebDriver...")
        chrome_options = Options()
        # chrome_options.add_argument('--headless')  # Commented out for testing
        
        # Basic options
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument(f'--user-agent={get_random_user_agent()}')
        
        # Anti-detection options
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Additional options for more human-like behavior
        chrome_options.add_argument('--disable-notifications')
        chrome_options.add_argument('--disable-popup-blocking')
        chrome_options.add_argument('--disable-infobars')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--disable-features=IsolateOrigins,site-per-process')
        chrome_options.add_argument('--disable-browser-side-navigation')
        chrome_options.add_argument('--disable-features=TranslateUI')
        chrome_options.add_argument('--disable-features=NetworkService')
        
        service = Service(ChromeDriverManager().install())
        current_driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Generate a new session ID
        current_session_id = str(uuid.uuid4())
        logger.info(f"Created new browser session with ID: {current_session_id}")
        
        # Test the driver
        logger.info("Testing Chrome WebDriver...")
        current_driver.get("about:blank")
        
        logger.info("Successfully created and tested Chrome WebDriver instance")
        return current_driver
    except Exception as e:
        logger.error(f"Failed to setup Chrome driver: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        cleanup_driver()
        return None
    finally:
        driver_lock = False

def cleanup_driver():
    """Clean up the current driver instance"""
    global current_driver, last_search_time, current_session_id
    if current_driver:
        try:
            logger.info(f"Cleaning up browser session with ID: {current_session_id}")
            current_driver.quit()
        except Exception as e:
            logger.error(f"Error during driver cleanup: {str(e)}")
        finally:
            current_driver = None
            last_search_time = None
            current_session_id = None

def is_search_session_valid():
    """Check if the current search session is still valid"""
    global last_search_time, current_driver, current_session_id
    if not current_driver or not last_search_time or not current_session_id:
        logger.warning("No active search session found")
        return False
    
    try:
        # Test if driver is still responsive
        current_driver.current_url
        current_time = time.time()
        if current_time - last_search_time > SEARCH_TIMEOUT:
            logger.warning(f"Search session {current_session_id} expired")
            cleanup_driver()
            return False
        return True
    except Exception as e:
        logger.warning(f"Driver for session {current_session_id} is no longer responsive: {str(e)}")
        cleanup_driver()
        return False

def get_current_driver():
    """Get the current driver instance"""
    global current_driver
    return current_driver

def update_search_time():
    """Update the last search time"""
    global last_search_time
    last_search_time = time.time()

def human_like_mouse_movement(driver, element):
    """Simulate human-like mouse movement to an element"""
    action = ActionChains(driver)
    action.move_to_element(element)
    action.pause(random.uniform(0.1, 0.3))
    action.perform()

def human_like_typing(element, text):
    """Simulate human-like typing with random delays"""
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(0.1, 0.3))

def human_like_scroll(driver):
    """Simulate human-like scrolling behavior"""
    # Get page height
    page_height = driver.execute_script("return document.body.scrollHeight")
    viewport_height = driver.execute_script("return window.innerHeight")
    
    # Scroll in chunks with random pauses
    current_position = 0
    while current_position < page_height:
        # Random scroll amount
        scroll_amount = random.randint(100, 300)
        current_position += scroll_amount
        
        # Scroll
        driver.execute_script(f"window.scrollTo(0, {current_position});")
        
        # Random pause
        time.sleep(random.uniform(0.5, 1.5))
        
        # Sometimes scroll back up a bit
        if random.random() < 0.2:
            current_position -= random.randint(50, 150)
            driver.execute_script(f"window.scrollTo(0, {current_position});")
            time.sleep(random.uniform(0.3, 0.7))

def handle_captcha(driver, max_retries=3):
    """Handle CAPTCHA with more sophisticated strategies"""
    for attempt in range(max_retries):
        try:
            # Check for various CAPTCHA indicators
            captcha_indicators = [
                "captcha",
                "robot check",
                "verify you're a human",
                "enter the characters you see",
                "type the characters you see",
                "security check",
                "prove you're not a robot"
            ]
            
            page_source = driver.page_source.lower()
            is_captcha = any(indicator in page_source for indicator in captcha_indicators)
            
            if is_captcha:
                logger.warning(f"CAPTCHA detected (attempt {attempt + 1}/{max_retries})")
                
                # Take a screenshot for debugging
                try:
                    screenshot_path = f"captcha_screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    driver.save_screenshot(screenshot_path)
                    logger.info(f"Saved CAPTCHA screenshot to {screenshot_path}")
                except Exception as e:
                    logger.error(f"Failed to save screenshot: {str(e)}")
                
                # Try multiple sophisticated strategies to bypass CAPTCHA
                strategies = [
                    # Strategy 1: Refresh with different parameters
                    lambda: driver.get(f"{driver.current_url}?{random.randint(1000, 9999)}"),
                    # Strategy 2: Clear cookies and refresh
                    lambda: (driver.delete_all_cookies(), driver.refresh()),
                    # Strategy 3: Go to homepage and wait
                    lambda: (driver.get('https://www.amazon.com'), time.sleep(random.uniform(3, 5))),
                    # Strategy 4: Back/Forward with delay
                    lambda: (driver.back(), time.sleep(random.uniform(2, 4)), driver.forward()),
                    # Strategy 5: JavaScript redirect with random delay
                    lambda: (driver.execute_script("window.location.href = 'https://www.amazon.com'"), time.sleep(random.uniform(2, 4)))
                ]
                
                # Try strategies in random order
                random.shuffle(strategies)
                for strategy in strategies:
                    try:
                        logger.info("Trying CAPTCHA bypass strategy...")
                        strategy()
                        time.sleep(random.uniform(3, 5))
                        
                        # Check if CAPTCHA is still present
                        if not any(indicator in driver.page_source.lower() for indicator in captcha_indicators):
                            logger.info("CAPTCHA bypass successful!")
                            return True
                    except Exception as e:
                        logger.error(f"Strategy failed: {str(e)}")
                        continue
                
                # If all strategies fail, try one last refresh with different user agent
                if attempt < max_retries - 1:
                    logger.info("All strategies failed, trying with different user agent...")
                    driver.execute_script(f"Object.defineProperty(navigator, 'userAgent', {{get: () => '{get_random_user_agent()}'}});")
                    driver.refresh()
                    time.sleep(random.uniform(5, 8))
                else:
                    raise Exception("All CAPTCHA bypass strategies failed")
            
            # If no CAPTCHA, proceed
            return True
            
        except Exception as e:
            logger.error(f"Error handling CAPTCHA: {str(e)}")
            if attempt == max_retries - 1:
                raise
            time.sleep(random.uniform(5, 10))
    
    return False

async def add_sponsored_products_to_cart(max_products=6):
    """Add sponsored products to cart"""
    global current_driver, last_search_time, current_session_id
    
    try:
        # Check if we have a valid session
        if not is_search_session_valid():
            raise Exception("No valid search session found. Please perform a search first.")
            
        logger.info(f"Adding up to {max_products} sponsored products to cart")
        
        # Find sponsored products using multiple selectors
        sponsored_selectors = [
            'div[data-component-type="s-search-result"] .s-label-popover-default',
            'div[data-component-type="s-sponsored"]',
            'div[data-component-type="sponsored-products"]'
        ]
        
        sponsored_products = []
        for selector in sponsored_selectors:
            try:
                products = current_driver.find_elements(By.CSS_SELECTOR, selector)
                if products:
                    sponsored_products.extend(products)
                    break
            except Exception as e:
                logger.warning(f"Failed to find products with selector {selector}: {str(e)}")
                continue
        
        if not sponsored_products:
            logger.warning("No sponsored products found")
            return 0
            
        logger.info(f"Found {len(sponsored_products)} sponsored products")
        added_count = 0
        
        for product in sponsored_products[:max_products]:
            try:
                # Find the add to cart button using multiple selectors
                cart_button_selectors = [
                    './/ancestor::div[contains(@class, "s-search-result")]//input[@value="Add to Cart"]',
                    './/ancestor::div[contains(@class, "s-search-result")]//input[@title="Add to Cart"]',
                    './/ancestor::div[contains(@class, "s-search-result")]//input[@title="Add to Shopping Cart"]',
                    './/ancestor::div[contains(@class, "s-search-result")]//input[@aria-label="Add to Cart"]'
                ]
                
                add_to_cart = None
                for selector in cart_button_selectors:
                    try:
                        add_to_cart = product.find_element(By.XPATH, selector)
                        if add_to_cart:
                            break
                    except:
                        continue
                
                if not add_to_cart:
                    logger.warning("Could not find Add to Cart button for product")
                    continue
                
                # Scroll to the button
                current_driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", add_to_cart)
                time.sleep(random.uniform(1, 2))
                
                # Click the button with human-like behavior
                human_like_mouse_movement(current_driver, add_to_cart)
                time.sleep(random.uniform(0.5, 1))
                
                try:
                    add_to_cart.click()
                except:
                    # If direct click fails, try JavaScript click
                    current_driver.execute_script("arguments[0].click();", add_to_cart)
                
                # Wait for confirmation
                confirmation_selectors = [
                    '#nav-cart-count',
                    '.a-size-medium-plus.a-color-base.sw-atc-text',
                    '.a-size-medium.a-color-base.sw-atc-text',
                    '.a-alert-container .a-alert-content'
                ]
                
                confirmed = False
                for selector in confirmation_selectors:
                    try:
                        WebDriverWait(current_driver, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                        confirmed = True
                        break
                    except:
                        continue
                
                if confirmed:
                    added_count += 1
                    logger.info(f"Successfully added product {added_count} to cart")
                else:
                    logger.warning("Could not confirm if product was added to cart")
                
                # Random delay between adds
                time.sleep(random.uniform(2, 4))
                
            except Exception as e:
                logger.warning(f"Failed to add product to cart: {str(e)}")
                continue
        
        return added_count
        
    except Exception as e:
        logger.error(f"Error adding to cart: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        cleanup_driver()
        raise

async def get_amazon_search_results(search_term):
    """Search Amazon and return results"""
    global current_driver, last_search_time, current_session_id
    
    try:
        # Get or create driver
        driver = setup_driver()
        if not driver:
            raise Exception("Failed to setup browser")
            
        logger.info(f"Starting search for: {search_term}")
        
        # Navigate to Amazon
        driver.get("https://www.amazon.com")
        time.sleep(random.uniform(2, 4))
        
        # Search for the term
        search_box = driver.find_element(By.ID, "twotabsearchtextbox")
        human_like_typing(search_box, search_term)
        search_box.send_keys(Keys.RETURN)
        time.sleep(random.uniform(3, 5))
        
        # Update search time
        update_search_time()
        
        # Get search results
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        results = []
        
        # Process search results
        for item in soup.select('div[data-component-type="s-search-result"]'):
            try:
                title = item.select_one('h2 a span')
                price = item.select_one('.a-price .a-offscreen')
                rating = item.select_one('.a-icon-star-small .a-icon-alt')
                sponsored = bool(item.select_one('.s-label-popover-default'))
                
                if title and price:
                    result = {
                        'title': title.text.strip(),
                        'price': price.text.strip(),
                        'rating': rating.text.strip() if rating else 'No rating',
                        'sponsored': sponsored
                    }
                    results.append(result)
            except Exception as e:
                logger.warning(f"Error processing search result: {str(e)}")
                continue
        
        # Format results
        formatted_results = "## Search Results\n\n"
        for i, result in enumerate(results[:10], 1):
            formatted_results += f"{i}. **{result['title']}**\n"
            formatted_results += f"   - Price: {result['price']}\n"
            formatted_results += f"   - Rating: {result['rating']}\n"
            formatted_results += f"   - Sponsored: {'Yes' if result['sponsored'] else 'No'}\n\n"
        
        return formatted_results, len(results)
        
    except Exception as e:
        logger.error(f"Error in search: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        cleanup_driver()
        raise

def save_to_markdown(content, filename):
    """Save content to a markdown file"""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    logger.info(f"Results saved to {filename}")

async def main():
    """Main function to test the scraper"""
    search_term = input("Enter search term: ")
    results, driver = await get_amazon_search_results(search_term)
    if results:
        filename = f"amazon_search_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        save_to_markdown(results, filename)
        print(f"\nResults saved to {filename}")

    results, driver = await add_sponsored_products_to_cart(4)

if __name__ == "__main__":
    asyncio.run(main()) 
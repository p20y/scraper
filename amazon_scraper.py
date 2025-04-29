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
from Screenshot import Screenshot

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG level
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Print to console only
    ]
)
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
    last_search_time = time.sleep(random.uniform(0.5, 1.5))

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

def take_fullpage_screenshot(driver, output_path):
    """Take a full-page screenshot using Chrome DevTools Protocol"""
    try:
        # Get the page dimensions
        metrics = driver.execute_cdp_cmd('Page.getLayoutMetrics', {})
        width = metrics['contentSize']['width']
        height = metrics['contentSize']['height']
        
        logger.debug(f"Page dimensions: {width}x{height}")
        
        # Set device metrics
        driver.execute_cdp_cmd('Emulation.setDeviceMetricsOverride', {
            "mobile": False,
            "width": width,
            "height": height,
            "deviceScaleFactor": 1,
        })
        
        # Capture screenshot
        screenshot = driver.execute_cdp_cmd('Page.captureScreenshot', {
            'fromSurface': True,
            'captureBeyondViewport': True
        })
        
        # Save it
        with open(output_path, 'wb') as f:
            f.write(bytes.fromhex(screenshot['data']))
            
        logger.debug(f"Screenshot saved to {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error taking full-page screenshot: {str(e)}")
        return False

async def perform_amazon_search(driver, search_term):
    """Perform a search on Amazon with retry mechanism and CAPTCHA handling

    Args:
        driver: Selenium WebDriver instance
        search_term (str): The search term to use

    Returns:
        bool: True if search was successful, False otherwise
    """
    try:
        # First perform the search with retry mechanism
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Navigate to Amazon
                driver.get("https://www.amazon.com")
                time.sleep(random.uniform(2, 4))
                
                # Try to find search box
                try:
                    search_box = driver.find_element(By.ID, "twotabsearchtextbox")
                    if search_box:
                        logger.debug("Found search box")
                        break
                except:
                    logger.warning(f"Attempt {attempt + 1}: Could not find search box, refreshing page...")
                    driver.refresh()
                    time.sleep(random.uniform(3, 5))
                    continue
                    
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1}: Error accessing Amazon: {str(e)}")
                if attempt < max_retries - 1:
                    driver.refresh()
                    time.sleep(random.uniform(3, 5))
                else:
                    raise Exception("Failed to access Amazon after multiple attempts")
        
        # If we still don't have a search box after all retries, raise an error
        try:
            search_box = driver.find_element(By.ID, "twotabsearchtextbox")
        except:
            raise Exception("Could not find search box after multiple attempts")
        
        # Search for the term
        human_like_typing(search_box, search_term)
        search_box.send_keys(Keys.RETURN)
        time.sleep(random.uniform(3, 5))
        
        return True
        
    except Exception as e:
        logger.error(f"Error performing search: {str(e)}")
        return False

async def get_amazon_search_results(search_term):

    """Search Amazon and return results"""
    driver = None
    try:
        # Setup new driver instance
        driver = setup_driver()
        if not driver:
            raise Exception("Failed to setup browser")
            
        logger.info(f"Starting search for: {search_term}")
        
        # Perform the search
        if not await perform_amazon_search(driver, search_term):
            raise Exception("Failed to perform search")
        
        # Scroll through the page to load all results
        last_height = driver.execute_script("return document.body.scrollHeight")
        results = []
        seen_products = set()  # To avoid duplicates
        
        while True:
            # Scroll down
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(2, 4))
            
            # Get current page source
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Process search results
            for item in soup.select('div[data-component-type="s-search-result"]'):
                try:
                    # Try multiple selectors for title and link
                    title_element = None
                    title_selectors = [
                        'h2 a',
                        'h2 span',
                        'a.a-link-normal.a-text-normal'
                    ]
                    
                    for title_selector in title_selectors:
                        title_element = item.select_one(title_selector)
                        if title_element:
                            break
                    
                    if not title_element:
                        continue
                        
                    title = title_element.text.strip()
                    if not title:
                        continue
                        
                    # Skip if we've already seen this product
                    if title in seen_products:
                        continue
                    seen_products.add(title)
                        
                    # Get product link
                    link = title_element.get('href', '')
                    if link and not link.startswith('http'):
                        link = f"https://www.amazon.com{link}"
                        
                    # Try multiple selectors for price
                    price = None
                    price_selectors = [
                        '.a-price .a-offscreen',
                        '.a-price span',
                        '.a-color-price'
                    ]
                    
                    for price_selector in price_selectors:
                        price_element = item.select_one(price_selector)
                        if price_element:
                            price = price_element.text.strip()
                            break
                            
                    if not price:
                        continue
                        
                    # Get number of reviews
                    num_reviews = None
                    
                    try:
                        # Find the reviews block
                        reviews_block = item.select_one("div[data-cy='reviews-block']")
                        if reviews_block:
                            # Get number of ratings from aria-label
                            ratings_elem = reviews_block.select_one("a[aria-label*='ratings']")
                            if ratings_elem:
                                ratings_text = ratings_elem.get('aria-label', '')
                                logger.debug(f"Found ratings text: {ratings_text}")
                                # Extract just the number from "119,455 ratings"
                                num_reviews = ratings_text.split()[0].replace(',', '')
                                logger.debug(f"Extracted review count: {num_reviews}")
                            else:
                                # Fallback to abbreviated count in parentheses
                                review_abbr = reviews_block.select_one("span.a-size-small.puis-normal-weight-text.s-underline-text")
                                if review_abbr:
                                    review_text = review_abbr.text.strip('()')
                                    logger.debug(f"Found abbreviated review text: {review_text}")
                                    # Convert K/M to actual numbers
                                    if 'K' in review_text:
                                        num_reviews = str(int(float(review_text.replace('K', '')) * 1000))
                                    elif 'M' in review_text:
                                        num_reviews = str(int(float(review_text.replace('M', '')) * 1000000))
                                    else:
                                        num_reviews = review_text
                                    logger.debug(f"Converted review count: {num_reviews}")
                            
                            # Get number of repeat buyers
                            repeat_buyers_elem = reviews_block.select_one("span.a-size-base.a-color-secondary")
                            if repeat_buyers_elem:
                                repeat_buyers_text = repeat_buyers_elem.text.strip()
                                logger.debug(f"Found repeat buyers text: {repeat_buyers_text}")
                                if 'bought multiple times' in repeat_buyers_text:
                                    # Extract the number and convert K/M to actual numbers
                                    num_text = repeat_buyers_text.split()[0]
                                    if 'K' in num_text:
                                        num_buyers = str(int(float(num_text.replace('K', '')) * 1000))
                                    elif 'M' in num_text:
                                        num_buyers = str(int(float(num_text.replace('M', '')) * 1000000))
                                    else:
                                        num_buyers = num_text
                                    logger.debug(f"Extracted repeat buyers: {num_buyers}")
                    except Exception as e:
                        logger.warning(f"Error extracting reviews: {str(e)}")
                    
                    # Check if sponsored
                    sponsored = False
                    sponsored_selectors = [
                        '.s-label-popover-default',  # Sponsored label
                        'div[data-component-type="sp-sponsored-result"]',  # Sponsored result container
                        'div[data-component-type="sp-sponsored-product"]',  # Sponsored product container
                        'div[data-component-type="sp-sponsored"]',  # Generic sponsored container
                        'span[data-component-type="sp-sponsored-label"]',  # Sponsored label span
                        'span[class*="sponsored"]',  # Any span with sponsored in class
                        'div[class*="sponsored"]',  # Any div with sponsored in class
                        'div[class*="AdHolder"]',  # Ad holder container
                        'div[data-cel-widget*="sponsored"]'  # Sponsored widget
                    ]
                    
                    # Check each selector
                    for selector in sponsored_selectors:
                        if item.select_one(selector):
                            sponsored = True
                            break
                    
                    # Also check for sponsored text in the product HTML
                    if not sponsored:
                        product_html = str(item)
                        sponsored_keywords = ['sponsored', 'advertisement', 'ad', 'sponsored product']
                        if any(keyword in product_html.lower() for keyword in sponsored_keywords):
                            sponsored = True
                    
                    # Get product ASIN
                    asin = item.get('data-asin', '')
                    if not asin:
                        # Try to find ASIN in the product link
                        try:
                            link_parts = link.split('/')
                            for part in link_parts:
                                if part.startswith('B0'):
                                    asin = part
                                    break
                        except:
                            asin = 'Not available'
                    
                    # Get search rank
                    rank = item.get('data-index', '')
                    if not rank:
                        # Try to find rank from parent elements
                        try:
                            parent = item.find_parent('div', {'data-index': True})
                            if parent:
                                rank = parent.get('data-index', '')
                        except:
                            rank = 'Not available'
                    
                    result = {
                        'title': title,
                        'price': price,
                        'num_reviews': num_reviews if num_reviews else 'No reviews',
                        'sponsored': sponsored,
                        'asin': asin,
                        'rank': rank
                    }
                    
                    logger.debug(f"Found product: {result['title']} - {result['price']} - {result['num_reviews']} reviews - ASIN: {result['asin']} - Rank: {result['rank']}")
                    results.append(result)
                    
                except Exception as e:
                    logger.warning(f"Error processing search result: {str(e)}")
                    continue
            
            # Check if we've reached the end of the page
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                # Try to find and click the "Next" button
                try:
                    next_button = driver.find_element(By.CSS_SELECTOR, '.s-pagination-next')
                    if next_button and not next_button.get_attribute('aria-disabled'):
                        next_button.click()
                        time.sleep(random.uniform(3, 5))
                        last_height = driver.execute_script("return document.body.scrollHeight")
                        continue
                except:
                    pass
                break
            last_height = new_height
        
        if not results:
            logger.warning("No products found")
            # Save the page source for debugging
            with open('debug_page_source.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            logger.info("Saved page source to debug_page_source.html")
        
        # Format results
        formatted_results = "## Search Results\n\n"
        for i, result in enumerate(results, 1):
            formatted_results += f"{i}. **{result['title']}**\n"
            formatted_results += f"   - Price: {result['price']}\n"
            formatted_results += f"   - Number of Reviews: {result['num_reviews']}\n"
            formatted_results += f"   - Sponsored: {'Yes' if result['sponsored'] else 'No'}\n"
            formatted_results += f"   - ASIN: {result['asin']}\n"
            formatted_results += f"   - Rank: {result['rank']}\n\n"
        
        return formatted_results, len(results)
        
    except Exception as e:
        logger.error(f"Error in search: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise

async def add_top_sponsored_products_to_cart(search_term, number_of_products):
    driver = None
    added_products = []  # List to store titles of successfully added products
    try:
        # Setup driver using the existing setup_driver method
        driver = setup_driver()
        if not driver:
            raise Exception("Failed to setup browser")
            
        logger.info(f"Starting search for sponsored products: {search_term}")
        
        # Construct Amazon search URL from search term
        search_term_encoded = search_term.replace(' ', '+')
        amazon_url = f"https://www.amazon.com/s?k={search_term_encoded}"
        driver.get(amazon_url)
        
        # Wait for page to load
        wait = WebDriverWait(driver, 15)
        logger.info("Waiting for page to load...")
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.s-main-slot")))
        logger.info("Page loaded successfully")
        
        # Check for captcha
        if not handle_captcha(driver):
            raise Exception("Failed to handle CAPTCHA")
        
        # Print the page title for debugging
        logger.info(f"Page title: {driver.title}")
        
        # Find all sponsored products using the exact HTML structure
        sponsored_selectors = [
            'div[class*="a-section"][class*="a-spacing-small"][class*="puis-padding-left-small"][class*="puis-padding-right-small"]',  # Main sponsored container
            'div[class*="puis-card-container"]'  # Card container
        ]
        
        sponsored_products = []  # Store both product info and add to cart button
        for selector in sponsored_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                logger.info(f"Found {len(elements)} elements with selector: {selector}")
                
                for element in elements:
                    try:
                        # Look for the "Sponsored" label with the exact class structure
                        sponsored_label = element.find_elements(By.CSS_SELECTOR, 'a[class="puis-label-popover puis-sponsored-label-text"] span[class="puis-label-popover-default"] span[class="a-color-secondary"]')
                        if sponsored_label:
                            # Verify the label actually says "Sponsored"
                            label_text = sponsored_label[0].text.strip()
                            if label_text.lower() != "sponsored":
                                continue
                                
                            # Get product link
                            product_link = element.find_element(By.CSS_SELECTOR, 'a[class="a-link-normal s-line-clamp-3 s-link-style a-text-normal"]').get_attribute("href")
                            # Get product title
                            product_title = element.find_element(By.CSS_SELECTOR, 'h2[class*="a-size-base-plus"] span').text
                            # Get Add to Cart button
                            add_to_cart = element.find_element(By.CSS_SELECTOR, 'button[name="submit.addToCart"]')
                            
                            if product_link and add_to_cart:
                                product_info = {
                                    'link': product_link,
                                    'title': product_title,
                                    'add_to_cart_button': add_to_cart
                                }
                                sponsored_products.append(product_info)
                                logger.info(f"Found sponsored product: {product_title}")
                                logger.info(f"Product link: [{product_title}]({product_link})")
                    except Exception as e:
                        logger.warning(f"Error processing element: {e}")
                        continue
            except Exception as e:
                logger.warning(f"Error with selector {selector}: {e}")
                continue

        logger.info(f"\nFound {len(sponsored_products)} sponsored products with Add to Cart buttons.")

        # Limit to top X
        sponsored_products = sponsored_products[:number_of_products]

        # Print all found products in markdown format
        logger.info("\nSponsored Products Found:")
        for idx, product in enumerate(sponsored_products, 1):
            logger.info(f"{idx}. [{product['title']}]({product['link']})")

        # Click Add to Cart for each product
        for index, product in enumerate(sponsored_products):
            try:
                logger.info(f"\nAdding product {index + 1} to cart: {product['title']}")
                logger.info(f"Product link: [{product['title']}]({product['link']})")
                driver.execute_script("arguments[0].click();", product['add_to_cart_button'])
                logger.info(f"Added product {index + 1} to cart")
                added_products.append(product['title'])  # Add title to list of successfully added products

                # Optional sleep to let Amazon process cart addition
                time.sleep(2)

            except Exception as e:
                logger.error(f"Error adding product {index + 1}: {e}")

        return added_products  # Return list of successfully added product titles

    except Exception as e:
        logger.error(f"Error in add_top_sponsored_products_to_cart: {e}")
        raise
    finally:
        if driver:
            cleanup_driver()

def save_to_markdown(content, filename):
    """Save content to a markdown file"""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    logger.info(f"Results saved to {filename}")

async def main():
    """Main function to test the scraper"""
    try:
        # Get search term from user
        search_term = input("Enter search term: ")
        
        # Perform search and get results
        results, count = await get_amazon_search_results(search_term)
        
        # Save results to markdown file
        if results:
            filename = f"amazon_search_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            save_to_markdown(results, filename)
            print(f"\nResults saved to {filename}")
            print(f"Found {count} products")
        
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")

async def add_sponsored_products_to_cart(asin_list, search_term="sponsored products"):
    """
    Add specific products to cart by their ASINs from search results page.
    If no valid session exists, performs a search first.
    
    Args:
        asin_list: List of ASINs to add to cart
        search_term: Search term to use to find the products (default: "sponsored products")
        
    Returns:
        A list of dictionaries containing information about the products that were added to cart
    """
    try:
        logger.info(f"Processing add to cart request for {len(asin_list)} products")
        added_products = []  # List to store products that were added to cart
        
        # Check if we have a valid session, if not perform a search first
        try:
            # Get the current driver
            driver = get_current_driver()
            if not driver:
                raise Exception("No valid search session found")
                
            # Find and add each product to cart
            for asin in asin_list:
                try:
                    # Find the product element by ASIN
                    product_element = driver.find_element(By.CSS_SELECTOR, f'div[data-asin="{asin}"]')
                    if not product_element:
                        logger.warning(f"Product with ASIN {asin} not found")
                        continue
                        
                    # Get product title
                    title_element = product_element.find_element(By.CSS_SELECTOR, 'h2 span')
                    product_title = title_element.text if title_element else "Unknown Product"
                    
                    # Get product link
                    link_element = product_element.find_element(By.CSS_SELECTOR, 'a.a-link-normal')
                    product_link = link_element.get_attribute('href') if link_element else None
                    
                    # Find and click Add to Cart button
                    add_to_cart_button = product_element.find_element(By.CSS_SELECTOR, 'button[name="submit.addToCart"]')
                    if add_to_cart_button:
                        driver.execute_script("arguments[0].click();", add_to_cart_button)
                        logger.info(f"Added product to cart: {product_title}")
                        
                        # Add product info to the list
                        added_products.append({
                            'title': product_title,
                            'link': product_link,
                            'asin': asin
                        })
                        
                        # Optional sleep to let Amazon process cart addition
                        time.sleep(2)
                    else:
                        logger.warning(f"Add to Cart button not found for product: {product_title}")
                        
                except Exception as e:
                    logger.warning(f"Error adding product {asin} to cart: {e}")
                    continue
                    
        except Exception as e:
            if "No valid search session found" in str(e):
                logger.info("No valid session found, performing search first...")
                # Perform a search to establish a valid session
                await get_amazon_search_results(search_term)
                # Try adding to cart again
                return await add_sponsored_products_to_cart(asin_list, search_term)
            else:
                raise
                
        return added_products  # Return list of products that were added to cart

    except Exception as e:
        logger.error(f"Error adding products to cart: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 
import sys
import logging
from mcp.server.fastmcp import FastMCP
from amazon_scraper import (
    get_amazon_search_results,
    add_sponsored_products_to_cart,
    cleanup_driver,
    setup_driver,
    handle_captcha
)
import traceback
import atexit
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

# Configure logging - set to INFO level and simplify format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(stream=sys.stderr)  # Print to stderr only
    ]
)
logger = logging.getLogger('amazon_scraper')

# Initialize MCP server
logger.info("Initializing MCP server...")
mcp = FastMCP("amazon_scraper")

# Register cleanup on exit
atexit.register(cleanup_driver)

@mcp.tool()
async def search_amazon(search_term: str) -> str:
    """
    Search Amazon for products and return results in markdown format.
    
    Args:
        search_term: The term to search for on Amazon
        
    Returns:
        A markdown formatted string containing the search results
    """
    try:
        # Perform search
        logger.info(f"Processing search for: {search_term}")
        results, count = await get_amazon_search_results(search_term)
        return results
            
    except Exception as e:
        logger.error(f"Error processing search: {str(e)}")
        return f"Error: Search failed - {str(e)}"

@mcp.tool()
async def add_sponsored_products_to_cart(search_term, number_of_products=4):
    driver = None
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

                # Optional sleep to let Amazon process cart addition
                time.sleep(2)

            except Exception as e:
                logger.error(f"Error adding product {index + 1}: {e}")

        return {
            'status': 'success',
            'message': f'Successfully added {len(sponsored_products)} products to cart',
            'products': [{'title': p['title'], 'link': p['link']} for p in sponsored_products]
        }

    except Exception as e:
        logger.error(f"Error in add_to_cart: {e}")
        return {
            'status': 'error',
            'message': str(e)
        }
    finally:
        if driver:
            cleanup_driver()

def run_server():
    """Run the MCP server"""
    try:
        logger.info("Starting server...")
        mcp.run(transport='stdio')
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        cleanup_driver()
        sys.exit(1)

if __name__ == "__main__":
    run_server() 
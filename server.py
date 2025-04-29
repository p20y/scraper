import sys
import logging
from mcp.server.fastmcp import FastMCP
from amazon_scraper import (
    get_amazon_search_results,
    add_sponsored_products_to_cart,
    cleanup_driver,
    setup_driver,
    handle_captcha,
    add_top_sponsored_products_to_cart
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
async def add_sponsored_products_to_cart(search_term: str, number_of_products: int = 4) -> dict:
    """
    Add sponsored products to cart by calling add_top_sponsored_products_to_cart from amazon_scraper.py.
    
    Args:
        search_term: The search term to find sponsored products
        number_of_products: Number of products to add to cart (default: 4)
        
    Returns:
        A dictionary containing the status and list of added products
    """
    try:
        # Validate input parameters
        if not isinstance(search_term, str) or not search_term.strip():
            raise ValueError("search_term must be a non-empty string")
            
        if not isinstance(number_of_products, int) or number_of_products <= 0:
            raise ValueError("number_of_products must be a positive integer")
            
        logger.info(f"Processing add to cart request for {number_of_products} products")
        
        # Call add_top_sponsored_products_to_cart from amazon_scraper.py
        added_products = await add_top_sponsored_products_to_cart(search_term, number_of_products)
        
        # Format response
        response = {
            'status': 'success' if added_products else 'warning',
            'message': f'Successfully added {len(added_products)} products to cart' if added_products else 'No products were added to cart',
            'products': added_products if added_products else []
        }
        
        logger.info(f"Response: {response}")
        return response
            
    except ValueError as ve:
        logger.error(f"Validation error: {str(ve)}")
        return {
            'status': 'error',
            'message': str(ve),
            'products': []
        }
    except Exception as e:
        logger.error(f"Error adding products to cart: {str(e)}")
        return {
            'status': 'error',
            'message': str(e),
            'products': []
        }

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
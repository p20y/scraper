import sys
import logging
from mcp.server.fastmcp import FastMCP
from amazon_scraper import (
    get_amazon_search_results,
    add_sponsored_products_to_cart,
    cleanup_driver
)
import traceback
import atexit

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
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
    """
    logger.debug(f"Received search request for term: {search_term}")
    
    try:
        # Perform search
        logger.info(f"Processing search for: {search_term}")
        results, _ = await get_amazon_search_results(search_term)
        return results
            
    except Exception as e:
        logger.error(f"Error processing search: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return f"Error: Search failed - {str(e)}"

@mcp.tool()
async def add_products_to_cart(max_products: int = 6) -> str:
    """
    Add sponsored products to cart using the existing browser session.
    
    Args:
        max_products: Maximum number of sponsored products to add (default: 6)
    
    Returns:
        A string message indicating the result of the operation
    """
    logger.debug(f"Received request to add {max_products} sponsored products to cart")
    
    try:
        logger.info(f"Processing add to cart request for {max_products} products")
        added_count = await add_sponsored_products_to_cart(max_products)
        
        if added_count > 0:
            return f"Successfully added {added_count} products to cart"
        else:
            return "No products were added to cart"
            
    except Exception as e:
        logger.error(f"Error adding products to cart: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return f"Error: Failed to add products to cart - {str(e)}"

def run_server():
    """Run the MCP server"""
    try:
        logger.info("Starting server...")
        mcp.run(transport='stdio')
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        cleanup_driver()
        sys.exit(1)

if __name__ == "__main__":
    run_server() 
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
import sys
from amazon_scraper import (
    get_amazon_search_results,
    add_top_sponsored_products_to_cart
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(stream=sys.stderr)
    ]
)
logger = logging.getLogger('amazon_scraper')

# Initialize FastAPI app
app = FastAPI(
    title="Amazon Scraper API",
    description="API for searching Amazon and adding sponsored products to cart",
    version="1.0.0"
)

# Define request models
class SearchRequest(BaseModel):
    search_term: str

class AddToCartRequest(BaseModel):
    search_term: str
    number_of_products: int = 4

# Define response models
class SearchResponse(BaseModel):
    results: str
    count: int

class AddToCartResponse(BaseModel):
    status: str
    message: str
    products: List[str]

@app.get("/")
async def root():
    """Root endpoint that returns API information"""
    return {
        "name": "Amazon Scraper API",
        "version": "1.0.0",
        "endpoints": [
            "/search",
            "/add-to-cart"
        ]
    }

@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """
    Search Amazon for products
    
    Args:
        request: SearchRequest containing the search term
        
    Returns:
        SearchResponse containing the search results and count
    """
    try:
        logger.info(f"Processing search request for: {request.search_term}")
        results, count = await get_amazon_search_results(request.search_term)
        return SearchResponse(results=results, count=count)
    except Exception as e:
        logger.error(f"Error processing search: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/add-to-cart", response_model=AddToCartResponse)
async def add_to_cart(request: AddToCartRequest):
    """
    Add sponsored products to cart
    
    Args:
        request: AddToCartRequest containing search term and number of products
        
    Returns:
        AddToCartResponse containing status, message, and list of added product titles
    """
    try:
        logger.info(f"Processing add to cart request for {request.number_of_products} products")
        added_products = await add_top_sponsored_products_to_cart(
            request.search_term,
            request.number_of_products
        )
        
        if added_products:
            return AddToCartResponse(
                status="success",
                message=f"Successfully added {len(added_products)} products to cart",
                products=added_products
            )
        else:
            return AddToCartResponse(
                status="warning",
                message="No products were added to cart",
                products=[]
            )
    except Exception as e:
        logger.error(f"Error adding products to cart: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

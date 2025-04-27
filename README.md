# Amazon Product Scraper

This script scrapes Amazon search results for a given search term and converts them to markdown format.

## Requirements

- Python 3.6 or higher
- Required packages listed in `requirements.txt`

## Installation

1. Clone this repository
2. Install the required packages:
```bash
pip install -r requirements.txt
```

## Usage

Run the script:
```bash
python amazon_scraper.py
```

The script will:
1. Search Amazon for "Lavender oils"
2. Extract product information including:
   - Product title
   - Price
   - Rating
   - Product URL
3. Save the results to `amazon_search_results.md`

## Notes

- The script includes random delays to avoid being blocked by Amazon
- Results are saved in markdown format for easy reading
- The script uses a browser-like user agent to mimic real browser requests 
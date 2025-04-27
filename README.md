# Amazon Scraper

A Python-based web scraper for Amazon that allows searching for products and adding sponsored products to cart.

## Features

- Search Amazon products
- Add sponsored products to cart
- Human-like behavior to avoid detection
- Session management
- Error handling and logging

## Requirements

- Python 3.7+
- Selenium
- Chrome WebDriver
- Other dependencies listed in `requirements.txt`

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/amazonscraper.git
cd amazonscraper
```

2. Create a virtual environment and activate it:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the server:
```bash
python server.py
```

2. Run the test client:
```bash
python simple_test_client.py
```

3. Follow the menu prompts to:
   - Search for products
   - Add sponsored products to cart
   - Exit the program

## Project Structure

- `amazon_scraper.py`: Core scraping functionality
- `server.py`: MCP server implementation
- `simple_test_client.py`: Simple test client for testing functionality
- `test_client.py`: Advanced test client with more features
- `requirements.txt`: Project dependencies

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
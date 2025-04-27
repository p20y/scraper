import asyncio
import sys
from amazon_scraper import (
    get_amazon_search_results,
    add_sponsored_products_to_cart,
    cleanup_driver
)

async def main():
    try:
        while True:
            print("\nAmazon Scraper Test Client")
            print("1. Search Amazon")
            print("2. Add products to cart")
            print("3. Exit")
            
            choice = input("\nEnter your choice (1-3): ").strip()
            
            if choice == "1":
                search_term = input("Enter search term: ").strip()
                if not search_term:
                    print("Error: Search term cannot be empty")
                    continue
                    
                print(f"\nSearching for: {search_term}")
                results, count = await get_amazon_search_results(search_term)
                print("\nSearch Results:")
                print(results)
                print(f"\nTotal products found: {count}")
                
            elif choice == "2":
                try:
                    max_products = int(input("Enter number of products to add (1-20): ").strip())
                    if max_products < 1 or max_products > 20:
                        print("Error: Number must be between 1 and 20")
                        continue
                        
                    print(f"\nAdding {max_products} products to cart...")
                    added_count = await add_sponsored_products_to_cart(max_products)
                    print(f"\nSuccessfully added {added_count} products to cart")
                    
                except ValueError:
                    print("Error: Please enter a valid number")
                except Exception as e:
                    print(f"Error: {str(e)}")
                    
            elif choice == "3":
                print("\nExiting...")
                break
                
            else:
                print("Error: Invalid choice")
                
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        cleanup_driver()

if __name__ == "__main__":
    asyncio.run(main()) 
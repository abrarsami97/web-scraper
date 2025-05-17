from scraper import WebScraper
import json

def main():
    # Example 1: Basic scraping without authentication
    scraper = WebScraper(use_selenium=False)
    try:
        # Scrape a website
        soup = scraper.scrape('https://example.com')
        if soup:
            # Define selectors for the data you want to extract
            selectors = {
                'title': 'h1',
                'paragraphs': 'p',
                'links': 'a'
            }
            
            # Extract the data
            data = scraper.extract_data(soup, selectors)
            
            # Save to JSON
            scraper.save_to_json(data, 'example_data.json')
            print("Data saved to example_data.json")
    finally:
        scraper.close()

    # Example 2: Scraping with authentication
    scraper = WebScraper(use_selenium=True)
    try:
        # Example credentials for a form-based login
        credentials = {
            'username': 'your_username',
            'password': 'your_password',
            'username_field': 'username',  # name attribute of username input
            'password_field': 'password',  # name attribute of password input
            'submit_selector': 'button[type="submit"]'  # CSS selector for submit button
        }
        
        # Authenticate
        if scraper.authenticate('https://example.com/login', 'form', credentials):
            print("Authentication successful!")
            
            # Now you can scrape authenticated pages
            soup = scraper.scrape('https://example.com/protected-page')
            if soup:
                # Define selectors for the protected content
                selectors = {
                    'user_info': '.user-profile',
                    'protected_content': '.content'
                }
                
                # Extract the data
                data = scraper.extract_data(soup, selectors)
                
                # Save to JSON
                scraper.save_to_json(data, 'protected_data.json')
                print("Protected data saved to protected_data.json")
        else:
            print("Authentication failed!")
    finally:
        scraper.close()

if __name__ == '__main__':
    main() 
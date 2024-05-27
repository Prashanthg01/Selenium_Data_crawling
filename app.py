import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urlparse

# Read the product URLs from CSV
product_urls = pd.read_csv('products.csv')['Product_Url'].tolist()

# Set up Selenium WebDriver with Chrome
options = Options()
options.headless = True  # Run headless Chrome
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def get_flipkart_details(url):
    driver.get(url)
    time.sleep(5)  # Wait for the page to load completely

    try:
        # Extracting ratings and reviews
        ratings_reviews_element = driver.find_element(By.CSS_SELECTOR, 'span.Wphh3N span')
        ratings_reviews_text = ratings_reviews_element.text.split('&')
        ratings = ratings_reviews_text[0].strip()
        reviews = ratings_reviews_text[1].strip()

        return {
            'Product URL': url,
            'Ratings': ratings,
            'Reviews': reviews
        }
    except Exception as e:
        print(f"Error extracting data for Flipkart URL: {url}\nError: {e}")
        return {
            'Product URL': url,
            'Ratings': 'N/A',
            'Reviews': 'N/A'
        }

def get_amazon_details(url):
    driver.get(url)
    time.sleep(5)  # Wait for the page to load completely

    try:
        # Navigate to "See more reviews" page
        see_all_reviews_link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[data-hook="see-all-reviews-link-foot"]'))
        )
        see_all_reviews_link.click()

        # Wait for the reviews page to load
        time.sleep(5)

        # Extracting ratings and reviews
        ratings_reviews_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-hook="cr-filter-info-review-rating-count"]'))
        )
        ratings_reviews_text = ratings_reviews_element.text.split(',')
        ratings = ratings_reviews_text[0].strip()
        reviews = ratings_reviews_text[1].strip()

        return {
            'Product URL': url,
            'Ratings': ratings,
            'Reviews': reviews
        }
    except Exception as e:
        print(f"Error extracting data for Amazon URL: {url}\nError: {e}")
        return {
            'Product URL': url,
            'Ratings': 'N/A',
            'Reviews': 'N/A'
        }

# List to store the product details
product_details_list = []

for url in product_urls:
    domain = urlparse(url).netloc
    if 'flipkart.com' in domain:
        product_details = get_flipkart_details(url)
    elif 'amazon.in' in domain:
        product_details = get_amazon_details(url)
    else:
        product_details = {
            'Product URL': url,
            'Ratings': 'N/A',
            'Reviews': 'N/A'
        }
    product_details_list.append(product_details)

# Convert list of dictionaries to DataFrame
products_df = pd.DataFrame(product_details_list)

def clean_and_convert(column):
    # Remove any non-numeric characters and convert to integer
    return column.str.replace(r'[^0-9]', '', regex=True).astype(int)
# Save the DataFrame to a CSV file
products_df['Ratings'] = clean_and_convert(products_df['Ratings'])
products_df['Reviews'] = clean_and_convert(products_df['Reviews'])

products_df.to_csv('product_reviews.csv', index=False)

# Close the WebDriver
driver.quit()

print("Data extraction completed. The details are saved to 'product_reviews.csv'.")

import csv
import requests
from bs4 import BeautifulSoup
import pandas as pd
import logging
import time
from datetime import datetime
from requests.exceptions import HTTPError


# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to fetch and parse the HTML content of a product page
def fetch_product_page(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        logging.info('Page fetched successfully')
        return BeautifulSoup(response.content, 'html.parser')
    else:
        logging.error(f'Failed to fetch page. Status code: {response.status_code}')
        return None

# Function to extract star ratings from the product page
def extract_star_ratings(soup, url):
    ratings_data = []
    
    # Extract number of ratings
    ratings_count_element = soup.select_one('#acrCustomerReviewText')
    if ratings_count_element:
        ratings_count = ratings_count_element.text.strip().split()[0]
        ratings_count = ratings_count.replace(",", "").replace(" ", "")  # Remove commas and spaces
        ratings_count = int(ratings_count)  # Convert to integer
        logging.info(f'Extracted number of ratings: {ratings_count}')
    else:
        logging.warning('Could not find ratings count element')
        return []
    
    rating_elements = soup.select('tr.a-histogram-row')
    for rating_element in rating_elements:
        anchor_tag = rating_element.find('a', class_='a-link-normal')
        if anchor_tag:
            star_rating = anchor_tag.text.strip().replace(' star', '_star')
            rating_percentage = rating_element.find('div', class_='a-meter-bar').get('style').split(':')[1].strip()
            
            rating_percentage = int(rating_percentage.rstrip("%"))
            rating = round((rating_percentage / 100) * ratings_count)
            
            logging.info(f'Extracted rating: {star_rating} with percentage: {rating_percentage}')
            ratings_data.append([url, star_rating, rating])
        else:
            logging.warning('Rating element without anchor tag found, skipping...')
    return ratings_data

def fetch_page(url, retries=3, delay=5):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
    }
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.text
        except HTTPError as e:
            if e.response.status_code == 429:
                logging.warning(f"Rate limit exceeded. Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                raise
    raise HTTPError(f"Failed to fetch URL after {retries} retries")

def extract_flipkart_star_ratings(soup, product_url):
    ratings = {}
    star_elements = soup.select('div.wNNofW ul.G1qQrW li.fQ-FC1 span.Fig8YH')
    rating_elements = soup.select('div.wNNofW ul.lpANVI li.fQ-FC1 div.BArk-j')
    
    if len(star_elements) == len(rating_elements):
        for star, rating in zip(star_elements, rating_elements):
            star_rating = f"{star.text.strip()}_star"
            ratings[star_rating] = rating.text.strip()
            logging.info(f"Extracted rating: {star_rating} with count: {ratings[star_rating]}")
    return [(product_url, star, ratings[star]) for star in ratings]

def crawl_ratings(url):
    page_content = fetch_page(url)
    soup = BeautifulSoup(page_content, 'html.parser')

    if 'amazon' in url:
        soup = fetch_product_page(url)
        return extract_star_ratings(soup, product_url) if soup else ''
    elif 'flipkart' in url:
        return extract_flipkart_star_ratings(soup, url)
    else:
        logging.warning(f"Unknown URL pattern: {url}")
        return []

# Load URLs from CSV
input_file = 'products.csv'
data = []

with open(input_file, newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        product_url = row['Product_Url']
        priority = row['Priority']
        logging.info(f"Fetching URL: {product_url}")
        try:
            ratings_output = crawl_ratings(product_url)
            data.extend(ratings_output)
            time.sleep(2)  # Adding a delay between requests
        except Exception as e:
            logging.error(f"Error processing URL {product_url}: {e}")

# Save results to a CSV file
output_file = 'ratings_output.csv'
date_today = datetime.today().strftime('%Y-%m-%d')
df = pd.DataFrame(data, columns=['URL', 'star_rating', f'ratings({date_today})'])
df.to_csv(output_file, index=False)
logging.info(f"Data saved to {output_file}")

from django.shortcuts import render
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from urllib.robotparser import RobotFileParser
import time



def get_robots_txt(url):
    """Fetch and parse robots.txt for a given URL"""
    try:
        parsed_url = urlparse(url)
        domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
        robots_url = urljoin(domain, '/robots.txt')
        
        response = requests.get(robots_url, timeout=5)
        if response.status_code == 200:
            return response.text
        else:
            return None
    except Exception as e:
        return None

#Check if a URL is allowed by robots.txt
def check_robots_allowed(url):

    try:
        parsed_url = urlparse(url)
        domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        rp = RobotFileParser()
        rp.set_url(urljoin(domain, '/robots.txt'))
        rp.read()
        
        return rp.can_fetch('*', url)
    except Exception as e:
        # If robots.txt doesn't exist or can't be parsed, assume it's allowed
        return True

# Send a GET request to the specified URL and return the HTML content
def get_HTML_content(url):

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise an error for bad responses
        return response.text
    except requests.Timeout:
        return None
    except requests.RequestException as e:
        return f"An error occurred: {e}"

def get_HTML_content_selenium(url, wait_time=5):
    """Fetch HTML content using Selenium for dynamic content"""
    driver = None
    try:
        # Configure Chrome options
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Run in background
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        # Create driver
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(15)
        
        # Navigate to URL
        driver.get(url)
        
        # Wait for page to load (wait for body element)
        WebDriverWait(driver, wait_time).until(
            EC.presence_of_element_located((By.TAG_NAME, 'body'))
        )
        
        # Allow time for JavaScript to render
        time.sleep(2)
        
        # Get rendered HTML
        html_content = driver.page_source
        return html_content
        
    except Exception as e:
        return f"Selenium error: {str(e)}"
    finally:
        if driver:
            driver.quit()
    
def parse_HTML(response):

    try:
        soup = BeautifulSoup(response, 'html.parser')
        return soup
    except Exception as e:
        return None
    
#Extract data from a page based on selected options
def extract_page_data(soup, scrape_options):
    
    data = {}
    
    if scrape_options['title']:
        data['title'] = soup.title.string if soup.title else 'No title found'
    
    if scrape_options['headings']:
        data['headings'] = [h.text for h in soup.find_all(['h1', 'h2', 'h3'])[:5]]
    
    if scrape_options['links']:
        data['links'] = [
            {
                'text': a.get_text(strip=True),
                'href': a.get('href')
            } for a in soup.find_all('a', limit=10)
        ]
    
    if scrape_options['paragraphs']:
        data['paragraphs'] = [p.text[:100] for p in soup.find_all('p')[:3]]
    
    if scrape_options['images']:
        data['images'] = [img.get('src') for img in soup.find_all('img', limit=5)]
    
    return data

#Convert relative URL to absolute URL
def get_absolute_url(base_url, relative_url):
    
    if not relative_url:
        return None
    return urljoin(base_url, relative_url)

# Check if target URL is from the same domain as base URL
def is_same_domain(base_url, target_url):
    
    if not target_url:
        return False
    base_domain = urlparse(base_url).netloc
    target_domain = urlparse(target_url).netloc
    return base_domain == target_domain

#Main view for scraping
def scrape(request):
   
    data = None
    error = None
    
    if request.method == 'POST':
        url = request.POST.get('url', '').strip()
        
        # Get selected scraping options
        scrape_options = {
            'title': request.POST.get('scrape_title') == 'on',
            'headings': request.POST.get('scrape_headings') == 'on',
            'links': request.POST.get('scrape_links') == 'on',
            'paragraphs': request.POST.get('scrape_paragraphs') == 'on',
            'images': request.POST.get('scrape_images') == 'on',
        }
        
        # Get advanced options
        scrape_link_targets = request.POST.get('scrape_link_targets') == 'on'
        use_selenium = request.POST.get('use_selenium') == 'on'
        recursive_depth = int(request.POST.get('recursive_depth', 1))
        
        # Validate URL input
        if not url:
            error = "Please enter a valid URL"
        elif not any(scrape_options.values()):
            error = "Please select at least one option to scrape"
        else:
            try:
                # Check robots.txt
                robots_content = get_robots_txt(url)
                is_allowed = check_robots_allowed(url)
                
                # Start scraping
                data = {
                    'robots_txt': robots_content,
                    'robots_allowed': is_allowed,
                    'fetch_method': 'Selenium (dynamic content)' if use_selenium else 'Requests (static content)',
                }
                visited_urls = set()
                
                # Scrape the main URL - use Selenium or Requests based on user choice
                if use_selenium:
                    html_content = get_HTML_content_selenium(url)
                else:
                    html_content = get_HTML_content(url)
                
                if isinstance(html_content, str) and html_content.startswith("An error"):
                    error = html_content
                elif html_content is None:
                    error = "Failed to parse the webpage"
                else:
                    soup = parse_HTML(html_content)
                    if soup is None:
                        error = "Could not parse HTML content"
                    else:
                        # Extract data from main page
                        main_page_data = extract_page_data(soup, scrape_options)
                        data['main_page'] = {
                            'url': url,
                            'data': main_page_data
                        }
                        visited_urls.add(url)
                        
                        # Scrape link targets if enabled
                        if scrape_link_targets and scrape_options['links'] and recursive_depth > 0:
                            data['linked_pages'] = []
                            
                            # Get links from main page
                            links = soup.find_all('a', limit=5)  # Limit to 5 links to avoid too many requests
                            
                            for link in links:
                                href = link.get('href')
                                if not href:
                                    continue
                                
                                # Convert to absolute URL
                                absolute_url = get_absolute_url(url, href)
                                
                                # Check if it's same domain and not visited
                                if absolute_url and is_same_domain(url, absolute_url) and absolute_url not in visited_urls:
                                    try:
                                        # Fetch and scrape linked page
                                        linked_html = get_HTML_content(absolute_url)
                                        
                                        if linked_html and not isinstance(linked_html, str):
                                            linked_soup = parse_HTML(linked_html)
                                            if linked_soup:
                                                linked_page_data = extract_page_data(linked_soup, scrape_options)
                                                data['linked_pages'].append({
                                                    'url': absolute_url,
                                                    'data': linked_page_data
                                                })
                                                visited_urls.add(absolute_url)
                                    except Exception as e:
                                        # Continue scraping even if one link fails
                                        pass
                            
                            if not data['linked_pages']:
                                del data['linked_pages']
                        
                        data['pages_scraped'] = len(visited_urls)
                        
            except Exception as e:
                error = f"Scraping error: {str(e)}"
    
    context = {
        'data': data,
        'error': error,
    }
    
    return render(request, 'home.html', context)

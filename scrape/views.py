from django.shortcuts import render
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.chrome.options import Options
from urllib.robotparser import RobotFileParser
import time


# Fetch and parse robots.txt for a given URL
def get_robots_txt(url):
    
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
# If robots.txt doesn't exist or can't be parsed, assume it's allowed
def check_robots_allowed(url):

    try:
        parsed_url = urlparse(url)
        domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        rp = RobotFileParser()
        rp.set_url(urljoin(domain, '/robots.txt'))
        rp.read()
        
        return rp.can_fetch('*', url)
    except Exception as e:
        return True


# Search for a phrase in page content, returns a dict 
def search_in_content(search_query, page_data):
    
    if not search_query or not page_data.get('full_text'):
        return None
    
    search_query_lower = search_query.lower()
    full_text = page_data.get('full_text', '')
    text_lower = full_text.lower()
    
    # Find all occurrences
    matches = []
    start = 0
    
    while True:
        position = text_lower.find(search_query_lower, start)
        if position == -1:
            break
        
        # Get context: 100 chars before and after
        context_start = max(0, position - 100)
        context_end = min(len(full_text), position + len(search_query) + 100)
        
        context = full_text[context_start:context_end].strip()
        
        # Add ellipsis if truncated (unsure what this means, Ai did the search function for me)
        if context_start > 0:
            context = '...' + context
        if context_end < len(full_text):
            context = context + '...'
        
        matches.append({
            'context': context,
            'position': position
        })
        
        start = position + 1
    
    if matches:
        return {
            'found': True,
            'count': len(matches),
            'matches': matches[:10]  # Limit to first 10 matches
        }
    else:
        return {
            'found': False,
            'count': 0,
            'matches': []
        }

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
    

#Fetch HTML content using Selenium for dynamic content
def get_HTML_content_selenium(url, wait_time=5):
    
    driver = None
    try:
        # Configure Chrome options
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Run in background
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument(
            '--disable-blink-features=AutomationControlled'
        )
        chrome_options.add_argument(
            'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
            ' AppleWebKit/537.36'
        )
        
        # Create driver
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(15)
        
        # Navigate to URL
        driver.get(url)
        
        # Wait for page to load (wait for body element)
        WebDriverWait(driver, wait_time).until(
            expected_conditions.presence_of_element_located(
                (By.TAG_NAME, 'body')
            )
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
def extract_page_data(soup, scrape_options, limits=None):
    
    if limits is None:
        limits = {
            'headings': 5,
            'links': 10,
            'paragraphs': 3,
            'images': 5,
            'videos': 5
        }
    
    data = {}
    
    if scrape_options['title']:
        data['title'] = soup.title.string if soup.title else 'No title found'
    
    if scrape_options['headings']:
        headings_list = soup.find_all(['h1', 'h2', 'h3'])
        data['headings'] = [
            h.text for h in headings_list[:limits['headings']]
        ]
    
    if scrape_options['links']:
        data['links'] = [
            {
                'text': a.get_text(strip=True),
                'href': a.get('href')
            } for a in soup.find_all('a', limit=limits['links'])
        ]
    
    if scrape_options['paragraphs']:
        paragraphs_list = soup.find_all('p')
        data['paragraphs'] = [
            p.text[:100] for p in paragraphs_list[:limits['paragraphs']]
        ]
    
    if scrape_options['images']:
        images_list = soup.find_all('img', limit=limits['images'])
        data['images'] = [img.get('src') for img in images_list]

    if scrape_options['videos']:
        videos_list = soup.find_all('video', limit=limits['videos'])
        data['videos'] = [video.get('src') for video in videos_list]

    if scrape_options['videos']:
        # Also check for video iframes (e.g., YouTube embeds)
        iframes = soup.find_all('iframe')
        video_iframes = [
            iframe.get('src') for iframe in iframes
            if 'youtube.com' in (iframe.get('src') or '')
        ][:limits['videos']]
        if 'videos' in data:
            data['videos'].extend(video_iframes)
        else:
            data['videos'] = video_iframes
    
    # Store all text content for search functionality
    data['full_text'] = soup.get_text()
    
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
        search_query = request.POST.get('search_query', '').strip()
        
        # Get selected scraping options
        scrape_options = {
            'title': request.POST.get('scrape_title') == 'on',
            'headings': request.POST.get('scrape_headings') == 'on',
            'links': request.POST.get('scrape_links') == 'on',
            'paragraphs': request.POST.get('scrape_paragraphs') == 'on',
            'images': request.POST.get('scrape_images') == 'on',
            'videos': request.POST.get('scrape_videos') == 'on',
        }
        
        # Get advanced options
        scrape_link_targets = request.POST.get('scrape_link_targets') == 'on'
        use_selenium = request.POST.get('use_selenium') == 'on'
        recursive_depth = int(request.POST.get('recursive_depth', 1))
        
        # Get result limits from user input
        limits = {
            'headings': int(request.POST.get('limit_headings', 5)),
            'links': int(request.POST.get('limit_links', 10)),
            'paragraphs': int(request.POST.get('limit_paragraphs', 3)),
            'images': int(request.POST.get('limit_images', 5)),
            'videos': int(request.POST.get('limit_videos', 5)),
            'linked_pages': int(request.POST.get('limit_linked_pages', 5))
        }
        
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
                    'fetch_method': (
                        'Selenium (dynamic content)'
                        if use_selenium
                        else 'Requests (static content)'
                    ),
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
                        main_page_data = extract_page_data(soup, scrape_options, limits)
                        data['main_page'] = {
                            'url': url,
                            'data': main_page_data
                        }
                        visited_urls.add(url)
                        
                        # Search in main page if search_query provided
                        if search_query:
                            search_result = search_in_content(search_query, main_page_data)
                            if search_result:
                                data['main_page']['search_result'] = search_result
                        
                        # Scrape link targets if enabled
                        if (
                            scrape_link_targets
                            and scrape_options['links']
                            and recursive_depth > 0
                        ):
                            data['linked_pages'] = []
                            
                            # Get extra links to account for
                            # same-domain filtering
                            links = soup.find_all(
                                'a',
                                limit=limits['linked_pages'] * 2
                            )
                            
                            for link in links:
                                href = link.get('href')
                                if not href:
                                    continue
                                
                                # Convert to absolute URL
                                absolute_url = get_absolute_url(url, href)
                                
                                # Check if same domain and not visited
                                if (
                                    absolute_url
                                    and is_same_domain(url, absolute_url)
                                    and absolute_url not in visited_urls
                                ):
                                    if (
                                        len(data['linked_pages'])
                                        >= limits['linked_pages']
                                    ):
                                        break
                                    
                                    try:
                                        # Fetch and scrape linked page
                                        linked_html = get_HTML_content(absolute_url)
                                        
                                        if linked_html and not isinstance(
                                            linked_html, str
                                        ):
                                            linked_soup = parse_HTML(
                                                linked_html
                                            )
                                            if linked_soup:
                                                linked_page_data = (
                                                    extract_page_data(
                                                        linked_soup,
                                                        scrape_options,
                                                        limits
                                                    )
                                                )
                                                linked_page_entry = {
                                                    'url': absolute_url,
                                                    'data': linked_page_data
                                                }
                                                
                                                # Search in linked page if
                                                # search_query provided
                                                if search_query:
                                                    search_result = (
                                                        search_in_content(
                                                            search_query,
                                                            linked_page_data
                                                        )
                                                    )
                                                    if search_result:
                                                        (
                                                            linked_page_entry[
                                                                'search_result'
                                                            ]
                                                        ) = search_result
                                                
                                                data['linked_pages'].append(linked_page_entry)
                                                visited_urls.add(absolute_url)
                                    except Exception as e:
                                        # Continue scraping even if one link fails
                                        pass
                            
                            if not data['linked_pages']:
                                del data['linked_pages']
                        
                        data['pages_scraped'] = len(visited_urls)
                        
            except Exception as e:
                error = f"Scraping error: {str(e)}"
    
    search_query_value = (
        request.POST.get('search_query', '')
        if request.method == 'POST'
        else ''
    )
    
    context = {
        'data': data,
        'error': error,
        'search_query': search_query_value,
    }
    
    return render(request, 'home.html', context)

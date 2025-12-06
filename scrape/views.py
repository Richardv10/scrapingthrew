from django.shortcuts import render
import requests
from bs4 import BeautifulSoup

# Send a GET request to the specified URL and return the HTML content

def get_HTML_content(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad responses
        return response.text
    except requests.RequestException as e:
        return f"An error occurred: {e}"
    
def parse_HTML(response):
    soup = BeautifulSoup(response, 'html.parser')
    
    return soup

def scrape(request):
    """Main view for scraping"""
    data = None
    error = None
    
    if request.method == 'POST':
        # Specify the URL to scrape
        url = 'https://example.com'  # Change this to your target URL
        
        try:
            html_content = get_HTML_content(url)
            soup = parse_HTML(html_content)
            
            # Extract data from the parsed HTML
            # Example: data = soup.find_all('div', class_='item')
            data = soup.title.string if soup.title else 'No title found'
            
        except Exception as e:
            error = f"Scraping error: {str(e)}"
    
    context = {
        'data': data,
        'error': error,
    }
    
    return render(request, 'home.html', context)

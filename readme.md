# ScrapingThrew

A powerful Django-based web scraper with support for both static and dynamic content.

## Features

- **Static Content Scraping** - Fast scraping with requests library
- **Dynamic Content Scraping** - Selenium support for JavaScript-heavy sites
- **Selective Scraping** - Choose what to scrape: titles, headings, links, paragraphs, images
- **Recursive Scraping** - Automatically scrape linked pages from the same domain
- **Robots.txt Compliance** - Check and display robots.txt rules for ethical scraping
- **User-Friendly Interface** - Simple form-based UI with visual feedback

## Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd scrapingthrew
```

2. Create virtual environment:
```bash
python -m venv .venv
.venv\Scripts\Activate.ps1  # Windows
source .venv/bin/activate  # Mac/Linux
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run migrations:
```bash
python manage.py migrate
```

5. Start the development server:
```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` in your browser.

## Usage

1. Enter a URL to scrape
2. Select what elements you want to scrape (title, headings, links, paragraphs, images)
3. Choose advanced options:
   - **Use Selenium** - For JavaScript-rendered content
   - **Scrape Link Targets** - Automatically scrape linked pages
   - **Recursion Depth** - How deep to follow links
4. Click "Start Scraping"
5. View results with robots.txt compliance check

## Project Structure

```
scrapingthrew/
├── scrape/                 # Main app
│   ├── views.py           # Scraping logic
│   ├── urls.py            # URL routing
│   ├── templates/         # HTML templates
│   └── static/css/        # Stylesheets
├── scraper/               # Project settings
├── manage.py              # Django management
└── requirements.txt       # Dependencies
```

## Requirements

- Python 3.8+
- Django 6.0
- BeautifulSoup4 - HTML parsing
- Selenium - Dynamic content scraping
- ChromeDriver - For Selenium (auto-downloads if available)

## Ethics

Always respect:
- Website robots.txt rules
- Terms of service
- Rate limiting
- Server resources

## License

## Dev diary UPDATE 11/12/25

Release of Alpha build onto Heroku, I will be rebuiding this in an Azure container once it's out of Alpha. 
Eco dynos don't support selenium due to processing power, (the dynamic content extraction isn't complete yet anyway)
I just want to experiment with the current build on a cloud platform, and this is the easiest.   

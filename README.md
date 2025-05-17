# Web Scraper

A powerful web scraping application built with Flask and Selenium that supports single-page scraping, sitemap parsing, and full website crawling.

## Features

- Single page scraping with CSS selectors
- Sitemap parsing and scraping
- Full website crawling with configurable depth
- Selenium support for JavaScript-heavy sites
- Automatic data extraction and JSON export
- Progress tracking and error handling
- Production-ready deployment configuration

## Installation

1. Clone the repository:
```bash
git clone https://github.com/abrarsami/web-scraper.git
cd web-scraper
```

2. Create and activate virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Development

Run the development server:
```bash
python app.py
```

The application will be available at `http://localhost:3000`

## Production Deployment

1. Install production dependencies:
```bash
pip install -r requirements-prod.txt
```

2. Configure environment variables:
```bash
export FLASK_ENV=production
export SECRET_KEY=your-secure-secret-key
```

3. Set up systemd service:
```bash
sudo cp webscraper.service /etc/systemd/system/
sudo systemctl enable webscraper
sudo systemctl start webscraper
```

4. Configure Nginx:
```bash
sudo cp nginx.conf /etc/nginx/sites-available/webscraper
sudo ln -s /etc/nginx/sites-available/webscraper /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Usage

1. Open the web interface at `http://localhost:3000`
2. Enter the target URL
3. Configure scraping options:
   - Use Selenium for JavaScript-heavy sites
   - Set wait time for dynamic content
   - Enable website crawling
   - Configure maximum pages to crawl
4. Enter CSS selectors in JSON format:
```json
{
    "title": "h1",
    "content": "p.content",
    "links": "a.link"
}
```
5. Click "Scrape" to start the process
6. Download results in JSON format

## Project Structure

```
web-scraper/
├── app.py              # Flask application
├── scraper.py          # Core scraping functionality
├── config.py           # Configuration management
├── wsgi.py            # Production WSGI entry point
├── requirements.txt    # Development dependencies
├── requirements-prod.txt # Production dependencies
├── webscraper.service  # Systemd service configuration
├── nginx.conf         # Nginx configuration
├── templates/         # HTML templates
├── static/           # Static files
├── downloads/        # Scraped data storage
└── logs/            # Application logs
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Security

- Never commit sensitive information
- Use environment variables for secrets
- Keep dependencies updated
- Follow security best practices

## Support

For issues and feature requests, please use the GitHub issue tracker. 
from flask import Flask, render_template, request, jsonify, send_file, url_for
from scraper import WebScraper, ScraperError, AuthenticationError, ScrapingError, SelectorError, SeleniumError
import json
import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
import traceback
from config import config

def create_app(config_name='default'):
    """Application factory function."""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Ensure required directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    # Configure logging
    handler = RotatingFileHandler(
        app.config['LOG_FILE'],
        maxBytes=10000000,  # 10MB
        backupCount=5
    )
    handler.setLevel(app.config['LOG_LEVEL'])
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)
    app.logger.setLevel(app.config['LOG_LEVEL'])

    @app.route('/')
    def index():
        """Render the main page"""
        app.logger.info('Rendering index page')
        return render_template('index.html')

    @app.route('/scrape', methods=['POST'])
    def scrape():
        """Handle scraping requests"""
        try:
            # Get form data
            url = request.form.get('url', '').strip()
            is_sitemap = request.form.get('is_sitemap') == 'on'
            use_selenium = request.form.get('use_selenium') == 'on'
            
            # Parse selectors
            try:
                selectors = json.loads(request.form.get('selectors', '{}'))
            except json.JSONDecodeError:
                app.logger.error("Invalid selectors format")
                return jsonify({
                    'error': 'Invalid selectors format. Please enter HTML tags in the format "key: tag", one per line.'
                }), 400

            if not url:
                app.logger.error("No URL provided")
                return jsonify({
                    'error': 'Please enter a URL'
                }), 400

            # Get crawling options
            is_crawl = request.form.get('is_crawl') == 'on'
            max_pages = int(request.form.get('max_pages', 100))
            same_domain_only = request.form.get('same_domain_only') == 'on'
            wait_time = int(request.form.get('wait_time', 0))

            # Validate max_pages
            if max_pages > 100:
                app.logger.warning(f"Max pages reduced from {max_pages} to 100 for performance")
                max_pages = 100

            app.logger.info(f"Starting scrape for URL: {url}")
            app.logger.debug(f"Selectors: {selectors}")
            app.logger.debug(f"Options: sitemap={is_sitemap}, crawl={is_crawl}, max_pages={max_pages}, same_domain_only={same_domain_only}, wait_time={wait_time}")

            # Initialize scraper
            scraper = WebScraper(
                use_selenium=use_selenium,
                debug=app.debug
            )

            try:
                # Scrape data
                if is_sitemap:
                    app.logger.info("Scraping from sitemap")
                    data = scraper.scrape_sitemap(url, selectors)
                elif is_crawl:
                    app.logger.info("Crawling website")
                    if selectors:
                        data = scraper.crawl_and_scrape(url, selectors, max_pages, same_domain_only, wait_time)
                    else:
                        data = scraper.crawl_website(url, max_pages, same_domain_only)
                else:
                    app.logger.info("Scraping single page")
                    if selectors:
                        data = scraper.scrape_page(url, selectors)
                    else:
                        soup = scraper.scrape(url)
                        data = [{
                            'url': url,
                            'title': soup.title.string if soup.title else None,
                            'links': [a.get('href') for a in soup.find_all('a', href=True)]
                        }]

                if not data:
                    app.logger.warning("No data found")
                    return jsonify({
                        'error': 'No data found'
                    }), 404

                # Save results to file
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f'scraped_data_{timestamp}.json'
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                
                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=2)

                app.logger.info(f"Successfully scraped {len(data)} items")
                return jsonify({
                    'success': True,
                    'message': f'Successfully scraped {len(data)} items',
                    'data': data,
                    'download_url': url_for('download_file', filename=filename)
                })

            except ScrapingError as e:
                app.logger.error(f"Scraping error: {str(e)}")
                return jsonify({
                    'error': str(e)
                }), 400
            except Exception as e:
                app.logger.error(f"Unexpected error during scraping: {str(e)}")
                app.logger.debug(traceback.format_exc())
                return jsonify({
                    'error': f'An unexpected error occurred during scraping: {str(e)}'
                }), 500
            finally:
                scraper.close()

        except Exception as e:
            app.logger.error(f"Error in scrape route: {str(e)}")
            app.logger.debug(traceback.format_exc())
            return jsonify({
                'error': 'An unexpected error occurred'
            }), 500

    @app.route('/download/<filename>')
    def download_file(filename):
        """Handle file downloads"""
        try:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if not os.path.exists(filepath):
                app.logger.error(f"File not found: {filename}")
                return jsonify({
                    'error': 'File not found'
                }), 404
            
            return send_file(
                filepath,
                as_attachment=True,
                download_name=filename
            )
        except Exception as e:
            app.logger.error(f"Download error: {str(e)}")
            return jsonify({
                'error': 'Failed to download file'
            }), 500

    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 errors"""
        app.logger.error(f'Page not found: {request.url}')
        return jsonify({
            'error': 'Page not found',
            'details': str(error)
        }), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors"""
        app.logger.error(f'Server error: {str(error)}')
        app.logger.debug(traceback.format_exc())
        return jsonify({
            'error': 'Internal server error',
            'details': str(error)
        }), 500

    return app

if __name__ == '__main__':
    app = create_app(os.environ.get('FLASK_ENV', 'development'))
    app.run(host='127.0.0.1', port=9000) 
from flask import Flask, render_template, request, jsonify, send_file
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
            url = request.form.get('url')
            is_sitemap = request.form.get('is_sitemap') == 'on'
            use_selenium = request.form.get('use_selenium') == 'on'
            wait_time = int(request.form.get('wait_time', 0))
            is_crawl = request.form.get('is_crawl') == 'on'
            max_pages = int(request.form.get('max_pages', 100))
            same_domain_only = request.form.get('same_domain_only') == 'on'
            
            # Parse selectors
            try:
                selectors = json.loads(request.form.get('selectors', '{}'))
            except json.JSONDecodeError:
                return jsonify({
                    'error': 'Invalid JSON in selectors. Please check the format.',
                    'details': 'Example format: {"title": "h1", "content": "p"}'
                }), 400

            # Validate inputs
            if not url:
                return jsonify({'error': 'URL is required'}), 400
            if not selectors:
                return jsonify({'error': 'At least one CSS selector is required'}), 400

            # Initialize scraper
            scraper = WebScraper(use_selenium=use_selenium, debug=app.debug)
            
            try:
                if is_crawl:
                    # Handle website crawling
                    data = scraper.crawl_and_scrape(
                        url, 
                        selectors,
                        max_pages=max_pages,
                        same_domain_only=same_domain_only,
                        wait_time=wait_time
                    )
                elif is_sitemap:
                    # Handle sitemap scraping
                    data = scraper.scrape_from_sitemap(url, selectors, wait_time)
                else:
                    # Handle single page scraping
                    soup = scraper.scrape(url, wait_time=wait_time)
                    data = scraper.extract_data(soup, selectors)

                # Save results
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f'scraped_data_{timestamp}.json'
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                
                scraper.save_to_json(data, filepath)
                
                return jsonify({
                    'success': True,
                    'message': 'Data scraped successfully',
                    'data': data,
                    'download_url': f'/download/{filename}'
                })

            except ScrapingError as e:
                app.logger.error(f"Scraping error: {str(e)}")
                return jsonify({
                    'error': 'Failed to scrape the page',
                    'details': str(e)
                }), 400
                
            except SelectorError as e:
                app.logger.error(f"Selector error: {str(e)}")
                return jsonify({
                    'error': 'Failed to extract data with provided selectors',
                    'details': str(e)
                }), 400
                
            except SeleniumError as e:
                app.logger.error(f"Selenium error: {str(e)}")
                return jsonify({
                    'error': 'Failed to initialize browser',
                    'details': str(e)
                }), 500
                
            except AuthenticationError as e:
                app.logger.error(f"Authentication error: {str(e)}")
                return jsonify({
                    'error': 'Authentication failed',
                    'details': str(e)
                }), 401
                
            except ScraperError as e:
                app.logger.error(f"Scraper error: {str(e)}")
                return jsonify({
                    'error': 'An error occurred during scraping',
                    'details': str(e)
                }), 500
                
            finally:
                scraper.close()

        except Exception as e:
            app.logger.error(f"Unexpected error: {str(e)}")
            app.logger.debug(traceback.format_exc())
            return jsonify({
                'error': 'An unexpected error occurred',
                'details': str(e)
            }), 500

    @app.route('/download/<filename>')
    def download_file(filename):
        """Handle file downloads"""
        try:
            return send_file(
                os.path.join(app.config['UPLOAD_FOLDER'], filename),
                as_attachment=True
            )
        except Exception as e:
            app.logger.error(f"Download error: {str(e)}")
            return jsonify({
                'error': 'Failed to download file',
                'details': str(e)
            }), 404

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
    app.run(host='127.0.0.1', port=3000) 
"""
Flask web application for GST Scraper
"""
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
from flask_cors import CORS
import os
from src.scraper import GSTScraper
from src.config import DEMO_MODE
from loguru import logger

app = Flask(__name__)
CORS(app)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')

# Initialize scraper
scraper = GSTScraper()

@app.route('/')
def index():
    """Home page with GST scraping form"""
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    """API endpoint to scrape GST data"""
    try:
        gstin = request.form.get('gstin', '').strip()

        if not gstin:
            flash('Please provide a GSTIN', 'error')
            return redirect(url_for('index'))

        logger.info(f"Received scraping request for GSTIN: {gstin}")

        # Scrape the GSTIN
        data = scraper.scrape_single_gstin(gstin)

        if data:
            # Save individual result
            csv_file, json_file = scraper.save_results([data])
            logger.success(f"Successfully scraped GSTIN: {gstin}")

            return render_template('result.html',
                                 gstin=gstin,
                                 data=data,
                                 csv_file=csv_file,
                                 json_file=json_file)
        else:
            flash('Failed to scrape GSTIN. Please try again.', 'error')
            return redirect(url_for('index'))

    except Exception as e:
        logger.exception(f"Error during scraping: {str(e)}")
        flash('An error occurred during scraping. Please try again.', 'error')
        return redirect(url_for('index'))

@app.route('/api/scrape', methods=['POST'])
def api_scrape():
    """JSON API endpoint for scraping"""
    try:
        data = request.get_json()
        gstin = data.get('gstin', '').strip() if data else ''

        if not gstin:
            return jsonify({'error': 'GSTIN is required'}), 400

        logger.info(f"API scraping request for GSTIN: {gstin}")

        result = scraper.scrape_single_gstin(gstin)

        if result:
            return jsonify({
                'success': True,
                'data': result
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to scrape GSTIN'
            }), 500

    except Exception as e:
        logger.exception(f"API error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'demo_mode': DEMO_MODE})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)

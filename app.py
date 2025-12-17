"""
Flask API for Portfolio Tracker
Serves portfolio data to the Apoena Wealth dashboard
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from src.portfolio_aggregator import PortfolioAggregator
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for cross-origin requests from the website

# Initialize portfolio aggregator
portfolio = None


def get_portfolio():
    """Lazy load portfolio aggregator"""
    global portfolio
    if portfolio is None:
        portfolio = PortfolioAggregator()
    return portfolio


@app.route('/')
def index():
    """API root endpoint"""
    return jsonify({
        'name': 'Apoena Wealth Portfolio Tracker API',
        'version': '1.0.0',
        'endpoints': {
            '/api/portfolio/summary': 'Get consolidated portfolio summary',
            '/api/portfolio/positions': 'Get all positions',
            '/api/portfolio/stocks': 'Get stock portfolio data',
            '/api/portfolio/crypto': 'Get crypto portfolio data',
            '/api/portfolio/bonds': 'Get bond portfolio data',
            '/api/portfolio/top-performers': 'Get top performing assets',
            '/api/portfolio/allocation': 'Get allocation chart data',
            '/api/portfolio/report': 'Get complete portfolio report'
        }
    })


@app.route('/api/portfolio/summary')
def get_summary():
    """Get consolidated portfolio summary"""
    try:
        base_currency = request.args.get('currency', 'BRL')
        p = get_portfolio()
        summary = p.get_consolidated_summary(base_currency=base_currency)
        return jsonify({
            'success': True,
            'data': summary,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/portfolio/positions')
def get_positions():
    """Get all positions across all asset types"""
    try:
        p = get_portfolio()
        positions = p.get_all_positions()
        return jsonify({
            'success': True,
            'data': positions,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/portfolio/stocks')
def get_stocks():
    """Get stock portfolio data"""
    try:
        p = get_portfolio()
        stock_data = {
            'summary': p.stock_portfolio.get_portfolio_summary(),
            'positions': p.stock_portfolio.get_current_values().to_dict('records'),
            'transactions': p.stock_portfolio.get_transactions_history().to_dict('records')
        }
        return jsonify({
            'success': True,
            'data': stock_data,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/portfolio/crypto')
def get_crypto():
    """Get crypto portfolio data"""
    try:
        currency = request.args.get('currency', 'BRL')
        p = get_portfolio()
        crypto_data = {
            'summary': p.crypto_portfolio.get_portfolio_summary(currency=currency),
            'positions': p.crypto_portfolio.get_current_values(currency=currency).to_dict('records'),
            'allocation': p.crypto_portfolio.get_allocation().to_dict('records'),
            'transactions': p.crypto_portfolio.get_transactions_history().to_dict('records')
        }
        return jsonify({
            'success': True,
            'data': crypto_data,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/portfolio/bonds')
def get_bonds():
    """Get bond portfolio data"""
    try:
        p = get_portfolio()
        bond_data = {
            'summary': p.bond_portfolio.get_portfolio_summary(),
            'positions': p.bond_portfolio.get_current_values().to_dict('records'),
            'allocation_by_type': p.bond_portfolio.get_allocation_by_type().to_dict('records'),
            'allocation_by_indexer': p.bond_portfolio.get_allocation_by_indexer().to_dict('records'),
            'maturity_schedule': p.bond_portfolio.get_maturity_schedule().to_dict('records')
        }
        return jsonify({
            'success': True,
            'data': bond_data,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/portfolio/top-performers')
def get_top_performers():
    """Get top performing assets"""
    try:
        n = int(request.args.get('limit', 10))
        p = get_portfolio()
        performers = p.get_top_performers(n=n).to_dict('records')
        return jsonify({
            'success': True,
            'data': performers,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/portfolio/allocation')
def get_allocation():
    """Get allocation chart data"""
    try:
        p = get_portfolio()
        allocation = p.get_allocation_chart_data()
        return jsonify({
            'success': True,
            'data': allocation,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/portfolio/report')
def get_report():
    """Get complete portfolio report"""
    try:
        p = get_portfolio()
        report = p.export_complete_report()
        return jsonify({
            'success': True,
            'data': report,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })


if __name__ == '__main__':
    # Development server
    app.run(debug=True, host='0.0.0.0', port=5000)

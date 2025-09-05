# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, jsonify
import os
import json
from werkzeug.utils import secure_filename
import openpyxl

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs('uploads', exist_ok=True)

products_data = []
api_tokens = {'yandex': '', 'ozon': '', 'wildberries': ''}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    global products_data
    
    if 'file' not in request.files:
        return jsonify({'error': 'File not found'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and file.filename.endswith(('.xlsx', '.xls')):
        try:
            wb = openpyxl.load_workbook(file)
            sheet = wb.active
            products_data = []
            
            for row in sheet.iter_rows(min_row=2, values_only=True):
                if row and len(row) >= 2:
                    products_data.append({
                        'article': str(row[0]) if row[0] else '',
                        'recommended_price': float(row[1]) if row[1] else 0
                    })
            
            return jsonify({
                'success': True,
                'message': f'Loaded {len(products_data)} products',
                'data': products_data
            })
                
        except Exception as e:
            return jsonify({'error': f'File reading error: {str(e)}'}), 500
    
    return jsonify({'error': 'Invalid file format'}), 400

@app.route('/api/save_settings', methods=['POST'])
def save_settings():
    global api_tokens
    
    data = request.get_json()
    api_tokens = {
        'yandex': data.get('yandex_token', ''),
        'ozon': data.get('ozon_token', ''),
        'wildberries': data.get('wildberries_token', '')
    }
    
    return jsonify({'success': True, 'message': 'Settings saved'})

@app.route('/api/update_prices', methods=['POST'])
def update_prices():
    global products_data
    
    if not products_data:
        return jsonify({'error': 'First load product data'}), 400
    
    results = []
    
    for product in products_data:
        import random
        results.append({
            'article': product['article'],
            'recommended_price': product['recommended_price'],
            'marketplaces': {
                'yandex': {
                    'name': f'Product {product["article"]} - Yandex',
                    'actual_price': round(product['recommended_price'] * random.uniform(0.7, 1.3), 2),
                    'is_low': False
                },
                'ozon': {
                    'name': f'Product {product["article"]} - Ozon',
                    'actual_price': round(product['recommended_price'] * random.uniform(0.7, 1.3), 2),
                    'is_low': False
                },
                'wildberries': {
                    'name': f'Product {product["article"]} - Wildberries',
                    'actual_price': round(product['recommended_price'] * random.uniform(0.7, 1.3), 2),
                    'is_low': False
                }
            }
        })
    
    for product in results:
        for marketplace in product['marketplaces'].values():
            marketplace['is_low'] = marketplace['actual_price'] < product['recommended_price']
    
    return jsonify({'success': True, 'data': results})

@app.route('/api/get_data')
def get_data():
    return jsonify({
        'products': products_data,
        'settings': api_tokens
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
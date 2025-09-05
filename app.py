# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, jsonify
import os
import json
from werkzeug.utils import secure_filename
import openpyxl
import requests
import time
from datetime import datetime

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

# Создаем необходимые папки
os.makedirs('uploads', exist_ok=True)
os.makedirs('templates', exist_ok=True)

products_data = []
api_tokens = {
    'yandex': {'seller_id': '', 'api_key': ''},
    'ozon': {'seller_id': '', 'api_key': ''},
    'wildberries': {'seller_id': '', 'api_key': ''}
}

class MarketplaceAPI:
    @staticmethod
    def get_yandex_product_info(article, seller_id, api_key):
        """Получение информации о товаре с Яндекс Маркет"""
        if not api_key or not seller_id:
            return None, None, None
            
        try:
            # Имитация API запроса к Яндекс Маркет
            # В реальности здесь будет реальный API вызов
            time.sleep(0.1)  # Имитация задержки
            
            # Заглушка для демонстрации
            import random
            price = random.uniform(100, 5000)
            name = f"Товар {article} (Яндекс)"
            url = f"https://market.yandex.ru/product/{article}"
            
            return round(price, 2), name, url
            
        except Exception as e:
            print(f"Yandex API error: {e}")
            return None, None, None

    @staticmethod
    def get_ozon_product_info(article, seller_id, api_key):
        """Получение информации о товаре с Ozon"""
        if not api_key or not seller_id:
            return None, None, None
            
        try:
            # Имитация API запроса к Ozon
            time.sleep(0.1)
            
            import random
            price = random.uniform(100, 5000)
            name = f"Товар {article} (Ozon)"
            url = f"https://www.ozon.ru/product/{article}"
            
            return round(price, 2), name, url
            
        except Exception as e:
            print(f"Ozon API error: {e}")
            return None, None, None

    @staticmethod
    def get_wildberries_product_info(article, seller_id, api_key):
        """Получение информации о товаре с Wildberries"""
        if not api_key or not seller_id:
            return None, None, None
            
        try:
            # Имитация API запроса к Wildberries
            time.sleep(0.1)
            
            import random
            price = random.uniform(100, 5000)
            name = f"Товар {article} (Wildberries)"
            url = f"https://www.wildberries.ru/catalog/{article}/detail.aspx"
            
            return round(price, 2), name, url
            
        except Exception as e:
            print(f"Wildberries API error: {e}")
            return None, None, None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    global products_data
    
    if 'file' not in request.files:
        return jsonify({'error': 'Файл не найден'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Файл не выбран'}), 400
    
    if file and file.filename.endswith(('.xlsx', '.xls')):
        try:
            wb = openpyxl.load_workbook(file)
            sheet = wb.active
            products_data = []
            
            for row_idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
                if row and len(row) >= 2:
                    # Обрабатываем артикул
                    article = str(row[0]).strip() if row[0] is not None else ''
                    
                    # Обрабатываем цену с проверкой на пустые значения
                    recommended_price = 0
                    price_value = row[1]
                    
                    if price_value is not None:
                        try:
                            price_str = str(price_value).strip()
                            if price_str:
                                recommended_price = float(price_str)
                        except (ValueError, TypeError):
                            continue
                    
                    if article:
                        products_data.append({
                            'article': article,
                            'recommended_price': recommended_price
                        })
            
            return jsonify({
                'success': True,
                'message': f'Загружено {len(products_data)} товаров',
                'data': products_data
            })
                
        except Exception as e:
            return jsonify({'error': f'Ошибка чтения файла: {str(e)}'}), 500
    
    return jsonify({'error': 'Недопустимый формат файла'}), 400

@app.route('/api/save_settings', methods=['POST'])
def save_settings():
    global api_tokens
    
    data = request.get_json()
    api_tokens = {
        'yandex': {
            'seller_id': data.get('yandex_seller_id', ''),
            'api_key': data.get('yandex_api_key', '')
        },
        'ozon': {
            'seller_id': data.get('ozon_seller_id', ''),
            'api_key': data.get('ozon_api_key', '')
        },
        'wildberries': {
            'seller_id': data.get('wildberries_seller_id', ''),
            'api_key': data.get('wildberries_api_key', '')
        }
    }
    
    return jsonify({'success': True, 'message': 'Настройки сохранены'})

@app.route('/api/update_prices', methods=['POST'])
def update_prices():
    global products_data, api_tokens
    
    if not products_data:
        return jsonify({'error': 'Сначала загрузите данные товаров'}), 400
    
    results = []
    
    for product in products_data:
        product_result = {
            'article': product['article'],
            'recommended_price': product['recommended_price'],
            'marketplaces': {}
        }
        
        # Получаем данные с Яндекс Маркет
        yandex_price, yandex_name, yandex_url = MarketplaceAPI.get_yandex_product_info(
            product['article'],
            api_tokens['yandex']['seller_id'],
            api_tokens['yandex']['api_key']
        )
        
        product_result['marketplaces']['yandex'] = {
            'name': yandex_name or f'Товар {product["article"]} - Яндекс',
            'actual_price': yandex_price or round(product['recommended_price'] * 0.9, 2),
            'is_low': False,
            'url': yandex_url or f"https://market.yandex.ru/search?text={product['article']}"
        }
        
        # Получаем данные с Ozon
        ozon_price, ozon_name, ozon_url = MarketplaceAPI.get_ozon_product_info(
            product['article'],
            api_tokens['ozon']['seller_id'],
            api_tokens['ozon']['api_key']
        )
        
        product_result['marketplaces']['ozon'] = {
            'name': ozon_name or f'Товар {product["article"]} - Ozon',
            'actual_price': ozon_price or round(product['recommended_price'] * 0.95, 2),
            'is_low': False,
            'url': ozon_url or f"https://www.ozon.ru/search/?text={product['article']}"
        }
        
        # Получаем данные с Wildberries
        wb_price, wb_name, wb_url = MarketplaceAPI.get_wildberries_product_info(
            product['article'],
            api_tokens['wildberries']['seller_id'],
            api_tokens['wildberries']['api_key']
        )
        
        product_result['marketplaces']['wildberries'] = {
            'name': wb_name or f'Товар {product["article"]} - Wildberries',
            'actual_price': wb_price or round(product['recommended_price'] * 1.05, 2),
            'is_low': False,
            'url': wb_url or f"https://www.wildberries.ru/catalog/0/search.aspx?search={product['article']}"
        }
        
        # Проверяем цены
        for marketplace in product_result['marketplaces'].values():
            if marketplace['actual_price'] and product['recommended_price']:
                marketplace['is_low'] = marketplace['actual_price'] < product['recommended_price']
        
        results.append(product_result)
    
    return jsonify({'success': True, 'data': results})

@app.route('/api/get_data')
def get_data():
    return jsonify({
        'products': products_data,
        'settings': api_tokens
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

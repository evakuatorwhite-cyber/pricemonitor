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

recommended_prices = {}  # Словарь артикул -> рекомендованная цена
api_tokens = {
    'yandex': {'seller_id': '', 'api_key': ''},
    'ozon': {'seller_id': '', 'api_key': ''},
    'wildberries': {'seller_id': '', 'api_key': ''}
}

class MarketplaceAPI:
    @staticmethod
    def get_yandex_products(seller_id, api_key):
        """Получение товаров с Яндекс Маркет (только с остатками)"""
        if not api_key or not seller_id:
            return []
            
        try:
            # Имитация API запроса к Яндекс Маркет
            # В реальности: GET https://api.partner.market.yandex.ru/campaigns/{seller_id}/offers
            time.sleep(0.5)
            
            # Заглушка для демонстрации - возвращаем товары с остатками
            import random
            products = []
            for i in range(12):  # 12 товаров для примера
                if random.random() > 0.3:  # 70% товаров с остатками
                    sku = f"YM{random.randint(10000, 99999)}"  # Внутренний SKU Яндекс
                    article = f"ART{random.randint(1000, 9999)}"  # Артикул товара
                    products.append({
                        'sku': sku,
                        'article': article,
                        'name': f'Товар Яндекс {sku}',
                        'price': round(random.uniform(100, 5000), 2),
                        'stock': random.randint(1, 100),
                        'url': f'https://market.yandex.ru/product/{sku}'
                    })
            return products
            
        except Exception as e:
            print(f"Yandex API error: {e}")
            return []

    @staticmethod
    def get_ozon_products(seller_id, api_key):
        """Получение товаров с Ozon (только с остатками)"""
        if not api_key or not seller_id:
            return []
            
        try:
            # Имитация API запроса к Ozon
            # В реальности: POST https://api-seller.ozon.ru/v2/product/list
            time.sleep(0.5)
            
            import random
            products = []
            for i in range(10):  # 10 товаров для примера
                if random.random() > 0.4:  # 60% товаров с остатками
                    sku = random.randint(1000000, 9999999)  # Внутренний SKU Ozon
                    article = f"ART{random.randint(1000, 9999)}"  # Артикул товара
                    products.append({
                        'sku': str(sku),
                        'article': article,
                        'name': f'Товар Ozon {sku}',
                        'price': round(random.uniform(100, 5000), 2),
                        'stock': random.randint(1, 50),
                        'url': f'https://www.ozon.ru/product/{sku}'
                    })
            return products
            
        except Exception as e:
            print(f"Ozon API error: {e}")
            return []

    @staticmethod
    def get_wildberries_products(seller_id, api_key):
        """Получение товаров с Wildberries (только с остатками)"""
        if not api_key or not seller_id:
            return []
            
        try:
            # Имитация API запроса к Wildberries
            # В реальности: GET https://suppliers-api.wildberries.ru/content/v1/cards/cursor/list
            time.sleep(0.5)
            
            import random
            products = []
            for i in range(15):  # 15 товаров для примера
                if random.random() > 0.2:  # 80% товаров с остатками
                    sku = random.randint(10000000, 99999999)  # Внутренний SKU Wildberries
                    article = f"ART{random.randint(1000, 9999)}"  # Артикул товара
                    products.append({
                        'sku': str(sku),
                        'article': article,
                        'name': f'Товар WB {sku}',
                        'price': round(random.uniform(100, 5000), 2),
                        'stock': random.randint(1, 200),
                        'url': f'https://www.wildberries.ru/catalog/{sku}/detail.aspx'
                    })
            return products
            
        except Exception as e:
            print(f"Wildberries API error: {e}")
            return []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    global recommended_prices
    
    if 'file' not in request.files:
        return jsonify({'error': 'Файл не найден'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Файл не выбран'}), 400
    
    if file and file.filename.endswith(('.xlsx', '.xls')):
        try:
            wb = openpyxl.load_workbook(file)
            sheet = wb.active
            recommended_prices = {}
            loaded_count = 0
            
            for row_idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
                if row and len(row) >= 2:
                    article = str(row[0]).strip() if row[0] is not None else ''
                    
                    recommended_price = 0
                    price_value = row[1]
                    
                    if price_value is not None:
                        try:
                            price_str = str(price_value).strip()
                            if price_str:
                                recommended_price = float(price_str)
                                if article:
                                    recommended_prices[article] = recommended_price
                                    loaded_count += 1
                        except (ValueError, TypeError):
                            continue
            
            return jsonify({
                'success': True,
                'message': f'Загружено {loaded_count} рекомендованных цен',
                'count': loaded_count
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
    global recommended_prices, api_tokens
    
    results = {
        'yandex': [],
        'ozon': [],
        'wildberries': []
    }
    
    # Получаем товары с каждого маркетплейса
    yandex_products = MarketplaceAPI.get_yandex_products(
        api_tokens['yandex']['seller_id'],
        api_tokens['yandex']['api_key']
    )
    
    ozon_products = MarketplaceAPI.get_ozon_products(
        api_tokens['ozon']['seller_id'],
        api_tokens['ozon']['api_key']
    )
    
    wb_products = MarketplaceAPI.get_wildberries_products(
        api_tokens['wildberries']['seller_id'],
        api_tokens['wildberries']['api_key']
    )
    
    # Обрабатываем товары Яндекс Маркет
    for product in yandex_products:
        recommended_price = recommended_prices.get(product['article'], 0)
        results['yandex'].append({
            'sku': product['sku'],
            'article': product['article'],
            'name': product['name'],
            'actual_price': product['price'],
            'recommended_price': recommended_price,
            'stock': product['stock'],
            'url': product['url'],
            'is_low': product['price'] < recommended_price if recommended_price > 0 else False
        })
    
    # Обрабатываем товары Ozon
    for product in ozon_products:
        recommended_price = recommended_prices.get(product['article'], 0)
        results['ozon'].append({
            'sku': product['sku'],
            'article': product['article'],
            'name': product['name'],
            'actual_price': product['price'],
            'recommended_price': recommended_price,
            'stock': product['stock'],
            'url': product['url'],
            'is_low': product['price'] < recommended_price if recommended_price > 0 else False
        })
    
    # Обрабатываем товары Wildberries
    for product in wb_products:
        recommended_price = recommended_prices.get(product['article'], 0)
        results['wildberries'].append({
            'sku': product['sku'],
            'article': product['article'],
            'name': product['name'],
            'actual_price': product['price'],
            'recommended_price': recommended_price,
            'stock': product['stock'],
            'url': product['url'],
            'is_low': product['price'] < recommended_price if recommended_price > 0 else False
        })
    
    return jsonify({
        'success': True, 
        'data': results,
        'stats': {
            'yandex': len(results['yandex']),
            'ozon': len(results['ozon']),
            'wildberries': len(results['wildberries']),
            'total': len(results['yandex']) + len(results['ozon']) + len(results['wildberries'])
        }
    })

@app.route('/api/get_data')
def get_data():
    return jsonify({
        'recommended_prices_count': len(recommended_prices),
        'settings': api_tokens
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

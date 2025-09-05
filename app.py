# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, jsonify
import os
import json
from werkzeug.utils import secure_filename
import openpyxl

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
                            # Преобразуем в строку и очищаем
                            price_str = str(price_value).strip()
                            if price_str:  # Если строка не пустая
                                recommended_price = float(price_str)
                        except (ValueError, TypeError):
                            # Пропускаем строку с неверной ценой
                            print(f"Предупреждение: Неверная цена в строке {row_idx}: {price_value}")
                            continue
                    
                    # Добавляем только если артикул не пустой
                    if article:
                        products_data.append({
                            'article': article,
                            'recommended_price': recommended_price
                        })
                    else:
                        print(f"Предупреждение: Пустой артикул в строке {row_idx}")
            
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
    global products_data
    
    if not products_data:
        return jsonify({'error': 'Сначала загрузите данные товаров'}), 400
    
    results = []
    
    for product in products_data:
        import random
        results.append({
            'article': product['article'],
            'recommended_price': product['recommended_price'],
            'marketplaces': {
                'yandex': {
                    'name': f'Товар {product["article"]} - Яндекс',
                    'actual_price': round(product['recommended_price'] * random.uniform(0.7, 1.3), 2),
                    'is_low': False
                },
                'ozon': {
                    'name': f'Товар {product["article"]} - Ozon',
                    'actual_price': round(product['recommended_price'] * random.uniform(0.7, 1.3), 2),
                    'is_low': False
                },
                'wildberries': {
                    'name': f'Товар {product["article"]} - Wildberries',
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
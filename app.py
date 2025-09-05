from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import os
import json
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Создаем папку для загрузок
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Хранение данных в памяти (в production используйте БД)
products_data = pd.DataFrame()
api_tokens = {
    'yandex': '',
    'ozon': '', 
    'wildberries': ''
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
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            df = pd.read_excel(filepath)
            if len(df.columns) >= 2:
                products_data = df.iloc[:, :2].copy()
                products_data.columns = ['article', 'recommended_price']
                
                return jsonify({
                    'success': True,
                    'message': f'Загружено {len(products_data)} товаров',
                    'data': products_data.to_dict('records')
                })
            else:
                return jsonify({'error': 'Файл должен содержать минимум 2 столбца'}), 400
                
        except Exception as e:
            return jsonify({'error': f'Ошибка чтения файла: {str(e)}'}), 500
    
    return jsonify({'error': 'Недопустимый формат файла'}), 400

@app.route('/api/save_settings', methods=['POST'])
def save_settings():
    global api_tokens
    
    data = request.get_json()
    api_tokens = {
        'yandex': data.get('yandex_token', ''),
        'ozon': data.get('ozon_token', ''),
        'wildberries': data.get('wildberries_token', '')
    }
    
    return jsonify({'success': True, 'message': 'Настройки сохранены'})

@app.route('/api/update_prices', methods=['POST'])
def update_prices():
    global products_data
    
    if products_data.empty:
        return jsonify({'error': 'Сначала загрузите данные товаров'}), 400
    
    # Имитация получения данных с API маркетплейсов
    results = []
    
    for _, product in products_data.iterrows():
        article = product['article']
        recommended_price = product['recommended_price']
        
        product_data = {
            'article': article,
            'recommended_price': recommended_price,
            'marketplaces': {}
        }
        
        # Имитация данных для каждого маркетплейса
        for marketplace in ['yandex', 'ozon', 'wildberries']:
            import random
            actual_price = round(recommended_price * random.uniform(0.7, 1.3), 2)
            
            product_data['marketplaces'][marketplace] = {
                'name': f'Товар {article} - {marketplace}',
                'actual_price': actual_price,
                'is_low': actual_price < recommended_price
            }
        
        results.append(product_data)
    
    return jsonify({'success': True, 'data': results})

@app.route('/api/get_data')
def get_data():
    return jsonify({
        'products': products_data.to_dict('records') if not products_data.empty else [],
        'settings': api_tokens
    })

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ['xlsx', 'xls']

if __name__ == '__main__':
    # Для разработки
    app.run(debug=True, host='0.0.0.0', port=5000)
    
    # Для production:
    # from waitress import serve
    # serve(app, host='0.0.0.0', port=5000)
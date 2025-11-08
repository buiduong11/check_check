#!/usr/bin/env python3
"""
Card Checker Web UI - Flask Application
"""

from flask import Flask, render_template, request, jsonify, Response
from flask_cors import CORS
import json
import time
import threading
from queue import Queue
from card_checker_pro import CardCheckerPro
import os

app = Flask(__name__)
CORS(app)

# Queue để gửi kết quả real-time
result_queue = Queue()
checker_instance = None
checker_lock = threading.Lock()

@app.route('/')
def index():
    """Trang chủ"""
    return render_template('index.html')

@app.route('/api/check', methods=['POST'])
def check_cards():
    """API check thẻ"""
    global checker_instance
    
    try:
        data = request.get_json()
        cards_input = data.get('cards', '')
        
        if not cards_input:
            return jsonify({'error': 'Không có thẻ để check'}), 400
        
        # Parse cards
        cards = []
        invalid_cards = []
        
        for line in cards_input.strip().split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Validate format: number|month|year|cvv hoặc number|month/year|cvv
            parts = line.split('|')
            if len(parts) < 3:
                invalid_cards.append({'card': line, 'reason': 'Sai format (cần: number|month|year|cvv)'})
                continue
            
            cards.append(line)
        
        if not cards and not invalid_cards:
            return jsonify({'error': 'Không có thẻ hợp lệ'}), 400
        
        # Start checking in background thread
        thread = threading.Thread(target=check_cards_background, args=(cards, invalid_cards))
        thread.daemon = True
        thread.start()
        
        return jsonify({'status': 'started', 'total': len(cards) + len(invalid_cards)})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def check_cards_background(cards, invalid_cards):
    """Check thẻ trong background thread"""
    global checker_instance
    
    try:
        # Gửi invalid cards trước
        for invalid in invalid_cards:
            result_queue.put({
                'type': 'result',
                'card': invalid['card'],
                'status': 'INVALID',
                'message': invalid['reason']
            })
            time.sleep(0.1)
        
        # Khởi tạo checker nếu chưa có
        with checker_lock:
            if checker_instance is None:
                result_queue.put({
                    'type': 'log',
                    'message': 'Đang khởi tạo browser...'
                })
                checker_instance = CardCheckerPro(threads=1, headless=False)
        
        # Check từng thẻ
        for card_line in cards:
            result_queue.put({
                'type': 'log',
                'message': f'Đang check: {card_line}'
            })
            
            # Parse card
            card = checker_instance.parse_card(card_line)
            if not card:
                result_queue.put({
                    'type': 'result',
                    'card': card_line,
                    'card_original': card_line,
                    'status': 'INVALID',
                    'message': 'Không thể parse thẻ'
                })
                continue
            
            # Check card
            card_info, status, message = checker_instance.check_card(card)
            
            result_queue.put({
                'type': 'result',
                'card': card_info,
                'card_original': card_line,  # Lưu format gốc user nhập
                'status': status,
                'message': message
            })
            
            time.sleep(1)
        
        result_queue.put({
            'type': 'complete',
            'message': 'Hoàn thành check tất cả thẻ'
        })
        
    except Exception as e:
        result_queue.put({
            'type': 'error',
            'message': str(e)
        })

@app.route('/api/stream')
def stream():
    """Server-Sent Events stream để gửi kết quả real-time"""
    def generate():
        while True:
            try:
                # Lấy kết quả từ queue
                result = result_queue.get(timeout=30)
                yield f"data: {json.dumps(result)}\n\n"
                
                if result.get('type') == 'complete':
                    break
                    
            except:
                # Gửi heartbeat
                yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Upload file thẻ"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Không có file'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Không có file được chọn'}), 400
        
        # Đọc nội dung file
        content = file.read().decode('utf-8')
        
        return jsonify({'content': content})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("="*70)
    print("CARD CHECKER WEB UI")
    print("="*70)
    print("Mở trình duyệt và truy cập: http://localhost:5001")
    print("="*70)
    app.run(debug=True, host='0.0.0.0', port=5001, threaded=True)

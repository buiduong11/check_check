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
from card_checker_chewy import CardCheckerChewy
from multi_checker_chewy import MultiBrowserChecker
import os

app = Flask(__name__)
CORS(app)

# Queue để gửi kết quả real-time
result_queue = Queue()
checker_instance = None
checker_lock = threading.Lock()
current_site = 'chewy'  # Mặc định là chewy
multi_checker_instance = None  # Multi-browser checker

# Worker function cho multiprocessing - PHẢI Ở NGOÀI để pickle được
def multi_browser_worker(worker_id, card_queue, mp_result_queue, max_live_per_account=4):
    """Worker process cho multi-browser checking"""
    try:
        checker = CardCheckerChewy()
        
        while True:
            try:
                card_line = card_queue.get(timeout=2)
                if card_line is None:  # Poison pill
                    break
            except:
                continue
            
            # Check card
            card_info, status, message = checker.check_card(card_line)
            mp_result_queue.put((worker_id, card_info, status, message))
            
            # Nếu đủ 4 LIVE → reset account
            if status == "APPROVED" and checker.live_count >= max_live_per_account:
                checker.reset_account()
        
        checker.close()
    except Exception as e:
        mp_result_queue.put((worker_id, "", "ERROR", str(e)))

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
        site = data.get('site', 'chewy')  # Mặc định chewy
        mode = 'single'  # FORCE single mode - chỉ chạy 1 browser
        num_browsers = 1  # Chỉ 1 browser
        
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
        if mode == 'multi' and site == 'chewy':
            thread = threading.Thread(target=check_cards_multi, args=(cards, invalid_cards, num_browsers))
        else:
            thread = threading.Thread(target=check_cards_background, args=(cards, invalid_cards, site))
        
        thread.daemon = True
        thread.start()
        
        return jsonify({'status': 'started', 'total': len(cards) + len(invalid_cards), 'mode': mode})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def check_cards_multi(cards, invalid_cards, num_browsers=5):
    """Check thẻ với multi-browser mode"""
    from multiprocessing import Process, Manager
    
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
        
        result_queue.put({
            'type': 'log',
            'message': f'Đang khởi tạo {num_browsers} browsers...'
        })
        
        # Tạo multi checker
        max_live_per_account = 4
        
        # Tạo queues cho multiprocessing
        manager = Manager()
        card_queue = manager.Queue()
        mp_result_queue = manager.Queue()
        
        # Đưa cards vào queue
        for card in cards:
            card_queue.put(card)
        
        # Thêm poison pills
        for _ in range(num_browsers):
            card_queue.put(None)
        
        # Start workers - SỬ DỤNG FUNCTION Ở NGOÀI
        workers = []
        for i in range(num_browsers):
            p = Process(target=multi_browser_worker, args=(i+1, card_queue, mp_result_queue, max_live_per_account))
            p.start()
            workers.append(p)
            time.sleep(1)
        
        # Thu thập kết quả
        checked_count = 0
        total_cards = len(cards)
        
        while checked_count < total_cards:
            try:
                worker_id, card_info, status, message = mp_result_queue.get(timeout=60)
                
                result_queue.put({
                    'type': 'result',
                    'card': card_info,
                    'card_original': card_info,
                    'status': status,
                    'message': f'[Worker {worker_id}] {message}'
                })
                
                checked_count += 1
                result_queue.put({
                    'type': 'log',
                    'message': f'Progress: {checked_count}/{total_cards}'
                })
                
            except:
                break
        
        # Đợi workers kết thúc
        for p in workers:
            p.join(timeout=5)
            if p.is_alive():
                p.terminate()
        
        result_queue.put({
            'type': 'complete',
            'message': f'Hoàn thành check {checked_count}/{total_cards} thẻ với {num_browsers} browsers'
        })
        
    except Exception as e:
        result_queue.put({
            'type': 'error',
            'message': f'Multi-browser error: {str(e)}'
        })

def check_cards_background(cards, invalid_cards, site='chewy'):
    """Check thẻ trong background thread"""
    global checker_instance, current_site
    
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
        
        # Khởi tạo checker nếu chưa có hoặc site thay đổi
        with checker_lock:
            if checker_instance is None or current_site != site:
                # Đóng checker cũ nếu có
                if checker_instance is not None:
                    try:
                        checker_instance.close()
                    except:
                        pass
                
                result_queue.put({
                    'type': 'log',
                    'message': f'Đang khởi tạo browser cho {site.upper()}...'
                })
                
                # Khởi tạo checker mới theo site
                if site == 'chewy':
                    checker_instance = CardCheckerChewy()
                else:
                    checker_instance = CardCheckerPro(threads=1, headless=False)
                
                current_site = site
        
        # Check từng thẻ
        for card_line in cards:
            result_queue.put({
                'type': 'log',
                'message': f'Đang check: {card_line}'
            })
            
            # Check card
            if site == 'chewy':
                # Chewy checker tự parse trong check_card
                card_info, status, message = checker_instance.check_card(card_line)
            else:
                # PipesAndCigars checker cần parse trước
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
    # Fix cho multiprocessing trên macOS/Windows
    from multiprocessing import freeze_support, set_start_method
    freeze_support()
    
    # Set spawn method để tránh fork issues trên macOS
    try:
        set_start_method('spawn')
    except RuntimeError:
        pass  # Already set
    
    print("="*70)
    print("CARD CHECKER WEB UI")
    print("="*70)
    print("Mở trình duyệt và truy cập: http://localhost:5001")
    print("="*70)
    app.run(debug=True, host='0.0.0.0', port=5001, threaded=True)

#!/usr/bin/env python3
"""
Multi-Browser Card Checker - CHEWY.COM
Chạy 5 browser cùng lúc, mỗi account tối đa 4 thẻ LIVE
"""

import time
import multiprocessing
from multiprocessing import Process, Queue, Manager
from typing import List, Tuple
from card_checker_chewy import CardCheckerChewy


# Worker function - PHẢI Ở NGOÀI class để pickle được
def multi_checker_worker(worker_id: int, card_queue, result_queue, max_live_per_account: int = 4):
    """
    Worker process - mỗi worker chạy 1 browser
    """
    print(f"[Worker {worker_id}] Starting...")
    
    try:
        checker = CardCheckerChewy()
        
        while True:
            # Lấy card từ queue
            try:
                card_line = card_queue.get(timeout=2)
                if card_line is None:  # Poison pill - kết thúc worker
                    print(f"[Worker {worker_id}] No more cards. Shutting down...")
                    break
            except:
                # Queue empty
                print(f"[Worker {worker_id}] Queue empty. Waiting...")
                time.sleep(1)
                continue
            
            print(f"\n[Worker {worker_id}] Checking: {card_line}")
            
            # Check card
            card_info, status, message = checker.check_card(card_line)
            
            # Lưu kết quả
            result_queue.put((worker_id, card_info, status, message))
            
            print(f"[Worker {worker_id}] Result: {status} - {message}")
            
            # Nếu thẻ LIVE → check xem đã đủ 4 chưa
            if status == "APPROVED":
                print(f"[Worker {worker_id}] LIVE count: {checker.live_count}/{max_live_per_account}")
                
                # Nếu đủ 4 thẻ LIVE → Tạo account mới
                if checker.live_count >= max_live_per_account:
                    print(f"[Worker {worker_id}] Đã đủ {max_live_per_account} thẻ LIVE!")
                    print(f"[Worker {worker_id}] Đóng browser và tạo account mới...")
                    
                    # Reset account (đóng browser cũ, tạo mới)
                    if not checker.reset_account():
                        print(f"[Worker {worker_id}] Lỗi reset account!")
                        break
                    
                    print(f"[Worker {worker_id}] Account mới đã sẵn sàng!")
        
        # Đóng browser khi kết thúc
        checker.close()
        print(f"[Worker {worker_id}] Finished!")
        
    except Exception as e:
        print(f"[Worker {worker_id}] ERROR: {e}")
        import traceback
        traceback.print_exc()


class MultiBrowserChecker:
    def __init__(self, num_browsers: int = 5, max_live_per_account: int = 4):
        self.num_browsers = num_browsers
        self.max_live_per_account = max_live_per_account
        
        print("\n" + "="*70)
        print(f"MULTI-BROWSER CARD CHECKER - {num_browsers} BROWSERS")
        print(f"Mỗi account tối đa: {max_live_per_account} thẻ LIVE")
        print("="*70 + "\n")
    
    def check_cards(self, card_list: List[str]) -> List[Tuple]:
        """
        Check danh sách cards với multi-browser
        """
        if not card_list:
            print("[!] Không có card nào để check!")
            return []
        
        print(f"\n[*] Tổng số cards: {len(card_list)}")
        print(f"[*] Số browsers: {self.num_browsers}")
        print(f"[*] Bắt đầu check...\n")
        
        # Tạo queues
        manager = Manager()
        card_queue = manager.Queue()
        result_queue = manager.Queue()
        
        # Đưa tất cả cards vào queue
        for card in card_list:
            card_queue.put(card)
        
        # Thêm poison pills để kết thúc workers
        for _ in range(self.num_browsers):
            card_queue.put(None)
        
        # Tạo và start workers - SỬ DỤNG FUNCTION Ở NGOÀI
        workers = []
        for i in range(self.num_browsers):
            p = Process(target=multi_checker_worker, args=(i+1, card_queue, result_queue, self.max_live_per_account))
            p.start()
            workers.append(p)
            time.sleep(1)  # Delay giữa các browser để tránh quá tải
        
        # Đợi tất cả workers hoàn thành
        for p in workers:
            p.join()
        
        # Thu thập kết quả
        results = []
        while not result_queue.empty():
            results.append(result_queue.get())
        
        return results
    
    def print_summary(self, results: List[Tuple], save_to_file: bool = True):
        """In tổng kết kết quả và lưu vào file"""
        print("\n" + "="*70)
        print("KẾT QUẢ TỔNG HỢP")
        print("="*70)
        
        live_count = 0
        die_count = 0
        error_count = 0
        
        live_cards = []
        die_cards = []
        error_cards = []
        
        for worker_id, card_info, status, message in results:
            status_symbol = "✓" if status == "APPROVED" else "✗"
            print(f"[Worker {worker_id}] [{status_symbol}] {card_info}: {status} - {message}")
            
            if status == "APPROVED":
                live_count += 1
                live_cards.append(card_info)
            elif status == "DECLINED":
                die_count += 1
                die_cards.append(card_info)
            else:
                error_count += 1
                error_cards.append(card_info)
        
        print("="*70)
        print(f"LIVE: {live_count} | DIE: {die_count} | ERROR: {error_count} | TOTAL: {len(results)}")
        print("="*70 + "\n")
        
        # Lưu kết quả vào file
        if save_to_file:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            
            # Lưu LIVE cards
            if live_cards:
                with open(f"live_cards_{timestamp}.txt", "w") as f:
                    for card in live_cards:
                        f.write(f"{card}\n")
                print(f"[✓] Đã lưu {len(live_cards)} LIVE cards vào live_cards_{timestamp}.txt")
            
            # Lưu DIE cards
            if die_cards:
                with open(f"die_cards_{timestamp}.txt", "w") as f:
                    for card in die_cards:
                        f.write(f"{card}\n")
                print(f"[✓] Đã lưu {len(die_cards)} DIE cards vào die_cards_{timestamp}.txt")
            
            # Lưu ERROR cards
            if error_cards:
                with open(f"error_cards_{timestamp}.txt", "w") as f:
                    for card in error_cards:
                        f.write(f"{card}\n")
                print(f"[✓] Đã lưu {len(error_cards)} ERROR cards vào error_cards_{timestamp}.txt")
            
            print()


if __name__ == "__main__":
    """Test với danh sách cards"""
    # Fix cho multiprocessing trên macOS/Windows
    from multiprocessing import freeze_support, set_start_method
    freeze_support()
    
    # Set spawn method để tránh fork issues trên macOS
    try:
        set_start_method('spawn')
    except RuntimeError:
        pass  # Already set
    
    # Đọc cards từ file cards.txt
    test_cards = []
    try:
        with open("cards.txt", "r") as f:
            test_cards = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        print(f"[✓] Đọc được {len(test_cards)} cards từ cards.txt")
    except FileNotFoundError:
        print("[!] Không tìm thấy file cards.txt")
        print("[*] Sử dụng test cards mặc định...")
        test_cards = [
            "4532015112830366|12|2025|123",
            "5425233430109903|11|2026|456",
            "4916338506082832|09|2027|789",
            "5425233430109911|08|2025|321",
            "4532015112830374|07|2026|654",
            "5425233430109929|06|2027|987",
            "4916338506082840|05|2025|147",
            "5425233430109937|04|2026|258",
            "4532015112830382|03|2027|369",
            "5425233430109945|02|2025|741",
        ]
    
    if not test_cards:
        print("[!] Không có cards để check!")
        exit(1)
    
    # Tạo checker với 5 browsers, mỗi account tối đa 4 thẻ LIVE
    checker = MultiBrowserChecker(num_browsers=5, max_live_per_account=4)
    
    # Check cards
    results = checker.check_cards(test_cards)
    
    # In tổng kết
    checker.print_summary(results)
    
    print("[✓] Hoàn thành!")

#!/usr/bin/env python3
"""
Test single browser để debug
"""

from card_checker_chewy import CardCheckerChewy
import time

if __name__ == "__main__":
    print("="*70)
    print("TEST SINGLE BROWSER")
    print("="*70)
    
    checker = CardCheckerChewy()
    
    # Test với 1 thẻ
    test_card = "4532015112830366|12|2025|123"
    
    print(f"\n[*] Testing card: {test_card}\n")
    
    card_info, status, message = checker.check_card(test_card)
    
    print(f"\n[RESULT] {status}: {message}\n")
    
    # Đợi 5s để xem browser
    print("[*] Đợi 5s để xem browser...")
    time.sleep(5)
    
    checker.close()
    print("[✓] Done!")

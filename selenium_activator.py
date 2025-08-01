#!/usr/bin/env python3
"""
Selenium-based Audible Activation Bytes Extractor
Based on inAudible-NG/audible-activator approach
Uses Selenium WebDriver to automate Audible login and extract activation bytes
"""

import os
import sys
import time
import base64
import hashlib
import binascii
import requests
import json
from pathlib import Path
from urllib.parse import urlencode, urlparse, parse_qsl

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.firefox.options import Options as FirefoxOptions
    from webdriver_manager.chrome import ChromeDriverManager
    from webdriver_manager.firefox import GeckoDriverManager
    from selenium.webdriver.chrome.service import Service as ChromeService
    from selenium.webdriver.firefox.service import Service as FirefoxService
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

class SeleniumActivationExtractor:
    def __init__(self, lang='us', debug=False, use_firefox=False):
        self.lang = lang
        self.debug = debug
        self.use_firefox = use_firefox
        self.driver = None
        
        # Base URLs for different regions
        self.base_urls = {
            'us': 'https://www.audible.com/',
            'uk': 'https://www.audible.co.uk/',
            'au': 'https://www.audible.com.au/',
            'de': 'https://www.audible.de/',
            'fr': 'https://www.audible.fr/',
            'jp': 'https://www.audible.co.jp/',
            'in': 'https://www.audible.in/'
        }
        
        self.base_url = self.base_urls.get(lang, self.base_urls['us'])
        
    def check_dependencies(self):
        """Check if required dependencies are available"""
        if not SELENIUM_AVAILABLE:
            return False, "Selenium is not installed. Install with: pip install selenium"
        
        # With webdriver-manager, we don't need to manually check for driver availability
        # It will automatically download and manage drivers
        return True, "Dependencies available"
    
    def setup_driver(self):
        """Set up Selenium WebDriver"""
        try:
            if self.use_firefox:
                options = FirefoxOptions()
                if not self.debug:
                    options.add_argument('--headless')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                
                # Use webdriver-manager to automatically download and manage GeckoDriver
                service = FirefoxService(GeckoDriverManager().install())
                self.driver = webdriver.Firefox(service=service, options=options)
            else:
                options = ChromeOptions()
                options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
                if not self.debug:
                    options.add_argument('--headless')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--disable-gpu')
                options.add_argument('--window-size=1920,1080')
                
                # Use webdriver-manager to automatically download and manage ChromeDriver
                service = ChromeService(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=options)
            
            return True, "WebDriver initialized successfully"
            
        except Exception as e:
            return False, f"Failed to initialize WebDriver: {str(e)}"
    
    def generate_player_id(self, custom_id=None):
        """Generate player ID for Audible authentication"""
        if custom_id:
            player_id = base64.b64encode(binascii.unhexlify(custom_id)).decode('ascii').rstrip()
        else:
            # Use empty string hash for consistent player ID
            player_id = base64.b64encode(hashlib.sha1(b"").digest()).decode('ascii').rstrip()
        
        return player_id
    
    def extract_activation_bytes(self, username, password, player_id=None):
        """Extract activation bytes using Selenium automation"""
        
        # Check dependencies first
        deps_ok, deps_msg = self.check_dependencies()
        if not deps_ok:
            return None, deps_msg
        
        # Set up WebDriver
        driver_ok, driver_msg = self.setup_driver()
        if not driver_ok:
            return None, driver_msg
        
        try:
            # Generate player ID
            if not player_id:
                player_id = self.generate_player_id()
            
            print(f"[*] Using Player ID: {player_id}")
            print(f"[*] Target region: {self.lang}")
            print(f"[*] Base URL: {self.base_url}")
            
            # Determine login URL based on username format
            if '@' in username:
                # Amazon login using email
                login_url = "https://www.amazon.com/ap/signin?"
                if self.lang == "uk":
                    login_url = "https://www.amazon.co.uk/ap/signin?"
                elif self.lang == "de":
                    login_url = "https://www.amazon.de/ap/signin?"
                elif self.lang == "fr":
                    login_url = "https://www.amazon.fr/ap/signin?"
                elif self.lang == "jp":
                    login_url = "https://www.amazon.co.jp/ap/signin?"
                elif self.lang == "au":
                    login_url = "https://www.amazon.com.au/ap/signin?"
                elif self.lang == "in":
                    login_url = "https://www.amazon.in/ap/signin?"
            else:
                # Direct Audible login
                login_url = f"{self.base_url}sign-in/ref=ap_to_private?forcePrivateSignIn=true&rdPath={self.base_url}?"
            
            # Prepare OpenID payload
            payload = {
                'openid.ns': 'http://specs.openid.net/auth/2.0',
                'openid.identity': 'http://specs.openid.net/auth/2.0/identifier_select',
                'openid.claimed_id': 'http://specs.openid.net/auth/2.0/identifier_select',
                'openid.mode': 'logout',
                'openid.assoc_handle': f'amzn_audible_{self.lang}',
                'openid.return_to': f'{self.base_url}player-auth-token?playerType=software&playerId={player_id}&bp_ua=y&playerModel=Desktop&playerManufacturer=Audible'
            }
            
            query_string = urlencode(payload)
            url = login_url + query_string
            
            print("[*] Navigating to Audible...")
            self.driver.get(f"{self.base_url}?ipRedirectOverride=true")
            
            print("[*] Navigating to login page...")
            self.driver.get(url)
            
            if self.debug:
                print("[!] DEBUG mode: Please login manually in the browser window")
                print("[!] Waiting up to 2 minutes for manual login...")
                
                # Wait for user to login by checking for a post-login element
                try:
                    WebDriverWait(self.driver, 120).until(
                        EC.presence_of_element_located((By.ID, "nav-main"))
                    )
                    print("[*] Manual login detected. Proceeding...")
                except TimeoutException:
                    print("[!] Timed out waiting for manual login.")
                    self.driver.quit()
                    return None, "Timed out waiting for manual login"
            else:
                print("[*] Attempting automated login...")
                
                # Wait for login form to load
                wait = WebDriverWait(self.driver, 10)
                
                try:
                    # Find email/username field
                    email_field = wait.until(EC.presence_of_element_located((By.ID, 'ap_email')))
                    email_field.clear()
                    email_field.send_keys(username)
                    
                    # Find password field
                    password_field = self.driver.find_element(By.ID, 'ap_password')
                    password_field.clear()
                    password_field.send_keys(password)
                    
                    # Submit form
                    password_field.submit()
                    
                    print("[*] Login submitted, waiting for response...")
                    time.sleep(5)
                    
                except Exception as e:
                    print(f"[!] Login automation failed: {e}")
                    print("[!] You may need to use debug mode for manual login")
                    return None, f"Login automation failed: {str(e)}"
            
            # If not in debug mode, check for common error conditions
            if not self.debug:
                current_url = self.driver.current_url
                page_source = self.driver.page_source.lower()
                
                if "captcha" in page_source or "robot" in page_source:
                    return None, "CAPTCHA detected. Please try again later or use debug mode."
                
                if "two-step" in page_source or "2fa" in page_source or "verification" in page_source:
                    return None, "Two-factor authentication detected. Please use debug mode for manual verification."
                
                if "sign-in" in current_url and "error" in page_source:
                    return None, "Login failed. Please check your credentials."
            
            # Look for activation token in the current page or redirects
            print("[*] Searching for activation data...")
            
            # Check if we're on the player-auth-token page
            if "player-auth-token" in current_url:
                print("[*] Found player auth token page")
                
                # Try to extract activation bytes from page source or network requests
                page_source = self.driver.page_source
                
                # Look for activation bytes in various formats
                import re
                
                # Pattern 1: Direct activation_bytes in JSON
                json_pattern = r'["\']activation_bytes["\']\\s*:\\s*["\']([A-Fa-f0-9]{8})["\']'
                match = re.search(json_pattern, page_source)
                if match:
                    activation_bytes = match.group(1).upper()
                    print(f"[*] Found activation bytes: {activation_bytes}")
                    return activation_bytes, "Success"
                
                # Pattern 2: Look in script tags or data attributes
                script_pattern = r'["\']([A-Fa-f0-9]{8})["\']'
                matches = re.findall(script_pattern, page_source)
                
                # Filter potential activation bytes (8 hex chars)
                potential_bytes = [m.upper() for m in matches if len(m) == 8 and all(c in '0123456789ABCDEFabcdef' for c in m)]
                
                if potential_bytes:
                    # Take the first valid-looking activation bytes
                    activation_bytes = potential_bytes[0]
                    print(f"[*] Found potential activation bytes: {activation_bytes}")
                    return activation_bytes, "Success (potential match)"
            
            # If direct extraction fails, try to navigate to library and trigger activation
            print("[*] Trying alternative activation method...")
            
            try:
                library_url = f"{self.base_url}library"
                self.driver.get(library_url)
                time.sleep(3)
                
                # Look for any books and try to access them
                # This might trigger activation bytes to be sent
                
                # Check page source again for activation bytes
                page_source = self.driver.page_source
                
                json_pattern = r'["\']activation_bytes["\']\\s*:\\s*["\']([A-Fa-f0-9]{8})["\']'
                match = re.search(json_pattern, page_source)
                if match:
                    activation_bytes = match.group(1).upper()
                    print(f"[*] Found activation bytes in library: {activation_bytes}")
                    return activation_bytes, "Success"
                
            except Exception as e:
                print(f"[!] Alternative method failed: {e}")
            
            return None, "Could not extract activation bytes. The page structure may have changed or your account may not have the required permissions."
            
        except Exception as e:
            return None, f"Extraction failed: {str(e)}"
        
        finally:
            if self.driver:
                self.driver.quit()
    
    def save_activation_bytes(self, activation_bytes, filename="activation_bytes.txt"):
        """Save activation bytes to file"""
        try:
            with open(filename, 'w') as f:
                f.write(activation_bytes)
            return True, f"Activation bytes saved to {filename}"
        except Exception as e:
            return False, f"Failed to save: {str(e)}"

def main():
    """Command line interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract Audible activation bytes using Selenium')
    parser.add_argument('--username', '-u', help='Audible username/email')
    parser.add_argument('--password', '-p', help='Audible password')
    parser.add_argument('--lang', '-l', default='us', help='Language/region (us, uk, de, fr, jp, au, in)')
    parser.add_argument('--debug', '-d', action='store_true', help='Run in debug mode (manual login)')
    parser.add_argument('--firefox', '-f', action='store_true', help='Use Firefox instead of Chrome')
    parser.add_argument('--player-id', help='Custom player ID (hex)')
    
    args = parser.parse_args()
    
    if not args.username:
        args.username = input("Audible username/email: ")
    
    if not args.password:
        import getpass
        args.password = getpass.getpass("Audible password: ")
    
    extractor = SeleniumActivationExtractor(
        lang=args.lang,
        debug=args.debug,
        use_firefox=args.firefox
    )
    
    print("Selenium Audible Activation Bytes Extractor")
    print("=" * 50)
    
    activation_bytes, message = extractor.extract_activation_bytes(
        args.username,
        args.password,
        args.player_id
    )
    
    if activation_bytes:
        print(f"\n✅ SUCCESS!")
        print(f"Activation Bytes: {activation_bytes}")
        
        # Save to file
        saved, save_msg = extractor.save_activation_bytes(activation_bytes)
        if saved:
            print(f"💾 {save_msg}")
        else:
            print(f"⚠️ {save_msg}")
            
        print(f"\nYou can now use these activation bytes with:")
        print(f"ffmpeg -activation_bytes {activation_bytes} -i input.aax output.mp3")
        
    else:
        print(f"\n❌ FAILED: {message}")
        print("\nTroubleshooting tips:")
        print("1. Try running with --debug flag for manual login")
        print("2. Check your username and password")
        print("3. Make sure you have ChromeDriver or Firefox installed")
        print("4. Your account may have 2FA enabled (use --debug)")
        print("5. You may have hit rate limits (wait 30 minutes)")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Audible Activation Bytes Extractor
Based on AAXtoMP3 and similar tools functionality.
Integrates multiple methods to extract activation bytes for .aax file conversion.
"""

import os
import sys
import json
import re
import subprocess
import requests
import time
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import base64
from selenium_activator import SeleniumActivationExtractor

class ActivationBytesExtractor:
    def __init__(self):
        self.activation_bytes = None
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def method_1_audible_cli(self):
        """Method 1: Use audible-cli if available"""
        print("\n=== Method 1: Audible-CLI ===")
        try:
            # Check if audible-cli is available
            result = subprocess.run(['py', '-m', 'audible_cli', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                print("❌ audible-cli not available")
                return None
            
            print("✓ audible-cli found, attempting to get activation bytes...")
            
            # Try to get activation bytes
            result = subprocess.run(['py', '-m', 'audible_cli', 'activation-bytes'], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                output = result.stdout.strip()
                # Extract 8-character hex string from output
                hex_match = re.search(r'\b([0-9A-Fa-f]{8})\b', output)
                if hex_match:
                    activation_bytes = hex_match.group(1).upper()
                    print(f"✅ Success! Activation bytes: {activation_bytes}")
                    return activation_bytes
                else:
                    print(f"⚠️ Command succeeded but no activation bytes found in output: {output}")
            else:
                print(f"❌ Command failed: {result.stderr}")
                if "No such profile" in result.stderr or "auth file" in result.stderr:
                    print("💡 Hint: Run 'py -m audible_cli quickstart' to set up authentication first")
        
        except Exception as e:
            print(f"❌ Error: {e}")
        
        return None
    
    def method_2_manual_auth(self, email=None, password=None):
        """Method 2: Manual authentication with Audible"""
        print("\n=== Method 2: Manual Authentication ===")
        
        if not email:
            email = input("Enter your Audible email: ").strip()
        if not password:
            import getpass
            password = getpass.getpass("Enter your Audible password: ").strip()
        
        if not email or not password:
            print("❌ Email and password required")
            return None
        
        try:
            # Try to authenticate using audible library
            import audible
            
            print("🔐 Authenticating with Audible...")
            
            # Create authenticator
            auth = audible.Authenticator.from_login(
                username=email,
                password=password,
                locale="us",
                with_username=False
            )
            
            print("✓ Authentication successful!")
            
            # Try to get activation bytes from auth object
            if hasattr(auth, 'activation_bytes') and auth.activation_bytes:
                activation_bytes = auth.activation_bytes
                print(f"✅ Activation bytes found: {activation_bytes}")
                return activation_bytes
            
            # Try alternative methods to get activation bytes
            client = audible.Client(auth=auth)
            
            # Method 2a: Check user profile for activation bytes
            try:
                profile = client.get("1.0/customer/information")
                if 'activation_bytes' in profile:
                    activation_bytes = profile['activation_bytes']
                    print(f"✅ Activation bytes from profile: {activation_bytes}")
                    return activation_bytes
            except:
                pass
            
            # Method 2b: Try to get from library endpoint
            try:
                library = client.get("1.0/library", num_results=1)
                # Sometimes activation bytes are in library metadata
                for item in library.get('items', []):
                    if 'activation_bytes' in item:
                        activation_bytes = item['activation_bytes']
                        print(f"✅ Activation bytes from library: {activation_bytes}")
                        return activation_bytes
            except:
                pass
            
            print("⚠️ Authentication successful but activation bytes not found in API response")
            print("💡 Try downloading a book to trigger activation bytes generation")
            
        except ImportError:
            print("❌ 'audible' library not installed. Install with: pip install audible")
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            if "2FA" in str(e) or "captcha" in str(e).lower():
                print("💡 Your account may have 2FA enabled or require captcha verification")
                print("💡 Try using the browser method instead")
        
        return None
    
    def method_2b_selenium_auth(self, email, password, browser='chrome', debug=False):
        """Method 2b: Selenium-based authentication (more reliable)"""
        print("\n=== Method 2b: Selenium Authentication ===")
        
        try:
            # Create Selenium extractor
            use_firefox = (browser.lower() == 'firefox')
            extractor = SeleniumActivationExtractor(lang='de', debug=debug, use_firefox=use_firefox)
            
            print("🔐 Using Selenium to authenticate with Audible...")
            
            activation_bytes, message = extractor.extract_activation_bytes(email, password)
            
            if activation_bytes:
                print(f"✅ Success! Activation bytes: {activation_bytes}")
                return activation_bytes
            else:
                print(f"❌ Selenium extraction failed: {message}")
                if "captcha" in message.lower() or "2fa" in message.lower():
                    print("💡 Try running with debug=True for manual login")
                    
                    # Offer debug mode
                    if not debug:
                        retry = input("Would you like to try debug mode for manual login? (y/n): ").strip().lower()
                        if retry == 'y':
                            return self.method_2b_selenium_auth(email, password, browser=browser, debug=True)
                
        except ImportError:
            print("❌ Selenium not available. Install with: pip install selenium")
            print("💡 Also need ChromeDriver: https://chromedriver.chromium.org/")
        except Exception as e:
            print(f"❌ Selenium extraction failed: {e}")
        
        return None
    
    def method_3_file_search(self):
        """Method 3: Search for activation bytes in existing files"""
        print("\n=== Method 3: File Search ===")
        
        search_locations = [
            Path.home() / "AppData" / "Roaming" / "Audible",
            Path.home() / "AppData" / "Local" / "Audible",
            Path.home() / "AppData" / "Roaming" / "AudibleDownloadManager",
            Path.home() / "Documents",
            Path.home() / "Downloads",
            Path(".")
        ]
        
        found_bytes = set()
        
        for location in search_locations:
            if not location.exists():
                continue
            
            print(f"🔍 Searching in: {location}")
            
            try:
                for file_path in location.rglob("*"):
                    if not file_path.is_file():
                        continue
                    
                    if file_path.suffix.lower() not in ['.json', '.txt', '.log', '.cfg', '.ini', '.xml']:
                        continue
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        # Look for activation bytes patterns
                        patterns = [
                            r'activation.?bytes["\s:=]+([0-9A-Fa-f]{8})',
                            r'"activation.?bytes"["\s:=]+([0-9A-Fa-f]{8})',
                            r'["\s]([0-9A-Fa-f]{8})["\s]',
                        ]
                        
                        for pattern in patterns:
                            matches = re.findall(pattern, content, re.IGNORECASE)
                            for match in matches:
                                if len(match) == 8:
                                    found_bytes.add(match.upper())
                                    print(f"  ✓ Found: {match.upper()} in {file_path.name}")
                    
                    except:
                        continue
            except:
                continue
        
        if found_bytes:
            # Test each found activation bytes
            for bytes_val in found_bytes:
                if self.test_activation_bytes(bytes_val):
                    print(f"✅ Working activation bytes: {bytes_val}")
                    return bytes_val
            
            print("⚠️ Found potential activation bytes but none tested successfully")
            return list(found_bytes)[0]  # Return first one found
        
        print("❌ No activation bytes found in files")
        return None
    
    def method_4_browser_extraction(self):
        """Method 4: Guide user through browser extraction"""
        print("\n=== Method 4: Browser Extraction ===")
        print("This method requires manual steps in your browser:")
        print()
        print("1. Open your browser and go to https://audible.com")
        print("2. Log into your Audible account")
        print("3. Open Developer Tools (F12)")
        print("4. Go to the Network tab and clear it")
        print("5. Try to download or play a book from your library")
        print("6. In the Network tab, search for:")
        print("   - 'activation_bytes'")
        print("   - 'license'")
        print("   - 'drm'")
        print("   - '.aax'")
        print("7. Look for an 8-character hexadecimal string")
        print()
        
        found = input("Did you find activation bytes? (y/n): ").strip().lower()
        if found == 'y':
            activation_bytes = input("Enter the activation bytes: ").strip()
            if activation_bytes and len(activation_bytes) == 8:
                if self.test_activation_bytes(activation_bytes):
                    print(f"✅ Activation bytes verified: {activation_bytes.upper()}")
                    return activation_bytes.upper()
                else:
                    print("⚠️ Activation bytes may not be correct, but saving anyway")
                    return activation_bytes.upper()
        
        return None
    
    def test_activation_bytes(self, activation_bytes):
        """Test activation bytes with a sample .aax file"""
        print(f"🧪 Testing activation bytes: {activation_bytes}")
        
        # Look for .aax files to test with
        test_locations = [
            Path.home() / "Documents",
            Path.home() / "Downloads",
            Path.home() / "Music",
            Path(".")
        ]
        
        aax_files = []
        for location in test_locations:
            if location.exists():
                aax_files.extend(list(location.rglob("*.aax")))
        
        if not aax_files:
            print("  ⚠️ No .aax files found for testing")
            return False
        
        test_file = aax_files[0]
        print(f"  📁 Testing with: {test_file.name}")
        
        try:
            # Try to get file info using ffprobe with activation bytes
            cmd = [
                'ffprobe',
                '-activation_bytes', activation_bytes,
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                str(test_file)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("  ✅ Success! Activation bytes work with this file")
                return True
            else:
                print(f"  ❌ Failed: {result.stderr}")
                return False
        
        except Exception as e:
            print(f"  ❌ Error testing: {e}")
            return False
    
    def save_activation_bytes(self, activation_bytes):
        """Save activation bytes to file"""
        if activation_bytes:
            # Save to multiple locations for convenience
            files_to_save = [
                'activation_bytes.txt',
                Path.home() / 'activation_bytes.txt'
            ]
            
            for file_path in files_to_save:
                try:
                    with open(file_path, 'w') as f:
                        f.write(activation_bytes)
                    print(f"💾 Saved to: {file_path}")
                except:
                    continue
    
    def extract(self, email=None, password=None):
        """Main extraction method - tries all methods"""
        print("🎯 Audible Activation Bytes Extractor")
        print("=" * 50)
        
        methods = [
            self.method_1_audible_cli,
            lambda: self.method_2_manual_auth(email, password) if email and password else None,
            lambda: self.method_2b_selenium_auth(email, password) if email and password else None,
            self.method_3_file_search,
            self.method_4_browser_extraction
        ]
        
        for i, method in enumerate(methods, 1):
            try:
                if method is None:
                    continue
                    
                print(f"\n🔄 Trying method {i}...")
                result = method()
                
                if result:
                    self.activation_bytes = result
                    self.save_activation_bytes(result)
                    print(f"\n🎉 SUCCESS! Activation bytes: {result}")
                    return result
                    
            except KeyboardInterrupt:
                print("\n\n⏹️ Extraction cancelled by user")
                return None
            except Exception as e:
                print(f"❌ Method {i} failed: {e}")
                continue
        
        print("\n❌ Could not extract activation bytes using any method")
        print("\n💡 Alternative suggestions:")
        print("1. Use AAXtoMP3 tool: https://github.com/KrumpetPirate/AAXtoMP3")
        print("2. Use OpenAudible: https://openaudible.org/")
        print("3. Check if you have .aa files (no activation bytes needed)")
        
        return None

def main():
    extractor = ActivationBytesExtractor()
    
    # Check for command line arguments
    email = None
    password = None
    
    if len(sys.argv) > 1:
        email = sys.argv[1]
    if len(sys.argv) > 2:
        password = sys.argv[2]
    
    activation_bytes = extractor.extract(email, password)
    
    if activation_bytes:
        print(f"\n✅ Final result: {activation_bytes}")
        print("You can now use these activation bytes in the Audible Converter app!")
    else:
        print("\n❌ Failed to extract activation bytes")
        sys.exit(1)

if __name__ == "__main__":
    main()

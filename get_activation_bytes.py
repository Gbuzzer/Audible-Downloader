#!/usr/bin/env python3
"""
Script to help extract Audible activation bytes using audible library.
This script provides multiple methods to obtain activation bytes.
"""

import os
import sys
import json
from pathlib import Path

def method1_manual_input():
    """Method 1: Manual input of activation bytes"""
    print("\n=== METHOD 1: Manual Input ===")
    print("If you already know your activation bytes, enter them here.")
    print("Activation bytes are 8 hexadecimal characters (e.g., 1A2B3C4D)")
    
    activation_bytes = input("Enter activation bytes (or press Enter to skip): ").strip()
    
    if activation_bytes:
        if len(activation_bytes) == 8 and all(c in '0123456789ABCDEFabcdef' for c in activation_bytes):
            print(f"✓ Valid activation bytes: {activation_bytes.upper()}")
            return activation_bytes.upper()
        else:
            print("✗ Invalid format. Activation bytes should be 8 hexadecimal characters.")
    
    return None

def method2_browser_instructions():
    """Method 2: Instructions for browser extraction"""
    print("\n=== METHOD 2: Browser Network Tab Extraction ===")
    print("Follow these steps to find activation bytes in your browser:")
    print()
    print("1. Open your browser and go to audible.com")
    print("2. Log into your Audible account")
    print("3. Open Developer Tools (F12)")
    print("4. Go to the Network tab")
    print("5. Clear the network log")
    print("6. Navigate to your library or try to download/play a book")
    print("7. In the Network tab, filter by:")
    print("   - Search for: 'activation_bytes', 'license', 'drm', or '.aax'")
    print("   - Look in request headers, response bodies, and URL parameters")
    print("8. Look for an 8-character hexadecimal string")
    print()
    print("Common locations:")
    print("- Response JSON with key 'activation_bytes'")
    print("- URL parameters in download requests")
    print("- Authorization headers")
    print()
    
    found = input("Did you find activation bytes using this method? (y/n): ").strip().lower()
    if found == 'y':
        activation_bytes = input("Enter the activation bytes you found: ").strip()
        if activation_bytes and len(activation_bytes) == 8:
            return activation_bytes.upper()
    
    return None

def method3_audible_cli_setup():
    """Method 3: Set up audible-cli properly"""
    print("\n=== METHOD 3: Audible-CLI Setup ===")
    print("Let's try to set up audible-cli step by step.")
    print()
    
    # Check if config directory exists
    config_dir = Path.home() / "AppData" / "Roaming" / "Audible"
    print(f"Config directory: {config_dir}")
    
    if not config_dir.exists():
        print("Creating config directory...")
        config_dir.mkdir(parents=True, exist_ok=True)
    
    print("\nTo use audible-cli, you need to:")
    print("1. Set up authentication with your Audible account")
    print("2. This requires your Audible username/email and password")
    print("3. The tool will authenticate and save credentials")
    print()
    
    proceed = input("Do you want to proceed with audible-cli setup? (y/n): ").strip().lower()
    if proceed == 'y':
        print("\nRun this command in a separate terminal:")
        print("py -m audible_cli quickstart")
        print("\nThen follow the prompts to:")
        print("- Enter profile name (default: audible)")
        print("- Enter your Audible email/username")
        print("- Enter your Audible password")
        print("- Select your country/marketplace")
        print()
        print("After setup, run:")
        print("py -m audible_cli activation-bytes")
        print()
        
        setup_done = input("Have you completed the audible-cli setup? (y/n): ").strip().lower()
        if setup_done == 'y':
            try:
                import subprocess
                result = subprocess.run(['py', '-m', 'audible_cli', 'activation-bytes'], 
                                      capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    output = result.stdout.strip()
                    print(f"✓ Activation bytes retrieved: {output}")
                    return output
                else:
                    print(f"✗ Error: {result.stderr}")
            except Exception as e:
                print(f"✗ Error running audible-cli: {e}")
    
    return None

def method4_file_search():
    """Method 4: Search for existing activation bytes in files"""
    print("\n=== METHOD 4: Search Existing Files ===")
    print("Searching for activation bytes in common locations...")
    
    search_paths = [
        Path.home() / "AppData" / "Roaming" / "Audible",
        Path.home() / "AppData" / "Local" / "Audible",
        Path.home() / "Documents",
        Path.home() / "Downloads"
    ]
    
    for search_path in search_paths:
        if search_path.exists():
            print(f"Searching in: {search_path}")
            try:
                for file_path in search_path.rglob("*"):
                    if file_path.is_file() and file_path.suffix.lower() in ['.json', '.txt', '.log', '.cfg', '.ini']:
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                # Look for 8-character hex strings that might be activation bytes
                                import re
                                hex_matches = re.findall(r'\b[0-9A-Fa-f]{8}\b', content)
                                if hex_matches:
                                    print(f"Found potential activation bytes in {file_path}: {hex_matches}")
                        except:
                            continue
            except:
                continue
    
    return None

def save_activation_bytes(activation_bytes):
    """Save activation bytes to a file for the converter app"""
    if activation_bytes:
        with open('activation_bytes.txt', 'w') as f:
            f.write(activation_bytes)
        print(f"\n✓ Activation bytes saved to: activation_bytes.txt")
        print(f"You can now use these in the Audible Converter app: {activation_bytes}")

def main():
    print("Audible Activation Bytes Extractor")
    print("=" * 40)
    print("This script will help you obtain activation bytes for .aax file conversion.")
    print()
    
    activation_bytes = None
    
    # Try different methods
    methods = [
        method1_manual_input,
        method2_browser_instructions,
        method3_audible_cli_setup,
        method4_file_search
    ]
    
    for method in methods:
        if activation_bytes:
            break
        try:
            result = method()
            if result:
                activation_bytes = result
                break
        except KeyboardInterrupt:
            print("\n\nOperation cancelled by user.")
            return
        except Exception as e:
            print(f"Error in method: {e}")
            continue
    
    if activation_bytes:
        save_activation_bytes(activation_bytes)
        print(f"\n🎉 SUCCESS! Your activation bytes are: {activation_bytes}")
        print("\nYou can now use these in the Audible Converter web app.")
    else:
        print("\n❌ Could not obtain activation bytes.")
        print("\nAlternative suggestions:")
        print("1. Try using AAXtoMP3 tool: https://github.com/KrumpetPirate/AAXtoMP3")
        print("2. Use inAudible tool: https://github.com/rmcrackan/inAudible")
        print("3. Check Audible forums for other extraction methods")
        print("4. If you have .aa files instead of .aax, no activation bytes are needed")

if __name__ == "__main__":
    main()

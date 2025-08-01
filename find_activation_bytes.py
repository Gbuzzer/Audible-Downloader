#!/usr/bin/env python3
"""
Simple script to search for existing activation bytes in common locations.
"""

import os
import re
from pathlib import Path

def search_for_activation_bytes():
    """Search for activation bytes in common file locations"""
    
    print("Searching for activation bytes in common locations...")
    print("=" * 50)
    
    # Common search locations
    search_locations = [
        Path.home() / "AppData" / "Roaming" / "Audible",
        Path.home() / "AppData" / "Local" / "Audible", 
        Path.home() / "AppData" / "Roaming" / "AudibleDownloadManager",
        Path.home() / "Documents",
        Path.home() / "Downloads",
        Path(".")  # Current directory
    ]
    
    # File extensions to search
    file_extensions = ['.json', '.txt', '.log', '.cfg', '.ini', '.xml', '.plist']
    
    found_bytes = []
    
    for location in search_locations:
        if not location.exists():
            continue
            
        print(f"\nSearching in: {location}")
        
        try:
            # Search files in this location
            for file_path in location.rglob("*"):
                if not file_path.is_file():
                    continue
                    
                if file_path.suffix.lower() not in file_extensions:
                    continue
                
                try:
                    # Try to read file
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # Look for activation bytes patterns
                    patterns = [
                        r'activation.?bytes["\s:=]+([0-9A-Fa-f]{8})',  # activation_bytes: "12345678"
                        r'"activation.?bytes"["\s:=]+([0-9A-Fa-f]{8})',  # "activation_bytes": "12345678"
                        r'["\s]([0-9A-Fa-f]{8})["\s]',  # Any 8-char hex string
                        r'bytes["\s:=]+([0-9A-Fa-f]{8})',  # bytes: "12345678"
                    ]
                    
                    for pattern in patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        for match in matches:
                            if len(match) == 8 and match not in found_bytes:
                                found_bytes.append(match.upper())
                                print(f"  ✓ Found potential activation bytes: {match.upper()} in {file_path.name}")
                
                except Exception as e:
                    # Skip files that can't be read
                    continue
                    
        except Exception as e:
            print(f"  Error searching {location}: {e}")
            continue
    
    return found_bytes

def test_activation_bytes(activation_bytes):
    """Test if activation bytes work with a sample .aax file"""
    print(f"\nTesting activation bytes: {activation_bytes}")
    
    # Look for .aax files in common locations
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
        print("  No .aax files found for testing")
        return False
    
    test_file = aax_files[0]
    print(f"  Testing with file: {test_file.name}")
    
    try:
        import subprocess
        
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
            print(f"  ✓ Activation bytes work! File can be read.")
            return True
        else:
            print(f"  ✗ Activation bytes failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"  Error testing: {e}")
        return False

def main():
    print("Activation Bytes Finder")
    print("=" * 30)
    
    # Search for activation bytes
    found_bytes = search_for_activation_bytes()
    
    if found_bytes:
        print(f"\n🎉 Found {len(found_bytes)} potential activation bytes:")
        for i, bytes_val in enumerate(found_bytes, 1):
            print(f"  {i}. {bytes_val}")
        
        # Test each one
        print("\nTesting activation bytes...")
        working_bytes = []
        
        for bytes_val in found_bytes:
            if test_activation_bytes(bytes_val):
                working_bytes.append(bytes_val)
        
        if working_bytes:
            print(f"\n✅ Working activation bytes found:")
            for bytes_val in working_bytes:
                print(f"  {bytes_val}")
                
                # Save to file
                with open('activation_bytes.txt', 'w') as f:
                    f.write(bytes_val)
                print(f"  Saved to: activation_bytes.txt")
                break
        else:
            print("\n⚠ Found potential bytes but none tested successfully.")
            print("You can still try them manually in the converter app.")
    else:
        print("\n❌ No activation bytes found in searched locations.")
        print("\nTry these alternatives:")
        print("1. Run: py manual_audible_setup.py")
        print("2. Use browser method to extract from audible.com")
        print("3. Check if you have .aa files instead (no activation bytes needed)")

if __name__ == "__main__":
    main()

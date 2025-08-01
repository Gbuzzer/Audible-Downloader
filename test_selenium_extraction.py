#!/usr/bin/env python3
"""
Test script for Selenium-based Audible Activation Bytes Extraction
"""

import sys
import os

# Add the current directory to the Python path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from selenium_activator import SeleniumActivationExtractor

def test_selenium_extraction():
    """Test the Selenium-based activation bytes extraction"""
    print("Testing Selenium-based Audible Activation Bytes Extraction")
    print("=" * 60)
    
    # Initialize the extractor
    extractor = SeleniumActivationExtractor(debug=True)  # Use debug mode for testing
    
    # Check dependencies
    deps_ok, deps_msg = extractor.check_dependencies()
    print(f"Dependencies check: {deps_msg}")
    
    if not deps_ok:
        print(f"Error: {deps_msg}")
        return
    
    print("\nDependencies are OK. The Selenium-based extraction should work correctly.")
    print("To test with real credentials, run the selenium_activator.py script directly.")

if __name__ == "__main__":
    test_selenium_extraction()

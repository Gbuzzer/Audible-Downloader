# Selenium Setup Guide for Activation Bytes Extraction

This guide will help you set up Selenium WebDriver for automated activation bytes extraction from Audible.

## Overview

The Selenium-based extraction method automates the login process to Audible and extracts activation bytes directly from the server response. This is more reliable than manual methods, especially for accounts with 2FA or CAPTCHA protection.

## Prerequisites

1. **Python packages** (install via requirements.txt)
2. **Web browser** (Chrome or Firefox)

## Installation Steps

### Step 1: Install Python Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- `selenium==4.15.0` - Web automation framework
- `audible==0.8.2` - Audible API library
- `webdriver-manager==4.0.2` - Automatic WebDriver management

### Step 2: Install Chrome or Firefox (Recommended)

With `webdriver-manager`, you no longer need to manually install ChromeDriver or GeckoDriver. The tool will automatically download and manage the appropriate driver for your browser.

1. **Install Google Chrome**: https://www.google.com/chrome/ OR
2. **Install Firefox**: https://www.mozilla.org/firefox/

That's it! The `webdriver-manager` package will automatically handle driver installation when you run the extraction script.

### Manual Driver Installation (Alternative)

If you prefer to manually manage drivers, follow these steps:

1. **Download Google Chrome**: https://www.google.com/chrome/
2. **Check Chrome version**: 
   - Open Chrome → Help → About Google Chrome
   - Note the version number (e.g., 119.0.6045.105)

3. **Download ChromeDriver**:
   - Go to: https://chromedriver.chromium.org/downloads
   - Download the version matching your Chrome version
   - Extract `chromedriver.exe` to the project folder

4. **Verify Installation**:
   ```bash
   # Test ChromeDriver
   chromedriver --version
   ```

### Step 3: Alternative - Firefox Setup

If you prefer Firefox over Chrome:

1. **Install Firefox**: https://www.mozilla.org/firefox/

With `webdriver-manager`, GeckoDriver will be automatically downloaded and managed when you run the extraction script.

## Usage

### Method 1: Web Interface

1. Start the app: `python app.py`
2. Open browser: http://127.0.0.1:5000
3. Click "Extract" → "Extract with Selenium (Recommended)"
4. Enter your Audible email and password
5. Click "Extract with Selenium"

### Method 2: Command Line

```bash
# Direct Selenium extraction
python selenium_activator.py --username your@email.com --password yourpassword

# Debug mode (manual login)
python selenium_activator.py --username your@email.com --debug

# Use Firefox instead of Chrome
python selenium_activator.py --username your@email.com --firefox

# Different region
python selenium_activator.py --username your@email.com --lang uk
```

### Method 3: Python Script

```python
from selenium_activator import SeleniumActivationExtractor

extractor = SeleniumActivationExtractor(debug=False)
activation_bytes, message = extractor.extract_activation_bytes("your@email.com", "password")

if activation_bytes:
    print(f"Success: {activation_bytes}")
else:
    print(f"Failed: {message}")
```

## Supported Regions

- `us` - United States (default)
- `uk` - United Kingdom  
- `au` - Australia
- `de` - Germany
- `fr` - France
- `jp` - Japan
- `in` - India

## Troubleshooting

### Common Issues

#### 1. ChromeDriver Version Mismatch
```
selenium.common.exceptions.SessionNotCreatedException: Message: session not created: This version of ChromeDriver only supports Chrome version X
```

**Solution**: Download the correct ChromeDriver version for your Chrome browser.

#### 2. ChromeDriver Not Found
```
selenium.common.exceptions.WebDriverException: Message: 'chromedriver' executable needs to be in PATH
```

**Solutions**:
- Place `chromedriver.exe` in the project folder
- Add ChromeDriver to your system PATH
- Use `webdriver-manager` for automatic management

#### 3. Login Issues

**CAPTCHA Detected**:
```bash
python selenium_activator.py --username your@email.com --debug
```
This opens a browser window for manual login.

**Two-Factor Authentication**:
- Use debug mode for manual 2FA entry
- Some accounts may require app-specific passwords

**Rate Limiting**:
- Wait 30 minutes between attempts
- Audible may temporarily block automated logins

#### 4. Headless Mode Issues

If headless mode fails, try with visible browser:
```python
extractor = SeleniumActivationExtractor(debug=True)  # Shows browser window
```

### Debug Mode

For accounts with 2FA, CAPTCHA, or other security measures:

```bash
python selenium_activator.py --username your@email.com --debug
```

This will:
1. Open a visible browser window
2. Navigate to the login page
3. Wait for you to manually complete login
4. Extract activation bytes after successful login

## Security Notes

1. **Credentials**: Never hardcode credentials in scripts
2. **Rate Limits**: Don't make too many requests (max 1-2 per hour)
3. **2FA**: Use app-specific passwords if available
4. **VPN**: Some regions may require VPN for access

## Alternative Methods

If Selenium fails, try these alternatives:

1. **Browser Network Tab Method**: Manual extraction via developer tools
2. **audible-cli**: Command-line tool (requires separate setup)
3. **File Search**: Look for existing activation bytes in system files
4. **AAXtoMP3**: External tool with built-in extraction

## Files Created

- `activation_bytes.txt` - Saved activation bytes
- `selenium_activator.py` - Main Selenium extraction script
- Browser cache/logs (temporary)

## Performance Tips

1. **Use Chrome**: Generally faster and more reliable than Firefox
2. **Headless Mode**: Faster execution (disable for debugging only)
3. **Reuse Activation Bytes**: Extract once, save for future use
4. **Regional Servers**: Use correct region for better performance

## Legal Notice

This tool is for personal use only. Use your own Audible account and activation bytes only for your legally purchased audiobooks. Do not share activation bytes or use them for piracy.

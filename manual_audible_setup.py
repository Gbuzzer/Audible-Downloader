#!/usr/bin/env python3
"""
Manual setup script for audible-cli to avoid interactive prompts.
This creates the necessary configuration files programmatically.
"""

import os
import json
from pathlib import Path
import getpass

def create_audible_config():
    """Create basic audible-cli configuration"""
    
    # Create config directory
    config_dir = Path.home() / "AppData" / "Roaming" / "Audible"
    config_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Config directory: {config_dir}")
    
    # Basic config.toml content
    config_content = """
[APP]
primary_profile = "audible"

[profile.audible]
auth_file = "audible.json"
country_code = "us"
"""
    
    config_file = config_dir / "config.toml"
    with open(config_file, 'w') as f:
        f.write(config_content.strip())
    
    print(f"Created config file: {config_file}")
    
    # Now we need to create an auth file
    print("\nTo complete the setup, you need to provide your Audible credentials.")
    print("This is required to authenticate with Audible and get activation bytes.")
    print()
    
    email = input("Enter your Audible email/username: ").strip()
    if not email:
        print("Email is required. Exiting.")
        return False
    
    password = getpass.getpass("Enter your Audible password: ").strip()
    if not password:
        print("Password is required. Exiting.")
        return False
    
    # Try to authenticate using the audible library directly
    try:
        import audible
        
        print("\nAuthenticating with Audible...")
        
        # Create auth object
        auth = audible.Authenticator.from_login(
            username=email,
            password=password,
            locale="us",
            with_username=False
        )
        
        # Save auth file
        auth_file = config_dir / "audible.json"
        auth.to_file(auth_file)
        
        print(f"✓ Authentication successful! Auth file saved to: {auth_file}")
        
        # Now try to get activation bytes
        print("\nTrying to get activation bytes...")
        
        try:
            client = audible.Client(auth=auth)
            
            # Try to get activation bytes
            # This might require additional API calls or different methods
            # depending on the audible library version
            
            # Method 1: Check if activation bytes are in auth
            if hasattr(auth, 'activation_bytes'):
                activation_bytes = auth.activation_bytes
                if activation_bytes:
                    print(f"✓ Activation bytes found: {activation_bytes}")
                    return activation_bytes
            
            # Method 2: Try to get from client
            if hasattr(client, 'get_activation_bytes'):
                activation_bytes = client.get_activation_bytes()
                if activation_bytes:
                    print(f"✓ Activation bytes found: {activation_bytes}")
                    return activation_bytes
            
            print("⚠ Authentication successful but activation bytes not found in this session.")
            print("Try running: py -m audible_cli activation-bytes")
            
        except Exception as e:
            print(f"⚠ Error getting activation bytes: {e}")
            print("Try running: py -m audible_cli activation-bytes")
        
        return True
        
    except Exception as e:
        print(f"✗ Authentication failed: {e}")
        print("\nPossible issues:")
        print("1. Incorrect email/password")
        print("2. Two-factor authentication enabled (not supported by this method)")
        print("3. Account locked or requires verification")
        print("\nTry the manual browser method instead.")
        return False

def main():
    print("Manual Audible-CLI Setup")
    print("=" * 30)
    print("This script will set up audible-cli configuration manually.")
    print()
    
    result = create_audible_config()
    
    if result:
        print("\n✓ Setup completed successfully!")
        print("\nNext steps:")
        print("1. Run: py -m audible_cli activation-bytes")
        print("2. If that doesn't work, try the browser method in get_activation_bytes.py")
    else:
        print("\n❌ Setup failed. Try alternative methods.")

if __name__ == "__main__":
    main()

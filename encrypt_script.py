import base64
import os
from cryptography.fernet import Fernet

def encrypt_script():
    # Generate key
    key = Fernet.generate_key()
    cipher_suite = Fernet(key)
    
    # Read main.py
    with open('main.py', 'rb') as file:
        script_content = file.read()
    
    # Encrypt the content
    encrypted_content = cipher_suite.encrypt(script_content)
    
    # Save encrypted content
    with open('encrypted_main.bin', 'wb') as file:
        file.write(encrypted_content)
    
    # Save key separately
    with open('script.key', 'wb') as file:
        file.write(key)
    
    print("Script encrypted successfully!")
    
if __name__ == "__main__":
    encrypt_script() 
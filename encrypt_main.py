from cryptography.fernet import Fernet
import base64

def encrypt_main():
    # Generate key
    key = Fernet.generate_key()
    cipher_suite = Fernet(key)
    
    # Read main.py
    with open('main.py', 'rb') as file:
        script_content = file.read()
    
    # Encrypt the content
    encrypted_content = cipher_suite.encrypt(script_content)
    
    # Save encrypted content
    with open('main.enc', 'wb') as file:
        file.write(encrypted_content)
    
    # Save key
    with open('main.key', 'wb') as file:
        file.write(key)
    
    print("✅ Main script encrypted successfully!")

if __name__ == "__main__":
    encrypt_main() 
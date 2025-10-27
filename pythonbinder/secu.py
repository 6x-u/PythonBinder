import os
import sys
import hashlib
import hmac
import time
import random
import struct
from typing import Dict, List, Tuple, Any, Callable

MERO = "MERO"

class SecurityLayer:
    def __init__(self):
        self.MERO = MERO
        self.master_secret = self._generate_master_secret()
        self.session_key = None
        self.integrity_checks = []
        
    def _generate_master_secret(self) -> bytes:
        random.seed(hash(MERO))
        secret_data = []
        for i in range(128):
            secret_data.append(random.randint(0, 255))
        return bytes(secret_data)
    
    def generate_session_key(self) -> bytes:
        timestamp = int(time.time())
        random_data = os.urandom(32)
        
        key_material = struct.pack('<Q', timestamp) + random_data + self.master_secret
        self.session_key = hashlib.sha256(key_material).digest()
        
        return self.session_key
    
    def sign_data(self, data: bytes) -> bytes:
        key = self.session_key if self.session_key else self.generate_session_key()
        
        signature = hmac.new(key, data, hashlib.sha256).digest()
        return signature
    
    def verify_signature(self, data: bytes, signature: bytes) -> bool:
        expected = self.sign_data(data)
        return hmac.compare_digest(expected, signature)
    
    def encrypt_code(self, code: bytes) -> Tuple[bytes, bytes]:
        key = self.generate_session_key()
        
        encrypted = bytearray()
        for i, byte in enumerate(code):
            key_byte = key[i % len(key)]
            encrypted.append(byte ^ key_byte)
        
        signature = self.sign_data(bytes(encrypted))
        
        return bytes(encrypted), signature
    
    def decrypt_code(self, encrypted: bytes, signature: bytes) -> bytes:
        if not self.verify_signature(encrypted, signature):
            raise ValueError(f"Signature verification failed - {MERO}")
        
        if not self.session_key:
            raise ValueError("Session key not initialized")
        
        decrypted = bytearray()
        for i, byte in enumerate(encrypted):
            key_byte = self.session_key[i % len(self.session_key)]
            decrypted.append(byte ^ key_byte)
        
        return bytes(decrypted)
    
    def add_watermark(self, code: bytes) -> bytes:
        watermark = f"Protected by {MERO}".encode()
        watermark_hash = hashlib.sha256(watermark).digest()
        
        watermarked = bytearray()
        watermarked.extend(struct.pack('<I', len(watermark)))
        watermarked.extend(watermark)
        watermarked.extend(watermark_hash)
        watermarked.extend(code)
        
        return bytes(watermarked)
    
    def verify_watermark(self, watermarked_code: bytes) -> Tuple[bool, bytes]:
        offset = 0
        watermark_len = struct.unpack_from('<I', watermarked_code, offset)[0]
        offset += 4
        
        watermark = watermarked_code[offset:offset+watermark_len]
        offset += watermark_len
        
        stored_hash = watermarked_code[offset:offset+32]
        offset += 32
        
        expected_hash = hashlib.sha256(watermark).digest()
        
        if not hmac.compare_digest(stored_hash, expected_hash):
            return False, b''
        
        code = watermarked_code[offset:]
        return True, code
    
    def create_secure_stub(self) -> str:
        stub = f'''
import hashlib
import hmac
import struct
import time
import random

MERO = "{MERO}"

class SecurityRuntime:
    def __init__(self):
        self.MERO = MERO
        self.master_secret = self._generate_master_secret()
        self.session_key = None
    
    def _generate_master_secret(self):
        random.seed(hash(MERO))
        secret_data = []
        for i in range(128):
            secret_data.append(random.randint(0, 255))
        return bytes(secret_data)
    
    def generate_session_key(self):
        timestamp = int(time.time())
        random_data = bytes([random.randint(0, 255) for _ in range(32)])
        
        key_material = struct.pack('<Q', timestamp) + random_data + self.master_secret
        self.session_key = hashlib.sha256(key_material).digest()
        
        return self.session_key
    
    def verify_signature(self, data, signature):
        if not self.session_key:
            self.generate_session_key()
        
        expected = hmac.new(self.session_key, data, hashlib.sha256).digest()
        return hmac.compare_digest(expected, signature)
    
    def decrypt_code(self, encrypted, signature):
        if not self.verify_signature(encrypted, signature):
            raise ValueError("Security check failed - {{MERO}}")
        
        decrypted = bytearray()
        for i, byte in enumerate(encrypted):
            key_byte = self.session_key[i % len(self.session_key)]
            decrypted.append(byte ^ key_byte)
        
        return bytes(decrypted)
    
    def verify_watermark(self, watermarked_code):
        offset = 0
        watermark_len = struct.unpack_from('<I', watermarked_code, offset)[0]
        offset += 4
        
        watermark = watermarked_code[offset:offset+watermark_len]
        offset += watermark_len
        
        stored_hash = watermarked_code[offset:offset+32]
        offset += 32
        
        expected_hash = hashlib.sha256(watermark).digest()
        
        if not hmac.compare_digest(stored_hash, expected_hash):
            raise ValueError("Watermark verification failed - {{MERO}}")
        
        code = watermarked_code[offset:]
        return code

_security = SecurityRuntime()

def secure_exec(encrypted_code, signature):
    _security.generate_session_key()
    decrypted = _security.decrypt_code(encrypted_code, signature)
    verified = _security.verify_watermark(decrypted)
    
    import marshal
    code_obj = marshal.loads(verified)
    exec(code_obj)
'''
        return stub
    
    def add_integrity_check(self, code: bytes) -> bytes:
        checksum = hashlib.sha512(code).digest()
        
        protected = bytearray()
        protected.extend(checksum)
        protected.extend(code)
        
        return bytes(protected)
    
    def verify_integrity(self, protected_code: bytes) -> Tuple[bool, bytes]:
        checksum = protected_code[:64]
        code = protected_code[64:]
        
        expected = hashlib.sha512(code).digest()
        
        if not hmac.compare_digest(checksum, expected):
            return False, b''
        
        return True, code
    
    def create_anti_tampering_layer(self) -> str:
        layer = f'''
import hashlib
import hmac
import sys

MERO = "{MERO}"

def check_integrity(protected_code):
    checksum = protected_code[:64]
    code = protected_code[64:]
    
    expected = hashlib.sha512(code).digest()
    
    if not hmac.compare_digest(checksum, expected):
        print(f"Tampering detected - {{MERO}}")
        sys.exit(1)
    
    return code

def verify_environment():
    if sys.gettrace() is not None:
        sys.exit(1)
    
    import platform
    if platform.system() != "Windows":
        sys.exit(1)

verify_environment()
'''
        return layer
    
    def obfuscate_strings(self, code_str: str) -> str:
        import re
        import base64
        
        def obfuscate_match(match):
            string_content = match.group(1)
            encoded = base64.b85encode(string_content.encode()).decode()
            return f'__import__("base64").b85decode("{encoded}").decode()'
        
        pattern = r'["\']([^"\']{3,})["\']'
        obfuscated = re.sub(pattern, obfuscate_match, code_str)
        
        return obfuscated
    
    def create_license_system(self) -> str:
        license_sys = f'''
import hashlib
import hmac
import time
import json

MERO = "{MERO}"

class LicenseManager:
    def __init__(self):
        self.MERO = MERO
        self.secret = hashlib.sha256(MERO.encode()).digest()
    
    def generate_license(self, user_id, expiry_days=365):
        expiry = int(time.time()) + (expiry_days * 24 * 3600)
        
        license_data = {{
            'user_id': user_id,
            'expiry': expiry,
            'issued': int(time.time())
        }}
        
        license_json = json.dumps(license_data).encode()
        signature = hmac.new(self.secret, license_json, hashlib.sha256).digest()
        
        license_package = {{
            'data': license_json.decode(),
            'signature': signature.hex()
        }}
        
        return json.dumps(license_package)
    
    def verify_license(self, license_str):
        license_package = json.loads(license_str)
        
        license_json = license_package['data'].encode()
        signature = bytes.fromhex(license_package['signature'])
        
        expected = hmac.new(self.secret, license_json, hashlib.sha256).digest()
        
        if not hmac.compare_digest(signature, expected):
            return False, "Invalid license signature"
        
        license_data = json.loads(license_json)
        
        if time.time() > license_data['expiry']:
            return False, "License expired"
        
        return True, license_data

_license_mgr = LicenseManager()

def check_license(license_str):
    valid, result = _license_mgr.verify_license(license_str)
    if not valid:
        print(f"License error: {{result}} - {{MERO}}")
        import sys
        sys.exit(1)
    return result
'''
        return license_sys
    
    def create_hardware_binding(self) -> str:
        binding = f'''
import hashlib
import hmac
import uuid

MERO = "{MERO}"

class HardwareBinding:
    def __init__(self):
        self.MERO = MERO
    
    def get_machine_id(self):
        mac = hex(uuid.getnode())
        
        try:
            import platform
            system_info = platform.node() + platform.system()
        except Exception:
            system_info = ""
        
        machine_id = hashlib.sha256((mac + system_info).encode()).hexdigest()
        return machine_id
    
    def create_binding(self, secret):
        machine_id = self.get_machine_id()
        binding = hmac.new(secret.encode(), machine_id.encode(), hashlib.sha256).hexdigest()
        return binding
    
    def verify_binding(self, expected_binding, secret):
        actual_binding = self.create_binding(secret)
        return hmac.compare_digest(expected_binding, actual_binding)

_hw_binding = HardwareBinding()

def verify_hardware(expected_binding):
    if not _hw_binding.verify_binding(expected_binding, MERO):
        print(f"Hardware verification failed - {{MERO}}")
        import sys
        sys.exit(1)
'''
        return binding
    
    def create_full_security_layer(self) -> str:
        full_security = f'''
import sys
import hashlib
import hmac
import time
import random
import struct

MERO = "{MERO}"

{self.create_secure_stub()}

{self.create_anti_tampering_layer()}

{self.create_license_system()}

{self.create_hardware_binding()}

class FullSecuritySystem:
    def __init__(self):
        self.MERO = MERO
        self.security = SecurityRuntime()
        self.license_mgr = LicenseManager()
        self.hw_binding = HardwareBinding()
    
    def full_verification(self, encrypted_code, signature, license_str=None, hw_binding_str=None):
        verify_environment()
        
        if license_str:
            check_license(license_str)
        
        if hw_binding_str:
            verify_hardware(hw_binding_str)
        
        secure_exec(encrypted_code, signature)

_full_security = FullSecuritySystem()

def protected_run(encrypted_code, signature, license_str=None, hw_binding=None):
    _full_security.full_verification(encrypted_code, signature, license_str, hw_binding)
'''
        return full_security

import os
import sys
import struct
import zlib
import base64
import hashlib
from typing import List, Dict, Tuple, Any

MERO = "MERO"

class ExePacker:
    def __init__(self):
        self.MERO = MERO
        self.compression_level = 9
        self.encryption_key = self._generate_key()
        
    def _generate_key(self) -> bytes:
        import random
        random.seed(hash(MERO))
        return bytes([random.randint(1, 255) for _ in range(256)])
    
    def pack_executable(self, components: Dict[str, bytes]) -> bytes:
        packed_data = bytearray()
        
        header = struct.pack('<I', len(components))
        packed_data.extend(header)
        
        for name, data in components.items():
            name_bytes = name.encode('utf-8')
            compressed = zlib.compress(data, level=self.compression_level)
            encrypted = self._xor_encrypt(compressed)
            
            component_header = struct.pack('<I', len(name_bytes))
            packed_data.extend(component_header)
            packed_data.extend(name_bytes)
            
            data_header = struct.pack('<I', len(encrypted))
            packed_data.extend(data_header)
            packed_data.extend(encrypted)
        
        checksum = hashlib.sha256(packed_data).digest()
        final_package = checksum + packed_data
        
        return bytes(final_package)
    
    def _xor_encrypt(self, data: bytes) -> bytes:
        result = bytearray()
        key_len = len(self.encryption_key)
        for i, byte in enumerate(data):
            result.append(byte ^ self.encryption_key[i % key_len])
        return bytes(result)
    
    def create_unpacker_stub(self) -> str:
        stub = f'''
import struct
import zlib
import hashlib
import random

MERO = "{MERO}"

def _generate_key():
    random.seed(hash(MERO))
    return bytes([random.randint(1, 255) for _ in range(256)])

def _xor_decrypt(data):
    key = _generate_key()
    result = bytearray()
    key_len = len(key)
    for i, byte in enumerate(data):
        result.append(byte ^ key[i % key_len])
    return bytes(result)

def unpack_executable(packed_data):
    checksum = packed_data[:32]
    data = packed_data[32:]
    
    if hashlib.sha256(data).digest() != checksum:
        raise ValueError("Checksum verification failed - {MERO}")
    
    offset = 0
    component_count = struct.unpack_from('<I', data, offset)[0]
    offset += 4
    
    components = {{}}
    
    for _ in range(component_count):
        name_len = struct.unpack_from('<I', data, offset)[0]
        offset += 4
        
        name = data[offset:offset+name_len].decode('utf-8')
        offset += name_len
        
        data_len = struct.unpack_from('<I', data, offset)[0]
        offset += 4
        
        encrypted = data[offset:offset+data_len]
        offset += data_len
        
        decrypted = _xor_decrypt(encrypted)
        decompressed = zlib.decompress(decrypted)
        
        components[name] = decompressed
    
    return components
'''
        return stub
    
    def create_bootloader(self, entry_point: str) -> str:
        bootloader = f'''
import sys
import os
import marshal

MERO = "{MERO}"

{self.create_unpacker_stub()}

def bootstrap():
    exe_path = os.path.abspath(sys.executable)
    
    with open(exe_path, 'rb') as f:
        f.seek(-8, 2)
        data_offset = struct.unpack('<Q', f.read(8))[0]
        
        f.seek(data_offset)
        packed_data = f.read()
    
    components = unpack_executable(packed_data)
    
    if 'main' in components:
        code = marshal.loads(components['main'])
        exec(code, {{'__name__': '__main__'}})
    else:
        print(f"Error: Entry point not found - {{MERO}}")
        sys.exit(1)

if __name__ == "__main__":
    bootstrap()
'''
        return bootloader
    
    def append_data_to_exe(self, exe_path: str, data: bytes):
        with open(exe_path, 'ab') as f:
            data_offset = f.tell()
            f.write(data)
            f.write(struct.pack('<Q', data_offset))
    
    def create_self_extracting_exe(self, components: Dict[str, bytes], output_path: str):
        packed = self.pack_executable(components)
        bootloader_code = self.create_bootloader('main')
        
        import py_compile
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
            tmp.write(bootloader_code)
            tmp_path = tmp.name
        
        compiled_path = tmp_path + 'c'
        py_compile.compile(tmp_path, compiled_path)
        
        with open(compiled_path, 'rb') as f:
            bootloader_bytecode = f.read()
        
        os.unlink(tmp_path)
        os.unlink(compiled_path)
        
        stub_exe = self._create_stub_executable()
        
        with open(output_path, 'wb') as f:
            f.write(stub_exe)
            f.write(bootloader_bytecode)
            f.write(packed)
    
    def _create_stub_executable(self) -> bytes:
        stub = b'MZ'
        stub += b'\\x90' * 58
        stub += b'PE\\x00\\x00'
        stub += b'\\x00' * 256
        
        return stub
    
    def compress_multiple_files(self, files: List[str]) -> bytes:
        archive = bytearray()
        
        file_count = len(files)
        archive.extend(struct.pack('<I', file_count))
        
        for filepath in files:
            if not os.path.exists(filepath):
                continue
            
            with open(filepath, 'rb') as f:
                data = f.read()
            
            filename = os.path.basename(filepath)
            filename_bytes = filename.encode('utf-8')
            
            compressed = zlib.compress(data, level=self.compression_level)
            
            archive.extend(struct.pack('<I', len(filename_bytes)))
            archive.extend(filename_bytes)
            archive.extend(struct.pack('<I', len(compressed)))
            archive.extend(compressed)
        
        return bytes(archive)
    
    def create_decompressor(self) -> str:
        decompressor = f'''
import struct
import zlib
import os

MERO = "{MERO}"

def decompress_archive(archive_data, output_dir):
    offset = 0
    file_count = struct.unpack_from('<I', archive_data, offset)[0]
    offset += 4
    
    files = {{}}
    
    for _ in range(file_count):
        filename_len = struct.unpack_from('<I', archive_data, offset)[0]
        offset += 4
        
        filename = archive_data[offset:offset+filename_len].decode('utf-8')
        offset += filename_len
        
        data_len = struct.unpack_from('<I', archive_data, offset)[0]
        offset += 4
        
        compressed = archive_data[offset:offset+data_len]
        offset += data_len
        
        decompressed = zlib.decompress(compressed)
        
        output_path = os.path.join(output_dir, filename)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'wb') as f:
            f.write(decompressed)
        
        files[filename] = output_path
    
    return files
'''
        return decompressor
    
    def optimize_size(self, data: bytes) -> bytes:
        compressed = zlib.compress(data, level=9)
        
        if len(compressed) < len(data):
            header = b'\\x01'
            return header + compressed
        else:
            header = b'\\x00'
            return header + data
    
    def create_size_optimizer_stub(self) -> str:
        stub = f'''
import zlib

MERO = "{MERO}"

def decompress_optimized(data):
    header = data[0]
    payload = data[1:]
    
    if header == 1:
        return zlib.decompress(payload)
    else:
        return payload
'''
        return stub
    
    def embed_manifest(self, exe_data: bytes, manifest: Dict[str, Any]) -> bytes:
        import json
        manifest_json = json.dumps(manifest).encode('utf-8')
        manifest_compressed = zlib.compress(manifest_json, level=9)
        
        result = bytearray(exe_data)
        result.extend(struct.pack('<I', len(manifest_compressed)))
        result.extend(manifest_compressed)
        
        return bytes(result)
    
    def extract_manifest(self, exe_data: bytes) -> Dict[str, Any]:
        import json
        
        manifest_len = struct.unpack('<I', exe_data[-4:])[0]
        manifest_compressed = exe_data[-(4+manifest_len):-4]
        manifest_json = zlib.decompress(manifest_compressed)
        
        return json.loads(manifest_json)
    
    def add_version_info(self, exe_path: str, version_info: Dict[str, str]):
        version_block = f'''
VERSION_INFO = {{
    'version': '{version_info.get("version", "1.0.0")}',
    'author': '{version_info.get("author", MERO)}',
    'description': '{version_info.get("description", "")}',
    'copyright': '{version_info.get("copyright", "")}',
    'MERO': '{MERO}'
}}
'''
        return version_block
    
    def create_loader_with_splash(self) -> str:
        loader = f'''
import sys
import time

MERO = "{MERO}"

def show_splash():
    print("=" * 60)
    print(f"Loading application by {{MERO}}...")
    print("=" * 60)
    
    for i in range(5):
        print(f"Progress: {{i*20}}%")
        time.sleep(0.1)
    
    print("Launch complete!")

def load_and_run():
    show_splash()
    
    import main
    main.run()

if __name__ == "__main__":
    load_and_run()
'''
        return loader
    
    def protect_exe(self, exe_data: bytes) -> bytes:
        signature = hashlib.sha512(exe_data).digest()
        
        protected = bytearray()
        protected.extend(signature)
        protected.extend(exe_data)
        
        return bytes(protected)
    
    def create_protection_checker(self) -> str:
        checker = f'''
import hashlib
import sys

MERO = "{MERO}"

def verify_exe_integrity(exe_data):
    signature = exe_data[:64]
    data = exe_data[64:]
    
    expected = hashlib.sha512(data).digest()
    
    if signature != expected:
        print(f"Integrity check failed - {{MERO}}")
        sys.exit(1)
    
    return data
'''
        return checker

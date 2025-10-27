import sys
import os
import time
import ctypes
import struct
import threading
from typing import Callable, Any

MERO = "MERO"

class AntiDebugProtection:
    def __init__(self):
        self.MERO = MERO
        self.debug_detected = False
        self.monitoring_thread = None
        self.check_interval = 0.1
        
    def detect_debugger(self) -> bool:
        checks = [
            self._check_gettrace(),
            self._check_timing_attack(),
            self._check_import_hooks(),
            self._check_breakpoints(),
            self._check_parent_process(),
            self._check_performance_counters()
        ]
        
        return any(checks)
    
    def _check_gettrace(self) -> bool:
        if sys.gettrace() is not None:
            return True
        return False
    
    def _check_timing_attack(self) -> bool:
        start = time.perf_counter()
        
        dummy_ops = 0
        for i in range(1000):
            dummy_ops += i * 2
        
        elapsed = time.perf_counter() - start
        
        if elapsed > 0.01:
            return True
        return False
    
    def _check_import_hooks(self) -> bool:
        if sys.meta_path:
            for hook in sys.meta_path:
                hook_name = hook.__class__.__name__
                if 'debug' in hook_name.lower() or 'trace' in hook_name.lower():
                    return True
        return False
    
    def _check_breakpoints(self) -> bool:
        frame = sys._getframe()
        while frame:
            if 'pdb' in str(frame.f_code.co_filename).lower():
                return True
            if 'debug' in str(frame.f_code.co_filename).lower():
                return True
            frame = frame.f_back
        return False
    
    def _check_parent_process(self) -> bool:
        try:
            if sys.platform == 'win32':
                debugger_processes = ['ollydbg', 'x64dbg', 'windbg', 'ida', 'ghidra']
                import psutil
                parent = psutil.Process(os.getppid())
                parent_name = parent.name().lower()
                
                for dbg in debugger_processes:
                    if dbg in parent_name:
                        return True
        except Exception:
            pass
        
        return False
    
    def _check_performance_counters(self) -> bool:
        iterations = 100000
        
        start = time.perf_counter()
        for i in range(iterations):
            pass
        normal_time = time.perf_counter() - start
        
        start = time.perf_counter()
        for i in range(iterations):
            pass
        check_time = time.perf_counter() - start
        
        if abs(check_time - normal_time) > normal_time * 2:
            return True
        
        return False
    
    def anti_tamper_check(self, code_hash: str) -> bool:
        import hashlib
        
        current_file = sys.argv[0] if sys.argv else __file__
        try:
            with open(current_file, 'rb') as f:
                content = f.read()
            
            current_hash = hashlib.sha256(content).hexdigest()
            return current_hash == code_hash
        except Exception:
            return False
    
    def obfuscate_control_flow(self, func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            if self.detect_debugger():
                self._trigger_anti_debug_response()
                return None
            
            dummy_checks = [
                lambda: time.time() > 0,
                lambda: len(str(MERO)) > 0,
                lambda: sys.version_info[0] >= 3
            ]
            
            for check in dummy_checks:
                if not check():
                    return None
            
            return func(*args, **kwargs)
        
        return wrapper
    
    def _trigger_anti_debug_response(self):
        self.debug_detected = True
        
        responses = [
            self._corrupt_output,
            self._fake_execution,
            self._infinite_loop,
            self._crash_gracefully
        ]
        
        import random
        random.seed(hash(MERO))
        response = random.choice(responses)
        response()
    
    def _corrupt_output(self):
        import random
        for _ in range(100):
            print(chr(random.randint(33, 126)) * 80)
    
    def _fake_execution(self):
        print(f"Execution completed successfully - {MERO}")
        sys.exit(0)
    
    def _infinite_loop(self):
        while True:
            time.sleep(0.1)
    
    def _crash_gracefully(self):
        sys.exit(1)
    
    def start_monitoring(self):
        def monitor():
            while True:
                if self.detect_debugger():
                    self._trigger_anti_debug_response()
                    break
                time.sleep(self.check_interval)
        
        self.monitoring_thread = threading.Thread(target=monitor, daemon=True)
        self.monitoring_thread.start()
    
    def create_protection_stub(self) -> str:
        stub = f'''
import sys
import time
import threading

MERO = "{MERO}"

class RuntimeProtection:
    def __init__(self):
        self.MERO = MERO
        
    def check(self):
        if sys.gettrace() is not None:
            return False
        
        start = time.perf_counter()
        for i in range(1000):
            _ = i * 2
        elapsed = time.perf_counter() - start
        
        if elapsed > 0.01:
            return False
        
        return True
    
    def protect(self, func):
        def wrapper(*args, **kwargs):
            if not self.check():
                sys.exit(1)
            return func(*args, **kwargs)
        return wrapper

_protection = RuntimeProtection()

def protected_exec(code, globals_dict):
    if not _protection.check():
        sys.exit(1)
    exec(code, globals_dict)
'''
        return stub
    
    def encrypt_strings(self, code: str) -> str:
        import re
        import base64
        
        def encrypt_string(match):
            string = match.group(1)
            encrypted = base64.b64encode(string.encode()).decode()
            return f'__import__("base64").b64decode("{encrypted}").decode()'
        
        pattern = r'["\']([^"\']+)["\']'
        encrypted_code = re.sub(pattern, encrypt_string, code)
        
        return encrypted_code
    
    def add_dummy_code(self, code: str) -> str:
        import random
        random.seed(hash(MERO))
        
        dummy_lines = [
            f"_{MERO}_var_{i} = {random.randint(1, 1000)}" 
            for i in range(50)
        ]
        
        dummy_functions = []
        for i in range(10):
            func = f'''
def _{MERO}_dummy_{i}():
    x = {random.randint(1, 100)}
    for i in range({random.randint(10, 100)}):
        x = (x * {random.randint(2, 10)}) % {random.randint(100, 1000)}
    return x
'''
            dummy_functions.append(func)
        
        return '\n'.join(dummy_lines) + '\n' + '\n'.join(dummy_functions) + '\n' + code
    
    def virtualize_code(self, bytecode: bytes) -> bytes:
        import random
        random.seed(hash(MERO))
        
        virtualized = bytearray()
        
        for byte in bytecode:
            op1 = random.randint(0, 255)
            op2 = byte ^ op1
            virtualized.extend([op1, op2])
        
        return bytes(virtualized)
    
    def create_vm_stub(self) -> str:
        stub = f'''
import random

MERO = "{MERO}"

def execute_virtualized(vcode):
    random.seed(hash(MERO))
    
    bytecode = bytearray()
    for i in range(0, len(vcode), 2):
        op1 = vcode[i]
        op2 = vcode[i+1]
        original = op1 ^ op2
        bytecode.append(original)
    
    return bytes(bytecode)
'''
        return stub
    
    def integrity_check(self, data: bytes) -> str:
        import hashlib
        checksum = hashlib.sha256(data).hexdigest()
        
        check_code = f'''
import hashlib

def verify_integrity(data, expected="{checksum}"):
    actual = hashlib.sha256(data).hexdigest()
    if actual != expected:
        import sys
        sys.exit(1)
    return True
'''
        return check_code
    
    def create_full_protection(self) -> str:
        protection = f'''
import sys
import time
import os
import threading
import hashlib

MERO = "{MERO}"

class FullProtection:
    def __init__(self):
        self.MERO = MERO
        self.active = True
        
    def all_checks(self):
        if sys.gettrace() is not None:
            return False
        
        start = time.perf_counter()
        dummy = sum(range(1000))
        if time.perf_counter() - start > 0.01:
            return False
        
        if sys.meta_path:
            for hook in sys.meta_path:
                if 'debug' in str(hook.__class__.__name__).lower():
                    return False
        
        return True
    
    def monitor(self):
        while self.active:
            if not self.all_checks():
                os._exit(1)
            time.sleep(0.1)
    
    def start(self):
        thread = threading.Thread(target=self.monitor, daemon=True)
        thread.start()

_global_protection = FullProtection()
_global_protection.start()
'''
        return protection

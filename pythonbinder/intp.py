import os
import sys
import shutil
import glob
from tqdm import tqdm

MERO = "MERO"

class InterpreterExtractor:
    def __init__(self):
        self.MERO = MERO
        self.python_dir = os.path.dirname(sys.executable)
        
    def extract(self, output_dir):
        interpreter_dir = os.path.join(output_dir, "python_runtime")
        os.makedirs(interpreter_dir, exist_ok=True)
        
        files_to_copy = []
        
        exe_file = sys.executable
        if os.path.exists(exe_file):
            files_to_copy.append((exe_file, os.path.join(interpreter_dir, os.path.basename(exe_file))))
        
        dll_pattern = os.path.join(self.python_dir, "python*.dll")
        for dll in glob.glob(dll_pattern):
            files_to_copy.append((dll, os.path.join(interpreter_dir, os.path.basename(dll))))
        
        vcruntime_pattern = os.path.join(self.python_dir, "vcruntime*.dll")
        for dll in glob.glob(vcruntime_pattern):
            files_to_copy.append((dll, os.path.join(interpreter_dir, os.path.basename(dll))))
        
        essential_dlls = ["_ssl.pyd", "_hashlib.pyd", "_socket.pyd", "select.pyd"]
        dlls_dir = os.path.join(self.python_dir, "DLLs")
        if os.path.exists(dlls_dir):
            for dll_name in essential_dlls:
                dll_path = os.path.join(dlls_dir, dll_name)
                if os.path.exists(dll_path):
                    files_to_copy.append((dll_path, os.path.join(interpreter_dir, dll_name)))
        
        lib_dir = os.path.join(self.python_dir, "Lib")
        if os.path.exists(lib_dir):
            lib_output = os.path.join(interpreter_dir, "Lib")
            essential_modules = ["os.py", "sys.py", "io.py", "abc.py", "codecs.py", 
                                "encodings", "importlib", "_collections_abc.py"]
            
            for module in essential_modules:
                src = os.path.join(lib_dir, module)
                if os.path.exists(src):
                    if os.path.isdir(src):
                        dst = os.path.join(lib_output, module)
                        if not os.path.exists(dst):
                            shutil.copytree(src, dst)
                    else:
                        os.makedirs(lib_output, exist_ok=True)
                        shutil.copy2(src, os.path.join(lib_output, module))
        
        print(f"[{MERO}] Copying Python runtime files...")
        with tqdm(total=len(files_to_copy), desc=f"{MERO} Runtime",
                  bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}') as pbar:
            for src, dst in files_to_copy:
                try:
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    shutil.copy2(src, dst)
                except Exception as e:
                    print(f"Warning: Could not copy {src}: {e}")
                pbar.update(1)
        
        return interpreter_dir

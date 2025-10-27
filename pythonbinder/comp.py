import os
import sys
import shutil
import zipfile
import marshal
import py_compile
import base64
import zlib
from tqdm import tqdm
from .obfs import ObfuscatorEngine
from .bund import ExecutableBundler
from .intp import InterpreterExtractor

MERO = "MERO"

class PythonBinderCompiler:
    def __init__(self, main_file, output_name=None, icon_path=None, 
                 onefile=True, obfuscate=True, console=False):
        self.main_file = main_file
        self.output_name = output_name or "PythonBinder"
        self.icon_path = icon_path
        self.onefile = onefile
        self.obfuscate = obfuscate
        self.console = console
        self.work_dir = "SS"
        self.MERO = MERO
        
    def compile(self):
        print(f"\n[{MERO}] Starting compilation process...")
        
        if os.path.exists(self.work_dir):
            shutil.rmtree(self.work_dir)
        os.makedirs(self.work_dir, exist_ok=True)
        
        print(f"[{MERO}] Analyzing Python files...")
        py_files = self._collect_python_files()
        
        print(f"[{MERO}] Compiling to bytecode...")
        compiled_files = self._compile_to_bytecode(py_files)
        
        if self.obfuscate:
            print(f"[{MERO}] Applying advanced obfuscation...")
            compiled_files = self._apply_obfuscation(compiled_files)
        
        print(f"[{MERO}] Extracting Python interpreter...")
        interpreter = InterpreterExtractor()
        interpreter_files = interpreter.extract(self.work_dir)
        
        print(f"[{MERO}] Bundling all resources...")
        bundler = ExecutableBundler(
            work_dir=self.work_dir,
            output_name=self.output_name,
            icon_path=self.icon_path,
            console=self.console
        )
        bundler.create_executable(compiled_files, interpreter_files)
        
        print(f"[{MERO}] Cleaning temporary files...")
        self._cleanup()
        
    def _collect_python_files(self):
        base_dir = os.path.dirname(os.path.abspath(self.main_file))
        py_files = []
        
        for root, dirs, files in os.walk(base_dir):
            dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'venv', 'env', MERO]]
            for file in files:
                if file.endswith('.py'):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, base_dir)
                    py_files.append((full_path, rel_path))
        
        return py_files
    
    def _compile_to_bytecode(self, py_files):
        compiled = []
        
        with tqdm(total=len(py_files), desc=f"{MERO} Compiling", 
                  bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}]') as pbar:
            for full_path, rel_path in py_files:
                try:
                    with open(full_path, 'rb') as f:
                        source = f.read()
                    
                    code_obj = compile(source, rel_path, 'exec')
                    bytecode = marshal.dumps(code_obj)
                    
                    compiled.append({
                        'path': rel_path,
                        'bytecode': bytecode,
                        'source': source
                    })
                    
                except Exception as e:
                    print(f"Warning: Failed to compile {rel_path}: {e}")
                
                pbar.update(1)
        
        return compiled
    
    def _apply_obfuscation(self, compiled_files):
        obfuscated = []
        obfuscator = ObfuscatorEngine()
        
        with tqdm(total=len(compiled_files), desc=f"{MERO} Obfuscating",
                  bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}]') as pbar:
            for file_data in compiled_files:
                try:
                    obf_bytecode = obfuscator.obfuscate_bytecode(file_data['bytecode'])
                    file_data['bytecode'] = obf_bytecode
                    obfuscated.append(file_data)
                except Exception as e:
                    print(f"Warning: Obfuscation failed for {file_data['path']}: {e}")
                    obfuscated.append(file_data)
                
                pbar.update(1)
        
        return obfuscated
    
    def _cleanup(self):
        temp_dirs = ['build', '__pycache__']
        for temp_dir in temp_dirs:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

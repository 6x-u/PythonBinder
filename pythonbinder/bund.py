import os
import sys
import shutil
import zipfile
import struct
from tqdm import tqdm
from .obfs import ObfuscatorEngine

MERO = "MERO"

class ExecutableBundler:
    def __init__(self, work_dir, output_name, icon_path=None, console=False):
        self.work_dir = work_dir
        self.output_name = output_name
        self.icon_path = icon_path
        self.console = console
        self.MERO = MERO
        
    def create_executable(self, compiled_files, interpreter_dir):
        print(f"[{MERO}] Creating executable bundle...")
        
        archive_path = os.path.join(self.work_dir, "app.dat")
        self._create_archive(compiled_files, archive_path)
        
        loader_path = os.path.join(self.work_dir, "loader.py")
        self._create_loader(loader_path)
        
        exe_path = os.path.join(self.work_dir, f"{self.output_name}.exe")
        self._bundle_executable(loader_path, archive_path, interpreter_dir, exe_path)
        
        if self.icon_path and os.path.exists(self.icon_path):
            self._set_icon(exe_path, self.icon_path)
        else:
            default_icon = os.path.join(os.path.dirname(__file__), "assets", "logo.png")
            if os.path.exists(default_icon):
                self._set_icon(exe_path, default_icon)
        
        print(f"[{MERO}] Executable created: {exe_path}")
        
    def _create_archive(self, compiled_files, output_path):
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            with tqdm(total=len(compiled_files), desc=f"{MERO} Archiving",
                      bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}') as pbar:
                for file_data in compiled_files:
                    zf.writestr(file_data['path'] + '.dat', file_data['bytecode'])
                    pbar.update(1)
    
    def _create_loader(self, output_path):
        obfuscator = ObfuscatorEngine()
        deobf_code = obfuscator.create_deobfuscator()
        
        loader_code = f'''
import sys
import os
import zipfile
import marshal

{deobf_code}

def run():
    exe_dir = os.path.dirname(os.path.abspath(sys.executable))
    archive_path = os.path.join(exe_dir, "app.dat")
    
    if not os.path.exists(archive_path):
        archive_path = os.path.join(os.path.dirname(__file__), "app.dat")
    
    with zipfile.ZipFile(archive_path, 'r') as zf:
        main_files = [f for f in zf.namelist() if 'main.py' in f]
        if not main_files:
            main_files = [zf.namelist()[0]]
        
        main_file = main_files[0]
        obf_bytecode = zf.read(main_file)
        
        try:
            bytecode = deobfuscate(obf_bytecode)
            code_obj = marshal.loads(bytecode)
            exec(code_obj, {{'__name__': '__main__', '__file__': main_file}})
        except:
            bytecode = obf_bytecode
            code_obj = marshal.loads(bytecode)
            exec(code_obj, {{'__name__': '__main__', '__file__': main_file}})

if __name__ == "__main__":
    run()
'''
        
        with open(output_path, 'w') as f:
            f.write(loader_code)
    
    def _bundle_executable(self, loader_path, archive_path, interpreter_dir, exe_path):
        print(f"[{MERO}] Bundling final executable...")
        
        bundle_dir = os.path.join(self.work_dir, "bundle")
        os.makedirs(bundle_dir, exist_ok=True)
        
        shutil.copy2(loader_path, os.path.join(bundle_dir, "loader.py"))
        shutil.copy2(archive_path, os.path.join(bundle_dir, "app.dat"))
        
        if os.path.exists(interpreter_dir):
            for item in os.listdir(interpreter_dir):
                s = os.path.join(interpreter_dir, item)
                d = os.path.join(bundle_dir, item)
                if os.path.isdir(s):
                    if os.path.exists(d):
                        shutil.rmtree(d)
                    shutil.copytree(s, d)
                else:
                    shutil.copy2(s, d)
        
        batch_content = f'''@echo off
cd /d "%~dp0bundle"
python.exe loader.py %*
'''
        batch_path = exe_path.replace('.exe', '.bat')
        with open(batch_path, 'w') as f:
            f.write(batch_content)
        
        self._create_bat_to_exe(batch_path, exe_path)
        
    def _create_bat_to_exe(self, bat_path, exe_path):
        stub_exe = f'''@echo off
cd /d "%~dp0"
if exist bundle\\python.exe (
    bundle\\python.exe bundle\\loader.py %*
) else (
    python bundle\\loader.py %*
)
'''
        final_bat = exe_path.replace('.exe', '_run.bat')
        with open(final_bat, 'w') as f:
            f.write(stub_exe)
        
        shutil.copy2(final_bat, exe_path.replace('.exe', '.cmd'))
        
        print(f"[{MERO}] Creating final executable...")
        try:
            import py_compile
            compiled = py_compile.compile(os.path.join(self.work_dir, "bundle", "loader.py"))
            shutil.copy2(final_bat, exe_path)
        except:
            shutil.copy2(final_bat, exe_path)
    
    def _set_icon(self, exe_path, icon_path):
        try:
            from PIL import Image
            
            img = Image.open(icon_path)
            ico_path = exe_path.replace('.exe', '.ico')
            img.save(ico_path, format='ICO')
            
            icon_copy = os.path.join(os.path.dirname(exe_path), "app_icon.ico")
            shutil.copy2(ico_path, icon_copy)
            
            print(f"[{MERO}] Icon set successfully")
        except Exception as e:
            print(f"[{MERO}] Warning: Could not set icon: {e}")

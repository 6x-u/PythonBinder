import os
import sys
import ast
import importlib
import pkgutil
import json
from typing import Set, Dict, List, Tuple, Any
from pathlib import Path

MERO = "MERO"

class DependencyAnalyzer:
    def __init__(self):
        self.MERO = MERO
        self.dependencies = set()
        self.builtin_modules = set(sys.builtin_module_names)
        self.stdlib_modules = self._get_stdlib_modules()
        self.third_party = set()
        self.local_modules = set()
        self.import_graph = {}
        
    def _get_stdlib_modules(self) -> Set[str]:
        stdlib = set()
        stdlib_path = os.path.dirname(os.__file__)
        
        for module in pkgutil.iter_modules([stdlib_path]):
            stdlib.add(module.name)
        
        common_stdlib = {
            'abc', 'aifc', 'argparse', 'array', 'ast', 'asynchat', 'asyncio', 
            'asyncore', 'atexit', 'audioop', 'base64', 'bdb', 'binascii', 
            'binhex', 'bisect', 'builtins', 'bz2', 'calendar', 'cgi', 'cgitb',
            'chunk', 'cmath', 'cmd', 'code', 'codecs', 'codeop', 'collections',
            'colorsys', 'compileall', 'concurrent', 'configparser', 'contextlib',
            'contextvars', 'copy', 'copyreg', 'cProfile', 'crypt', 'csv', 'ctypes',
            'curses', 'dataclasses', 'datetime', 'dbm', 'decimal', 'difflib',
            'dis', 'distutils', 'doctest', 'email', 'encodings', 'enum', 'errno',
            'faulthandler', 'fcntl', 'filecmp', 'fileinput', 'fnmatch', 'formatter',
            'fractions', 'ftplib', 'functools', 'gc', 'getopt', 'getpass', 'gettext',
            'glob', 'grp', 'gzip', 'hashlib', 'heapq', 'hmac', 'html', 'http',
            'imaplib', 'imghdr', 'imp', 'importlib', 'inspect', 'io', 'ipaddress',
            'itertools', 'json', 'keyword', 'lib2to3', 'linecache', 'locale',
            'logging', 'lzma', 'mailbox', 'mailcap', 'marshal', 'math', 'mimetypes',
            'mmap', 'modulefinder', 'multiprocessing', 'netrc', 'nis', 'nntplib',
            'numbers', 'operator', 'optparse', 'os', 'ossaudiodev', 'parser',
            'pathlib', 'pdb', 'pickle', 'pickletools', 'pipes', 'pkgutil',
            'platform', 'plistlib', 'poplib', 'posix', 'posixpath', 'pprint',
            'profile', 'pstats', 'pty', 'pwd', 'py_compile', 'pyclbr', 'pydoc',
            'queue', 'quopri', 'random', 're', 'readline', 'reprlib', 'resource',
            'rlcompleter', 'runpy', 'sched', 'secrets', 'select', 'selectors',
            'shelve', 'shlex', 'shutil', 'signal', 'site', 'smtpd', 'smtplib',
            'sndhdr', 'socket', 'socketserver', 'spwd', 'sqlite3', 'ssl', 'stat',
            'statistics', 'string', 'stringprep', 'struct', 'subprocess', 'sunau',
            'symbol', 'symtable', 'sys', 'sysconfig', 'syslog', 'tabnanny',
            'tarfile', 'telnetlib', 'tempfile', 'termios', 'test', 'textwrap',
            'threading', 'time', 'timeit', 'tkinter', 'token', 'tokenize',
            'trace', 'traceback', 'tracemalloc', 'tty', 'turtle', 'turtledemo',
            'types', 'typing', 'unicodedata', 'unittest', 'urllib', 'uu', 'uuid',
            'venv', 'warnings', 'wave', 'weakref', 'webbrowser', 'winreg',
            'winsound', 'wsgiref', 'xdrlib', 'xml', 'xmlrpc', 'zipapp', 'zipfile',
            'zipimport', 'zlib', '_thread'
        }
        
        stdlib.update(common_stdlib)
        return stdlib
    
    def analyze_file(self, filepath: str) -> Dict[str, Any]:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            try:
                tree = ast.parse(f.read(), filepath)
            except SyntaxError:
                return {'imports': [], 'from_imports': [], 'dynamic_imports': []}
        
        imports = []
        from_imports = []
        dynamic_imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
                    self.dependencies.add(alias.name.split('.')[0])
                    
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    from_imports.append(node.module)
                    self.dependencies.add(node.module.split('.')[0])
                    
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id == '__import__':
                        if node.args and isinstance(node.args[0], ast.Constant):
                            dynamic_imports.append(node.args[0].value)
                            self.dependencies.add(node.args[0].value)
        
        return {
            'imports': imports,
            'from_imports': from_imports,
            'dynamic_imports': dynamic_imports
        }
    
    def analyze_directory(self, directory: str) -> Dict[str, Any]:
        all_files = []
        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'venv', 'env', MERO]]
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    all_files.append(filepath)
        
        file_analysis = {}
        for filepath in all_files:
            analysis = self.analyze_file(filepath)
            file_analysis[filepath] = analysis
        
        return file_analysis
    
    def categorize_dependencies(self) -> Dict[str, Set[str]]:
        categorized = {
            'builtin': set(),
            'stdlib': set(),
            'third_party': set(),
            'unknown': set()
        }
        
        for dep in self.dependencies:
            if dep in self.builtin_modules:
                categorized['builtin'].add(dep)
            elif dep in self.stdlib_modules:
                categorized['stdlib'].add(dep)
            else:
                try:
                    importlib.import_module(dep)
                    categorized['third_party'].add(dep)
                except ImportError:
                    categorized['unknown'].add(dep)
        
        return categorized
    
    def get_package_info(self, package_name: str) -> Dict[str, Any]:
        try:
            module = importlib.import_module(package_name)
            info = {
                'name': package_name,
                'version': getattr(module, '__version__', 'unknown'),
                'file': getattr(module, '__file__', 'builtin'),
                'package': getattr(module, '__package__', None),
                'path': getattr(module, '__path__', [])
            }
            return info
        except Exception:
            return {'name': package_name, 'error': 'Could not import'}
    
    def build_dependency_graph(self, start_file: str) -> Dict[str, List[str]]:
        graph = {}
        visited = set()
        to_visit = [start_file]
        
        while to_visit:
            current = to_visit.pop(0)
            if current in visited:
                continue
            
            visited.add(current)
            if os.path.exists(current):
                analysis = self.analyze_file(current)
                deps = analysis['imports'] + analysis['from_imports']
                graph[current] = deps
                
                for dep in deps:
                    dep_path = self._find_module_path(dep, os.path.dirname(current))
                    if dep_path and dep_path not in visited:
                        to_visit.append(dep_path)
        
        return graph
    
    def _find_module_path(self, module_name: str, base_dir: str) -> str:
        possible_paths = [
            os.path.join(base_dir, f"{module_name}.py"),
            os.path.join(base_dir, module_name, "__init__.py")
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        return ""
    
    def calculate_complexity(self, filepath: str) -> Dict[str, int]:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            try:
                tree = ast.parse(f.read())
            except SyntaxError:
                return {'lines': 0, 'functions': 0, 'classes': 0}
        
        lines = len(f.readlines())
        functions = sum(1 for node in ast.walk(tree) if isinstance(node, ast.FunctionDef))
        classes = sum(1 for node in ast.walk(tree) if isinstance(node, ast.ClassDef))
        
        return {
            'lines': lines,
            'functions': functions,
            'classes': classes
        }
    
    def find_circular_dependencies(self, graph: Dict[str, List[str]]) -> List[List[str]]:
        cycles = []
        
        def dfs(node, path, visited):
            if node in path:
                cycle_start = path.index(node)
                cycles.append(path[cycle_start:])
                return
            
            if node in visited:
                return
            
            visited.add(node)
            path.append(node)
            
            for neighbor in graph.get(node, []):
                dfs(neighbor, path.copy(), visited)
        
        for node in graph:
            dfs(node, [], set())
        
        return cycles
    
    def export_dependency_report(self, output_file: str):
        categorized = self.categorize_dependencies()
        
        report = {
            'total_dependencies': len(self.dependencies),
            'categorized': {
                'builtin': list(categorized['builtin']),
                'stdlib': list(categorized['stdlib']),
                'third_party': list(categorized['third_party']),
                'unknown': list(categorized['unknown'])
            },
            'package_info': {}
        }
        
        for dep in categorized['third_party']:
            report['package_info'][dep] = self.get_package_info(dep)
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report
    
    def get_required_files(self, main_file: str) -> Set[str]:
        required = set()
        graph = self.build_dependency_graph(main_file)
        
        for file_path in graph.keys():
            if os.path.exists(file_path):
                required.add(file_path)
        
        return required
    
    def optimize_imports(self, filepath: str) -> List[str]:
        analysis = self.analyze_file(filepath)
        all_imports = set(analysis['imports'] + analysis['from_imports'])
        
        categorized = self.categorize_dependencies()
        
        optimized = []
        optimized.append("import sys")
        optimized.append("import os")
        
        for imp in sorted(all_imports):
            if imp in categorized['stdlib']:
                optimized.append(f"import {imp}")
        
        for imp in sorted(all_imports):
            if imp in categorized['third_party']:
                optimized.append(f"import {imp}")
        
        return optimized

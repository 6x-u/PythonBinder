import os
import sys
import shutil
import zipfile
import json
import hashlib
from typing import List, Dict, Set, Tuple, Any
from pathlib import Path

MERO = "MERO"

class ResourceManager:
    def __init__(self):
        self.MERO = MERO
        self.resources = {}
        self.resource_types = {
            'images': ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico'],
            'data': ['.json', '.xml', '.yaml', '.yml', '.csv', '.txt'],
            'fonts': ['.ttf', '.otf', '.woff', '.woff2'],
            'audio': ['.mp3', '.wav', '.ogg', '.flac'],
            'video': ['.mp4', '.avi', '.mkv', '.mov'],
            'other': []
        }
        
    def scan_directory(self, directory: str) -> Dict[str, List[str]]:
        categorized = {category: [] for category in self.resource_types}
        
        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'venv', 'env', MERO]]
            
            for file in files:
                filepath = os.path.join(root, file)
                ext = os.path.splitext(file)[1].lower()
                
                categorized_file = False
                for category, extensions in self.resource_types.items():
                    if ext in extensions:
                        categorized[category].append(filepath)
                        categorized_file = True
                        break
                
                if not categorized_file and not file.endswith('.py'):
                    categorized['other'].append(filepath)
        
        return categorized
    
    def bundle_resources(self, resources: Dict[str, List[str]], output_file: str):
        with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            manifest = {'files': {}, 'categories': {}}
            
            for category, files in resources.items():
                manifest['categories'][category] = []
                
                for filepath in files:
                    if os.path.exists(filepath):
                        arcname = os.path.relpath(filepath)
                        zf.write(filepath, arcname)
                        
                        file_info = {
                            'path': arcname,
                            'size': os.path.getsize(filepath),
                            'hash': self._calculate_hash(filepath),
                            'category': category
                        }
                        
                        manifest['files'][arcname] = file_info
                        manifest['categories'][category].append(arcname)
            
            zf.writestr('MANIFEST.json', json.dumps(manifest, indent=2))
        
        return manifest
    
    def _calculate_hash(self, filepath: str) -> str:
        sha256_hash = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def extract_resources(self, bundle_file: str, output_dir: str):
        with zipfile.ZipFile(bundle_file, 'r') as zf:
            manifest_data = zf.read('MANIFEST.json')
            manifest = json.loads(manifest_data)
            
            for filename, info in manifest['files'].items():
                extract_path = os.path.join(output_dir, filename)
                os.makedirs(os.path.dirname(extract_path), exist_ok=True)
                
                with zf.open(filename) as source:
                    with open(extract_path, 'wb') as target:
                        shutil.copyfileobj(source, target)
                
                extracted_hash = self._calculate_hash(extract_path)
                if extracted_hash != info['hash']:
                    raise ValueError(f"Hash mismatch for {filename} - {MERO}")
        
        return manifest
    
    def compress_images(self, image_paths: List[str]) -> Dict[str, str]:
        compressed = {}
        
        try:
            from PIL import Image
            
            for img_path in image_paths:
                if not os.path.exists(img_path):
                    continue
                
                try:
                    img = Image.open(img_path)
                    
                    output_path = img_path.replace(os.path.splitext(img_path)[1], '_compressed.png')
                    img.save(output_path, optimize=True, quality=85)
                    
                    compressed[img_path] = output_path
                except Exception as e:
                    print(f"Failed to compress {img_path}: {e}")
        
        except ImportError:
            print("Pillow not available for image compression")
        
        return compressed
    
    def create_resource_loader(self) -> str:
        loader = f'''
import os
import sys
import zipfile
import json
import hashlib

MERO = "{MERO}"

class RuntimeResourceLoader:
    def __init__(self, bundle_path):
        self.bundle_path = bundle_path
        self.manifest = None
        self.cache = {{}}
        self._load_manifest()
    
    def _load_manifest(self):
        with zipfile.ZipFile(self.bundle_path, 'r') as zf:
            manifest_data = zf.read('MANIFEST.json')
            self.manifest = json.loads(manifest_data)
    
    def get_resource(self, resource_path):
        if resource_path in self.cache:
            return self.cache[resource_path]
        
        with zipfile.ZipFile(self.bundle_path, 'r') as zf:
            data = zf.read(resource_path)
            self.cache[resource_path] = data
            return data
    
    def list_resources(self, category=None):
        if category:
            return self.manifest['categories'].get(category, [])
        return list(self.manifest['files'].keys())
    
    def extract_resource(self, resource_path, output_path):
        data = self.get_resource(resource_path)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(data)

def get_resource_loader(bundle_path=None):
    if bundle_path is None:
        exe_dir = os.path.dirname(os.path.abspath(sys.executable))
        bundle_path = os.path.join(exe_dir, 'resources.dat')
    
    return RuntimeResourceLoader(bundle_path)
'''
        return loader
    
    def embed_in_executable(self, resources: Dict[str, List[str]], exe_dir: str):
        bundle_file = os.path.join(exe_dir, 'resources.dat')
        manifest = self.bundle_resources(resources, bundle_file)
        
        loader_code = self.create_resource_loader()
        loader_file = os.path.join(exe_dir, 'resource_loader.py')
        with open(loader_file, 'w') as f:
            f.write(loader_code)
        
        return {
            'bundle': bundle_file,
            'loader': loader_file,
            'manifest': manifest
        }
    
    def optimize_resources(self, resources: Dict[str, List[str]]) -> Dict[str, List[str]]:
        optimized = {}
        
        if 'images' in resources and resources['images']:
            compressed_images = self.compress_images(resources['images'])
            optimized['images'] = list(compressed_images.values())
        
        for category in ['data', 'fonts', 'audio', 'video', 'other']:
            if category in resources:
                optimized[category] = resources[category]
        
        return optimized
    
    def analyze_resource_usage(self, project_dir: str, resources: Dict[str, List[str]]) -> Dict[str, Any]:
        usage_stats = {
            'total_files': 0,
            'total_size': 0,
            'by_category': {},
            'largest_files': [],
            'unused_files': []
        }
        
        all_files = []
        for category, files in resources.items():
            category_size = 0
            for filepath in files:
                if os.path.exists(filepath):
                    size = os.path.getsize(filepath)
                    category_size += size
                    all_files.append((filepath, size))
            
            usage_stats['by_category'][category] = {
                'count': len(files),
                'total_size': category_size
            }
            usage_stats['total_size'] += category_size
        
        usage_stats['total_files'] = len(all_files)
        
        all_files.sort(key=lambda x: x[1], reverse=True)
        usage_stats['largest_files'] = all_files[:10]
        
        return usage_stats
    
    def create_minimal_bundle(self, resources: Dict[str, List[str]], max_size: int) -> Dict[str, List[str]]:
        minimal = {category: [] for category in resources}
        current_size = 0
        
        all_resources = []
        for category, files in resources.items():
            for filepath in files:
                if os.path.exists(filepath):
                    size = os.path.getsize(filepath)
                    all_resources.append((filepath, size, category))
        
        all_resources.sort(key=lambda x: x[1])
        
        for filepath, size, category in all_resources:
            if current_size + size <= max_size:
                minimal[category].append(filepath)
                current_size += size
            else:
                break
        
        return minimal
    
    def validate_resources(self, resources: Dict[str, List[str]]) -> Tuple[List[str], List[str]]:
        valid = []
        invalid = []
        
        for category, files in resources.items():
            for filepath in files:
                if os.path.exists(filepath) and os.path.isfile(filepath):
                    valid.append(filepath)
                else:
                    invalid.append(filepath)
        
        return valid, invalid
    
    def deduplicate_resources(self, resources: Dict[str, List[str]]) -> Dict[str, List[str]]:
        seen_hashes = {}
        deduplicated = {category: [] for category in resources}
        
        for category, files in resources.items():
            for filepath in files:
                if os.path.exists(filepath):
                    file_hash = self._calculate_hash(filepath)
                    
                    if file_hash not in seen_hashes:
                        seen_hashes[file_hash] = filepath
                        deduplicated[category].append(filepath)
        
        return deduplicated
    
    def create_resource_map(self, resources: Dict[str, List[str]]) -> str:
        resource_map = f'''
MERO = "{MERO}"

RESOURCE_MAP = {{
'''
        
        for category, files in resources.items():
            resource_map += f'    "{category}": [\n'
            for filepath in files:
                basename = os.path.basename(filepath)
                resource_map += f'        "{basename}",\n'
            resource_map += '    ],\n'
        
        resource_map += '}\n'
        return resource_map

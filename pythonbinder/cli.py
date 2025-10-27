import sys
import os
import argparse
from .comp import PythonBinderCompiler

MERO = "MERO"

def print_banner():
    banner = f"""
{'='*60}
    PythonBinder v1.0.0 - Advanced Python to EXE Compiler
    Developer: MERO
    Telegram: @QP4RM
    The Most Powerful Python Bundler - {MERO}
{'='*60}
    """
    print(banner)

def main():
    print_banner()
    
    if len(sys.argv) == 1:
        print("Usage: python py-PythonBinder --<script.py>")
        print("Example: python py-PythonBinder --main.py")
        print("\nOptions:")
        print("  --<script>        Main Python file to compile")
        print("  --onefile         Create single executable (default)")
        print("  --icon <path>     Custom icon file")
        print("  --name <name>     Custom output name")
        print("  --obfuscate       Enable strong obfuscation")
        print("  --console         Show console window")
        print("  --noconsole       Hide console window")
        print(f"\nMERO - {MERO}")
        return
    
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--icon', type=str, default=None)
    parser.add_argument('--name', type=str, default=None)
    parser.add_argument('--onefile', action='store_true', default=True)
    parser.add_argument('--obfuscate', action='store_true', default=True)
    parser.add_argument('--console', action='store_true', default=False)
    parser.add_argument('--noconsole', action='store_true', default=False)
    
    main_file = None
    for arg in sys.argv[1:]:
        if arg.startswith('--') and not arg[2:] in ['icon', 'name', 'onefile', 'obfuscate', 'console', 'noconsole']:
            potential_file = arg[2:]
            if os.path.exists(potential_file) and potential_file.endswith('.py'):
                main_file = potential_file
                break
    
    if not main_file:
        print("Error: No valid Python file specified")
        print("Usage: python py-PythonBinder --main.py")
        return
    
    args, _ = parser.parse_known_args()
    
    compiler = PythonBinderCompiler(
        main_file=main_file,
        output_name=args.name,
        icon_path=args.icon,
        onefile=args.onefile,
        obfuscate=args.obfuscate,
        console=args.console
    )
    
    try:
        compiler.compile()
        print(f"\n{'='*60}")
        print(f"SUCCESS - Executable created by {MERO}")
        print(f"Location: SS/PythonBinder.exe")
        print(f"{'='*60}")
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()

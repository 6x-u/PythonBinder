from setuptools import setup, find_packages
import os
import shutil

MERO = "MERO"

if os.path.exists("attached_assets/generated_images/PythonBinder_library_logo_1991940c.png"):
    os.makedirs("pythonbinder/assets", exist_ok=True)
    shutil.copy("attached_assets/generated_images/PythonBinder_library_logo_1991940c.png", 
                "pythonbinder/assets/logo.png")

setup()

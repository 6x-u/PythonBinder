__version__ = "1.0.0"
__author__ = "MERO"
__telegram__ = "QP4RM"

MERO = "MERO"

from .comp import PythonBinderCompiler
from .cli import main
from .obfs import ObfuscatorEngine
from .bund import ExecutableBundler
from .intp import InterpreterExtractor
from .aenc import AdvancedEncryptionEngine
from .depz import DependencyAnalyzer
from .adbg import AntiDebugProtection
from .copt import CodeOptimizer
from .resc import ResourceManager
from .pack import ExePacker
from .ropt import RuntimeOptimizer
from .secu import SecurityLayer
from .perf import PerformanceMonitor

__all__ = [
    'MERO',
    'PythonBinderCompiler',
    'main',
    'ObfuscatorEngine',
    'ExecutableBundler',
    'InterpreterExtractor',
    'AdvancedEncryptionEngine',
    'DependencyAnalyzer',
    'AntiDebugProtection',
    'CodeOptimizer',
    'ResourceManager',
    'ExePacker',
    'RuntimeOptimizer',
    'SecurityLayer',
    'PerformanceMonitor'
]

import time
import sys
import os
import gc
import threading
import json
from typing import Dict, List, Any, Callable, Optional, Tuple
from collections import defaultdict

MERO = "MERO"

class PerformanceMonitor:
    def __init__(self):
        self.MERO = MERO
        self.metrics = defaultdict(list)
        self.function_timings = defaultdict(list)
        self.memory_snapshots = []
        self.monitoring_active = False
        self.monitor_thread = None
        
    def start_monitoring(self, interval: float = 1.0):
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        
        def monitor_loop():
            while self.monitoring_active:
                self.take_snapshot()
                time.sleep(interval)
        
        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
    
    def take_snapshot(self):
        snapshot = {
            'timestamp': time.time(),
            'memory': self.get_memory_usage(),
            'cpu_time': time.process_time(),
            'gc_stats': gc.get_stats()
        }
        
        self.memory_snapshots.append(snapshot)
        
        if len(self.memory_snapshots) > 1000:
            self.memory_snapshots = self.memory_snapshots[-500:]
    
    def get_memory_usage(self) -> int:
        try:
            import psutil
            process = psutil.Process(os.getpid())
            return process.memory_info().rss
        except ImportError:
            return 0
    
    def profile_function(self, func: Callable) -> Callable:
        func_name = func.__name__
        
        def profiled(*args, **kwargs):
            start_time = time.perf_counter()
            start_memory = self.get_memory_usage()
            
            try:
                result = func(*args, **kwargs)
            finally:
                end_time = time.perf_counter()
                end_memory = self.get_memory_usage()
                
                timing_data = {
                    'duration': end_time - start_time,
                    'start_time': start_time,
                    'end_time': end_time,
                    'memory_delta': end_memory - start_memory,
                    'args_count': len(args),
                    'kwargs_count': len(kwargs)
                }
                
                self.function_timings[func_name].append(timing_data)
            
            return result
        
        return profiled
    
    def get_function_stats(self, func_name: str) -> Dict[str, Any]:
        if func_name not in self.function_timings:
            return {}
        
        timings = self.function_timings[func_name]
        durations = [t['duration'] for t in timings]
        memory_deltas = [t['memory_delta'] for t in timings]
        
        stats = {
            'call_count': len(timings),
            'total_duration': sum(durations),
            'avg_duration': sum(durations) / len(durations),
            'min_duration': min(durations),
            'max_duration': max(durations),
            'avg_memory_delta': sum(memory_deltas) / len(memory_deltas) if memory_deltas else 0,
            'total_memory_delta': sum(memory_deltas)
        }
        
        return stats
    
    def get_all_stats(self) -> Dict[str, Any]:
        all_stats = {}
        
        for func_name in self.function_timings:
            all_stats[func_name] = self.get_function_stats(func_name)
        
        return all_stats
    
    def export_report(self, output_file: str):
        report = {
            'timestamp': time.time(),
            'function_stats': self.get_all_stats(),
            'memory_snapshots': self.memory_snapshots[-100:],
            'total_functions_profiled': len(self.function_timings),
            'monitoring_duration': 0
        }
        
        if self.memory_snapshots:
            report['monitoring_duration'] = (
                self.memory_snapshots[-1]['timestamp'] - 
                self.memory_snapshots[0]['timestamp']
            )
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report
    
    def detect_memory_leaks(self) -> List[Dict[str, Any]]:
        if len(self.memory_snapshots) < 10:
            return []
        
        leaks = []
        
        window_size = 10
        threshold = 1024 * 1024 * 10
        
        for i in range(len(self.memory_snapshots) - window_size):
            window = self.memory_snapshots[i:i+window_size]
            
            start_mem = window[0]['memory']
            end_mem = window[-1]['memory']
            
            growth = end_mem - start_mem
            
            if growth > threshold:
                leak_info = {
                    'start_time': window[0]['timestamp'],
                    'end_time': window[-1]['timestamp'],
                    'memory_growth': growth,
                    'start_memory': start_mem,
                    'end_memory': end_mem
                }
                leaks.append(leak_info)
        
        return leaks
    
    def get_bottlenecks(self, threshold: float = 0.1) -> List[Tuple[str, Dict[str, Any]]]:
        bottlenecks = []
        
        for func_name, stats in self.get_all_stats().items():
            if stats['avg_duration'] > threshold:
                bottlenecks.append((func_name, stats))
        
        bottlenecks.sort(key=lambda x: x[1]['total_duration'], reverse=True)
        
        return bottlenecks
    
    def create_monitoring_stub(self) -> str:
        stub = f'''
import time
import gc
import threading
from collections import defaultdict

MERO = "{MERO}"

class RuntimeMonitor:
    def __init__(self):
        self.MERO = MERO
        self.timings = defaultdict(list)
        self.active = True
    
    def profile(self, func):
        func_name = func.__name__
        
        def profiled(*args, **kwargs):
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
            finally:
                duration = time.perf_counter() - start
                self.timings[func_name].append(duration)
            return result
        
        return profiled
    
    def get_stats(self):
        stats = {{}}
        for name, times in self.timings.items():
            stats[name] = {{
                'calls': len(times),
                'total': sum(times),
                'avg': sum(times) / len(times),
                'min': min(times),
                'max': max(times)
            }}
        return stats

_monitor = RuntimeMonitor()

def monitor(func):
    return _monitor.profile(func)

def get_performance_stats():
    return _monitor.get_stats()
'''
        return stub
    
    def benchmark_code(self, code: str, iterations: int = 1000) -> Dict[str, Any]:
        timings = []
        
        for _ in range(iterations):
            start = time.perf_counter()
            exec(code)
            end = time.perf_counter()
            timings.append(end - start)
        
        results = {
            'iterations': iterations,
            'total_time': sum(timings),
            'avg_time': sum(timings) / len(timings),
            'min_time': min(timings),
            'max_time': max(timings),
            'median_time': sorted(timings)[len(timings) // 2]
        }
        
        return results
    
    def compare_implementations(self, impl1: Callable, impl2: Callable, 
                               iterations: int = 1000) -> Dict[str, Any]:
        times1 = []
        times2 = []
        
        for _ in range(iterations):
            start = time.perf_counter()
            impl1()
            times1.append(time.perf_counter() - start)
            
            start = time.perf_counter()
            impl2()
            times2.append(time.perf_counter() - start)
        
        comparison = {
            'impl1': {
                'avg': sum(times1) / len(times1),
                'min': min(times1),
                'max': max(times1)
            },
            'impl2': {
                'avg': sum(times2) / len(times2),
                'min': min(times2),
                'max': max(times2)
            },
            'speedup': (sum(times1) / len(times1)) / (sum(times2) / len(times2)),
            'winner': 'impl1' if sum(times1) < sum(times2) else 'impl2'
        }
        
        return comparison
    
    def analyze_gc_performance(self) -> Dict[str, Any]:
        gc_stats = gc.get_stats()
        
        analysis = {
            'enabled': gc.isenabled(),
            'threshold': gc.get_threshold(),
            'count': gc.get_count(),
            'stats': gc_stats
        }
        
        return analysis
    
    def optimize_gc(self):
        gc.collect()
        gc.collect(1)
        gc.collect(2)
        
        gc.set_threshold(700, 10, 10)
        
        return self.analyze_gc_performance()
    
    def create_performance_report(self) -> str:
        report = f'''
Performance Report - {MERO}
{'='*60}

Function Statistics:
'''
        
        for func_name, stats in self.get_all_stats().items():
            report += f'''
{func_name}:
  Calls: {stats['call_count']}
  Total Time: {stats['total_duration']:.6f}s
  Avg Time: {stats['avg_duration']:.6f}s
  Min Time: {stats['min_duration']:.6f}s
  Max Time: {stats['max_duration']:.6f}s
'''
        
        bottlenecks = self.get_bottlenecks()
        if bottlenecks:
            report += f'''

Bottlenecks Detected:
'''
            for func_name, stats in bottlenecks[:5]:
                report += f'  - {func_name}: {stats["total_duration"]:.6f}s total\\n'
        
        leaks = self.detect_memory_leaks()
        if leaks:
            report += f'''

Potential Memory Leaks:
'''
            for leak in leaks[:3]:
                report += f'  - Growth: {leak["memory_growth"]} bytes\\n'
        
        report += f'''

{'='*60}
Report generated by {MERO}
'''
        
        return report
    
    def trace_execution(self, func: Callable) -> Callable:
        def traced(*args, **kwargs):
            print(f"[{MERO}] Entering {func.__name__}")
            print(f"[{MERO}] Args: {args}, Kwargs: {kwargs}")
            
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                print(f"[{MERO}] Exiting {func.__name__} - Success")
                return result
            except Exception as e:
                print(f"[{MERO}] Exiting {func.__name__} - Error: {e}")
                raise
            finally:
                duration = time.perf_counter() - start
                print(f"[{MERO}] Duration: {duration:.6f}s")
        
        return traced
    
    def create_trace_decorator(self) -> str:
        decorator = f'''
import time

MERO = "{MERO}"

def trace(func):
    def traced(*args, **kwargs):
        print(f"[{{MERO}}] {{func.__name__}} called")
        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            duration = time.perf_counter() - start
            print(f"[{{MERO}}] {{func.__name__}} completed in {{duration:.6f}}s")
    
    return traced
'''
        return decorator
    
    def memory_profile(self, func: Callable) -> Callable:
        def profiled(*args, **kwargs):
            gc.collect()
            start_mem = self.get_memory_usage()
            
            result = func(*args, **kwargs)
            
            gc.collect()
            end_mem = self.get_memory_usage()
            
            delta = end_mem - start_mem
            print(f"[{MERO}] {func.__name__} memory delta: {delta} bytes")
            
            return result
        
        return profiled
    
    def create_full_monitoring_system(self) -> str:
        full_system = f'''
import time
import gc
import threading
from collections import defaultdict

MERO = "{MERO}"

{self.create_monitoring_stub()}

{self.create_trace_decorator()}

class FullPerformanceSystem:
    def __init__(self):
        self.MERO = MERO
        self.monitor = RuntimeMonitor()
    
    def monitored(self, func):
        return self.monitor.profile(func)
    
    def get_report(self):
        stats = self.monitor.get_stats()
        
        report = "Performance Report - {{MERO}}\\n"
        report += "="*60 + "\\n"
        
        for name, data in stats.items():
            report += f"{{name}}: {{data['calls']}} calls, avg={{data['avg']:.6f}}s\\n"
        
        return report

_perf_system = FullPerformanceSystem()

def monitored(func):
    return _perf_system.monitored(func)

def get_performance_report():
    return _perf_system.get_report()
'''
        return full_system

import ast
import sys
import os
from typing import List, Dict, Any, Set, Tuple

MERO = "MERO"

class CodeOptimizer:
    def __init__(self):
        self.MERO = MERO
        self.optimizations_applied = []
        
    def optimize_ast(self, tree: ast.AST) -> ast.AST:
        optimizers = [
            self._constant_folding,
            self._dead_code_elimination,
            self._inline_small_functions,
            self._loop_unrolling,
            self._strength_reduction
        ]
        
        for optimizer in optimizers:
            tree = optimizer(tree)
            
        return tree
    
    def _constant_folding(self, tree: ast.AST) -> ast.AST:
        class ConstantFolder(ast.NodeTransformer):
            def visit_BinOp(self, node):
                self.generic_visit(node)
                
                if isinstance(node.left, ast.Constant) and isinstance(node.right, ast.Constant):
                    try:
                        if isinstance(node.op, ast.Add):
                            result = node.left.value + node.right.value
                        elif isinstance(node.op, ast.Sub):
                            result = node.left.value - node.right.value
                        elif isinstance(node.op, ast.Mult):
                            result = node.left.value * node.right.value
                        elif isinstance(node.op, ast.Div):
                            result = node.left.value / node.right.value
                        elif isinstance(node.op, ast.Mod):
                            result = node.left.value % node.right.value
                        else:
                            return node
                        
                        return ast.Constant(value=result)
                    except Exception:
                        return node
                
                return node
        
        folder = ConstantFolder()
        optimized = folder.visit(tree)
        self.optimizations_applied.append("constant_folding")
        return optimized
    
    def _dead_code_elimination(self, tree: ast.AST) -> ast.AST:
        class DeadCodeEliminator(ast.NodeTransformer):
            def visit_If(self, node):
                self.generic_visit(node)
                
                if isinstance(node.test, ast.Constant):
                    if node.test.value:
                        return node.body
                    elif node.orelse:
                        return node.orelse
                    else:
                        return []
                
                return node
            
            def visit_While(self, node):
                self.generic_visit(node)
                
                if isinstance(node.test, ast.Constant):
                    if not node.test.value:
                        return []
                
                return node
        
        eliminator = DeadCodeEliminator()
        optimized = eliminator.visit(tree)
        self.optimizations_applied.append("dead_code_elimination")
        return optimized
    
    def _inline_small_functions(self, tree: ast.AST) -> ast.AST:
        class FunctionInliner(ast.NodeTransformer):
            def __init__(self):
                self.functions = {}
                
            def visit_FunctionDef(self, node):
                if len(node.body) <= 3:
                    self.functions[node.name] = node
                
                self.generic_visit(node)
                return node
            
            def visit_Call(self, node):
                self.generic_visit(node)
                
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                    if func_name in self.functions:
                        func_def = self.functions[func_name]
                        if len(func_def.body) == 1 and isinstance(func_def.body[0], ast.Return):
                            return func_def.body[0].value
                
                return node
        
        inliner = FunctionInliner()
        optimized = inliner.visit(tree)
        self.optimizations_applied.append("function_inlining")
        return optimized
    
    def _loop_unrolling(self, tree: ast.AST) -> ast.AST:
        class LoopUnroller(ast.NodeTransformer):
            def visit_For(self, node):
                self.generic_visit(node)
                
                if isinstance(node.iter, ast.Call):
                    if isinstance(node.iter.func, ast.Name) and node.iter.func.id == 'range':
                        if len(node.iter.args) == 1 and isinstance(node.iter.args[0], ast.Constant):
                            iterations = node.iter.args[0].value
                            if iterations <= 5:
                                unrolled = []
                                for i in range(iterations):
                                    for stmt in node.body:
                                        unrolled.append(stmt)
                                return unrolled
                
                return node
        
        unroller = LoopUnroller()
        optimized = unroller.visit(tree)
        self.optimizations_applied.append("loop_unrolling")
        return optimized
    
    def _strength_reduction(self, tree: ast.AST) -> ast.AST:
        class StrengthReducer(ast.NodeTransformer):
            def visit_BinOp(self, node):
                self.generic_visit(node)
                
                if isinstance(node.op, ast.Mult):
                    if isinstance(node.right, ast.Constant) and node.right.value == 2:
                        return ast.BinOp(
                            left=node.left,
                            op=ast.Add(),
                            right=node.left
                        )
                    
                    if isinstance(node.right, ast.Constant):
                        if node.right.value & (node.right.value - 1) == 0:
                            power = (node.right.value - 1).bit_length()
                            return ast.BinOp(
                                left=node.left,
                                op=ast.LShift(),
                                right=ast.Constant(value=power)
                            )
                
                if isinstance(node.op, ast.Div):
                    if isinstance(node.right, ast.Constant):
                        if node.right.value & (node.right.value - 1) == 0:
                            power = (node.right.value - 1).bit_length()
                            return ast.BinOp(
                                left=node.left,
                                op=ast.RShift(),
                                right=ast.Constant(value=power)
                            )
                
                return node
        
        reducer = StrengthReducer()
        optimized = reducer.visit(tree)
        self.optimizations_applied.append("strength_reduction")
        return optimized
    
    def optimize_imports(self, tree: ast.AST) -> ast.AST:
        class ImportOptimizer(ast.NodeTransformer):
            def __init__(self):
                self.used_imports = set()
                self.all_names = set()
                
            def visit_Name(self, node):
                self.all_names.add(node.id)
                return node
            
            def visit_Import(self, node):
                filtered_names = []
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    if name in self.all_names:
                        filtered_names.append(alias)
                
                if filtered_names:
                    node.names = filtered_names
                    return node
                return None
        
        optimizer = ImportOptimizer()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                optimizer.visit_Name(node)
        
        optimized = optimizer.visit(tree)
        self.optimizations_applied.append("import_optimization")
        return optimized
    
    def remove_docstrings(self, tree: ast.AST) -> ast.AST:
        class DocstringRemover(ast.NodeTransformer):
            def visit_FunctionDef(self, node):
                self.generic_visit(node)
                
                if node.body and isinstance(node.body[0], ast.Expr):
                    if isinstance(node.body[0].value, ast.Constant):
                        if isinstance(node.body[0].value.value, str):
                            node.body = node.body[1:]
                
                return node
            
            def visit_ClassDef(self, node):
                self.generic_visit(node)
                
                if node.body and isinstance(node.body[0], ast.Expr):
                    if isinstance(node.body[0].value, ast.Constant):
                        if isinstance(node.body[0].value.value, str):
                            node.body = node.body[1:]
                
                return node
            
            def visit_Module(self, node):
                self.generic_visit(node)
                
                if node.body and isinstance(node.body[0], ast.Expr):
                    if isinstance(node.body[0].value, ast.Constant):
                        if isinstance(node.body[0].value.value, str):
                            node.body = node.body[1:]
                
                return node
        
        remover = DocstringRemover()
        optimized = remover.visit(tree)
        self.optimizations_applied.append("docstring_removal")
        return optimized
    
    def optimize_bytecode(self, code_obj):
        import types
        
        new_consts = []
        for const in code_obj.co_consts:
            if isinstance(const, types.CodeType):
                new_consts.append(self.optimize_bytecode(const))
            else:
                new_consts.append(const)
        
        optimized = types.CodeType(
            code_obj.co_argcount,
            code_obj.co_posonlyargcount,
            code_obj.co_kwonlyargcount,
            code_obj.co_nlocals,
            code_obj.co_stacksize,
            code_obj.co_flags,
            code_obj.co_code,
            tuple(new_consts),
            code_obj.co_names,
            code_obj.co_varnames,
            code_obj.co_filename,
            code_obj.co_name,
            code_obj.co_firstlineno,
            code_obj.co_lnotab,
            code_obj.co_freevars,
            code_obj.co_cellvars
        )
        
        return optimized
    
    def compress_names(self, tree: ast.AST) -> ast.AST:
        class NameCompressor(ast.NodeTransformer):
            def __init__(self):
                self.name_map = {}
                self.counter = 0
                
            def _get_short_name(self, original):
                if original not in self.name_map:
                    self.name_map[original] = f"_{MERO}{self.counter}"
                    self.counter += 1
                return self.name_map[original]
            
            def visit_FunctionDef(self, node):
                if not node.name.startswith('_'):
                    node.name = self._get_short_name(node.name)
                self.generic_visit(node)
                return node
            
            def visit_Name(self, node):
                if not node.id.startswith('_'):
                    node.id = self._get_short_name(node.id)
                return node
        
        compressor = NameCompressor()
        optimized = compressor.visit(tree)
        self.optimizations_applied.append("name_compression")
        return optimized
    
    def full_optimization(self, source_code: str) -> Tuple[str, List[str]]:
        try:
            tree = ast.parse(source_code)
        except SyntaxError as e:
            return source_code, [f"Syntax error: {e}"]
        
        tree = self.optimize_ast(tree)
        tree = self.optimize_imports(tree)
        tree = self.remove_docstrings(tree)
        tree = self.compress_names(tree)
        
        ast.fix_missing_locations(tree)
        
        try:
            optimized_code = ast.unparse(tree)
        except Exception:
            optimized_code = source_code
        
        return optimized_code, self.optimizations_applied
    
    def analyze_performance(self, source_code: str) -> Dict[str, Any]:
        try:
            tree = ast.parse(source_code)
        except SyntaxError:
            return {'error': 'Syntax error in code'}
        
        stats = {
            'total_lines': len(source_code.split('\n')),
            'functions': 0,
            'classes': 0,
            'loops': 0,
            'conditionals': 0,
            'imports': 0,
            'complexity_score': 0
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                stats['functions'] += 1
            elif isinstance(node, ast.ClassDef):
                stats['classes'] += 1
            elif isinstance(node, (ast.For, ast.While)):
                stats['loops'] += 1
            elif isinstance(node, ast.If):
                stats['conditionals'] += 1
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                stats['imports'] += 1
        
        stats['complexity_score'] = (
            stats['functions'] * 2 +
            stats['classes'] * 5 +
            stats['loops'] * 3 +
            stats['conditionals'] * 1
        )
        
        return stats

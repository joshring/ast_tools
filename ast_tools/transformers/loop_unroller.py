import ast
from copy import deepcopy
import astor
from .symbol_replacer import replace_symbols
from ..macros import unroll


def is_call(node):
    return isinstance(node, ast.Call)


def is_name(node):
    return isinstance(node, ast.Name)


class Unroller(ast.NodeTransformer):
    def __init__(self, env):
        self.env = env

    def visit_For(self, node):
        node = super().generic_visit(node)
        try:
            iter_obj = eval(astor.to_source(node.iter), {}, self.env)
            is_constant = True
        except Exception as e:
            is_constant = False
        if is_constant and isinstance(iter_obj, unroll):
            body = []
            for i in iter_obj:
                if not isinstance(i, int):
                    raise NotImplementedError("Unrolling over iterator of"
                                              "non-int")
                symbol_table = {node.target.id: ast.Num(i, kind=None)}
                for child in node.body:
                    body.append(
                        replace_symbols(deepcopy(child), symbol_table)
                    )
            return body
        return node


def unroll_for_loops(tree, env):
    return Unroller(env).visit(tree)




class Unroller_by_factor(ast.NodeTransformer):
    """
    unroll a loop, giving a constant number of evaluations per loop iteration
    """
    def __init__(self, env, factor):
        self.env = env
        self.factor = abs(factor)


    def visit_For(self, node):
        """
        function to be run while traversing ast node of `For` loops
        
            ast.For attributes: 'target', 'iter', 'body', 'orelse'
        """
        node = super().generic_visit(node)
        ## if iteration expression (iter) evaluates as a constant, using only (env) variables we determine it is unrollable
        try:
            iter_obj = eval(astor.to_source(node.iter), {}, self.env)
            is_constant = True
        except Exception as e:
            is_constant = False
    
        
        ## we only allow this transform on ranges, not on lists
        ## TODO: We could apply an additional type check and specialisation for lists below, better to do so outside of this tight for loop
        if is_constant and isinstance(iter_obj, range):

            if iter_obj.step not in [1,-1]:
                raise ValueError(f'unrolling range({iter_obj.start}, {iter_obj.stop}, {iter_obj.step}) is not supported, '
                                 f'only ranges with step=1, or step=-1 are supported, but {iter_obj.step} was provided')

            
            iteration_range = abs( abs(iter_obj.start) - abs(iter_obj.stop) )
            ## loop is NOP
            if iteration_range == 0:
                return None
            
            if self.factor > iteration_range:
                raise ValueError(f'factor {self.factor} was larger than the iteration range of {iteration_range}')
            
            
            if iteration_range % self.factor > 0:
                raise ValueError(f'the iteration_range: {iteration_range} is not exactly divisible by factor: {self.factor}')
              

            new_loop_body = []

            ## imcrementing range
            if iter_obj.stop > iter_obj.start:
                
                for unrol_iter in range(0, self.factor):

                    """
                    For each iteration to be unrolled, it appends the contents of the For loop body to the return list (after) 
                    replacing any instances of the loop variable with the current iteration's value. `ast.Num(i, kind=None)`
                    This is done using the symbol_table
                    """

                    replacement_ast_node = ast.BinOp(
                        left    = ast.Name(id=node.target.id, ctx=ast.Load()), 
                        op      = ast.Add(), 
                        right   = ast.Num(n=unrol_iter, kind=None)
                    )
                        
                    
                    ## node.target.id is the iteration variable's name, eg `i` from the example `for i in range(4)` which is replaced by the iteration's value of i
                    symbol_table = {node.target.id: replacement_ast_node}
                    
                    ## iterating through loop body 
                    for body_object in node.body:
                        new_loop_body.append(
                            replace_symbols(
                                tree            = deepcopy(body_object), 
                                symbol_table    = symbol_table
                            )
                        )

                
                ## create new ast.For object with the newly unrolled loop body
                replacement_for_node = ast.For(
                    target      = ast.Name(id='i', ctx=ast.Store()), 
                    iter        = ast.Call(
                        func        = ast.Name(id='range', ctx=ast.Load()), 
                        args        = [ast.Num(n=iter_obj.start), ast.Num(n=iter_obj.stop), ast.Num(n=self.factor),], 
                        keywords    = []
                    ),
                    body        = new_loop_body,
                    orelse      = []
                )
                
                return replacement_for_node
            
                        
            ## decrementing range
            else:

                for unroll_iteration in range(0, self.factor):

                    """
                    For each iteration to be unrolled, it appends the contents of the For loop body to the return list (after) 
                    replacing any instances of the loop variable with the current iteration's value. `ast.Num(i, kind=None)`
                    This is done using the symbol_table
                    """

                    replacement_ast_node = ast.BinOp(
                        left    = ast.Name(id=node.target.id, ctx=ast.Load()), 
                        op      = ast.Sub(), 
                        right   = ast.Num(n=unroll_iteration, kind=None)
                    )
                        
                    
                    ## node.target.id is the iteration variable's name, eg `i` from the example `for i in range(4)` which is replaced by the iteration's value of i
                    symbol_table = {node.target.id: replacement_ast_node}
                    
                    ## iterating through loop body 
                    for body_object in node.body:
                        new_loop_body.append(
                            replace_symbols(
                                tree            = deepcopy(body_object), 
                                symbol_table    = symbol_table
                            )
                        )

                
                ## create new ast.For object with the newly unrolled loop body
                replacement_for_node = ast.For(
                    target      = ast.Name(id='i', ctx=ast.Store()), 
                    iter        = ast.Call(
                        func        = ast.Name(id='range', ctx=ast.Load()), 
                        args        = [ast.Num(n=iter_obj.start), ast.Num(n=iter_obj.stop), ast.Num(n=self.factor * -1),], 
                        keywords    = []
                    ),
                    body        = new_loop_body,
                    orelse      = iter_obj.orelse
                )
                
                return replacement_for_node
            

        
        ## if isinstance of a general iterator over say a list, could likely do the same trick as above over the list indicies
        elif is_constant and isinstance(iter_obj, unroll):
            raise NotImplementedError('Only implemented for `for` loops which iterate over a range, eg `for i in range(22)`')
        
        return node


def unroll_for_loops_by_factor(tree, env, factor):
    return Unroller_by_factor(env=env, factor=factor).visit(node=tree)


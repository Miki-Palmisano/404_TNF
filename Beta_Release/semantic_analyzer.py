class SemanticAnalyzer:
    def __init__(self, ast):
        self.ast = ast
        self.symbol_table = {}

    def analyze(self):
        for stmt in self.ast:
            self.visit(stmt, self.symbol_table)

    def visit(self, node, table):
        match node:
            case ('declare', type_, name, expr):
                if name in table:
                    raise ValueError(f"Variable '{name}' already declared")
                if expr:
                    expr_type = self.expr_type(expr, table)
                    if not self.type_compatible(type_, expr_type):
                        raise TypeError(f"Type incompatibility in declaration of '{name}': {type_} vs {expr_type}")
                table[name] = type_
            case ('assign', name, expr):
                if name not in table:
                    raise ValueError(f"Variable '{name}' not declared")
                expr_type = self.expr_type(expr, table)
                var_type = table[name]
                if not self.type_compatible(var_type, expr_type):
                    raise TypeError(f"Type incompatibility in assignment to '{name}': {var_type} vs {expr_type}")
            case ('if', condition, body, else_body):
                # Ensure condition evaluates to a boolean type
                cond_type = self.expr_type(condition, table)
                if cond_type != 'TYPE_BOOL':
                    raise TypeError(f"If condition must be a boolean, got {cond_type}")
                for stmt in body:
                    self.visit(stmt, table)
                for stmt in else_body:
                    self.visit(stmt, table)
            case ('while', condition, body):
                # Ensure condition evaluates to a boolean type
                cond_type = self.expr_type(condition, table)
                if cond_type != 'TYPE_BOOL':
                    raise TypeError(f"While condition must be a boolean, got {cond_type}")
                for stmt in body:
                    self.visit(stmt, table)
            case ('increment', name) | ('decrement', name):
                if name not in table:
                    raise ValueError(f"Variable '{name}' not declared")
                var_type = table[name]
                if var_type not in ('TYPE_INT', 'TYPE_FLOAT'):
                    raise TypeError(f"Increment/decrement not valid for type '{var_type}'")
            case ('cout', expr):
                self.expr_type(expr, table)  # Just ensure the expression can be evaluated
            case ('cin', name):
                if name not in table:
                    raise ValueError(f"Variable '{name}' not declared")
            case ('function_def', return_type, name, params, body):
                if name in table:
                    raise ValueError(f"Function '{name}' already declared")
                # Store function signature in the symbol table
                table[name] = ('function', return_type, params)

                # Create a new local scope for function parameters and body
                local_table = table.copy()
                for ptype, pname in params:
                    if pname in local_table:
                        raise ValueError(f"Parameter '{pname}' in function '{name}' already declared in this scope")
                    local_table[pname] = ptype

                # Analyze the function body within its local scope
                for stmt in body:
                    self.visit(stmt, local_table)
            case ('call', name, args):
                # This case is now handled in expr_type, but it's good to keep a visit for statement-level calls
                self.expr_type(node, table)  # Delegate type checking to expr_type
            case ('return', expr):
                # For simplicity, we are not checking if the return type matches the function's declared return type here.
                # In a full-fledged compiler, you'd need to know the current function's return type.
                self.expr_type(expr, table)
            case _:
                raise ValueError(f"Unknown node type: {node}")

    def expr_type(self, expr, table):
        match expr:
            case ('int', _):
                return 'TYPE_INT'
            case ('float', _):
                return 'TYPE_FLOAT'
            case ('string', _):
                return 'TYPE_STRING'
            case ('bool', _):
                return 'TYPE_BOOL'
            case ('var', name):
                if name not in table:
                    raise ValueError(f"Variable '{name}' not declared")
                return table[name]
            case ('minus', inner) | ('not', inner):
                inner_type = self.expr_type(inner, table)
                if expr[0] == 'minus' and inner_type not in ('TYPE_INT', 'TYPE_FLOAT'):
                    raise TypeError(f"Unary minus not valid for type '{inner_type}'")
                if expr[0] == 'not' and inner_type != 'TYPE_BOOL':
                    raise TypeError(f"Logical NOT not valid for type '{inner_type}'")
                return inner_type

            case ('funcall', name, args):
                if name not in table or table[name][0] != 'function':
                    raise ValueError(f"Function '{name}' not declared or is not a function")

                func_return_type, func_params = table[name][1], table[name][2]

                if len(func_params) != len(args):
                    raise TypeError(
                        f"Function '{name}' called with incorrect number of arguments: expected {len(func_params)}, got {len(args)}")

                for i, (param_type, _) in enumerate(func_params):
                    arg_type = self.expr_type(args[i], table)
                    if not self.type_compatible(param_type, arg_type):
                        raise TypeError(
                            f"Type incompatibility in argument {i + 1} of function '{name}': expected {param_type}, got {arg_type}")

                return func_return_type

            case ("binop", op, left, right):
                ltype = self.expr_type(left, table)
                rtype = self.expr_type(right, table)
                if op in ('PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'MODULE'):
                    if ltype == rtype and ltype in ('TYPE_INT', 'TYPE_FLOAT'):
                        return ltype
                    # Allow int and float to mix for arithmetic operations, result is float
                    if (ltype == 'TYPE_INT' and rtype == 'TYPE_FLOAT') or \
                            (ltype == 'TYPE_FLOAT' and rtype == 'TYPE_INT'):
                        return 'TYPE_FLOAT'
                    else:
                        raise TypeError(f"Arithmetic operation of incompatible type: {ltype}, {rtype}")
                if op in ('EQ', 'NEQ', 'LT', 'GT', 'LE', 'GE'):
                    if ltype == rtype:  # Basic type check for comparisons
                        return 'TYPE_BOOL'
                    else:
                        raise TypeError(f"Incompatible types for comparison: {ltype}, {rtype}")
                if op in ('AND', 'OR'):
                    if ltype == rtype == 'TYPE_BOOL':
                        return 'TYPE_BOOL'
                    else:
                        raise TypeError(f"Logical operator between non-boolean types: {ltype}, {rtype}")
                raise TypeError(f"Unknown operator: {op}")

            case ('concat', left, right):
                self.expr_type(left, table)  # Ensure left is valid
                self.expr_type(right, table)
                return 'TYPE_STRING'  # Concatenation always results in a string

            case _:
                raise TypeError(f"Expression not recognized: {expr}")

    def type_compatible(self, declared, expr_type):
        if declared == expr_type:
            return True
        if declared == 'TYPE_FLOAT' and expr_type == 'TYPE_INT':
            return True
        return False


if __name__ == '__main__':

    code = '''

    int somma(int a, int b) {
        return a + b;
    }

    int i = 0;
    int j = 0;
    int outer_limit = 1000;
    int inner_limit = 1000;
    int somma_result = somma(5, 10);

    cout << "Value: " << somma_result << endl;

    while (i < outer_limit) {
        j = 0;
        while (j < inner_limit) {
            if ((i + j) % 2 == 0) {
                cout << "Even sum: " << (i + j) << endl;
            } else {
                cout << "Odd sum: " << (i + j) << endl;
            }
            j++;
        }
        i++;
    }
    '''

    from lexer import lexer
    from parser import parser

    tokens = lexer(code)
    ast = parser(tokens).parse()
    analyzer = SemanticAnalyzer(ast)
    analyzer.analyze()
    print("Semantic analysis completed successfully.")
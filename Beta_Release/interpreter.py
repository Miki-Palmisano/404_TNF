class Interpreter:
    def __init__(self, ast):
        self.ast = ast
        self.env = {}

    def run(self):
        for stmt in self.ast:
            self.execute(stmt)

    def execute(self, node, current_function_returntype=None):
        match node:
            case ("function_def", rettype, name, params, body):
                self.env[name] = ("function", rettype, params, body)
            case ("declare", tipo, nome, expr):
                if nome in self.env:
                    raise RuntimeError(f"Variable '{nome}' already declared")
                value = self.eval_expr(expr) if expr else None
                # Controllo: se expr è funcall e la funzione è void, errore!
                if isinstance(expr, tuple) and expr[0] == "funcall":
                    func_name = expr[1]
                    if func_name in self.env and self.env[func_name][1] == "VOID":
                        raise RuntimeError(f"Cannot assign the result of void function '{func_name}' to a variable")
                self.env[nome] = (tipo, value)
            case ("assign", nome, expr):
                if nome not in self.env:
                    raise RuntimeError(f"Variable '{nome}' not declared")
                tipo, _ = self.env[nome]
                value = self.eval_expr(expr)
                if isinstance(expr, tuple) and expr[0] == "funcall":
                    func_name = expr[1]
                    if func_name in self.env and self.env[func_name][1] == "VOID":
                        raise RuntimeError(f"Cannot assign the result of void function '{func_name}' to a variable")
                self.env[nome] = (tipo, value)
            case ("if", cond, body, else_body):
                cond_value = self.eval_expr(cond)
                if cond_value:
                    for stmt in body:
                        self.execute(stmt, current_function_returntype)
                else:
                    for stmt in else_body:
                        self.execute(stmt, current_function_returntype)
            case ("while", cond, body):
                while self.eval_expr(cond):
                    for stmt in body:
                        self.execute(stmt, current_function_returntype)
            case ("cout", expr):
                value = self.eval_expr(expr)
                if value is not None:
                    print(value)
            case ("cin", var):
                if var not in self.env:
                    raise RuntimeError(f"Variable '{var}' not declared")
                tipo, _ = self.env[var]
                user_input = input(f"Enter value for {var} ({tipo}): ")
                if tipo == "TYPE_INT":
                    value = int(user_input)
                elif tipo == "TYPE_FLOAT":
                    value = float(user_input)
                elif tipo == "TYPE_STRING":
                    value = user_input
                self.env[var] = (tipo, value)
            case ("funcall", name, args):
                self.eval_expr(("funcall", name, args))

            case ("return", expr):
                # Passa il rettype corrente (lo passa funcall nell'argomento current_function_returntype)
                if current_function_returntype == "VOID" and expr is not None:
                    raise RuntimeError("Cannot return a value from a void function")
                val = self.eval_expr(expr) if expr is not None else None
                return ("return", val)
            case _:
                raise RuntimeError(f"Unknown statement: {node}")

    def eval_expr(self, expr):
        match expr:
            case ("int", val):
                return int(val)
            case ("float", val):
                return float(val)
            case ("string", val):
                return val.strip('"')
            case ("var", name):
                if name not in self.env:
                    raise RuntimeError(f"Variable '{name}' not declared")
                return self.env[name][1]
            case ("binop", op, left, right):
                l = self.eval_expr(left)
                r = self.eval_expr(right)
                match op:
                    case "PLUS": return l + r
                    case "MINUS": return l - r
                    case "TIMES": return l * r
                    case "DIVIDE": return l / r
                    case "EQ": return l == r
                    case "LT": return l < r
                    case "GT": return l > r
                    case "LE": return l <= r
                    case "GE": return l >= r
                raise RuntimeError(f"Unsupported operator {op}")
            case ("not", inner):
                return not self.eval_expr(inner)
            case ("funcall", name, args):
                if name not in self.env or self.env[name][0] != "function":
                    raise RuntimeError(f"Function '{name}' not defined")
                _, rettype, params, body = self.env[name]
                if len(params) != len(args):
                    raise RuntimeError(f"Function '{name}' expects {len(params)} args, got {len(args)}")
                arg_values = [self.eval_expr(arg) for arg in args]
                saved_env = self.env.copy()
                self.env = self.env.copy()
                for (ptype, pname), value in zip(params, arg_values):
                    self.env[pname] = (ptype, value)
                ret_val = None
                try:
                    for stmt in body:
                        result = self.execute(stmt, rettype)  # Passa il rettype corrente!
                        if isinstance(result, tuple) and result[0] == "return":
                            ret_val = result[1]
                            break
                finally:
                    self.env = saved_env
                if rettype == "VOID":
                    return None
                if rettype in ("TYPE_INT", "TYPE_FLOAT", "TYPE_STRING") and ret_val is None:
                    raise RuntimeError(
                        f"Function '{name}' declared as {rettype[5:].lower()} but missing return statement")
                return ret_val
            case _:
                raise RuntimeError(f"Invalid expression: {expr}")




if __name__ == "__main__":
    from lexer import lexer
    from parser import Parser

    codice = '''
    int counter = 0;
    
    while ( counter < 5 ) {
        cout << counter;
        counter += 1;
    }
    '''

    tokens = lexer(codice)
    parser = Parser(tokens)
    ast = parser.parse()

    print("\n--- Interprete Output ---")
    interpreter = Interpreter(ast)
    interpreter.run()

class Interpreter:
    def __init__(self, ast):
        self.ast = ast
        self.env = {}

    def run(self):
        for stmt in self.ast:
            self.execute(stmt)

    def execute(self, node):
        match node:
            case ("function_def", rettype, name, params, body):
                self.env[name] = ("function", rettype, params, body)
            case ("declare", tipo, nome, expr):
                if nome in self.env:
                    raise RuntimeError(f"Variable '{nome}' already declared")
                value = self.eval_expr(expr) if expr else None
                self.env[nome] = (tipo, value)
            case ("assign", nome, expr):
                if nome not in self.env:
                    raise RuntimeError(f"Variable '{nome}' not declared")
                tipo, _ = self.env[nome]
                value = self.eval_expr(expr)
                self.env[nome] = (tipo, value)
            case ("if", cond, body, else_body):
                cond_value = self.eval_expr(cond)
                if cond_value:
                    for stmt in body:
                        self.execute(stmt)
                else:
                    for stmt in else_body:
                        self.execute(stmt)
            case ("while", cond, body):
                while self.eval_expr(cond):
                    for stmt in body:
                        self.execute(stmt)
            case ("cout", expr):
                print(self.eval_expr(expr))
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
            case ("return", expr):
                return ("return", self.eval_expr(expr))
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
                        result = self.execute(stmt)
                        if isinstance(result, tuple) and result[0] == "return":
                            ret_val = result[1]
                            break
                finally:
                    self.env = saved_env
                return ret_val
            case _:
                raise RuntimeError(f"Invalid expression: {expr}")



if __name__ == "__main__":
    from lexer import lexer
    from parser import Parser

    codice = '''
    
    int somma(int a, int b) {
    return a + b;
    }

    int x = somma(2, 3);
    cout << x;

    '''

    tokens = lexer(codice)
    parser = Parser(tokens)
    ast = parser.parse()

    print("\n--- Interprete Output ---")
    interpreter = Interpreter(ast)
    interpreter.run()

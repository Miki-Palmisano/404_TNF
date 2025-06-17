class Interpreter:
    def __init__(self, ast):
        self.ast = ast
        self.env = {}  # Symbol table: variabili definite

    def run(self):
        for stmt in self.ast:
            self.execute(stmt)

    def execute(self, node):
        match node:
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
                if tipo == "INT":
                    value = int(user_input)
                elif tipo == "FLOAT":
                    value = float(user_input)
                elif tipo == "STRING":
                    value = user_input
                self.env[var] = (tipo, value)

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
            case _:
                raise RuntimeError(f"Invalid expression: {expr}")


if __name__ == "__main__":
    from lexer import lexer
    from parser import Parser

    codice = '''
    a = 5;
    float b = 3;
    if (a > b) {
        cout << a+b;
    } else {
        cout << "Ciao belliiii";
    }
    '''

    tokens = lexer(codice)
    parser = Parser(tokens)
    ast = parser.parse()

    print("\n--- Interprete Output ---")
    interpreter = Interpreter(ast)
    interpreter.run()

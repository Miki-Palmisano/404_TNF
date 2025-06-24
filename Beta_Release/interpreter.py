class Interpreter:
    def __init__(self, ast):
        self.ast = ast
        self.env_stack = [{}]

    def run(self):
        for stmt in self.ast:
            self.execute(stmt)

    def lookup(self, name):
        # Cerca dallo scope locale a quello globale
        for env in reversed(self.env_stack):
            if name in env:
                return env[name]
        raise RuntimeError(f"Variable '{name}' not declared")

    def assign(self, name, value):
        # Assegna alla variabile nel primo scope dove esiste
        for env in reversed(self.env_stack):
            if name in env:
                if value[0] != env[name][0]:
                    raise RuntimeError(f"Type mismatch in assignment to '{name}': {env[name][0]} vs {value[0]}")
                env[name] = value
                return
        raise RuntimeError(f"Variable '{name}' not declared")

    def declare(self, name, tipo, value):
        env = self.env_stack[-1] # Prende l'ambiente corrente
        if name in env:
            raise RuntimeError(f"Variable '{name}' already declared")
        env[name] = (tipo, value)

    def execute(self, node, current_function_returntype=None):
        match node:
            case ("function_def", return_type, name, params, body):
                self.env_stack[0][name] = ("function", return_type, params, body)

            case ("declare", tipo, name, expr):
                value = self.eval_expr(expr) if expr else None
                self.declare(name, tipo, value)

            case ("assign", name, expr):
                value = self.eval_expr(expr)
                _, _ = self.lookup(name)
                self.assign(name, (self.lookup(name)[0], value))

            case ("if", cond, body, else_body):
                self.env_stack.append({})  # Aggiunge un nuovo ambiente locale per l'if
                try:
                    branch = body if self.eval_expr(cond) else else_body
                    for stmt in branch:
                        result = self.execute(stmt, current_function_returntype)
                        if isinstance(result, tuple) and result[0] == "return":
                            return result
                finally:
                    self.env_stack.pop()  # Rimuove l'ambiente locale dopo l'esecuzione dell'if/else

            case ("while", cond, body):
                while self.eval_expr(cond):
                    self.env_stack.append({})
                    try:
                        for stmt in body:
                            result = self.execute(stmt, current_function_returntype)
                            if isinstance(result, tuple) and result[0] == "return":
                                return result
                    finally:
                        self.env_stack.pop()  # Rimuove l'ambiente locale dopo l'esecuzione del ciclo

            case ("cout", expr):
                output = self.eval_expr(expr)
                if output is not None:
                    print(output, end="")

            case ("cin", vars_):   # Gestisce l'input da tastiera per più variabili
                raw_inputs = input().strip().split()  # Legge la riga e la divide in parole (valori)

                if len(raw_inputs) < len(vars_):  # Verifica che ci siano abbastanza input
                    raise RuntimeError(
                        f"Expected {len(vars_)} inputs, got {len(raw_inputs)}")

                for name, text in zip(vars_, raw_inputs):  # Associa ogni input a una variabile
                    tipo, _ = self.lookup(name)   # Recupera il tipo della variabile
                    try:  # Prova a convertire in base al tipo
                        value = int(text) if tipo == "TYPE_INT" else \
                            float(text) if tipo == "TYPE_FLOAT" else text
                    except ValueError:  # Errore se la conversione fallisce
                        raise RuntimeError(
                            f"Cannot assign '{text}' to {tipo} variable '{name}'")
                    self.assign(name, (tipo, value))  # Assegna il valore convertito alla variabile

            case ("funcall", name, args):
                self.eval_expr(("funcall", name, args))

            case ("return", expr):
                val = self.eval_expr(expr) if expr is not None else None
                return ("return", val)

            case ("pre_increment", var):  # Gestisce ++x;
                type_, value = self.lookup(var)
                new_value = value + 1 if type_ == "TYPE_INT" else value + 1.0
                self.assign(var, (type_, new_value))
                return new_value

            case ("pre_decrement", var):  # Gestisce --x;
                type_, value = self.lookup(var)
                new_value = value - 1 if type_ == "TYPE_INT" else value - 1.0
                self.assign(var, (type_, new_value))
                return new_value

            case ("post_increment", var):
                type_, value = self.lookup(var)
                new_value = value + 1 if type_ == "TYPE_INT" else value + 1.0
                self.assign(var, (type_, new_value))
                return value

            case ("post_decrement", var):
                type_, value = self.lookup(var)
                new_value = value - 1 if type_ == "TYPE_INT" else value - 1.0
                self.assign(var, (type_, new_value))
                return value

    def eval_expr(self, expr):
        match expr:
            case ("int", val): return int(val)
            case ("float", val): return float(val)
            case ("string", val): return val
            case ('bool', value): return value.lower() == 'true'

            case ("var", name):
                return self.lookup(name)[1]

            case ("concat", expr, next_expr):
                return str(self.eval_expr(expr)) + str(self.eval_expr(next_expr))

            case ('pre_increment') | ('post_increment') | ('pre_decrement') | ('post_decrement') as op, name:
                return self.execute((op, name))

            case ('not', inner): return not self.eval_expr(inner)

            case ('minus', inner): return -self.eval_expr(inner)

            case ('binop', op, left, right):
                l = self.eval_expr(left)
                r = self.eval_expr(right)

                match op:
                    case "PLUS": return l + r
                    case "MINUS": return l - r
                    case "TIMES": return l * r
                    case "DIVIDE": return l / r
                    case "MODULE": return l % r
                    case "AND":
                        if isinstance(l, str) or isinstance(r, str):
                            raise RuntimeError("Cannot apply logical AND to string operands")
                        return int(bool(l) and bool(r))
                    case "OR":
                        if isinstance(l, str) or isinstance(r, str):
                            raise RuntimeError("Cannot apply logical OR to string operands")
                        return int(bool(l) or bool(r))
                    case "NEQ": return l != r
                    case "EQ": return l == r
                    case "LT": return l < r
                    case "GT": return l > r
                    case "LE": return l <= r
                    case "GE": return l >= r
                raise RuntimeError(f"Unsupported operator {op} in expression {expr}")

            case ("funcall", name, args):
                func = self.lookup(name)
                if func[0] != "function":
                    raise RuntimeError(f"'{name}' is not a function")
                _, return_type, params, body = func
                if len(params) != len(args):
                    raise RuntimeError(f"Function '{name}' expects {len(params)} args, got {len(args)}")
                arg_values = [self.eval_expr(arg) for arg in args]

                new_env = {}
                for (ptype, pname), value in zip(params, arg_values):
                    new_env[pname] = (ptype, value)

                self.env_stack.append(new_env)

                try:
                    for stmt in body:
                        result = self.execute(stmt, return_type)
                        if isinstance(result, tuple) and result[0] == "return":
                            return result[1]
                finally:
                    self.env_stack.pop()  # Rimuove l'ambiente locale dopo l'esecuzione della funzione

                if return_type == "VOID":
                    return None
                if return_type in ("TYPE_INT", "TYPE_FLOAT", "TYPE_STRING", "TYPE_BOOL"):
                    raise RuntimeError(
                        f"Function '{name}' declared as {return_type[5:].lower()} but missing return statement")

            case _:
                raise RuntimeError(f"Invalid expression: {expr}")




if __name__ == "__main__":
    from lexer import lexer
    from parser import Parser
    from semantic_analyzer import SemanticAnalyzer

    codice = '''
    int z = 0;
    int somma(int a, int b) {
        return a + b;
    }
    int main() {
        int x = 5;
        int y = 10;
        z = somma(x, y);
        cout << "La somma è: " << z << endl;
        return 0;
    }
    '''

    tokens = lexer(codice)
    parser = Parser(tokens)
    ast = parser.parse()
    SemanticAnalyzer(ast).analyze()

    interpreter = Interpreter(ast)

    # registra funzioni e variabili globali
    for stmt in ast:
        if isinstance(stmt, tuple) and stmt[0] in ("function_def", "declare", "assign"):
            interpreter.execute(stmt)

    interpreter.eval_expr(("funcall", "main", []))
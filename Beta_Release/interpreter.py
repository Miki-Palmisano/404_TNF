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
                env[name] = value
                return
        raise RuntimeError(f"Variable '{name}' not declared")

    def declare(self, name, tipo, value):
        env = self.env_stack[-1] # Prende l'ambiente corrente (l'ultimo della pila, funziona poiché l'ultimo è quello locale cancellato dopo l'esecuzione)
        if name in env:
            raise RuntimeError(f"Variable '{name}' already declared")
        env[name] = (tipo, value)

    def execute(self, node, current_function_returntype=None):
        match node:
            case ("function_def", return_type, name, params, body):
                self.env_stack[0][name] = ("function", return_type, params, body)

            case ("declare", tipo, name, expr):
                value = self.eval_expr(expr) if expr else None
                # Controllo: se expr è funcall e la funzione è void, errore!
                if isinstance(expr, tuple) and expr[0] == "funcall":
                    func_name = expr[1]
                    func = self.lookup(func_name)
                    if func[1] == "VOID":
                        raise RuntimeError(f"Cannot assign the result of void function '{func_name}' to a variable")
                self.declare(name, tipo, value)

            case ("assign", name, expr):
                value = self.eval_expr(expr)
                if isinstance(expr, tuple) and expr[0] == "funcall":
                    func_name = expr[1]
                    func = self.lookup(func_name)
                    if func[1] == "VOID":
                        raise RuntimeError(f"Cannot assign the result of void function '{func_name}' to a variable")
                type_, _ = self.lookup(name)
                self.assign(name, (type_, value))

            case ("if", cond, body, else_body):
                if self.eval_expr(cond):
                    self.env_stack.append({})
                    for stmt in body:
                        self.execute(stmt, current_function_returntype)
                    self.env_stack.pop() # Rimuove l'ambiente locale dopo l'esecuzione dell'if
                else:
                    self.env_stack.append({})
                    for stmt in else_body:
                        self.execute(stmt, current_function_returntype)
                    self.env_stack.pop() # Rimuove l'ambiente locale dopo l'esecuzione dell'if/else

            case ("while", cond, body):
                while self.eval_expr(cond):
                    self.env_stack.append({})
                    for stmt in body:
                        self.execute(stmt, current_function_returntype)
                    self.env_stack.pop() # Rimuove l'ambiente locale dopo l'esecuzione del ciclo

            case ("cout", expr):
                output = self.eval_expr(expr)
                if output is not None:
                    print(output, end="")

            case ("cin", var):
                value = input()
                type_ = self.lookup(var)

                if type_ == "TYPE_INT":
                    self.assign(var, ("TYPE_INT", int(value)))
                elif type_ == "TYPE_FLOAT":
                    self.assign(var, ("TYPE_FLOAT", int(value)))
                elif type_ == "TYPE_STRING":
                    self.assign(var, ("TYPE_STRING", int(value)))

            case ("funcall", name, args):
                self.eval_expr(("funcall", name, args))

            case ("return", expr):
                # Passa il rettype corrente (lo passa funcall nell'argomento current_function_returntype)
                if current_function_returntype == "VOID" and expr is not None:
                    raise RuntimeError("Cannot return a value from a void function")
                val = self.eval_expr(expr) if expr is not None else None
                return ("return", val)

            case ("pre_increment", var):
                type_, value = self.lookup(var)
                if type_ not in ("TYPE_INT", "TYPE_FLOAT"):
                    raise RuntimeError(f"Cannot increment variable '{var}' of type {type_}")
                new_value = value + 1 if type_ == "TYPE_INT" else value + 1.0
                self.assign(var, (type_, new_value))
                return new_value  # Restituisce il nuovo valore dopo l'incremento

            case ("pre_decrement", var):
                type_, value = self.lookup(var)
                if type_ not in ("TYPE_INT", "TYPE_FLOAT"):
                    raise RuntimeError(f"Cannot decrement variable '{var}' of type {type_}")
                new_value = value - 1 if type_ == "TYPE_INT" else value - 1.0
                self.assign(var, (type_, new_value))
                return new_value  # Restituisce il nuovo valore dopo il decremento

            case ("post_increment", var):
                type_, value = self.lookup(var)
                if type_ not in ("TYPE_INT", "TYPE_FLOAT"):
                    raise RuntimeError(f"Cannot increment variable of type '{type_}'")
                new_value = value + 1 if type_ == "TYPE_INT" else value + 1.0
                self.assign(var, (type_, new_value))
                return value  # Restituisce il valore prima dell'incremento

            case ("post_decrement", var):
                type_, value = self.lookup(var)
                if type_ not in ("TYPE_INT", "TYPE_FLOAT"):
                    raise RuntimeError(f"Cannot decrement variable of type '{type_}'")
                new_value = value - 1 if type_ == "TYPE_INT" else value - 1.0
                self.assign(var, (type_, new_value))
                return value  # Restituisce il valore prima del decremento

            case _:
                raise RuntimeError(f"Unknown statement: {node}")

    def eval_expr(self, expr):
        match expr:
            case ("int", val): return int(val)

            case ("float", val): return float(val)

            case ("string", val): return val

            case ("var", name):
                return self.lookup(name)[1]

            case ("concat", expr, next_expr):
                return str(self.eval_expr(expr)) + str(self.eval_expr(next_expr))

            case ('not', inner): return not self.eval_expr(inner)

            case ('minus', inner): return -self.eval_expr(inner)

            case ('bool', value): return value.lower() == 'true'

            case ('binop', op, left, right):
                l = self.eval_expr(left)
                r = self.eval_expr(right)

                # blocco per AND/OR
                if op in ("AND", "OR"):
                    # impedisci l'uso con stringhe
                    if isinstance(l, str) or isinstance(r, str):
                        raise RuntimeError("Cannot apply logical AND/OR to string operands")
                    if op == "AND":
                        return int(bool(l) and bool(r))  # 0 o 1
                    else:  # "OR"
                        return int(bool(l) or bool(r))
                match op:
                    case "PLUS": return l + r
                    case "MINUS": return l - r
                    case "TIMES": return l * r
                    case "DIVIDE": return l / r
                    case "MODULE": return l % r
                    case "AND": return bool(l) and bool(r)
                    case "OR": return bool(l) or bool(r)
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
                ret_val = None

                for stmt in body:
                    result = self.execute(stmt, return_type)
                    if isinstance(result, tuple) and result[0] == "return":
                        ret_val = result[1]
                        break
                self.env_stack.pop() # Rimuove l'ambiente locale dopo l'esecuzione della funzione

                if return_type == "VOID":
                    return None
                if return_type in ("TYPE_INT", "TYPE_FLOAT", "TYPE_STRING") and ret_val is None:
                    raise RuntimeError(
                        f"Function '{name}' declared as {return_type[5:].lower()} but missing return statement")
                return ret_val

            case _:
                raise RuntimeError(f"Invalid expression: {expr}")




if __name__ == "__main__":
    from lexer import lexer
    from parser import parser
    from semantic_analyzer import SemanticAnalyzer

    codice = '''
    // Test bool, operatori logici e confronto
    bool entrambiPositivi(int a, int b) {
        return a > 0 && b > 0;
    }
    
    int main() {
        cout << entrambiPositivi(3, 4) << endl;   // stampa 1
        cout << entrambiPositivi(-1, 2) << endl;  // stampa 0
        return 0;
    }
    '''

    tokens = lexer(codice)
    parser = parser(tokens)
    ast = parser.parse()
    sem_analyzer = SemanticAnalyzer(ast).analyze()

    print("\n--- Interprete Output ---")
    interpreter = Interpreter(ast)

    for stmt in ast:
        if isinstance(stmt, tuple) and stmt[0] in ("function_def", "declare", "assign"):
            interpreter.execute(stmt)

    if "main" not in interpreter.env_stack[0]:
        raise RuntimeError("No main function defined in the code")
    else:
        interpreter.eval_expr(("funcall", "main", []))  # Esegui la funzione main
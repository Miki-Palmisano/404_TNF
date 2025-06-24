class SemanticAnalyzer:
    def __init__(self, ast):
        self.ast = ast
        self.stack_symbol_table = [{}]


    def declare_variable(self, name, type_):
        scope = self.stack_symbol_table[-1]
        if name in scope:
            raise ValueError(f"Variable '{name}' already declared in this scope")
        scope[name] = type_

    def lookup_variable(self, name):
        for scope in reversed(self.stack_symbol_table):
            if name in scope:
                return scope[name]
        raise ValueError(f"Variable '{name}' not declared in any scope")

    def analyze(self):
        for stmt in self.ast:
            self.visit(stmt)

    def visit(self, node): # table è la tabella dei simboli corrente
        match node:
            case ('declare', type_, name, expr): # Verifica la dichiarazione di una variabile
                if expr:
                    expr_type = self.expr_type(expr)
                    if not self.type_compatible(type_, expr_type):
                        raise TypeError(f"Type incompatibility in declaration of '{name}': {type_} vs {expr_type}")
                self.declare_variable(name, type_)

            case ('assign', name, expr): # Verifica l'assegnazione a una variabile
                expr_type = self.expr_type(expr)
                var_type = self.lookup_variable(name)
                if not self.type_compatible(var_type, expr_type):
                    raise TypeError(f"Type incompatibility in assignment to '{name}': {var_type} vs {expr_type}")

            case ('if', condition, body, else_body): # Verifica la condizione di un if e il tipo delle espressioni nei blocchi

                cond_type = self.expr_type(condition)
                if cond_type != 'TYPE_BOOL':
                    raise TypeError(f"If condition must be a boolean, got {cond_type}")
                self.stack_symbol_table.append({})  # Nuova tabella dei simboli per il blocco if
                for stmt in body:
                    self.visit(stmt)
                self.stack_symbol_table.pop()  # Elimina la tabella dei simboli del blocco if
                self.stack_symbol_table.append({})  # Nuova tabella dei simboli per il blocco else
                for stmt in else_body:
                    self.visit(stmt)
                self.stack_symbol_table.pop()  # Elimina la tabella dei simboli del blocco else

            case ('while', condition, body): # Verifica la condizione di un while e il tipo delle espressioni nel corpo

                cond_type = self.expr_type(condition)
                if cond_type != 'TYPE_BOOL':
                    raise TypeError(f"While condition must be a boolean, got {cond_type}")
                self.stack_symbol_table.append({})  # Nuova tabella dei simboli per il blocco while
                for stmt in body:
                    self.visit(stmt)
                self.stack_symbol_table.pop()  # Elimina la tabella dei simboli del blocco while

            case ('cout', expr): # Verifica l'output di cout
                self.expr_type(expr)  # Just ensure the expression can be evaluated

            case ('cin', names):  # ora è una lista
                for n in names:
                    self.lookup_variable(n)

            case ('function_def', return_type, name, params, body): # Verifica la definizione di una funzione

                self.declare_variable(name, ('function', return_type, params))

                self.stack_symbol_table.append({})  # Nuova tabella dei simboli per il corpo della funzione
                for ptype, pname in params:
                    self.declare_variable(pname, ptype)

                prev_return_type = getattr(self, 'current_function_return_type', None)
                self.current_function_return_type = return_type

                for stmt in body:
                    self.visit(stmt)
                self.current_function_return_type = prev_return_type
                self.stack_symbol_table.pop()  # Elimina la tabella dei simboli del corpo della funzione

            case ('funcall', name, args): # Verifica la chiamata a una funzione

                self.expr_type(node)

            case ('return', expr): # Verifica il tipo di ritorno di una funzione
                return_type = getattr(self, 'current_function_return_type', None)
                if return_type == "VOID" and expr is not None:
                    raise TypeError("Cannot return a value from a void function")
                if return_type != "VOID":
                    expr_type = self.expr_type(expr)
                    if not self.type_compatible(return_type, expr_type):
                        raise TypeError(f"Type incompatibility in return: expected {return_type}, got {expr_type}")

            case ('pre_increment', name) | ('pre_decrement', name) \
                    | ('post_increment', name) | ('post_decrement', name): # Verifica l'incremento/decremento di una variabile
                var_type = self.lookup_variable(name)
                if var_type not in ('TYPE_INT', 'TYPE_FLOAT'):
                    raise TypeError(f"Increment/decrement not valid for type '{var_type}'")

            case _:
                raise ValueError(f"Unknown node type: {node}")

    # Questo metodo determina il tipo di un'espressione e verifica la sua correttezza rispetto alla tabella dei simboli.
    def expr_type(self, expr):
        match expr:
            case ('int', _):
                return 'TYPE_INT'

            case ('float', _):
                return 'TYPE_FLOAT'

            case ('string', _):
                return 'TYPE_STRING'

            case ('bool', _):
                return 'TYPE_BOOL'

            case ('var', name): # Verifica se la variabile è dichiarata
                return self.lookup_variable(name)

            case ('minus', inner) | ('not', inner): # Verifica l'operatore unario
                inner_type = self.expr_type(inner)
                if expr[0] == 'minus' and inner_type not in ('TYPE_INT', 'TYPE_FLOAT'):
                    raise TypeError(f"Unary minus not valid for type '{inner_type}'")
                if expr[0] == 'not' and inner_type != 'TYPE_BOOL':
                    raise TypeError(f"Logical NOT not valid for type '{inner_type}'")
                return inner_type

            case ('funcall', name, args): # Verifica la chiamata a una funzione
                entry = self.lookup_variable(name)
                if not isinstance(entry, tuple) or entry[0] != 'function':
                    raise ValueError(f"Function '{name}' not declared or is not a function")

                func_return_type, func_params = entry[1], entry[2]

                if len(func_params) != len(args):
                    raise TypeError(
                        f"Function '{name}' called with incorrect number of arguments: expected {len(func_params)}, got {len(args)}")

                for i, (ptype, _) in enumerate(func_params):
                    arg_type = self.expr_type(args[i])
                    if not self.type_compatible(ptype, arg_type):
                        raise TypeError( f"Type incompatibility in argument {i + 1} of function '{name}': expected {ptype}, got {arg_type}")

                return func_return_type

            case ("binop", op, left, right): # Verifica le operazioni binarie
                ltype = self.expr_type(left)
                rtype = self.expr_type(right)
                if op in ('PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'MODULE'):
                    if ltype == rtype and ltype in ('TYPE_INT', 'TYPE_FLOAT'):
                        return ltype
                    if ltype == 'TYPE_STRING' or rtype == 'TYPE_STRING' and op == 'PLUS':
                        return 'TYPE_STRING'
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
                # dentro expr_type, nel ramo ("binop", op, left, right)
                if op in ('AND', 'OR'):
                    # tipi ammessi
                    allowed = ('TYPE_BOOL', 'TYPE_INT', 'TYPE_FLOAT')
                    if ltype in allowed and rtype in allowed:
                        return 'TYPE_BOOL'  # la semantica è booleana
                    else:
                        raise TypeError( f"Logical operator between unsupported types: {ltype}, {rtype}")

                raise TypeError(f"Unknown operator: {op}")

            case ('concat', left, right): # Verifica la concatenazione di stringhe
                self.expr_type(left)
                self.expr_type(right)
                return 'TYPE_STRING'

            case ('pre_increment', name) | ('pre_decrement', name) \
                 | ('post_increment', name) | ('post_decrement', name): # Verifica l'incremento/decremento prefisso

                var_type = self.lookup_variable(name)
                if var_type not in ('TYPE_INT', 'TYPE_FLOAT'):
                    raise TypeError(f"Increment/decrement not valid for type '{var_type}'")
                return var_type  # Ritorna il tipo della variabile dopo l'incremento/decremento

            case _:
                raise TypeError(f"Expression not recognized: {expr}")

    # Questo metodo verifica se due tipi sono compatibili.
    def type_compatible(self, declared, expr_type):
        return declared == expr_type or \
                (declared == 'TYPE_FLOAT' and expr_type == 'TYPE_INT')


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
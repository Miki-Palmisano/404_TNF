class SemanticAnalyzer:
    def __init__(self, ast):
        self.ast = ast
        self.stack_symbol_table = [{}]          # ➊ pila di scope (0 = globale)
        self.current_function_return_type = None

    #  Helpers per la tabella dei simboli

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

    #  Analisi principale AST

    def analyze(self):
        for stmt in self.ast:
            self.visit(stmt)

    def visit(self, node):
        match node:

            # ── Dichiarazione variabile ────────────────────
            case ('declare', type_, name, expr):
                if type_ == "VOID":                                  # ⓐ blocca variabile VOID
                    raise TypeError(f"Variable '{name}' cannot be declared with type VOID")

                if expr:
                    expr_type = self.expr_type(expr)
                    if not self.type_compatible(type_, expr_type):
                        raise TypeError(f"Type incompatibility in declaration of '{name}': {type_} vs {expr_type}")

                self.declare_variable(name, type_)

            case ('assign', name, expr):
                expr_type = self.expr_type(expr)
                var_type = self.lookup_variable(name)

                if var_type == "VOID":                               # ⓑ assegnare a VOID è vietato
                    raise TypeError(f"Cannot assign to variable '{name}' of type VOID")

                if not self.type_compatible(var_type, expr_type):
                    raise TypeError(f"Type incompatibility in assignment to '{name}': {var_type} vs {expr_type}")

            case ('if', condition, body, else_body):
                cond_type = self.expr_type(condition)
                if cond_type != 'TYPE_BOOL':
                    raise TypeError(f"If condition must be a boolean, got {cond_type}")

                # blocco IF
                self.stack_symbol_table.append({})
                for stmt in body:
                    self.visit(stmt)
                self.stack_symbol_table.pop()

                # blocco ELSE
                self.stack_symbol_table.append({})
                for stmt in else_body:
                    self.visit(stmt)
                self.stack_symbol_table.pop()

            case ('while', condition, body):
                cond_type = self.expr_type(condition)
                if cond_type != 'TYPE_BOOL':
                    raise TypeError(f"While condition must be a boolean, got {cond_type}")

                self.stack_symbol_table.append({})
                for stmt in body:
                    self.visit(stmt)
                self.stack_symbol_table.pop()

            case ('cout', expr):
                self.expr_type(expr)    # basta che sia valutabile

            case ('cin', names):        # names è lista di ID
                for n in names:
                    tipo = self.lookup_variable(n)
                    if tipo == "VOID":                      # ⓒ cin su VOID
                        raise TypeError(f"Cannot read input into variable '{n}' of type VOID")

            case ('function_def', return_type, name, params, body):

                # nome funzione nello scope corrente
                self.declare_variable(name, ('function', return_type, params))

                # controlla parametri duplicati
                param_names = set()
                for _, pname in params:
                    if pname in param_names:
                        raise ValueError(f"Duplicate parameter name '{pname}' in function '{name}'")
                    param_names.add(pname)

                # nuovo scope per i parametri
                self.stack_symbol_table.append({})
                for ptype, pname in params:
                    self.declare_variable(pname, ptype)

                prev_ret = self.current_function_return_type
                self.current_function_return_type = return_type

                # visita corpo funzione
                for stmt in body:
                    self.visit(stmt)

                self.current_function_return_type = prev_ret
                self.stack_symbol_table.pop()

                # return mancante per funzioni non-void
                if return_type != "VOID":
                    if not any(self.contains_return(stmt) for stmt in body):
                        raise TypeError(f"Function '{name}' declared as {return_type[5:].lower()} but has no return statement")

            # Chiamata funzione (fuori dalle espressioni)
            case ('funcall', _name, _args):
                self.expr_type(node)

            # Return
            case ('return', expr):
                rt = self.current_function_return_type
                if rt == "VOID" and expr is not None:
                    raise TypeError("Cannot return a value from a void function")
                if rt != "VOID":
                    expr_t = self.expr_type(expr)
                    if not self.type_compatible(rt, expr_t):
                        raise TypeError(f"Type incompatibility in return: expected {rt}, got {expr_t}")

            # ++ / --
            case ('pre_increment', name) | ('pre_decrement', name) \
               | ('post_increment', name) | ('post_decrement', name):
                var_type = self.lookup_variable(name)
                if var_type not in ('TYPE_INT', 'TYPE_FLOAT'):
                    raise TypeError(f"Increment/decrement not valid for type '{var_type}'")

            # Default
            case _:
                raise ValueError(f"Unknown node type: {node}")

    #  Analisi espressioni

    def expr_type(self, expr):
        match expr:

            case ('int', _):    return 'TYPE_INT'
            case ('float', _):  return 'TYPE_FLOAT'
            case ('string', _): return 'TYPE_STRING'
            case ('bool', _):   return 'TYPE_BOOL'

            case ('var', name):
                return self.lookup_variable(name)

            case ('minus', inner) | ('not', inner):
                inner_t = self.expr_type(inner)
                if expr[0] == 'minus' and inner_t not in ('TYPE_INT', 'TYPE_FLOAT'):
                    raise TypeError(f"Unary minus not valid for type '{inner_t}'")
                if expr[0] == 'not' and inner_t != 'TYPE_BOOL':
                    raise TypeError(f"Logical NOT not valid for type '{inner_t}'")
                return inner_t

            # ── Chiamata funzione dentro espr. ─
            case ('funcall', name, args):
                entry = self.lookup_variable(name)
                if not (isinstance(entry, tuple) and entry[0] == 'function'):
                    raise ValueError(f"Function '{name}' not declared or is not a function")

                func_return_type, func_params = entry[1], entry[2]
                if len(func_params) != len(args):
                    raise TypeError(f"Function '{name}' called with incorrect number of arguments: "
                                    f"expected {len(func_params)}, got {len(args)}")

                for i, (ptype, _) in enumerate(func_params):
                    arg_t = self.expr_type(args[i])
                    if not self.type_compatible(ptype, arg_t):
                        raise TypeError(f"Type incompatibility in argument {i+1} of function '{name}': "
                                        f"expected {ptype}, got {arg_t}")
                return func_return_type

            # Binop
            case ('binop', op, left, right):
                l = self.expr_type(left)
                r = self.expr_type(right)

                if op in ('PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'MODULE'):
                    if l == r and l in ('TYPE_INT', 'TYPE_FLOAT'):
                        return l
                    if (l == 'TYPE_INT' and r == 'TYPE_FLOAT') or (l == 'TYPE_FLOAT' and r == 'TYPE_INT'):
                        return 'TYPE_FLOAT'
                    if op == 'PLUS' and ('TYPE_STRING' in (l, r)):
                        return 'TYPE_STRING'
                    raise TypeError(f"Arithmetic operation of incompatible type: {l}, {r}")

                if op in ('EQ', 'NEQ', 'LT', 'GT', 'LE', 'GE'):
                    if l == r:
                        return 'TYPE_BOOL'
                    raise TypeError(f"Incompatible types for comparison: {l}, {r}")

                if op in ('AND', 'OR'):
                    allowed = ('TYPE_BOOL', 'TYPE_INT', 'TYPE_FLOAT')
                    if l in allowed and r in allowed:
                        return 'TYPE_BOOL'
                    raise TypeError(f"Logical operator between unsupported types: {l}, {r}")

                raise TypeError(f"Unknown operator: {op}")

            # Concatenazione stringhe
            case ('concat', left, right):
                lt = self.expr_type(left)
                rt = self.expr_type(right)
                if lt != 'TYPE_STRING' and rt != 'TYPE_STRING':
                    raise TypeError(f"Concatenation requires at least one string, got {lt}, {rt}")
                return 'TYPE_STRING'

            # ++/-- in espressione
            case ('pre_increment', name) | ('pre_decrement', name) \
                 | ('post_increment', name) | ('post_decrement', name):
                var_type = self.lookup_variable(name)
                if var_type not in ('TYPE_INT', 'TYPE_FLOAT'):
                    raise TypeError(f"Increment/decrement not valid for type '{var_type}'")
                return var_type

            case _:
                raise TypeError(f"Expression not recognized: {expr}")


    #  Compatibilità di tipo (int-to-float permessa)

    def type_compatible(self, declared, expr_type):
        return declared == expr_type or \
               (declared == 'TYPE_FLOAT' and expr_type == 'TYPE_INT')


    #  Helper per verificare presenza di return

    def contains_return(self, stmt):
        if isinstance(stmt, tuple) and stmt[0] == 'return':
            return True
        if isinstance(stmt, tuple) and stmt[0] == 'if':
            return any(self.contains_return(s) for s in stmt[2]) or \
                   any(self.contains_return(s) for s in stmt[3])
        if isinstance(stmt, tuple) and stmt[0] == 'while':
            return any(self.contains_return(s) for s in stmt[2])
        return False

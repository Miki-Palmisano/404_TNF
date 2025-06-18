from lexer import lexer

class parser():
    def __init__(self, tokens):
        self.tokens = tokens
        self.current = 0

    # Avanza al prossimo token, se disponibile e lo restituisce
    def peek(self):
        if self.current < len(self.tokens):
            return self.tokens[self.current]
        return None

    # Si aspetta che il prossimo token sia di un certo tipo
    def advance(self):
        tok = self.peek()
        if tok:
            self.current += 1
        return tok

    # Si aspetta un token di un certo tipo, altrimenti lancia un errore
    def expect(self, type_):
        tok = self.advance()
        if tok is None or tok[0] != type_:
            raise self.error(f"Expected {type_}, got {tok}", tok)
        return tok

    # Analizza un singolo statement in base al tipo del prossimo token
    def parse(self):
        # Funzione principale che processa tutti gli statement fino alla fine del codice
        statements = []
        while self.peek() is not None:
            stmt = self.statement()
            if stmt:
                statements.append(stmt)
        return statements

    # Gestisce gli statement in base al tipo del prossimo token
    def statement(self):
        tok = self.peek()

        if tok is None:
            return None
        elif tok[0] in ("TYPE_INT", "TYPE_FLOAT", "TYPE_STRING"):
            return self.declaration()
        elif tok[0] == "ID":
            return self.assignment_or_funcall()
        elif tok[0] == "IF":
            return self.if_statement()
        elif tok[0] == "COUT":
            return self.cout_statement()
        elif tok[0] == "CIN":
            return self.cin_statement()
        else:
            self.error(f"Unexpected token {tok}", tok)

    # Gestisce le assegnazioni o le chiamate di funzione
    def factor(self):
        # Gestisce i fattori, che possono essere numeri, variabili o espressioni tra parentesi
        tok = self.peek()

        if tok is None:
            self.error("Unexpected end of input", tok)
        elif tok[0] == "ID":
            self.advance()
            return ("var", tok[1])
        elif tok[0] in ("INT", "FLOAT", "STRING"):
            self.advance()
            return (tok[0].lower(), tok[1])
        elif tok[0] == "LPAREN":
            self.advance()
            expr = self.comparison()
            self.expect("RPAREN")
            return expr
        elif tok[0] == "NOT":
            self.advance()
            expr = self.factor()
            return ("not", expr)
        else:
            self.error(f"Unexpected token {tok}", tok)

    # Gestisce le espressioni aritmetiche, es: 5 + 3 * 2
    def term(self):
        left = self.factor()
        while self.peek() and self.peek()[0] in ("TIMES", "DIVIDE"):
            op = self.advance()[0]
            right = self.factor()
            left = (op, left, right)
        return left

    # Gestisce le espressioni additive, es: x + 5 - 3
    def additive(self):
        left = self.term()
        while self.peek() and self.peek()[0] in ("PLUS", "MINUS"):
            op = self.advance()[0]
            right = self.term()
            left = (op, left, right)
        return left

    # Gestisce le espressioni di confronto, es: x == 5, x < 10
    def comparison(self):
        left = self.additive()
        while self.peek() and self.peek()[0] in ("LT", "GT", "EQ", "LE", "GE"):
            op = self.advance()[0]
            right = self.additive()
            left = (op, left, right)
        return left

    # Gestisce dichiarazione variabili, es: int x = 5;
    def declaration(self):
        type_ = self.advance()[0]
        name = self.expect("ID")[1]
        expr = None
        tok = self.peek()

        if tok and tok[0] == "ASSIGN":
            self.advance()
            expr = self.comparison()

            if expr[0] == "float" and type_ == "INT":
                self.error(f"Cannot assign Float number to Int variable", tok)
            elif expr[0] == "int" and type_ == "FLOAT":
                expr = ("float", f"{expr[1]}.0")
        self.expect("SEMICOLON")
        return ("declare", type_, name, expr)

    def if_statement(self):
        self.expect("IF")
        self.expect("LPAREN")
        condition = self.comparison()
        self.expect("RPAREN")
        self.expect("LBRACE")

        body = []
        while self.peek() and self.peek()[0] != "RBRACE":
            stmt = self.statement()
            if stmt:
                body.append(stmt)

        self.expect("RBRACE")
        else_body = []
        if self.peek() and self.peek()[0] == "ELSE":
            self.advance()
            if self.peek() and self.peek()[0] == "IF":
                else_body.append(self.if_statement())
            else:
                self.expect("LBRACE")
                while self.peek() and self.peek()[0] != "RBRACE":
                    stmt = self.statement()
                    if stmt:
                        else_body.append(stmt)
                self.expect("RBRACE")
        return ("if", condition, body, else_body)

    def assignment_or_funcall(self):
        name = self.expect("ID")[1]
        tok = self.peek()

        if tok and tok[0] == "ASSIGN":
            self.advance()
            expr = self.comparison()
            self.expect("SEMICOLON")
            return ("assign", name, expr)
        else:
            self.error("Invalid statement after identifier", tok)

    def cout_statement(self):
        self.expect("COUT")
        self.expect("LSHIFT")
        expr = self.comparison()
        if self.peek() and self.peek()[0] == "STRING":
            expr = ("string", expr[1])
        while self.peek() and self.peek()[0] == "LSHIFT":
            self.advance()
            next_expr = self.comparison()
            if next_expr[0] == "STRING":
                next_expr = ("string", next_expr[1])
            expr = ("concat", expr, next_expr)
        if self.peek() and self.peek()[0] == "SEMICOLON":
            self.advance()
        else:
            self.error("Expected SEMICOLON after cout statement", self.peek())
        return ("cout", expr)

    def cin_statement(self):
        self.expect("CIN")
        self.expect("RSHIFT")
        var = self.expect("ID")[1]
        if self.peek() and self.peek()[0] == "SEMICOLON":
            self.advance()
        else:
            self.error("Expected SEMICOLON after cin statement", self.peek())
        return ("cin", var)

    # Gestisce errori di sintassi, indicando la linea in cui si è verificato
    def error(self, message, token):
        line = token[2] if token else "unknown"
        raise SyntaxError(f"{message} at line {line}")



if __name__ == "__main__":
    code = '''
    int a = 5;
    float b = 3.2;
    if (a > b) {
        cout << "A maggiore di b";
    } else if (a <= 5) {
        cout << "A minore o uguale a b";
        cout << "CIAO MONDO";
    } else {
        cout << "Vita Rovinata";
    }
    cin >> a;
    '''

    tokens = lexer(code)
    parser_instance = parser(tokens)
    ast = parser_instance.parse()

    from pprint import pprint
    pprint(ast)
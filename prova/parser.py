from lexer import lexer
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens  # Lista di token prodotti dal lexer
        self.pos = 0  # Posizione corrente nella lista dei token

    def peek(self):
        # Guarda il prossimo token senza consumarlo (non avanza la posizione)
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None  # Nessun token se siamo oltre la fine

    def advance(self):
        # Prende e restituisce il prossimo token, avanzando la posizione
        tok = self.peek()
        self.pos += 1
        return tok

    def expect(self, type_):
        # Si aspetta che il prossimo token sia di un certo tipo,
        # altrimenti lancia un errore di sintassi
        tok = self.advance()
        if tok is None or tok[0] != type_:
            raise self.error(f"Expected {type_}, got {tok}", tok)
        return tok

    def parse(self):
        # Funzione principale: processa tutti gli statement finché non finisce il codice
        statements = []
        while self.peek() is not None:
            stmt = self.statement()
            if stmt: statements.append(stmt)
        return statements

    # ---- STATEMENTS ----
    def statement(self):
        # Analizza quale tipo di istruzione stiamo per processare in base al prossimo token
        tok = self.peek()
        if tok is None:
            return None
        if tok[0] in ("INT", "FLOAT", "STRING"):
            return self.declaration()  # Dichiarazione variabile
        elif tok[0] == "ID":
            return self.assignment_or_funcall()  # Assegnazione o chiamata funzione
        elif tok[0] == "IF":
            return self.if_statement()  # Istruzione if
        elif tok[0] == "WHILE":
            return self.while_statement()  # Istruzione while
        elif tok[0] == "COUT":
            return self.cout_statement()  # Stampa
        elif tok[0] == "CIN":
            return self.cin_statement()  # Input
        else:
            self.error(f"Unexpected token {tok}", tok)  # Token non atteso

    def declaration(self):
        # Gestisce dichiarazione variabili, es: int x = 5;
        type_ = self.advance()[0]  # Prende il tipo (INT/FLOAT/STRING)
        name = self.expect("ID")[1]  # Prende il nome della variabile
        expr = None  # Espressione di inizializzazione (opzionale)
        tok = self.peek()
        if tok and tok[0] == "ASSIGN":
            self.advance()  # Consuma il segno "="
            expr = self.expression()  # Parso l'espressione a destra

            if expr[0] == "float" and type_ == "INT":
                self.error(f"Cannot assign Float number to Int variable", tok)
            elif expr[0] == "int" and type_ == "FLOAT":
                expr = ("float", f"{expr[1]}.0")

        self.expect("SEMICOLON")  # Consuma il ";"
        return ("declare", type_, name, expr)  # Nodo AST della dichiarazione

    def assignment_or_funcall(self):
        # Gestisce assegnazione (es: x = 5;) o chiamata funzione (es: foo(3);)
        name = self.advance()[1]  # Prende il nome (ID)
        tok = self.peek()
        if tok and tok[0] == "ASSIGN":
            self.advance()  # Consuma "="
            expr = self.expression()  # Valuta la parte destra dell'assegnazione
            self.expect("SEMICOLON")  # Consuma ";"
            return ("assign", name, expr)
        elif self.peek() and self.peek()[0] == "LPAREN":
            self.advance()  # Consuma "("
            args = []
            while self.peek() and self.peek()[0] != "RPAREN":
                args.append(self.expression())  # Ogni argomento
                if self.peek() and self.peek()[0] == "COMMA":
                    self.advance()  # Consuma ","
            self.expect("RPAREN")  # Consuma ")"
            self.expect("SEMICOLON")  # Consuma ";"
            return ("funcall", name, args)
        else:
            self.error("Invalid statement after identifier", tok)

    def if_statement(self):
        # Gestisce istruzione if...else...
        self.expect("IF")  # Consuma "if"
        self.expect("LPAREN")  # Consuma "("
        cond = self.expression()  # Condizione dell'if
        self.expect("RPAREN")  # Consuma ")"
        self.expect("LBRACE")  # Consuma "{"
        body = []
        while self.peek() and self.peek()[0] != "RBRACE":
            body.append(self.statement())  # Corpo del blocco if
        self.expect("RBRACE")  # Consuma "}"
        else_body = []
        if self.peek() and self.peek()[0] == "ELSE":
            self.advance()  # Consuma "else"
            self.expect("LBRACE")  # Consuma "{"
            while self.peek() and self.peek()[0] != "RBRACE":
                else_body.append(self.statement())  # Corpo del blocco else
            self.expect("RBRACE")  # Consuma "}"
        return ("if", cond, body, else_body)

    def while_statement(self):
        # Gestisce istruzione while
        self.expect("WHILE")
        self.expect("LPAREN")
        cond = self.expression()  # Condizione del ciclo
        self.expect("RPAREN")
        self.expect("LBRACE")
        body = []
        while self.peek() and self.peek()[0] != "RBRACE":
            body.append(self.statement())  # Corpo del ciclo
        self.expect("RBRACE")
        return ("while", cond, body)

    def comparison(self):
        left = self.additive()
        while self.peek() and self.peek()[0] in ("LT", "GT", "EQ", "LE", "GE"):
            op = self.advance()[0]
            right = self.additive()
            left = ("binop", op, left, right)
        return left

    def cout_statement(self):
        # Gestisce istruzione cout (stampa)
        self.expect("COUT")
        self.expect("LSHIFT")
        expr = self.expression()  # Cosa stampare
        self.expect("SEMICOLON")
        return ("cout", expr)

    def cin_statement(self):
        # Gestisce istruzione cin (input)
        self.expect("CIN")
        self.expect("RSHIFT")
        var = self.expect("ID")[1]  # Variabile in cui salvare input
        self.expect("SEMICOLON")
        return ("cin", var)

    # ---- EXPRESSIONS ----
    def additive(self):
        left = self.term()
        while self.peek() and self.peek()[0] in ("PLUS", "MINUS"):
            op = self.advance()[0]
            right = self.term()
            left = ("binop", op, left, right)
        return left

    def expression(self):
        return self.comparison()

    def term(self):
        # Gestisce espressioni con * e / (precedenza più alta)
        left = self.factor()
        while self.peek() and self.peek()[0] in ("TIMES", "DIVIDE"):
            op = self.advance()[0]
            right = self.factor()
            left = ("binop", op, left, right)
        return left

    def factor(self):
        # Gestisce numeri, stringhe, variabili, e parentesi
        tok = self.peek()
        if tok[0] == "INT":
            return ("int", self.advance()[1])
        elif tok[0] == "FLOAT":
            return ("float", self.advance()[1])
        elif tok[0] == "STRING":
            return ("string", self.advance()[1])
        elif tok[0] == "ID":
            return ("var", self.advance()[1])
        elif tok[0] == "LPAREN":
            self.advance()
            expr = self.expression()
            self.expect("RPAREN")
            return expr
        else:
            self.error("Invalid factor")  # Espressione non valida

    def error(self, msg, tok):
        line = tok[2] if tok else '?'
        raise SyntaxError(f"Error in line {tok}: {msg}")  # Stampa un errore di sintassi


# === ESEMPIO USO ===
if __name__ == "__main__":
    # Esempio di codice C++ da analizzare
    codice = ''' 
    
    a = 5;
    float b = 3;
    if (a > b) {
        cout << "a maggiore";
    } 
    '''
    tokens = lexer(codice)  # Analizza il codice in token
    parser = Parser(tokens)  # Istanzia il parser
    ast = parser.parse()  # Parsing, ottieni AST
    from pprint import pprint

    pprint(ast)  # Stampa l'albero sintattico astratto

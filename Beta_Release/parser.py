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
        tok = self.peek()
        if tok is None:
            return None

        # FUNZIONE: tipo + id + ( ==> function_definition!
        if tok[0] in ("TYPE_INT", "TYPE_FLOAT", "TYPE_STRING", "TYPE_BOOL", "VOID") \
                and self.pos + 1 < len(self.tokens) and self.tokens[self.pos + 1][0] == "ID" \
                and self.pos + 2 < len(self.tokens) and self.tokens[self.pos + 2][0] == "LPAREN":
            return self.function_definition()

        # VARIABILE
        if tok[0] in ("TYPE_INT", "TYPE_FLOAT", "TYPE_STRING","TYPE_BOOL"):
            return self.declaration()

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
        elif tok[0] == "RETURN":
            return self.return_statement()
        else:
            self.error(f"Unexpected token {tok}", tok)  # Token non atteso

    def return_statement(self):
        self.expect("RETURN")
        expr = self.logic()
        self.expect("SEMICOLON")
        return ("return", expr)

    def declaration(self):
        # Gestisce dichiarazione variabili, es: int x = 5;
        type_ = self.advance()[0]  # Prende il tipo (INT/FLOAT/STRING)
        name = self.expect("ID")[1]  # Prende il nome della variabile
        expr = None  # Espressione di inizializzazione (opzionale)
        tok = self.peek()

        if tok and tok[0] == "ASSIGN":
            self.advance()  # Consuma il segno "="
            expr = self.logic()  # Parso l'espressione a destra

        self.expect("SEMICOLON")  # Consuma il ";"
        return ("declare", type_, name, expr)  # Nodo AST della dichiarazione

    def assignment_or_funcall(self):
        # Gestisce assegnazione (es: x = 5;) o chiamata funzione (es: foo(3);)
        name = self.advance()[1]  # Prende il nome (ID)
        tok = self.peek()
        if tok and tok[0] == "ASSIGN":
            self.advance()  # Consuma "="
            expr = self.logic()  # Valuta la parte destra dell'assegnazione
            self.expect("SEMICOLON")  # Consuma ";"
            return ("assign", name, expr)

        elif self.peek() and self.peek()[0] == "LPAREN":
            self.advance()  # Consuma "("
            args = []
            while self.peek() and self.peek()[0] != "RPAREN":
                args.append(self.logic())  # Ogni argomento
                if self.peek() and self.peek()[0] == "COMMA":
                    self.advance()  # Consuma ","
            self.expect("RPAREN")  # Consuma ")"
            self.expect("SEMICOLON")  # Consuma ";"
            return ("funcall", name, args)

        elif tok and tok[0] == "INCREMENT":
            self.advance()
            if self.peek() and self.peek()[0] == "SEMICOLON":
                self.advance()
                return ("post_increment", name)
            else:
                return ("pre_increment", name)

        elif tok and tok[0] == "DECREMENT":
            self.advance()
            if self.peek() and self.peek()[0] == "SEMICOLON":
                self.advance()
                return ("post_decrement", name)
            else:
                return ("pre_decrement", name)
        else:
            self.error("Invalid statement after identifier", tok)

    def if_statement(self):
        # Gestisce istruzione if...else...
        self.expect("IF")  # Consuma "if"
        self.expect("LPAREN")  # Consuma "("
        cond = self.logic()  # Condizione dell'if
        self.expect("RPAREN")  # Consuma ")"
        self.expect("LBRACE")  # Consuma "{"

        body = []
        while self.peek() and self.peek()[0] != "RBRACE":
            body.append(self.statement())  # Corpo del blocco if
        self.expect("RBRACE")  # Consuma "}"

        else_body = []
        if self.peek() and self.peek()[0] == "ELSE":
            self.advance()  # Consuma "else"
            if self.peek() and self.peek()[0] == "IF":
                else_body.append(self.if_statement())
            else:
                self.expect("LBRACE")
                while self.peek() and self.peek()[0] != "RBRACE":
                    stmt = self.statement()
                    if stmt:
                        else_body.append(stmt)
                self.expect("RBRACE")
        return ("if", cond, body, else_body)

    def while_statement(self):
        # Gestisce istruzione while
        self.expect("WHILE")
        self.expect("LPAREN")
        cond = self.logic()  # Condizione del ciclo
        self.expect("RPAREN")
        self.expect("LBRACE")

        body = []
        while self.peek() and self.peek()[0] != "RBRACE":
            body.append(self.statement())  # Corpo del ciclo
        self.expect("RBRACE")
        return ("while", cond, body)

    def comparison(self):
        left = self.additive()
        while self.peek() and self.peek()[0] in ("LT", "GT", "EQ", "LE", "GE", "NEQ"):
            op = self.advance()[0]
            right = self.additive()
            left = ("binop", op, left, right)
        return left

    def cout_statement(self):
        # Gestisce istruzione cout (stampa)
        self.expect("COUT")
        self.expect("LSHIFT")
        expr = self.logic()  # Cosa stampare

        while self.peek() and self.peek()[0] == "LSHIFT":
            self.advance() # Consuma "<<"
            if self.peek()[0] == "ENDL":
                self.advance() # Consuma "endl"
                expr = ("concat", expr, ("string", "\n"))  # Aggiunge endl
            else:
                next_expr = self.logic()
                expr = ("concat", expr, next_expr)  # Concatenazione delle espressioni

        if self.peek() and self.peek()[0] == "SEMICOLON":
            self.advance()
        else:
            self.error("Expected semicolon after cout statement", self.peek())
        return ("cout", expr)

    def cin_statement(self):
        # cin >> x >> y >> z ;
        self.expect("CIN")

        vars_ = []
        while True:
            self.expect("RSHIFT")
            var = self.expect("ID")[1]
            vars_.append(var)

            # fine istruzione
            if self.peek() and self.peek()[0] == "SEMICOLON":
                self.advance()  # consuma il ';'
                break

            # se non c’è un altro “>>” -> errore di sintassi
            if not self.peek() or self.peek()[0] != "RSHIFT":
                self.error("Expected '>>' or ';' in cin statement", self.peek())

        return ("cin", vars_)  # ⬅ ritorna lista di nomi

    # ---- EXPRESSIONS ----
    def additive(self):
        left = self.term()
        while self.peek() and self.peek()[0] in ("PLUS", "MINUS"):
            op = self.advance()[0]
            right = self.term()
            left = ("binop", op, left, right)
        return left

    def logic(self):
        return self.or_expr()

    def or_expr(self):
        left = self.and_expr()
        while self.peek() and self.peek()[0] == "OR":
            self.advance()
            right = self.and_expr()
            left = ("binop", "OR", left, right)
        return left

    def and_expr(self):
        left = self.comparison()
        while self.peek() and self.peek()[0] == "AND":
            self.advance()
            right = self.comparison()
            left = ("binop", "AND", left, right)
        return left

    def term(self):
        # Gestisce espressioni con * e / (precedenza più alta)
        left = self.factor()
        while self.peek() and self.peek()[0] in ("TIMES", "DIVIDE", "MODULE"):
            op = self.advance()[0]
            right = self.factor()
            left = ("binop", op, left, right)
        return left

    def factor(self):
        tok = self.peek()
        if tok is None:
            self.error("Unexpected end of input", tok)

        elif tok[0] == "NOT": # Gestisce l'operatore logico NOT
            self.advance()
            expr = self.factor()
            return ("not", expr)

        elif tok[0] in ("INT", "FLOAT", "STRING"): # Gestisce i letterali
            return (tok[0].lower(), self.advance()[1])

        elif tok[0] == "BOOL":
            return ("bool", self.advance()[1])

        elif tok[0] == "INCREMENT": # Gestisce l'incremento prefisso
            self.advance()
            var_tok = self.expect("ID")
            return ("pre_increment", var_tok[1])

        elif tok[0] == "DECREMENT": # Gestisce il decremento prefisso
            self.advance()
            var_tok = self.expect("ID")
            return ("pre_decrement", var_tok[1])

        elif tok[0] == "ID": # Gestisce variabili e chiamate di funzione
            name = self.advance()[1]
            # Controlla se è un incremento o decremento postfisso
            if self.peek() and self.peek()[0] == "INCREMENT":
                self.advance()
                return ("post_increment", name)
            elif self.peek() and self.peek()[0] == "DECREMENT":
                self.advance()
                return ("post_decrement", name)
            # Funzione o variabile
            if self.peek() and self.peek()[0] == "LPAREN":
                self.advance()  # Consuma '('
                args = []
                while self.peek() and self.peek()[0] != "RPAREN":
                    args.append(self.logic())
                    if self.peek() and self.peek()[0] == "COMMA":
                        self.advance()  # Consuma ','
                self.expect("RPAREN")
                return ("funcall", name, args)
            else:
                return ("var", name)

        elif tok[0] == "MINUS":
            self.advance()
            expr = self.factor()
            return ("minus", expr)

        elif tok[0] == "LPAREN": # Gestisce le espressioni tra parentesi
            self.advance()
            expr = self.logic()
            self.expect("RPAREN")
            return expr
        else:
            self.error(f"Unexpected token {tok}", tok)


    def function_definition(self):
        return_type = self.advance()[0]  # tipo di ritorno (INT, FLOAT, STRING)
        name = self.expect("ID")[1]  # nome della funzione
        self.expect("LPAREN")  # (
        params = []
        while self.peek() and self.peek()[0] != "RPAREN":
            ptype = self.advance()[0]  # tipo parametro
            pname = self.expect("ID")[1]  # nome parametro
            params.append((ptype, pname))
            if self.peek() and self.peek()[0] == "COMMA":
                self.advance()  # ,
        self.expect("RPAREN")  # )
        self.expect("LBRACE")  # {
        body = []
        while self.peek() and self.peek()[0] != "RBRACE":
            body.append(self.statement())
        self.expect("RBRACE")  # }
        return ("function_def", return_type, name, params, body)

    def error(self, msg, tok):
        line = tok[2] if tok else '?'
        raise SyntaxError(f"Error in line {line}: {msg}")  # Stampa un errore di sintassi


# === ESEMPIO USO ===
if __name__ == "__main__":
    # Esempio di codice C++ da analizzare
    codice = '''
    bool bothPositive(int a, int b) {
    return (a > 0 && b > 0);  // ← qui c'è l'uso corretto di &&
}

int main() {
    std::cout << bothPositive(3, 4) << std::endl;  // stampa 1
    return 0;
}
    '''
    tokens = lexer(codice)  # Analizza il codice in token
    parser = Parser(tokens)  # Istanzia il parser
    ast = parser.parse()  # Parsing, ottieni AST
    from pprint import pprint

    pprint(ast)  # Stampa l'albero sintattico astratto

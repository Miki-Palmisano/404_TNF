import re

# Token specification (regex pattern, token name)
'''
Cosa fa:
Qui elenchi tutti i tipi di token che il lexer deve riconoscere, ciascuno associato a una regex.
L’ordine è importante: i token con pattern più lunghi (come == o &&) vanno prima di quelli più corti (come = o &).
'''

TOKEN_SPECIFICATION = [
    ('FLOAT',       r'\d+\.\d+'),        # float number -> \d+\.\d+ una o più cifre seguite da un punto e da 1 o più cifre
    ('INT',         r'\d+'),             # int number -> \d+ una o più cifre
    ('STRING',      r'"[^"\n]*"'),       # Stringa delimitata da due virgolette -> [^"\n] che non siano virgolette o a capo, * che sia 0 o più, " " che siano delimitate da virgolette
    ('BOOL',        r'\b(true|false)\b'),# Boolean -> true o false, \b indica che deve essere una parola intera (non parte di un'altra parola)
    ('ID',          r'[a-zA-Z_]\w*'),    # Identificatore -> qualsiasi sequenza di caratteri che cominci con una lettera (maiuscola o minuscola) o con il carattere _, \w* seguito anche da lettere o numeri
    ('LSHIFT',      r'<<'),              # << indirizzamento
    ('RSHIFT',      r'>>'),              # >> indirizzamento
    ('NEQ',         r'!='),              # Not equal -> diverso
    ('EQ',          r'=='),              # Equal
    ('ASSIGN',      r'='),               # Assegnazione
    ('AND',         r'&&'),              # And
    ('OR',          r'\|\|'),            # Or
    ('NOT',         r'!'),               # Not
    ('COMMENT',     r'//.*'),            # Commento su una riga -> // seguito da qualsiasi carattere fino alla fine della riga
    ('INCREMENT',   r'\+\+'),            # Incremento -> ++
    ('DECREMENT',   r'--'),              # Decremento -> --
    ('PLUS',        r'\+'),              # +
    ('MINUS',       r'-'),               # -
    ('TIMES',       r'\*'),              # *
    ('DIVIDE',      r'/'),               # /
    ('MODULE',      r'%'),               # %
    ('LE',          r'<='),              # minore o uguale
    ('GE',          r'>='),              # maggiore o uguale
    ('LT',          r'<'),               # minore
    ('GT',          r'>'),               # maggiore
    ('LPAREN',      r'\('),              # ( parentesi aperta
    ('RPAREN',      r'\)'),              # ) parentesi chiusa
    ('LBRACE',      r'\{'),              # { parentesi aperta
    ('RBRACE',      r'\}'),              # } parentesi chiusa
    ('SEMICOLON',   r';'),               # ;
    ('COMMA',       r','),               # ,
    ('SKIP',        r'[ \t]+'),          # Ignora gli spazi e le tabulazioni, non significative in C++
    ('NEWLINE',     r'\n'),              # Nuova linea
    ('MISMATCH',    r'.'),               # qualsiasi altro carattere
]


'''Cosa fa:
Elenca le parole chiave C++ che il lexer dovrà distinguere dagli identificatori normali (variabili, funzioni).
'''
# Reserved keywords (C++ subset)
KEYWORDS = {
    'if', 'else', 'while', 'for', 'return', 'int', 'float', 'string', 'cin', 'cout', 'main','void', 'bool', 'endl'
}

'''Cosa fa:
Costruisce un’unica grande regex, che unisce tutte le regex dei token, assegnando a ciascuna un nome (usando la sintassi (?P<NOME>PATTERN)).
get_token è una funzione che cerca il primo token nella stringa in una data posizione.
'''
# Compile regex
token_parts = []  # Crea una lista vuota che conterrà le parti di regex, una per ogni tipo di token

for pair in TOKEN_SPECIFICATION:  # Per ogni coppia (nome_token, regex) nella lista delle specifiche
    part = '(?P<%s>%s)' % pair    # Crea una stringa regex con un "named group":
                                  # - %s viene sostituito dal nome del token (es: 'ID', 'NUMBER', ...)
                                  # - %s viene sostituito dalla regex che trova quel token
                                  # Esempio: ('ID', r'[a-zA-Z_]\w*') diventa '(?P<ID>[a-zA-Z_]\w*)'
    token_parts.append(part)      # Aggiungi questa stringa alla lista

token_regex = '|'.join(token_parts)  # Unisci tutte le parti in una sola grande regex,
                                     # separandole con il simbolo | (che in regex vuol dire "oppure")
                                     # Esempio: '(?P<ID>[a-zA-Z_]\w*)|(?P<NUMBER>\d+)|(?P<PLUS>\+)'

get_token = re.compile(token_regex).match  # Compila la regex in un oggetto "regex"
                                           # .match è un metodo che, dato un testo e una posizione,
                                           # cerca se almeno una di queste regex combacia con l'inizio del testo


def lexer(code):
    line_num = 1            # tiene traccia del numero di riga (utile per errori).
    tokens = []             # è la lista dove salverai i token trovati.
    tok = get_token(code)    # cerca il prossimo token a partire dalla posizione pos.
    while tok is not None:   # Entra in un ciclo che continua finché trova token (mo è il match object).
        typ = tok.lastgroup
        val = tok.group(typ)
        if typ == 'NEWLINE':        # se trova un token NEWLINE (\n), aumenta il contatore delle righe.
            line_num += 1
        elif typ == 'SKIP' or typ == 'COMMENT':         # se trova spazi o tab (SKIP), li ignora.
            pass
        elif typ == 'MISMATCH':
            raise RuntimeError(f'Unexpected character {val!r} on line {line_num}') # se trova caratteri non previsti, lancia un errore (ti dice dove c’è il problema).
        else:
            if typ == 'ID' and val in KEYWORDS:
                if val in ('int', 'float', 'string', 'bool'):
                    typ = "TYPE_"+val.upper()
                elif val in ('true', 'false'):
                    typ = "BOOL"
                else:
                    typ = val.upper()
            elif typ == 'STRING':
                val = val[1:-1]

            tokens.append((typ, val, line_num))   # aggiunge (tipo, valore) alla lista dei token trovati.
        pos = tok.end()                  # restituisce l’indice (posizione) dopo l’ultimo carattere del token trovato.
        tok = get_token(code, pos)       # Rilancia la ricerca del prossimo token a partire dalla posizione pos, cioè subito dopo il token precedente.
    return tokens


if __name__ == "__main__":
    # Esempio di codice C++ da analizzare
    codice = '''
    int a = 5;
    float b = 3;
    bool c = true;
    if (!a >= b) {
        cout << "a maggiore";
    }
    '''
    for token in lexer(codice):
        print(token)
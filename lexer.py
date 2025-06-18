import re

TOKEN = [
    ('STRING',          r'"[^"\n]*"'),
    ('FLOAT',           r'\d+\.\d+'),
    ('INT',             r'\d+'),
    ('ID',              r'[a-zA-Z_]\w*'),
    ('LSHIFT',          r'<<'),
    ('RSHIFT',          r'>>'),
    ('EQ',              r'=='),
    ('ASSIGN',          r'='),
    ('NEQ',             r'!='),
    ('NOT',             r'!'),
    ('GE',              r'>='),
    ('LE',              r'<='),
    ('LT',              r'<'),
    ('GT',              r'>'),
    ('AND',             r'\&\&'),
    ('OR',              r'\|\|'),
    ('PLUS',            r'\+'),
    ('MINUS',           r'-'),
    ('DIVIDE',          r'/'),
    ('TIMES',           r'\*'),
    ('LPAREN',          r'\('),
    ('RPAREN',          r'\)'),
    ('LBRACE',          r'\{'),
    ('RBRACE',          r'\}'),
    ('SEMICOLON',       r';'),
    ('COMMA',           r','),
    ('SKIP',            r'[ \t]+'),
    ('NEWLINE',         r'\n'),
    ('MISMATCH',        r'.')
]

PROIBITED_KEYWORDS = { 'if', 'else', 'main', 'while', 'int', 'float', 'string', 'cin', 'cout', 'return', 'void' }

token_list = []

for pair in TOKEN:
    part = '(?P<%s>%s)' % pair
    token_list.append(part)

token_regex = '|'.join(token_list)
get_token = re.compile(token_regex).match

def lexer(code):
    line_number = 1
    tokens = []
    tok = get_token(code)

    while tok is not None:
        type = tok.lastgroup
        val = tok.group(type)
        if type == 'NEWLINE':
            line_number += 1
        elif type == 'SKIP':
            pass
        elif type == 'MISMATCH':
            raise SyntaxError(f"Error in line {line_number}: Unexpected Character")
        else:
            if type == 'ID' and val in PROIBITED_KEYWORDS:
                if val in ('int','string','float','void'):
                    type = "TYPE_"+val.upper()
                else:
                    type = val.upper()
            tokens.append((type, val, line_number))
        pos = tok.end()
        tok = get_token(code, pos)
    return tokens

if __name__ == '__main__':
    code = '''
    int a;
    a = 5;
    float b = 3.2;
    if (a > 5) {
        cout << "A maggiore di 5";
    } else {
        cout << "A minore o uguale a 5";
    }
    cin >> a;
    '''

    for token in lexer(code):
        print(token)
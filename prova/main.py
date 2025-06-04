from lexer import tokenize
from parser import Parser

code = '''
function add(a, b) {
    return a + b;
}
'''

tokens = tokenize(code)
parser = Parser(tokens)
ast = parser.parse()

print(ast.__dict__)  # stampa la struttura della funzione

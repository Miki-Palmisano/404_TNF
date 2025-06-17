from lexer import lexer
from parser import Parser

code = '''
function add(a, b) {
    return a + b;
}
'''

tokens = lexer(code)
parser = Parser(tokens)
ast = parser.parse()

from pprint import pprint

pprint(ast)
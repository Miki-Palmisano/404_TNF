from lexer import lexer
from parser import Parser

code = ''' 
    int a;
    a = 5;
    float b = 3;
    if (a > b) {
        cout << "a maggiore";
    } 
'''

tokens = lexer(code)
parser = Parser(tokens)
ast = parser.parse()

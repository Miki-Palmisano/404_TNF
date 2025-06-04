# ast.py


class FunctionDef:
    def __init__(self, name, params, body):
        self.name = name
        self.params = params
        self.body = body

class Return:
    def __init__(self, value):
        self.value = value

class BinOp:
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

class Var:
    def __init__(self, name):
        self.name = name

class Num:
    def __init__(self, value):
        self.value = float(value) if '.' in value else int(value)

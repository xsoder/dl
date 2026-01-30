#!/usr/bin/env python3

import sys

SYM_TOK = ['+', '-', '*', '/', '(', ')', '>', '<', '=', ':', ';', '{', '}']
TYPE_TOK = ['i32']
KEY_TOK = ['main', 'return']

class Token:
    def __init__(self, typ, val):
        self.typ = typ
        self.val = val

    def __repr__(self):
        return f"Token(typ='{self.typ}', val='{self.val}')\n"

def tokenize(input_string):
    toks = []
    current = ""
    for ch in input_string:
        if ch in SYM_TOK:
            if current:
                if current.isdigit():
                    toks.append(Token('NUM', int(current)))
                elif current in TYPE_TOK:
                    toks.append(Token('TYPE', current))
                elif current in KEY_TOK:
                    toks.append(Token('KEY', current))
                else:
                    toks.append(Token('VAR', current))
                current = ""
            toks.append(Token('SYM', ch))
        elif ch.isspace():
            if current:
                if current.isdigit():
                    toks.append(Token('NUM', int(current)))
                elif current in TYPE_TOK:
                    toks.append(Token('TYPE', current))
                elif current in KEY_TOK:
                    toks.append(Token('KEY', current))
                else:
                    toks.append(Token('VAR', current))
                current = ""
        else:
            current += ch

    if current:
        if current.isdigit():
            toks.append(Token('NUM', int(current)))
        elif current in TYPE_TOK:
            toks.append(Token('TYPE', current))
        elif current in KEY_TOK:
            toks.append(Token('KEY', current))
        else:
            toks.append(Token('VAR', current))

    return toks

def extract_token(tokens, sym_type, sym_name):
    return [token for token in tokens if token.typ == sym_type and token.val == sym_name]

def read_file(file_path):
    with open(file_path) as fs:
        return fs.read()

def find_entry(tok, file_path):
    main_sym = 'main'
    entry = extract_token(tok, 'KEY', main_sym)
    if len(entry) == 0:
        print(f"{file_path}:0: ERROR: Could not find entry point {main_sym}")
        exit(1)
    else:
        print(f"Entry point found at {file_path}")


def parse_file(file_path):
    content = read_file(file_path)
    tk = tokenize(content)
    find_entry(tk, file_path)
    p = Parser(tk)
    ast = p.parse_function()
    return ast

def print_ast(node, indent=0):
    prefix = ' ' * indent
    if isinstance(node, Function):
        print(f"{prefix}Function: {node.name.val}")
        for stmt in node.body:
            print_ast(stmt, indent + 2)
    elif isinstance(node, Variable):
        print(f"{prefix}Variable: {node.val}")
    elif isinstance(node, Number):
        print(f"{prefix}Number: {node.val}")
    elif isinstance(node, VarDecl):
        print(f"{prefix}VarDec: {node.val}: {node.typ}")
        print_ast(node.expr, indent + 2)
    elif isinstance(node, Return):
        print(f"{prefix}Return:")
        print_ast(node.expr, indent + 2)
    else:
        assert False, "Unreachable"

class Parser:
    def __init__(self, token):
        self.token = token
        self.pos = 0

    def peek(self):
        if self.pos < len(self.token):
            return self.token[self.pos]
        return None

    def consume(self, typ = None, val = None):
        tok = self.peek()
        if tok is None:
            print(f"Unexpected token type {tok.typ} and name {tok.val}")
            return
        if tok.typ != typ and typ:
            print(f"Unexpected token type {tok.typ} and name {tok.val}")
            return
        elif tok.val != val and val:
            print(f"Unexpected token type {tok.typ} and name {tok.val}")
            return
        self.pos += 1
        return tok

    def get_current_token(self):
        if self.pos < len(self.token):
            return self.token[self.pos]
        return None

    def parse_statement(self):
        tk = self.get_current_token()
        if tk.typ == 'VAR':
            return self.parse_decl()
        elif tk.typ == 'KEY' and tk.val == 'return':
            return self.parse_ret()
        else:
            assert False, "Not implemented"

    def parse_decl(self):
        name = self.consume('VAR')
        self.consume('SYM', ':')
        typ = self.consume('TYPE')
        self.consume('SYM', '=')
        expr = self.parse_expr()
        self.consume('SYM', ';')
        return VarDecl(name.val, typ.val, expr)

    def parse_ret(self):
        self.consume('KEY', 'return')
        expr = self.parse_expr()
        self.consume('SYM', ';')
        return Return(expr)

    def parse_function(self):
        name = self.consume('KEY', 'main')

        self.consume('SYM', ':')
        self.consume('SYM', ':')
        self.consume('TYPE', 'i32')
        self.consume('SYM', '{')

        body = self.parse_block()

        self.consume('SYM', '}')
        return Function(name, None, body)

    def parse_expr(self):
        tok = self.get_current_token()
        if tok.typ == 'VAR':
            self.consume('VAR')
            return Variable(tok.val)
        elif tok.typ == 'NUM':
            self.consume('NUM')
            return Number(tok.val, tok.typ)
        else:
            assert False, "Unreachable"

    def parse_block(self):
        statements = []
        while self.get_current_token().val != '}':
            statements.append(self.parse_statement())
        return statements

class Function:
    def __init__(self, name, param, body):
        self.name = name
        self.param = param
        self.body = body

class Binop:
    def __init__(self, lhs, rhs, op):
        self.lhs = lhs
        self.rhs = rhs
        self.op = op

class Number:
    def __init__(self, val, typ):
        self.val = val
        self.typ = typ

class Variable:
    def __init__(self, val, typ='i32'):
        self.val = val
        self.typ = typ

class VarDecl:
    def __init__(self, val, typ, expr):
        self.val = val
        self.typ = typ
        self.expr = expr

class Return:
    def __init__(self, expr):
        self.expr = expr

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("USAGE: dl ./filename")
        exit(1)

    file_path = sys.argv[1]
    ast = parse_file(file_path)
    print_ast(ast)

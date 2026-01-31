#!/usr/bin/env python3

import sys, subprocess, os

SYM_TOK = ['+', '-', '*', '/', '(', ')', '>', '<', '=', ':', ';', '{', '}']
TYPE_TOK = ['i32', 'i8', 'i16', 'i64']
KEY_TOK = ['main', 'return']

class CompileError(Exception):
    pass

class Token:
    def __init__(self, typ, val, line):
        self.typ = typ
        self.val = val
        self.line = line

def tokenize(input_string):
    toks = []
    current = ""
    line = 1

    def emit_current():
        nonlocal current
        if not current:
            return
        if current.isdigit():
            toks.append(Token('NUM', int(current), line))
        elif current in TYPE_TOK:
            toks.append(Token('TYPE', current, line))
        elif current in KEY_TOK:
            toks.append(Token('KEY', current, line))
        else:
            toks.append(Token('VAR', current, line))
        current = ""

    for ch in input_string:
        if ch == '\n':
            emit_current()
            line += 1
        elif ch in SYM_TOK:
            emit_current()
            toks.append(Token('SYM', ch, line))
        elif ch.isspace():
            emit_current()
        else:
            current += ch

    emit_current()
    return toks

def read_file(path):
    with open(path) as f:
        return f.read()

def extract_token(tokens, typ, val):
    return [t for t in tokens if t.typ == typ and t.val == val]

def find_entry(tokens, file_path):
    if not extract_token(tokens, 'KEY', 'main'):
        raise CompileError(f"{file_path}: ERROR: missing entry point main")

def parse_file(file_path):
    content = read_file(file_path)
    tokens = tokenize(content)
    find_entry(tokens, file_path)
    parser = Parser(tokens, file_path)
    return parser.parse_function()

class Parser:
    def __init__(self, tokens, file_path):
        self.tokens = tokens
        self.pos = 0
        self.file_path = file_path
        self.sym = {}

    def error(self, msg, tok=None):
        line = tok.line if tok else 0
        raise CompileError(f"{self.file_path}:{line}: ERROR: {msg}")

    def peek(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def consume(self, typ=None, val=None):
        tok = self.peek()
        if tok is None:
            self.error("unexpected end of file")
        if typ and tok.typ != typ:
            self.error(f"expected {typ}, got {tok.typ}", tok)
        if val and tok.val != val:
            self.error(f"expected '{val}', got '{tok.val}'", tok)
        self.pos += 1
        return tok

    def parse_function(self):
        self.consume('KEY', 'main')
        self.consume('SYM', ':')
        self.consume('SYM', ':')
        self.consume('TYPE', 'i32')
        self.consume('SYM', '{')
        body = self.parse_block()
        self.consume('SYM', '}')
        return Function(body)

    def parse_block(self):
        stmts = []
        while self.peek().val != '}':
            stmts.append(self.parse_statement())
        return stmts

    def parse_statement(self):
        tok = self.peek()
        if tok.typ == 'VAR':
            return self.parse_decl()
        if tok.typ == 'KEY' and tok.val == 'return':
            return self.parse_return()
        self.error("invalid statement", tok)

    def parse_decl(self):
        name = self.consume('VAR')
        self.consume('SYM', ':')
        typ = self.consume('TYPE')
        self.consume('SYM', '=')
        expr = self.parse_expr()
        self.consume('SYM', ';')

        if expr.typ is None:
            expr.typ = typ.val

        if expr.typ != typ.val:
            self.error(f"type mismatch: cannot assign {expr.typ} to {typ.val}", name)

        self.sym[name.val] = typ.val
        return VarDecl(name.val, typ.val, expr)

    def parse_return(self):
        tok = self.consume('KEY', 'return')
        expr = self.parse_expr()
        self.consume('SYM', ';')

        if expr.typ is None:
            expr.typ = 'i32'

        if expr.typ != 'i32':
            self.error(f"return type {expr.typ}, expected i32", tok)

        return Return(expr)

    def parse_expr(self):
        tok = self.peek()

        if tok.typ == 'NUM':
            self.consume('NUM')
            return IntLiteral(tok.val)

        if tok.typ == 'VAR':
            self.consume('VAR')
            if tok.val not in self.sym:
                self.error(f"undeclared variable '{tok.val}'", tok)
            return Variable(tok.val, self.sym[tok.val])

        self.error("invalid expression", tok)

class Function:
    def __init__(self, body):
        self.body = body

class IntLiteral:
    def __init__(self, val):
        self.val = val
        self.typ = None

class Variable:
    def __init__(self, name, typ):
        self.val = name
        self.typ = typ

class VarDecl:
    def __init__(self, name, typ, expr):
        self.name = name
        self.typ = typ
        self.expr = expr

class Return:
    def __init__(self, expr):
        self.expr = expr

class CodeGen:
    def __init__(self, filename='a.asm'):
        self.out = []
        self.filename = filename
        self.sym = {}
        self.offset = 0

    def emit(self, line):
        self.out.append(line)

    def generate(self, node):
        if isinstance(node, Function):
            self.generate_func(node)
        elif isinstance(node, VarDecl):
            self.generate_vardec(node)
        elif isinstance(node, Return):
            self.generate_return(node)
        elif isinstance(node, Variable):
            self.generate_var(node)
        elif isinstance(node, IntLiteral):
            self.generate_intlit(node)
        else:
            assert False, "Unreachable"

    def generate_func(self, fn):
        self.emit("format ELF64")
        self.emit("public main")
        self.emit("section '.text' executable")
        self.emit("")
        self.emit("main:")
        self.emit("        push rbp")
        self.emit("        mov rbp, rsp")

        for stmt in fn.body:
            self.generate(stmt)

        self.emit("        pop rbp")
        self.emit("        ret\n")
    def generate_vardec(self, vardecl):
        offset = self.offset
        if vardecl.typ == 'i8' or vardecl.typ == 'u8':
            offset += 1
        elif vardecl.typ == 'i16' or vardecl.typ == 'u16':
            offset += 2
        elif vardecl.typ == 'i32' or vardecl.typ == 'u32':
            offset += 4
        elif vardecl.typ == 'u64' or vardecl.typ == 'i64':
            offset += 8
        else:
            offset += 1

        if isinstance(vardecl.expr, IntLiteral):
            self.emit(f"        mov DWORD [rbp-{offset}], {vardecl.expr.val}")
        else:
            print(f"{self.filename}:{self.line}: ERROR: Could not get integer literal {ret.val}")
            exit(1)
            
    def generate_var(self, vardecl):
        offset = self.offset
        if vardecl.typ == 'i8' or vardecl.typ == 'u8':
            offset += 1
        elif vardecl.typ == 'i16' or vardecl.typ == 'u16':
            offset += 2
        elif vardecl.typ == 'i32' or vardecl.typ == 'u32':
            offset += 4
        elif vardecl.typ == 'u64' or vardecl.typ == 'i64':
            offset += 8
        else:
            offset += 1

        if isinstance(vardecl.expr, IntLiteral):
            self.emit(f"        mov DWORD [rbp-{offset}], {vardecl.expr.val}")

    def generate_intlit(self, intlit):
        # self.emit(f"        mov DWORD [rbp-{byte}], {intlit.val}")
        self.emit(f"        ;; TODO: ")

    def generate_return(self, retval):
        ret = retval.expr
        if isinstance(retval.expr, IntLiteral):
            self.emit(f"        mov eax, {ret.val}")
        else:
            print(f"{self.filename}:{self.line}: ERROR: Could not get integer literal {ret.val}")
            exit(1)
    def write_file(self):
        with open(self.filename, 'w') as f:
            f.write('\n'.join(self.out))
            return self.filename

def print_ast(node, indent=0):
    p = ' ' * indent
    if isinstance(node, Function):
        print(f"{p}Function")
        for s in node.body:
            print_ast(s, indent + 2)
    elif isinstance(node, VarDecl):
        print(f"{p}VarDecl {node.name}:{node.typ}")
        print_ast(node.expr, indent + 2)
    elif isinstance(node, Return):
        print(f"{p}Return")
        print_ast(node.expr, indent + 2)
    elif isinstance(node, Variable):
        print(f"{p}Variable {node.val}")
    elif isinstance(node, IntLiteral):
        print(f"{p}IntLiteral {node.val}")

def usage():
    print("USAGE: dl <file>")
    sys.exit(1)

def compilation(inputfile, objfile='a.o', outputfile='a.out'):
    if inputfile == None:
        usage()
        exit(1)
    cmd = ['fasm', inputfile, objfile]
    print(f"CMD: {cmd}")
    subprocess.run(cmd)

    cmd = ['gcc', objfile, '-o', outputfile]
    print(f"CMD: {cmd}")
    subprocess.run(cmd)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        usage()
    try:
        ast = parse_file(sys.argv[1])
        cd = CodeGen()
        cd.generate(ast)
        inputfile = cd.write_file()
        compilation(inputfile)

    except CompileError as e:
        print(e)
        sys.exit(1)

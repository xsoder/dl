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
    for t in tk:
        print(t)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("USAGE: dl ./filename")
        exit(1)

    file_path = sys.argv[1]
    parse_file(file_path)


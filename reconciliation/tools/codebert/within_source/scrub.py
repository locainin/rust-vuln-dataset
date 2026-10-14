#!/usr/bin/env python3
"""Label-scrubbing transformation (versioned). Removes every comment from Rust
source while respecting string/char literals and raw strings, drops blank
lines. Inputs are file CONTENTS only; paths, advisory IDs and metadata never
reach the model. Version: scrub-v1 (freeze this string in the paper)."""
SCRUB_VERSION = "scrub-v1"

def scrub(src: str) -> str:
    out, i, n = [], 0, len(src)
    while i < n:
        c = src[i]
        if c == '/' and i+1 < n and src[i+1] == '/':          # line comment
            while i < n and src[i] != '\n': i += 1
        elif c == '/' and i+1 < n and src[i+1] == '*':        # block comment (nested)
            depth, i = 1, i+2
            while i < n and depth:
                if src[i] == '/' and i+1 < n and src[i+1] == '*': depth += 1; i += 2
                elif src[i] == '*' and i+1 < n and src[i+1] == '/': depth -= 1; i += 2
                else: i += 1
        elif c == 'r' and i+1 < n and src[i+1] in '#"':        # raw string r#"..."#
            j = i+1; hashes = 0
            while j < n and src[j] == '#': hashes += 1; j += 1
            if j < n and src[j] == '"':
                end = '"' + '#'*hashes
                k = src.find(end, j+1)
                k = n if k < 0 else k+len(end)
                out.append(src[i:k]); i = k
            else:
                out.append(c); i += 1
        elif c == '"':                                         # string literal
            j = i+1
            while j < n:
                if src[j] == '\\': j += 2
                elif src[j] == '"': j += 1; break
                else: j += 1
            out.append(src[i:j]); i = j
        elif c == "'":                                         # char literal / lifetime
            if i+2 < n and (src[i+1] == '\\' or src[i+2] == "'"):
                j = i+2
                while j < n and src[j] != "'": j += 1
                out.append(src[i:j+1]); i = j+1
            else:
                out.append(c); i += 1                          # lifetime tick
        else:
            out.append(c); i += 1
    lines = [l.rstrip() for l in ''.join(out).split('\n')]
    return '\n'.join(l for l in lines if l.strip())

if __name__ == "__main__":
    import sys
    print(scrub(open(sys.argv[1], encoding='utf-8', errors='replace').read()))

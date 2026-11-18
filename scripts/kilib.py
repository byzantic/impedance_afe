"""Minimal KiCad symbol-library helpers: S-expression parse, extract+flatten symbols, pin geometry."""
import re, os

SYMDIR = "/usr/share/kicad/symbols"

def tokenize(s):
    i, n = 0, len(s)
    while i < n:
        c = s[i]
        if c in '()':
            yield c; i += 1
        elif c.isspace():
            i += 1
        elif c == '"':
            j = i + 1; buf = []
            while s[j] != '"':
                if s[j] == '\\': buf.append(s[j:j+2]); j += 2
                else: buf.append(s[j]); j += 1
            yield ('S', ''.join(buf)); i = j + 1
        else:
            j = i
            while j < n and not s[j].isspace() and s[j] not in '()': j += 1
            yield ('A', s[i:j]); i = j

def parse(s):
    stack = [[]]
    for t in tokenize(s):
        if t == '(':
            stack.append([])
        elif t == ')':
            x = stack.pop(); stack[-1].append(x)
        else:
            stack[-1].append(t)
    return stack[0][0]

def dump(x, ind=0):
    if isinstance(x, tuple):
        return '"%s"' % x[1] if x[0] == 'S' else x[1]
    head = dump(x[0]) if x else ''
    simple = all(not isinstance(e, list) for e in x)
    if simple:
        return '(' + ' '.join(dump(e) for e in x) + ')'
    out = '(' + head
    for e in x[1:]:
        if isinstance(e, list):
            out += '\n' + '  ' * (ind + 1) + dump(e, ind + 1)
        else:
            out += ' ' + dump(e)
    return out + ')'

def name(x):  # head atom
    return x[0][1] if x and isinstance(x[0], tuple) else None

_libcache = {}
def lib(libname):
    if libname not in _libcache:
        p = libname + '.kicad_sym' if os.path.exists(libname + '.kicad_sym') else os.path.join(SYMDIR, libname + '.kicad_sym')
        _libcache[libname] = parse(open(p).read())
    return _libcache[libname]

def find_sym(libname, sym):
    for e in lib(libname)[1:]:
        if isinstance(e, list) and name(e) == 'symbol' and e[1][1] == sym:
            return e
    raise KeyError(f'{libname}:{sym}')

def flattened(libname, sym):
    """Return symbol node named 'lib:sym' with extends resolved."""
    import copy
    s = copy.deepcopy(find_sym(libname, sym))
    ext = [e for e in s if isinstance(e, list) and name(e) == 'extends']
    if ext:
        parent = flattened(libname, ext[0][1][1])
        pname = parent[1][1].split(':', 1)[1]
        child_props = {e[1][1]: e for e in s if isinstance(e, list) and name(e) == 'property'}
        new = [('A', 'symbol'), ('S', sym)]
        for e in parent[2:]:
            if isinstance(e, list) and name(e) == 'property' and e[1][1] in child_props:
                new.append(child_props.pop(e[1][1]))
            elif isinstance(e, list) and name(e) == 'symbol':
                sub = copy.deepcopy(e)
                sub[1] = ('S', sub[1][1].replace(pname, sym, 1))
                new.append(sub)
            else:
                new.append(e)
        # leftover child-only props: insert after other props
        idx = max(i for i, e in enumerate(new) if isinstance(e, list) and name(e) == 'property') + 1
        for p in child_props.values():
            new.insert(idx, p); idx += 1
        s = new
    s[1] = ('S', f'{libname}:{sym}')
    return s

def pins(symnode, unit=1):
    """List of dict(number,name,x,y,angle,etype) in lib coords (y up)."""
    out = []
    def walk(n, u):
        for e in n:
            if isinstance(e, list):
                if name(e) == 'symbol':
                    m = re.search(r'_(\d+)_(\d+)$', e[1][1])
                    walk(e, int(m.group(1)) if m else u)
                elif name(e) == 'pin':
                    if u not in (0, unit): continue
                    at = [x for x in e if isinstance(x, list) and name(x) == 'at'][0]
                    num = [x for x in e if isinstance(x, list) and name(x) == 'number'][0][1][1]
                    nm = [x for x in e if isinstance(x, list) and name(x) == 'name'][0][1][1]
                    hidden = any(isinstance(x, tuple) and x[1] == 'hide' for x in e)
                    out.append(dict(number=num, name=nm, x=float(at[1][1]), y=float(at[2][1]),
                                    angle=float(at[3][1]) if len(at) > 3 else 0, etype=e[1][1], hidden=hidden))
    walk(symnode, unit)
    return out

def prop(symnode, key):
    for e in symnode:
        if isinstance(e, list) and name(e) == 'property' and e[1][1] == key:
            return e[2][1]
    return None

if __name__ == '__main__':
    import sys
    for spec in sys.argv[1:]:
        l, s = spec.split(':')
        n = flattened(l, s)
        print(spec, prop(n, 'Footprint'))
        for p in pins(n):
            print('   ', p['number'], p['name'], p['etype'], p['x'], p['y'], p['angle'])

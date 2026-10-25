"""Попарное сходство работ: код (токены, без комментариев и строк) и текст markdown (словесные 5-граммы).

Запуск: python3 -I grading/tools/similarity.py <repo_root> <out_json>
"""
import io, json, os, re, sys, tokenize, itertools

root, out = sys.argv[1], sys.argv[2]
files = sorted(f for f in os.listdir(root) if f.endswith('.ipynb') or f == 'Спирин.py')


def text_of(x):
    return ''.join(x) if isinstance(x, list) else (x or '')


def code_tokens(src):
    toks = []
    try:
        for t in tokenize.generate_tokens(io.StringIO(src).readline):
            if t.type in (tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT):
                continue
            if t.type == tokenize.STRING:
                toks.append('S')
            elif t.type == tokenize.NAME:
                toks.append(t.string)
            elif t.type == tokenize.NUMBER:
                toks.append('N')
            else:
                toks.append(t.string)
    except Exception:
        toks = re.findall(r'\w+|[^\s\w]', re.sub(r'#.*', '', src))
    return toks


def comments(src):
    return [c.strip('# ').lower() for c in re.findall(r'#[^\n]*', src) if len(c) > 12]


docs = {}
for f in files:
    sid = os.path.splitext(f)[0]
    p = os.path.join(root, f)
    if f.endswith('.py'):
        src = open(p, encoding='utf-8').read()
        md = ' '.join(re.findall(r'"""(.*?)"""', src, re.S))
        code = [src]
    else:
        nb = json.load(open(p, encoding='utf-8'))
        code = [text_of(c['source']) for c in nb['cells'] if c['cell_type'] == 'code']
        md = '\n'.join(text_of(c['source']) for c in nb['cells'] if c['cell_type'] == 'markdown')
    code_src = '\n'.join(re.sub(r'^\s*[!%].*$', '', c, flags=re.M) for c in code)
    toks = code_tokens(code_src)
    grams = set(tuple(toks[i:i + 12]) for i in range(max(0, len(toks) - 11)))
    words = re.findall(r'[а-яёa-z0-9]+', md.lower())
    wgrams = set(tuple(words[i:i + 6]) for i in range(max(0, len(words) - 5)))
    docs[sid] = {'code': grams, 'md': wgrams, 'comments': set(comments(code_src))}


def jac(a, b):
    return len(a & b) / len(a | b) if a and b else 0.0


def cont(a, b):  # доля меньшего множества, найденная в большем
    return len(a & b) / min(len(a), len(b)) if a and b else 0.0


pairs = []
for a, b in itertools.combinations(docs, 2):
    A, B = docs[a], docs[b]
    pairs.append({'a': a, 'b': b,
                  'code_jac': round(jac(A['code'], B['code']), 3), 'code_cont': round(cont(A['code'], B['code']), 3),
                  'md_jac': round(jac(A['md'], B['md']), 3), 'md_cont': round(cont(A['md'], B['md']), 3),
                  'same_comments': sorted(A['comments'] & B['comments'])[:10]})
json.dump(pairs, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('пар:', len(pairs))
for key in ('code_cont', 'md_cont'):
    print('\nТоп по', key)
    for p in sorted(pairs, key=lambda x: -x[key])[:25]:
        print(f"  {p[key]:.3f}  code_jac={p['code_jac']:.3f} md_jac={p['md_jac']:.3f}  {p['a'][:30]} <-> {p['b'][:30]}  comm={len(p['same_comments'])}")

# --- второй проход: убираем общие для многих работ фрагменты (текст условия, стандартные идиомы)
from collections import Counter
md_freq = Counter(g for d in docs.values() for g in d['md'])
code_freq = Counter(g for d in docs.values() for g in d['code'])
rare = []
for a, b in itertools.combinations(docs, 2):
    A, B = docs[a], docs[b]
    mda = {g for g in A['md'] if md_freq[g] <= 2}; mdb = {g for g in B['md'] if md_freq[g] <= 2}
    ca = {g for g in A['code'] if code_freq[g] <= 2}; cb = {g for g in B['code'] if code_freq[g] <= 2}
    rare.append({'a': a, 'b': b, 'md_shared_rare': len(mda & mdb), 'code_shared_rare': len(ca & cb),
                 'md_rare_frac': round(len(mda & mdb) / max(1, min(len(mda), len(mdb))), 3),
                 'code_rare_frac': round(len(ca & cb) / max(1, min(len(ca), len(cb))), 3)})
json.dump(rare, open(out.replace('.json', '_rare.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for key in ('code_shared_rare', 'md_shared_rare'):
    print('\nТоп по', key, '(фрагменты, встречающиеся только в этих двух работах)')
    for p in sorted(rare, key=lambda x: -x[key])[:20]:
        print(f"  {p[key]:5d} ({p[key.replace('shared_rare','rare_frac')]:.3f})  {p['a'][:30]} <-> {p['b'][:30]}")

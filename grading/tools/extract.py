"""Разворачивает работы студентов в читаемый вид и ищет инъекции/технические признаки.

Код студентов не выполняется: .ipynb читается как JSON.
Запуск: python3 -I grading/tools/extract.py <repo_root> <out_dir>
Для каждой работы: <out_dir>/<id>/cells.md, <out_dir>/<id>/img/*.png; сводка: <out_dir>/scan.json
"""
import base64, json, os, re, sys, unicodedata

root, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)

files = sorted(f for f in os.listdir(root)
               if f.endswith('.ipynb') or f == 'Спирин.py')

KEYWORDS = ['ignore', 'instruction', 'grader', 'prompt', 'assistant', 'system', 'chatgpt', 'gpt', 'claude',
            'llm', 'openai', 'copilot', 'gemini', 'deepseek', 'cursor',
            'ии', 'нейросет', 'проверяющ', 'оценк', 'балл', 'игнорир', 'инструкц', 'модель', 'ассистент']
HIDDEN = {chr(c) for c in list(range(0x200B, 0x2010)) + [0x2060, 0xFEFF, 0x00AD, 0x2061, 0x2062, 0x2063, 0x2064, 0x180E]}
TAGCHARS = re.compile('[\U000E0000-\U000E007F]')


def text_of(x):
    return ''.join(x) if isinstance(x, list) else (x or '')


def scan_text(s, where, res):
    low = s.lower()
    for k in KEYWORDS:
        if k in ('ии', 'gpt'):
            pat = r'(?<![а-яёa-z])' + k + r'(?![а-яёa-z])'
            if re.search(pat, low):
                res['keywords'].setdefault(k, []).append(where)
        elif k in low:
            res['keywords'].setdefault(k, []).append(where)
    hid = [f'U+{ord(ch):04X}' for ch in s if ch in HIDDEN]
    if hid or TAGCHARS.search(s):
        res['hidden_chars'].append({'where': where, 'chars': sorted(set(hid)) + (['TAG'] if TAGCHARS.search(s) else [])})
    for m in re.finditer(r'<!--(.*?)-->', s, re.S):
        res['html_comments'].append({'where': where, 'text': m.group(1)[:500]})
    for m in re.finditer(r'<[^>]*(display\s*:\s*none|visibility\s*:\s*hidden|font-size\s*:\s*0|color\s*:\s*(white|#fff))[^>]*>', s, re.I):
        res['hidden_html'].append({'where': where, 'tag': m.group(0)[:300]})
    for m in re.finditer(r'!\[[^\]]*\]\(([^)]+)\)|<img[^>]+src=["\']([^"\']+)', s):
        res['md_images'].append({'where': where, 'src': (m.group(1) or m.group(2))[:200]})
    for m in re.finditer(r'(/Users/[^\s\'"]+|/home/[^\s\'"]+|[A-Z]:\\\\?[^\s\'"]+|/content/[^\s\'"]*|/kaggle/[^\s\'"]*|drive/MyDrive[^\s\'"]*)', s):
        res['paths'].add(m.group(0)[:120])
    # необычные (не латиница/кириллица/обычная пунктуация) символы — гомоглифы и т.п.
    for ch in set(s):
        cat = unicodedata.category(ch)
        if cat in ('Cf', 'Co', 'Cs') and ch not in HIDDEN:
            res['hidden_chars'].append({'where': where, 'chars': [f'U+{ord(ch):04X} ({cat})']})


MARKERS = {
    'matplotlib_use_agg': r"matplotlib\.use\(\s*['\"]Agg",
    'type_hints': r'def \w+\([^)]*:\s*[A-Za-z_\[\]., ]+\)|\)\s*->\s*[A-Za-z_]',
    'docstrings': r'^\s*(\"\"\"|\'\'\')',
    'assert': r'^\s*assert\b',
    'raise': r'^\s*raise\b',
    'seed42': r'seed\s*=?\s*\(?\s*42|random_state\s*=\s*42',
    'pip_in_try': r'try:\s*\n\s*import[^\n]*\n\s*except[^\n]*\n[^\n]*pip',
    'pip_install': r'pip install',
    'scipy_stats': r'scipy|statsmodels|pearsonr|spearmanr|ttest|wilson|binom|anova|f_oneway|mannwhitney',
    'xg_model': r'xG|expected goals|LogisticRegression|sklearn',
    'display_image_func': r'IPython\.display\s+import\s+(Image|display)|display\(Image',
    'savefig': r'savefig',
    'f_string_print_sections': r'print\(\s*f?["\']=+',
}


def scan_markers(code, res):
    for k, pat in MARKERS.items():
        n = len(re.findall(pat, code, re.M | re.I))
        if n:
            res['markers'][k] = n


summary = {}
for fname in files:
    sid = os.path.splitext(fname)[0]
    d = os.path.join(out, sid)
    os.makedirs(os.path.join(d, 'img'), exist_ok=True)
    res = {'file': fname, 'keywords': {}, 'hidden_chars': [], 'html_comments': [], 'hidden_html': [],
           'md_images': [], 'paths': set(), 'markers': {}, 'attachments': [], 'nb_metadata': None,
           'cell_metadata_keys': {}, 'exec_counts': [], 'n_code': 0, 'n_md': 0, 'n_images': 0,
           'errors': 0, 'md_words': 0, 'code_lines': 0, 'comment_lines': 0}
    path = os.path.join(root, fname)
    lines = []
    if fname.endswith('.py'):
        src = open(path, encoding='utf-8', errors='replace').read()
        scan_text(src, 'py', res); scan_markers(src, res)
        res['n_code'] = 1
        res['code_lines'] = src.count('\n')
        res['comment_lines'] = len(re.findall(r'^\s*#', src, re.M))
        lines.append(f'# {fname}\n\n```python\n{src}\n```\n')
    else:
        nb = json.load(open(path, encoding='utf-8'))
        res['nb_metadata'] = nb.get('metadata', {})
        scan_text(json.dumps(nb.get('metadata', {}), ensure_ascii=False), 'nb.metadata', res)
        lines.append(f'# {fname}\n\nnbformat {nb.get("nbformat")}.{nb.get("nbformat_minor")}; metadata keys: {list(nb.get("metadata", {}).keys())}\n')
        all_code = []
        img_no = 0
        for i, c in enumerate(nb.get('cells', [])):
            ct = c.get('cell_type')
            src = text_of(c.get('source'))
            md_keys = [k for k in c.get('metadata', {}).keys()]
            for k in md_keys:
                res['cell_metadata_keys'][k] = res['cell_metadata_keys'].get(k, 0) + 1
            meta_txt = json.dumps(c.get('metadata', {}), ensure_ascii=False)
            if len(meta_txt) > 2:
                scan_text(meta_txt, f'cell{i}.metadata', res)
            if c.get('attachments'):
                for an, av in c['attachments'].items():
                    res['attachments'].append({'cell': i, 'name': an})
                    for mime, b64 in av.items():
                        if mime.startswith('image/'):
                            img_no += 1
                            fn = f'att_c{i}_{img_no}.{mime.split("/")[1].split("+")[0]}'
                            open(os.path.join(d, 'img', fn), 'wb').write(base64.b64decode(b64))
                            lines.append(f'[вложение {an} → img/{fn}]\n')
            scan_text(src, f'cell{i}.{ct}', res)
            if ct == 'markdown':
                res['n_md'] += 1
                res['md_words'] += len(src.split())
                lines.append(f'\n---- [{i}] markdown ----\n{src}\n')
            elif ct == 'code':
                res['n_code'] += 1
                res['exec_counts'].append(c.get('execution_count'))
                all_code.append(src)
                res['code_lines'] += src.count('\n') + 1
                res['comment_lines'] += len(re.findall(r'^\s*#', src, re.M))
                lines.append(f'\n---- [{i}] code, In[{c.get("execution_count")}] ----\n```python\n{src}\n```\n')
                for o in c.get('outputs', []):
                    ot = o.get('output_type')
                    if ot == 'stream':
                        t = text_of(o.get('text'))
                        scan_text(t, f'cell{i}.stream', res)
                        if 'pip install' in t or 'Requirement already satisfied' in t or 'Successfully installed' in t:
                            res['markers']['pip_output'] = res['markers'].get('pip_output', 0) + 1
                        lines.append(f'[{o.get("name")}]\n{t[:6000]}' + ('\n…(обрезано)' if len(t) > 6000 else '') + '\n')
                    elif ot in ('execute_result', 'display_data'):
                        data = o.get('data', {})
                        for mime in ('image/png', 'image/jpeg'):
                            if mime in data:
                                img_no += 1; res['n_images'] += 1
                                fn = f'c{i}_{img_no}.{mime.split("/")[1]}'
                                b64 = data[mime] if isinstance(data[mime], str) else ''.join(data[mime])
                                open(os.path.join(d, 'img', fn), 'wb').write(base64.b64decode(b64))
                                lines.append(f'[рисунок → img/{fn}]\n')
                        if 'image/svg+xml' in data:
                            img_no += 1; res['n_images'] += 1
                            fn = f'c{i}_{img_no}.svg'
                            open(os.path.join(d, 'img', fn), 'w').write(text_of(data['image/svg+xml']))
                            lines.append(f'[рисунок svg → img/{fn}]\n')
                        if 'text/plain' in data:
                            t = text_of(data['text/plain'])
                            scan_text(t, f'cell{i}.result', res)
                            lines.append(f'[Out]\n{t[:6000]}' + ('\n…(обрезано)' if len(t) > 6000 else '') + '\n')
                        if 'text/html' in data and 'text/plain' not in data:
                            t = text_of(data['text/html'])
                            scan_text(t, f'cell{i}.html', res)
                            lines.append(f'[Out html]\n{re.sub("<[^>]+>", " ", t)[:4000]}\n')
                        elif 'text/html' in data:
                            scan_text(text_of(data['text/html']), f'cell{i}.html', res)
                        if 'text/markdown' in data:
                            t = text_of(data['text/markdown'])
                            scan_text(t, f'cell{i}.mdout', res)
                            lines.append(f'[Out markdown]\n{t[:4000]}\n')
                    elif ot == 'error':
                        res['errors'] += 1
                        tb = '\n'.join(o.get('traceback', []))
                        tb = re.sub(r'\x1b\[[0-9;]*m', '', tb)
                        lines.append(f'[ОШИБКА {o.get("ename")}: {o.get("evalue")}]\n{tb[-1500:]}\n')
            else:
                lines.append(f'\n---- [{i}] {ct} ----\n{src}\n')
        scan_markers('\n'.join(all_code), res)
    ec = res['exec_counts']
    nonnull = [x for x in ec if x is not None]
    res['exec_summary'] = {'code_cells': len(ec), 'null': len(ec) - len(nonnull),
                           'monotonic': nonnull == sorted(nonnull),
                           'min': min(nonnull) if nonnull else None, 'max': max(nonnull) if nonnull else None}
    res['paths'] = sorted(res['paths'])
    del res['exec_counts']
    open(os.path.join(d, 'cells.md'), 'w', encoding='utf-8').write('\n'.join(lines))
    summary[sid] = res

json.dump(summary, open(os.path.join(out, 'scan.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=list)
print(len(summary), 'работ')

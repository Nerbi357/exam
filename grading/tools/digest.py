"""Компактная текстовая выжимка работ для быстрой проверки (без картинок) и автопометки.

Код студентов не выполняется. Запуск: python3 -I grading/tools/digest.py <repo_root> <works_dir>
Пишет <works_dir>/<id>/digest.md и <works_dir>/<id>/auto.md
"""
import json, os, re, subprocess, sys

root, W = sys.argv[1], sys.argv[2]
files = sorted(f for f in os.listdir(root) if f.endswith('.ipynb') or f == 'Спирин.py')
OUT_LIM = 2500


def text_of(x):
    return ''.join(x) if isinstance(x, list) else (x or '')


def clean(s):
    s = re.sub(r'data:image/[a-z+]+;base64,[A-Za-z0-9+/=]+', '[картинка]', s)
    s = re.sub(r'\x1b\[[0-9;]*m', '', s)
    return s


def cut(s, n=OUT_LIM):
    return s if len(s) <= n else s[:n] + f'\n…(обрезано, всего {len(s)} символов)'


MARKERS = {
    1: [r'29710,\s*38', r'29710,\s*39'],
    2: [r'Final/2OT|2OT'],
    3: [r'Buffalo Sabres - Boston Bruins \(4 - 3', r'Vegas Golden Knights - Carolina Hurricanes \(0 - 3'],
    4: [r'5\.92[67]', r'2\.2[56]'],
    6: [r'Tampa Bay Lightning', r'Pittsburgh Penguins', r'9 ?- ?6|6 ?- ?9'],
    7: [r'2025030216', r'\b40\b', r'\b41\b'],
    8: [r'12\.20[67]|12\.21', r'62\.169|62\.17', r'46\.239|46\.24', r'188\.2', r'96\.3[89]'],
    10: [r'0\.625', r'0\.679', r'0\.614', r'0\.531|0\.586|0\.444', r'164'],
    11: [r'0\.706', r'0\.554', r'0\.599', r'0\.609|0\.618'],
    12: [r'31\.667', r'3\.250|3\.25\b', r'23\.263', r'28\.417', r'2\.750|2\.75\b'],
    14: [r'2025030132', r'Final/2OT, 2026-04-20', r'\b208\b'],
    16: [r'Brett Howden\D{0,40}14'],
    17: [r'Jack Eichel\D{0,40}20', r'Mitch Marner\D{0,40}14\b'],
    18: [r'Mitch Marner\D{0,40}29'],
    19: [r'Jason Robertson\D{0,40}5\.0', r'Kucherov\D{0,40}4\.286|Kucherov\D{0,40}4\.29', r'Pastrnak\D{0,40}4\.4\b|Pastrnak\D{0,40}4\.40', r'Clayton Keller\D{0,40}4\.2\b|Clayton Keller\D{0,40}4\.20'],
    20: [r'Lawson Crouse\D{0,40}6\.33', r'Dennis Gilbert', r'Cole Smith'],
}
CODE_MARKERS = {
    5: [r'countplot', r'order\s*=', r'xlabel|set_xlabel|xlabel\s*=', r'ylabel|set_ylabel|ylabel\s*='],
    9: [r'common_norm\s*=\s*False', r"stat\s*=\s*['\"](density|probability|percent)", r'histplot|displot|kdeplot'],
    13: [r'regplot|lmplot|polyfit'],
    15: [r'plot_rink', r'%\s*2|odd|нечет|Defending Side', r'scatterplot|scatter\('],
}
GOALIES = ['Alex Lyon', 'Andrei Vasilevskiy', 'Brandon Bussi', 'Dan Vladar', 'Frederik Andersen', 'Joonas Korpisalo',
           'Scott Wedgewood', 'Ukko-Pekka Luukkonen', 'Arturs Silovs', 'Jakub Dobes']

for f in files:
    sid = os.path.splitext(f)[0]
    d = os.path.join(W, sid)
    os.makedirs(d, exist_ok=True)
    parts, outs, codes, goalie_outs = [], [], [], []
    if f.endswith('.py'):
        src = open(os.path.join(root, f), encoding='utf-8').read()
        pdf = os.path.join(root, 'Спирин_REPORT.pdf')
        txt = subprocess.run(['pdftotext', '-layout', pdf, '-'], capture_output=True, text=True).stdout
        parts.append(f'# {f} (скрипт; выводы и тексты — в отчёте PDF ниже)\n\n```python\n{src}\n```\n')
        parts.append(f'\n# Текст отчёта Спирин_REPORT.pdf (графики не показаны)\n\n{txt}\n')
        outs.append(txt); codes.append(src); goalie_outs.append(txt)
    else:
        nb = json.load(open(os.path.join(root, f), encoding='utf-8'))
        parts.append(f'# {f}\n')
        for i, c in enumerate(nb.get('cells', [])):
            src = clean(text_of(c.get('source')))
            if c['cell_type'] == 'markdown':
                parts.append(f'\n[{i}] MD:\n{src}\n')
                continue
            if c['cell_type'] != 'code':
                continue
            codes.append(src)
            parts.append(f'\n[{i}] CODE In[{c.get("execution_count")}]:\n{src}\n')
            cell_out = []
            for o in c.get('outputs', []):
                ot = o.get('output_type')
                if ot == 'stream':
                    t = clean(text_of(o.get('text')))
                    cell_out.append(t); parts.append('OUT:\n' + cut(t) + '\n')
                elif ot in ('execute_result', 'display_data'):
                    data = o.get('data', {})
                    if any(k.startswith('image/') for k in data):
                        parts.append('[график]\n')
                    if 'text/plain' in data and not any(k.startswith('image/') for k in data):
                        t = clean(text_of(data['text/plain']))
                        if t.startswith('<Figure') or t.startswith('<seaborn') or t.startswith('<Axes') or t.startswith('<matplotlib'):
                            parts.append(f'OUT: {t[:80]}\n')
                        else:
                            cell_out.append(t); parts.append('OUT:\n' + cut(t) + '\n')
                    elif 'text/html' in data and 'text/plain' not in data:
                        t = re.sub(r'<[^>]+>', ' ', text_of(data['text/html']))
                        cell_out.append(t); parts.append('OUT(html):\n' + cut(t) + '\n')
                elif ot == 'error':
                    tb = clean('\n'.join(o.get('traceback', [])))
                    parts.append(f'ОШИБКА {o.get("ename")}: {o.get("evalue")}\n' + '\n'.join(tb.splitlines()[-4:]) + '\n')
            outs.extend(cell_out)
            if 'Goalie' in src:
                goalie_outs.extend(cell_out)
    open(os.path.join(d, 'digest.md'), 'w', encoding='utf-8').write(''.join(parts))
    allout = '\n'.join(outs); allcode = '\n'.join(codes)
    lines = [f'# Автопометки ({sid}) — подсказка, не вердикт; ищется во ВСЕХ выводах/коде тетради\n']
    for k, pats in MARKERS.items():
        lines.append(f'п.{k} выводы: ' + '; '.join(f'«{p}» {"ЕСТЬ" if re.search(p, allout) else "нет"}' for p in pats))
    for k, pats in CODE_MARKERS.items():
        lines.append(f'п.{k} код: ' + '; '.join(f'«{p}» {"ЕСТЬ" if re.search(p, allcode, re.I) else "нет"}' for p in pats))
    go = '\n'.join(goalie_outs)
    lines.append('п.21 имена вратарей в выводах ячеек, где код использует столбцы Goalie: ' + ', '.join(f'{g} {"ЕСТЬ" if g in go else "нет"}' for g in GOALIES))
    try:
        facts = json.load(open(os.path.join(d, 'facts.json'), encoding='utf-8'))
        lines.append('\n# Технические факты\n' + json.dumps(facts, ensure_ascii=False, indent=0))
    except FileNotFoundError:
        pass
    open(os.path.join(d, 'auto.md'), 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
print('ok', len(files))

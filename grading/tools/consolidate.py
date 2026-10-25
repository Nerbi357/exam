"""Сведение результатов быстрой проверки: сверка с прежней проверкой, автопометками и каталог снятий по пунктам.

Запуск: python3 grading/tools/consolidate.py <fast_dir> <reference_grades.json> <works_dir>
"""
import json, os, re, sys
from collections import defaultdict

fast, refp, W = sys.argv[1:4]
ref = json.load(open(refp, encoding='utf-8'))
res = {}
for f in os.listdir(fast):
    if f.endswith('.json') and not f.startswith(('waves', 'pilot')):
        r = json.load(open(os.path.join(fast, f), encoding='utf-8'))
        res[r.get('id') or f[:-5]] = r
print('результатов:', len(res))

# 1. сверка с прежней проверкой (A и B совпали — сильный референс)
print('\n=== Расхождения ≥1 балла с прежней проверкой (A, B) ===')
for wid, r in sorted(res.items()):
    if wid not in ref:
        continue
    for it in r['items']:
        v = ref[wid]['items'].get(str(it['n'])) or ref[wid]['items'].get(it['n'])
        pa, pb = (v['A'] or {}).get('points'), (v['B'] or {}).get('points')
        if pa is None or pb is None:
            continue
        if abs(it['pts'] - pa) >= 1 and abs(it['pts'] - pb) >= 1:
            print(f"{wid[:22]:22s} п.{it['n']:2d}: новый {it['pts']} | A {pa} B {pb} | новое: {it['why'][:90]} | A: {((v['A'] or {}).get('feedback') or '')[:90]}")

# 2. сверка с автопометками
print('\n=== Автопометки против баллов ===')
checks = {1: r'«29710,\\s\*38» ЕСТЬ', 4: r'«5\\.92\[67\]» ЕСТЬ', 8: r'«12\\.20\[67\]\|12\\.21» ЕСТЬ', 10: r'«0\\.625» ЕСТЬ',
          12: r'«31\\.667» ЕСТЬ', 14: r'«2025030132» ЕСТЬ', 16: r'Howden.{0,30}ЕСТЬ', 17: r'Eichel.{0,30}20» ЕСТЬ', 18: r'Marner.{0,30}29» ЕСТЬ'}
for wid, r in sorted(res.items()):
    auto = open(os.path.join(W, wid, 'auto.md'), encoding='utf-8').read()
    for it in r['items']:
        n = it['n']
        if n in checks:
            line = next((l for l in auto.splitlines() if l.startswith(f'п.{n} выводы')), '')
            found = re.search(checks[n], line) is not None
            if found and it['pts'] < it['max'] - 0.75:
                print(f"{wid[:22]:22s} п.{n}: эталон в выводе ЕСТЬ, но {it['pts']}/{it['max']}: {it['why'][:110]}")
            if not found and it['pts'] == it['max'] and n not in (14,):
                print(f"{wid[:22]:22s} п.{n}: эталонного числа в выводе НЕТ, но полный балл")

# 3. каталог снятий по пунктам
print('\n=== Каталог снятий ===')
cat = defaultdict(list)
for wid, r in sorted(res.items()):
    for it in r['items']:
        if it['pts'] < it['max']:
            cat[it['n']].append((it['max'] - it['pts'], wid, it['why']))
for n in sorted(cat):
    print(f'\n-- п.{n}: {len(cat[n])} работ')
    for d, wid, why in sorted(cat[n], key=lambda x: (-x[0], x[1])):
        print(f'   −{d:<4} {wid[:22]:22s} {why[:150]}')

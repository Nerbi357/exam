"""Собирает результаты агентов-проверяющих из журналов workflow в один JSON.

Запуск: python3 grading/tools/aggregate.py <out_json> <journal1> [<journal2> ...]
Для каждой работы: оценки проверяющих A и B, решение арбитра (если было), итог по пунктам.
"""
import ast, json, sys

out, journals = sys.argv[1], sys.argv[2:]
started, results = {}, {}
for j in journals:
    for line in open(j, encoding='utf-8'):
        d = json.loads(line)
        if d.get('type') == 'started':
            started[d['key']] = d.get('label', '')
        elif d.get('type') == 'result':
            r = d['result']
            if isinstance(r, str):
                try:
                    r = json.loads(r)
                except Exception:
                    try:
                        r = ast.literal_eval(r)
                    except Exception:
                        pass
            results[started.get(d['key'], d['key'])] = r

works = {}
for label, r in results.items():
    if ':' not in label:
        continue
    role, wid = label.split(':', 1)
    works.setdefault(wid, {})[role] = r

final = {}
for wid, w in works.items():
    a, b, res = w.get('A'), w.get('B'), w.get('R')
    items = {}
    for i in range(1, 23):
        ia = next((x for x in (a or {}).get('items', []) if x['item'] == i), None)
        ib = next((x for x in (b or {}).get('items', []) if x['item'] == i), None)
        ir = next((x for x in (res or {}).get('items', []) if x['item'] == i), None) if res else None
        if ir is not None:
            items[i] = {'points': ir['points'], 'source': 'R', 'feedback': ir.get('feedback', ''),
                        'comment_status': ir.get('comment_status', ''), 'uncovered': ir.get('uncovered', ''),
                        'reasoning': ir.get('reasoning', ''), 'A': ia, 'B': ib}
        else:
            base = ia or ib
            items[i] = {'points': base['points'] if base else None, 'source': 'A' if ia else 'B',
                        'feedback': (base or {}).get('feedback', ''), 'comment_status': (base or {}).get('comment_status', ''),
                        'uncovered': ' | '.join(x for x in [(ia or {}).get('uncovered', ''), (ib or {}).get('uncovered', '')] if x),
                        'A': ia, 'B': ib}
    ai = (res or {}).get('ai') or None
    final[wid] = {'student_name': (a or b or {}).get('student_name', ''),
                  'items': items,
                  'total': sum((v['points'] or 0) for v in items.values()),
                  'ai_A': (a or {}).get('ai'), 'ai_B': (b or {}).get('ai'), 'ai_R': ai,
                  'injection_A': (a or {}).get('injection'), 'injection_B': (b or {}).get('injection'),
                  'notable_A': (a or {}).get('notable', []), 'notable_B': (b or {}).get('notable', []),
                  'notes_A': (a or {}).get('other_notes', ''), 'notes_B': (b or {}).get('other_notes', ''),
                  'has': sorted(w.keys())}
json.dump(final, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('работ:', len(final))

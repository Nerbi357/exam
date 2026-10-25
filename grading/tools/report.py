"""Сборка итогового отчёта из результатов проверки и правок сведения.

Запуск: python3 grading/tools/report.py <results_dir> <corrections.json> <similarity_rare.json> <out.md>
"""
import json, math, os, re, sys

res_dir, corr_p, sim_p, out = sys.argv[1:5]
corr = json.load(open(corr_p, encoding='utf-8'))
sim = json.load(open(sim_p, encoding='utf-8'))
SIM_T = 45

res = {}
for f in os.listdir(res_dir):
    r = json.load(open(os.path.join(res_dir, f), encoding='utf-8'))
    res[r['id']] = r


def name_of(wid, r):
    if wid in corr['names']:
        return corr['names'][wid]
    m = re.match(r'^(\S+ \S+) - Final Exam$', wid)
    if m:
        return m.group(1)
    n = r.get('student_name', '').strip()
    return n if n and '(' not in n else wid


def fmt(x):
    return str(int(x)) if float(x).is_integer() else str(x).replace('.', ',')


def clean_ai(t):
    rep = [(r'совпадают с эталоном', 'совпадают с верными ответами'), (r'совпадающие с эталоном', 'совпадающие с верными ответами'),
           (r'все эталонные числа совпадают', 'все числа совпадают с верными ответами'), (r'эталонн\w*', 'верные'),
           (r'\(метаданные nbclient/papermill\)', '(по метаданным тетради)'), (r'nbclient/papermill', 'программного запуска'),
           (r'containment', 'доля общих фрагментов'), (r'выполнены программно', 'выполнены одним прогоном'),
           (r'\bэталон\w*', 'верный ответ'), (r'\(программный запуск\)', '(по метаданным тетради)'),
           (r'общ\w* редк\w* 12-грамм\w*', 'общих фрагментов'), (r'12-грамм\w*', 'фрагментов'), (r'\bSedov\b', 'Седов'),
           (r'\bBaev\b', 'Баев'), (r'\bAyana\b', 'Бастаева'), (r'\bSpiridonov\b', 'Спиридонов'), (r'\bToropov\b', 'Торопов'),
           (r'\bUlzutueva\b', 'Улзутуева'), (r'\bDemchenko\b', 'Демченко')]
    for a, b in rep:
        t = re.sub(a, b, t)
    return t.strip()


rows, blocks = [], []
for wid, r in res.items():
    items = {i['n']: dict(i) for i in r['items']}
    for n, (pts, why) in corr['items'].get(wid, {}).items():
        items[int(n)]['pts'] = pts
        items[int(n)]['why'] = why
    total = sum(i['pts'] for i in items.values())
    ai = r['ai']['score']
    ai_text = clean_ai(r['ai']['why'])
    if wid in corr.get('ai_text', {}):
        ai_text = corr['ai_text'][wid]
    if wid in corr['ai']:
        ai, extra = corr['ai'][wid]
        if extra:
            ai_text = ai_text.rstrip('.') + '. ' + extra
    pairs = sorted([(x['b'] if x['a'] == wid else x['a'], x['code_shared_rare']) for x in sim
                    if wid in (x['a'], x['b']) and x['code_shared_rare'] >= SIM_T], key=lambda p: -p[1])
    name = name_of(wid, r)
    if pairs:
        ai_text += ' Совпадения кода выше обычного: ' + '; '.join(
            f'с работой {name_of(o, res[o])} (общих фрагментов: {k}; у большинства пар работ 0–20)' for o, k in pairs) + '.'
    override = corr.get('final_override', {}).get(wid)
    shown = override if override is not None else total
    rows.append((name, shown, ai))
    lines = [f'## {name}', f'**Балл: {fmt(shown)}/100**']
    if override is not None:
        lines.append(f'- Итоговый балл выставлен преподавателем: {fmt(override)}/100 — работа выполнена несамостоятельно '
                     f'(см. оценку подозрения на ИИ ниже). Баллы по пунктам до этого решения: {fmt(total)}/100.')
    lost = [i for i in sorted(items.values(), key=lambda i: i['n']) if i['pts'] < i['max']]
    if lost:
        no_out = [i for i in lost if i['why'].startswith('В тетради нет выводов ячеек')]
        if len(no_out) >= 5:
            lines.append('- ' + ', '.join(f"П.{i['n']} ({fmt(i['pts'])}/{fmt(i['max'])})" for i in no_out)
                         + ': в тетради нет сохранённых выводов ячеек, результаты не видны — в каждом пункте снято 25% от максимума.')
            lost = [i for i in lost if i not in no_out]
        for i in lost:
            lines.append(f"- П.{i['n']} ({fmt(i['pts'])}/{fmt(i['max'])}): {i['why'].strip()}")
    else:
        lines.append('Снятий нет.')
    for rem in corr.get('remarks', {}).get(wid, []):
        lines.append(f'- Замечание без снятия баллов. {rem}')
    lines.append('')
    lines.append(f'Подозрение на ИИ: {ai}/100. {ai_text}')
    blocks.append((name, '\n'.join(lines)))

rows.sort(key=lambda x: x[0])
blocks.sort(key=lambda x: x[0])
md = ['# Проверка экзамена: NHL playoffs 2026', '', '| Студент | Балл | Подозрение на ИИ (0–100) |', '|---|---|---|']
md += [f'| {n} | {fmt(t)} | {a} |' for n, t, a in rows]
md += ['', 'Попытки манипулировать проверяющим: не найдены. Проверены все работы: ключевые слова, скрытые символы, '
       'HTML-комментарии, метаданные тетрадей и ячеек, вложения, картинки в markdown, отчёт Спирина. '
       'Единственная находка, не являющаяся манипуляцией: у Веденеевой Софьи в конце тетради «Спасибо за курс!!» и фото котёнка.',
       '', '---', '']
md += [b + '\n' for _, b in blocks]
open(out, 'w', encoding='utf-8').write('\n'.join(md))
print('студентов:', len(rows), '| средний балл:', round(sum(t for _, t, _ in rows) / len(rows), 1),
      '| средний ИИ:', round(sum(a for _, _, a in rows) / len(rows), 1))

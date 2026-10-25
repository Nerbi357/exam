# Эталон: NHL playoffs 2026

Код: `reference/solution.py`, полный вывод: `reference/solution_output.txt`, рисунки: `reference/fig/`.
Условие: `reference/task/page01.png` … `page10.png`. Правила оценивания: `RULES.md`.

## Данные и ловушки

- 29 710 событий, 82 игры, 16 команд. Первый столбец файла — номер строки: читать с `index_col=0`, иначе 39 столбцов и сдвиг номеров в `iloc` (в примере п.1 `iloc[:10,[2,3,4,9,12]]` → Date, Away Team, Home Team, Remaining Time, Play Type; без `index_col` → Game ID, Date, Away Team, Elapsed Time, Play Length).
- Битая кодировка в трёх именах: `Juraj SlafkovskÃ½`, `Tim StÃ¼tzle`, `Oskar BÃ¤ck` (исправлять не требуется).
- Периоды 1–5: 60 игр в основное время, 18 — в 1-м овертайме, 4 — во 2-м. Ничьих нет. Накопленный счёт не убывает; максимум = последняя строка = число событий goal.
- `Home Team's Defending Side` постоянен внутри периода, но **не определяется чётностью периода**: в 1-м периоде хозяева защищают левые ворота в 31 игре, правые — в 51.
- Вратарь на льду указан и среди `Player on the Ice #1–#6`, и в столбце `Goalie`; пустые места в составе — NaN.
- **Состав и вратари в строке гола — уже после гола** (как на следующем вбрасывании):
  - 34 гола в пустые ворота (в событии перед голом вратаря обороняющейся команды нет), но в строке гола у 31 из них вратарь указан;
  - 5 голов, после которых вратаря сразу заменили: в строке гола уже сменщик;
  - у всех 22 голов в овертайме состав пустой (`# of ... Players on the Ice` = 0, вратари NaN).
  - Правильно: вратарь на льду в момент гола = вратарь в последнем событии этой игры перед голом с непустым составом.
- В событиях shot-on-goal и missed-shot `Player in the Event #2` дублирует `#1` (100 % строк) — вопреки таблице 3. Если сложить #1 и #2 для бросков, каждый бросок посчитается дважды.
- blocked-shot: `Team Making the Play` — бьющая команда, `#1` — блокировавший (обычно соперник), `#2` — бьющий; `Play Zone` — с точки зрения блокировавшего.
- Составы в строках stoppage/penalty тоже записаны «после события». В одном случае (игра 2025030142, P3 17:55) строка delayed-penalty с той же секундой, что и гол, уже несёт состав после гола; ответ п.21 от этого не меняется.
- Ещё 2 гола в концовке (2025030171 P3 18:21 с 132.7 фута, 2025030183 P3 18:27 с 172.6 фута), вероятно, в пустые ворота, но вратарь в данных указан; на ответ п.21 не влияет.
- Смены вратаря по ходу игры — в 10 командо-матчах (2025030112 BUF, 114 BOS, 185 ANA, 215 BUF, 216 BUF и MTL, 233 COL, 235 COL, 243 ANA, 413 CAR).
- Хвост расстояний: 251 бросок дальше 89 футов (со своей половины): 202 в створ, 19 голов, 30 мимо; все из своей (164) или средней (87) зоны, равномерно по периодам (в створ: 70/63/58/9/2 по периодам 1–5).

## Ответы по пунктам

### 1 (2)
`events.shape == (29710, 38)`; первые 10 строк как в примере.

### 2 (6)
Столбцы `Date, Away Team, Home Team, Away Score, Home Score, Outcome`, индекс Game ID. Последние 5 строк совпадают с примером. Outcome: Final 60, Final/OT 18, Final/2OT 4 (по максимальному периоду 3/4/5).

### 3 (3)
Формат: «хозяева - гости (голы хозяев - голы гостей, исход, дата)».
- `gameInfo(2025030111)` → `Buffalo Sabres - Boston Bruins (4 - 3, Final, 2026-04-19)`
- `gameInfo(2025030416)` → `Vegas Golden Knights - Carolina Hurricanes (0 - 3, Final, 2026-06-14)`

### 4 (3)
count 82, mean 5.927, std 2.260, min 1, 25% 5, 50% 6, 75% 7, max 15 — как в примере.

### 5 (5\*)
Высоты столбцов: 1→2, 2→1, 3→9, 4→5, 5→19, 6→16, 7→16, 8→5, 9→5, 10→1, 11→2, 12–14→0, 15→1 (как рис. 1).
Комментарий по существу: распределение унимодальное, чаще всего 5–7 голов (51 матч из 82), мода 5; скошено вправо, один выброс — 15 голов (Colorado – Minnesota 9:6); матчей с 1–2 голами мало.

### 6 (3)
- Наименьшее (1 гол, 2 игры): `Montréal Canadiens - Tampa Bay Lightning (0 - 1, Final/OT, 2026-05-01)`, `Philadelphia Flyers - Pittsburgh Penguins (1 - 0, Final/OT, 2026-04-29)`
- Наибольшее (15): `Colorado Avalanche - Minnesota Wild (9 - 6, Final, 2026-05-03)`

### 7 (5)
Максимум — игра 2025030216 `Montréal Canadiens - Buffalo Sabres (3 - 8, Final, 2026-05-16)`: **40** игроков. Следом 39: 2025030112, 2025030215, 2025030413, 2025030235.
- 41 (как в примере) получается, если NaN посчитать игроком (`pd.unique`, `nunique(dropna=False)`, `len(set(...))` с NaN). Игра та же.
- Учёт или неучёт столбцов `Goalie` ответ не меняет (вратари есть в `#1–#6`).
- Ошибка «сумма `nunique` по столбцам»: max 141, игра 2025030233.

### 8 (7)
`Shot Length` для 7 266 бросков (shot-on-goal, goal, missed-shot); ворота: хозяева бьют в правые (X=89), если `Defending Side == left`, иначе в левые; гости — наоборот. Значения из примера: строки 7→12.207, 9→12.000, 12→29.411, 13→62.169, 19→52.924, …, 29704→46.239, 29707→49.041. Описательные: mean 35.409, median 31.898, max 188.215.
- Ворота по знаку X: отличаются 212 бросков, max 96.385 (хвост пропадает).
- До центра ворот (без учёта ширины створа): среднее 36.793 вместо 35.409.
- Перепутаны ворота хозяев/гостей: среднее ≈ 148.9.

### 9 (6\*)
Гистограммы `Shot Length` по группам «on goal» (shot-on-goal + goal, 4 623) и «missed» (2 643), нормированные отдельно (`stat='density', common_norm=False` или `displot(..., stat='density', common_norm=False)`), вид как рис. 3.
Вывод: распределения похожи (медианы 31.8 и 32.2 фута), с близкой дистанции броски чаще точные, на 50–70 футах больше промахов; у точных — длинный хвост за 89 футов (4.8 % точных против 1.1 % неточных).
Почему хвост: броски/выбросы шайбы из своей и средней зоны — если шайба летит в створ, вратарь её ловит и бросок засчитывается как «в створ»; если мимо — обычно это проброс (icing), а не missed-shot; плюс голы в пустые ворота в концовках (19 голов из хвоста). Рис. 3 в условии, судя по высотам, построен с шириной корзины 5 футов; у seaborn по умолчанию ~3.3 фута — форма та же.

### 10 (5\*)
`Share = (shot-on-goal + goal) / (shot-on-goal + goal + missed-shot)` по каждой команде в каждой игре, 164 значения; первые/последние совпадают с примером (0.625, 0.679, 0.614, 0.636, 0.694 … 0.583, 0.558, 0.510, 0.639, 0.595). Среднее 0.639, медиана 0.639, std 0.085, min 0.353, max 0.860; ниже 0.5 — в 6 случаях.
Вывод: обычно 55–70 % незаблокированных бросков попадают в створ, разброс между играми заметный.
- Голы не в числителе: 0.531, 0.607, 0.523, …
- Без голов вообще (sog / (sog + miss)): 0.586, 0.654, 0.575, …
- С blocked в знаменателе: 0.444, 0.543, 0.466, …

### 11 (4\*)
Среднее по матчам: top-5 Edmonton 0.706, Philadelphia 0.684, Dallas 0.670, Minnesota 0.656, Colorado 0.653; bottom-5 Pittsburgh 0.554, Utah 0.599, Carolina 0.615, Tampa Bay 0.626, Buffalo 0.626.
- Вариант Σ/Σ (принимается): top те же 5 (0.700, 0.681, 0.669, 0.657, 0.649); bottom Pittsburgh 0.554, Utah 0.609, Carolina 0.613, Ottawa 0.618, Tampa Bay 0.624.
Комментарий по существу: разброс между командами небольшой (0.55–0.71); точность бросков не определяет успех (Carolina — финалист и чемпион — в нижней пятёрке) и т. п.

### 12 (5)
Shot = shot-on-goal + goal, среднее по всем играм команды:

| Команда | Shot | Goal |
|---|---|---|
| Anaheim Ducks | 31.667 | 3.250 |
| Boston Bruins | 25.167 | 2.000 |
| Buffalo Sabres | 30.462 | 3.308 |
| Carolina Hurricanes | 31.632 | 3.474 |
| Colorado Avalanche | 32.154 | 3.385 |
| Dallas Stars | 31.000 | 2.500 |
| Edmonton Oilers | 28.333 | 3.500 |
| Los Angeles Kings | 25.250 | 1.250 |
| Minnesota Wild | 28.727 | 3.727 |
| Montréal Canadiens | 23.263 | 2.842 |
| Ottawa Senators | 27.500 | 1.250 |
| Philadelphia Flyers | 24.600 | 2.100 |
| Pittsburgh Penguins | 26.500 | 1.833 |
| Tampa Bay Lightning | 28.000 | 2.143 |
| Utah Mammoth | 27.833 | 3.000 |
| Vegas Golden Knights | 26.545 | 3.455 |

- Shot без голов: Anaheim 28.417, Boston 23.167, Buffalo 27.154, Carolina 28.158, …
- Голы только по матчам, где команда забивала: завышены Montréal (+0.334), Ottawa (+0.417), Philadelphia (+0.233), Pittsburgh (+0.917), Vegas (+0.165).

### 13 (5\*)
`regplot` по 16 точкам п.12. r = 0.521 (p = 0.039), наклон ≈ 0.156 гола на бросок. Spearman ρ = 0.578. Если из Shot убрать голы, r = 0.250 — часть связи механическая (голы входят в броски). Связь положительная, умеренная, но разброс большой (Montréal, Ottawa, Minnesota, Vegas далеко от линии), доверительная полоса широкая, точек мало — допустим и ответ «связь есть, но слабая/неустойчивая».

### 14 (3)
`Carolina Hurricanes - Ottawa Senators (3 - 2, Final/2OT, 2026-04-20)` (2025030132), 208 бросков (83 в створ, 66 мимо, 54 blocked, 5 голов). Без голов (203), без blocked (154), только sog+goal (88) — та же игра.

### 15 (9)
Игра 2025030132, 208 точек (Carolina 109, Ottawa 99). Defending Side хозяев по периодам: right, left, right, left, right ⇒ зеркалирование нечётных периодов ровно совпадает с зеркалированием по Defending Side. После преобразования броски хозяев (Carolina) справа (98 %), гостей (Ottawa) слева (99 %); вид как рис. 5. Эталонный рисунок: `reference/fig/p15_rink.png`.

### 16 (2)
Brett Howden 14, Pavel Dorofeyev 12, Logan Stankoven 11, Mitch Marner 10, Nikolaj Ehlers 8, Jordan Staal 8, затем по 7: Alex Newhook, Taylor Hall, Jackson Blake, Nathan MacKinnon, Matt Boldy, Mark Stone (6 игроков на места 7–12 — любые 4 из них верны).

### 17 (3)
Jack Eichel 20, Mitch Marner 19, Lane Hutson 13, Jackson Blake 13, Nick Suzuki 12, Taylor Hall 12, Martin Necas 12, Shea Theodore 12, Kirill Kaprizov 11, Quinn Hughes 11 (на границе ничьей нет: 11-е место — 10).
- Только #2: Marner 14, Eichel 11, Necas 9, Hutson 8, Hall 8, Suzuki 7, MacKinnon 7, Dahlin 6, Ehlers 6, K'Andre Miller 6.

### 18 (3)
Mitch Marner 29, Jack Eichel 22, Jackson Blake 20, Taylor Hall 19, Brett Howden 18, Shea Theodore 18, Nikolaj Ehlers 18, затем по 16: Nick Suzuki, Pavel Dorofeyev, Lane Hutson, Logan Stankoven (4 игрока на места 8–11 — любые 3 из них верны).

### 19 (4)
Основной вариант: (shot-on-goal + goal) Player #1 / число игр, где игрок был на льду:
Jason Robertson 5.000 (30/6), Dylan Guenther 4.500 (27/6), Nikita Kucherov 4.429 (31/7), Matt Boldy 4.364 (48/11), Quinton Byfield 4.250 (17/4), Darren Raddysh 4.000 (28/7), Joel Eriksson Ek 4.000 (24/6), Alex Laferriere 3.750 (15/4), David Pastrnak 3.667 (22/6), Nathan MacKinnon 3.615 (47/13).
- Только shot-on-goal, игры на льду: Kucherov 4.286, Byfield 4.250, Robertson 4.167, Guenther 4.000, Raddysh 3.857, Laferriere 3.750, Boldy 3.727, Eriksson Ek 3.500, Clayton Keller 3.333, Alex Tuch / Rasmus Dahlin 3.231.
- Знаменатель «игры команды» (sog + goal): совпадает с основным в первых 9, далее MacKinnon 3.615, Dahlin 3.538.
- Знаменатель «только игры с броском» (завышает, −1): Robertson 5.0, Guenther 4.5, Kucherov 4.429, Pastrnak 4.4, Boldy 4.364, Byfield 4.25, Keller 4.2, Carlsson 4.1, Raddysh 4.0, Eriksson Ek 4.0.

### 20 (3)
hit Player #1 / игры на льду: Lawson Crouse 6.333 (38/6), Alexander Petrovic 6.000 (6/1), Alex Turcotte 6.000 (6/1), Yakov Trenin 5.667 (51/9), Dylan Cozens 5.500 (22/4), Vasily Podkolzin 5.333 (32/6), Ivan Barbashev 5.000 (110/22), Carl Grundstrom 5.000 (15/3), Marcus Foligno 5.000 (55/11), Owen Tippett 4.833 (29/6).
- «Игры команды»: Crouse 6.333, Cozens 5.5, Podkolzin 5.333, Barbashev 5.0, Foligno 5.0, Carrier 4.789, Trenin 4.636, Cole Smith 4.545, Jordan Staal 4.526, Laferriere 4.5 (принимается).
- «Только игры с hit» (−1): Crouse 6.333, Petrovic 6.0, Turcotte 6.0, Trenin 5.667, Cozens 5.5, Dennis Gilbert 5.5, Podkolzin 5.333, MacKenzie Weegar 5.2, Carrier 5.056, Grundstrom 5.0.

### 21 (7)
**Верно (8 вратарей):** Alex Lyon, Andrei Vasilevskiy, Brandon Bussi, Dan Vladar, Frederik Andersen, Joonas Korpisalo, Scott Wedgewood, Ukko-Pekka Luukkonen.

| Game ID | Команда | Вратарь | Игра |
|---|---|---|---|
| 2025030112 | Buffalo | Alex Lyon (вышел на замену) | Buffalo Sabres - Boston Bruins (2 - 4, Final, 2026-04-21) |
| 2025030114 | Boston | Joonas Korpisalo (вышел на замену) | Boston Bruins - Buffalo Sabres (1 - 6, Final, 2026-04-26) |
| 2025030126 | Tampa Bay | Andrei Vasilevskiy | Montréal Canadiens - Tampa Bay Lightning (0 - 1, Final/OT, 2026-05-01) |
| 2025030131 | Carolina | Frederik Andersen | Carolina Hurricanes - Ottawa Senators (2 - 0, Final, 2026-04-18) |
| 2025030142 | Philadelphia | Dan Vladar | Pittsburgh Penguins - Philadelphia Flyers (0 - 3, Final, 2026-04-20) |
| 2025030146 | Philadelphia | Dan Vladar | Philadelphia Flyers - Pittsburgh Penguins (1 - 0, Final/OT, 2026-04-29) |
| 2025030216 | Buffalo | Ukko-Pekka Luukkonen (вышел на замену) | Montréal Canadiens - Buffalo Sabres (3 - 8, Final, 2026-05-16) |
| 2025030221 | Carolina | Frederik Andersen | Carolina Hurricanes - Philadelphia Flyers (3 - 0, Final, 2026-05-02) |
| 2025030235 | Colorado | Scott Wedgewood | Colorado Avalanche - Minnesota Wild (4 - 3, Final/OT, 2026-05-13) |
| 2025030314 | Carolina | Frederik Andersen | Montréal Canadiens - Carolina Hurricanes (0 - 4, Final, 2026-05-27) |
| 2025030416 | Carolina | Brandon Bussi | Vegas Golden Knights - Carolina Hurricanes (0 - 3, Final, 2026-06-14) |

Типичные варианты (шкала — в RULES.md):
- вратарь из строки гола: Vasilevskiy, **Arturs Silovs**, Bussi, Vladar, Andersen, **Jakub Dobes**, Korpisalo, Wedgewood — лишние Silovs (2025030146) и Dobes (2025030126) — их единственный пропущенный гол был в овертайме, где состав пустой; нет Lyon и Luukkonen — гол, после которого их выпустили, записан на них; у Bussi лишний матч 2025030413 (4/7);
- строка гола + овертаймы исправлены: Vasilevskiy, Bussi, Vladar, Andersen, Korpisalo, Wedgewood — нет Lyon и Luukkonen (5/7);
- «сухие» матчи команды: Vasilevskiy, Bussi, Vladar, Andersen (3/7);
- голы в пустые ворота засчитать вратарю команды — список не меняется;
- вратарь из последнего события строго раньше по времени (а не просто предыдущей строки) — список тот же.

Три независимых решения (эталон и два агента) дали одинаковый список.

### 22 (7\*)
Свободный вопрос. Пример эталона (совпал у двух независимых решателей): команда, забившая первой, выиграла 56 из 82 матчей (68.3 %); хозяева выиграли 39 из 82 (47.6 %), но в овертаймах — 14 из 22; команда, лидировавшая после двух периодов, выиграла 46 из 57. Голы по периодам: 145 / 150 / 169 / 18 / 4; все голы в пустые ворота — в 3-м периоде.

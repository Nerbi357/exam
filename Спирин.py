# Финальный экзамен - Анализ данных в Python
# Спирин Г.В.

import os
import sys
import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.ticker import MaxNLocator

from rink import plot_rink

warnings.filterwarnings('ignore')

# Работаем из папки скрипта (там лежат данные и rink.py), откуда бы его ни запустили
if '__file__' in globals():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
# Чтобы имена с диакритикой (Montréal) печатались без ошибок даже при выводе в файл
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Times New Roman', 'DejaVu Serif']
plt.rcParams['font.size'] = 12
os.makedirs('figures', exist_ok=True)


def header(number, title):
    print(f'\n========== Пункт {number}. {title} ==========')


def save_figure(fig, name):
    fig.savefig(f'figures/{name}.pdf', bbox_inches='tight')
    fig.savefig(f'figures/{name}.png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'График сохранён: figures/{name}.pdf')


# Пункт 1
header(1, 'Чтение данных')
events = pd.read_excel('NHL-playoffs-2026.xlsx', index_col=0)
print('events.shape =', events.shape)
print(events.iloc[:10, [2, 3, 4, 9, 12]])

player_cols = (
    [f"Away Team's Player on the Ice #{i}" for i in range(1, 7)] + ["Away Team's Goalie"] +
    [f"Home Team's Player on the Ice #{i}" for i in range(1, 7)] + ["Home Team's Goalie"]
)
event_player_cols = ['Player in the Event #1', 'Player in the Event #2', 'Player in the Event #3']


# В трёх именах в файле битая кодировка (UTF-8, прочитанный как Latin-1):
# 'Juraj SlafkovskÃ½' вместо 'Juraj Slafkovský' и т.п. Исправляем обратным преобразованием.
def fix_encoding(name):
    if isinstance(name, str) and 'Ã' in name:
        try:
            return name.encode('latin-1').decode('utf-8')
        except UnicodeError:
            return name
    return name


all_names = pd.unique(events[player_cols + event_player_cols].values.ravel())
fixed_names = {n: fix_encoding(n) for n in all_names if isinstance(n, str) and fix_encoding(n) != n}
for col in player_cols + event_player_cols:
    events[col] = events[col].map(fix_encoding)
print()
print('Исправлена кодировка имён:', fixed_names)

# Пункт 2
header(2, 'Сводная таблица по играм')
outcome_map = {3: 'Final', 4: 'Final/OT', 5: 'Final/2OT', 6: 'Final/3OT', 7: 'Final/4OT'}

games = events.groupby('Game ID').agg(
    Date=('Date', 'first'),
    **{'Away Team': ('Away Team', 'first')},
    **{'Home Team': ('Home Team', 'first')},
    **{'Away Score': ('Cumulated Away Score', 'max')},
    **{'Home Score': ('Cumulated Home Score', 'max')},
    MaxPeriod=('Period', 'max'),
)
games['Outcome'] = games['MaxPeriod'].map(outcome_map)
games = games.drop(columns='MaxPeriod')

print('games.columns =', games.columns.tolist())
print(games.iloc[-5:, -4:])


# Пункт 3
def gameInfo(gameId):
    g = games.loc[gameId]
    return (f"{g['Home Team']} - {g['Away Team']} "
            f"({g['Home Score']} - {g['Away Score']}, {g['Outcome']}, {g['Date']})")


header(3, 'Функция gameInfo')
print(gameInfo(games.index.min()))
print(gameInfo(games.index.max()))

# Пункт 4
header(4, 'Сколько всего шайб забито в каждой игре')
games['Total Score'] = games['Away Score'] + games['Home Score']
print(games['Total Score'].describe())

# Пункт 5
header(5, 'Гистограмма числа голов в матче')
fig, ax = plt.subplots(figsize=(10, 6))
# Показываем все значения от минимума до максимума, включая пустые 12-14 гола,
# иначе столбец "15" встанет вплотную к "11" и хвост распределения исказится.
score_range = list(range(games['Total Score'].min(), games['Total Score'].max() + 1))
sns.countplot(x=games['Total Score'], order=score_range, color='steelblue', ax=ax)
ax.yaxis.set_major_locator(MaxNLocator(integer=True))
ax.set_xlabel('Число голов')
ax.set_ylabel('Число матчей')
save_figure(fig, 'total_score_hist')

score_counts = games['Total Score'].value_counts()
typical = games['Total Score'].between(5, 7)
print(f"""
Комментарий: распределение одновершинное. Чаще всего за матч забивали
{score_counts.idxmax()} голов ({score_counts.max()} матчей из {len(games)}), ещё по 16 матчей закончились с 6 и 7
голами, а всего матчей с 5-7 голами - {typical.sum()} из {len(games)} ({typical.mean():.0%}). Среднее ({games['Total Score'].mean():.2f})
и медиана ({games['Total Score'].median():.0f}) почти совпадают: типичный матч этого плей-офф - 5-7 голов
на двоих. Слева небольшой хвост из трёх очень скупых матчей с 1-2 голами
(оба матча с одним голом закончились 1:0 в овертайме, см. пункт 6).
Справа - редкие голевые перестрелки: три матча с 10-11 голами и один явный
выброс в 15 голов (Colorado Avalanche - Minnesota Wild, 9 - 6); матчей с
12-14 голами не было.
""")

# Пункт 6
header(6, 'Самые нерезультативные и самые результативные игры')
min_score = games['Total Score'].min()
print([gameInfo(gid) for gid in games[games['Total Score'] == min_score].index])
max_score = games['Total Score'].max()
print([gameInfo(gid) for gid in games[games['Total Score'] == max_score].index])

# Пункт 7
header(7, 'Игры с наибольшим числом участвовавших игроков')
# Все 14 колонок состава (6 полевых + вратарь у каждой команды) переводим в один
# столбец и для каждой игры считаем число разных непустых имён.
lineup = events[['Game ID'] + player_cols].melt(id_vars='Game ID', value_name='Player')
player_counts = lineup.dropna(subset=['Player']).groupby('Game ID')['Player'].nunique()
player_counts.name = 'Player Count'

most_players = player_counts[player_counts == player_counts.max()].to_frame()
most_players.insert(0, 'Game Info', [gameInfo(gid) for gid in most_players.index])
print(most_players)

# Сверка с примером из задания (там 41): посчитаем то же самое, но с NaN
with_nan = lineup.groupby('Game ID')['Player'].nunique(dropna=False)
print()
print(f'Если считать пустое значение NaN отдельным "игроком": {with_nan.max()} (игра {with_nan.idxmax()})')
print(f'Разница "с NaN" минус "без NaN" по всем {len(player_counts)} играм:',
      (with_nan - player_counts).unique().tolist())
print("""
Комментарий: в примере из задания для игры 2025030216 указано 41, у меня 40.
Разница ровно в одно значение: пустая ячейка NaN (например, при игре в
меньшинстве на льду 5 игроков и колонка #6 пустая) - это не игрок, но
pd.unique() считает NaN отдельным уникальным значением. Если посчитать так
же, получается ровно 41 для той же игры, причём разница равна 1 во всех 82
играх. Поэтому правильный ответ - 40 разных игроков, а игра та же самая.
""")

# Пункт 8
header(8, 'Расстояние до ворот')
shots = events[events['Play Type'].isin(['shot-on-goal', 'goal', 'missed-shot'])].copy()

is_home_shooter = shots['Team Making the Play'] == shots['Home Team']
defends_left = shots["Home Team's Defending Side"] == 'left'

# Defending Side == 'left' -> хозяева бьют в X=89, гости в X=-89.
# Defending Side == 'right' -> наоборот.
goal_x = np.where(
    is_home_shooter,
    np.where(defends_left, 89, -89),
    np.where(defends_left, -89, 89),
)

x = shots['X Coordinate on the Ice Rink'].values
y = shots['Y Coordinate on the Ice Rink'].values

dy = np.where(y < -3, y + 3, np.where(y > 3, y - 3, 0))
shots['Shot Length'] = np.sqrt((x - goal_x) ** 2 + dy ** 2)

print(shots[['Game ID', 'Play Type', 'Shot Length']])

# Пункт 9
header(9, 'Распределение длины точных и неточных бросков')
shots['Shot'] = shots['Play Type'].map({'missed-shot': 'missed', 'shot-on-goal': 'on goal', 'goal': 'on goal'})

g3 = sns.displot(shots, x='Shot Length', hue='Shot', stat='density', common_norm=False,
                 kde=True, height=5, aspect=1.6, bins=30)
g3.set_axis_labels('Shot length, feet', 'Frequency')
save_figure(g3.figure, 'shot_length_hist')

median_length = shots.groupby('Shot')['Shot Length'].median()
dist_groups = pd.cut(shots['Shot Length'], bins=[0, 10, 30, 50, 70, 89, 200],
                     labels=['0-10', '10-30', '30-50', '50-70', '70-89', '89+'], include_lowest=True)
dist_share = pd.crosstab(dist_groups, shots['Shot'], normalize='columns')
print()
print('Медиана длины броска, футы:', median_length.round(1).to_dict())
print('Доля бросков каждой группы по дистанциям, футы:')
print(dist_share.round(3))

# Хвост: точные броски дальше 100 футов
far = shots[shots['Shot Length'] > 100]
far_saved = far[far['Play Type'] == 'shot-on-goal']
far_goals = far[far['Play Type'] == 'goal']
remaining_sec = pd.to_timedelta('00:' + far_goals['Remaining Time']).dt.total_seconds()
scorer_is_home = far_goals['Team Making the Play'] == far_goals['Home Team']
lead_after_goal = np.where(scorer_is_home,
                           far_goals['Cumulated Home Score'] - far_goals['Cumulated Away Score'],
                           far_goals['Cumulated Away Score'] - far_goals['Cumulated Home Score'])
late_goals = ((far_goals['Period'] == 3) & (remaining_sec <= 180)).sum()
saved_by_period = far_saved['Period'].value_counts()
print()
print('Броски дальше 100 футов:', far['Play Type'].value_counts().to_dict())
print('  отбитые вратарём (shot-on-goal) по периодам:', far_saved['Period'].value_counts().sort_index().to_dict())
print('  отбитые вратарём по зоне броска:', far_saved['Play Zone'].value_counts().to_dict())
print(f'  голы: всего {len(far_goals)}, в последние 3 минуты 3-го периода - {late_goals}, '
      f'забиты командой, которая уже вела в счёте, - {(lead_after_goal >= 2).sum()}')

print(f"""
Комментарий: распределения точных и неточных бросков очень похожи:
медианы почти совпадают ({median_length['on goal']:.1f} и {median_length['missed']:.1f} фута), основная масса
бросков обеих групп - ближе 70 футов. Отличия небольшие: у точных бросков
чуть больше доля самых коротких бросков, до 10 футов ({dist_share.loc['0-10', 'on goal']:.1%} против {dist_share.loc['0-10', 'missed']:.1%}),
у неточных - бросков с 50-70 футов ({dist_share.loc['50-70', 'missed']:.1%} против {dist_share.loc['50-70', 'on goal']:.1%}). Главное
отличие - хвост: со своей половины площадки (дальше 89 футов) сделано
{dist_share.loc['89+', 'on goal']:.1%} точных бросков и только {dist_share.loc['89+', 'missed']:.1%} неточных.

Почему такой хвост. Дальше 100 футов {len(far) - (far['Shot'] == 'missed').sum()} точных бросков и всего {(far['Shot'] == 'missed').sum()} неточных.
{len(far_saved)} из этих {len(far) - (far['Shot'] == 'missed').sum()} - не голы, а броски, которые вратарь остановил. Они идут
равномерно по всему матчу (1-й период - {saved_by_period.get(1, 0)}, 2-й - {saved_by_period.get(2, 0)}, 3-й - {saved_by_period.get(3, 0)},
овертаймы - {saved_by_period[saved_by_period.index > 3].sum()}), и {(far_saved['Play Zone'] == 'Defensive').mean():.0%} из них сделаны из своей зоны защиты:
это выбросы шайбы из своей зоны. Если такая шайба долетела до ворот и
вратарь её поймал, в протоколе это бросок в створ, а выброс мимо ворот,
по-видимому, вообще не записывается как бросок - поэтому у неточных бросков
хвоста почти нет. Остальные {len(far_goals)} - голы, и почти все они - голы в пустые
ворота: {late_goals} из {len(far_goals)} забиты в последние 3 минуты 3-го периода, и все {(lead_after_goal >= 2).sum()} -
командой, которая уже вела в счёте (проигрывающая команда в концовке меняет
вратаря на шестого полевого игрока).
""")

# Пункт 10
header(10, 'Доля точных бросков у каждой команды в каждой игре')
unblocked = events[events['Play Type'].isin(['shot-on-goal', 'goal', 'missed-shot'])].copy()
unblocked['is_on_goal'] = unblocked['Play Type'].isin(['shot-on-goal', 'goal'])

numshots = unblocked.groupby(['Game ID', 'Team Making the Play'])['is_on_goal'].mean()
numshots = numshots.to_frame('Share of Shots on Goal')
print(numshots['Share of Shots on Goal'].round(3))

share = numshots['Share of Shots on Goal']
print()
print(share.describe().round(3))
by_team = share.groupby(level='Team Making the Play')
within_std = by_team.std().mean()
between_std = by_team.mean().std()
print(f'Разброс доли от игры к игре внутри одной команды (средний std): {within_std:.3f}')
print(f'Разброс средних долей между командами (std): {between_std:.3f}')

# Связь с результатом: сравниваем победителя и проигравшего в каждой игре
winner = pd.Series(np.where(games['Home Score'] > games['Away Score'], games['Home Team'], games['Away Team']),
                   index=games.index)
share_df = share.reset_index()
share_df['Won'] = share_df['Team Making the Play'] == share_df['Game ID'].map(winner)
won_share = share_df[share_df['Won']].set_index('Game ID')['Share of Shots on Goal'].sort_index()
lost_share = share_df[~share_df['Won']].set_index('Game ID')['Share of Shots on Goal'].sort_index()
n_winner_more_accurate = (won_share > lost_share).sum()
print(f'Средняя доля точных бросков: у победителей {won_share.mean():.3f}, у проигравших {lost_share.mean():.3f}')
print(f'Победитель бросал точнее соперника в {n_winner_more_accurate} из {len(won_share)} игр')

print(f"""
Комментарий: в среднем в створ попадает около {share.mean():.0%} незаблокированных
бросков команды, но от игры к игре доля сильно скачет: от {share.min():.2f} до {share.max():.2f},
у половины значений - от {share.quantile(0.25):.2f} до {share.quantile(0.75):.2f}. Разброс внутри одной команды
от игры к игре (std {within_std:.3f}) более чем вдвое больше, чем разница между
средними уровнями команд (std {between_std:.3f}), поэтому по одной игре судить о
точности команды нельзя - нужно усреднять по всем играм (пункт 11).
С результатом матча точность почти не связана: победитель бросал точнее
соперника только в {n_winner_more_accurate} из {len(won_share)} игр, а средняя доля у победителей
({won_share.mean():.3f}) даже немного ниже, чем у проигравших ({lost_share.mean():.3f}). Вывод: доля
бросков в створ сама по себе не определяет, кто выиграет матч.
""")

# Пункт 11
header(11, 'Пять команд с самыми высокими и самыми низкими средними долями')
avgnumshots = numshots['Share of Shots on Goal'].groupby(level='Team Making the Play').mean()
print('=== Топ-5 по доле точных бросков ===')
print(avgnumshots.nlargest(5))
print()
print('=== Антитоп-5 по доле точных бросков ===')
print(avgnumshots.nsmallest(5))

games_per_team = by_team.size()
wins_per_team = winner.value_counts().reindex(avgnumshots.index, fill_value=0)
team_table = pd.DataFrame({'Share': avgnumshots, 'Games': games_per_team, 'Wins': wins_per_team})
median_distance = shots.groupby('Team Making the Play')['Shot Length'].median()
corr_wins = avgnumshots.corr(wins_per_team / games_per_team)
corr_distance = avgnumshots.corr(median_distance)
print()
print(team_table.sort_values('Share', ascending=False).round(3))
print(f'Корреляция средней доли точных бросков с долей побед: {corr_wins:.2f}')
print(f'Корреляция средней доли точных бросков с медианной дистанцией броска: {corr_distance:.2f}')

rank = avgnumshots.rank(ascending=False).astype(int)
print(f"""
Комментарий: точнее всех бросает Edmonton Oilers ({avgnumshots['Edmonton Oilers']:.3f}), хуже всех -
Pittsburgh Penguins ({avgnumshots['Pittsburgh Penguins']:.3f}). Но к этим цифрам надо относиться осторожно:
у {(games_per_team <= 6).sum()} команд из 16 всего 4-6 игр (у Edmonton и Pittsburgh - по 6), а в
пункте 10 видно, что от игры к игре доля сильно скачет. С успехом в плей-офф
точность не связана: чемпион Carolina Hurricanes - в пятёрке худших
({avgnumshots['Carolina Hurricanes']:.3f}, {rank['Carolina Hurricanes']}-е место из 16), финалист Vegas Golden Knights - на {rank['Vegas Golden Knights']}-м месте,
а лучший по точности Edmonton выиграл только {wins_per_team['Edmonton Oilers']} матча из {games_per_team['Edmonton Oilers']} и вылетел в
первом раунде. Корреляция средней доли с долей побед около нуля ({corr_wins:.2f}).
Связи с дистанцией бросков тоже нет (корреляция с медианной дистанцией
{corr_distance:.2f}), то есть дело не в том, что лучшие бросают ближе. Вывод: различия
между командами по точности небольшие и во многом случайные, а на результат
сильнее влияет, сколько команда бросает (пункты 12-13).
""")

# Пункт 12
header(12, 'Среднее число бросков в створ и голов за игру')
# Полный список пар (Game ID, команда) для всех игр, где команда реально
# играла - нужен, чтобы не терять игры с 0 бросками/голами при усреднении.
team_games = pd.concat([
    games.reset_index()[['Game ID', 'Away Team']].rename(columns={'Away Team': 'Team'}),
    games.reset_index()[['Game ID', 'Home Team']].rename(columns={'Home Team': 'Team'}),
])

shot_events = events[events['Play Type'].isin(['shot-on-goal', 'goal'])]
goal_events = events[events['Play Type'] == 'goal']

shots_per_game = shot_events.groupby(['Game ID', 'Team Making the Play']).size()
goals_per_game = goal_events.groupby(['Game ID', 'Team Making the Play']).size()

full_idx = pd.MultiIndex.from_frame(team_games, names=['Game ID', 'Team Making the Play'])
shots_full = shots_per_game.reindex(full_idx, fill_value=0)
goals_full = goals_per_game.reindex(full_idx, fill_value=0)

avgshots = pd.DataFrame({
    'Shot': shots_full.groupby(level='Team Making the Play').mean(),
    'Goal': goals_full.groupby(level='Team Making the Play').mean(),
})
print(avgshots.round(3))

# Пункт 13
header(13, 'Связь числа бросков в створ и голов')
corr = avgshots['Shot'].corr(avgshots['Goal'])
slope, intercept = np.polyfit(avgshots['Shot'], avgshots['Goal'], 1)
residuals = avgshots['Goal'] - (slope * avgshots['Shot'] + intercept)

# Перестановочный тест: 10 000 раз случайно перемешиваем броски между командами
# и смотрим, как часто случайно получается корреляция не слабее найденной.
rng = np.random.default_rng(0)
perm_corr = np.array([np.corrcoef(rng.permutation(avgshots['Shot'].values), avgshots['Goal'].values)[0, 1]
                      for _ in range(10000)])
p_value = (np.abs(perm_corr) >= abs(corr)).mean()
print(f'Корреляция: {corr:.3f}, R^2: {corr ** 2:.3f}, наклон: {slope:.3f} гола на 1 бросок, p-value: {p_value:.3f}')
print('Отклонения от линии регрессии (голов за игру):')
print(residuals.sort_values().round(2))

fig, ax = plt.subplots(figsize=(9, 6))
sns.regplot(data=avgshots, x='Shot', y='Goal', ax=ax)
for team, row in avgshots.iterrows():
    ax.annotate(team, (row['Shot'], row['Goal']), fontsize=8,
                xytext=(3, 3), textcoords='offset points')
ax.set_xlabel('Average number of shots on goal per game')
ax.set_ylabel('Average number of goals per game')
save_figure(fig, 'shots_goals_regression')

print(f"""
Комментарий: связь видна - линия регрессии идёт вверх, корреляция {corr:.3f}; в среднем
каждый дополнительный бросок в створ за игру даёт примерно +{slope:.2f} гола за игру.
Но связь умеренная: R^2 = {corr ** 2:.2f}, то есть число бросков объясняет только около
четверти различий в голах между командами, а доверительная полоса широкая -
точек всего 16. Перестановочный тест даёт p-value = {p_value:.3f}: случайно такая
связь получается редко, так что на уровне 5% её можно считать значимой, хотя
и на грани. Сильнее всего от линии отклоняются Vegas Golden Knights, Minnesota
Wild и Montréal Canadiens (забивают примерно на гол за игру больше, чем
"положено" при их числе бросков), а также Ottawa Senators и Los Angeles Kings
(на 1-1.35 гола меньше). Значит, кроме количества бросков, важна их
реализация: качество моментов и игра вратарей соперника.
""")

# Пункт 14
header(14, 'Матч с наибольшим числом ударов по воротам')
all_attempts = events[events['Play Type'].isin(['shot-on-goal', 'goal', 'missed-shot', 'blocked-shot'])]
attempts_per_game = all_attempts.groupby('Game ID').size()
idxmax = attempts_per_game.idxmax()
print(gameInfo(idxmax), '-', attempts_per_game.max(), 'ударов')

# Пункт 15
header(15, 'Удары по воротам в этом матче на площадке')
game_shots = events[(events['Game ID'] == idxmax) &
                    events['Play Type'].isin(['shot-on-goal', 'goal', 'blocked-shot', 'missed-shot'])].copy()

# В этой игре хозяева в нечётных периодах (1, 3, 5) защищают правые ворота и бьют
# влево, поэтому после отражения (x, y) -> (-x, -y) их удары окажутся справа.
print('Сторона ворот хозяев по периодам:',
      events[events['Game ID'] == idxmax].groupby('Period')["Home Team's Defending Side"].first().to_dict())
odd_period = game_shots['Period'] % 2 == 1
game_shots.loc[odd_period, 'X Coordinate on the Ice Rink'] *= -1
game_shots.loc[odd_period, 'Y Coordinate on the Ice Rink'] *= -1

game_shots['Team'] = game_shots['Team Making the Play']
game_shots['Outcome'] = game_shots['Play Type']
home_team_name = games.loc[idxmax, 'Home Team']
away_team_name = games.loc[idxmax, 'Away Team']

# Проверка: удары хозяев должны быть справа (x > 0), гостей - слева (x < 0)
is_home = game_shots['Team'] == home_team_name
on_right = game_shots['X Coordinate on the Ice Rink'] > 0
print(f'Удары на "своей" стороне после преобразования: хозяева {on_right[is_home].mean():.1%}, '
      f'гости {(~on_right[~is_home]).mean():.1%}')

plt.figure(figsize=(7, 3))
plot_rink()
sns.scatterplot(
    data=game_shots, x='X Coordinate on the Ice Rink', y='Y Coordinate on the Ice Rink',
    hue='Outcome', hue_order=['goal', 'shot-on-goal', 'blocked-shot', 'missed-shot'],
    palette={'goal': 'red', 'shot-on-goal': 'm', 'blocked-shot': 'b', 'missed-shot': 'g'},
    style='Team', markers={home_team_name: '>', away_team_name: '<'}, s=40,
)
plt.legend(bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=8)
plt.axis('equal')
plt.axis('off')
plt.title(gameInfo(idxmax), fontsize=10)
plt.tight_layout(pad=0.1)
save_figure(plt.gcf(), 'game_shots_rink')


# Пункты 16-20: списки из десяти игроков. Если на 10-м месте ничья, честнее
# показать всех игроков с таким же значением, чем обрезать список случайно.
def top10_with_ties(values):
    values = values.sort_index().sort_values(ascending=False, kind='stable')
    return values[values >= values.iloc[9]]


def tie_note(top):
    if len(top) > 10:
        last = top.iloc[-1]
        print(f'(на 10-м месте ничья: у {(top == last).sum()} игроков одинаковое значение {last}, '
              f'поэтому в списке {len(top)} игроков)')


# Пункт 16
header(16, 'Десять лучших снайперов')
goals = events[events['Play Type'] == 'goal']
top_scorers = top10_with_ties(goals['Player in the Event #1'].value_counts())
print(top_scorers)
tie_note(top_scorers)

# Пункт 17
header(17, 'Десять лучших по голевым передачам')
assists = pd.concat([goals['Player in the Event #2'], goals['Player in the Event #3']]).dropna()
top_assists = top10_with_ties(assists.value_counts())
print(top_assists)
tie_note(top_assists)

# Пункт 18
header(18, 'Десять лучших по очкам (гол + пас)')
points = pd.concat([
    goals['Player in the Event #1'],
    goals['Player in the Event #2'],
    goals['Player in the Event #3'],
]).dropna()
top_points = top10_with_ties(points.value_counts())
print(top_points)
tie_note(top_points)

# Для "среднего за игру" делим на число игр, в которых игрок реально выходил
# на лёд (по колонкам состава), а не на число игр его команды.
player_games = lineup.dropna(subset=['Player'])[['Game ID', 'Player']].drop_duplicates()
games_played_count = player_games.groupby('Player').size()


def per_game_top10(event_type_list, column_name):
    totals = events[events['Play Type'].isin(event_type_list)]['Player in the Event #1'].value_counts()
    table = pd.DataFrame({
        column_name: totals / games_played_count.reindex(totals.index),
        'Games': games_played_count.reindex(totals.index),
    }).dropna()
    # при равных значениях - по алфавиту, чтобы порядок не зависел от версии pandas
    table = table.sort_index().sort_values(column_name, ascending=False, kind='stable')
    return table[table[column_name] >= table[column_name].iloc[9]]


# Пункт 19
header(19, 'Десять лучших по среднему числу бросков в створ за игру')
# Бросок в створ = shot-on-goal или goal (гол - это тоже попадание в створ), как в пункте 12
top_sog = per_game_top10(['shot-on-goal', 'goal'], 'Shots on Goal per Game')
print(top_sog.round(3))

# Пункт 20
header(20, 'Десять лучших по среднему числу силовых приёмов за игру')
top_hits = per_game_top10(['hit'], 'Hits per Game')
print(top_hits.round(3))
one_game = top_hits[top_hits['Games'] == 1].index.tolist()
print(f"""
Комментарий: среднее считается по играм, в которых игрок реально был на льду.
В столбце Games видно, на скольких играх основано среднее: у {' и '.join(one_game)}
это всего одна игра, поэтому их места в списке ненадёжны.
""")

# Пункт 21
header(21, 'Вратари, хотя бы в одном матче не пропустившие ни одного гола')
# Особенность данных: у всех решающих голов в овертайме нет состава на льду
# (# of ... Players on the Ice = 0, все колонки игроков пустые). Без поправки
# такой гол не засчитывается ни одному вратарю. Поэтому для событий без состава
# берём вратаря из предыдущего события этой же игры.
goalie_on_ice = {}
for side in ['Away', 'Home']:
    col = f"{side} Team's Goalie"
    no_lineup = events[f"# of {side} Team's Players on the Ice"] == 0
    previous_goalie = events[col].mask(no_lineup).groupby(events['Game ID']).ffill()
    goalie_on_ice[side] = events[col].where(~no_lineup, previous_goalie)

goal_mask = events['Play Type'] == 'goal'
goal_rows = events[goal_mask].copy()
scoring_is_home = goal_rows['Team Making the Play'] == goal_rows['Home Team']
goal_rows['Conceding Goalie'] = np.where(scoring_is_home, goalie_on_ice['Away'][goal_mask],
                                         goalie_on_ice['Home'][goal_mask])
goal_rows['Conceding Goalie (no fix)'] = np.where(scoring_is_home, goal_rows["Away Team's Goalie"],
                                                  goal_rows["Home Team's Goalie"])
no_lineup_goals = goal_rows["# of Away Team's Players on the Ice"] == 0
all_in_overtime = (goal_rows.loc[no_lineup_goals, 'Period'] > 3).all()
print(f'Голов без данных о составе на льду: {no_lineup_goals.sum()}, '
      f'все забиты в овертайме: {"да" if all_in_overtime else "нет"}')

# Все пары (вратарь, игра), в которых вратарь хотя бы раз был на льду
goalie_game_rows = []
for side in ['Away', 'Home']:
    sub = events[['Game ID', f"{side} Team's Goalie"]].dropna().drop_duplicates()
    goalie_game_rows.append(sub.rename(columns={f"{side} Team's Goalie": 'Goalie'}))
goalie_games = pd.concat(goalie_game_rows).drop_duplicates().set_index(['Goalie', 'Game ID'])


def clean_appearances(conceding_col):
    goals_against = goal_rows.dropna(subset=[conceding_col]).groupby([conceding_col, 'Game ID']).size()
    goals_against.index.names = ['Goalie', 'Game ID']
    against = goals_against.reindex(goalie_games.index, fill_value=0)
    return against[against == 0].index


clean = clean_appearances('Conceding Goalie')
shutout_goalies = sorted(clean.get_level_values('Goalie').unique())
print(shutout_goalies)
print()
for goalie, gid in sorted(clean):
    print(f'  {goalie}: {gameInfo(gid)}')
naive_goalies = sorted(clean_appearances('Conceding Goalie (no fix)').get_level_values('Goalie').unique())
print()
print('Без поправки на овертаймы в список ошибочно попали бы ещё:', sorted(set(naive_goalies) - set(shutout_goalies)))

# Пункт 22 - собственный вопрос
header(22, 'Собственный вопрос: тактика на матч лидеров')
# Финал (последний раунд по Game ID) выиграла Carolina Hurricanes у Vegas Golden Knights.
# Вопрос: какую тактику выбрать Vegas на гипотетический матч-реванш через неделю -
# с какого расстояния бросать, бросать ли чаще, нужны ли силовые приёмы?
finalists = ['Vegas Golden Knights', 'Carolina Hurricanes']
final_games = games.index[games.index.astype(str).str[-3] == '4']
final_wins = winner[final_games].value_counts()
print('Матчи финала:')
for gid in final_games:
    print(' ', gameInfo(gid))
print('Победы в финале:', final_wins.to_dict())

# 1) Конверсия броска в гол в зависимости от дистанции (все команды, весь плей-офф)
shots['is_goal'] = shots['Play Type'] == 'goal'
dist_labels = ['0-10', '10-20', '20-30', '30-40', '40-50', '50-60', '60-89', '89+']
shots['Distance'] = pd.cut(shots['Shot Length'], bins=[0, 10, 20, 30, 40, 50, 60, 89, 200],
                           labels=dist_labels, include_lowest=True)
conversion_by_dist = shots.groupby('Distance', observed=True)['is_goal'].agg(['size', 'sum', 'mean'])
conversion_by_dist.columns = ['Shots', 'Goals', 'Conversion']
print()
print('Конверсия броска (точного или неточного) в гол по дистанции, весь плей-офф:')
print(conversion_by_dist.round(3))


# 2) Профиль двух финалистов: весь плей-офф и отдельно финальная серия
def team_profile(team, game_ids):
    n = (team_games['Game ID'].isin(game_ids) & (team_games['Team'] == team)).sum()
    team_events = events[events['Game ID'].isin(game_ids) & (events['Team Making the Play'] == team)]
    play_type = team_events['Play Type']
    on_goal = play_type.isin(['shot-on-goal', 'goal']).sum()
    n_goals = (play_type == 'goal').sum()
    team_shots = shots[shots['Game ID'].isin(game_ids) & (shots['Team Making the Play'] == team)]
    return pd.Series({
        'Games': n,
        'Shot attempts/game': play_type.isin(['shot-on-goal', 'goal', 'missed-shot', 'blocked-shot']).sum() / n,
        'Shots on goal/game': on_goal / n,
        'Goals/game': n_goals / n,
        'Shooting %': 100 * n_goals / on_goal,
        'Median distance, ft': team_shots['Shot Length'].median(),
        'Shots < 20 ft, %': 100 * (team_shots['Shot Length'] < 20).mean(),
        'Hits/game': (play_type == 'hit').sum() / n,
    })


profile_all = pd.DataFrame({team: team_profile(team, games.index) for team in finalists}).T
profile_final = pd.DataFrame({team: team_profile(team, final_games) for team in finalists}).T
profile_all['Games'] = profile_all['Games'].astype(int)
profile_final['Games'] = profile_final['Games'].astype(int)
print()
print('Весь плей-офф:')
print(profile_all.round(2).T)
print()
print('Только финальная серия:')
print(profile_final.round(2).T)

# 3) Что отличает победителя от проигравшего в отдельном матче (все 82 игры)
hits_per_game = events[events['Play Type'] == 'hit'].groupby(['Game ID', 'Team Making the Play']).size()
team_game_stats = pd.DataFrame({
    'Shots on goal': shots_full,
    'Hits': hits_per_game.reindex(full_idx, fill_value=0),
}).reset_index()
team_game_stats['Won'] = team_game_stats['Team Making the Play'] == team_game_stats['Game ID'].map(winner)
won = team_game_stats[team_game_stats['Won']].set_index('Game ID').sort_index()
lost = team_game_stats[~team_game_stats['Won']].set_index('Game ID').sort_index()
winner_more = {}
print()
for col in ['Shots on goal', 'Hits']:
    winner_more[col] = (won[col] > lost[col]).sum()
    print(f'{col}: у победителя больше - в {winner_more[col]} из {len(won)} игр, '
          f'меньше - в {(won[col] < lost[col]).sum()}, поровну - в {(won[col] == lost[col]).sum()}')

fig, axes = plt.subplots(1, 2, figsize=(13, 5))
bar_colors = ['steelblue'] * (len(dist_labels) - 1) + ['lightgray']
conv_pct = 100 * conversion_by_dist['Conversion']
bars = axes[0].bar(dist_labels, conv_pct, color=bar_colors)
axes[0].bar_label(bars, fmt='%.1f', fontsize=9)
axes[0].text(len(dist_labels) - 1, conv_pct.iloc[-1] + 0.9, 'голы в\nпустые ворота', ha='center', fontsize=9)
axes[0].set_ylim(0, conv_pct.max() * 1.15)
axes[0].set_xlabel('Дистанция броска, футы')
axes[0].set_ylabel('Доля бросков, ставших голом, %')
axes[0].set_title('Конверсия броска по дистанции (весь плей-офф)')

compare = pd.DataFrame({'Весь плей-офф': profile_all['Shots on goal/game'],
                        'Финал': profile_final['Shots on goal/game']})
compare.T.plot(kind='bar', ax=axes[1], color=['#B4975A', '#CC0000'], rot=0)
for container in axes[1].containers:
    axes[1].bar_label(container, fmt='%.1f', fontsize=9)
axes[1].set_ylim(0, compare.values.max() * 1.25)
axes[1].set_ylabel('Бросков в створ за игру')
axes[1].set_title('Броски в створ: Vegas vs Carolina')
axes[1].legend(title=None, loc='upper center', ncol=2)
fig.tight_layout()
save_figure(fig, 'tactics_analysis')

vgk_all, car_all = profile_all.loc['Vegas Golden Knights'], profile_all.loc['Carolina Hurricanes']
vgk_fin, car_fin = profile_final.loc['Vegas Golden Knights'], profile_final.loc['Carolina Hurricanes']
extra_shots = car_all['Shots on goal/game'] - vgk_all['Shots on goal/game']
extra_goals = extra_shots * vgk_all['Shooting %'] / 100
conv = 100 * conversion_by_dist['Conversion']

print(f"""
Вопрос: финал выиграла Carolina Hurricanes ({final_wins['Carolina Hurricanes']} - {final_wins['Vegas Golden Knights']} по матчам). Представим, что через
неделю Vegas Golden Knights снова играет с Carolina - матч двух лидеров
плей-офф. Какую тактику выбрать Vegas: с какого расстояния бросать, бросать ли
чаще и стоит ли делать ставку на силовые приёмы?

1. Дистанция. Чем ближе бросок, тем выше шанс гола: {conv['0-10']:.1f}% для бросков ближе
10 футов, {conv['20-30']:.1f}% с 20-30 футов, {conv['40-50']:.1f}% с 40-50 футов и {conv['60-89']:.1f}% с 60-89 футов.
Рост в последнем столбце (89+ футов, своя половина площадки) - это в
основном голы в пустые ворота в концовках (пункт 9), а не настоящая
эффективность таких бросков. Vegas и так бросает ближе Carolina: медианная дистанция
{vgk_all['Median distance, ft']:.1f} против {car_all['Median distance, ft']:.1f} футов, ближе 20 футов - {vgk_all['Shots < 20 ft, %']:.1f}% бросков против {car_all['Shots < 20 ft, %']:.1f}%
(в финале {vgk_fin['Shots < 20 ft, %']:.1f}% против {car_fin['Shots < 20 ft, %']:.1f}%). Здесь менять ничего не нужно.

2. Частота бросков - главное отличие. За весь плей-офф Vegas делала
{vgk_all['Shot attempts/game']:.1f} попытки броска и {vgk_all['Shots on goal/game']:.1f} броска в створ за игру, Carolina - {car_all['Shot attempts/game']:.1f} и {car_all['Shots on goal/game']:.1f}.
В финальной серии то же самое: {vgk_fin['Shot attempts/game']:.1f} против {car_fin['Shot attempts/game']:.1f} попыток и {vgk_fin['Shots on goal/game']:.1f} против {car_fin['Shots on goal/game']:.1f}
бросков в створ. Реализация бросков за весь плей-офф у Vegas даже выше
({vgk_all['Shooting %']:.1f}% против {car_all['Shooting %']:.1f}%), но в финале была ниже ({vgk_fin['Shooting %']:.1f}% против {car_fin['Shooting %']:.1f}%): на шести
матчах она сильно зависит от вратарей и случая, а меньший объём бросков у
Vegas виден в обоих срезах. Победитель бросал в створ больше соперника в
{winner_more['Shots on goal']} из {len(won)} игр, а в пункте 13 каждый лишний бросок в створ за игру давал
команде в среднем +{slope:.2f} гола.

3. Силовые приёмы. Связи с победой нет: победитель провёл больше силовых
приёмов только в {winner_more['Hits']} из {len(won)} игр, то есть ровно в половине. В финале Vegas
проводила их даже больше Carolina ({vgk_fin['Hits/game']:.1f} против {car_fin['Hits/game']:.1f} за игру) - и
проиграла серию.

Рекомендация: Vegas стоит сохранить свой выбор позиций (бросать с близкого
расстояния, а не издалека) и при этом бросать заметно чаще: активнее
входить в зону атаки и чаще доводить владение до броска, а не тратить
силы на силовую борьбу. Если Vegas выйдет на объём Carolina (+{extra_shots:.1f} броска
в створ за игру) при своей реализации {vgk_all['Shooting %']:.1f}%, это даст около +{extra_goals:.2f} гола
за игру (с {vgk_all['Goals/game']:.2f} до ~{vgk_all['Goals/game'] + extra_goals:.1f}). Это оценка сверху: когда бросков
больше, их среднее качество обычно падает.

Оговорки: выборки маленькие ({int(vgk_all['Games'])} и {int(car_all['Games'])} игр, в финале - 6), и речь о
связях в данных, а не о доказанных причинах. Поэтому это направление для
тактики, а не точный прогноз.
""")

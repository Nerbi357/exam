"""Эталонное решение экзамена NHL playoffs 2026 (для проверки работ).

Запуск из корня репозитория:  python3 reference/solution.py
Печатает ответы по пунктам, рисунки сохраняет в reference/fig/.
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from rink import plot_rink

FIG = os.path.join(ROOT, 'reference', 'fig')
pd.set_option('display.width', 200)
pd.set_option('display.max_columns', 20)


def head(n):
    print('\n' + '=' * 20, f'Пункт {n}', '=' * 20)


# ---------------------------------------------------------------- 1
head(1)
events = pd.read_excel(os.path.join(ROOT, 'NHL-playoffs-2026.xlsx'), index_col=0)
print(events.shape)
print(events.iloc[:10, [2, 3, 4, 9, 12]])
raw = pd.read_excel(os.path.join(ROOT, 'NHL-playoffs-2026.xlsx'))
print('без index_col=0:', raw.shape, '; iloc[:3,[2,3,4,9,12]] ->', list(raw.columns[[2, 3, 4, 9, 12]]))

# ---------------------------------------------------------------- 2
head(2)
gb = events.groupby('Game ID')
games = gb[['Date', 'Away Team', 'Home Team']].first()
games['Away Score'] = gb['Cumulated Away Score'].max()
games['Home Score'] = gb['Cumulated Home Score'].max()
games['Outcome'] = gb['Period'].max().map({3: 'Final', 4: 'Final/OT', 5: 'Final/2OT'})
print(games.columns)
print(games.iloc[-5:, -4:])
print(games['Outcome'].value_counts().to_dict())
last = gb[['Cumulated Away Score', 'Cumulated Home Score']].last()
goals_by_team = events[events['Play Type'] == 'goal'].groupby(['Game ID', 'Team Making the Play']).size()
check = all(goals_by_team.get((i, r['Away Team']), 0) == r['Away Score'] and
            goals_by_team.get((i, r['Home Team']), 0) == r['Home Score'] for i, r in games.iterrows())
print('max == последняя строка:', (last.values == games[['Away Score', 'Home Score']].values).all(),
      '| подсчёт событий goal совпадает со счётом:', check)

# ---------------------------------------------------------------- 3
head(3)


def gameInfo(gameId):
    r = games.loc[gameId]
    return f"{r['Home Team']} - {r['Away Team']} ({r['Home Score']} - {r['Away Score']}, {r['Outcome']}, {r['Date']})"


print(gameInfo(games.index.min()))
print(gameInfo(games.index.max()))

# ---------------------------------------------------------------- 4
head(4)
games['Total Score'] = games['Away Score'] + games['Home Score']
print(games['Total Score'].describe().round(3))

# ---------------------------------------------------------------- 5
head(5)
vc = games['Total Score'].value_counts().sort_index()
print('высоты столбцов:', vc.to_dict())
plt.figure(figsize=(7, 4))
sns.countplot(x=games['Total Score'], order=range(1, 16), color='C0')
plt.xlabel('Число голов'); plt.ylabel('Число матчей')
plt.tight_layout(); plt.savefig(os.path.join(FIG, 'p05_countplot.png'), dpi=110); plt.close()

# ---------------------------------------------------------------- 6
head(6)
ts = games['Total Score']
print([gameInfo(i) for i in games.index[ts == ts.min()]])
print([gameInfo(i) for i in games.index[ts == ts.max()]])

# ---------------------------------------------------------------- 7
head(7)
pcols = [c for c in events.columns if 'Player on the Ice' in c] + ["Away Team's Goalie", "Home Team's Goalie"]
players = events.set_index('Game ID')[pcols].stack().groupby(level=0).nunique()
pc = games[[]].copy()
pc['Game Info'] = [gameInfo(i) for i in pc.index]
pc['Player Count'] = players
print(pc.sort_values('Player Count', ascending=False).head(5))
with_nan = events.groupby('Game ID')[pcols].apply(lambda d: pd.unique(d.values.ravel()).size)
print('если NaN считать игроком: max =', with_nan.max(), 'игра', with_nan.idxmax())
naive_sum = events.groupby('Game ID')[pcols].nunique().sum(axis=1)
print('ошибка «сумма nunique по столбцам»: max =', naive_sum.max(), 'игра', naive_sum.idxmax())

# ---------------------------------------------------------------- 8
head(8)


def dist(x, y, X):
    return np.where(y < -3, np.sqrt((x - X) ** 2 + (y + 3) ** 2),
                    np.where(y > 3, np.sqrt((x - X) ** 2 + (y - 3) ** 2), np.abs(x - X)))


shots = events[events['Play Type'].isin(['shot-on-goal', 'goal', 'missed-shot'])].copy()
is_home = shots['Team Making the Play'] == shots['Home Team']
home_left = shots["Home Team's Defending Side"] == 'left'
GX = np.where(is_home == home_left, 89, -89)
x, y = shots['X Coordinate on the Ice Rink'], shots['Y Coordinate on the Ice Rink']
shots['Shot Length'] = dist(x, y, GX)
events.loc[shots.index, 'Shot Length'] = shots['Shot Length']
print(events[events['Play Type'].isin(['shot-on-goal', 'goal', 'missed-shot'])][['Game ID', 'Play Type', 'Shot Length']].round(3))
print(shots['Shot Length'].describe().round(3))
# типичные ошибки
d_sign = dist(x, y, np.where(x > 0, 89, -89))
print('вариант «ворота по знаку X»: отличаются', int((np.abs(d_sign - shots['Shot Length']) > 1e-9).sum()), 'бросков, max =', round(float(np.nanmax(d_sign)), 3))
d_center = np.sqrt((x - GX) ** 2 + y ** 2)
print('вариант «до центра ворот»: среднее', round(float(np.mean(d_center)), 3), 'vs', round(shots['Shot Length'].mean(), 3))
d_swap = dist(x, y, -GX)
print('вариант «перепутаны ворота»: среднее', round(float(np.mean(d_swap)), 3))
d_noshift = np.sqrt((x - GX) ** 2 + y ** 2)

# ---------------------------------------------------------------- 9
head(9)
shots['Shot'] = np.where(shots['Play Type'] == 'missed-shot', 'missed', 'on goal')
print(shots['Shot'].value_counts().to_dict())
sns.histplot(data=shots, x='Shot Length', hue='Shot', stat='density', common_norm=False, kde=True, bins=40)
plt.xlabel('Shot length, feet'); plt.ylabel('Density')
plt.tight_layout(); plt.savefig(os.path.join(FIG, 'p09_hist.png'), dpi=110); plt.close()
far = shots[shots['Shot Length'] > 89]
print('броски дальше 89 футов (из своей половины):', far['Play Type'].value_counts().to_dict())
print('  по зонам:', pd.crosstab(far['Play Type'], far['Play Zone']).to_dict())
print('  по периодам (в створ):', far[far['Play Type'] == 'shot-on-goal']['Period'].value_counts().sort_index().to_dict())
print('медианы:', shots.groupby('Shot')['Shot Length'].median().round(3).to_dict())
print('доля бросков дальше 89 футов:', shots.groupby('Shot')['Shot Length'].apply(lambda s: round((s > 89).mean(), 4)).to_dict())

# ---------------------------------------------------------------- 10
head(10)
cnt = (events[events['Play Type'].isin(['shot-on-goal', 'goal', 'missed-shot'])]
       .groupby(['Game ID', 'Team Making the Play'])['Play Type'].value_counts().unstack(fill_value=0))
numshots = pd.DataFrame(index=cnt.index)
numshots['On Goal'] = cnt['shot-on-goal'] + cnt['goal']
numshots['All'] = cnt['shot-on-goal'] + cnt['goal'] + cnt['missed-shot']
numshots['Share of Shots on Goal'] = numshots['On Goal'] / numshots['All']
print(numshots['Share of Shots on Goal'].round(3))
print(numshots['Share of Shots on Goal'].describe().round(3))
s = numshots['Share of Shots on Goal']
print('доля < 0.5 в', int((s < 0.5).sum()), 'случаях из', len(s))
blk = events[events['Play Type'] == 'blocked-shot'].groupby(['Game ID', 'Team Making the Play']).size().reindex(cnt.index, fill_value=0)
alt = {
    'голы не в числителе: sog/(sog+goal+miss)': cnt['shot-on-goal'] / numshots['All'],
    'без голов вообще: sog/(sog+miss)': cnt['shot-on-goal'] / (cnt['shot-on-goal'] + cnt['missed-shot']),
    'с blocked в знаменателе': numshots['On Goal'] / (numshots['All'] + blk),
}
for k, v in alt.items():
    print('вариант', k, ':', v.round(3).head(3).tolist())

# ---------------------------------------------------------------- 11
head(11)
avgnumshots = s.groupby(level=1).mean()
print(avgnumshots.nlargest(5).round(3)); print(avgnumshots.nsmallest(5).round(3))
pooled = numshots.groupby(level=1)[['On Goal', 'All']].sum()
pooled = pooled['On Goal'] / pooled['All']
print('вариант Σ/Σ: top', pooled.nlargest(5).round(3).to_dict(), '| bottom', pooled.nsmallest(5).round(3).to_dict())
for k, v in alt.items():
    a = v.groupby(level=1).mean()
    print('вариант', k, ': top', list(a.nlargest(5).index), '| bottom', list(a.nsmallest(5).index))

# ---------------------------------------------------------------- 12
head(12)
sg = (events[events['Play Type'].isin(['shot-on-goal', 'goal'])]
      .groupby(['Game ID', 'Team Making the Play'])['Play Type'].value_counts().unstack(fill_value=0))
# все игры каждой команды (у каждой команды в каждой игре есть броски, проверяем)
team_games = pd.concat([games['Away Team'], games['Home Team']]).value_counts()
print('игр у команд совпадает с числом строк в группировке:', (sg.groupby(level=1).size() == team_games.reindex(sg.groupby(level=1).size().index)).all())
avgshots = pd.DataFrame({'Shot': sg['shot-on-goal'] + sg['goal'], 'Goal': sg['goal']}).groupby(level=1).mean()
print(avgshots.round(3))
alt12 = pd.DataFrame({'Shot': sg['shot-on-goal'], 'Goal': sg['goal']}).groupby(level=1).mean()
print('вариант Shot без голов:', alt12['Shot'].round(3).head(4).to_dict())
g_only = events[events['Play Type'] == 'goal'].groupby(['Game ID', 'Team Making the Play']).size().groupby(level=1).mean()
bad = (g_only - avgshots['Goal']).round(3)
print('вариант «голы только по матчам, где команда забивала»: завышены', bad[bad != 0].to_dict())

# ---------------------------------------------------------------- 13
head(13)
r = np.corrcoef(avgshots['Shot'], avgshots['Goal'])[0, 1]
slope, intercept = np.polyfit(avgshots['Shot'], avgshots['Goal'], 1)
from scipy import stats
print('r =', round(r, 3), '| p =', round(stats.pearsonr(avgshots['Shot'], avgshots['Goal'])[1], 3),
      '| наклон =', round(slope, 3), '| точек:', len(avgshots))
plt.figure(figsize=(7, 5))
sns.regplot(data=avgshots, x='Shot', y='Goal')
for t, row in avgshots.iterrows():
    plt.annotate(t, (row['Shot'], row['Goal']), fontsize=7)
plt.xlabel('Average number of shots on goal per game'); plt.ylabel('Average number of goals per game')
plt.tight_layout(); plt.savefig(os.path.join(FIG, 'p13_regplot.png'), dpi=110); plt.close()

# ---------------------------------------------------------------- 14
head(14)
ALL4 = ['shot-on-goal', 'goal', 'missed-shot', 'blocked-shot']
nshots = events[events['Play Type'].isin(ALL4)].groupby('Game ID').size()
idxmax = nshots.idxmax()
print(gameInfo(idxmax), '| бросков:', nshots.max())
for name, types in {'без голов': ['shot-on-goal', 'missed-shot', 'blocked-shot'],
                    'без blocked': ['shot-on-goal', 'goal', 'missed-shot'],
                    'только sog+goal': ['shot-on-goal', 'goal']}.items():
    v = events[events['Play Type'].isin(types)].groupby('Game ID').size()
    print('вариант', name, ':', v.idxmax(), v.max())

# ---------------------------------------------------------------- 15
head(15)
gs = events[(events['Game ID'] == idxmax) & events['Play Type'].isin(ALL4)].copy()
odd = gs['Period'] % 2 == 1
gs['x'] = np.where(odd, -gs['X Coordinate on the Ice Rink'], gs['X Coordinate on the Ice Rink'])
gs['y'] = np.where(odd, -gs['Y Coordinate on the Ice Rink'], gs['Y Coordinate on the Ice Rink'])
flip = np.where(gs["Home Team's Defending Side"] == 'left', 1, -1)
print('Defending Side по периодам:', gs.groupby('Period')["Home Team's Defending Side"].first().to_dict())
print('зеркалирование по нечётным периодам == по Defending Side:',
      np.allclose(gs['x'], gs['X Coordinate on the Ice Rink'] * flip))
hm = gs['Team Making the Play'] == gs['Home Team']
print('бросков:', len(gs), gs['Play Type'].value_counts().to_dict(), gs['Team Making the Play'].value_counts().to_dict())
print('доля бросков хозяев справа:', round((gs.loc[hm, 'x'] > 0).mean(), 3), '| гостей слева:', round((gs.loc[~hm, 'x'] < 0).mean(), 3))
plt.figure(figsize=(10, 4.5))
plot_rink()
sns.scatterplot(data=gs, x='x', y='y', hue='Play Type', style='Team Making the Play', s=25)
plt.axis('equal'); plt.axis('off'); plt.title(gameInfo(idxmax))
plt.legend(fontsize=7, loc='upper center')
plt.tight_layout(); plt.savefig(os.path.join(FIG, 'p15_rink.png'), dpi=110); plt.close()

# ---------------------------------------------------------------- 16-18
goal_ev = events[events['Play Type'] == 'goal']
goals = goal_ev['Player in the Event #1'].value_counts()
assists = pd.concat([goal_ev['Player in the Event #2'], goal_ev['Player in the Event #3']]).value_counts()
points = goals.add(assists, fill_value=0).astype(int).sort_values(ascending=False)


def top(s, name, n=10):
    s = s.sort_values(ascending=False)
    th = s.iloc[n - 1]
    print(s[s >= th].to_string())
    print(f'-> значение на 10-м месте: {th}; игроков с не меньшим значением: {(s >= th).sum()}')


head(16); top(goals, 'goals')
head(17); top(assists, 'assists')
print('вариант «только #2»:', goal_ev['Player in the Event #2'].value_counts().head(10).to_dict())
head(18); top(points, 'points')
inner = (goals + assists).dropna().sort_values(ascending=False)
print('вариант с потерей игроков без голов/передач (сложение без fill_value): top10 совпадает:',
      set(inner.head(10).index) <= set(points[points >= points.sort_values(ascending=False).iloc[9]].index))

# ---------------------------------------------------------------- 19-20
pl = [c for c in events.columns if 'Player on the Ice' in c]
onice = events.set_index('Game ID')[pl].stack().reset_index()
onice.columns = ['Game ID', 'lvl', 'Player']
games_on_ice = onice.drop_duplicates(['Game ID', 'Player']).groupby('Player').size()


def per_game(types, label):
    ev = events[events['Play Type'].isin(types)]
    tot = ev.groupby('Player in the Event #1').size()
    main = (tot / games_on_ice.reindex(tot.index)).sort_values(ascending=False)
    with_ev = (tot / ev.groupby('Player in the Event #1')['Game ID'].nunique()).sort_values(ascending=False)
    print(f'{label}: среднее за игру (знаменатель — игры на льду):')
    df = pd.DataFrame({'Total': tot, 'Games': games_on_ice.reindex(tot.index), 'Per Game': main.round(3)})
    print(df.sort_values('Per Game', ascending=False).head(12).to_string())
    print('вариант «только игры с событием»:', with_ev.round(3).head(10).to_dict())
    return main


head(19)
m19 = per_game(['shot-on-goal', 'goal'], 'в створ + голы')
m19b = per_game(['shot-on-goal'], 'только shot-on-goal')
head(20)
m20 = per_game(['hit'], 'hit')
# знаменатель «игры команды» (игрок — в команде, за которую он бросал)
team_of = events.groupby('Player in the Event #1')['Team Making the Play'].agg(lambda s: s.mode().iat[0])
tg = team_of.map(team_games)
for types, lab in [(['shot-on-goal', 'goal'], '19'), (['hit'], '20')]:
    tot = events[events['Play Type'].isin(types)].groupby('Player in the Event #1').size()
    print(f'вариант п.{lab} «игры команды»:', (tot / tg.reindex(tot.index)).sort_values(ascending=False).round(3).head(10).to_dict())

# ---------------------------------------------------------------- 21
head(21)
AG, HG = "Away Team's Goalie", "Home Team's Goalie"
NA, NH = "# of Away Team's Players on the Ice", "# of Home Team's Players on the Ice"
ev = events.reset_index(drop=True)
valid = (ev[NA] > 0) & (ev[NH] > 0)
# индекс последней строки с непустым составом строго до текущей (в пределах игры)
pos = pd.Series(np.where(valid, ev.index, np.nan))
prev_valid = pos.groupby(ev['Game ID']).shift(1).groupby(ev['Game ID']).ffill()
g = ev[ev['Play Type'] == 'goal'].copy()
g_home = g['Team Making the Play'] == g['Home Team']
pv = ev.loc[prev_valid.loc[g.index].astype(int)]
g['in_net'] = np.where(g_home, pv[AG].values, pv[HG].values)          # верно: вратарь до гола
g['row'] = np.where(g_home, g[AG], g[HG])                             # наивно: вратарь из строки гола
g['row_otfix'] = np.where(g['Period'] >= 4, g['in_net'], g['row'])    # строка гола, овертаймы исправлены
print('голов:', len(g), '| в овертайме (пустой состав):', int((g['Period'] >= 4).sum()),
      '| в пустые ворота (вратаря не было до гола):', int(pd.isna(g['in_net']).sum()),
      '| в строке гола другой вратарь, чем до гола (замена сразу после гола):',
      int(((g['row'] != g['in_net']) & g['row'].notna() & g['in_net'].notna()).sum()))
gp = []
for gid, d in ev.groupby('Game ID'):
    for col, team in [(AG, d['Away Team'].iat[0]), (HG, d['Home Team'].iat[0])]:
        for name in d[col].dropna().unique():
            gp.append((gid, team, name))
gp = pd.DataFrame(gp, columns=['Game ID', 'Team', 'Goalie'])


def shutouts(col):
    ga = g.dropna(subset=[col]).groupby(['Game ID', col]).size()
    t = gp.copy()
    t['GA'] = [ga.get((a, b), 0) for a, b in zip(t['Game ID'], t['Goalie'])]
    return t[t['GA'] == 0]


so = shutouts('in_net')
so = so.assign(Info=[gameInfo(i) for i in so['Game ID']])
print('ВЕРНО:', sorted(so['Goalie'].unique()))
print(so[['Game ID', 'Team', 'Goalie', 'Info']].to_string(index=False))
for col, lab in [('row', 'вратарь из строки гола'), ('row_otfix', 'строка гола + овертаймы исправлены')]:
    s2 = sorted(shutouts(col)['Goalie'].unique())
    print(f'вариант «{lab}»:', s2)
team_so = set()
for gid, r in games.iterrows():
    for team, ga in [(r['Away Team'], r['Home Score']), (r['Home Team'], r['Away Score'])]:
        if ga == 0:
            team_so |= set(gp[(gp['Game ID'] == gid) & (gp['Team'] == team)]['Goalie'])
print('вариант «сухие матчи команды»:', sorted(team_so))
# EN-голы начисляются вратарям команды
en = g[g['in_net'].isna()].groupby(['Game ID', 'Team Making the Play']).size()
t = gp.copy()
ga = g.dropna(subset=['in_net']).groupby(['Game ID', 'in_net']).size()
t['GA'] = [ga.get((a, b), 0) for a, b in zip(t['Game ID'], t['Goalie'])]
opp = {}
for gid, r in games.iterrows():
    opp[(gid, r['Away Team'])] = r['Home Team']; opp[(gid, r['Home Team'])] = r['Away Team']
t['EN'] = [en.get((a, opp[(a, b)]), 0) for a, b in zip(t['Game ID'], t['Team'])]
print('вариант «голы в пустые ворота тоже на вратаря»:', sorted(t[(t['GA'] + t['EN']) == 0]['Goalie'].unique()))

# ---------------------------------------------------------------- 22
head(22)
# Вопрос: как часто выигрывает команда, забившая первой, и есть ли преимущество своей площадки?
first = g.sort_values(['Game ID', 'Period', 'Elapsed Time']).groupby('Game ID').first()
winner = np.where(games['Home Score'] > games['Away Score'], games['Home Team'], games['Away Team'])
games['Winner'] = winner
fs = (first['Team Making the Play'] == games.loc[first.index, 'Winner'])
print('команда, забившая первой, выиграла в', int(fs.sum()), 'из', len(fs), 'матчей:', round(fs.mean(), 3))
hw = (games['Winner'] == games['Home Team'])
print('хозяева выиграли', int(hw.sum()), 'из', len(hw), ':', round(hw.mean(), 3))

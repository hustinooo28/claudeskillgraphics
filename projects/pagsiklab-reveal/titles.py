"""All on-screen words, in one place. Writes build/titles.json for titles.js."""
import json, os
from realm import HOUSES, CAMPUS

os.makedirs('build/titles', exist_ok=True)
T = []


def add(name, text, size, cy, x=960, align='center', weight=700, track=0, style='flat', color='#ffffff', shadow=True):
    T.append(dict(text=text, size=size, cy=cy, x=x, align=align, weight=weight, track=track, style=style,
                  color=color, shadow=shadow, out=f'build/titles/{name}.png'))


# cold open + credits
add('who', 'WHO WILL REIGN?', 64, 905, weight=600, track=10, style='silver')
add('lsc_l1', 'THE LOCAL STUDENT COUNCIL', 34, 760, weight=700, track=10, color='#e9edf0')
add('lsc_l2', 'DSSC · STA. CRUZ EXTENSION CAMPUS', 20, 805, weight=600, track=9, color='#aab3ba')
add('lsc_l3', 'PRESENTS', 20, 852, weight=600, track=14, color='#c9a46a')
add('ak_l1', 'A PRODUCTION BY', 20, 395, weight=600, track=14, color='#c9a46a')
add('year', '2026', 200, 540, weight=900, track=30, style='silver')

# lower thirds: icon at x=150, text from x=232
LX = 232
for h in HOUSES:
    k = h['key']
    add(f'{k}_name', h['house'], 52, 852, x=LX, align='left', weight=700, track=6, style='silver')
    add(f'{k}_sub', f"TEAM {h['team']}  ·  {h['seat']}  ·  {h['motto']}", 25, 905, x=LX + 2, align='left', weight=700, track=5, color='#e0bf7c')
    add(f'{k}_sec', '   ·   '.join(h['sections']), 22, 948, x=LX + 2, align='left', weight=700, track=4, color='#c6ccd1')
add('campus_name', 'THE SEAT OF THE REALM', 52, 852, x=LX, align='left', weight=700, track=6, style='silver')
add('campus_sub', 'DSSC  ·  STA. CRUZ EXTENSION CAMPUS', 25, 905, x=LX + 2, align='left', weight=700, track=5, color='#e0bf7c')
add('campus_sec', 'WHERE ALL SIX HOUSES MEET', 22, 948, x=LX + 2, align='left', weight=700, track=6, color='#c6ccd1')

# finale
add('era', 'A NEW ERA IS HERE', 54, 540, weight=600, track=14, style='silver')
add('title', 'PAGSIKLAB', 190, 470, weight=900, track=22, style='silver')
add('title_sub', 'MINI OLYMPICS 2026', 44, 640, weight=700, track=20, style='gold')
add('title_q', 'WHO WILL CLAIM THE THRONE?', 26, 735, weight=600, track=12, color='#e2e6e9')
add('end_lsc', 'THE LOCAL STUDENT COUNCIL  ·  DSSC STA. CRUZ EXTENSION CAMPUS', 15, 1010, weight=600, track=6, color='#8d969d')

json.dump(T, open('build/titles.json', 'w'))
print(len(T), 'text layers')

"""Shared layout of the realm: seats (map coords 0..1, y=0 is north), teams, timing.
Read by the map generator, the Blender scene builder and the compositor."""

FPS = 24
MAP_SIZE = 40.0            # Blender units across the map plane (x: -20..20, y: -20..20)

HOUSES = [  # team order from the Mini Olympics sheet
    dict(key='targaryen', team=1, house='HOUSE TARGARYEN', seat='DRAGONSTONE', motto='FIRE AND BLOOD',
         sections=['BSAB-1B', 'BSAB-2B', 'DIT-2A', 'BSAB-3B'], pos=(0.835, 0.43), style='dragonstone',
         color=(0.55, 0.08, 0.06), grade='fire'),
    dict(key='lannister', team=2, house='HOUSE LANNISTER', seat='CASTERLY ROCK', motto='HEAR ME ROAR',
         sections=['BSAB-3A', 'ACT-1B', 'BSIT-3B', 'BSIT-2A'], pos=(0.215, 0.50), style='rock',
         color=(0.62, 0.12, 0.08), grade='gold'),
    dict(key='tyrell', team=3, house='HOUSE TYRELL', seat='HIGHGARDEN', motto='GROWING STRONG',
         sections=['BSIT-4A', 'BSAB-4B', 'DIT-3A', 'BPA-2A'], pos=(0.34, 0.71), style='rings',
         color=(0.22, 0.42, 0.18), grade='green'),
    dict(key='stark', team=4, house='HOUSE STARK', seat='WINTERFELL', motto='WINTER IS COMING',
         sections=['ACT-1A', 'BSIT-2B', 'BSIT-4B', 'DIT-2B'], pos=(0.47, 0.17), style='keep',
         color=(0.55, 0.58, 0.62), grade='cold'),
    dict(key='martell', team=5, house='HOUSE MARTELL', seat='SUNSPEAR', motto='UNBOWED, UNBENT, UNBROKEN',
         sections=['BSIT-3A', 'BSAB-4A', 'BSIT-1B', 'BSAB-2A'], pos=(0.71, 0.87), style='domes',
         color=(0.85, 0.45, 0.10), grade='sun'),
    dict(key='baratheon', team=6, house='HOUSE BARATHEON', seat="STORM'S END", motto='OURS IS THE FURY',
         sections=['BSIT-1A', 'BPA-1A', 'BSAB-1A'], pos=(0.665, 0.60), style='drum',
         color=(0.85, 0.65, 0.12), grade='storm'),
]

# the throne: our own campus, at the heart of the realm
CAMPUS = dict(key='campus', house='THE SEAT OF THE REALM', seat='STA. CRUZ', motto='DSSC STA. CRUZ EXTENSION CAMPUS',
              pos=(0.47, 0.41))

# ---------------- edit (seconds) ----------------
COLD_OPEN = (0.0, 7.0)          # trophy in the dark, "WHO WILL REIGN?", then the words alone on black
TUNNEL = (7.0, 12.0)            # red/blue light streaks, the 2026 glass card
CREDITS = (12.0, 18.0)          # the akashic (12-15), the Local Student Council presents (15-18)
MAP_IN = (18.0, 24.0)           # fall through the clouds onto the realm
HOUSE_START = 24.0
HOUSE_LEN = 11.0
CAMPUS_WIN = (HOUSE_START + 6 * HOUSE_LEN, HOUSE_START + 6 * HOUSE_LEN + 11.0)  # 87 - 98  the campus builds
OVERVIEW = (CAMPUS_WIN[1], CAMPUS_WIN[1] + 7.0)                                # 98 - 105  "A NEW ERA IS HERE"
TITLE = (OVERVIEW[1], OVERVIEW[1] + 13.0)                                      # 105 - 118
END = TITLE[1]


def house_window(i):
    s = HOUSE_START + i * HOUSE_LEN
    return s, s + HOUSE_LEN


def to_world(pos):
    """map (u, v) -> Blender (x, y); v=0 is north = +y"""
    u, v = pos
    return (u - 0.5) * MAP_SIZE, (0.5 - v) * MAP_SIZE

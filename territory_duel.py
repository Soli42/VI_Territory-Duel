"""
Borba za teritoriju (Territory Duel) - Zadatak I
Formulacija problema i interfejs.

Reprezentacija stanja:
    GameState.board[r][c] = [boja, vlasnik]
        boja   : 0..K-1
        vlasnik: 0 - neutralno, 1 - P1 (crni), 2 - P2 (beli)
    (isti format kao u JSON-u iz faze II)

Invarijanta: sva polja regiona jednog igraca imaju istu boju
(boju koju je igrac poslednju izabrao, odnosno pocetnu boju start polja).
"""

import os
import random
from collections import deque

NEUTRAL, P1, P2 = 0, 1, 2
MIN_N, MAX_N = 2, 30
MIN_K, MAX_K = 2, 15

DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))  # samo horizontalno/vertikalno

PALETTE_HEX = [
    "#E96F50", "#F4CA58", "#A7D36A", "#9671C4", "#F59E4B",
    "#3FB8C5", "#4C78C7", "#D96AA7", "#2E8B57", "#8B4513",
    "#808080", "#FFD700", "#00CED1", "#FF1493", "#7CFC00",
]


# --------------------------------------------------------------------------
# Struktura stanja
# --------------------------------------------------------------------------
class GameState:
    def __init__(self, n, k, palette, board, current_player):
        self.n = n
        self.k = k
        self.palette = palette            # {indeks_boje: "#RRGGBB"}
        self.board = board                # n x n lista [boja, vlasnik]
        self.current_player = current_player

    def copy(self):
        return GameState(self.n, self.k, dict(self.palette),
                         [[cell[:] for cell in row] for row in self.board],
                         self.current_player)


def opponent(player):
    return P2 if player == P1 else P1


def start_cell(state, player):
    return (0, 0) if player == P1 else (state.n - 1, state.n - 1)


def create_initial_state(n, k, first_player=P1):
    """Generise n x n tablu sa nasumicnim bojama i postavlja start polja."""
    if not (MIN_N <= n <= MAX_N):
        raise ValueError(f"N mora biti u opsegu {MIN_N}-{MAX_N}")
    if not (MIN_K <= k <= MAX_K):
        raise ValueError(f"K mora biti u opsegu {MIN_K}-{MAX_K}")

    palette = {i: PALETTE_HEX[i] for i in range(k)}
    board = [[[random.randrange(k), NEUTRAL] for _ in range(n)] for _ in range(n)]

    # Start polja razlicitih boja (da igrac ne pocne vec "dodirnut" bojom protivnika)
    while board[n - 1][n - 1][0] == board[0][0][0]:
        board[n - 1][n - 1][0] = random.randrange(k)

    board[0][0][1] = P1
    board[n - 1][n - 1][1] = P2
    return GameState(n, k, palette, board, first_player)


# --------------------------------------------------------------------------
# Pomocne funkcije
# --------------------------------------------------------------------------
def neighbors(state, r, c):
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < state.n and 0 <= nc < state.n:
            yield nr, nc


def region_cells(state, player):
    return [(r, c) for r in range(state.n) for c in range(state.n)
            if state.board[r][c][1] == player]


def region_color(state, player):
    cells = region_cells(state, player)
    if not cells:
        return None
    r, c = cells[0]
    return state.board[r][c][0]


def regions_touch(state):
    """True ako se regioni P1 i P2 dodiruju (susedstvo 4-povezano)."""
    for r, c in region_cells(state, P1):
        for nr, nc in neighbors(state, r, c):
            if state.board[nr][nc][1] == P2:
                return True
    return False


def neutral_gain(state, player, color):
    """Skup neutralnih polja koja igrac osvaja izborom boje 'color':
    sva neutralna polja te boje povezana (preko polja te boje) sa njegovim regionom."""
    gained = set()
    queue = deque()
    for r, c in region_cells(state, player):
        for nr, nc in neighbors(state, r, c):
            cell = state.board[nr][nc]
            if cell[1] == NEUTRAL and cell[0] == color and (nr, nc) not in gained:
                gained.add((nr, nc))
                queue.append((nr, nc))
    while queue:
        r, c = queue.popleft()
        for nr, nc in neighbors(state, r, c):
            cell = state.board[nr][nc]
            if cell[1] == NEUTRAL and cell[0] == color and (nr, nc) not in gained:
                gained.add((nr, nc))
                queue.append((nr, nc))
    return gained


def can_take_over(state, player, color):
    """Igrac moze preuzeti protivnicki region ako se regioni dodiruju
    i izabrana boja je trenutna boja protivnickog regiona."""
    return regions_touch(state) and region_color(state, opponent(player)) == color


# --------------------------------------------------------------------------
# Dozvoljeni potezi
# --------------------------------------------------------------------------
def get_allowed_moves(state, player=None):
    """Boje kojima igrac osvaja bar jedno novo polje ili preuzima protivnicki region."""
    if player is None:
        player = state.current_player
    return [color for color in range(state.k)
            if neutral_gain(state, player, color) or can_take_over(state, player, color)]


def is_valid_move(state, color, player=None):
    if player is None:
        player = state.current_player
    return isinstance(color, int) and 0 <= color < state.k and \
        color in get_allowed_moves(state, player)


# --------------------------------------------------------------------------
# Kraj igre
# --------------------------------------------------------------------------
def check_game_over(state):
    """Vraca (kraj, pobednik, razlog). pobednik: P1, P2 ili 0 (nereseno) / None ako igra traje."""
    c1 = len(region_cells(state, P1))
    c2 = len(region_cells(state, P2))

    if c1 == 0:
        return True, P2, "P2 je preuzeo sva polja protivnika."
    if c2 == 0:
        return True, P1, "P1 je preuzeo sva polja protivnika."

    if not get_allowed_moves(state, state.current_player):
        if c1 > c2:
            winner = P1
        elif c2 > c1:
            winner = P2
        else:
            winner = 0
        who = "P1" if state.current_player == P1 else "P2"
        return True, winner, f"{who} nema dozvoljen potez; poredi se velicina regiona ({c1} : {c2})."

    return False, None, ""


# --------------------------------------------------------------------------
# Prikaz stanja
# --------------------------------------------------------------------------
def _rgb(hex_color):
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _bg(hex_color):
    r, g, b = _rgb(hex_color)
    return f"\033[48;2;{r};{g};{b}m"


def _luma_fg(hex_color):
    r, g, b = _rgb(hex_color)
    return "\033[30m" if (0.299 * r + 0.587 * g + 0.114 * b) > 140 else "\033[97m"


RESET = "\033[0m"


def print_state(state, show_moves=True):
    """Prikaz table: boja polja (pozadina + indeks), crna tacka (●) = P1, bela (○) = P2.
    Start polja su oznacena sa P1 / P2."""
    os.system("")  # omogucava ANSI na Windows terminalima
    n = state.n
    print()
    print("    " + "".join(f"{c:^4}" for c in range(n)))
    for r in range(n):
        line = f"{r:>3} "
        for c in range(n):
            color, owner = state.board[r][c]
            hexc = state.palette[color]
            if (r, c) == (0, 0):
                text, fg = "P1", "\033[30;1m"
            elif (r, c) == (n - 1, n - 1):
                text, fg = "P2", "\033[97;1m"
            elif owner == P1:
                text, fg = f"{color}●", "\033[30;1m"
            elif owner == P2:
                text, fg = f"{color}○", "\033[97;1m"
            else:
                text, fg = f"{color}", _luma_fg(hexc)
            line += _bg(hexc) + fg + f"{text:^4}" + RESET
        print(line)

    c1 = len(region_cells(state, P1))
    c2 = len(region_cells(state, P2))
    print(f"\nRegion P1 (●): {c1} polja, boja {region_color(state, P1)}"
          f"   |   Region P2 (○): {c2} polja, boja {region_color(state, P2)}")

    if show_moves:
        allowed = set(get_allowed_moves(state))
        print("Paleta: ", end="")
        for color in range(state.k):
            hexc = state.palette[color]
            mark = " " if color in allowed else "X"
            print(_bg(hexc) + _luma_fg(hexc) + f" {color}{mark}" + RESET, end=" ")
        print("  (X = nedozvoljena boja)")
        who = "P1 (crni)" if state.current_player == P1 else "P2 (beli)"
        print(f"Na potezu: {who}\n")


# --------------------------------------------------------------------------
# Unos parametara i poteza
# --------------------------------------------------------------------------
def read_int(prompt, lo, hi):
    while True:
        raw = input(prompt).strip()
        try:
            value = int(raw)
        except ValueError:
            print("  Unesite ceo broj.")
            continue
        if lo <= value <= hi:
            return value
        print(f"  Vrednost mora biti u opsegu {lo}-{hi}.")


def input_game_parameters():
    """Unos N, K, ko igra prvi (covek/racunar) i koji igrac (P1/P2) igra prvi."""
    n = read_int(f"Dimenzija table N ({MIN_N}-{MAX_N}): ", MIN_N, MAX_N)
    k = read_int(f"Broj boja K ({MIN_K}-{MAX_K}): ", MIN_K, MAX_K)
    first_type = read_int("Ko igra prvi? (1 - covek, 2 - racunar): ", 1, 2)
    first_player = read_int("Koji igrac igra prvi? (1 - P1, 2 - P2): ", 1, 2)
    return {
        "n": n,
        "k": k,
        "first_is_human": first_type == 1,
        "first_player": P1 if first_player == 1 else P2,
    }


def input_move(state):
    """Trazi od coveka boju sve dok unos nije ispravan i dozvoljen."""
    allowed = get_allowed_moves(state)
    while True:
        raw = input(f"Izaberite boju {allowed}: ").strip()
        try:
            color = int(raw)
        except ValueError:
            print("  Unos nije broj.")
            continue
        if not (0 <= color < state.k):
            print(f"  Boja mora biti u opsegu 0-{state.k - 1}.")
        elif color not in allowed:
            print("  Ta boja ne povecava region (nedozvoljen potez).")
        else:
            return color


# --------------------------------------------------------------------------
# Demonstracija (faza I - bez operatora promene stanja)
# --------------------------------------------------------------------------
def main():
    params = input_game_parameters()
    state = create_initial_state(params["n"], params["k"], params["first_player"])
    print_state(state)

    over, winner, reason = check_game_over(state)
    if over:
        print("Kraj igre:", reason)
        return

    color = input_move(state)
    gain = len(neutral_gain(state, state.current_player, color))
    print(f"\nIspravan potez: boja {color} "
          f"({'preuzimanje protivnika' if can_take_over(state, state.current_player, color) else f'+{gain} novih polja'}).")
    print("Primena poteza (operator promene stanja) se implementira u fazi II.")


if __name__ == "__main__":
    main()

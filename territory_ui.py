"""
Borba za teritoriju (Territory Duel) - Tkinter interfejs (faza I)

Koristi logiku iz territory_duel.py (mora biti u istom folderu).
Pokretanje:  python territory_ui.py

Tabla se crta na Canvas-u, paleta je takodje Canvas (radi isto na Windows/macOS/Linux).
Potez = klik na boju u paleti. Nedozvoljene boje su precrtane i ne reaguju na klik.

Faza II: kada u territory_duel.py dodate funkciju
    apply_move(state, color) -> novo GameState (sa promenjenim igracem na potezu)
interfejs ce je automatski koristiti. Do tada klik na ispravnu boju samo prikazuje
koliko polja bi se osvojilo.
"""

import tkinter as tk
from tkinter import messagebox

import territory_duel as td

try:
    from territory_duel import apply_move  # faza II
except ImportError:
    apply_move = None

BOARD_PIXELS = 600
BG = "#EEF2F7"


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Borba za teritoriju (Territory Duel)")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)
        self.state = None
        self.human = {td.P1: True, td.P2: True}
        self.show_setup()

    # ------------------------------------------------------------------
    # Ekran za unos parametara
    # ------------------------------------------------------------------
    def clear(self):
        for w in self.root.winfo_children():
            w.destroy()

    def show_setup(self):
        self.clear()
        f = tk.Frame(self.root, bg=BG, padx=30, pady=25)
        f.pack()

        tk.Label(f, text="Borba za teritoriju", font=("Helvetica", 20, "bold"),
                 bg=BG).grid(row=0, column=0, columnspan=2, pady=(0, 15))

        self.n_var = tk.IntVar(value=10)
        self.k_var = tk.IntVar(value=8)
        self.first_type = tk.IntVar(value=1)    # 1 - covek, 2 - racunar
        self.first_player = tk.IntVar(value=1)  # 1 - P1, 2 - P2

        tk.Label(f, text=f"Dimenzija table N ({td.MIN_N}-{td.MAX_N}):", bg=BG).grid(
            row=1, column=0, sticky="w", pady=4)
        tk.Spinbox(f, from_=td.MIN_N, to=td.MAX_N, textvariable=self.n_var, width=6).grid(
            row=1, column=1, sticky="w")

        tk.Label(f, text=f"Broj boja K ({td.MIN_K}-{td.MAX_K}):", bg=BG).grid(
            row=2, column=0, sticky="w", pady=4)
        tk.Spinbox(f, from_=td.MIN_K, to=td.MAX_K, textvariable=self.k_var, width=6).grid(
            row=2, column=1, sticky="w")

        tk.Label(f, text="Ko igra prvi:", bg=BG).grid(row=3, column=0, sticky="w", pady=(10, 0))
        r = tk.Frame(f, bg=BG)
        r.grid(row=3, column=1, sticky="w", pady=(10, 0))
        tk.Radiobutton(r, text="Čovek", variable=self.first_type, value=1, bg=BG).pack(side="left")
        tk.Radiobutton(r, text="Računar", variable=self.first_type, value=2, bg=BG).pack(side="left")

        tk.Label(f, text="Koji igrač igra prvi:", bg=BG).grid(row=4, column=0, sticky="w", pady=4)
        r = tk.Frame(f, bg=BG)
        r.grid(row=4, column=1, sticky="w")
        tk.Radiobutton(r, text="P1 (crni)", variable=self.first_player, value=1, bg=BG).pack(side="left")
        tk.Radiobutton(r, text="P2 (beli)", variable=self.first_player, value=2, bg=BG).pack(side="left")

        self.setup_msg = tk.Label(f, text="", fg="#B00020", bg=BG)
        self.setup_msg.grid(row=5, column=0, columnspan=2, pady=(8, 0))

        tk.Button(f, text="Počni igru", width=18, command=self.start_game).grid(
            row=6, column=0, columnspan=2, pady=(10, 0))

    def start_game(self):
        try:
            n, k = int(self.n_var.get()), int(self.k_var.get())
        except (tk.TclError, ValueError):
            self.setup_msg.config(text="N i K moraju biti celi brojevi.")
            return
        if not (td.MIN_N <= n <= td.MAX_N) or not (td.MIN_K <= k <= td.MAX_K):
            self.setup_msg.config(
                text=f"N mora biti {td.MIN_N}-{td.MAX_N}, a K {td.MIN_K}-{td.MAX_K}.")
            return

        first = td.P1 if self.first_player.get() == 1 else td.P2
        first_is_human = self.first_type.get() == 1
        self.human = {first: first_is_human, td.opponent(first): not first_is_human}
        self.state = td.create_initial_state(n, k, first)
        self.game_over = False
        self.build_game_screen()
        self.refresh()

    # ------------------------------------------------------------------
    # Ekran igre
    # ------------------------------------------------------------------
    def build_game_screen(self):
        self.clear()
        n, k = self.state.n, self.state.k
        self.cell = max(14, BOARD_PIXELS // n)
        side = self.cell * n

        f = tk.Frame(self.root, bg=BG, padx=15, pady=12)
        f.pack()

        self.score_lbl = tk.Label(f, text="", font=("Helvetica", 11), bg=BG)
        self.score_lbl.pack()
        self.status_lbl = tk.Label(f, text="", font=("Helvetica", 12, "bold"), bg=BG)
        self.status_lbl.pack(pady=(2, 8))

        self.board_cv = tk.Canvas(f, width=side, height=side, bg="white", highlightthickness=0)
        self.board_cv.pack()

        self.pal = max(26, min(48, side // k))
        self.pal_cv = tk.Canvas(f, width=self.pal * k, height=self.pal + 4, bg=BG, highlightthickness=0)
        self.pal_cv.pack(pady=(10, 4))
        self.pal_cv.bind("<Button-1>", self.on_palette_click)

        tk.Button(f, text="Nova igra", command=self.show_setup).pack(pady=(6, 0))

    def refresh(self):
        self.draw_board()
        self.draw_palette()
        self.update_status()

    def draw_board(self):
        s, cv, cell = self.state, self.board_cv, self.cell
        cv.delete("all")
        for r in range(s.n):
            for c in range(s.n):
                color, owner = s.board[r][c]
                x, y = c * cell, r * cell
                cv.create_rectangle(x + 1, y + 1, x + cell - 1, y + cell - 1,
                                    fill=s.palette[color], outline="white")
                if owner == td.NEUTRAL:
                    continue
                dot_fill, dot_line, txt = ("black", "white", "white") if owner == td.P1 \
                    else ("white", "black", "black")
                is_start = (r, c) == td.start_cell(s, owner)
                rad = cell * (0.34 if is_start else 0.16)
                cx, cy = x + cell / 2, y + cell / 2
                cv.create_oval(cx - rad, cy - rad, cx + rad, cy + rad,
                               fill=dot_fill, outline=dot_line, width=1)
                if is_start and cell >= 22:
                    cv.create_text(cx, cy, text="P1" if owner == td.P1 else "P2",
                                   fill=txt, font=("Helvetica", max(7, cell // 4), "bold"))

    def draw_palette(self):
        s, cv, p = self.state, self.pal_cv, self.pal
        cv.delete("all")
        allowed = set(td.get_allowed_moves(s)) if not self.game_over else set()
        for color in range(s.k):
            x = color * p
            cv.create_rectangle(x + 3, 2, x + p - 3, p - 2, fill=s.palette[color], outline="#555")
            if color not in allowed:
                cv.create_line(x + 8, 7, x + p - 8, p - 7, width=2, fill="#222")
                cv.create_line(x + 8, p - 7, x + p - 8, 7, width=2, fill="#222")
            cv.create_text(x + p / 2, p - 8, text=str(color), font=("Helvetica", 8),
                           fill="#222")

    def update_status(self, msg=None):
        s = self.state
        c1 = len(td.region_cells(s, td.P1))
        c2 = len(td.region_cells(s, td.P2))
        self.score_lbl.config(text=f"P1 (crni ●): {c1} polja     P2 (beli ○): {c2} polja")
        if msg is not None:
            self.status_lbl.config(text=msg)
            return
        if self.game_over:
            return
        who = "P1 (crni)" if s.current_player == td.P1 else "P2 (beli)"
        kind = "čovek" if self.human[s.current_player] else "računar"
        extra = "" if self.human[s.current_player] else " – algoritam dolazi u fazi III"
        self.status_lbl.config(text=f"Na potezu: {who}, {kind}{extra}")

    # ------------------------------------------------------------------
    # Unos poteza
    # ------------------------------------------------------------------
    def on_palette_click(self, event):
        if self.game_over:
            return
        s = self.state
        if not self.human[s.current_player]:
            self.update_status("Na potezu je računar.")
            return
        color = event.x // self.pal
        if not (0 <= color < s.k):
            return
        if not td.is_valid_move(s, color):
            self.update_status(f"Boja {color} nije dozvoljena (ne povećava region).")
            return

        if apply_move is None:
            gain = len(td.neutral_gain(s, s.current_player, color))
            what = "preuzimanje protivnika" if td.can_take_over(s, s.current_player, color) \
                else f"+{gain} novih polja"
            self.update_status(f"Ispravan potez: boja {color} ({what}). "
                               f"Primena poteza dolazi u fazi II.")
            return

        self.state = apply_move(s, color)
        over, winner, reason = td.check_game_over(self.state)
        if over:
            self.game_over = True
        self.refresh()
        if over:
            self.announce(winner, reason)

    def announce(self, winner, reason):
        text = "Nerešeno!" if winner == 0 else \
            ("Pobednik: P1 (crni)" if winner == td.P1 else "Pobednik: P2 (beli)")
        self.update_status(text)
        messagebox.showinfo("Kraj igre", f"{text}\n{reason}")


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
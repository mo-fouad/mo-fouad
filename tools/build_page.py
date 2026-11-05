"""Full GitHub profile page for mo-fouad, as a stack of SVG sections (light + dark).

Sections have transparent backgrounds so they flow on GitHub's own page colour.
argv[1] = output dir, argv[2] = contributions json (gh api graphql output)
"""
import base64, io, json, os, sys
from html import escape
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools import subset

HERE = os.path.dirname(os.path.abspath(__file__))
F = lambda n: os.path.join(HERE, "fonts", n)
W = 800

# ------------------------------------------------------------------ tokens
GRID = {
    "light": ["#EBEDF0", "#9BE9A8", "#40C463", "#30A14E", "#216E39"],
    "dark": ["#1E242C", "#0E4429", "#006D32", "#26A641", "#39D353"],
}
THEMES = {
    "light": dict(snake=["#B9532F", "#C96442", "#D97757", "#E08B6E", "#E8A288", "#EFB9A3"], ink="#1A1A19", muted="#6B6A65", faint="#9A988F", line="#E3E0D8",
                  card="#FFFFFF", cardline="#E1DED6", clay="#C2603F", key="#2F6DB5",
                  tagline="#D9D6CE", tagtext="#4A4945",
                  idea="#966A1C", model="#5E7345", api="#B5532F", app="#3F6B99", live="#1A1A19",
                  ok="#4E7D3A", tint=0.06, tagtint=0.09,
                  term="#1F1E1D", termline="#1F1E1D"),
    "dark": dict(snake=["#F2946F", "#E8835F", "#D97757", "#C96E50", "#B4654B", "#9A5D48"], ink="#ECEAE4", muted="#A3A19A", faint="#7D7B74", line="#30363D",
                 card="#161B22", cardline="#30363D", clay="#E08A6B", key="#79A8E0",
                 tagline="#3D444D", tagtext="#C9C6BE",
                 idea="#DDAE62", model="#A6BC8B", api="#E39373", app="#93B8DE", live="#ECEAE4",
                 ok="#93C77F", tint=0.10, tagtint=0.14,
                 term="#1C1C1B", termline="#3A3936"),
}
TERM = dict(ink="#F0EEE6", muted="#A6A39A", clay="#D4714F", btn_text="#1C1C1B")

ROLES = {
    "display": (F("Newsreader.ttf"), {"wght": 460, "opsz": 72}, "Georgia,serif"),
    "h2": (F("Newsreader.ttf"), {"wght": 450, "opsz": 36}, "Georgia,serif"),
    "serif": (F("Newsreader.ttf"), {"wght": 400, "opsz": 18}, "Georgia,serif"),
    "sans": (F("HankenGrotesk.ttf"), {"wght": 400}, "-apple-system,Helvetica,Arial,sans-serif"),
    "sansb": (F("HankenGrotesk.ttf"), {"wght": 600}, "-apple-system,Helvetica,Arial,sans-serif"),
    "mono": (F("JetBrainsMono.ttf"), {"wght": 400}, "ui-monospace,Menlo,monospace"),
    "monob": (F("JetBrainsMono.ttf"), {"wght": 600}, "ui-monospace,Menlo,monospace"),
}

_fonts = {}
def font(role):
    if role not in _fonts:
        path, axes, _ = ROLES[role]
        _fonts[role] = instancer.instantiateVariableFont(TTFont(path), axes)
    return _fonts[role]

def tw(role, size, s):
    f = font(role); cmap = f.getBestCmap(); hm = f["hmtx"]
    return sum(hm[cmap.get(ord(c), cmap[ord("M")])][0] for c in s) * size / f["head"].unitsPerEm

def wrap(role, size, s, width):
    lines, cur = [], ""
    for word in s.split():
        nxt = (cur + " " + word).strip()
        if tw(role, size, nxt) > width and cur:
            lines.append(cur); cur = word
        else:
            cur = nxt
    return lines + [cur]

def woff2(role, text):
    b = io.BytesIO(); font(role).save(b); b.seek(0); ft = TTFont(b)
    o = subset.Options(); o.flavor = "woff2"; o.layout_features = ["kern", "liga"]; o.name_IDs = []
    s = subset.Subsetter(o); s.populate(text=text + " "); s.subset(ft)
    out = io.BytesIO(); ft.flavor = "woff2"; ft.save(out)
    return base64.b64encode(out.getvalue()).decode()

class SVG:
    def __init__(self, h, title):
        self.h, self.title, self.body = h, title, []
        self.used = {r: set() for r in ROLES}
    def text(self, x, y, s, role, size, fill, anchor="start", cls="", spacing=None):
        self.used[role].update(s)
        ls = f' letter-spacing="{spacing}"' if spacing is not None else ""
        klass = f"{role} {cls}".strip()
        self.body.append(f'<text x="{x:.1f}" y="{y:.1f}" class="{klass}" font-size="{size}" fill="{fill}" '
                         f'text-anchor="{anchor}"{ls} xml:space="preserve">{escape(s)}</text>')
    def runs(self, x, y, parts, role, size):
        cx = x
        for s, fill in parts:
            if s:
                self.text(cx, y, s, role, size, fill)
            cx += tw(role, size, s)
        return cx
    def raw(self, s): self.body.append(s)
    def hline(self, y, t):
        self.raw(f'<line x1="0" y1="{y}" x2="{W}" y2="{y}" stroke="{t["line"]}"/>')
    def render(self, css=""):
        faces = "".join(
            f"@font-face{{font-family:'pf-{r}';src:url(data:font/woff2;base64,{woff2(r, ''.join(sorted(c)))}) format('woff2');}}"
            f".{r}{{font-family:'pf-{r}',{ROLES[r][2]};}}"
            for r, c in self.used.items() if c)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{self.h}" viewBox="0 0 {W} {self.h}" '
                f'role="img" aria-label="{escape(self.title)}"><title>{escape(self.title)}</title>'
                f'<style>{faces}{css}</style>' + "".join(self.body) + "</svg>")

REDUCED = "@media (prefers-reduced-motion: reduce){.motion{display:none}.blink{animation:none}}"

def section_head(s, t, top, label, title, meta=None):
    s.text(0, top + 14, label, "mono", 12.5, t["clay"])
    s.text(-1, top + 54, title, "h2", 34, t["ink"])
    if meta:
        s.text(W, top + 52, meta, "mono", 12.5, t["faint"], anchor="end")

def tag(s, t, x_right, y, label, h=22):
    w = tw("mono", 11.5, label) + 18
    x = x_right - w
    s.raw(f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{h}" rx="4" fill="{t["card"]}" stroke="{t["tagline"]}"/>')
    s.text(x + w / 2, y + 15, label, "mono", 11.5, t["tagtext"], anchor="middle")
    return x

# ------------------------------------------------------------------ snake on the contribution grid
SNAKE_CSS = (".snake-static{display:none}"
             "@media (prefers-reduced-motion: reduce){.snake-anim{display:none}.snake-static{display:inline}}")

def snake_route(cells):
    """Head positions (col,row) per step: from the top-left corner, always walk the
    shortest grid path to the nearest uneaten cell. Returns positions and the step
    each target cell is eaten at."""
    pos, todo, steps, eaten = (0, 0), set(cells), [(0, 0)], {}
    if pos in todo:
        todo.discard(pos); eaten[pos] = 0
    while todo:
        tgt = min(todo, key=lambda c: (abs(c[0]-pos[0]) + abs(c[1]-pos[1]), c[0], c[1]))
        while pos != tgt:  # rows first, then columns: looks more snake-like on a 7-row grid
            if pos[1] != tgt[1]:
                pos = (pos[0], pos[1] + (1 if tgt[1] > pos[1] else -1))
            else:
                pos = (pos[0] + (1 if tgt[0] > pos[0] else -1), pos[1])
            steps.append(pos)
            if pos in todo:
                todo.discard(pos); eaten[pos] = len(steps) - 1
    return steps, eaten

def snake_grid(s, t, g, grid, levels, gx, gy, cell, gap, length=5, dt=0.11):
    pitch = cell + gap
    lvl = {(i, d["weekday"]): levels[d["level"]] for i, wk in enumerate(grid) for d in wk}
    xy = lambda c: (gx + c[0] * pitch, gy + c[1] * pitch)

    # static grid, shown only when motion is reduced
    s.raw('<g class="snake-static">' + "".join(
        f'<rect x="{xy(c)[0]:.1f}" y="{xy(c)[1]:.1f}" width="{cell}" height="{cell}" rx="2" fill="{g[v]}"/>'
        for c, v in lvl.items()) + "</g>")

    steps, eaten = snake_route([c for c, v in lvl.items() if v > 0])
    run = (len(steps) - 1 + length) * dt          # head walks the route, tail catches up
    hold, back = 0.8, 1.2                          # pause on the empty grid, then cells grow back
    D = run + hold + back + 0.6
    f = lambda sec: f"{sec / D:.4f}"
    restore = run + hold

    parts = ['<g class="snake-anim">']
    for c, v in lvl.items():
        x, y = xy(c)
        if v == 0 or c not in eaten:
            parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{cell}" height="{cell}" rx="2" fill="{g[v]}"/>')
            continue
        te = eaten[c] * dt
        parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{cell}" height="{cell}" rx="2" fill="{g[v]}">'
                     f'<animate attributeName="fill" dur="{D:.2f}s" repeatCount="indefinite" calcMode="discrete" '
                     f'values="{g[v]};{g[0]};{g[v]}" keyTimes="0;{f(te)};{f(restore + back * (c[0] / max(1, len(grid))))}"/></rect>')

    # snake: segment k sits k steps behind the head
    n = len(steps) + length
    for k in range(length - 1, -1, -1):
        pts = []
        for st in range(n):
            c = steps[min(max(st - k, 0), len(steps) - 1)]
            x, y = xy(c); pts.append(f"{x + cell/2:.1f},{y + cell/2:.1f}")
        kt = ";".join(f"{(i * dt) / D:.4f}" for i in range(n)) + ";1"
        pts.append(pts[-1])
        size = cell - 1 if k == 0 else cell - 2 - k * 0.6
        op = 1 if k == 0 else max(0.35, 0.9 - k * 0.14)
        parts.append(f'<rect x="{-size/2:.1f}" y="{-size/2:.1f}" width="{size:.1f}" height="{size:.1f}" rx="{2.5 if k else 3}" '
                     f'fill="{t["clay"]}" fill-opacity="{op:.2f}">'
                     f'<animateMotion dur="{D:.2f}s" repeatCount="indefinite" calcMode="linear" '
                     f'values="{";".join(pts)}" keyTimes="{kt}"/>'
                     f'<animate attributeName="opacity" dur="{D:.2f}s" repeatCount="indefinite" calcMode="discrete" '
                     f'values="1;0" keyTimes="0;{f(run + 0.25)}"/></rect>')
    parts.append("</g>")
    s.raw("".join(parts))
    print(f"  snake: {len(steps)} steps, {len(eaten)} cells, loop {D:.1f}s", file=sys.stderr)

def snake_loop_route(cols=22, rows=7, start=(3, 3), length=6, foods=14, live=3, seed=11):
    """Simulate a closed snake walk. Returns head positions (a cycle: last step is next to
    the first) and food events [(cell, appear_step, eat_step, level)] with steps mod len."""
    import random
    from collections import deque
    rnd = random.Random(seed)
    cells = [(c, r) for c in range(cols) for r in range(rows)]
    path = [start]

    def body():
        return set(path[-(length - 1):]) if len(path) > 1 else set()

    def step_towards(goal, blocked):
        """Next cell on a shortest route to goal avoiding blocked; prefers going straight."""
        dist = {goal: 0}; q = deque([goal])
        while q:
            c = q.popleft()
            for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (c[0] + d[0], c[1] + d[1])
                if 0 <= n[0] < cols and 0 <= n[1] < rows and n not in dist and (n not in blocked or n == path[-1]):
                    dist[n] = dist[c] + 1; q.append(n)
        cur = path[-1]
        if cur not in dist:
            return None
        heading = (cur[0] - path[-2][0], cur[1] - path[-2][1]) if len(path) > 1 else (1, 0)
        opts = []
        for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (cur[0] + d[0], cur[1] + d[1])
            if dist.get(n, 1e9) == dist[cur] - 1:
                opts.append((d != heading, n))
        return min(opts)[1] if opts else None

    def walk_to(goal, avoid):
        while path[-1] != goal:
            nxt = step_towards(goal, avoid | body()) or step_towards(goal, avoid)
            path.append(nxt)

    def free_cell(taken):
        while True:
            c = rnd.choice(cells)
            if c not in taken and c != start and abs(c[0] - path[-1][0]) + abs(c[1] - path[-1][1]) > 3:
                return c

    initial = []
    for _ in range(live):
        initial.append(free_cell(set(initial) | {start}))
    active = {c: (0, rnd.randint(2, 4)) for c in initial}      # cell -> (appear step, level)
    finals, events, spawned = {}, [], live
    while active:
        here = path[-1]
        tgt = min(active, key=lambda c: (abs(c[0] - here[0]) + abs(c[1] - here[1]), c))
        walk_to(tgt, (set(active) - {tgt}) | set(finals))
        a, lvl = active.pop(tgt)
        events.append([tgt, a, len(path) - 1, lvl])
        taken = set(active) | set(finals) | set(initial) | body() | {path[-1]}
        if spawned < foods:
            c = free_cell(taken); active[c] = (len(path) - 1, rnd.randint(2, 4)); spawned += 1
        else:  # bring back the opening dots, so the next loop starts exactly like this one
            k = len(finals)
            if k < live:
                finals[initial[k]] = len(path) - 1
    walk_to(start, set(finals))
    path.pop()                       # path[-1] == start == path[0]; keep it a cycle
    n = len(path)
    for e in events:                 # opening dots appeared in the previous loop
        if e[0] in finals and e[1] == 0:
            e[1] = finals[e[0]] - n  # negative: wraps to the end of the loop
    return path, events

def snake_loop_grid(s, t, g, grid, levels, gx, gy, cell, gap, length=6, dt=0.13):
    pitch = cell + gap
    xy = lambda c: (gx + c[0] * pitch, gy + c[1] * pitch)
    cols = len(grid)
    path, events = snake_loop_route(cols=cols, length=length)
    n = len(path); D = n * dt
    f = lambda st: f"{(st % n) / n:.4f}"

    # reduced motion: the real contribution grid, still
    real = {(i, d["weekday"]): levels[d["level"]] for i, wk in enumerate(grid) for d in wk}
    s.raw('<g class="snake-static">' + "".join(
        f'<rect x="{xy(c)[0]:.1f}" y="{xy(c)[1]:.1f}" width="{cell}" height="{cell}" rx="2" fill="{g[v]}"/>'
        for c, v in real.items()) + "</g>")

    parts = ['<g class="snake-anim">']
    for c in real:  # empty board
        x, y = xy(c)
        parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{cell}" height="{cell}" rx="2" fill="{g[0]}"/>')
    for cell_, a, e, lvl in events:  # dots
        x, y = xy(cell_)
        if a < 0:   # visible at loop start, eaten at e, back at n+a
            vals, kt = "1;0;1", f"0;{f(e)};{f(n + a)}"
        else:
            vals, kt = ("0;1;0", f"0;{f(a)};{f(e)}") if a > 0 else ("1;0", f"0;{f(e)}")
        parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{cell}" height="{cell}" rx="2" fill="{g[lvl]}" opacity="0">'
                     f'<animate attributeName="opacity" dur="{D:.2f}s" repeatCount="indefinite" calcMode="discrete" '
                     f'values="{vals}" keyTimes="{kt}"/></rect>')
    # snake: head darkest, tail lightest; segment k is k steps behind the head
    shades = [4, 4, 3, 3, 2, 1][:length]
    kt = ";".join(f"{i / n:.4f}" for i in range(n)) + ";1"
    for k in range(length - 1, -1, -1):
        pts = []
        for st in range(n + 1):
            x, y = xy(path[(st - k) % n]); pts.append(f"{x + cell/2:.1f},{y + cell/2:.1f}")
        parts.append(f'<rect x="{-cell/2}" y="{-cell/2}" width="{cell}" height="{cell}" rx="{3 if k == 0 else 2}" fill="{g[shades[k]]}">'
                     f'<animateMotion dur="{D:.2f}s" repeatCount="indefinite" calcMode="linear" '
                     f'values="{";".join(pts)}" keyTimes="{kt}"/></rect>')
    parts.append("</g>")
    s.raw("".join(parts))
    print(f"  snake loop: {n} steps, {len(events)} dots, {D:.1f}s", file=sys.stderr)

SNAKE_MODE = "runner"   # "runner": dots stream right to left · "loop": dots pop up in place (snake-advanced)

def snake_runner_route(cols=22, rows=7, start=(2, 3), length=6, ticks=140, seed=5):
    """Dots enter at the right edge and move one cell left per tick; the snake moves one
    cell per tick and heads for the nearest dot it can cut off. Every move keeps the start
    cell within reach, so the snake is back home exactly at `ticks` (a closed walk).
    Returns (path, dots) with dots as dicts: s (spawn tick), r (row), lvl, end (tick it
    disappears), eaten (bool)."""
    import random
    rnd = random.Random(seed)
    assert ticks % 2 == 0
    dots, t = [], 2
    while t < ticks - cols - 2:          # last dot is off the board before the loop ends
        for r in rnd.sample(range(rows), rnd.choice((1, 1, 2))):   # sometimes two dots enter together
            dots.append({"s": t, "r": r, "lvl": rnd.randint(2, 4), "end": t + cols, "eaten": False})
        t += rnd.choice((1, 2, 2, 3))
    # light green dots: a second stream the snake leaves alone (and steers around)
    ghosts, t, used = [], 1, {(d["s"], d["r"]) for d in dots}
    while t < ticks - cols - 2:
        for r in rnd.sample(range(rows), rnd.choice((1, 2, 2, 3))):
            if (t, r) not in used:
                ghosts.append({"s": t, "r": r, "lvl": 1, "end": t + cols, "eaten": False})
        t += rnd.choice((1, 1, 2))
    cell = lambda d, tt: (cols - 1 - (tt - d["s"]), d["r"])
    alive = lambda d, tt: d["s"] <= tt < d["end"]
    man = lambda a, b: abs(a[0] - b[0]) + abs(a[1] - b[1])
    path = [start]
    for t in range(ticks):
        cur, remaining = path[-1], ticks - (t + 1)
        blocked = set(path[-(length - 1):])
        nbrs = [(cur[0] + dx, cur[1] + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
        nbrs = [n for n in nbrs if 0 <= n[0] < cols and 0 <= n[1] < rows and man(n, start) <= remaining]
        cands = [n for n in nbrs if n not in blocked] or nbrs
        def hits_ghost(n):
            return any(alive(gd, t + 1) and (cell(gd, t + 1) == n or
                       (alive(gd, t) and cell(gd, t) == n and cell(gd, t + 1) == cur)) for gd in ghosts)
        cands = [n for n in cands if not hits_ghost(n)] or cands
        # nearest dot we can reach before it leaves the board
        best = None
        for d in dots:
            if d["eaten"] or d["end"] <= t + 1:
                continue
            for k in range(1, cols + 1):
                tt = t + k
                if not (d["s"] <= tt < d["end"]):
                    continue
                if cell(d, tt)[0] <= cols - 8 and man(cur, cell(d, tt)) <= k:   # meet dots out on the board
                    if best is None or k < best[0]:
                        best = (k, cell(d, tt))
                    break
        heading = (cur[0] - path[-2][0], cur[1] - path[-2][1]) if len(path) > 1 else (1, 0)
        if best:
            goal = best[1]
            nxt = min(cands, key=lambda n: (man(n, goal), (n[0] - cur[0], n[1] - cur[1]) != heading))
        else:  # nothing to chase: cruise, drifting back towards home
            mid = (cols // 2 - 3, rows // 2)   # drift back towards the middle-left and wait for the next dot
            nxt = min(cands, key=lambda n: (man(n, mid) > 2 and man(n, mid) >= man(cur, mid), (n[0] - cur[0], n[1] - cur[1]) != heading, rnd.random()))
        path.append(nxt)
        for d in dots:   # eat if the head lands on a dot, or they pass through each other
            if d["eaten"] or not alive(d, t + 1):
                continue
            if cell(d, t + 1) == nxt or (alive(d, t) and cell(d, t) == nxt and cell(d, t + 1) == cur):
                d["eaten"], d["end"] = True, t + 1
    assert path[-1] == start, path[-1]
    path.pop()
    # when the snake was boxed in with no clean way around, leave that light dot out
    n = len(path)
    def touched(gd):
        return any(alive(gd, tt) and (cell(gd, tt) == path[tt] or
                   (alive(gd, tt + 1) and cell(gd, tt) == path[(tt + 1) % n] and cell(gd, tt + 1) == path[tt]))
                   for tt in range(n))
    ghosts = [gd for gd in ghosts if not touched(gd)]
    return path, dots, ghosts

def snake_runner_grid(s, t, g, grid, levels, gx, gy, cell, gap, length=6, dt=0.13):
    pitch = cell + gap
    xy = lambda c: (gx + c[0] * pitch, gy + c[1] * pitch)
    cols = len(grid)
    path, dots, ghosts = snake_runner_route(cols=cols, length=length)
    n = len(path); D = n * dt
    f = lambda st: f"{st / n:.4f}"
    real = {(i, d["weekday"]): levels[d["level"]] for i, wk in enumerate(grid) for d in wk}
    s.raw('<g class="snake-static">' + "".join(
        f'<rect x="{xy(c)[0]:.1f}" y="{xy(c)[1]:.1f}" width="{cell}" height="{cell}" rx="2" fill="{g[v]}"/>'
        for c, v in real.items()) + "</g>")
    parts = ['<g class="snake-anim">']
    for c in real:
        x, y = xy(c)
        parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{cell}" height="{cell}" rx="2" fill="{g[0]}"/>')
    bw, bh = cols * pitch - gap, 7 * pitch - gap
    parts.append(f'<clipPath id="board"><rect x="{gx}" y="{gy}" width="{bw:.1f}" height="{bh:.1f}"/></clipPath>'
                 f'<g clip-path="url(#board)">')
    for d in ghosts + dots:  # slides in past the right edge, then left until eaten or out past the left edge
        s0 = d["s"] - 1                                   # one tick earlier, still outside the board
        x0 = xy((cols, d["r"]))[0]
        x1 = x0 - (d["end"] - s0) * pitch
        y = xy((0, d["r"]))[1]
        parts.append(f'<rect x="{x0:.1f}" y="{y:.1f}" width="{cell}" height="{cell}" rx="2" fill="{g[d["lvl"]]}" opacity="0">'
                     f'<animate attributeName="x" dur="{D:.2f}s" repeatCount="indefinite" '
                     f'values="{x0:.1f};{x0:.1f};{x1:.1f};{x1:.1f}" keyTimes="0;{f(s0)};{f(d["end"])};1"/>'
                     f'<animate attributeName="opacity" dur="{D:.2f}s" repeatCount="indefinite" calcMode="discrete" '
                     f'values="0;1;0" keyTimes="0;{f(s0)};{f(d["end"])}"/></rect>')
    parts.append("</g>")
    snake = t["snake"][:length]          # clay, dark head to light tail
    kt = ";".join(f"{i / n:.4f}" for i in range(n)) + ";1"
    for k in range(length - 1, -1, -1):
        pts = []
        for st in range(n + 1):
            x, y = xy(path[(st - k) % n]); pts.append(f"{x + cell/2:.1f},{y + cell/2:.1f}")
        parts.append(f'<rect x="{-cell/2}" y="{-cell/2}" width="{cell}" height="{cell}" rx="{3 if k == 0 else 2}" fill="{snake[k]}">'
                     f'<animateMotion dur="{D:.2f}s" repeatCount="indefinite" calcMode="linear" '
                     f'values="{";".join(pts)}" keyTimes="{kt}"/></rect>')
    parts.append("</g>")
    s.raw("".join(parts))
    eaten = sum(d["eaten"] for d in dots)
    print(f"  snake runner: {n} ticks, {len(dots)} dots, {eaten} eaten, {len(ghosts)} light dots left alone, {D:.1f}s", file=sys.stderr)

# ------------------------------------------------------------------ hero
def hero(t, g, contrib):
    H = 268
    s = SVG(H, "Mo Fouad. Full-stack engineer shipping products end to end: typed APIs, web apps and mobile, "
               f"from the first schema to the last deploy. "
               f"{contrib['total']:,} contributions in the last {contrib['weeks']} weeks.")
    s.runs(0, 26, [("~ ", t["clay"]), ("$ whoami", t["muted"])], "mono", 13)
    s.text(-3, 104, "Mo Fouad", "display", 70, t["ink"])
    para = ("Full-stack engineer shipping products end to end — typed APIs, web apps and mobile, "
            "from the first schema to the last deploy.")
    y = 148
    for line in wrap("sans", 17.5, para, 420):
        s.text(0, y, line, "sans", 17.5, t["muted"]); y += 28
    # contributions card
    cx, cy, cw, ch = 470, 14, 330, 214
    s.raw(f'<rect x="{cx+.5}" y="{cy+.5}" width="{cw-1}" height="{ch-1}" rx="12" fill="{t["card"]}" stroke="{t["cardline"]}"/>')
    s.text(cx + 20, cy + 30, "contributions", "mono", 12, t["muted"])
    s.text(cx + cw - 20, cy + 30, f"last {contrib['weeks']} weeks", "mono", 12, t["faint"], anchor="end")
    cell, gap = 10, 3.1
    gx, gy = cx + 20, cy + 48
    levels = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}
    (snake_runner_grid if SNAKE_MODE == "runner" else snake_loop_grid)(s, t, g, contrib["grid"], levels, gx, gy, cell, gap)
    by2 = gy + 7 * (cell + gap) + 30
    s.text(cx + 20, by2, f"{contrib['total']:,} contributions", "mono", 11.5, t["muted"])
    lx = cx + cw - 20
    s.text(lx, by2, "more", "mono", 11, t["faint"], anchor="end")
    lx -= tw("mono", 11, "more") + 6
    for k in range(4, -1, -1):
        lx -= cell
        s.raw(f'<rect x="{lx:.1f}" y="{by2-9}" width="{cell}" height="{cell}" rx="2" fill="{g[k]}"/>'); lx -= 3
    s.text(lx - 3, by2, "less", "mono", 11, t["faint"], anchor="end")
    s.hline(H - 0.5, t)
    return s.render(SNAKE_CSS)

# ------------------------------------------------------------------ shipping
def shipping(t, repo):
    H = 262
    s = SVG(H, f"What I'm shipping. {repo['name']}: {repo['desc']} Tags: {', '.join(repo['tags'])}.")
    section_head(s, t, 34, "01 / git log --oneline", "What I'm shipping", "1 active repo")
    top = 130
    s.hline(top, t)
    s.text(0, top + 44, repo["hash"], "mono", 12.5, t["faint"])
    s.raw(f'<circle cx="86" cy="{top+38}" r="4" fill="{t["clay"]}"/>')
    s.text(98, top + 44, repo["name"], "sansb", 19, t["ink"])
    y = top + 72
    for line in wrap("sans", 15, repo["desc"], 400):
        s.text(80, y, line, "sans", 15, t["muted"]); y += 23
    xr = W - 34
    for tg in reversed(repo["tags"]):
        xr = tag(s, t, xr, top + 40, tg) - 8
    # arrow
    ax, ay = W - 8, top + 51
    s.raw(f'<path d="M{ax-9},{ay} L{ax},{ay-9} M{ax-7},{ay-9} L{ax},{ay-9} L{ax},{ay-2}" stroke="{t["muted"]}" '
          f'stroke-width="1.4" fill="none" stroke-linecap="round"/>')
    s.hline(H - 0.5, t)
    return s.render()

# ------------------------------------------------------------------ how I ship (journey)
def stages(t):
    I, M = t["ink"], t["muted"]
    return [
        ("idea", "notes.md", "serif", [[("Teachers turn a", I)], [("PDF into a quiz", I)], [("in one click.", I)]],
         ["Figma", "Obsidian"]),
        ("model", "schema.prisma", "code", [[("model", t["model"]), (" Quiz {", I)], [("  title ", I), ("String", M)],
                                            [("  items ", I), ("Item[]", M)], [("}", I)]], ["Prisma", "PostgreSQL"]),
        ("api", "schema.graphql", "code", [[("type", t["api"]), (" Quiz {", I)], [("  title: ", I), ("String!", M)],
                                            [("  items: ", I), ("[Item!]", M)], [("}", I)]], ["GraphQL", "Node.js", "Fastify"]),
        ("app", "Quiz.tsx", "code", [[("<", I), ("Quiz", t["app"])], [("  id=", I), ("{quizId}", M)],
                                      [("  onDone=", I), ("{save}", M)], [("/>", I)]], ["React", "Next.js", "Expo"]),
        ("live", "release", "status", ["web", "ios", "android"], ["Docker", "AWS", "GitHub Actions"]),
    ]

def how(t):
    n, gap = 5, 12; cw = (W - gap * (n - 1)) / n
    head_top = 34; track_y = 168; card_top = 190; lh = 18; csize = 11
    card_h = 34 + 4 * lh + 8
    tag_top = card_top + card_h + 14; tag_h = 21; tag_gap = 6; tsize = 10.5
    rows_max, layout = 1, []
    for i, st in enumerate(stages(t)):
        x0 = i * (cw + gap); x, row, items = x0, 0, []
        for tg in st[4]:
            w = tw("monob", tsize, tg) + 16
            if x + w > x0 + cw + 0.1:
                row += 1; x = x0
            items.append((x, row, w, tg)); x += w + tag_gap
        rows_max = max(rows_max, row + 1); layout.append(items)
    bracket_y = tag_top + rows_max * tag_h + (rows_max - 1) * tag_gap + 24
    H = bracket_y + 52

    s = SVG(H, "How I ship, from idea to live: idea (Figma, Obsidian), model (Prisma, PostgreSQL), "
               "API (GraphQL, Node.js, Fastify), app (React, Next.js, Expo), live (Docker, AWS, GitHub Actions). "
               "TypeScript end to end.")
    section_head(s, t, head_top, "02 / idea → live", "How I ship", "one product, five steps")
    centers = [i * (cw + gap) + cw / 2 for i in range(n)]
    s.raw(f'<path id="track" d="M{centers[0]:.1f},{track_y} L{centers[-1]:.1f},{track_y}" stroke="{t["line"]}" stroke-width="1.5" fill="none"/>')
    madv = tw("mono", csize, "M")
    for i, (key, fname, kind, lines, _) in enumerate(stages(t)):
        x = i * (cw + gap); c = t[key]; cx = centers[i]
        s.text(cx, track_y - 16, key, "monob", 12.5, c, anchor="middle")
        s.raw(f'<circle cx="{cx:.1f}" cy="{track_y}" r="5" fill="{t["card"]}" stroke="{c}" stroke-width="2"/>')
        s.raw(f'<line x1="{cx:.1f}" y1="{track_y+5}" x2="{cx:.1f}" y2="{card_top}" stroke="{c}" stroke-opacity=".45"/>')
        s.raw(f'<rect x="{x+.75:.1f}" y="{card_top+.75}" width="{cw-1.5:.1f}" height="{card_h-1.5}" rx="9" fill="{t["card"]}"/>')
        s.raw(f'<rect x="{x+.75:.1f}" y="{card_top+.75}" width="{cw-1.5:.1f}" height="{card_h-1.5}" rx="9" '
              f'fill="{c}" fill-opacity="{t["tint"]}" stroke="{c}" stroke-opacity=".65" stroke-width="1.25"/>')
        s.text(x + 11, card_top + 19, fname, "monob", 10.5, c)
        s.raw(f'<line x1="{x:.1f}" y1="{card_top+28}" x2="{x+cw:.1f}" y2="{card_top+28}" stroke="{c}" stroke-opacity=".3"/>')
        by = card_top + 50
        if kind == "code":
            for j, parts in enumerate(lines):
                cxx = x + 11
                for txt, fill in parts:
                    if txt.strip():
                        s.text(cxx, by + j * lh, txt, "mono", csize, fill)
                    cxx += madv * len(txt)
            assert max(sum(len(p) for p, _ in l) for l in lines) * madv < cw - 18, fname
        elif kind == "serif":
            for j, parts in enumerate(lines):
                s.text(x + 11, by + j * lh + 1, parts[0][0], "serif", 14.5, parts[0][1])
                assert tw("serif", 14.5, parts[0][0]) < cw - 18
        else:
            for j, target in enumerate(lines):
                yy = by + j * lh
                s.text(x + 11, yy, target, "mono", csize, t["ink"])
                s.raw(f'<circle cx="{x+cw-52:.1f}" cy="{yy-3.8:.1f}" r="3.6" fill="{t["ok"]}"/>')
                s.text(x + cw - 44, yy, "live", "mono", csize, t["muted"])
        for (tx, row, w, tg) in layout[i]:
            ty = tag_top + row * (tag_h + tag_gap)
            s.raw(f'<rect x="{tx:.1f}" y="{ty}" width="{w:.1f}" height="{tag_h}" rx="{tag_h/2}" fill="{c}" '
                  f'fill-opacity="{t["tagtint"]}" stroke="{c}" stroke-opacity=".45"/>')
            s.text(tx + w / 2, ty + 14.5, tg, "monob", tsize, t["ink"], anchor="middle")
    bx1, bx2 = cw + gap, 3 * (cw + gap) + cw
    s.raw(f'<path d="M{bx1:.1f},{bracket_y-6} L{bx1:.1f},{bracket_y} L{bx2:.1f},{bracket_y} L{bx2:.1f},{bracket_y-6}" '
          f'stroke="{t["faint"]}" fill="none"/>')
    s.text((bx1 + bx2) / 2, bracket_y + 20, "TypeScript, end to end", "serif", 15.5, t["muted"], anchor="middle")
    # motion
    D, move, pause = 7.0, 0.6, 0.5
    arrive, times, pts, tc = [0.0], [0.0, pause], [0, 0], pause
    for k in range(1, n):
        tc += move; arrive.append(tc); times.append(tc); pts.append(k / (n - 1))
        if k < n - 1:
            tc += pause; times.append(tc); pts.append(k / (n - 1))
    vis = (tc + 0.9) / D
    times.append(D); pts.append(1)
    s.raw(f'<circle class="motion" r="4.5" fill="{t["ink"]}"><animateMotion dur="{D}s" repeatCount="indefinite" '
          f'calcMode="linear" keyTimes="{";".join(f"{v/D:.4f}" for v in times)}" keyPoints="{";".join(f"{v:.4f}" for v in pts)}">'
          f'<mpath href="#track"/></animateMotion><animate attributeName="opacity" dur="{D}s" repeatCount="indefinite" '
          f'values="1;1;0;0" keyTimes="0;{vis:.4f};{min(vis+.03,.99):.4f};1"/></circle>')
    for i, a in enumerate(arrive):
        c = t[stages(t)[i][0]]; a0, a1 = a / D, (a + .7) / D
        if a == 0:
            kt, vr, vo = f"0;{a1:.4f};1", "5;15;15", "0.6;0;0"
        else:
            kt, vr, vo = f"0;{a0-.001:.4f};{a0:.4f};{a1:.4f};1", "5;5;5;15;15", "0;0;0.6;0;0"
        s.raw(f'<circle class="motion" cx="{centers[i]:.1f}" cy="{track_y}" r="5" fill="none" stroke="{c}" stroke-width="2" opacity="0">'
              f'<animate attributeName="r" dur="{D}s" repeatCount="indefinite" values="{vr}" keyTimes="{kt}"/>'
              f'<animate attributeName="opacity" dur="{D}s" repeatCount="indefinite" values="{vo}" keyTimes="{kt}"/></circle>')
    s.hline(H - 0.5, t)
    return s.render(REDUCED)

# ------------------------------------------------------------------ toolbox
def toolbox(t):
    cols = [("frontend", ["React", "Next.js", "Vite", "Storybook"]),
            ("mobile", ["React Native", "Expo", "EAS"]),
            ("backend", ["Node · Bun", "Fastify", "GraphQL", "Prisma"]),
            ("infra", ["PostgreSQL", "Docker", "MCP servers", "CI/CD"])]
    H = 300
    s = SVG(H, "Toolbox. Frontend: React, Next.js, Vite, Storybook. Mobile: React Native, Expo, EAS. "
               "Backend: Node, Bun, Fastify, GraphQL, Prisma. Infra: PostgreSQL, Docker, MCP servers, CI/CD. "
               "TypeScript everywhere.")
    section_head(s, t, 34, "03 / cat stack.json", "Toolbox", "TypeScript everywhere")
    cw = W / 4; top = 136
    for i, (k, items) in enumerate(cols):
        x = i * cw + (0 if i == 0 else 22)
        if i:
            s.raw(f'<line x1="{i*cw:.1f}" y1="{top-6}" x2="{i*cw:.1f}" y2="{top + 18 + len(items)*31}" stroke="{t["line"]}"/>')
        s.text(x, top + 8, f'"{k}"', "mono", 12.5, t["key"])
        for j, it in enumerate(items):
            s.text(x, top + 42 + j * 31, it, "sans", 16.5, t["ink"])
    return s.render()

# ------------------------------------------------------------------ contact
def contact(t, email):
    H = 318
    s = SVG(H, f'git commit -m "let\'s build something". Have a product to ship, a gnarly API to untangle, '
               f'or just want to talk shop? My inbox is open: {email}')
    s.raw(f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="14" fill="{t["term"]}" stroke="{t["termline"]}"/>')
    for i, c in enumerate(["#E5534B", "#D9A43B", "#57AB5A"]):
        s.raw(f'<circle cx="{22 + i*18}" cy="22" r="5.5" fill="{c}"/>')
    s.text(88, 26, "zsh — mo-fouad", "mono", 11.5, TERM["muted"])
    s.raw(f'<line x1="0" y1="44" x2="{W}" y2="44" stroke="#3A3936"/>')
    end = s.runs(40, 112, [("$ ", TERM["clay"]), ('git commit -m "let\'s build something"', TERM["ink"])], "mono", 25)
    s.raw(f'<rect class="blink" x="{end+8:.1f}" y="88" width="14" height="30" rx="1.5" fill="{TERM["clay"]}"/>')
    y = 160
    for line in ["Have a product to ship, a gnarly API to untangle, or just want to talk shop?",
                 "My inbox is open."]:
        s.text(40, y, line, "sans", 16.5, TERM["muted"]); y += 27
    # email button
    bw = tw("sansb", 15.5, email) + 64; bx, by, bh = 40, 222, 46
    s.raw(f'<rect x="{bx}" y="{by}" width="{bw:.1f}" height="{bh}" rx="8" fill="{TERM["clay"]}"/>')
    ix, iy = bx + 20, by + 16
    s.raw(f'<rect x="{ix}" y="{iy}" width="16" height="12" rx="2" fill="none" stroke="{TERM["btn_text"]}" stroke-width="1.6"/>'
          f'<path d="M{ix+1},{iy+1.5} L{ix+8},{iy+7} L{ix+15},{iy+1.5}" fill="none" stroke="{TERM["btn_text"]}" stroke-width="1.6"/>')
    s.text(bx + 46, by + 29, email, "sansb", 15.5, TERM["btn_text"])
    return s.render("@keyframes bl{0%,49%{opacity:1}50%,100%{opacity:0}}.blink{animation:bl 1.1s steps(1) infinite}"
                    + REDUCED)

# ------------------------------------------------------------------ footer
def footer(t):
    H = 56
    s = SVG(H, "© 2026 Mo Fouad. Written in TypeScript, shipped on Fridays.")
    s.hline(0.5, t)
    s.text(0, 36, "© 2026 Mo Fouad", "mono", 12, t["faint"])
    s.text(W, 36, "// written in TypeScript, shipped on Fridays", "mono", 12, t["faint"], anchor="end")
    return s.render()

# ------------------------------------------------------------------ data + build
if __name__ == "__main__":
    OUT, CONTRIB = sys.argv[1], sys.argv[2]
    d = json.load(open(CONTRIB))["data"]["viewer"]["contributionsCollection"]["contributionCalendar"]
    weeks = d["weeks"][-22:]
    grid = [[{"weekday": __import__("datetime").date.fromisoformat(x["date"]).isoweekday() % 7, "level": x["contributionLevel"]}
             for x in wk["contributionDays"]] for wk in weeks]
    contrib = {"weeks": len(weeks), "grid": grid,
               "total": sum(x["contributionCount"] for wk in weeks for x in wk["contributionDays"])}
    repo = {"name": "type-prisma-gql", "hash": "30222df",
            "desc": "A lightweight TypeGraphQL for Prisma 7. Write your models once, get GraphQL types and resolvers, "
                    "no reflect-metadata.",
            "tags": ["TypeScript", "GraphQL", "Prisma 7"]}
    EMAIL = "mo.fouad.saga@gmail.com"

    os.makedirs(OUT, exist_ok=True)
    for name, t in THEMES.items():
        for part, svg in (("hero", hero(t, GRID[name], contrib)), ("shipping", shipping(t, repo)), ("how", how(t)),
                          ("toolbox", toolbox(t)), ("contact", contact(t, EMAIL)), ("footer", footer(t))):
            p = os.path.join(OUT, f"{part}-{name}.svg")
            open(p, "w").write(svg)
            print(f"{p}  {os.path.getsize(p)//1024} KB")

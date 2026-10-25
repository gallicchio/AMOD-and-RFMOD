"""A small Manhattan router for the dense tiles: runs inside gen_pcb (KiCad's Python), after the parts are placed
and the hand-drawn wires laid, and connects what a tile declares with `route(net, [a, b, ...])`.

Grid of STEP mm over the tile (plus a margin into the gutters, so a rail via in the gutter can be reached).  Two
layers: the front (where the silk draws the result) and the back, with a via where the path changes layer.  A cell
is blocked on a layer by any pad or track of another net (expanded by the clearance and half the track width), on
the front also by the other footprints' courtyards (soft: a cost, so a track crosses under a part only when it must),
and on both by every via.  Breadth-first with costs (straight 1, turn 4, via 20, courtyard 6), so a route is short
and straight when it can be.  Same-net pads are free to cross.  The result is a list of segments per layer and the
vias; gen_pcb lays them like hand-drawn wires, so the silk and the netlist checks see them the same way.
"""
import heapq, math

STEP = 0.2
CLEAR = 0.2
VIA_D = 0.6


class Grid:
    def __init__(self, x0, y0, x1, y1):
        self.x0, self.y0 = x0, y0
        self.nx = int(round((x1 - x0) / STEP)) + 1
        self.ny = int(round((y1 - y0) / STEP)) + 1
        # cost layers: 0 front, 1 back; -1 = blocked
        self.cost = [[[1.0] * self.ny for _ in range(self.nx)] for _ in range(2)]
        self.via_ok = [[True] * self.ny for _ in range(self.nx)]

    def cells(self, bx0, by0, bx1, by1):
        i0 = max(0, int(math.floor((bx0 - self.x0) / STEP)))
        i1 = min(self.nx - 1, int(math.ceil((bx1 - self.x0) / STEP)))
        j0 = max(0, int(math.floor((by0 - self.y0) / STEP)))
        j1 = min(self.ny - 1, int(math.ceil((by1 - self.y0) / STEP)))
        for i in range(i0, i1 + 1):
            for j in range(j0, j1 + 1):
                yield i, j

    def cells_inside(self, bx0, by0, bx1, by1):
        """The cells whose centres lie inside the box (none when it is thinner than a step: then the nearest one)."""
        i0 = int(math.ceil((bx0 - self.x0) / STEP - 1e-9)); i1 = int(math.floor((bx1 - self.x0) / STEP + 1e-9))
        j0 = int(math.ceil((by0 - self.y0) / STEP - 1e-9)); j1 = int(math.floor((by1 - self.y0) / STEP + 1e-9))
        if i1 < i0:
            i0 = i1 = int(round(((bx0 + bx1) / 2 - self.x0) / STEP))
        if j1 < j0:
            j0 = j1 = int(round(((by0 + by1) / 2 - self.y0) / STEP))
        for i in range(max(0, i0), min(self.nx - 1, i1) + 1):
            for j in range(max(0, j0), min(self.ny - 1, j1) + 1):
                yield i, j

    def block(self, layer, bx0, by0, bx1, by1, grow):
        for i, j in self.cells_inside(bx0 - grow, by0 - grow, bx1 + grow, by1 + grow):
            self.cost[layer][i][j] = -1.0

    def block_circle(self, layer, cx, cy, r):
        for i, j in self.cells_inside(cx - r, cy - r, cx + r, cy + r):
            x, y = self.xy(i, j)
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                self.cost[layer][i][j] = -1.0

    def soft(self, layer, bx0, by0, bx1, by1, extra):
        for i, j in self.cells(bx0, by0, bx1, by1):
            if self.cost[layer][i][j] >= 0:
                self.cost[layer][i][j] += extra

    def no_via(self, bx0, by0, bx1, by1, grow):
        for i, j in self.cells_inside(bx0 - grow, by0 - grow, bx1 + grow, by1 + grow):
            self.via_ok[i][j] = False

    def free(self, layer, bx0, by0, bx1, by1):
        for i, j in self.cells(bx0, by0, bx1, by1):
            self.cost[layer][i][j] = 1.0

    def xy(self, i, j):
        return (self.x0 + i * STEP, self.y0 + j * STEP)

    def ij(self, x, y):
        i = min(self.nx - 1, max(0, int(round((x - self.x0) / STEP))))
        j = min(self.ny - 1, max(0, int(round((y - self.y0) / STEP))))
        return (i, j)


def search(grid, starts, goals, width, via_cost=20.0, turn_cost=4.0):
    """starts / goals: sets of (i, j, layer).  Returns [(i, j, layer), ...] from a start to a goal, or None."""
    INF = float("inf")
    best = {}
    pq = []
    for s in starts:
        best[(s[0], s[1], s[2], -1)] = 0.0
        heapq.heappush(pq, (0.0, s[0], s[1], s[2], -1, None))
    came = {}
    goal_set = set(goals)
    dirs = ((1, 0), (-1, 0), (0, 1), (0, -1))
    while pq:
        c, i, j, l, d, prev = heapq.heappop(pq)
        key = (i, j, l, d)
        if came.get(key, "unset") != "unset":
            continue
        came[key] = prev
        if (i, j, l) in goal_set:
            path = []
            k = key
            while k is not None:
                path.append((k[0], k[1], k[2]))
                k = came[k]
            path.reverse()
            return path
        for nd, (di, dj) in enumerate(dirs):
            ni, nj = i + di, j + dj
            if not (0 <= ni < grid.nx and 0 <= nj < grid.ny):
                continue
            cc = grid.cost[l][ni][nj]
            if cc < 0:
                continue
            nc = c + cc + (turn_cost if (d != -1 and d != nd) else 0.0)
            nk = (ni, nj, l, nd)
            if nc < best.get(nk, INF):
                best[nk] = nc
                heapq.heappush(pq, (nc, ni, nj, l, nd, key))
        # change layer here
        nl = 1 - l
        if grid.via_ok[i][j] and grid.cost[nl][i][j] >= 0:
            nc = c + via_cost
            nk = (i, j, nl, d)
            if nc < best.get(nk, INF):
                best[nk] = nc
                heapq.heappush(pq, (nc, i, j, nl, d, key))
    return None


def simplify(path):
    """Collapse collinear runs: [(x, y, layer)] -> segments per layer and the via points."""
    out = []
    for k, (i, j, l) in enumerate(path):
        if k == 0 or k == len(path) - 1:
            out.append((i, j, l)); continue
        pi, pj, pl = path[k - 1]
        ni, nj, nl = path[k + 1]
        if l != pl or l != nl:
            out.append((i, j, l)); continue
        if (i - pi, j - pj) != (ni - i, nj - j):
            out.append((i, j, l))
    return out

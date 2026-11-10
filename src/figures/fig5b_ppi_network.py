# -*- coding: utf-8 -*-
# --- GitHub-release path bootstrap (auto-generated) ---
import os as _os, sys as _sys
_SRC = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if not _os.path.exists(_os.path.join(_SRC, 'config.py')):
    _SRC = _os.path.dirname(_os.path.abspath(__file__))
if _SRC not in _sys.path:
    _sys.path.insert(0, _SRC)
_PROJECT = _os.environ.get('UKB_PROJECT_ROOT', _os.path.dirname(_SRC))
# ------------------------------------------------------
"""
fig5b_ppi.py — Fig5B + FigS5 compact STRING PPI network redraw (vision sub-agent).

Purpose
-------
Redraw the STRING PPI networks as compact, journal-ready single-column figures:
  * Main  : "Any organ failure" combined PPI network  -> result906/panels/Fig5B.pdf/.png
  * Supp  : the other 5 organs (Heart/Lung/Liver/Kidney/Hematologic)
           -> result906/figures_supp/FigS5_PPI_{..}.pdf/.png

Style (per .audit_fix/fig5b_ppi.md)
  * Tight spring layout (seed=42), no white frame/axes, no title (caption does it).
  * Node size & colour = degree (YlOrRd family, coordinated with Fig5_GO_dotplot),
    hub prominent but small figure stays clean.
  * Only the top (~N) hubs are labelled (official symbols), placed ON their node:
    text is centred inside the circle when it fits (contrast text on the warm
    fill), otherwise tucked just off the node's outward edge with a thin white
    halo so it stays legible.  Pixel-level collision resolution removes
    label-label overlap while a spring + cap keep each label hugging its node.
    No hub ring, no leader lines - the circle reads directly as the protein name.
  * Edges: thin grey lines, width & alpha proportional to combined_score.
  * Arial, 600 dpi.
"""
import os
from pathlib import Path

import numpy as np
import pandas as pd
import networkx as nx
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize, LinearSegmentedColormap
import matplotlib.patheffects as pe

# ----------------------------------------------------------------------
# Paths / font / global style
# ----------------------------------------------------------------------
FD = Path(_PROJECT + '/.cache/fonts')
for fn in ('Arial.ttf', 'Arial-Bold.ttf'):
    p = FD / fn
    if p.exists():
        fm.fontManager.addfont(str(p))

plt.rcParams.update({
    'font.family': 'Arial',
    'font.size': 7.0,
    'figure.dpi': 600,
    'savefig.dpi': 600,
})

EDGE_DIR = Path(_PROJECT + '/result/of903/input907_analysis_output/ppi/top100')  # 907 版(含 brain/Stroke)
OUT_MAIN = Path(_PROJECT + '/result/result906/panels')
OUT_SUPP = Path(_PROJECT + '/result/result906/figures_supp')

ORG_LABEL = {
    'organ': 'Any organ failure',
    'heart': 'Heart', 'lung': 'Lung', 'liver': 'Liver',
    'renal': 'Kidney', 'hemat': 'Hematologic', 'brain': 'Stroke',
}
JOBS = [
    ('organ', 'Fig5B', True),
    ('heart', 'FigS5_PPI_Heart', False),
    ('lung', 'FigS5_PPI_Lung', False),
    ('liver', 'FigS5_PPI_Liver', False),
    ('renal', 'FigS5_PPI_Kidney', False),
    ('hemat', 'FigS5_PPI_Hematologic', False),
    ('brain', 'FigS5_PPI_Stroke', False),
]

# YlOrRd family (coordinated with Fig5_GO_dotplot warm theme)
# 与 Fig5_GO_dotplot 完全同色带 (sig_red), 保持 Fig5 图族呼应
CMAP = LinearSegmentedColormap.from_list('sig_red', [
    (0.00, '#FFEDA0'),
    (0.25, '#FDBF6F'),
    (0.50, '#F07B3F'),
    (0.75, '#D6291C'),
    (1.00, '#5E0008'),
])

# ----------------------------------------------------------------------
# Tunable style parameters
# ----------------------------------------------------------------------
NODE_SMIN = 60.0          # scatter area (pt^2) for the smallest (degree-min) node
NODE_SMAX = 420.0         # scatter area for the largest (degree-max) node
EDGE_W_MIN, EDGE_W_MAX = 0.25, 1.40
EDGE_A_MIN, EDGE_A_MAX = 0.14, 0.60   # raised alpha floor keeps central edges visible
EDGE_COLOR = '#6C7A89'
NODE_EDGE = 'white'
NODE_EDGE_W = 0.45
PAD_FRAC = 0.050          # axis padding as a fraction of the data span

# ---- on-node hub label placement: ALL labels are centred INSIDE the node ----
# Every hub label is drawn at its node's centre ("circle == protein name").
# The font size is adaptive per hub: it is chosen so the label's half-width
# reaches at most INSIDE_WFIT x node radius (i.e. text width <= node diameter
# x coefficient), clamped to [FONT_MIN, FONT_MAX].  Very long symbols in the
# smallest hubs may overflow the circle slightly but stay centre-anchored and
# readable (with a thin halo).  No rings, no leader lines, no edge placement.
INSIDE_WFIT = 0.88        # fraction of node radius the text half-width may reach
FONT_MIN = 4.5            # adaptive font floor (pt)
FONT_MAX = 7.0            # adaptive font ceiling (pt)
TEXT_DARK = '#1A1A1A'
TEXT_LIGHT = '#FFFFFF'
HALO_DARK = '#FFFFFF'     # halo behind dark text (thin white stroke)
HALO_LIGHT = '#2B0A0A'    # halo behind white text (thin dark stroke) for contrast
HALO_LW = 1.2             # halo line width (pt) - very thin
LAYOUT_K = 2.0
LAYOUT_ITERS = 500
HUB_N = {
    'organ': 14,
    'heart': 12, 'lung': 12, 'liver': 12,
    'renal': 12, 'hemat': 12, 'brain': 12,
}

# ---- hub-separation relaxation (de-crowds the core so topology is readable) ----
SEP_PX = 26.0             # target gap (px) between node borders in the core
HUB_BOOST = 1.65          # extra separation applied to hub-hub node pairs
RELAX_ITERS = 400         # relaxation iterations
RELAX_STEP = 0.60         # fraction of residual overlap resolved per iteration
SPRING = 0.020            # pull-back toward the spring anchor (keeps layout compact)

# ---- hub identity: large, high-saturation nodes already signal "hub"; no ring ----

FIG_W_CM = {'organ': 13.6}   # main target width (cm)
FIG_SCALE_SUPP = 0.88


def build_graph(edges_csv):
    df = pd.read_csv(edges_csv)
    G = nx.Graph()
    G.add_edges_from([(r['protein1'], r['protein2'],
                       {'combined_score': float(r['combined_score'])})
                      for _, r in df.iterrows()])
    return G


def spring_layout_centered(G, seed=42):
    """Spring layout, recentred on origin (aspect preserved)."""
    pos = nx.spring_layout(G, k=LAYOUT_K, iterations=LAYOUT_ITERS, seed=seed)
    arr = np.array([pos[n] for n in G.nodes()])
    arr -= arr.mean(axis=0)
    return {n: arr[i] for i, n in enumerate(G.nodes())}


def node_px_radius(deg, dmin, dmax):
    """Node visual radius in pixels, derived from the scatter area (dpi=600)."""
    nor = (deg - dmin) / (dmax - dmin) if dmax > dmin else 0.0
    s = NODE_SMIN + nor * (NODE_SMAX - NODE_SMIN)
    return np.sqrt(s / np.pi) * 600.0 / 72.0


def relax_hubs(G, pos, deg, dmin, dmax, fig_w_cm, sep_px=SEP_PX,
               hub_boost=HUB_BOOST, iters=RELAX_ITERS, step=RELAX_STEP,
               spring=SPRING, hub_n=None, extra_r=None):
    """De-crowd the core: push overlapping node pairs apart in data space.

    Forces a target border-to-border gap (in px) between every node pair whose
    current distance is below it; hub-hub pairs get ``hub_boost`` extra room so
    the top-degree nodes separate enough that the central topology is readable.
    A weak spring toward the original spring anchor keeps the whole 84-node
    graph compact and prevents the non-hub periphery from scattering.  Returns
    the relaxed positions and the calibrated data-units-per-pixel scaling used
    for the ring marker radius.

    ``extra_r`` (optional dict node -> px) adds to a node's own radius in the
    separation test.  Since labels now live centred INSIDE the node, a label
    that is wider than its circle contributes its overflow to ``extra_r`` so
    hubs are pushed far enough apart that no label collides with a neighbour.
    """
    import math
    nodes = list(G.nodes())
    if hub_n is None:
        hub_n = HUB_N.get('organ', 14)
    hubset = set(sorted(nodes, key=lambda n: -deg[n])[:hub_n])
    r_px = {n: node_px_radius(deg[n], dmin, dmax) + (extra_r or {}).get(n, 0.0)
            for n in nodes}

    cur = {n: np.array(pos[n], float) for n in nodes}
    anchor = {n: np.array(pos[n], float) for n in nodes}

    def data_per_px():
        xs = np.array([cur[n][0] for n in nodes])
        ys = np.array([cur[n][1] for n in nodes])
        span = max(xs.max() - xs.min(), ys.max() - ys.min())
        ax_w_in = fig_w_cm / 2.54
        ax_w_px = ax_w_in * 0.85 * 600.0          # subplot(111) ~85% of figure width
        return span / ax_w_px if ax_w_px > 0 else 1.0

    for it in range(iters):
        dpp = data_per_px()
        moved = False
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                ni, nj = nodes[i], nodes[j]
                dx = cur[nj][0] - cur[ni][0]
                dy = cur[nj][1] - cur[ni][1]
                d = math.hypot(dx, dy)
                mind = (r_px[ni] + r_px[nj] + sep_px) * dpp
                if ni in hubset and nj in hubset:
                    mind *= hub_boost
                if d < mind:
                    if d < 1e-9:
                        ea = (it * 0.7) % 6.2832
                        ux, uy = math.cos(ea), math.sin(ea)
                    else:
                        ux, uy = dx / d, dy / d
                    push = (mind - d) * step
                    cur[ni][0] -= ux * push; cur[ni][1] -= uy * push
                    cur[nj][0] += ux * push; cur[nj][1] += uy * push
                    moved = True
        for n in nodes:
            cur[n] = cur[n] + spring * (anchor[n] - cur[n])
        if not moved:
            break
    arr = np.array([cur[n] for n in nodes])
    arr -= arr.mean(axis=0)
    return {n: arr[i] for i, n in enumerate(nodes)}, data_per_px()


def draw_network(G, out_png, out_pdf, fig_w_cm, hub_n, seed=42):
    deg = dict(G.degree())
    nodes = list(G.nodes())
    dvals = np.array([deg[n] for n in nodes], dtype=float)
    dmin, dmax = float(dvals.min()), float(dvals.max())
    nor = (dvals - dmin) / (dmax - dmin) if dmax > dmin else np.zeros_like(dvals)

    node_sizes = NODE_SMIN + nor * (NODE_SMAX - NODE_SMIN)

    fig = plt.figure(figsize=(fig_w_cm / 2.54, fig_w_cm / 2.54))
    ax = fig.add_subplot(111)
    ax.set_aspect('equal')
    rend = fig.canvas.get_renderer()

    # ---- hub identity + node geometry (independent of the layout) ----
    hub = sorted(nodes, key=lambda n: -deg[n])[:hub_n]
    hubset = set(hub)
    node_r = {n: node_px_radius(deg[n], dmin, dmax) for n in nodes}
    sm_tmp = ScalarMappable(norm=Normalize(vmin=dmin, vmax=dmax), cmap=CMAP)
    sm_tmp.set_array([])
    node_c = {n: sm_tmp.to_rgba(deg[n]) for n in nodes}

    def _luma(rgba):
        r, g, b = rgba[0], rgba[1], rgba[2]
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    # ---- fit each hub label to its node centre ----
    # Measure the label's half-width at the ceiling font; the font size that
    # brings the half-width to <= node_radius * INSIDE_WFIT (i.e. text width
    # <= node diameter x coefficient) is chosen, clamped to [FONT_MIN, FONT_MAX].
    # Labels that cannot fit even at FONT_MIN keep the floor size and simply
    # overflow the circle slightly (still centre-anchored).  The overflow is
    # passed to relax_hubs so hub separation keeps labels clear of neighbours.
    fs_of, halfw_of, overflow = {}, {}, {}
    for n in hub:
        r = node_r[n]
        t = ax.text(0.0, 0.0, n, fontsize=FONT_MAX, ha='center', va='center',
                    zorder=4)
        bb = t.get_window_extent(renderer=rend)
        halfw_M, halfh_M = bb.width / 2.0, bb.height / 2.0
        t.remove()
        fs_w = FONT_MAX * (r * INSIDE_WFIT) / halfw_M if halfw_M > 0 else FONT_MAX
        fs_h = FONT_MAX * (r * INSIDE_WFIT) / halfh_M if halfh_M > 0 else FONT_MAX
        fs = min(fs_w, fs_h, FONT_MAX)
        fs_of[n] = max(FONT_MIN, fs)
        # re-measure at the chosen size for the exact overflow it will produce
        t2 = ax.text(0.0, 0.0, n, fontsize=fs_of[n], ha='center', va='center',
                     zorder=4)
        bb2 = t2.get_window_extent(renderer=rend)
        halfw_of[n] = bb2.width / 2.0
        t2.remove()
        overflow[n] = max(0.0, halfw_of[n] - r)

    # layout (seed=42) with hub separation that also clears overflowing labels
    pos0 = spring_layout_centered(G, seed=seed)
    pos, dpp = relax_hubs(G, pos0, deg, dmin, dmax, fig_w_cm,
                          hub_n=hub_n, extra_r=overflow)

    # edges
    for u, v, d in G.edges(data=True):
        s = d['combined_score']
        w = EDGE_W_MIN + (s - 0.4) / 0.6 * (EDGE_W_MAX - EDGE_W_MIN)
        a = EDGE_A_MIN + (s - 0.4) / 0.6 * (EDGE_A_MAX - EDGE_A_MIN)
        ax.plot([pos[u][0], pos[v][0]], [pos[u][1], pos[v][1]],
                color=EDGE_COLOR, linewidth=w, alpha=a, zorder=1)

    # nodes
    ax.scatter(*zip(*[pos[n] for n in nodes]),
               s=node_sizes, c=dvals, cmap=CMAP,
               vmin=dmin, vmax=dmax, alpha=0.95, zorder=2,
               edgecolors=NODE_EDGE, linewidths=NODE_EDGE_W)

    # axis limits (aspect-preserving, centred)
    xs = np.array([pos[n][0] for n in nodes])
    ys = np.array([pos[n][1] for n in nodes])
    padx = PAD_FRAC * (xs.max() - xs.min())
    pady = PAD_FRAC * (ys.max() - ys.min())
    ax.set_xlim(xs.min() - padx, xs.max() + padx)
    ax.set_ylim(ys.min() - pady, ys.max() + pady)
    ax.set_axis_off()
    # =====================================================================
    # Hub labels: EVERY label is drawn at its node's CENTRE (inside circle).
    # Font size was fitted per hub above (text width <= node diameter x
    # coefficient, clamped to [FONT_MIN, FONT_MAX]).  Colour is chosen for
    # contrast against the node's warm fill (light fill -> dark text, dark
    # fill -> white text) and a very thin halo lifts the glyphs off the filled
    # circle / edges.  No hub ring, no leader lines, no edge placement:
    # "circle == protein name" is read directly.
    # =====================================================================
    inv = ax.transData.inverted()
    tgt = ax.transData

    def _to_disp(p):
        return np.array(tgt.transform(p))

    node_disp = {m: _to_disp(np.array(pos[m], float)) for m in nodes}

    texts = {}
    for n in hub:
        luma = _luma(node_c[n])
        tc = TEXT_LIGHT if luma < 0.52 else TEXT_DARK
        halo = HALO_LIGHT if tc == TEXT_LIGHT else HALO_DARK
        t = ax.text(pos[n][0], pos[n][1], n, fontsize=fs_of[n],
                    ha='center', va='center', zorder=5, color=tc)
        t.set_path_effects([pe.withStroke(linewidth=HALO_LW, foreground=halo)])
        texts[n] = t

    # ---- diagnosis: quantify the settled layout (report in the log) ----
    PAD_PX = 3.0

    def _pbox(n):
        bb = texts[n].get_window_extent(renderer=rend)
        w = bb.width + 2 * PAD_PX
        h = bb.height + 2 * PAD_PX
        cx, cy = (bb.x0 + bb.x1) / 2, (bb.y0 + bb.y1) / 2
        from matplotlib.transforms import Bbox
        return Bbox([[cx - w / 2, cy - h / 2], [cx + w / 2, cy + h / 2]])

    boxes = {n: _pbox(n) for n in hub}
    ll_overlap = 0
    for i in range(len(hub)):
        for j in range(i + 1, len(hub)):
            if boxes[hub[i]].overlaps(boxes[hub[j]]):
                ll_overlap += 1
    lnode_overlap = 0
    for n in hub:
        b = boxes[n]
        for m in nodes:
            if m == n:
                continue
            cm = node_disp[m]
            if b.x0 < cm[0] < b.x1 and b.y0 < cm[1] < b.y1:
                overlap = True
            else:
                cx = min(max(cm[0], b.x0), b.x1)
                cy = min(max(cm[1], b.y0), b.y1)
                overlap = ((cm[0] - cx) ** 2 + (cm[1] - cy) ** 2
                           < node_r[m] ** 2)
            if overlap:
                lnode_overlap += 1
                break
    inside = len(hub)        # every hub label is centred inside its node
    n_edges = 0              # no edge placement remains
    fs_vals = [fs_of[n] for n in hub]
    fs_min = round(min(fs_vals), 2)
    fs_max = round(max(fs_vals), 2)

    # ---- small degree colourbar on the right ----
    sm = ScalarMappable(norm=Normalize(vmin=dmin, vmax=dmax), cmap=CMAP)
    sm.set_array([])
    cax = fig.add_axes([0.92, 0.28, 0.02, 0.45])
    cb = fig.colorbar(sm, cax=cax)
    cb.set_label('Degree', fontsize=7.0, labelpad=3)
    cb.ax.tick_params(labelsize=6.0, length=2.5)
    cb.outline.set_linewidth(0.6)
    cb.outline.set_edgecolor('#888888')
    cb.ax.yaxis.set_major_locator(plt.MaxNLocator(5))

    # ---- save ----
    fig.savefig(out_png, dpi=600, bbox_inches='tight', pad_inches=0.02)
    fig.savefig(out_pdf, bbox_inches='tight', pad_inches=0.02)
    from PIL import Image
    im = Image.open(out_png)
    w_cm, h_cm = im.size[0] / 600 * 2.54, im.size[1] / 600 * 2.54
    plt.close(fig)
    return dict(nodes=G.number_of_nodes(), edges=G.number_of_edges(),
                dmin=int(dmin), dmax=int(dmax), hub=hub_n,
                w_cm=round(w_cm, 2), h_cm=round(h_cm, 2),
                centered=inside, edged=n_edges,
                fs_min=fs_min, fs_max=fs_max,
                ll_overlap=ll_overlap, lnode_overlap=lnode_overlap)


def main():
    os.makedirs(OUT_MAIN, exist_ok=True)
    os.makedirs(OUT_SUPP, exist_ok=True)
    print('=' * 70)
    print('Fig5B / FigS5 compact PPI networks (organ + 5 organs)')
    print('=' * 70)
    for key, stem, is_main in JOBS:
        G = build_graph(EDGE_DIR / f'{key}_PPI_edges.csv')
        out_dir = OUT_MAIN if is_main else OUT_SUPP
        stem_p = (out_dir / stem).as_posix()
        fig_w = FIG_W_CM.get('organ', 12.0) if is_main \
            else FIG_W_CM.get('organ', 12.0) * FIG_SCALE_SUPP
        r = draw_network(G, stem_p + '.png', stem_p + '.pdf', fig_w, HUB_N[key])
        print(f"[{ORG_LABEL[key]:<18}] {stem:<22} "
              f"nodes={r['nodes']:>3} edges={r['edges']:>3} "
              f"deg={r['dmin']}-{r['dmax']} hubs={r['hub']} "
              f"size={r['w_cm']}x{r['h_cm']}cm "
              f"center={r['centered']}/edge={r['edged']} "
              f"fs={r['fs_min']}-{r['fs_max']} "
              f"ovl(ll)={r['ll_overlap']} ovl(ln)={r['lnode_overlap']}")


if __name__ == '__main__':
    main()

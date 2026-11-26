#!/usr/bin/env python3
"""Figures.  Every panel is driven by analysis.json; no literal carries data."""
import json, os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 8, "axes.linewidth": 0.6,
    "axes.edgecolor": "#333333", "figure.dpi": 300, "savefig.bbox": "tight",
})

INK = "#1a1a1a"; MUTED = "#6b6b6b"; ACCENT = "#2f5d8a"; LIGHT = "#c9d6e3"


def _save(fig, outdir, name):
    fig.savefig(os.path.join(outdir, name + ".png"))
    fig.savefig(os.path.join(outdir, name + ".pdf"))
    plt.close(fig)


def fig_evidence_map(a, outdir):
    rows = a["evidence_map"]
    doms = ["behaviour", "information", "thought", "emotion"]
    cats = sorted({r["crime_type"] for r in rows})
    M = np.zeros((len(doms), len(cats)))
    for r in rows:
        M[doms.index(r["bite_domain"]), cats.index(r["crime_type"])] = r["n"]
    fig, ax = plt.subplots(figsize=(6.6, 2.5))
    vmax = max(M.max(), 1)
    im = ax.imshow(M, cmap="Blues", vmin=0, vmax=vmax, aspect="auto")
    ax.set_xticks(range(len(cats)))
    ax.set_xticklabels([c.replace("other/unspecified", "other /\nunspecified") for c in cats],
                       rotation=32, ha="right", fontsize=7)
    ax.set_yticks(range(len(doms)))
    ax.set_yticklabels([d.capitalize() for d in doms])
    for i in range(len(doms)):
        for j in range(len(cats)):
            v = int(M[i, j])
            ax.text(j, i, "·" if v == 0 else str(v), ha="center", va="center", fontsize=7,
                    color=(MUTED if v == 0 else ("white" if v > vmax * 0.55 else INK)))
    ax.set_xlabel("Criminal outcome type")
    ax.set_ylabel("Manipulation domain (BITE)")
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0)
    cb = fig.colorbar(im, ax=ax, fraction=0.025, pad=0.02)
    cb.set_label("records", fontsize=7)
    cb.ax.tick_params(labelsize=6)
    ax.set_title("Records by manipulation domain and outcome type (· = no record)",
                 fontsize=8, loc="left")
    _save(fig, outdir, "fig1_evidence_map")


def fig_toolchain(a, outdir):
    tf = a.get("tool_families") or {}
    counts = tf.get("counts") or {}
    N = tf.get("N") or 1
    names = list(counts)
    order = sorted(range(len(names)), key=lambda i: counts[names[i]])
    vals = [counts[names[i]] for i in order]
    fig, ax = plt.subplots(figsize=(6.4, 2.3))
    y = np.arange(len(names))
    ax.barh(y, vals, color=[ACCENT if v else "#e6e6e6" for v in vals],
            edgecolor=INK, linewidth=0.5, height=0.6)
    ax.set_yticks(y)
    ax.set_yticklabels([names[i] for i in order], fontsize=6.6)
    for k, v in enumerate(vals):
        ax.text(v + 0.08, k, "%d/%d" % (v, N), va="center", fontsize=6.5, color=MUTED)
    ax.set_xlim(0, max(3, (max(vals) if vals else 1) * 1.8))
    ax.set_xlabel("Records naming a tool of this family (n)")
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(length=2)
    ax.set_title("Assessment tools named, by family (N = %d records)" % N, fontsize=8, loc="left")
    _save(fig, outdir, "fig2_toolchain")


def fig_reporting(a, outdir):
    ct = a["construct_table"]
    labels = {
        "C1_group_def": "Group definition", "C2_role": "Participant role",
        "C3_duration": "Involvement/exit duration", "C4_mechanism": "Named mechanism",
        "C5_instrument": "Standardised instrument", "C6_offence": "Offence type",
        "C7_severity": "Offence severity", "C8_legal": "Legal outcome",
        "C9_jurisdiction": "Jurisdiction", "C10_source": "Data source",
        "C11_comparison": "Comparison/baseline", "C12_n": "Sample size (n)",
    }
    rows = sorted(ct, key=lambda r: r["pct"])
    fig, ax = plt.subplots(figsize=(5.6, 3.4))
    y = np.arange(len(rows))
    vals = [r["pct"] for r in rows]
    ax.barh(y, vals, color=[ACCENT if v < 50 else LIGHT for v in vals],
            edgecolor=INK, linewidth=0.5, height=0.66)
    ax.set_yticks(y)
    ax.set_yticklabels([labels[r["construct"]] for r in rows], fontsize=7.5)
    for i, r in enumerate(rows):
        ax.text(vals[i] + 1.2, i, "%d/%d" % (r["n_reported_verified"], r["N"]),
                va="center", fontsize=6.5, color=MUTED)
    ax.set_xlim(0, 100)
    ax.set_xlabel("Records reporting the construct in title/abstract (%)")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.tick_params(length=2)
    ax.set_title("Reporting completeness across %d records" % rows[0]["N"], fontsize=8, loc="left")
    _save(fig, outdir, "fig3_reporting")


def fig_loop(a, outdir):
    fig, ax = plt.subplots(figsize=(4.8, 3.1))
    ax.set_xlim(0, 10); ax.set_ylim(0, 6); ax.axis("off")
    boxes = [
        ("Predict", "a mechanism should\nproduce an effect", 5.0, 5.0),
        ("Report", "role, duration, instrument,\noutcome, in comparable form", 8.1, 2.9),
        ("Compare", "studies can be set\nside by side", 5.0, 0.9),
        ("Re-predict", "the effect that survives\ncomparison is the one to test", 1.9, 2.9),
    ]
    for name, sub, x, y in boxes:
        ax.add_patch(plt.Rectangle((x - 1.6, y - 0.62), 3.2, 1.24, facecolor="#f2f5f8",
                                   edgecolor=INK, linewidth=0.7))
        ax.text(x, y + 0.2, name, ha="center", va="center", fontsize=8, fontweight="bold")
        ax.text(x, y - 0.28, sub, ha="center", va="center", fontsize=5.6, color=MUTED)
    arrows = [((6.6, 4.6), (7.4, 3.5)), ((6.6, 2.1), (6.4, 1.5)),
              ((3.4, 1.5), (3.2, 2.1)), ((2.7, 3.5), (3.5, 4.6))]
    for (x1, y1), (x2, y2) in arrows:
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="-|>", color=MUTED, lw=0.9,
                                    connectionstyle="arc3,rad=0.18"))
    ax.set_title("The design loop the reporting set is meant to close", fontsize=8, loc="left")
    _save(fig, outdir, "fig4_loop")


def fig_prisma(a, outdir):
    pr = a["prisma"]
    steps = [
        ("Records identified (%d sources)" % len(pr["identification"]), pr["records_retrieved_total"], None),
        ("Unique records after deduplication", pr["unique_after_cross_db_dedup"],
         "duplicates removed: %d" % (pr["records_retrieved_total"] - pr["unique_after_cross_db_dedup"])),
        ("Records after year/language limits",
         pr["unique_after_cross_db_dedup"] - pr["excluded_year"] - pr["excluded_language"],
         "excluded: year %d, language %d" % (pr["excluded_year"], pr["excluded_language"])),
        ("Records screened at title/abstract", pr["screened"],
         "no base-block match: %d" % pr["excluded_no_base_block"]),
        ("Records included in synthesis", pr["final_included"],
         "auto-excluded: %d; second pass: %d" % (pr["auto_excluded_conf_ge_090"], pr["second_pass_excluded"])),
    ]
    fig, ax = plt.subplots(figsize=(5.6, 4.6))
    ax.set_xlim(0, 11); ax.set_ylim(-0.5, len(steps) * 2 + 0.5)
    ax.axis("off")
    y = len(steps) * 2 - 1
    for i, (label, n, side) in enumerate(steps):
        ax.add_patch(plt.Rectangle((0.3, y - 0.7), 6.6, 1.4, facecolor="#f2f5f8",
                                   edgecolor=INK, linewidth=0.7))
        ax.text(0.6, y + 0.18, label, fontsize=7.4, va="center")
        if n is not None:
            ax.text(6.6, y - 0.22, "n = %d" % n, fontsize=9, va="center", ha="right",
                    fontweight="bold")
        if side:
            ax.annotate(side, xy=(7.1, y), xytext=(7.5, y), fontsize=6.4, va="center",
                        color=MUTED,
                        arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.6))
        if i < len(steps) - 1:
            ax.annotate("", xy=(3.6, y - 2 + 0.72), xytext=(3.6, y - 0.72),
                        arrowprops=dict(arrowstyle="-|>", color=INK, lw=0.9))
        y -= 2
    ax.set_title("PRISMA-ScR flow", fontsize=8.5, loc="left")
    _save(fig, outdir, "figS1_prisma")


def fig_fulltext_lift(a, outdir):
    fl = a.get("fulltext_lift") or {}
    pc = fl.get("per_construct") or {}
    if not pc:
        return
    keys = ["C5_instrument", "C11_comparison", "C3_duration", "C12_n", "C4_mechanism",
            "C7_severity", "C1_group_def", "C2_role", "C8_legal", "C10_source",
            "C6_offence", "C9_jurisdiction"]
    labels = {"C1_group_def": "Group definition", "C2_role": "Participant role",
              "C3_duration": "Duration", "C4_mechanism": "Named mechanism",
              "C5_instrument": "Instrument", "C6_offence": "Offence type",
              "C7_severity": "Severity", "C8_legal": "Legal outcome",
              "C9_jurisdiction": "Jurisdiction", "C10_source": "Data source",
              "C11_comparison": "Comparison", "C12_n": "Sample size"}
    keys = [k for k in keys if k in pc]
    y = np.arange(len(keys))
    ab = [pc[k]["abstract_pct"] for k in keys]
    ft = [pc[k]["fulltext_pct"] for k in keys]
    fig, ax = plt.subplots(figsize=(5.8, 3.6))
    ax.scatter(ab, y, s=26, color=ACCENT, label="abstract", zorder=3)
    ax.scatter(ft, y, s=26, color="#c0504d", label="full text", zorder=3)
    for i, k in enumerate(keys):
        ax.plot([ab[i], ft[i]], [i, i], color="#bbbbbb", lw=1.0, zorder=1)
    ax.set_yticks(y)
    ax.set_yticklabels([labels[k] for k in keys], fontsize=7.4)
    ax.set_xlabel("% of records reporting the construct")
    ax.set_xlim(0, 100)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.legend(frameon=False, fontsize=7, loc="lower right")
    n = fl.get("n_pairs")
    ax.set_title("Same %s records, abstract versus full text" % n, fontsize=8, loc="left")
    _save(fig, outdir, "fig5_fulltext_lift")


def main(analysis_path, outdir):
    a = json.load(open(analysis_path, encoding="utf8"))
    os.makedirs(outdir, exist_ok=True)
    fig_evidence_map(a, outdir)
    fig_toolchain(a, outdir)
    fig_reporting(a, outdir)
    fig_loop(a, outdir)
    fig_prisma(a, outdir)
    fig_fulltext_lift(a, outdir)
    print("FIGURES_DONE", outdir)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

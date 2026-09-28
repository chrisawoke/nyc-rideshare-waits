"""
The three charts the write-up uses, drawn from outputs/ (run run_analysis.py first).

Each chart carries no title of its own: the heading above it on the page states its point,
and a title inside the image would either repeat that or disagree with it. Colours are
teal-600 and coral-600 from the site's palette, checked for colour-blind separation and
contrast against this navy surface.

Each chart is drawn twice. A 10-inch chart shown on a phone is about 350px wide, which puts
its labels near 6px; the phone version is a narrower canvas with the same type sizes, so the
words come out roughly twice as large. The page shows whichever fits.
"""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

OUT = Path("outputs")
CHARTS = Path("charts")
CHARTS.mkdir(exist_ok=True)

NAVY = "#0a192f"
TEAL = "#22a99c"
CORAL = "#e85a2d"
TEXT = "#ffffffd9"
MUTED = "#ffffff80"

PHONE = False


def canvas():
    fig, ax = plt.subplots(figsize=(4.6, 5.4) if PHONE else (10, 5.6), dpi=200)
    fig.patch.set_facecolor(NAVY)
    ax.set_facecolor(NAVY)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(colors=MUTED, length=0, labelsize=11)
    return fig, ax


def save(fig, name):
    if PHONE:
        name = name.replace(".png", "_phone.png")
    fig.tight_layout(pad=1.2)
    fig.savefig(CHARTS / name, facecolor=NAVY, bbox_inches="tight", pad_inches=0.3)
    plt.close(fig)
    print(f"saved charts/{name}")


def by_hour():
    """Long-wait rate by hour: the problem is a late-night one, with a second peak at rush hour."""
    df = pd.read_csv(OUT / "by_hour.csv")
    avg = pd.read_csv(OUT / "headline.csv")["long_wait_pct"].iloc[0]
    fig, ax = canvas()

    # 22:00 to 04:59 is the late-night segment the recommendation targets; shading both
    # ends of the day keeps it readable as one window on a 0-23 axis.
    for lo, hi in ((-0.5, 4.5), (21.5, 23.5)):
        ax.axvspan(lo, hi, color="#ffffff", alpha=0.05, lw=0)
    ax.text(2, 23.4, "Late night", color=MUTED, fontsize=11, ha="center", style="italic")

    ax.axhline(avg, color="#ffffff", alpha=0.3, lw=1, ls=(0, (2, 3)))
    if not PHONE:
        ax.text(8.4, avg + 0.5, f"Month average {avg:.0f}%", color=MUTED, fontsize=10.5)

    ax.plot(df["hr"], df["long_wait_pct"], color=TEAL, lw=2.75, solid_capstyle="round", zorder=3)
    ax.scatter(df["hr"], df["long_wait_pct"], s=26, color=TEAL, zorder=4, edgecolor=NAVY, linewidth=2)

    peak = df.loc[df["long_wait_pct"].idxmax()]
    low = df.loc[df["long_wait_pct"].idxmin()]
    ax.annotate(f"{peak.long_wait_pct:.0f}% at 4am", xy=(peak.hr, peak.long_wait_pct), xytext=(10, 6),
                textcoords="offset points", color=TEXT, fontsize=12, fontweight="bold")
    ax.annotate(f"{low.long_wait_pct:.0f}% at 10am", xy=(low.hr, low.long_wait_pct), xytext=(0, -20),
                textcoords="offset points", color=TEXT, fontsize=12, fontweight="bold", ha="center")

    ax.set_xlim(-0.5, 23.5)
    ax.set_ylim(0, 25)
    if PHONE:
        ax.set_xticks([0, 6, 12, 18])
        ax.set_xticklabels(["12am", "6am", "12pm", "6pm"])
    else:
        ax.set_xticks([0, 3, 6, 9, 12, 15, 18, 21])
        ax.set_xticklabels(["12am", "3am", "6am", "9am", "12pm", "3pm", "6pm", "9pm"])
    ax.set_yticks([0, 5, 10, 15, 20, 25])
    ax.set_yticklabels(["0", "5", "10", "15", "20", "25%"])
    ax.set_ylabel("Rides waiting over 10 minutes", color=MUTED, fontsize=11, labelpad=10)
    ax.grid(axis="y", color="#ffffff", alpha=0.08, lw=1)
    ax.set_axisbelow(True)
    save(fig, "by_hour.png")


def wait_split():
    """Where the minutes of a wait go: almost all of it is the driver still on the way."""
    df = pd.read_csv(OUT / "wait_split.csv").set_index("group_name")
    rows = ["Long waits, airports", "Long waits, city", "All rides"]
    labels = ["Long waits at JFK\nand LaGuardia", "Long waits\nelsewhere", "All rides"]
    df = df.loc[rows]
    fig, ax = canvas()

    y = range(len(rows))
    ax.barh(y, df["to_arrive_min"], color=TEAL, height=0.5, zorder=3)
    # The navy edge is the 2px gap between the two segments of a stacked bar.
    ax.barh(y, df["at_curb_min"], left=df["to_arrive_min"], color=CORAL, height=0.5,
            edgecolor=NAVY, linewidth=2, zorder=3)

    for i, (_, r) in enumerate(df.iterrows()):
        total = r.to_arrive_min + r.at_curb_min
        share = f"{r.to_arrive_share_pct:.0f}%"
        label = f"{total:.1f} min\n{share} driver" if PHONE else f"{total:.1f} min, {share} waiting for the driver"
        ax.text(total + 0.3, i, label,
                color=TEXT, fontsize=11.5, va="center")

    # Direct labels under the longest bar instead of a legend box.
    big = df.iloc[0]
    if PHONE:
        # Too narrow to sit side by side: one under the other, each by its own segment.
        ax.text(0, -0.34, "Driver on the way", color=TEAL, fontsize=11, fontweight="bold", ha="left", va="top")
        ax.text(big.to_arrive_min + big.at_curb_min, -0.62, "At the curb", color=CORAL, fontsize=11,
                fontweight="bold", ha="right", va="top")
    else:
        ax.text(big.to_arrive_min / 2, -0.34, "Driver on the way", color=TEAL, fontsize=11,
                fontweight="bold", ha="center", va="top")
        ax.text(big.to_arrive_min + big.at_curb_min / 2, -0.34, "At the curb", color=CORAL, fontsize=11,
                fontweight="bold", ha="center", va="top")

    ax.set_yticks(list(y))
    ax.set_yticklabels(labels, color=TEXT, fontsize=11.5)
    ax.set_xlim(0, 21 if PHONE else 27)
    ax.set_xticks([0, 5, 10, 15])
    ax.set_xticklabels(["0", "5", "10", "15 min"])
    ax.set_ylim(-1.0 if PHONE else -0.75, 2.45)
    ax.grid(axis="x", color="#ffffff", alpha=0.08, lw=1)
    ax.set_axisbelow(True)
    save(fig, "wait_split.png")


def concentration():
    """A tenth of the zone-hours hold over two fifths of the long waits."""
    df = pd.read_csv(OUT / "concentration_curve.csv")
    top = pd.read_csv(OUT / "top_tenth.csv").iloc[0]
    fig, ax = canvas()

    ax.plot([0, 100], [0, 100], color="#ffffff", alpha=0.3, lw=1, ls=(0, (2, 3)))
    even = "If long waits were\nspread evenly" if PHONE else "If long waits were spread evenly"
    ax.text(*((58, 14) if PHONE else (62, 55)), even, color=MUTED, fontsize=10.5)

    ax.plot(df["pct_of_zone_hours"], df["pct_of_long_waits"], color=TEAL, lw=2.75, zorder=3)
    ax.fill_between(df["pct_of_zone_hours"], df["pct_of_long_waits"], df["pct_of_zone_hours"],
                    color=TEAL, alpha=0.08, lw=0)

    x, yv = 10, top.share_of_long_waits_pct
    ax.plot([x, x], [0, yv], color=CORAL, lw=1.25, ls=(0, (2, 2)), zorder=2)
    ax.plot([0, x], [yv, yv], color=CORAL, lw=1.25, ls=(0, (2, 2)), zorder=2)
    ax.scatter([x], [yv], s=90, color=CORAL, edgecolor=NAVY, linewidth=2, zorder=5)
    ax.annotate(f"The top 10% of zone-hours\nhold {yv:.0f}% of long waits", xy=(x, yv), xytext=(16, -6),
                textcoords="offset points", color=TEXT, fontsize=12, fontweight="bold", va="top")

    ax.set_xlim(0, 100)
    ax.set_ylim(0, 102)
    ax.set_xticks([0, 10, 25, 50, 75, 100])
    ax.set_xticklabels(["0", "10", "25", "50", "75", "100%"])
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_yticklabels(["0", "25", "50", "75", "100%"])
    ax.set_xlabel("Zone-hours, worst first", color=MUTED, fontsize=11, labelpad=10)
    ax.set_ylabel("Share of all long waits", color=MUTED, fontsize=11, labelpad=10)
    ax.grid(color="#ffffff", alpha=0.08, lw=1)
    ax.set_axisbelow(True)
    save(fig, "concentration.png")


if __name__ == "__main__":
    for PHONE in (False, True):
        by_hour()
        wait_split()
        concentration()

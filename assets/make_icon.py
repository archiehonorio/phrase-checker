"""Generate a terminal/cmd-style app icon (assets/icon.ico + static/favicon.png).

Draws a dark rounded "console window" with a green ">_" prompt. Vector-style
(lines/rects, no font dependency) so it stays crisp at every size.
"""

from pathlib import Path
from PIL import Image, ImageDraw

S = 1024  # supersample canvas, then downscale
BG = (12, 12, 12, 255)        # cmd black
BAR = (32, 32, 32, 255)       # title bar
DOT = (90, 90, 90, 255)
GREEN = (22, 198, 12, 255)    # classic console green
BORDER = (60, 60, 60, 255)


def rounded(draw, box, r, fill, outline=None, width=1):
    draw.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)


def build() -> Image.Image:
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    m = int(S * 0.07)                       # outer margin
    win = (m, m, S - m, S - m)
    rad = int(S * 0.13)

    # window body + border
    rounded(d, win, rad, BG, outline=BORDER, width=int(S * 0.012))

    # title bar
    bar_h = int(S * 0.16)
    rounded(d, (m, m, S - m, m + bar_h + rad), rad, BAR)
    d.rectangle((m, m + bar_h, S - m, m + bar_h + 2), fill=BG)
    d.rectangle((m + 1, m + bar_h - rad, S - m - 1, m + bar_h), fill=BAR)

    # three traffic-light dots
    cy = m + bar_h // 2
    r = int(S * 0.022)
    for i, x in enumerate([0.13, 0.19, 0.25]):
        cx = int(S * x)
        col = [(255, 95, 86, 255), (255, 189, 46, 255), (39, 201, 63, 255)][i]
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=col)

    # ">" prompt chevron
    lw = int(S * 0.055)
    top = (int(S * 0.30), int(S * 0.46))
    apex = (int(S * 0.48), int(S * 0.60))
    bot = (int(S * 0.30), int(S * 0.74))
    d.line([top, apex], fill=GREEN, width=lw, joint="curve")
    d.line([apex, bot], fill=GREEN, width=lw, joint="curve")

    # "_" cursor / underscore
    ux1, ux2 = int(S * 0.52), int(S * 0.72)
    uy = int(S * 0.71)
    rounded(d, (ux1, uy, ux2, uy + lw), lw // 2, GREEN)

    return img


def main():
    here = Path(__file__).resolve().parent
    root = here.parent
    big = build()

    sizes = [16, 24, 32, 48, 64, 128, 256]
    frames = [big.resize((s, s), Image.LANCZOS) for s in sizes]

    ico_path = here / "icon.ico"
    frames[-1].save(ico_path, format="ICO", sizes=[(s, s) for s in sizes])

    # favicon for the web/window
    static = root / "src" / "phrasecheck" / "web" / "static"
    static.mkdir(parents=True, exist_ok=True)
    big.resize((256, 256), Image.LANCZOS).save(static / "favicon.png")

    print("wrote", ico_path)
    print("wrote", static / "favicon.png")


if __name__ == "__main__":
    main()

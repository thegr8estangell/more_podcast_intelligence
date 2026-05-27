"""
more-podcast-intelligence / send_report.py
Reads podcast_data.json and sends a formatted HTML email
with Spotify, YouTube, and Podcast Index sections.
"""

import json
import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
GMAIL_EMAIL    = os.environ["GMAIL_EMAIL"]
GMAIL_PASSWORD = os.environ["GMAIL_PASSWORD"]
REPORT_EMAIL   = os.environ["REPORT_EMAIL"]

RED            = "#C6002B"
DARK           = "#101820"
GRAY           = "#919395"
WHITE          = "#FFFFFF"
BORDER         = "#E0E0E0"

SPOTIFY_GREEN  = "#1DB954"
YOUTUBE_RED    = "#FF0000"
PI_PURPLE      = "#6B4FBB"

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

IHEART_BADGE = (
    '<span style="display:inline-block;background:#C6002B;color:#fff;'
    'font-size:9px;font-weight:700;letter-spacing:0.08em;padding:2px 6px;'
    'border-radius:3px;margin-left:6px;vertical-align:middle;'
    'text-transform:uppercase;">iHeart</span>'
)


def iheart_badge(show: dict) -> str:
    return IHEART_BADGE if show.get("iheart") else ""


def count_box(label: str, count: int, accent: str) -> str:
    return (
        f'<td style="text-align:left;padding-right:12px;">'
        f'<div style="display:inline-block;background:{WHITE};border:1px solid {BORDER};'
        f'border-radius:6px;padding:10px 16px;min-width:80px;">'
        f'<div style="font-size:22px;font-weight:700;color:{accent};line-height:1;">{count}</div>'
        f'<div style="font-size:10px;color:{GRAY};font-weight:600;'
        f'letter-spacing:0.1em;text-transform:uppercase;margin-top:3px;">{label}</div>'
        f'</div></td>'
    )


def section_header(title: str, subtitle: str, accent: str, emoji: str) -> str:
    return f"""
    <tr>
      <td style="padding:0 0 16px 0;">
        <table width="100%" cellpadding="0" cellspacing="0" border="0">
          <tr>
            <td>
              <div style="border-left:4px solid {accent};padding-left:12px;">
                <div style="font-size:18px;font-weight:700;color:{DARK};line-height:1.2;">
                  {emoji} {title}
                </div>
                <div style="font-size:11px;color:{GRAY};margin-top:3px;">{subtitle}</div>
              </div>
            </td>
          </tr>
        </table>
      </td>
    </tr>
    """


def count_row(sections: list) -> str:
    cells = "".join(
        count_box(s["label"], s["count"], s["accent"])
        for s in sections
    )
    return f"""
    <tr>
      <td style="padding:0 0 20px 0;">
        <table cellpadding="0" cellspacing="0" border="0"><tr>{cells}</tr></table>
      </td>
    </tr>
    """


def show_row(show: dict, accent: str) -> str:
    rank   = show.get("rank", "")
    title  = show.get("title", "Unknown")
    author = show.get("author", "")
    img    = show.get("image", "")
    url    = show.get("url", "#")
    badge  = iheart_badge(show)

    author_line = (
        f'<div style="font-size:11px;color:{GRAY};margin-top:2px;">{author}</div>'
        if author else ""
    )
    img_html = (
        f'<img src="{img}" width="40" height="40" style="width:40px;height:40px;'
        f'object-fit:cover;display:block;" />'
        if img else ""
    )

    return f"""
    <tr>
      <td style="padding:8px 0;border-bottom:1px solid {BORDER};">
        <table width="100%" cellpadding="0" cellspacing="0" border="0">
          <tr>
            <td width="28" style="vertical-align:middle;padding-right:8px;">
              <div style="font-size:13px;font-weight:700;color:{accent};text-align:right;">{rank}</div>
            </td>
            <td width="44" style="vertical-align:middle;padding-right:10px;">
              <div style="width:40px;height:40px;background:#f0f0f0;border-radius:5px;overflow:hidden;">
                {img_html}
              </div>
            </td>
            <td style="vertical-align:middle;">
              <div style="font-size:13px;font-weight:600;color:{DARK};">
                <a href="{url}" style="color:{DARK};text-decoration:none;">{title}</a>
                {badge}
              </div>
              {author_line}
            </td>
          </tr>
        </table>
      </td>
    </tr>
    """


def featured_card(show: dict, accent: str) -> str:
    title  = show.get("title", "Unknown")
    author = show.get("author", "")
    img    = show.get("image", "")
    url    = show.get("url", "#")
    badge  = iheart_badge(show)

    img_html = (
        f'<img src="{img}" width="100%" style="width:100%;height:80px;'
        f'object-fit:cover;display:block;border-radius:6px 6px 0 0;" />'
        if img else
        f'<div style="width:100%;height:80px;background:#e8e8e8;border-radius:6px 6px 0 0;"></div>'
    )
    author_line = (
        f'<div style="font-size:10px;color:{GRAY};margin-top:2px;">{author}</div>'
        if author else ""
    )

    return f"""
    <td style="vertical-align:top;padding:4px;">
      <div style="background:{WHITE};border:1px solid {BORDER};border-radius:8px;overflow:hidden;">
        <a href="{url}" style="text-decoration:none;">{img_html}</a>
        <div style="padding:8px 10px 10px;">
          <div style="font-size:12px;font-weight:600;color:{DARK};line-height:1.3;">
            <a href="{url}" style="color:{DARK};text-decoration:none;">{title}</a>
            {badge}
          </div>
          {author_line}
        </div>
      </div>
    </td>
    """


def two_col_section(left_title: str, left_shows: list,
                    right_title: str, right_shows: list,
                    accent: str) -> str:
    """Side-by-side: featured cards left | ranked list right."""
    left_rows = ""
    for i in range(0, len(left_shows), 2):
        pair  = left_shows[i:i+2]
        cells = "".join(featured_card(s, accent) for s in pair)
        if len(pair) == 1:
            cells += '<td style="padding:4px;"></td>'
        left_rows += f"<tr>{cells}</tr>"

    left_html = f"""
    <table width="100%" cellpadding="0" cellspacing="0" border="0">
      <tr><td style="padding-bottom:8px;">
        <div style="font-size:10px;font-weight:700;letter-spacing:0.15em;
                    text-transform:uppercase;color:{GRAY};">{left_title}</div>
      </td></tr>
      <tr><td>
        <table width="100%" cellpadding="0" cellspacing="0" border="0">{left_rows}</table>
      </td></tr>
    </table>
    """

    right_rows = "".join(show_row(s, accent) for s in right_shows)
    right_html = f"""
    <table width="100%" cellpadding="0" cellspacing="0" border="0">
      <tr><td style="padding-bottom:8px;">
        <div style="font-size:10px;font-weight:700;letter-spacing:0.15em;
                    text-transform:uppercase;color:{GRAY};">{right_title}</div>
      </td></tr>
      <tr><td>
        <table width="100%" cellpadding="0" cellspacing="0" border="0">{right_rows}</table>
      </td></tr>
    </table>
    """

    return f"""
    <tr>
      <td style="padding:0 0 8px 0;">
        <table width="100%" cellpadding="0" cellspacing="0" border="0">
          <tr>
            <td width="48%" style="vertical-align:top;padding-right:12px;">{left_html}</td>
            <td width="4%" style="vertical-align:top;">
              <div style="width:1px;background:{BORDER};height:100%;min-height:200px;margin:0 auto;"></div>
            </td>
            <td width="48%" style="vertical-align:top;padding-left:12px;">{right_html}</td>
          </tr>
        </table>
      </td>
    </tr>
    """


def full_width_list(label: str, shows: list, accent: str) -> str:
    rows = "".join(show_row(s, accent) for s in shows)
    return f"""
    <tr>
      <td style="padding:0 0 8px 0;">
        <div style="font-size:10px;font-weight:700;letter-spacing:0.15em;
                    text-transform:uppercase;color:{GRAY};margin-bottom:12px;">{label}</div>
        <table width="100%" cellpadding="0" cellspacing="0" border="0">{rows}</table>
      </td>
    </tr>
    """


def platform_divider() -> str:
    return """
    <tr>
      <td style="padding:24px 0;">
        <div style="height:1px;background:#e0e0e0;"></div>
      </td>
    </tr>
    """


# ─────────────────────────────────────────────
# BUILD EMAIL
# ─────────────────────────────────────────────

def build_email(data: dict) -> str:
    today   = data.get("date", datetime.now().strftime("%Y-%m-%d"))
    spotify = data.get("spotify",       {})
    youtube = data.get("youtube",       {})
    pi      = data.get("podcast_index", {})

    sp_editors = spotify.get("editors_pick", [])
    sp_shows   = spotify.get("top_shows",    [])
    yt_shows   = youtube.get("top_shows",    [])
    pi_shows   = pi.get("top_shows",         [])

    all_shows    = sp_editors + sp_shows + yt_shows + pi_shows
    iheart_count = sum(1 for s in all_shows if s.get("iheart"))

    try:
        date_str = datetime.strptime(today, "%Y-%m-%d").strftime("%B %d, %Y")
    except Exception:
        date_str = today

    # ── SPOTIFY ──────────────────────────────
    sp_header = section_header(
        "Spotify", "Spotify Web API · Top Shows & Editors Pick",
        SPOTIFY_GREEN, "🟢"
    )
    sp_counts = count_row([
        {"label": "Editors Pick", "count": len(sp_editors), "accent": SPOTIFY_GREEN},
        {"label": "Top Shows",    "count": len(sp_shows),   "accent": SPOTIFY_GREEN},
        {"label": "iHeart",       "count": sum(1 for s in sp_editors + sp_shows if s.get("iheart")), "accent": RED},
    ])
    if sp_editors and sp_shows:
        sp_body = two_col_section("Editors Pick", sp_editors, "Top 20 Shows", sp_shows, SPOTIFY_GREEN)
    elif sp_shows:
        sp_body = full_width_list("Top 5 Shows", sp_shows, SPOTIFY_GREEN)
    else:
        sp_body = "<tr><td style='padding:16px;color:#999;font-size:13px;'>No data available this week.</td></tr>"

    # ── YOUTUBE ──────────────────────────────
    yt_header = section_header(
        "YouTube", "charts.youtube.com/podcasts · Weekly by watchtime",
        YOUTUBE_RED, "🔴"
    )
    yt_counts = count_row([
        {"label": "Top Shows", "count": len(yt_shows), "accent": YOUTUBE_RED},
        {"label": "iHeart",    "count": sum(1 for s in yt_shows if s.get("iheart")), "accent": RED},
    ])
    yt_body = full_width_list("Top 20 Shows", yt_shows, YOUTUBE_RED) if yt_shows else \
        "<tr><td style='padding:16px;color:#999;font-size:13px;'>No data available this week.</td></tr>"

    # ── PODCAST INDEX ────────────────────────
    pi_header = section_header(
        "Podcast Index", "api.podcastindex.org · Trending past 7 days",
        PI_PURPLE, "🎙️"
    )
    pi_counts = count_row([
        {"label": "Trending",  "count": len(pi_shows), "accent": PI_PURPLE},
        {"label": "iHeart",    "count": sum(1 for s in pi_shows if s.get("iheart")), "accent": RED},
    ])
    pi_body = full_width_list("Top 10 Trending", pi_shows, PI_PURPLE) if pi_shows else \
        "<tr><td style='padding:16px;color:#999;font-size:13px;'>No data available this week.</td></tr>"

    # ── iHEART SUMMARY BAR ───────────────────
    iheart_bar = ""
    if iheart_count > 0:
        iheart_bar = f"""
        <tr>
          <td bgcolor="{DARK}" style="background-color:{DARK};padding:12px 28px;">
            <span style="display:inline-block;background:{RED};color:#fff;
              font-size:11px;font-weight:700;padding:4px 10px;border-radius:4px;
              letter-spacing:0.08em;text-transform:uppercase;">iHeart</span>
            <span style="font-size:12px;color:rgba(255,255,255,0.8);margin-left:10px;">
              {iheart_count} iHeartMedia show{'s' if iheart_count != 1 else ''} detected across all platforms this week
            </span>
          </td>
        </tr>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>More Podcast Intelligence — {date_str}</title>
</head>
<body style="margin:0;padding:0;background-color:#F5F5F5;font-family:Arial,Helvetica,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="#F5F5F5">
    <tr>
      <td align="center" style="padding:24px 16px;">
        <table width="620" cellpadding="0" cellspacing="0" border="0" style="max-width:620px;width:100%;">

          <!-- HEADER -->
          <tr>
            <td bgcolor="{RED}" style="background-color:{RED};border-radius:10px 10px 0 0;padding:20px 28px;">
              <div style="font-size:20px;font-weight:700;color:#fff;letter-spacing:-0.3px;">🎙️ More Podcast Intelligence</div>
              <div style="font-size:12px;color:rgba(255,255,255,0.75);margin-top:4px;">
                {date_str} · Spotify · YouTube · Podcast Index
              </div>
            </td>
          </tr>

          {iheart_bar}

          <!-- BODY -->
          <tr>
            <td bgcolor="{WHITE}" style="background-color:{WHITE};border-radius:0 0 10px 10px;padding:28px;">
              <table width="100%" cellpadding="0" cellspacing="0" border="0">

                {sp_header}
                {sp_counts}
                {sp_body}

                {platform_divider()}

                {yt_header}
                {yt_counts}
                {yt_body}

                {platform_divider()}

                {pi_header}
                {pi_counts}
                {pi_body}

                <!-- FOOTER -->
                <tr>
                  <td style="padding-top:28px;border-top:1px solid {BORDER};">
                    <div style="font-size:11px;color:{GRAY};line-height:1.6;">
                      iHeartMedia Podcast Intelligence · {date_str}<br/>
                      Sources: Spotify Web API · YouTube Charts · Podcast Index API
                    </div>
                  </td>
                </tr>

              </table>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

    return html


# ─────────────────────────────────────────────
# SEND
# ─────────────────────────────────────────────

def send_email(html: str, date_str: str):
    print(f"\n📧 Sending report to {REPORT_EMAIL}...")
    try:
        msg            = MIMEMultipart("alternative")
        msg["Subject"] = f"More Podcast Intelligence — {date_str}"
        msg["From"]    = GMAIL_EMAIL
        msg["To"]      = REPORT_EMAIL
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(GMAIL_EMAIL, GMAIL_PASSWORD)
            server.sendmail(GMAIL_EMAIL, REPORT_EMAIL, msg.as_string())

        print("  ✅ Report sent!")
    except Exception as e:
        print(f"  ⚠️ Failed to send: {e}")
        raise


if __name__ == "__main__":
    print("\n📬 Building email report...")

    try:
        with open("podcast_data.json") as f:
            data = json.load(f)
    except FileNotFoundError:
        print("⚠️  podcast_data.json not found — run scraper.py first")
        exit(1)

    html     = build_email(data)
    date_str = data.get("date", datetime.now().strftime("%Y-%m-%d"))

    with open("email_preview.html", "w") as f:
        f.write(html)
    print("  💾 Preview saved to email_preview.html")

    send_email(html, date_str)

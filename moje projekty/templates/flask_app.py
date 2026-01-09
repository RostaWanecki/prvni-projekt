
from flask import Flask, render_template_string
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

def load_data_from_sqlite():
    conn = sqlite3.connect("weather.db")
    df = pd.read_sql_query("SELECT * FROM marine_weather", conn)
    conn.close()
    return df

def plot_to_base64(fig):
    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", dpi=140)  # trochu ostřejší
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)
    return encoded

@app.route("/")
def index():
    df = load_data_from_sqlite()

    # Když DB bude prázdná, ať to nespadne
    if df.empty:
        html = """
        <html>
        <head>
          <meta charset="utf-8">
          <title>Mořské počasí – analýza</title>
          <style>
            body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;background:#0b1020;color:#e8eeff;margin:0;padding:24px}
            .card{max-width:900px;margin:0 auto;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.12);border-radius:14px;padding:18px;box-shadow:0 12px 30px rgba(0,0,0,.35)}
            .muted{color:#a8b3d6}
          </style>
        </head>
        <body>
          <div class="card">
            <h1>🌊 Analýza mořského počasí</h1>
            <p class="muted">V databázi nejsou žádná data. Nejdřív spusť main.py a načti data z API.</p>
          </div>
        </body>
        </html>
        """
        return render_template_string(html)

    # Bezpečně převedeme sloupec time na datetime (kvůli výpisu/řazení)
    # (když to nepůjde, necháme jak je)
    try:
        df["time_dt"] = pd.to_datetime(df["time"])
        df = df.sort_values("time_dt")
        time_labels = df["time_dt"].dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        time_labels = df["time"]

    # Výpočty
    df["storm"] = df["wave_height"] > 0.5
    storm_prob = df["storm"].mean() * 100
    avg_temp_storm = df.loc[df["storm"], "sea_temp"].mean()

    # Když nejsou žádné bouřky, avg_temp_storm bude NaN -> hezčí text
    if pd.isna(avg_temp_storm):
        avg_temp_text = "— (žádné bouřky v datech)"
    else:
        avg_temp_text = f"{avg_temp_storm:.2f} °C"

    # Graf
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(time_labels, df["sea_temp"])
    ax.set_xlabel("Čas")
    ax.set_ylabel("Teplota moře [°C]")
    ax.set_title("Teplota moře v čase")
    ax.set_xticks([])  # aby to nebylo přeplácané
    img_chart = plot_to_base64(fig)

    # Uděláme hezčí tabulku: vybereme jen relevantní sloupce (pokud existují)
    cols = [c for c in ["time", "wave_height", "sea_temp", "wave_direction"] if c in df.columns]
    df_table = df[cols].copy()

    # Přidáme zaokrouhlení
    for c in ["wave_height", "sea_temp", "wave_direction"]:
        if c in df_table.columns:
            df_table[c] = df_table[c].round(2)

    table_html = df_table.to_html(index=False, classes="data-table", border=0, escape=False)

    html = f"""
    <!doctype html>
    <html lang="cs">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Mořské počasí – analýza</title>
        <style>
            :root {{
              --bg:#0b1020;
              --card:rgba(255,255,255,.06);
              --line:rgba(255,255,255,.12);
              --text:#e8eeff;
              --muted:#a8b3d6;
              --accent:#7aa2ff;
            }}

            body {{
              font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
              background: radial-gradient(1200px 600px at 20% 0%, #182450 0%, var(--bg) 55%);
              color: var(--text);
              margin: 0;
              padding: 24px;
            }}

            .wrap {{
              max-width: 1050px;
              margin: 0 auto;
              display: grid;
              gap: 14px;
            }}

            .card {{
              background: var(--card);
              border: 1px solid var(--line);
              border-radius: 14px;
              padding: 16px 18px;
              box-shadow: 0 12px 30px rgba(0,0,0,.35);
            }}

            h1 {{
              margin: 0 0 6px;
              font-size: 22px;
              letter-spacing: .2px;
            }}

            .muted {{
              color: var(--muted);
              font-size: 13px;
              margin: 0;
            }}

            .stats {{
              display: grid;
              grid-template-columns: repeat(2, minmax(0, 1fr));
              gap: 12px;
              margin-top: 10px;
            }}

            .stat {{
              background: rgba(0,0,0,.18);
              border: 1px solid rgba(255,255,255,.08);
              border-radius: 12px;
              padding: 12px;
            }}

            .stat .label {{
              color: var(--muted);
              font-size: 12px;
              text-transform: uppercase;
              letter-spacing: .08em;
              margin-bottom: 6px;
            }}

            .stat .value {{
              font-size: 20px;
              font-variant-numeric: tabular-nums;
            }}

            img {{
              width: 100%;
              height: auto;
              border-radius: 12px;
              border: 1px solid rgba(255,255,255,.10);
              background: rgba(0,0,0,.12);
            }}

            .table-wrap {{
              overflow: auto;
              border-radius: 12px;
              border: 1px solid rgba(255,255,255,.10);
            }}

            table.data-table {{
              width: 100%;
              border-collapse: collapse;
              min-width: 720px;
              background: rgba(0,0,0,.10);
            }}

            table.data-table thead th {{
              position: sticky;
              top: 0;
              background: rgba(17, 26, 51, .95);
              backdrop-filter: blur(6px);
              color: var(--muted);
              font-size: 12px;
              text-transform: uppercase;
              letter-spacing: .08em;
              padding: 10px 12px;
              text-align: left;
              border-bottom: 1px solid rgba(255,255,255,.10);
              white-space: nowrap;
            }}

            table.data-table tbody td {{
              padding: 10px 12px;
              border-bottom: 1px solid rgba(255,255,255,.08);
              white-space: nowrap;
              font-variant-numeric: tabular-nums;
            }}

            table.data-table tbody tr:nth-child(even) td {{
              background: rgba(255,255,255,.02);
            }}

            table.data-table tbody tr:hover td {{
              background: rgba(122,162,255,.08);
            }}

            @media (max-width: 720px) {{
              .stats {{
                grid-template-columns: 1fr;
              }}
            }}
        </style>
    </head>
    <body>
      <div class="wrap">
        <div class="card">
          <h1>🌊 Analýza mořského počasí</h1>
          <p class="muted">Data jsou načtená z SQLite: <strong>weather.db</strong> (tabulka <strong>marine_weather</strong>)</p>

          <div class="stats">
            <div class="stat">
              <div class="label">Pravděpodobnost bouřky</div>
              <div class="value">{storm_prob:.2f}%</div>
            </div>
            <div class="stat">
              <div class="label">Průměrná teplota při bouřkách</div>
              <div class="value">{avg_temp_text}</div>
            </div>
          </div>
        </div>

        <div class="card">
          <h2 style="margin:0 0 10px;font-size:16px;color:var(--muted);font-weight:600;">
            Graf: teplota moře v čase
          </h2>
          <img src="data:image/png;base64,{img_chart}" alt="Graf teploty moře" />
        </div>

        <div class="card">
          <h2 style="margin:0 0 10px;font-size:16px;color:var(--muted);font-weight:600;">
            Datová tabulka
          </h2>
          <div class="table-wrap">
            {table_html}
          </div>
        </div>
      </div>
    </body>
    </html>
    """

    return render_template_string(html)

if __name__ == "__main__":
    app.run(debug=True)

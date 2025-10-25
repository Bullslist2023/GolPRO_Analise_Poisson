# app.py
"""
O_Gatilho_de_Arquimedes - Versão_Final (GolPRO v2.0)
- Tema claro & elegante (dourado + royal blue)
- Entrada: total de jogos por time
- Probabilidades Poisson 0..10 (exatas) + acumuladas
- Gráficos de pizza modernos e legíveis (animação/transition leve)
- Tabelas simples com os percentuais
- Rodapé com autor e ano (2025)
- Gera PDF apenas quando o usuário clicar
"""
import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import poisson
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table as RLTable, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors as rl_colors
from PIL import Image
import datetime

st.set_page_config(page_title="GolPRO v2.0 - Scorpion Premium", page_icon="🦂", layout="wide")

# --------------------------
# Style: tema claro -> branco, dourado, royal blue
# --------------------------
st.markdown(
    """
    <style>
    :root {
        --dourado: #C9A516;
        --royal: #1F3A93;
        --light: #FFFFFF;
        --muted: #6b6b6b;
        --bg: #f8f9fb;
    }
    body { background-color: var(--bg); color: #111; }
    h1, h2, h3 { color: var(--dourado); }
    .stApp .css-1v3fvcr { padding-top: 0px; }
    .stButton>button { background-color: var(--royal); color: white; border-radius:8px; padding:0.45rem 0.8rem; border: 2px solid var(--dourado); font-weight:700; }
    .stButton>button:hover { background-color: var(--dourado); color: black; }
    [data-testid="stSidebar"] { background-color: white; border-left: 1px solid #e6e6e6; }
    .small-muted { font-size:12px; color: var(--muted); }
    footer {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)

# --------------------------
# Header + optional logo
# --------------------------
colh1, colh2 = st.columns([0.82, 0.18])
with colh1:
    st.title("🦂 GolPRO v2.0 — Scorpion Premium (Light Edition)")
    st.markdown("**Análise estatística (Poisson)** para Gols, Escanteios, Finalizações e Cartões — agora com tabelas 0→10 e PDFs sob demanda.")
with colh2:
    logo_file = st.file_uploader("Upload do logotipo (opcional)", type=['png','jpg','jpeg'])
    if logo_file:
        try:
            img = Image.open(logo_file).convert("RGB")
            st.image(img, use_column_width=True)
        except:
            st.text("Arquivo de logo inválido.")

st.divider()

# --------------------------
# Inputs: times, médias e total de jogos
# --------------------------
st.header("📥 Dados dos Times")
c1, c2 = st.columns(2)
with c1:
    time_a = st.text_input("Nome do Time A", "Insira o Nome do Time A")
    total_matches_a = st.number_input("Total de jogos (A) usados para calcular médias", min_value=0, max_value=1000, value=20, step=1)
    media_gols_a = st.number_input("⚽ Média de Gols (A)", min_value=0.0, max_value=20.0, value=1.8, step=0.1)
    media_esc_a = st.number_input("🚩 Média de Escanteios (A)", min_value=0.0, max_value=50.0, value=6.2, step=0.1)
    media_final_a = st.number_input("🎯 Média de Finalizações (A)", min_value=0.0, max_value=80.0, value=13.4, step=0.1)
    media_cart_a = st.number_input("🟨 Média de Cartões (A)", min_value=0.0, max_value=15.0, value=2.3, step=0.1)
with c2:
    time_b = st.text_input("Nome do Time B", "Insira o Nome do Time B")
    total_matches_b = st.number_input("Total de jogos (B) usados para calcular médias", min_value=0, max_value=1000, value=18, step=1)
    media_gols_b = st.number_input("⚽ Média de Gols (B)", min_value=0.0, max_value=20.0, value=1.5, step=0.1)
    media_esc_b = st.number_input("🚩 Média de Escanteios (B)", min_value=0.0, max_value=50.0, value=5.8, step=0.1)
    media_final_b = st.number_input("🎯 Média de Finalizações (B)", min_value=0.0, max_value=80.0, value=12.9, step=0.1)
    media_cart_b = st.number_input("🟨 Média de Cartões (B)", min_value=0.0, max_value=15.0, value=2.0, step=0.1)

st.markdown(
    f"<div class='small-muted'>Nota: as médias são consideradas com base em {total_matches_a} jogos (Time A) e {total_matches_b} jogos (Time B). Quanto maior a amostra, mais confiáveis as estimativas.</div>",
    unsafe_allow_html=True
)
st.divider()

# --------------------------
# Funções Poisson: exatas 0..10 e acumulada
# --------------------------
def poisson_probs(mu, k_max=10):
    """Retorna lista de P(X=k) de k=0..k_max (em %), e acumuladas P(X<=k) em %"""
    ks = np.arange(0, k_max + 1)
    pmf = poisson.pmf(ks, mu)
    pmf_pct = np.round(pmf * 100, 4)
    cdf = np.round(np.cumsum(pmf) * 100, 4)
    return ks, pmf_pct, cdf

# eventos e cores (mais vibrantes)
eventos = ["🎯 Finalizações", "🚩 Escanteios", "🟨 Cartões", "⚽ Gols"]
pie_colors = ["#1F3A93", "#C9A516", "#007ACC", "#E04848"]  # royal blue, gold, bright blue, red tone

# compute tables for A and B
def make_event_tables(mu):
    ks, pmf_pct, cdf_pct = poisson_probs(mu, 10)
    df = pd.DataFrame({
        "k": ks,
        "Probabilidade exata (%)": pmf_pct,
        "Probabilidade acumulada P(X ≤ k) (%)": cdf_pct
    })
    return df

tables_a = {
    "Finalizações": make_event_tables(media_final_a),
    "Escanteios": make_event_tables(media_esc_a),
    "Cartões": make_event_tables(media_cart_a),
    "Gols": make_event_tables(media_gols_a)
}
tables_b = {
    "Finalizações": make_event_tables(media_final_b),
    "Escanteios": make_event_tables(media_esc_b),
    "Cartões": make_event_tables(media_cart_b),
    "Gols": make_event_tables(media_gols_b)
}

# For pie: use probability of at least one occurrence (1 - P(X=0))
def prob_at_least_one(mu):
    return 1 - poisson.pmf(0, mu)

probs_a = [prob_at_least_one(media_final_a), prob_at_least_one(media_esc_a), prob_at_least_one(media_cart_a), prob_at_least_one(media_gols_a)]
probs_b = [prob_at_least_one(media_final_b), prob_at_least_one(media_esc_b), prob_at_least_one(media_cart_b), prob_at_least_one(media_gols_b)]

df_pie_a = pd.DataFrame({"Evento": eventos, "Probabilidade (%)": np.round(np.array(probs_a) * 100, 2)})
df_pie_b = pd.DataFrame({"Evento": eventos, "Probabilidade (%)": np.round(np.array(probs_b) * 100, 2)})

# --------------------------
# Pie charts side-by-side (animated transition)
# --------------------------
st.header("📊 Pie: Chance de Ocorre ao Menos 1 Vez (por evento)")

col_left, col_right = st.columns(2)
with col_left:
    fig_a = px.pie(df_pie_a, values="Probabilidade (%)", names="Evento",
                   color="Evento", color_discrete_sequence=pie_colors, title=f"{time_a}")
    fig_a.update_traces(textinfo="percent+label", pull=[0.02, 0.02, 0.02, 0.02])
    fig_a.update_layout(template="plotly_white", title_font_color="#1F3A93",
                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                        transition={"duration": 600, "easing": "cubic-in-out"})
    fig_a.update_traces(marker=dict(line=dict(color='white', width=2)))
    st.plotly_chart(fig_a, use_container_width=True)

with col_right:
    fig_b = px.pie(df_pie_b, values="Probabilidade (%)", names="Evento",
                   color="Evento", color_discrete_sequence=pie_colors, title=f"{time_b}")
    fig_b.update_traces(textinfo="percent+label", pull=[0.02, 0.02, 0.02, 0.02])
    fig_b.update_layout(template="plotly_white", title_font_color="#1F3A93",
                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                        transition={"duration": 600, "easing": "cubic-in-out"})
    fig_b.update_traces(marker=dict(line=dict(color='white', width=2)))
    st.plotly_chart(fig_b, use_container_width=True)

# Add explicit legend/explanation below pies
st.markdown("**O que as porcentagens no gráfico representam:**\n\n- Cada fatia mostra a **probabilidade de aquele evento ocorrer ao menos 1 vez** durante a partida (P(X ≥ 1)).\n- Percentuais baseados nas médias fornecidas (Poisson).")
st.markdown("**Como ler:** ex.: se Finalizações = 90% → há 90% de chance do time ter pelo menos 1 finalização (isto engloba 1,2,3,... finalizações). Use as tabelas abaixo para ver probabilidades exatas (0,1,2,..10) e acumuladas (P(X ≤ k)).")

st.divider()

# --------------------------
# Tables 0..10 and accumulated (simple tables)
# --------------------------
st.header("📈 Tabelas: Probabilidades exatas (0 → 10) e Acumuladas")

for evento_key, label in zip(["Finalizações", "Escanteios", "Cartões", "Gols"], eventos):
    st.subheader(f"{label} — {time_a} (Tabela 0→10)")
    st.table(tables_a[evento_key].rename(columns={
        "k": "Número de eventos (k)",
        "Probabilidade exata (%)": "P(X=k) (%)",
        "Probabilidade acumulada P(X ≤ k) (%)": "P(X ≤ k) (%)"
    }).set_index("Número de eventos (k)"))
    st.subheader(f"{label} — {time_b} (Tabela 0→10)")
    st.table(tables_b[evento_key].rename(columns={
        "k": "Número de eventos (k)",
        "Probabilidade exata (%)": "P(X=k) (%)",
        "Probabilidade acumulada P(X ≤ k) (%)": "P(X ≤ k) (%)"
    }).set_index("Número de eventos (k)"))
    st.markdown("---")

# --------------------------
# Quick insights (differences)
# --------------------------
st.header("📊 Insights Rápidos")
diffs_pp = np.round((np.array(probs_a) - np.array(probs_b)) * 100, 2)
k1, k2, k3, k4 = st.columns(4)
k1.metric("Finalizações (A - B, pp)", f"{diffs_pp[0]} pp")
k2.metric("Escanteios (A - B, pp)", f"{diffs_pp[1]} pp")
k3.metric("Cartões (A - B, pp)", f"{diffs_pp[2]} pp")
k4.metric("Gols (A - B, pp)", f"{diffs_pp[3]} pp")
st.markdown("<div class='small-muted'>pp = pontos percentuais (diferença em porcentagem)</div>", unsafe_allow_html=True)

st.divider()

# --------------------------
# Interpretation notes (dynamic)
# --------------------------
st.header("🧠 Como usar estas probabilidades (prático)")
st.markdown("""
- **Probabilidade exata (P(X=k))**: diz exatamente a chance daquele número ocorrer (ex.: P(X=2) = 30%).
- **Probabilidade acumulada (P(X ≤ k))**: útil para estimar 'até k eventos' (ex.: P(X ≤ 2) = 70%).
- **P(X ≥ 1)** (pie): rápido indicador se o evento deve ocorrer ao menos uma vez.
- Use **P(X ≥ 1)** para seleções rápidas e as tabelas 0→10 para ajustes finos de mercado/tática.
""")

st.divider()

# --------------------------
# PDF Generation (on demand)
# --------------------------
def fig_to_png_bytes(fig):
    try:
        return fig.to_image(format="png", scale=2)
    except Exception:
        return None

def df_to_table_data(df):
    rows = []
    for _, r in df.iterrows():
        rows.append([str(int(r['k'])), f"{r['Probabilidade exata (%)']}%", f"{r['Probabilidade acumulada P(X ≤ k) (%)']}%"])
    return rows

def generate_pdf(title, time_a, total_a, df_pie_a, tables_a, fig_a_bytes, time_b, total_b, df_pie_b, tables_b, fig_b_bytes, logo_bytes=None):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=18, leftMargin=18, topMargin=18, bottomMargin=18)
    elements = []
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="TitleStyle", fontSize=18, alignment=1, textColor=rl_colors.HexColor("#1F3A93")))
    styles.add(ParagraphStyle(name="Body", fontSize=10, textColor=rl_colors.black))

    # header
    if logo_bytes:
        try:
            logo_io = BytesIO(logo_bytes)
            logo_img = RLImage(logo_io, width=120, height=40)
            elements.append(logo_img)
        except: pass
    elements.append(Paragraph(title, styles['TitleStyle']))
    elements.append(Spacer(1,6))
    elements.append(Paragraph(f"Gerado em: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Body']))
    elements.append(Spacer(1,10))

    # Pie images A/B
    if fig_a_bytes:
        elements.append(RLImage(BytesIO(fig_a_bytes), width=360, height=220))
        elements.append(Spacer(1,8))
    # table A summary
    elements.append(Paragraph(f"{time_a} — Total jogos usados: {total_a}", styles['Body']))
    table_data = [["k", "P(X=k) (%)", "P(X ≤ k) (%)"]] + df_to_table_data(tables_a)
    t = RLTable(table_data, hAlign='LEFT', colWidths=[40, 120, 120])
    t.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), rl_colors.HexColor("#1F3A93")),
                           ('TEXTCOLOR',(0,0),(-1,0), rl_colors.white),
                           ('GRID', (0,0), (-1,-1), 0.25, rl_colors.grey)]))
    elements.append(t)
    elements.append(Spacer(1,12))

    if fig_b_bytes:
        elements.append(RLImage(BytesIO(fig_b_bytes), width=360, height=220))
        elements.append(Spacer(1,8))
    elements.append(Paragraph(f"{time_b} — Total jogos usados: {total_b}", styles['Body']))
    table_data_b = [["k", "P(X=k) (%)", "P(X ≤ k) (%)"]] + df_to_table_data(tables_b)
    t2 = RLTable(table_data_b, hAlign='LEFT', colWidths=[40, 120, 120])
    t2.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), rl_colors.HexColor("#1F3A93")),
                           ('TEXTCOLOR',(0,0),(-1,0), rl_colors.white),
                           ('GRID', (0,0), (-1,-1), 0.25, rl_colors.grey)]))
    elements.append(t2)
    elements.append(Spacer(1,12))

    # footer / summary / credits
    elements.append(Paragraph("Resumo: Probabilidades por evento (Poisson) — Use com responsabilidade.", styles['Body']))
    elements.append(Spacer(1,6))
    elements.append(Paragraph("Desenvolvido por Juan Santos — Projeto iniciado em 2025", styles['Body']))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

st.header("📤 Gerar Relatório PDF (sob demanda)")
colp1, colp2 = st.columns([0.4, 0.6])
with colp1:
    if st.button("Gerar PDF do Relatório"):
        # prepare logo bytes
        logo_bytes = None
        if logo_file:
            try:
                logo_file.seek(0)
                logo_bytes = logo_file.read()
            except:
                logo_bytes = None

        fig_a_png = fig_to_png_bytes(fig_a)
        fig_b_png = fig_to_png_bytes(fig_b)

        pdf = generate_pdf("GolPRO v2.0 - Relatório", time_a, total_matches_a, df_pie_a, tables_a["Finalizações"], fig_a_png,
                           time_b, total_matches_b, df_pie_b, tables_b["Finalizações"], fig_b_png, logo_bytes=logo_bytes)
        st.success("Relatório PDF gerado.")
        st.download_button("Download PDF", data=pdf, file_name=f"GolPRO_Report_{time_a}_vs_{time_b}.pdf", mime="application/pdf")
with colp2:
    st.markdown("""
    O relatório inclui:  
    - Gráficos de pizza (imagens, quando possível);  
    - Tabelas 0→10 com probabilidades exatas e acumuladas;  
    - Nota sobre total de jogos e rodapé com autor/ano.  
    *Observação:* se a exportação de figuras falhar (dependendo do ambiente/kaleido), o PDF ainda será gerado com as tabelas.
    """)

st.divider()

# --------------------------
# Footer (visual)
# --------------------------
st.markdown(
    """
    <div style="width:100%; text-align:center; padding:10px 0; color:#444; border-top:1px solid #e6e6e6;">
        Desenvolvido por <b>Juan Santos</b> — Projeto iniciado em <b>2025</b> • GolPRO v2.0
    </div>
    """,
    unsafe_allow_html=True
)

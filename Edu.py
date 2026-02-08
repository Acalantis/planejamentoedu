import streamlit as st
import pandas as pd
from io import StringIO
from datetime import datetime
import re
import locale

# =============================
# CONFIGURAÇÃO
# =============================
st.set_page_config(page_title="Planejamento Financeiro", layout="wide")
st.title("📊 Planejamento Financeiro")

try:
    locale.setlocale(locale.LC_ALL, "pt_BR.UTF-8")
except:
    pass

# =============================
# VISUALIZAÇÃO / MODO IMPRESSÃO
# =============================
st.markdown("### 🖨️ Visualização")
modo_impressao = st.toggle("Modo impressão (para print/PDF)")

if modo_impressao:
    st.markdown("""
        <style>
        /* ESCONDE APENAS CAMPOS DE ENTRADA (NÃO textos, NÃO métricas) */
        textarea,
        input[type="number"],
        div[data-baseweb="input"],
        div[data-baseweb="textarea"] {
            display: none !important;
        }

        /* Quebra de página antes das contas pagas */
        .pagina-contas-pagas {
            page-break-before: always;
            break-before: page;
        }

        @page {
            size: A4 portrait;
            margin: 12mm;
        }
        </style>
    """, unsafe_allow_html=True)

st.divider()

# =============================
# BLOCO 1 – RECEBÍVEIS MANUAIS
# =============================
st.subheader("💰 Recebíveis (Manual)")

c1, c2 = st.columns(2)

with c1:
    recebido_manual = st.number_input("Recebidos", min_value=0.0, format="%.2f")

with c2:
    a_receber_manual = st.number_input("A receber", min_value=0.0, format="%.2f")

# =============================
# KPIs VISUAIS
# =============================
st.markdown("""
<style>
.kpi-card {
    padding: 24px;
    border-radius: 14px;
    background: linear-gradient(135deg, #1f2933, #111827);
    box-shadow: 0 8px 20px rgba(0,0,0,0.35);
    text-align: center;
}
.kpi-title {
    font-size: 15px;
    color: #9ca3af;
}
.kpi-value {
    font-size: 32px;
    font-weight: 700;
    color: #f9fafb;
}
</style>
""", unsafe_allow_html=True)

k1, k2 = st.columns(2)

with k1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">💵 Total Recebidos</div>
        <div class="kpi-value">R$ {recebido_manual:,.2f}</div>
    </div>
    """, unsafe_allow_html=True)

with k2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">⏳ Total a Receber</div>
        <div class="kpi-value">R$ {a_receber_manual:,.2f}</div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# =============================
# PRÓXIMA SEMANA – VIA COLAGEM
# =============================
st.subheader("📅 Recebíveis da Próxima Semana")

texto_semana = st.text_area(
    "Cole aqui o relatório bruto da próxima semana",
    height=320
)

dados_semana = []
data_atual = None

if texto_semana.strip():
    for linha in texto_semana.splitlines():
        linha = linha.strip()

        if not linha:
            continue

        if re.fullmatch(r"\d{2}/\d{2}/\d{4}", linha):
            try:
                data_atual = datetime.strptime(linha, "%d/%m/%Y")
            except:
                data_atual = None
            continue

        linha_lower = linha.lower()

        if (
            "cliente" in linha_lower
            or linha_lower.startswith("total")
            or data_atual is None
        ):
            continue

        valores = re.findall(r"\d{1,3}(?:\.\d{3})*,\d{2}", linha)

        if len(valores) >= 2:
            saldo_raw = valores[-2].replace(".", "").replace(",", ".")
            try:
                saldo = float(saldo_raw)
                dados_semana.append([data_atual, saldo])
            except:
                pass

    if dados_semana:
        df_semana = pd.DataFrame(dados_semana, columns=["data", "saldo"])

        resumo_semana = (
            df_semana
            .groupby("data")["saldo"]
            .sum()
            .reset_index()
            .sort_values("data")
        )

        resumo_semana["data_label"] = resumo_semana["data"].dt.strftime("%d/%m")
        total_semana = resumo_semana["saldo"].sum()

        st.metric("📅 Total da próxima semana", f"R$ {total_semana:,.2f}")

        st.bar_chart(
            resumo_semana.set_index("data_label")["saldo"]
        )

st.divider()

# =============================
# BLOCO 2 – CONTAS PAGAS (SAÍDAS)
# =============================
st.markdown('<div class="pagina-contas-pagas">', unsafe_allow_html=True)

st.subheader("💸 Contas Pagas – Saídas")

texto_pagamentos = st.text_area(
    "Cole aqui o bloco de SAÍDAS",
    height=250
)

if texto_pagamentos.strip():
    registros = []

    for linha in texto_pagamentos.splitlines():
        linha = linha.strip()
        linha_lower = linha.lower()

        if (
            not linha
            or linha_lower.startswith("saídas")
            or linha_lower.startswith("total")
        ):
            continue

        partes = re.split(r"\t+|\s{2,}", linha)

        if len(partes) >= 2:
            categoria = partes[0].strip()
            valor_raw = partes[1].replace(".", "").replace(",", ".")

            try:
                valor = float(valor_raw)
                registros.append([categoria, valor])
            except:
                pass

    if registros:
        df_saida = pd.DataFrame(registros, columns=["Categoria", "Valor"])
        total_saida = df_saida["Valor"].sum()

        st.metric("🔴 Total de Saídas", f"R$ {total_saida:,.2f}")

        st.dataframe(
            df_saida.sort_values("Valor", ascending=False),
            use_container_width=True
        )

st.markdown('</div>', unsafe_allow_html=True)

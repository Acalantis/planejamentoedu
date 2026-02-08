import streamlit as st
import pandas as pd
from datetime import timedelta
from io import StringIO
import locale

# =============================
# CONFIGURAÇÃO
# =============================
st.set_page_config(page_title="Financeiro", layout="wide")
st.title("📊 Painel Financeiro")

try:
    locale.setlocale(locale.LC_TIME, "pt_BR.UTF-8")
except:
    pass

# =============================
# SESSION STATE
# =============================
if "etapa" not in st.session_state:
    st.session_state["etapa"] = 1

if "texto_receber" not in st.session_state:
    st.session_state["texto_receber"] = ""

if "texto_pago" not in st.session_state:
    st.session_state["texto_pago"] = ""

# =============================
# RESET
# =============================
if st.session_state["etapa"] == 3:
    if st.button("📄 Outro documento"):
        st.session_state.clear()
        st.rerun()

# =============================
# ETAPA 1 — CONTAS A RECEBER
# =============================
if st.session_state["etapa"] == 1:

    st.subheader("📋 Etapa 1 — Cole as Contas a Receber")

    texto = st.text_area(
        "Cole o relatório completo de contas a receber",
        height=280
    )

    if texto.strip():
        st.session_state["texto_receber"] = texto
        st.session_state["etapa"] = 2
        st.rerun()

# =============================
# ETAPA 2 — CONTAS PAGAS (RESUMO)
# =============================
elif st.session_state["etapa"] == 2:

    st.subheader("📋 Etapa 2 — Cole o resumo das Contas Pagas")

    texto = st.text_area(
        "Cole exatamente como vem do Excel (Categoria | Valor | %)",
        height=260
    )

    if texto.strip():
        st.session_state["texto_pago"] = texto
        st.session_state["etapa"] = 3
        st.rerun()

# =============================
# ETAPA 3 — DASHBOARD
# =============================
elif st.session_state["etapa"] == 3:

    # =====================================================
    # CONTAS A RECEBER
    # =====================================================
    df = pd.read_csv(
        StringIO(st.session_state["texto_receber"]),
        sep="\t",
        decimal=","
    )

    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )

    df["vencimento"] = pd.to_datetime(df["vencimento"], dayfirst=True, errors="coerce")
    df["saldo"] = pd.to_numeric(df["saldo"], errors="coerce").fillna(0)
    df["recebido"] = pd.to_numeric(df["recebido"], errors="coerce").fillna(0)

    hoje = pd.Timestamp.today().normalize()

    total_recebido = df["recebido"].sum()
    a_receber = df[df["vencimento"] > hoje]
    total_a_receber = a_receber["saldo"].sum()

    inicio = hoje + timedelta(days=1)
    fim = hoje + timedelta(days=6)

    prox_semana = a_receber[
        (a_receber["vencimento"] >= inicio) &
        (a_receber["vencimento"] <= fim)
    ]

    total_semana = prox_semana["saldo"].sum()

    grafico_semana = (
        prox_semana
        .groupby("vencimento")["saldo"]
        .sum()
        .reset_index()
        .sort_values("vencimento")
    )

    grafico_semana["dia"] = grafico_semana["vencimento"].dt.strftime("%d")

    mensal = (
        a_receber
        .assign(mes=a_receber["vencimento"].dt.to_period("M"))
        .groupby("mes")["saldo"]
        .sum()
        .reset_index()
    )

    mensal["mes"] = mensal["mes"].dt.to_timestamp()
    mensal["mes_extenso"] = mensal["mes"].dt.strftime("%B / %Y").str.capitalize()

    st.subheader("📈 Contas a Receber")

    c1, c2, c3 = st.columns(3)
    c1.metric("💰 Recebido", f"R$ {total_recebido:,.2f}")
    c2.metric("⏳ A Receber Total", f"R$ {total_a_receber:,.2f}")
    c3.metric("📅 Próxima Semana", f"R$ {total_semana:,.2f}")

    st.subheader("📊 Próximos 7 Dias")
    if grafico_semana.empty:
        st.info("Nenhum valor a receber na próxima semana.")
    else:
        st.bar_chart(grafico_semana.set_index("dia")["saldo"])

    st.subheader("📆 A Receber por Mês")
    st.dataframe(
        mensal[["mes_extenso", "saldo"]]
        .rename(columns={"mes_extenso": "Mês", "saldo": "Saldo"}),
        use_container_width=True
    )

    # =====================================================
    # CONTAS PAGAS — SAÍDAS (FORMATO EXCEL)
    # =====================================================
    st.divider()
    st.subheader("🔴 Contas Pagas — Saídas por Categoria")

    linhas = st.session_state["texto_pago"].splitlines()
    dados = []

    for l in linhas:
        l = l.strip()

        # ignora lixo
        if not l:
            continue
        if l.lower() in ["categoria", "saídas"]:
            continue
        if "porcentagem" in l.lower():
            continue

        partes = l.split("\t")

        if len(partes) >= 2:
            categoria = partes[0].strip()
            valor = partes[1].strip()
            percentual = partes[2].strip() if len(partes) > 2 else None

            dados.append([categoria, valor, percentual])

    df_pago = pd.DataFrame(
        dados,
        columns=["categoria", "valor", "percentual"]
    )

    # conversão PT-BR
    df_pago["valor"] = (
        df_pago["valor"]
        .astype(str)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
    )

    df_pago["valor"] = pd.to_numeric(df_pago["valor"], errors="coerce").fillna(0)

    df_pago["percentual"] = (
        df_pago["percentual"]
        .astype(str)
        .str.replace(",", ".", regex=False)
    )

    df_pago["percentual"] = pd.to_numeric(df_pago["percentual"], errors="coerce")

    # remove linhas inválidas
    df_pago = df_pago[df_pago["valor"] > 0]

    total_gastos = df_pago["valor"].sum()

    st.metric("💸 Total de Gastos", f"R$ {total_gastos:,.2f}")

    st.dataframe(
        df_pago.rename(columns={
            "categoria": "Categoria",
            "valor": "Valor",
            "percentual": "Porcentagem %"
        }),
        use_container_width=True
    )


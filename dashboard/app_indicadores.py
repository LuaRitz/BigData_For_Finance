# app_indicadores.py
"""
Dashboard de Indicadores Financeiros — Big Data for Finance
Integra as views: Liquidez, Endividamento, Rentabilidade, Atividade e Fleuriet
Fonte: layer_03_gold.mart_indicadores_financeiros

Uso:
    cd dashboard
    streamlit run app_indicadores.py
"""

import os
import streamlit as st
import pandas as pd
import numpy as np
from sqlalchemy import text
from dotenv import load_dotenv

# ==============================================================================
# 1. AMBIENTE
# ==============================================================================
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

try:
    from database import get_db_connection
except ImportError:
    st.error("❌ O arquivo 'database.py' deve estar no mesmo diretório.")
    st.stop()

# ==============================================================================
# 2. CONFIGURAÇÃO DA PÁGINA
# ==============================================================================
st.set_page_config(
    page_title="Indicadores Financeiros | CVM Gold",
    page_icon="📐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Design system consistente com o projeto (cores FAE + estilo executivo)
st.markdown("""
    <style>
    .main { background-color: #F8FAFC; }
    
    /* Cartões KPI */
    .executive-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 6px;
        box-shadow: 0 1px 3px rgba(15,23,42,.05);
        border-left: 5px solid #1E293B;
        margin-bottom: 12px;
    }
    
    /* Badges de governança */
    .governance-badge {
        background-color: #F1F5F9;
        padding: 4px 12px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 600;
        color: #475569;
        border: 1px solid #E2E8F0;
        margin-right: 8px;
        display: inline-block;
    }
    
    /* Sinalizações semânticas */
    .status-positive { color: #10B981; font-weight: 600; }
    .status-neutral  { color: #F59E0B; font-weight: 600; }
    .status-negative { color: #EF4444; font-weight: 600; }
    
    /* Remove padding top excessivo */
    .block-container { padding-top: 1.5rem; }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 3. CARREGAMENTO DOS DADOS (GOLD MART)
# ==============================================================================
engine = get_db_connection()

@st.cache_data(ttl=600)
def fetch_gold_mart():
    """Busca toda a tabela gold de indicadores."""
    query = """
        SELECT
            "CNPJ_CIA", "DT_REFER", "RAZAO_SOCIAL", "SETOR", "TP_MERC",
            -- Variáveis de input (BP)
            "V01_ATIVO_TOTAL", "V02_ATIVO_CIRC", "V03_ATIVO_NCIRC",
            "V04_RLP", "V05_IMOBILIZADO", "V06_ESTOQUES_RAW", "V06_ESTOQUES",
            "V07_CONTAS_RECEBER", "V09_FORNECEDORES",
            "V10_PASSIVO_CIRC", "V11_PASSIVO_NCIRC", "V12_PL",
            "V13_EMP_CP", "V14_EMP_LP",
            "V22_CAIXA_BP", "V15B_APLIC_FIN",
            -- Variáveis de input (DRE)
            "V17_RECEITA_LIQ", "V18_CPV", "V19_LUCRO_BRUTO",
            "V20_EBIT", "V21_LUCRO_LIQ",
            "V25_LPA_BASICO", "V26_LPA_DILUIDO_RAW", "V26_LPA_DILUIDO",
            -- DFC
            "V23_CAIXA_DFC",
            -- Auxiliares
            "AUX_PASSIVO_TOTAL", "AUX_ACF", "AUX_DIVIDA_BRUTA", "AUX_DIVIDA_LIQUIDA",
            "AUX_CAPITAL_INVEST", "AUX_CPV_ABS",
            -- Indicadores de Liquidez
            "IND_LIQUIDEZ_GERAL", "IND_LIQUIDEZ_CORRENTE",
            "IND_LIQUIDEZ_SECA",  "IND_LIQUIDEZ_IMEDIATA",
            -- Indicadores de Endividamento
            "IND_PCT_CP", "IND_PCT_AT", "IND_GARANTIA_CT",
            "IND_COMPOSICAO_ENDIV", "IND_IMOB_CP", "IND_IMOB_AT",
            -- Indicadores de Rentabilidade
            "IND_MARGEM_BRUTA", "IND_MARGEM_OPERACIONAL", "IND_MARGEM_LIQUIDA",
            "IND_LPA_DILUIDO", "IND_ROA", "IND_ROE", "IND_ROI",
            -- Indicadores de Atividade
            "IND_GIRO_ESTOQUES", "IND_GIRO_CR", "IND_GIRO_CP", "IND_GIRO_AC",
            "IND_PMRE", "IND_PMRV", "IND_PMPC", "IND_PMRAC",
            "IND_CICLO_ECONOMICO", "IND_CICLO_FINANCEIRO",
            -- Modelo Fleuriet
            "IND_CGL", "IND_NCG", "IND_ST"
        FROM layer_03_gold.mart_indicadores_financeiros
        ORDER BY "RAZAO_SOCIAL", "DT_REFER";
    """
    try:
        with engine.connect() as conn:
            df = pd.read_sql(text(query), conn)
            df.columns = [c.upper() for c in df.columns]
            df["DT_REFER"] = pd.to_datetime(df["DT_REFER"])
            df["ANO"] = df["DT_REFER"].dt.year.astype(str)
            return df
    except Exception as e:
        st.error(f"🚨 Erro ao carregar a camada Gold: {e}")
        st.stop()


df_master = fetch_gold_mart()

if df_master.empty:
    st.warning("A tabela `layer_03_gold.mart_indicadores_financeiros` está vazia.")
    st.stop()

# ==============================================================================
# 4. SIDEBAR — FILTROS
# ==============================================================================
with st.sidebar:
    st.markdown("## 📐 Indicadores Financeiros")
    st.caption("Big Data for Finance · CVM Gold Layer")
    st.markdown("---")

    # Empresa
    lista_emp = (
        df_master[["CNPJ_CIA", "RAZAO_SOCIAL"]]
        .drop_duplicates()
        .sort_values("RAZAO_SOCIAL")
    )
    cnpj_sel = st.selectbox(
        "🏢 Empresa",
        options=lista_emp["CNPJ_CIA"].tolist(),
        format_func=lambda x: lista_emp.loc[
            lista_emp["CNPJ_CIA"] == x, "RAZAO_SOCIAL"
        ].values[0],
    )

    # Ano
    anos_disp = sorted(df_master["ANO"].unique(), reverse=True)
    ano_sel = st.multiselect("📅 Anos Fiscais", anos_disp, default=[anos_disp[0]])

    # Escopo geográfico (herdado do app principal)
    # Como a gold não tem UF física, mantemos apenas escopo setorial
    escopo_sel = st.radio(
        "🌐 Benchmark",
        options=["Nacional (Mesmo Setor)", "Todo o Universo CVM"],
        help="Define o grupo de comparação para cálculo de medianas e quartis.",
    )

    st.markdown("---")

    # Navegação de views
    st.markdown("### 📊 Módulo de Análise")
    view_sel = st.radio(
        "Selecionar Painel",
        options=[
            "💧 Liquidez",
            "🏗️ Endividamento",
            "💰 Rentabilidade",
            "⚙️ Atividade & Ciclos",
            "🏦 Modelo Fleuriet",
        ],
    )

    st.markdown("---")
    st.caption(f"**Registros:** {len(df_master):,} linhas na Gold")

# ==============================================================================
# 5. FILTROS DERIVADOS
# ==============================================================================
df_ano = df_master[df_master["ANO"].isin(ano_sel)]
df_foco_df = df_ano[df_ano["CNPJ_CIA"] == cnpj_sel]

if df_foco_df.empty:
    st.error(f"Empresa sem dados para o ano {ano_sel}. Selecione outro ano.")
    st.stop()

df_foco: pd.Series = df_foco_df.iloc[0]
nome_empresa = df_foco["RAZAO_SOCIAL"]
setor_empresa = df_foco["SETOR"]

# Benchmark
if escopo_sel.startswith("Nacional"):
    df_concorrentes = df_ano[df_ano["SETOR"] == setor_empresa].copy()
else:
    df_concorrentes = df_ano.copy()

# Histórico completo da empresa (para Efeito Tesoura)
df_hist_empresa = df_master[df_master["CNPJ_CIA"] == cnpj_sel].sort_values("DT_REFER")

# ==============================================================================
# 6. CABEÇALHO
# ==============================================================================
st.title("📐 Painel de Indicadores Financeiros")
st.markdown(f"Análise detalhada: **{nome_empresa}** · Exercício **{ano_sel}**")

st.markdown(
    f"<div class='governance-badge'>Origem: layer_03_gold (PostgreSQL)</div>"
    f"<div class='governance-badge'>Setor: {setor_empresa}</div>"
    f"<div class='governance-badge'>Benchmark: {escopo_sel} · {len(df_concorrentes)} registros</div>"
    f"<div class='governance-badge'>Períodos disponíveis: {len(df_hist_empresa)}</div>",
    unsafe_allow_html=True,
)
st.markdown("---")

# ==============================================================================
# 7. ROTEAMENTO DE VIEWS
# ==============================================================================

if "Liquidez" in view_sel:
    from views.liquidez import render_liquidez_page
    render_liquidez_page(
        df_foco=df_foco,
        df_concorrentes=df_concorrentes,
        nome_empresa=nome_empresa,
        ano=", ".join(ano_sel),
        escopo=escopo_sel,
    )

elif "Endividamento" in view_sel:
    from views.endividamento import render_endividamento_page
    render_endividamento_page(
        df_foco=df_foco,
        df_concorrentes=df_concorrentes,
        nome_empresa=nome_empresa,
        ano=", ".join(ano_sel),
        escopo=escopo_sel,
    )

elif "Rentabilidade" in view_sel:
    from views.rentabilidade import render_rentabilidade_page
    render_rentabilidade_page(
        df_foco=df_foco,
        df_concorrentes=df_concorrentes,
        nome_empresa=nome_empresa,
        ano=", ".join(ano_sel),
        escopo=escopo_sel,
    )

elif "Atividade" in view_sel:
    from views.atividade import render_atividade_page
    render_atividade_page(
        df_foco=df_foco,
        df_concorrentes=df_concorrentes,
        nome_empresa=nome_empresa,
        ano=", ".join(ano_sel),
        escopo=escopo_sel,
    )

elif "Fleuriet" in view_sel:
    from views.fleuriet import render_fleuriet_page
    render_fleuriet_page(
        df_foco=df_foco,
        df_concorrentes=df_concorrentes,
        df_master_empresa=df_hist_empresa,
        nome_empresa=nome_empresa,
        ano=", ".join(ano_sel),
        escopo=escopo_sel,
    )

# ==============================================================================
# 8. RODAPÉ
# ==============================================================================
st.markdown("---")
c1, c2 = st.columns([3, 1])
with c1:
    st.caption(
        "Desenvolvido para fins didáticos de análise de dados financeiros da CVM. "
        "Fonte: `layer_03_gold.mart_indicadores_financeiros` · Data Contract v1.0.0"
    )
with c2:
    st.caption("© 2026 Lucas, Arthur, Guilherme - Big Data for Finance")

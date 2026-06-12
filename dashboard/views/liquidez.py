# views/liquidez.py
"""
Painel de Indicadores de Liquidez
Grupo 1 — Liquidez Geral, Corrente, Seca e Imediata
Fonte: layer_03_gold.mart_indicadores_financeiros
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px


# ==============================================================================
# HELPERS
# ==============================================================================

def _fmt(v, decimals=2, suffix=""):
    """Formata número float com fallback seguro para NaN."""
    if pd.isna(v):
        return "N/D"
    return f"{v:,.{decimals}f}{suffix}"


def _status_html(empresa, benchmark, maior_melhor=True):
    """Retorna badge HTML de comparação com benchmark."""
    if pd.isna(empresa) or pd.isna(benchmark):
        return "<span style='color:#94A3B8;font-weight:600;'>— S/D</span>"
    if maior_melhor:
        ok = empresa >= benchmark
    else:
        ok = empresa <= benchmark
    if ok:
        return "<span style='color:#10B981;font-weight:600;'>▲ Acima</span>"
    return "<span style='color:#EF4444;font-weight:600;'>▼ Abaixo</span>"


def _kpi_card(title, value, suffix, benchmark_label, benchmark_val, empresa_val, maior_melhor=True, reference_note=""):
    """Renderiza um cartão KPI padronizado."""
    status = _status_html(empresa_val, benchmark_val, maior_melhor)
    ref = f"<div style='font-size:10px;color:#94A3B8;margin-top:4px;'>{reference_note}</div>" if reference_note else ""
    st.markdown(
        f"""
        <div style='background:#fff;padding:18px;border-radius:6px;
                    box-shadow:0 1px 3px rgba(15,23,42,.06);
                    border-left:5px solid #1E293B;margin-bottom:10px;'>
            <div style='color:#64748B;font-size:11px;font-weight:700;
                        text-transform:uppercase;letter-spacing:.8px;'>{title}</div>
            <div style='color:#0F172A;font-size:28px;font-weight:700;
                        margin:4px 0;letter-spacing:-.5px;'>{_fmt(empresa_val, suffix=suffix)}</div>
            <div style='font-size:12px;color:#475569;font-weight:500;'>
                {status} | {benchmark_label}: {_fmt(benchmark_val, suffix=suffix)}
            </div>
            {ref}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _gauge(value, title, min_val, max_val, threshold_ok, threshold_warn, unit=""):
    """Cria gauge Plotly reutilizável."""
    if pd.isna(value):
        fig = go.Figure()
        fig.add_annotation(text="Dado não disponível", showarrow=False,
                           font=dict(size=14, color="#94A3B8"))
        fig.update_layout(height=220, margin=dict(t=40, b=10, l=10, r=10))
        return fig

    color = "#10B981" if value >= threshold_ok else ("#F59E0B" if value >= threshold_warn else "#EF4444")
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={"text": title, "font": {"size": 13}},
        number={"suffix": unit, "font": {"size": 22}},
        gauge={
            "axis": {"range": [min_val, max_val], "tickfont": {"size": 10}},
            "bar": {"color": color, "thickness": 0.25},
            "steps": [
                {"range": [min_val, threshold_warn], "color": "#FEE2E2"},
                {"range": [threshold_warn, threshold_ok], "color": "#FEF3C7"},
                {"range": [threshold_ok, max_val], "color": "#D1FAE5"},
            ],
            "threshold": {
                "line": {"color": "#1E293B", "width": 3},
                "thickness": 0.75,
                "value": threshold_ok,
            },
        },
    ))
    fig.update_layout(height=220, margin=dict(t=50, b=10, l=30, r=30))
    return fig


# ==============================================================================
# RENDER PRINCIPAL
# ==============================================================================

def render_liquidez_page(df_foco: pd.Series, df_concorrentes: pd.DataFrame,
                         nome_empresa: str, ano: str, escopo: str):
    """
    Renderiza o painel completo de Liquidez.

    Parameters
    ----------
    df_foco        : pd.Series — linha da empresa selecionada (colunas em UPPER).
    df_concorrentes: pd.DataFrame — empresas do mesmo setor/escopo (para benchmark).
    nome_empresa   : str — razão social da empresa.
    ano            : str — ano fiscal selecionado.
    escopo         : str — label do escopo geográfico.
    """

    st.markdown(f"### 💧 Análise de Liquidez — {nome_empresa} ({ano})")
    st.caption(
        "Mede a **capacidade de pagamento** da empresa. "
        "Fonte: `layer_03_gold.mart_indicadores_financeiros` · "
        f"Benchmark setorial: **{len(df_concorrentes)}** empresas ({escopo})"
    )
    st.markdown("---")

    # ------------------------------------------------------------------
    # Benchmarks medianos do setor
    # ------------------------------------------------------------------
    def med(col):
        s = df_concorrentes[col].replace([np.inf, -np.inf], np.nan).dropna()
        return s.median() if not s.empty else np.nan

    med_lg  = med("IND_LIQUIDEZ_GERAL")
    med_lc  = med("IND_LIQUIDEZ_CORRENTE")
    med_ls  = med("IND_LIQUIDEZ_SECA")
    med_li  = med("IND_LIQUIDEZ_IMEDIATA")

    v_lg  = df_foco.get("IND_LIQUIDEZ_GERAL", np.nan)
    v_lc  = df_foco.get("IND_LIQUIDEZ_CORRENTE", np.nan)
    v_ls  = df_foco.get("IND_LIQUIDEZ_SECA", np.nan)
    v_li  = df_foco.get("IND_LIQUIDEZ_IMEDIATA", np.nan)

    # ------------------------------------------------------------------
    # ROW 1 — KPI Cards
    # ------------------------------------------------------------------
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        _kpi_card("Liquidez Geral", None, "", "Mediana setor", med_lg, v_lg,
                  reference_note="✅ Satisfatório acima de 1,0")
    with c2:
        _kpi_card("Liquidez Corrente", None, "", "Mediana setor", med_lc, v_lc,
                  reference_note="✅ Satisfatório acima de 1,5")
    with c3:
        _kpi_card("Liquidez Seca", None, "", "Mediana setor", med_ls, v_ls,
                  reference_note="✅ Quanto maior, melhor")
    with c4:
        _kpi_card("Liquidez Imediata", None, "", "Mediana setor", med_li, v_li,
                  reference_note="ℹ️ Normal entre 0,10–0,30")

    st.markdown("---")

    # ------------------------------------------------------------------
    # ROW 2 — Gauges visuais
    # ------------------------------------------------------------------
    st.markdown("#### Termômetros de Solvência")
    g1, g2, g3, g4 = st.columns(4)
    with g1:
        st.plotly_chart(_gauge(v_lg, "Liquidez Geral", 0, 3, 1.0, 0.7), use_container_width=True)
    with g2:
        st.plotly_chart(_gauge(v_lc, "Liquidez Corrente", 0, 4, 1.5, 1.0), use_container_width=True)
    with g3:
        st.plotly_chart(_gauge(v_ls, "Liquidez Seca", 0, 4, 1.0, 0.7), use_container_width=True)
    with g4:
        st.plotly_chart(_gauge(v_li, "Liquidez Imediata", 0, 1, 0.3, 0.1), use_container_width=True)

    st.markdown("---")

    # ------------------------------------------------------------------
    # ROW 3 — Evolução Histórica + Boxplot Setorial
    # ------------------------------------------------------------------
    col_hist, col_box = st.columns([1, 1])

    with col_hist:
        st.markdown("#### Evolução Histórica dos Índices")

        # Filtra todos os períodos da empresa selecionada no df_master (passado via concorrentes trick)
        cnpj = df_foco.get("CNPJ_CIA", None)
        if cnpj is not None and not df_concorrentes.empty and "CNPJ_CIA" in df_concorrentes.columns:
            # Recupera histórico de TODAS as datas disponíveis da empresa
            # O df_concorrentes pode não ter outros anos — usamos apenas o que tiver
            df_hist_emp = df_concorrentes[df_concorrentes["CNPJ_CIA"] == cnpj].copy()
        else:
            df_hist_emp = pd.DataFrame()

        if not df_hist_emp.empty and "DT_REFER" in df_hist_emp.columns:
            df_hist_emp = df_hist_emp.sort_values("DT_REFER")
            fig_hist = go.Figure()
            indicadores_hist = {
                "Liq. Geral": ("IND_LIQUIDEZ_GERAL", "#1E293B"),
                "Liq. Corrente": ("IND_LIQUIDEZ_CORRENTE", "#9B2BC7"),
                "Liq. Seca": ("IND_LIQUIDEZ_SECA", "#E0D449"),
                "Liq. Imediata": ("IND_LIQUIDEZ_IMEDIATA", "#82E8E1"),
            }
            for label, (col, cor) in indicadores_hist.items():
                if col in df_hist_emp.columns:
                    fig_hist.add_trace(go.Scatter(
                        x=df_hist_emp["DT_REFER"], y=df_hist_emp[col],
                        name=label, line=dict(color=cor, width=2),
                        mode="lines+markers"
                    ))
            fig_hist.update_layout(
                template="simple_white", height=300,
                margin=dict(t=20, b=20, l=0, r=0),
                legend=dict(orientation="h", y=-0.25),
                yaxis_title="Índice",
            )
            st.plotly_chart(fig_hist, use_container_width=True)
        else:
            st.info("Histórico multi-período não disponível neste escopo de filtro.")

    with col_box:
        st.markdown("#### Posição no Mercado (Boxplot Setorial)")
        with st.expander("Como ler um boxplot?"):
            st.markdown("A linha central é a mediana, o retângulo mostra o 1º e 3º quartis, e os 'bigodes' indicam a variação dentro de 1.5x o IQR. Para mais informações, consulte o seguinte blog: [Como interpretar boxplots](https://fernandafperes.com.br/blog/interpretacao-boxplot/).")
        cols_box = {
            "Liq. Geral": "IND_LIQUIDEZ_GERAL",
            "Liq. Corrente": "IND_LIQUIDEZ_CORRENTE",
            "Liq. Seca": "IND_LIQUIDEZ_SECA",
            "Liq. Imediata": "IND_LIQUIDEZ_IMEDIATA",
        }
        df_melt = df_concorrentes.melt(
            id_vars=["RAZAO_SOCIAL"],
            value_vars=list(cols_box.values()),
            var_name="Indicador", value_name="Valor"
        ).replace([np.inf, -np.inf], np.nan).dropna(subset=["Valor"])

        label_map = {v: k for k, v in cols_box.items()}
        df_melt["Indicador"] = df_melt["Indicador"].map(label_map)

        fig_box = px.box(
            df_melt, x="Indicador", y="Valor",
            color_discrete_sequence=["#475569"],
            points=False,
        )
        # Marca a empresa foco
        for label, col in cols_box.items():
            val = df_foco.get(col, np.nan)
            if not pd.isna(val):
                fig_box.add_trace(go.Scatter(
                    x=[label], y=[val],
                    mode="markers",
                    marker=dict(color="#9B2BC7", size=12, symbol="diamond",
                                line=dict(color="white", width=1.5)),
                    name=nome_empresa, showlegend=(label == list(cols_box.keys())[0])
                ))
        fig_box.update_layout(
            template="simple_white", height=300,
            margin=dict(t=20, b=20, l=0, r=0),
            showlegend=True, legend=dict(orientation="h", y=-0.25),
            yaxis_title="Índice",
        )
        st.plotly_chart(fig_box, use_container_width=True)

    st.markdown("---")

    # ------------------------------------------------------------------
    # ROW 4 — Diagnóstico Qualitativo + Decomposição do AC
    # ------------------------------------------------------------------
    col_diag, col_ac = st.columns([1, 1])

    with col_diag:
        st.markdown("#### Diagnóstico de Solvência")

        def _diag(label, valor, ok_threshold, warn_threshold, maior_melhor=True):
            if pd.isna(valor):
                st.warning(f"**{label}:** Dado não disponível (N/D)")
                return
            if maior_melhor:
                if valor >= ok_threshold:
                    st.success(f"**{label}:** {_fmt(valor)} — ✅ Situação confortável")
                elif valor >= warn_threshold:
                    st.warning(f"**{label}:** {_fmt(valor)} — ⚠️ Atenção recomendada")
                else:
                    st.error(f"**{label}:** {_fmt(valor)} — 🚨 Situação de risco")
            else:
                if valor <= ok_threshold:
                    st.success(f"**{label}:** {_fmt(valor)} — ✅ Situação confortável")
                elif valor <= warn_threshold:
                    st.warning(f"**{label}:** {_fmt(valor)} — ⚠️ Atenção recomendada")
                else:
                    st.error(f"**{label}:** {_fmt(valor)} — 🚨 Situação de risco")

        _diag("Liquidez Geral", v_lg, 1.0, 0.7)
        _diag("Liquidez Corrente", v_lc, 1.5, 1.0)
        _diag("Liquidez Seca", v_ls, 1.0, 0.7)

        # Alerta de caixa ocioso
        if not pd.isna(v_li) and v_li > 0.5:
            st.info("ℹ️ **Caixa Elevado:** Liquidez Imediata acima de 0,50 pode indicar capital ocioso — "
                    "oportunidade de alocação em investimentos ou redução de dívida.")
        elif not pd.isna(v_li) and v_li < 0.05:
            st.warning("⚠️ **Caixa Baixo:** Liquidez Imediata abaixo de 0,05 — empresa depende "
                       "fortemente de linhas de crédito para honrar pagamentos imediatos.")

    with col_ac:
        st.markdown("#### Composição do Ativo Circulante")
        v_caixa  = df_foco.get("V22_CAIXA_BP", 0) or 0
        v_aplic  = df_foco.get("V15B_APLIC_FIN", 0) or 0
        v_cr     = df_foco.get("V07_CONTAS_RECEBER", 0) or 0
        v_estq   = df_foco.get("V06_ESTOQUES", 0) or 0
        v_outros = max(0, (df_foco.get("V02_ATIVO_CIRC", 0) or 0)
                       - v_caixa - v_aplic - v_cr - v_estq)

        labels = ["Caixa", "Aplic. Fin.", "Contas a Receber", "Estoques", "Outros"]
        values = [v_caixa, v_aplic, v_cr, v_estq, v_outros]
        colors = ["#1E293B", "#9B2BC7", "#82E8E1", "#E0D449", "#CBD5E1"]

        # Remove zeros
        filtered = [(l, v, c) for l, v, c in zip(labels, values, colors) if v > 0]
        if filtered:
            fl, fv, fc = zip(*filtered)
            fig_ac = go.Figure(go.Bar(
                x=fl, y=fv,
                marker_color=fc,
                text=[f"R$ {v:,.0f}" for v in fv],
                textposition='auto',
            ))
            fig_ac.update_layout(
                height=300, 
                margin=dict(t=10, b=10, l=0, r=0),
                template="simple_white",
                yaxis_title="Valor (R$)"
            )
            st.plotly_chart(fig_ac, use_container_width=True)
        else:
            st.info("Dados do Ativo Circulante não disponíveis para decomposição.")

    st.markdown("---")

    # ------------------------------------------------------------------
    # ROW 5 — Tabela-resumo
    # ------------------------------------------------------------------
    st.markdown("#### Tabela-Resumo dos Indicadores de Liquidez")

    resumo = pd.DataFrame({
        "Indicador": [
            "Liquidez Geral (LG)",
            "Liquidez Corrente (LC)",
            "Liquidez Seca (LS)",
            "Liquidez Imediata (LI)",
        ],
        "Fórmula": [
            "(AC + RLP) / (PC + ELP)",
            "AC / PC",
            "(AC − Estoques) / PC",
            "Caixa (BP) / PC",
        ],
        f"Empresa ({ano})": [
            _fmt(v_lg), _fmt(v_lc), _fmt(v_ls), _fmt(v_li)
        ],
        "Mediana Setor": [
            _fmt(med_lg), _fmt(med_lc), _fmt(med_ls), _fmt(med_li)
        ],
        "Referência": ["> 1,0", "> 1,5", "> 1,0", "0,10 – 0,30"],
    })
    st.dataframe(resumo, use_container_width=True, hide_index=True)

    st.caption(
        "**Fonte:** `layer_03_gold.mart_indicadores_financeiros` | "
        "**Contas:** V02 (AC), V04 (RLP), V10 (PC), V11 (PNC), V06 (Estoques), V22 (Caixa BP) | "
        "**Premissa:** Nota N1 — Liquidez Imediata usa `1.01.01` (BP), nunca `6.05.02` (DFC)."
    )

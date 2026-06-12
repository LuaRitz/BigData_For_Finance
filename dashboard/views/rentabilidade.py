# views/rentabilidade.py
"""
Painel de Rentabilidade
Grupo 3 + 4 — Margens (Bruta, Operacional, Líquida), LPA, ROA, ROE, ROI
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
    if pd.isna(v):
        return "N/D"
    return f"{v:,.{decimals}f}{suffix}"


def _kpi_card_rent(title, empresa_val, suffix, benchmark_val, benchmark_label,
                    cor_positiva="#10B981", reference_note=""):
    if pd.isna(empresa_val) or pd.isna(benchmark_val):
        cor_borda = "#94A3B8"
        status = "<span style='color:#94A3B8;'>— S/D</span>"
    elif empresa_val >= benchmark_val:
        cor_borda = cor_positiva
        status = f"<span style='color:{cor_positiva};font-weight:600;'>▲ Acima</span>"
    else:
        cor_borda = "#EF4444"
        status = "<span style='color:#EF4444;font-weight:600;'>▼ Abaixo</span>"

    ref = f"<div style='font-size:10px;color:#94A3B8;margin-top:4px;'>{reference_note}</div>" if reference_note else ""
    st.markdown(
        f"""
        <div style='background:#fff;padding:18px;border-radius:6px;
                    box-shadow:0 1px 3px rgba(15,23,42,.06);
                    border-left:5px solid {cor_borda};margin-bottom:10px;'>
            <div style='color:#64748B;font-size:11px;font-weight:700;
                        text-transform:uppercase;letter-spacing:.8px;'>{title}</div>
            <div style='color:#0F172A;font-size:26px;font-weight:700;
                        margin:4px 0;'>{_fmt(empresa_val, suffix=suffix)}</div>
            <div style='font-size:12px;color:#475569;'>
                {status} | {benchmark_label}: {_fmt(benchmark_val, suffix=suffix)}
            </div>
            {ref}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ==============================================================================
# RENDER PRINCIPAL
# ==============================================================================

def render_rentabilidade_page(df_foco: pd.Series, df_concorrentes: pd.DataFrame,
                               nome_empresa: str, ano: str, escopo: str):
    """
    Renderiza o painel de Rentabilidade e Margens.
    """

    st.markdown(f"### 💰 Rentabilidade e Margens — {nome_empresa} ({ano})")
    st.caption(
        "Mede **quanto sobra de cada R$ 1,00 vendido** e o retorno gerado sobre os ativos e capital. "
        f"Benchmark setorial: **{len(df_concorrentes)}** empresas ({escopo})"
    )
    st.markdown("---")

    # ------------------------------------------------------------------
    # Variáveis
    # ------------------------------------------------------------------
    v_rec   = df_foco.get("V17_RECEITA_LIQ", np.nan)
    v_cpv   = df_foco.get("V18_CPV", np.nan)
    v_lb    = df_foco.get("V19_LUCRO_BRUTO", np.nan)
    v_ebit  = df_foco.get("V20_EBIT", np.nan)
    v_ll    = df_foco.get("V21_LUCRO_LIQ", np.nan)
    v_lpa_b = df_foco.get("V25_LPA_BASICO", np.nan)
    v_lpa_d = df_foco.get("V26_LPA_DILUIDO", np.nan)

    v_mb  = df_foco.get("IND_MARGEM_BRUTA", np.nan)
    v_mo  = df_foco.get("IND_MARGEM_OPERACIONAL", np.nan)
    v_ml  = df_foco.get("IND_MARGEM_LIQUIDA", np.nan)
    v_roa = df_foco.get("IND_ROA", np.nan)
    v_roe = df_foco.get("IND_ROE", np.nan)
    v_roi = df_foco.get("IND_ROI", np.nan)

    def med(col):
        s = df_concorrentes[col].replace([np.inf, -np.inf], np.nan).dropna()
        return s.median() if not s.empty else np.nan

    med_mb  = med("IND_MARGEM_BRUTA")
    med_mo  = med("IND_MARGEM_OPERACIONAL")
    med_ml  = med("IND_MARGEM_LIQUIDA")
    med_roa = med("IND_ROA")
    med_roe = med("IND_ROE")
    med_roi = med("IND_ROI")

    # ------------------------------------------------------------------
    # ROW 1 — Cascata DRE Waterfall
    # ------------------------------------------------------------------
    st.markdown("#### Cascata de Margens (DRE Waterfall)")
    col_wf, col_lpa = st.columns([2, 1])

    with col_wf:
        if not any(pd.isna(x) for x in [v_rec, v_lb, v_ebit, v_ll]):
            cpv_abs = abs(v_cpv) if not pd.isna(v_cpv) else (v_rec - v_lb)
            desp_op = v_lb - v_ebit
            desp_fin_e_imp = v_ebit - v_ll

            fig_wf = go.Figure(go.Waterfall(
                orientation="v",
                measure=["absolute", "relative", "total", "relative", "total", "relative", "total"],
                x=["Receita Líquida", "(-) CPV", "= Lucro Bruto",
                   "(-) Desp. Operacionais", "= EBIT",
                   "(-) Fin./Impostos", "= Lucro Líquido"],
                y=[v_rec, -cpv_abs, v_lb, -max(0, desp_op), v_ebit,
                   -max(0, desp_fin_e_imp), v_ll],
                connector={"line": {"color": "#CBD5E1"}},
                increasing={"marker": {"color": "#10B981"}},
                decreasing={"marker": {"color": "#EF4444"}},
                totals={"marker": {"color": "#1E293B"}},
                texttemplate="%{y:,.0f}",
                textposition="outside",
            ))
            fig_wf.update_layout(
                template="simple_white", height=320,
                margin=dict(t=20, b=40, l=0, r=0),
                yaxis_title="R$ (mil)",
                showlegend=False,
            )
            st.plotly_chart(fig_wf, use_container_width=True)
        else:
            st.info("Dados da DRE insuficientes para montar a cascata de margens.")

    with col_lpa:
        st.markdown("**Lucro por Ação (LPA)**")
        st.markdown(
            f"""
            <div style='background:#F8FAFC;padding:20px;border-radius:8px;border:1px solid #E2E8F0;'>
                <div style='font-size:12px;color:#64748B;font-weight:600;
                            text-transform:uppercase;letter-spacing:.5px;'>LPA Básico ON</div>
                <div style='font-size:28px;font-weight:700;color:#1E293B;margin:6px 0;'>
                    {_fmt(v_lpa_b, suffix=" R$/ação")}
                </div>
                <div style='font-size:12px;color:#64748B;font-weight:600;
                            text-transform:uppercase;letter-spacing:.5px;margin-top:16px;'>LPA Diluído ON</div>
                <div style='font-size:28px;font-weight:700;color:#9B2BC7;margin:6px 0;'>
                    {_fmt(v_lpa_d, suffix=" R$/ação")}
                </div>
                <div style='font-size:10px;color:#94A3B8;margin-top:12px;'>
                    Fonte: 3.99.01.01 (básico) · 3.99.02.01 (diluído)<br>
                    Premissa N3: nunca usar conta pai 3.99
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        # Alerta Marisa
        if not pd.isna(v_lpa_b) and abs(v_lpa_b) > 10000:
            st.warning("⚠️ **Outlier detectado:** |LPA| > R$10.000 — suspeita de dado anômalo "
                       "(cf. filtro Marisa 2021 no premissas_calculo.md).")

    st.markdown("---")

    # ------------------------------------------------------------------
    # ROW 2 — KPI Cards: Margens
    # ------------------------------------------------------------------
    st.markdown("#### Indicadores de Margem")
    c1, c2, c3 = st.columns(3)
    with c1:
        _kpi_card_rent("Margem Bruta", v_mb * 100 if not pd.isna(v_mb) else np.nan, "%",
                       med_mb * 100 if not pd.isna(med_mb) else np.nan, "Mediana setor",
                       reference_note="Lucro Bruto / Receita Líquida")
    with c2:
        _kpi_card_rent("Margem Operacional (EBIT)", v_mo * 100 if not pd.isna(v_mo) else np.nan, "%",
                       med_mo * 100 if not pd.isna(med_mo) else np.nan, "Mediana setor",
                       reference_note="EBIT / Receita Líquida — conta 3.05")
    with c3:
        _kpi_card_rent("Margem Líquida", v_ml * 100 if not pd.isna(v_ml) else np.nan, "%",
                       med_ml * 100 if not pd.isna(med_ml) else np.nan, "Mediana setor",
                       reference_note="Lucro Líquido / Receita Líquida")

    st.markdown("---")

    # ------------------------------------------------------------------
    # ROW 3 — KPI Cards: Retornos + Comparativo Setor
    # ------------------------------------------------------------------
    st.markdown("#### Retornos sobre Investimento")
    c4, c5, c6 = st.columns(3)
    with c4:
        _kpi_card_rent("ROA — Retorno s/ Ativos", v_roa * 100 if not pd.isna(v_roa) else np.nan, "%",
                       med_roa * 100 if not pd.isna(med_roa) else np.nan, "Mediana setor",
                       reference_note="Lucro Líquido / Ativo Total")
    with c5:
        _kpi_card_rent("ROE — Retorno s/ PL", v_roe * 100 if not pd.isna(v_roe) else np.nan, "%",
                       med_roe * 100 if not pd.isna(med_roe) else np.nan, "Mediana setor",
                       cor_positiva="#9B2BC7", reference_note="Lucro Líquido / Patrimônio Líquido")
    with c6:
        _kpi_card_rent("ROI — Retorno s/ Invest.", v_roi * 100 if not pd.isna(v_roi) else np.nan, "%",
                       med_roi * 100 if not pd.isna(med_roi) else np.nan, "Mediana setor",
                       reference_note="LL / (PL + Emp.CP + Emp.LP)")

    st.markdown("---")

    # ------------------------------------------------------------------
    # ROW 4 — Gráfico Comparativo + Evolução Histórica
    # ------------------------------------------------------------------
    col_comp, col_hist = st.columns([1, 1])

    with col_comp:
        st.markdown("#### Comparativo com Setor (Boxplot)")
        with st.expander("Como ler um boxplot?"):
            st.markdown("A linha central é a mediana, o retângulo mostra o 1º e 3º quartis, e os 'bigodes' indicam a variação dentro de 1.5x o IQR. Para mais informações, consulte o seguinte blog: [Como interpretar boxplots](https://fernandafperes.com.br/blog/interpretacao-boxplot/).")
        cols_box = {
            "Margem Bruta %": "IND_MARGEM_BRUTA",
            "Margem Op. %": "IND_MARGEM_OPERACIONAL",
            "Margem Líq. %": "IND_MARGEM_LIQUIDA",
            "ROE %": "IND_ROE",
            "ROA %": "IND_ROA",
        }
        # Converte para %
        df_box = df_concorrentes[["RAZAO_SOCIAL"] + list(cols_box.values())].copy()
        for col in cols_box.values():
            df_box[col] = df_box[col] * 100

        df_melt = df_box.melt(
            id_vars=["RAZAO_SOCIAL"],
            value_vars=list(cols_box.values()),
            var_name="Indicador", value_name="Valor"
        ).replace([np.inf, -np.inf], np.nan).dropna(subset=["Valor"])
        label_map = {v: k for k, v in cols_box.items()}
        df_melt["Indicador"] = df_melt["Indicador"].map(label_map)

        fig_box = px.box(df_melt, x="Indicador", y="Valor",
                         color_discrete_sequence=["#475569"], points=False)

        # Marca empresa foco
        for label, col in cols_box.items():
            val = df_foco.get(col, np.nan)
            if not pd.isna(val):
                fig_box.add_trace(go.Scatter(
                    x=[label], y=[val * 100],
                    mode="markers",
                    marker=dict(color="#9B2BC7", size=12, symbol="diamond",
                                line=dict(color="white", width=1.5)),
                    name=nome_empresa,
                    showlegend=(label == list(cols_box.keys())[0])
                ))
        fig_box.update_layout(
            template="simple_white", height=320,
            margin=dict(t=20, b=60, l=0, r=0),
            yaxis_title="%",
            legend=dict(orientation="h", y=-0.3, font=dict(size=10)),
            xaxis=dict(tickangle=-20),
        )
        st.plotly_chart(fig_box, use_container_width=True)

    with col_hist:
        st.markdown("#### Evolução Histórica das Margens")
        cnpj = df_foco.get("CNPJ_CIA", None)
        if cnpj is not None and not df_concorrentes.empty and "CNPJ_CIA" in df_concorrentes.columns:
            df_hist = df_concorrentes[df_concorrentes["CNPJ_CIA"] == cnpj].sort_values("DT_REFER")
        else:
            df_hist = pd.DataFrame()

        if not df_hist.empty and "DT_REFER" in df_hist.columns:
            fig_hist = go.Figure()
            series = [
                ("Margem Bruta", "IND_MARGEM_BRUTA", "#1E293B"),
                ("Margem Operacional", "IND_MARGEM_OPERACIONAL", "#9B2BC7"),
                ("Margem Líquida", "IND_MARGEM_LIQUIDA", "#10B981"),
                ("ROE", "IND_ROE", "#E0D449"),
                ("ROA", "IND_ROA", "#82E8E1"),
            ]
            for label, col, cor in series:
                if col in df_hist.columns:
                    fig_hist.add_trace(go.Scatter(
                        x=df_hist["DT_REFER"],
                        y=df_hist[col] * 100,
                        name=label, line=dict(color=cor, width=2), mode="lines+markers"
                    ))
            # Linha de zero
            fig_hist.add_hline(y=0, line_dash="dot", line_color="#94A3B8", line_width=1)
            fig_hist.update_layout(
                template="simple_white", height=320,
                margin=dict(t=20, b=20, l=0, r=0),
                legend=dict(orientation="h", y=-0.3, font=dict(size=9)),
                yaxis_title="%",
            )
            st.plotly_chart(fig_hist, use_container_width=True)
        else:
            st.info("Histórico multi-período não disponível neste escopo.")

    st.markdown("---")

    # ------------------------------------------------------------------
    # ROW 5 — Diagnóstico qualitativo
    # ------------------------------------------------------------------
    st.markdown("#### Diagnóstico de Rentabilidade")
    d1, d2 = st.columns(2)

    with d1:
        ml_pct = v_ml * 100 if not pd.isna(v_ml) else np.nan
        if not pd.isna(ml_pct):
            if ml_pct < 0:
                st.error(f"**Margem Líquida ({_fmt(ml_pct)}%):** 🔴 Empresa com prejuízo — custos e despesas "
                         "superam a receita operacional.")
            elif ml_pct < 5:
                st.warning(f"**Margem Líquida ({_fmt(ml_pct)}%):** ⚠️ Margem muito estreita — empresa vulnerável "
                           "a choques de custo ou queda de receita.")
            elif ml_pct < 15:
                st.info(f"**Margem Líquida ({_fmt(ml_pct)}%):** 🔵 Margem aceitável para a maioria dos setores.")
            else:
                st.success(f"**Margem Líquida ({_fmt(ml_pct)}%):** 🟢 Margem sólida — empresa com bom poder "
                           "de precificação ou estrutura de custos eficiente.")

        roe_pct = v_roe * 100 if not pd.isna(v_roe) else np.nan
        if not pd.isna(roe_pct):
            if roe_pct < 0:
                st.error(f"**ROE ({_fmt(roe_pct)}%):** Empresa destruindo valor para os acionistas.")
            elif roe_pct < 10:
                st.warning(f"**ROE ({_fmt(roe_pct)}%):** Retorno abaixo do custo de capital típico (Selic/WACC).")
            else:
                st.success(f"**ROE ({_fmt(roe_pct)}%):** Retorno competitivo sobre patrimônio dos acionistas.")

    with d2:
        if not pd.isna(v_mb) and not pd.isna(v_ml):
            gap = (v_mb - v_ml) * 100
            if gap > 30:
                st.warning(f"**Gap Bruta→Líquida ({_fmt(gap)}pp):** Grande erosão de margem entre o bruto e o líquido "
                           "— despesas financeiras ou tributárias elevadas.")
            elif gap > 15:
                st.info(f"**Gap Bruta→Líquida ({_fmt(gap)}pp):** Erosão moderada — avaliar estrutura de despesas.")
            else:
                st.success(f"**Gap Bruta→Líquida ({_fmt(gap)}pp):** Controle de despesas eficiente.")

        if not pd.isna(v_roa) and not pd.isna(v_roe):
            if v_roe > v_roa * 1.5:
                st.info("**ROE > 1,5× ROA:** Empresa usa alavancagem financeira para amplificar o retorno — "
                        "estratégia válida se a dívida estiver bem dimensionada.")

    st.markdown("---")

    # ------------------------------------------------------------------
    # ROW 6 — Tabela-resumo
    # ------------------------------------------------------------------
    st.markdown("#### Tabela-Resumo dos Indicadores de Rentabilidade")
    resumo = pd.DataFrame({
        "Indicador": [
            "Margem Bruta",
            "Margem Operacional (EBIT)",
            "Margem Líquida",
            "ROA",
            "ROE",
            "ROI",
            "LPA Básico ON",
            "LPA Diluído ON",
        ],
        "Fórmula / Conta": [
            "3.03 / 3.01",
            "3.05 / 3.01",
            "3.11 / 3.01",
            "3.11 / 1",
            "3.11 / 2.03",
            "3.11 / (2.03+V13+V14)",
            "3.99.01.01",
            "COALESCE(3.99.02.01, 3.99.01.01)",
        ],
        f"Empresa ({ano})": [
            _fmt(v_mb * 100 if not pd.isna(v_mb) else np.nan, suffix="%"),
            _fmt(v_mo * 100 if not pd.isna(v_mo) else np.nan, suffix="%"),
            _fmt(v_ml * 100 if not pd.isna(v_ml) else np.nan, suffix="%"),
            _fmt(v_roa * 100 if not pd.isna(v_roa) else np.nan, suffix="%"),
            _fmt(v_roe * 100 if not pd.isna(v_roe) else np.nan, suffix="%"),
            _fmt(v_roi * 100 if not pd.isna(v_roi) else np.nan, suffix="%"),
            _fmt(v_lpa_b, suffix=" R$/ação"),
            _fmt(v_lpa_d, suffix=" R$/ação"),
        ],
        "Mediana Setor": [
            _fmt(med_mb * 100 if not pd.isna(med_mb) else np.nan, suffix="%"),
            _fmt(med_mo * 100 if not pd.isna(med_mo) else np.nan, suffix="%"),
            _fmt(med_ml * 100 if not pd.isna(med_ml) else np.nan, suffix="%"),
            _fmt(med_roa * 100 if not pd.isna(med_roa) else np.nan, suffix="%"),
            _fmt(med_roe * 100 if not pd.isna(med_roe) else np.nan, suffix="%"),
            _fmt(med_roi * 100 if not pd.isna(med_roi) else np.nan, suffix="%"),
            "—", "—",
        ],
    })
    st.dataframe(resumo, use_container_width=True, hide_index=True)

    st.caption(
        "**Fonte:** `layer_03_gold.mart_indicadores_financeiros` | "
        "**Premissa N3:** LPA usa leaves `3.99.01.01` / `3.99.02.01` — nunca a conta pai `3.99`."
    )

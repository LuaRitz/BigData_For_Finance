# views/atividade.py
"""
Painel de Atividade, Giro e Ciclos Operacionais
Grupo 5 + 6 — Giros (Estoques, CR, CP, AC), Prazos Médios (PMRE, PMRV, PMPC, PMRAC),
               Ciclo Econômico e Ciclo Financeiro
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

def _fmt(v, decimals=1, suffix=""):
    if pd.isna(v):
        return "N/D"
    return f"{v:,.{decimals}f}{suffix}"


def _kpi_card_ativ(title, empresa_val, suffix, benchmark_val, maior_melhor=True,
                    reference_note="", highlight_color="#1E293B"):
    if pd.isna(empresa_val) or pd.isna(benchmark_val):
        cor_borda = "#94A3B8"
        status = "<span style='color:#94A3B8;'>— S/D</span>"
    elif maior_melhor:
        cor_borda = "#10B981" if empresa_val >= benchmark_val else "#EF4444"
        status = ("<span style='color:#10B981;font-weight:600;'>▲ Acima</span>"
                  if empresa_val >= benchmark_val else
                  "<span style='color:#EF4444;font-weight:600;'>▼ Abaixo</span>")
    else:
        cor_borda = "#10B981" if empresa_val <= benchmark_val else "#EF4444"
        status = ("<span style='color:#10B981;font-weight:600;'>▼ Melhor</span>"
                  if empresa_val <= benchmark_val else
                  "<span style='color:#EF4444;font-weight:600;'>▲ Pior</span>")

    ref = f"<div style='font-size:10px;color:#94A3B8;margin-top:4px;'>{reference_note}</div>" if reference_note else ""
    val_display = _fmt(empresa_val, suffix=suffix)
    st.markdown(
        f"""
        <div style='background:#fff;padding:16px;border-radius:6px;
                    box-shadow:0 1px 3px rgba(15,23,42,.06);
                    border-left:5px solid {cor_borda};margin-bottom:10px;'>
            <div style='color:#64748B;font-size:10px;font-weight:700;
                        text-transform:uppercase;letter-spacing:.8px;'>{title}</div>
            <div style='color:#0F172A;font-size:24px;font-weight:700;
                        margin:4px 0;'>{val_display}</div>
            <div style='font-size:11px;color:#475569;'>
                {status} | Med: {_fmt(benchmark_val, suffix=suffix)}
            </div>
            {ref}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ==============================================================================
# RENDER PRINCIPAL
# ==============================================================================

def render_atividade_page(df_foco: pd.Series, df_concorrentes: pd.DataFrame,
                           nome_empresa: str, ano: str, escopo: str):
    """
    Renderiza o painel de Atividade, Giro e Ciclos.
    """

    st.markdown(f"### ⚙️ Atividade, Giro e Ciclos Operacionais — {nome_empresa} ({ano})")
    st.caption(
        "Mede a **eficiência operacional** da empresa — quantas vezes os ativos giram e quanto tempo "
        "o dinheiro fica 'preso' no ciclo. "
        f"Benchmark setorial: **{len(df_concorrentes)}** empresas ({escopo})"
    )
    st.markdown("---")

    # ------------------------------------------------------------------
    # Indicadores
    # ------------------------------------------------------------------
    v_ge    = df_foco.get("IND_GIRO_ESTOQUES", np.nan)
    v_gcr   = df_foco.get("IND_GIRO_CR", np.nan)
    v_gcp   = df_foco.get("IND_GIRO_CP", np.nan)
    v_gac   = df_foco.get("IND_GIRO_AC", np.nan)
    v_pmre  = df_foco.get("IND_PMRE", np.nan)
    v_pmrv  = df_foco.get("IND_PMRV", np.nan)
    v_pmpc  = df_foco.get("IND_PMPC", np.nan)
    v_pmrac = df_foco.get("IND_PMRAC", np.nan)
    v_ce    = df_foco.get("IND_CICLO_ECONOMICO", np.nan)
    v_cf    = df_foco.get("IND_CICLO_FINANCEIRO", np.nan)

    def med(col):
        s = df_concorrentes[col].replace([np.inf, -np.inf], np.nan).dropna()
        return s.median() if not s.empty else np.nan

    med_ge    = med("IND_GIRO_ESTOQUES")
    med_gcr   = med("IND_GIRO_CR")
    med_gcp   = med("IND_GIRO_CP")
    med_gac   = med("IND_GIRO_AC")
    med_pmre  = med("IND_PMRE")
    med_pmrv  = med("IND_PMRV")
    med_pmpc  = med("IND_PMPC")
    med_pmrac = med("IND_PMRAC")
    med_ce    = med("IND_CICLO_ECONOMICO")
    med_cf    = med("IND_CICLO_FINANCEIRO")

    # ------------------------------------------------------------------
    # ROW 1 — Diagrama Visual do Ciclo (timeline horizontal)
    # ------------------------------------------------------------------
    st.markdown("#### Diagrama do Ciclo Operacional e Financeiro")

    pmre_d  = v_pmre  if not pd.isna(v_pmre)  else 0
    pmrv_d  = v_pmrv  if not pd.isna(v_pmrv)  else 0
    pmpc_d  = v_pmpc  if not pd.isna(v_pmpc)  else 0
    ce_d    = pmre_d + pmrv_d
    cf_d    = ce_d - pmpc_d

    fig_ciclo = go.Figure()

    # Barra Ciclo Econômico
    fig_ciclo.add_trace(go.Bar(
        name="PMRE (Estoque)",
        x=[pmre_d], y=["Ciclo Econômico"],
        orientation="h", marker_color="#E0D449",
        text=[f"PMRE: {_fmt(pmre_d, 0)} dias"],
        textposition="inside", insidetextanchor="middle",
    ))
    fig_ciclo.add_trace(go.Bar(
        name="PMRV (Recebimento)",
        x=[pmrv_d], y=["Ciclo Econômico"],
        orientation="h", marker_color="#9B2BC7",
        text=[f"PMRV: {_fmt(pmrv_d, 0)} dias"],
        textposition="inside", insidetextanchor="middle",
    ))

    # Barra Ciclo Financeiro (PMPC reduz)
    fig_ciclo.add_trace(go.Bar(
        name="PMPC (Pagamento — reduz ciclo)",
        x=[pmpc_d], y=["Ciclo Financeiro"],
        orientation="h", marker_color="#10B981",
        text=[f"PMPC: {_fmt(pmpc_d, 0)} dias"],
        textposition="inside", insidetextanchor="middle",
    ))
    restante = max(0, ce_d - pmpc_d)
    fig_ciclo.add_trace(go.Bar(
        name="Ciclo Financeiro Restante",
        x=[restante], y=["Ciclo Financeiro"],
        orientation="h", marker_color="#EF4444",
        text=[f"CF: {_fmt(restante, 0)} dias"],
        textposition="inside", insidetextanchor="middle",
    ))

    fig_ciclo.update_layout(
        barmode="stack", template="simple_white", height=200,
        margin=dict(t=10, b=10, l=10, r=10),
        legend=dict(orientation="h", y=-0.5, font=dict(size=10)),
        xaxis_title="Dias",
    )
    st.plotly_chart(fig_ciclo, use_container_width=True)

    if cf_d < 0:
        st.success(f"✅ **Ciclo Financeiro Negativo ({_fmt(cf_d, 0)} dias):** A empresa recebe dos clientes "
                   "antes de pagar seus fornecedores — operação **autofinanciada** (modelo supermercado/e-commerce).")
    elif cf_d <= 30:
        st.info(f"ℹ️ **Ciclo Financeiro Curto ({_fmt(cf_d, 0)} dias):** Necessidade de capital de giro reduzida.")
    elif cf_d <= 90:
        st.warning(f"⚠️ **Ciclo Financeiro Moderado ({_fmt(cf_d, 0)} dias):** Capital de giro necessário para "
                   "cobrir o gap entre pagar e receber.")
    else:
        st.error(f"🚨 **Ciclo Financeiro Longo ({_fmt(cf_d, 0)} dias):** Alta necessidade de capital de giro — "
                 "risco se crédito estiver restrito.")

    st.markdown("---")

    # ------------------------------------------------------------------
    # ROW 2 — Prazos Médios (KPI cards)
    # ------------------------------------------------------------------
    st.markdown("#### Prazos Médios (dias)")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        has_estoque = not pd.isna(df_foco.get("V06_ESTOQUES_RAW", np.nan))
        if has_estoque or not pd.isna(v_pmre):
            _kpi_card_ativ("PMRE — Renovação Estoques", v_pmre, " dias",
                           med_pmre, maior_melhor=False,
                           reference_note="⬇️ Menos dias = giro mais rápido")
        else:
            st.info("**PMRE:** N/A\n\n*(empresa sem estoques — setor serviços)*")
    with c2:
        _kpi_card_ativ("PMRV — Recebimento Vendas", v_pmrv, " dias",
                       med_pmrv, maior_melhor=False,
                       reference_note="⬇️ Menos dias = caixa mais rápido")
    with c3:
        _kpi_card_ativ("PMPC — Pagamento Fornec.", v_pmpc, " dias",
                       med_pmpc, maior_melhor=True,
                       reference_note="⬆️ Mais dias = melhor para o caixa")
    with c4:
        _kpi_card_ativ("PMRAC — Giro AC", v_pmrac, " dias",
                       med_pmrac, maior_melhor=False,
                       reference_note="⬇️ Menos dias = ativo circulante mais eficiente")

    st.markdown("---")

    # ------------------------------------------------------------------
    # ROW 3 — Indicadores de Giro (KPI cards)
    # ------------------------------------------------------------------
    st.markdown("#### Giros (vezes por período)")
    c5, c6, c7, c8 = st.columns(4)
    with c5:
        _kpi_card_ativ("Giro de Estoques", v_ge, "x", med_ge, maior_melhor=True,
                       reference_note="⬆️ Mais giros = estoque mais eficiente",
                       highlight_color="#E0D449")
    with c6:
        _kpi_card_ativ("Giro Contas a Receber", v_gcr, "x", med_gcr, maior_melhor=True,
                       reference_note="⬆️ Mais giros = recebimento mais ágil")
    with c7:
        _kpi_card_ativ("Giro Contas a Pagar", v_gcp, "x", med_gcp, maior_melhor=False,
                       reference_note="⬇️ Menos giros = mais prazo c/ fornecedores")
    with c8:
        _kpi_card_ativ("Giro Ativo Circulante", v_gac, "x", med_gac, maior_melhor=True,
                       reference_note="⬆️ Mais giros = AC mais produtivo")

    st.markdown("---")

    # ------------------------------------------------------------------
    # ROW 4 — Comparativo setorial (radar de prazos)
    # ------------------------------------------------------------------
    col_radar, col_hist = st.columns([1, 1])

    with col_radar:
        st.markdown("#### Radar de Eficiência Operacional")
        # Score normalizado: para prazos, menor = melhor → invertemos
        radar_def = [
            ("PMRE (inv.)", "IND_PMRE", False),
            ("PMRV (inv.)", "IND_PMRV", False),
            ("PMPC", "IND_PMPC", True),          # maior = melhor
            ("Giro CR", "IND_GIRO_CR", True),
            ("Giro Estoq.", "IND_GIRO_ESTOQUES", True),
        ]
        labels_r = [x[0] for x in radar_def]

        def norm_score(val, col, mb):
            s = df_concorrentes[col].replace([np.inf, -np.inf], np.nan).dropna()
            if s.empty or pd.isna(val):
                return 0.5
            p5, p95 = s.quantile(0.05), s.quantile(0.95)
            rng = p95 - p5
            if rng == 0:
                return 0.5
            score = (val - p5) / rng
            score = max(0.0, min(1.0, score))
            return score if mb else 1.0 - score

        scores_emp = [norm_score(df_foco.get(col, np.nan), col, mb) for _, col, mb in radar_def]
        scores_med = [norm_score(df_concorrentes[col].replace([np.inf,-np.inf],np.nan).dropna().median()
                                 if not df_concorrentes.empty else np.nan, col, mb)
                      for _, col, mb in radar_def]

        fig_r = go.Figure()
        fig_r.add_trace(go.Scatterpolar(
            r=scores_emp + [scores_emp[0]], theta=labels_r + [labels_r[0]],
            fill="toself", fillcolor="rgba(155,43,199,.15)",
            line=dict(color="#9B2BC7", width=2), name=nome_empresa
        ))
        fig_r.add_trace(go.Scatterpolar(
            r=scores_med + [scores_med[0]], theta=labels_r + [labels_r[0]],
            fill="toself", fillcolor="rgba(30,41,59,.08)",
            line=dict(color="#1E293B", width=1.5, dash="dash"), name="Mediana Setor"
        ))
        fig_r.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 1], tickfont=dict(size=8))),
            showlegend=True, height=320,
            margin=dict(t=20, b=20, l=20, r=20),
            legend=dict(font=dict(size=10)),
        )
        st.plotly_chart(fig_r, use_container_width=True)

    with col_hist:
        st.markdown("#### Evolução Histórica dos Prazos Médios")
        cnpj = df_foco.get("CNPJ_CIA", None)
        if cnpj is not None and not df_concorrentes.empty and "CNPJ_CIA" in df_concorrentes.columns:
            df_hist = df_concorrentes[df_concorrentes["CNPJ_CIA"] == cnpj].sort_values("DT_REFER")
        else:
            df_hist = pd.DataFrame()

        if not df_hist.empty and "DT_REFER" in df_hist.columns:
            fig_hist = go.Figure()
            series = [
                ("PMRE", "IND_PMRE", "#E0D449"),
                ("PMRV", "IND_PMRV", "#9B2BC7"),
                ("PMPC", "IND_PMPC", "#10B981"),
                ("Ciclo Fin.", "IND_CICLO_FINANCEIRO", "#EF4444"),
            ]
            for label, col, cor in series:
                if col in df_hist.columns:
                    fig_hist.add_trace(go.Scatter(
                        x=df_hist["DT_REFER"], y=df_hist[col],
                        name=label, line=dict(color=cor, width=2), mode="lines+markers"
                    ))
            fig_hist.add_hline(y=0, line_dash="dot", line_color="#94A3B8", line_width=1)
            fig_hist.update_layout(
                template="simple_white", height=320,
                margin=dict(t=20, b=20, l=0, r=0),
                legend=dict(orientation="h", y=-0.3, font=dict(size=10)),
                yaxis_title="Dias",
            )
            st.plotly_chart(fig_hist, use_container_width=True)
        else:
            st.info("Histórico multi-período não disponível neste escopo.")

    st.markdown("---")

    # ------------------------------------------------------------------
    # ROW 5 — Tabela-resumo
    # ------------------------------------------------------------------
    st.markdown("#### Tabela-Resumo de Atividade e Ciclos")
    resumo = pd.DataFrame({
        "Indicador": [
            "Giro de Estoques",
            "Giro Contas a Receber",
            "Giro Contas a Pagar",
            "Giro Ativo Circulante",
            "PMRE (dias)",
            "PMRV (dias)",
            "PMPC (dias)",
            "PMRAC (dias)",
            "Ciclo Econômico (dias)",
            "Ciclo Financeiro (dias)",
        ],
        "Fórmula": [
            "ABS(CPV) / Estoques",
            "Receita / CR",
            "ABS(CPV) / Fornecedores",
            "Receita / AC",
            "Estoques × 360 / ABS(CPV)",
            "CR × 360 / Receita",
            "Fornecedores × 360 / ABS(CPV)",
            "AC × 360 / Receita",
            "PMRE + PMRV",
            "PMRE + PMRV − PMPC",
        ],
        f"Empresa ({ano})": [
            _fmt(v_ge, 2, "x"), _fmt(v_gcr, 2, "x"),
            _fmt(v_gcp, 2, "x"), _fmt(v_gac, 2, "x"),
            _fmt(v_pmre, 1, " dias"), _fmt(v_pmrv, 1, " dias"),
            _fmt(v_pmpc, 1, " dias"), _fmt(v_pmrac, 1, " dias"),
            _fmt(v_ce, 1, " dias"), _fmt(v_cf, 1, " dias"),
        ],
        "Mediana Setor": [
            _fmt(med_ge, 2, "x"), _fmt(med_gcr, 2, "x"),
            _fmt(med_gcp, 2, "x"), _fmt(med_gac, 2, "x"),
            _fmt(med_pmre, 1, " dias"), _fmt(med_pmrv, 1, " dias"),
            _fmt(med_pmpc, 1, " dias"), _fmt(med_pmrac, 1, " dias"),
            _fmt(med_ce, 1, " dias"), _fmt(med_cf, 1, " dias"),
        ],
        "Melhor": [
            "⬆️ Maior", "⬆️ Maior", "⬇️ Menor", "⬆️ Maior",
            "⬇️ Menor", "⬇️ Menor", "⬆️ Maior", "⬇️ Menor",
            "⬇️ Menor", "⬇️ Menor",
        ],
    })
    st.dataframe(resumo, use_container_width=True, hide_index=True)

    st.caption(
        "**Premissa N2:** Empresas sem estoques (educação, turismo, bolsas) exibem PMRE/Giro Estoques/Ciclo Econômico "
        "como N/D — não como zero. | **Fonte:** `layer_03_gold.mart_indicadores_financeiros`"
    )

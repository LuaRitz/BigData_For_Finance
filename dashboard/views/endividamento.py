# views/endividamento.py
"""
Painel de Endividamento e Estrutura de Capital
Grupo 2 — PCT/CP, PCT/AT, Garantia CP/CT, Composição de Endividamento,
           Imobilização de Capital Próprio, Imobilização do Ativo Total
Fonte: layer_03_gold.mart_indicadores_financeiros
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px


# ==============================================================================
# HELPERS (duplicados localmente para isolamento de view)
# ==============================================================================

def _fmt(v, decimals=2, suffix=""):
    if pd.isna(v):
        return "N/D"
    return f"{v:,.{decimals}f}{suffix}"


def _kpi_card_end(title, empresa_val, suffix, benchmark_val, benchmark_label,
                   maior_melhor=True, reference_note=""):
    if pd.isna(empresa_val):
        cor_borda = "#94A3B8"
    elif maior_melhor:
        cor_borda = "#10B981" if empresa_val >= benchmark_val else "#EF4444"
    else:
        cor_borda = "#10B981" if empresa_val <= benchmark_val else "#EF4444"

    if not pd.isna(empresa_val) and not pd.isna(benchmark_val):
        if maior_melhor:
            status = "<span style='color:#10B981;font-weight:600;'>▲ Acima</span>" if empresa_val >= benchmark_val \
                else "<span style='color:#EF4444;font-weight:600;'>▼ Abaixo</span>"
        else:
            status = "<span style='color:#10B981;font-weight:600;'>▼ Melhor</span>" if empresa_val <= benchmark_val \
                else "<span style='color:#EF4444;font-weight:600;'>▲ Pior</span>"
    else:
        status = "<span style='color:#94A3B8;'>— S/D</span>"

    ref = f"<div style='font-size:10px;color:#94A3B8;margin-top:4px;'>{reference_note}</div>" if reference_note else ""
    st.markdown(
        f"""
        <div style='background:#fff;padding:18px;border-radius:6px;
                    box-shadow:0 1px 3px rgba(15,23,42,.06);
                    border-left:5px solid {cor_borda};margin-bottom:10px;'>
            <div style='color:#64748B;font-size:11px;font-weight:700;
                        text-transform:uppercase;letter-spacing:.8px;'>{title}</div>
            <div style='color:#0F172A;font-size:26px;font-weight:700;
                        margin:4px 0;letter-spacing:-.5px;'>{_fmt(empresa_val, suffix=suffix)}</div>
            <div style='font-size:12px;color:#475569;font-weight:500;'>
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

def render_endividamento_page(df_foco: pd.Series, df_concorrentes: pd.DataFrame,
                               nome_empresa: str, ano: str, escopo: str):
    """
    Renderiza o painel de Endividamento e Estrutura de Capital.
    """

    st.markdown(f"### 🏗️ Estrutura de Capital e Endividamento — {nome_empresa} ({ano})")
    st.caption(
        "Revela **de onde vêm os recursos** que financiam a empresa e o nível de dependência de terceiros. "
        f"Benchmark setorial: **{len(df_concorrentes)}** empresas ({escopo})"
    )
    st.markdown("---")

    # ------------------------------------------------------------------
    # Variáveis brutas (para decomposição)
    # ------------------------------------------------------------------
    v_pc   = df_foco.get("V10_PASSIVO_CIRC", np.nan)
    v_pnc  = df_foco.get("V11_PASSIVO_NCIRC", np.nan)
    v_pl   = df_foco.get("V12_PL", np.nan)
    v_at   = df_foco.get("V01_ATIVO_TOTAL", np.nan)
    v_anc  = df_foco.get("V03_ATIVO_NCIRC", np.nan)

    # Indicadores calculados
    v_pct_cp  = df_foco.get("IND_PCT_CP", np.nan)
    v_pct_at  = df_foco.get("IND_PCT_AT", np.nan)
    v_gar_ct  = df_foco.get("IND_GARANTIA_CT", np.nan)
    v_comp    = df_foco.get("IND_COMPOSICAO_ENDIV", np.nan)
    v_imob_cp = df_foco.get("IND_IMOB_CP", np.nan)
    v_imob_at = df_foco.get("IND_IMOB_AT", np.nan)

    # ------------------------------------------------------------------
    # Benchmarks
    # ------------------------------------------------------------------
    def med(col):
        s = df_concorrentes[col].replace([np.inf, -np.inf], np.nan).dropna()
        return s.median() if not s.empty else np.nan

    med_pct_cp  = med("IND_PCT_CP")
    med_pct_at  = med("IND_PCT_AT")
    med_gar_ct  = med("IND_GARANTIA_CT")
    med_comp    = med("IND_COMPOSICAO_ENDIV")
    med_imob_cp = med("IND_IMOB_CP")
    med_imob_at = med("IND_IMOB_AT")

    # ------------------------------------------------------------------
    # ROW 1 — Estrutura de Capital (visualização principal)
    # ------------------------------------------------------------------
    st.markdown("#### Composição do Passivo e Patrimônio")
    col_stack, col_waterfall = st.columns([1, 1])

    with col_stack:
        # Gráfico de barras empilhadas: PC / PNC / PL em % do AT
        if not any(pd.isna(x) for x in [v_pc, v_pnc, v_pl, v_at]) and v_at > 0:
            pct_pc  = v_pc  / v_at * 100
            pct_pnc = v_pnc / v_at * 100
            pct_pl  = v_pl  / v_at * 100

            fig_stack = go.Figure(data=[
                go.Bar(name="Passivo Circulante", x=["Estrutura Capital"], y=[pct_pc],
                       marker_color="#EF4444", text=[f"{pct_pc:.1f}%"], textposition="inside"),
                go.Bar(name="Passivo Não Circ.", x=["Estrutura Capital"], y=[pct_pnc],
                       marker_color="#F59E0B", text=[f"{pct_pnc:.1f}%"], textposition="inside"),
                go.Bar(name="Patrimônio Líquido", x=["Estrutura Capital"], y=[pct_pl],
                       marker_color="#10B981", text=[f"{pct_pl:.1f}%"], textposition="inside"),
            ])
            fig_stack.update_layout(
                barmode="stack", template="simple_white", height=300,
                margin=dict(t=30, b=10, l=0, r=0),
                legend=dict(orientation="h", y=-0.2, font=dict(size=10)),
                yaxis_title="% do Ativo Total",
                title="Estrutura de Financiamento (% AT)",
            )
            st.plotly_chart(fig_stack, use_container_width=True)
        else:
            st.info("Dados insuficientes para gráfico de estrutura de capital.")

    with col_waterfall:
        # Decomposição do Ativo: Circulante vs Não Circulante
        v_ac = df_foco.get("V02_ATIVO_CIRC", 0) or 0
        v_anc_val = df_foco.get("V03_ATIVO_NCIRC", 0) or 0
        if v_ac + v_anc_val > 0:
            fig_ativo = go.Figure(go.Pie(
                labels=["Ativo Circulante", "Ativo Não Circulante"],
                values=[v_ac, v_anc_val],
                hole=0.42,
                marker=dict(colors=["#1E293B", "#82E8E1"]),
                textfont=dict(size=11),
            ))
            fig_ativo.update_layout(
                title="Composição do Ativo Total",
                height=300, margin=dict(t=40, b=10, l=0, r=0),
                legend=dict(orientation="h", y=-0.1, font=dict(size=10)),
            )
            st.plotly_chart(fig_ativo, use_container_width=True)
        else:
            st.info("Dados do Ativo não disponíveis.")

    st.markdown("---")

    # ------------------------------------------------------------------
    # ROW 2 — KPI Cards (6 indicadores)
    # ------------------------------------------------------------------
    st.markdown("#### Indicadores de Endividamento e Imobilização")
    c1, c2, c3 = st.columns(3)
    c4, c5, c6 = st.columns(3)

    with c1:
        _kpi_card_end("PCT / Capital Próprio", v_pct_cp, "x", med_pct_cp, "Mediana setor",
                      maior_melhor=False, reference_note="⬇️ Quanto menor, menos endividado")
    with c2:
        _kpi_card_end("PCT / Ativo Total", v_pct_at * 100 if not pd.isna(v_pct_at) else np.nan,
                      "%", med_pct_at * 100 if not pd.isna(med_pct_at) else np.nan, "Mediana setor",
                      maior_melhor=False, reference_note="⚠️ Acima de 70% = alerta")
    with c3:
        _kpi_card_end("Garantia CP / CT", v_gar_ct, "x", med_gar_ct, "Mediana setor",
                      maior_melhor=True, reference_note="⬆️ Quanto maior, mais segurança p/ credores")
    with c4:
        _kpi_card_end("Composição Endividamento", v_comp * 100 if not pd.isna(v_comp) else np.nan,
                      "%", med_comp * 100 if not pd.isna(med_comp) else np.nan, "Mediana setor",
                      maior_melhor=False, reference_note="⚠️ Acima de 60% CP = risco de liquidez")
    with c5:
        _kpi_card_end("Imobilização Capital Próprio",
                      v_imob_cp * 100 if not pd.isna(v_imob_cp) else np.nan,
                      "%", med_imob_cp * 100 if not pd.isna(med_imob_cp) else np.nan, "Mediana setor",
                      maior_melhor=False, reference_note="✅ Satisfatório abaixo de 100%")
    with c6:
        _kpi_card_end("Imobilização Ativo Total",
                      v_imob_at * 100 if not pd.isna(v_imob_at) else np.nan,
                      "%", med_imob_at * 100 if not pd.isna(med_imob_at) else np.nan, "Mediana setor",
                      maior_melhor=False, reference_note="ℹ️ Depende do setor (ref. ~50%)")

    st.markdown("---")

    # ------------------------------------------------------------------
    # ROW 3 — Perfil da Dívida + Evolução histórica
    # ------------------------------------------------------------------
    col_radar, col_hist = st.columns([1, 1])

    with col_radar:
        st.markdown("#### Perfil de Risco Comparativo (Radar)")
        # Normaliza indicadores para 0-1 para radar
        cols_radar = {
            "PCT/CP (inv.)": ("IND_PCT_CP", False),
            "PCT/AT (inv.)": ("IND_PCT_AT", False),
            "Garantia CT": ("IND_GARANTIA_CT", True),
            "Comp. Endiv. (inv.)": ("IND_COMPOSICAO_ENDIV", False),
            "Imob. CP (inv.)": ("IND_IMOB_CP", False),
        }
        labels_r = list(cols_radar.keys())
        
        def norm_score(val, col, maior_melhor, pctil_min, pctil_max):
            """Score 0-1 baseado nos percentis do setor."""
            if pd.isna(val):
                return 0.0
            rng = pctil_max - pctil_min
            if rng == 0:
                return 0.5
            score = (val - pctil_min) / rng
            score = max(0.0, min(1.0, score))
            return score if maior_melhor else 1.0 - score

        scores_empresa = []
        scores_mediana = []
        for label, (col, mb) in cols_radar.items():
            serie = df_concorrentes[col].replace([np.inf, -np.inf], np.nan).dropna()
            p5  = serie.quantile(0.05) if not serie.empty else 0
            p95 = serie.quantile(0.95) if not serie.empty else 1
            scores_empresa.append(norm_score(df_foco.get(col, np.nan), col, mb, p5, p95))
            scores_mediana.append(norm_score(serie.median() if not serie.empty else np.nan, col, mb, p5, p95))

        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=scores_empresa + [scores_empresa[0]],
            theta=labels_r + [labels_r[0]],
            fill="toself", fillcolor="rgba(155,43,199,0.15)",
            line=dict(color="#9B2BC7", width=2),
            name=nome_empresa
        ))
        fig_radar.add_trace(go.Scatterpolar(
            r=scores_mediana + [scores_mediana[0]],
            theta=labels_r + [labels_r[0]],
            fill="toself", fillcolor="rgba(30,41,59,0.08)",
            line=dict(color="#1E293B", width=1.5, dash="dash"),
            name="Mediana Setor"
        ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 1], tickfont=dict(size=8))),
            showlegend=True, height=320,
            margin=dict(t=20, b=20, l=30, r=30),
            legend=dict(font=dict(size=10)),
        )
        st.plotly_chart(fig_radar, use_container_width=True)
        st.caption("Score 0–1 normalizado pelo P5–P95 do setor. Maior = melhor posição relativa.")

    with col_hist:
        st.markdown("#### Evolução Histórica do Endividamento")
        cnpj = df_foco.get("CNPJ_CIA", None)
        if cnpj is not None and not df_concorrentes.empty and "CNPJ_CIA" in df_concorrentes.columns:
            df_hist = df_concorrentes[df_concorrentes["CNPJ_CIA"] == cnpj].sort_values("DT_REFER")
        else:
            df_hist = pd.DataFrame()

        if not df_hist.empty and "DT_REFER" in df_hist.columns:
            fig_hist = go.Figure()
            series_hist = [
                ("PCT/CP", "IND_PCT_CP", "#EF4444"),
                ("Garantia CT", "IND_GARANTIA_CT", "#10B981"),
                ("Comp. Endiv.", "IND_COMPOSICAO_ENDIV", "#F59E0B"),
            ]
            for label, col, cor in series_hist:
                if col in df_hist.columns:
                    fig_hist.add_trace(go.Scatter(
                        x=df_hist["DT_REFER"], y=df_hist[col],
                        name=label, line=dict(color=cor, width=2), mode="lines+markers"
                    ))
            fig_hist.update_layout(
                template="simple_white", height=320,
                margin=dict(t=20, b=20, l=0, r=0),
                legend=dict(orientation="h", y=-0.25, font=dict(size=10)),
                yaxis_title="Índice / Razão",
            )
            st.plotly_chart(fig_hist, use_container_width=True)
        else:
            st.info("Histórico multi-período não disponível neste escopo de filtro.")

    st.markdown("---")

    # ------------------------------------------------------------------
    # ROW 4 — Diagnóstico qualitativo
    # ------------------------------------------------------------------
    st.markdown("#### Diagnóstico de Estrutura de Capital")
    d1, d2 = st.columns(2)

    with d1:
        # Endividamento geral
        pct_at_pct = v_pct_at * 100 if not pd.isna(v_pct_at) else np.nan
        if not pd.isna(pct_at_pct):
            if pct_at_pct <= 40:
                st.success(f"**Endividamento Total ({_fmt(pct_at_pct)}% AT):** 🟢 Estrutura conservadora — "
                           "baixa dependência de capital de terceiros.")
            elif pct_at_pct <= 70:
                st.info(f"**Endividamento Total ({_fmt(pct_at_pct)}% AT):** 🔵 Alavancagem moderada — "
                        "compatível com a maioria dos setores.")
            else:
                st.error(f"**Endividamento Total ({_fmt(pct_at_pct)}% AT):** 🔴 Alavancagem elevada — "
                         "risco de insolvência em cenários de estresse.")

        comp_pct = v_comp * 100 if not pd.isna(v_comp) else np.nan
        if not pd.isna(comp_pct):
            if comp_pct <= 40:
                st.success(f"**Perfil da Dívida ({_fmt(comp_pct)}% CP):** Dívida concentrada no longo prazo — "
                           "menor pressão de caixa imediata.")
            elif comp_pct <= 60:
                st.warning(f"**Perfil da Dívida ({_fmt(comp_pct)}% CP):** Perfil equilibrado — atenção ao "
                           "refinanciamento das parcelas de curto prazo.")
            else:
                st.error(f"**Perfil da Dívida ({_fmt(comp_pct)}% CP):** Alta concentração no CP — "
                         "empresa sob pressão de liquidez imediata.")

    with d2:
        imob_cp_pct = v_imob_cp * 100 if not pd.isna(v_imob_cp) else np.nan
        if not pd.isna(imob_cp_pct):
            if imob_cp_pct < 100:
                st.success(f"**Imobilização CP ({_fmt(imob_cp_pct)}%):** PL cobre todo o ANC e ainda "
                           "sobra capital para o giro operacional. ✅")
            else:
                st.error(f"**Imobilização CP ({_fmt(imob_cp_pct)}%):** PL insuficiente para cobrir o ANC — "
                         "empresa financia ativo permanente com dívida de terceiros. 🚨")

        if not pd.isna(v_gar_ct):
            if v_gar_ct >= 1.0:
                st.success(f"**Garantia CP/CT ({_fmt(v_gar_ct)}x):** Patrimônio cobre toda a dívida com terceiros.")
            else:
                st.warning(f"**Garantia CP/CT ({_fmt(v_gar_ct)}x):** Capital próprio insuficiente para cobrir "
                           "100% da dívida. Credores estão expostos a risco.")

    st.markdown("---")

    # ------------------------------------------------------------------
    # ROW 5 — Tabela-resumo
    # ------------------------------------------------------------------
    st.markdown("#### Tabela-Resumo dos Indicadores de Endividamento")
    resumo = pd.DataFrame({
        "Indicador": [
            "PCT / Capital Próprio",
            "PCT / Ativo Total",
            "Garantia CP / CT",
            "Composição Endividamento",
            "Imobilização Capital Próprio",
            "Imobilização Ativo Total",
        ],
        "Fórmula": [
            "(PC + ELP) / PL",
            "(PC + ELP) / AT",
            "PL / (PC + ELP)",
            "PC / (PC + ELP)",
            "ANC / PL",
            "ANC / AT",
        ],
        f"Empresa ({ano})": [
            _fmt(v_pct_cp, suffix="x"),
            _fmt(v_pct_at * 100 if not pd.isna(v_pct_at) else np.nan, suffix="%"),
            _fmt(v_gar_ct, suffix="x"),
            _fmt(v_comp * 100 if not pd.isna(v_comp) else np.nan, suffix="%"),
            _fmt(v_imob_cp * 100 if not pd.isna(v_imob_cp) else np.nan, suffix="%"),
            _fmt(v_imob_at * 100 if not pd.isna(v_imob_at) else np.nan, suffix="%"),
        ],
        "Mediana Setor": [
            _fmt(med_pct_cp, suffix="x"),
            _fmt(med_pct_at * 100 if not pd.isna(med_pct_at) else np.nan, suffix="%"),
            _fmt(med_gar_ct, suffix="x"),
            _fmt(med_comp * 100 if not pd.isna(med_comp) else np.nan, suffix="%"),
            _fmt(med_imob_cp * 100 if not pd.isna(med_imob_cp) else np.nan, suffix="%"),
            _fmt(med_imob_at * 100 if not pd.isna(med_imob_at) else np.nan, suffix="%"),
        ],
        "Referência": [
            "Menor = melhor",
            "< 70%",
            "Maior = melhor",
            "< 60% (CP)",
            "< 100%",
            "~50% (setor-dependente)",
        ],
    })
    st.dataframe(resumo, use_container_width=True, hide_index=True)

    st.caption(
        "**Fonte:** `layer_03_gold.mart_indicadores_financeiros` | "
        "**Contas:** V01 (AT), V10 (PC), V11 (PNC), V12 (PL), V03 (ANC)"
    )

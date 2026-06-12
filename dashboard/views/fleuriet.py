# views/fleuriet.py
"""
Painel do Modelo Fleuriet — Recursos Financeiros
Grupo 7 — CGL/CCL, NCG, Saldo de Tesouraria, Efeito Tesoura
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

def _fmt_brl(v):
    """Formata como valor monetário BRL."""
    if pd.isna(v):
        return "N/D"
    sinal = "-" if v < 0 else ""
    return f"{sinal}R$ {abs(v):,.0f}"


def _fmt(v, decimals=2, suffix=""):
    if pd.isna(v):
        return "N/D"
    return f"{v:,.{decimals}f}{suffix}"


def _valor_card(title, valor, positivo_bom=True, sub_label="", icon=""):
    """Card colorido baseado no sinal do valor."""
    if pd.isna(valor):
        cor = "#94A3B8"
        borda = "#94A3B8"
        signal_label = "— Dado não disponível"
    elif valor >= 0 and positivo_bom:
        cor = "#10B981"
        borda = "#10B981"
        signal_label = "🟢 Positivo — situação favorável"
    elif valor < 0 and not positivo_bom:
        cor = "#10B981"
        borda = "#10B981"
        signal_label = "🟢 Negativo — situação favorável"
    elif valor >= 0 and not positivo_bom:
        cor = "#F59E0B"
        borda = "#F59E0B"
        signal_label = "🟡 Positivo — empresa precisa de capital externo"
    else:
        cor = "#EF4444"
        borda = "#EF4444"
        signal_label = "🔴 Negativo — alerta de liquidez"

    sub = f"<div style='font-size:11px;color:#64748B;margin-top:2px;'>{sub_label}</div>" if sub_label else ""
    st.markdown(
        f"""
        <div style='background:#fff;padding:20px;border-radius:8px;
                    box-shadow:0 1px 4px rgba(15,23,42,.07);
                    border-left:6px solid {borda};margin-bottom:12px;'>
            <div style='color:#64748B;font-size:11px;font-weight:700;
                        text-transform:uppercase;letter-spacing:.8px;'>{icon} {title}</div>
            <div style='color:{cor};font-size:26px;font-weight:700;margin:8px 0;'>
                {_fmt_brl(valor)}
            </div>
            <div style='font-size:12px;color:#475569;'>{signal_label}</div>
            {sub}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ==============================================================================
# RENDER PRINCIPAL
# ==============================================================================

def render_fleuriet_page(df_foco: pd.Series, df_concorrentes: pd.DataFrame,
                          df_master_empresa: pd.DataFrame,
                          nome_empresa: str, ano: str, escopo: str):
    """
    Renderiza o painel do Modelo Fleuriet.

    Parameters
    ----------
    df_master_empresa : pd.DataFrame — todos os períodos da empresa selecionada
                        (necessário para o Efeito Tesoura).
    """

    st.markdown(f"### 🏦 Modelo Fleuriet — Recursos Financeiros — {nome_empresa} ({ano})")
    st.caption(
        "Analisa a **saúde do fluxo de caixa operacional** e detecta o **Efeito Tesoura** — "
        "sinal de deterioração financeira progressiva. "
        f"Benchmark: **{len(df_concorrentes)}** empresas ({escopo})"
    )
    st.markdown("---")

    # ------------------------------------------------------------------
    # Variáveis
    # ------------------------------------------------------------------
    v_cgl = df_foco.get("IND_CGL", np.nan)
    v_ncg = df_foco.get("IND_NCG", np.nan)
    v_st  = df_foco.get("IND_ST", np.nan)

    # Componentes auxiliares para decomposição
    v_ac   = df_foco.get("V02_ATIVO_CIRC", np.nan)
    v_pc   = df_foco.get("V10_PASSIVO_CIRC", np.nan)
    v_acf  = df_foco.get("AUX_ACF", np.nan)             # Ativo Circ. Financeiro
    v_emp_cp = df_foco.get("V13_EMP_CP", np.nan)        # PCF proxy
    v_cr   = df_foco.get("V07_CONTAS_RECEBER", np.nan)
    v_estq = df_foco.get("V06_ESTOQUES", np.nan) or 0
    v_forn = df_foco.get("V09_FORNECEDORES", np.nan)

    def med(col):
        s = df_concorrentes[col].replace([np.inf, -np.inf], np.nan).dropna()
        return s.median() if not s.empty else np.nan

    med_cgl = med("IND_CGL")
    med_ncg = med("IND_NCG")
    med_st  = med("IND_ST")

    # ------------------------------------------------------------------
    # ROW 1 — Os três valores-chave do Fleuriet
    # ------------------------------------------------------------------
    st.markdown("#### Os Três Pilares do Modelo Fleuriet")
    c1, c2, c3 = st.columns(3)

    with c1:
        _valor_card(
            "Capital de Giro Líquido (CGL)",
            v_cgl, positivo_bom=True,
            sub_label=f"Fórmula: AC − PC | Med. setor: {_fmt_brl(med_cgl)}",
            icon="💼"
        )
    with c2:
        _valor_card(
            "Necessidade de Capital de Giro (NCG)",
            v_ncg, positivo_bom=False,  # NCG negativo = melhor (fornecedores financiam a empresa)
            sub_label=f"ACO − PCO | Med. setor: {_fmt_brl(med_ncg)}",
            icon="⚡"
        )
    with c3:
        _valor_card(
            "Saldo de Tesouraria (ST)",
            v_st, positivo_bom=True,
            sub_label=f"ACF − PCF | Med. setor: {_fmt_brl(med_st)}",
            icon="💰"
        )

    # Identidade CGL = NCG + ST
    if not any(pd.isna(x) for x in [v_cgl, v_ncg, v_st]):
        st.info(
            f"**Identidade Fleuriet:** CGL = NCG + ST → "
            f"{_fmt_brl(v_cgl)} = {_fmt_brl(v_ncg)} + {_fmt_brl(v_st)} "
            f"(diferença: {_fmt_brl(v_cgl - (v_ncg + v_st))})"
        )

    st.markdown("---")

    # ------------------------------------------------------------------
    # ROW 2 — Diagnóstico do Tipo de Empresa (Fleuriet)
    # ------------------------------------------------------------------
    st.markdown("#### Classificação Fleuriet")

    tipo_fleuriet = None
    if not any(pd.isna(x) for x in [v_cgl, v_ncg, v_st]):
        if v_cgl > 0 and v_ncg < 0 and v_st > 0:
            tipo_fleuriet = ("Tipo I — Excelente (🏆)", "#10B981",
                             "CGL > 0 | NCG < 0 | ST > 0 — Rara e poderosa: "
                             "operação autofinanciada e com sobra de tesouraria. "
                             "Comum em grandes varejistas (Mercadão).")
        elif v_cgl > 0 and v_ncg > 0 and v_st > 0:
            tipo_fleuriet = ("Tipo II — Sólido (✅)", "#82E8E1",
                             "CGL > 0 | NCG > 0 | ST > 0 — Situação confortável: "
                             "capital de longo prazo cobre a NCG e sobra para a tesouraria.")
        elif v_cgl > 0 and v_ncg > 0 and v_st < 0:
            tipo_fleuriet = ("Tipo III — Insatisfatório (⚠️)", "#F59E0B",
                             "CGL > 0 | NCG > 0 | ST < 0 — Empresa usa empréstimos de curto prazo "
                             "para financiar a NCG. Se o ST piorar progressivamente = Efeito Tesoura.")
        elif v_cgl < 0 and v_ncg < 0 and v_st > 0:
            tipo_fleuriet = ("Tipo IV — Alto Risco (🔴)", "#EF4444",
                             "CGL < 0 | NCG < 0 | ST > 0 — Empresa financia ativos fixos com "
                             "recursos de curto prazo. Situação de risco estrutural.")
        elif v_cgl < 0 and v_ncg > 0 and v_st < 0:
            tipo_fleuriet = ("Tipo V — Péssimo (🚨)", "#DC2626",
                             "CGL < 0 | NCG > 0 | ST < 0 — Empresa em desequilíbrio total. "
                             "Capital de giro negativo e dívidas de curto prazo crescentes.")
        elif v_cgl < 0 and v_ncg < 0 and v_st < 0:
            tipo_fleuriet = ("Tipo VI — Super Alto Risco (💀)", "#7F1D1D",
                             "CGL < 0 | NCG < 0 | ST < 0 — Situação extrema: fontes de curto prazo "
                             "financiam o ativo permanente. Insolvência iminente se não revertido.")
        else:
            tipo_fleuriet = ("Tipo Atípico (ℹ️)", "#94A3B8",
                             "Combinação não padrão — análise individual recomendada.")

    if tipo_fleuriet:
        label, cor, descr = tipo_fleuriet
        st.markdown(
            f"""
            <div style='background:{cor}18;border:2px solid {cor};border-radius:8px;
                        padding:20px;margin-bottom:16px;'>
                <div style='font-size:18px;font-weight:700;color:{cor};'>{label}</div>
                <div style='color:#1E293B;margin-top:8px;font-size:14px;'>{descr}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.warning("Dados insuficientes para classificar o tipo Fleuriet.")

    st.markdown("---")

    # ------------------------------------------------------------------
    # ROW 3 — Efeito Tesoura (Série Histórica do ST)
    # ------------------------------------------------------------------
    st.markdown("#### Monitoramento do Efeito Tesoura")
    st.caption(
        "O **Efeito Tesoura** ocorre quando o Saldo de Tesouraria se torna progressivamente mais negativo "
        "enquanto a NCG cresce — sinal de insolvência crescente por expansão desordenada."
    )

    if not df_master_empresa.empty and "DT_REFER" in df_master_empresa.columns:
        df_hist = df_master_empresa.sort_values("DT_REFER").copy()

        fig_tesoura = go.Figure()

        # ST histórico
        if "IND_ST" in df_hist.columns:
            fig_tesoura.add_trace(go.Scatter(
                x=df_hist["DT_REFER"], y=df_hist["IND_ST"],
                name="Saldo Tesouraria (ST)", mode="lines+markers",
                line=dict(color="#9B2BC7", width=2.5),
                fill="tozeroy",
                fillcolor="rgba(155,43,199,0.08)",
            ))

        # NCG histórico
        if "IND_NCG" in df_hist.columns:
            fig_tesoura.add_trace(go.Scatter(
                x=df_hist["DT_REFER"], y=df_hist["IND_NCG"],
                name="NCG", mode="lines+markers",
                line=dict(color="#EF4444", width=2, dash="dot"),
            ))

        # CGL histórico
        if "IND_CGL" in df_hist.columns:
            fig_tesoura.add_trace(go.Scatter(
                x=df_hist["DT_REFER"], y=df_hist["IND_CGL"],
                name="CGL", mode="lines+markers",
                line=dict(color="#10B981", width=2),
            ))

        # Linha zero
        fig_tesoura.add_hline(y=0, line_dash="dash", line_color="#94A3B8", line_width=1.5,
                               annotation_text="Zero", annotation_position="right")

        fig_tesoura.update_layout(
            template="simple_white", height=340,
            margin=dict(t=20, b=20, l=0, r=0),
            legend=dict(orientation="h", y=-0.25, font=dict(size=10)),
            yaxis_title="R$",
            title=f"Evolução CGL | NCG | ST — {nome_empresa}",
        )
        st.plotly_chart(fig_tesoura, use_container_width=True)

        # Detecção automática do Efeito Tesoura
        if "IND_ST" in df_hist.columns and len(df_hist) >= 3:
            st_serie = df_hist["IND_ST"].dropna().values
            if len(st_serie) >= 3:
                # Verifica tendência de piora nos últimos 3+ períodos
                tendencia_piora = all(st_serie[i] < st_serie[i-1] for i in range(-1, -min(4, len(st_serie)), -1))
                todos_negativos = all(x < 0 for x in st_serie[-3:]) if len(st_serie) >= 3 else False

                if todos_negativos and tendencia_piora:
                    st.error(
                        "🚨 **EFEITO TESOURA DETECTADO:** O Saldo de Tesouraria está negativo e "
                        "piorando progressivamente nos últimos períodos. A empresa está se afastando "
                        "do equilíbrio financeiro — risco crescente de insolvência."
                    )
                elif todos_negativos:
                    st.warning(
                        "⚠️ **Atenção:** Saldo de Tesouraria negativo nos últimos 3 períodos. "
                        "Monitorar tendência — se continuar deteriorando, configura Efeito Tesoura."
                    )
                elif not pd.isna(v_st) and v_st < 0:
                    st.info("ℹ️ ST negativo no período atual. Análise histórica necessária para confirmar tendência.")
    else:
        st.info("Dados históricos não disponíveis para análise do Efeito Tesoura.")

    st.markdown("---")

    # ------------------------------------------------------------------
    # ROW 4 — Decomposição visual: AC e PC operacional vs financeiro
    # ------------------------------------------------------------------
    st.markdown("#### Decomposição Circulante: Operacional × Financeiro")
    col_ativo, col_passivo = st.columns(2)

    with col_ativo:
        st.markdown("**Ativo Circulante**")
        v_caixa_bp = df_foco.get("V22_CAIXA_BP", 0) or 0
        v_aplic    = df_foco.get("V15B_APLIC_FIN", 0) or 0
        aco_cr     = df_foco.get("V07_CONTAS_RECEBER", 0) or 0
        aco_estq   = v_estq
        outros_ac  = max(0, (df_foco.get("V02_ATIVO_CIRC", 0) or 0)
                         - v_caixa_bp - v_aplic - aco_cr - aco_estq)

        labels_ac = ["Caixa (ACF)", "Aplic. Fin. (ACF)", "CR (ACO)", "Estoques (ACO)", "Outros"]
        vals_ac   = [v_caixa_bp, v_aplic, aco_cr, aco_estq, outros_ac]
        colors_ac = ["#1E293B", "#475569", "#9B2BC7", "#E0D449", "#CBD5E1"]
        filtered  = [(l, v, c) for l, v, c in zip(labels_ac, vals_ac, colors_ac) if v > 0]

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

    with col_passivo:
        st.markdown("**Passivo Circulante**")
        pco_forn   = df_foco.get("V09_FORNECEDORES", 0) or 0
        pcf_emp    = df_foco.get("V13_EMP_CP", 0) or 0
        outros_pc  = max(0, (df_foco.get("V10_PASSIVO_CIRC", 0) or 0) - pco_forn - pcf_emp)

        labels_pc = ["Fornecedores (PCO)", "Emp. CP (PCF)", "Outros PC"]
        vals_pc   = [pco_forn, pcf_emp, outros_pc]
        colors_pc = ["#10B981", "#EF4444", "#CBD5E1"]
        filtered_pc = [(l, v, c) for l, v, c in zip(labels_pc, vals_pc, colors_pc) if v > 0]

        if filtered_pc:
            fl, fv, fc = zip(*filtered_pc)
            fig_pc = go.Figure(go.Bar(
                x=fl, y=fv,
                marker_color=fc,
                text=[f"R$ {v:,.0f}" for v in fv],
                textposition='auto',
            ))
            fig_pc.update_layout(
                height=300, 
                margin=dict(t=10, b=10, l=0, r=0),
                template="simple_white",
                yaxis_title="Valor (R$)"
            )
            st.plotly_chart(fig_pc, use_container_width=True)

    st.markdown("---")

    # ------------------------------------------------------------------
    # ROW 5 — Benchmark setorial (boxplot)
    # ------------------------------------------------------------------
    st.markdown("#### Posição Setorial (CGL, NCG, ST)")
    with st.expander("Como ler um boxplot?"):
        st.markdown("A linha central é a mediana, o retângulo mostra o 1º e 3º quartis, e os 'bigodes' indicam a variação dentro de 1.5x o IQR. Para mais informações, consulte o seguinte blog: [Como interpretar boxplots](https://fernandafperes.com.br/blog/interpretacao-boxplot/).")    
    cols_bx = {"CGL": "IND_CGL", "NCG": "IND_NCG", "ST": "IND_ST"}
    df_melt = df_concorrentes.melt(
        id_vars=["RAZAO_SOCIAL"],
        value_vars=list(cols_bx.values()),
        var_name="Indicador", value_name="Valor"
    ).replace([np.inf, -np.inf], np.nan).dropna(subset=["Valor"])
    df_melt["Indicador"] = df_melt["Indicador"].map({v: k for k, v in cols_bx.items()})

    fig_bx = px.box(df_melt, x="Indicador", y="Valor",
                    color_discrete_sequence=["#475569"], points=False)
    for label, col in cols_bx.items():
        val = df_foco.get(col, np.nan)
        if not pd.isna(val):
            fig_bx.add_trace(go.Scatter(
                x=[label], y=[val], mode="markers",
                marker=dict(color="#9B2BC7", size=12, symbol="diamond",
                            line=dict(color="white", width=1.5)),
                name=nome_empresa,
                showlegend=(label == "CGL")
            ))
    fig_bx.add_hline(y=0, line_dash="dot", line_color="#94A3B8")
    fig_bx.update_layout(
        template="simple_white", height=280,
        margin=dict(t=10, b=10, l=0, r=0),
        yaxis_title="R$",
        legend=dict(font=dict(size=10)),
    )
    st.plotly_chart(fig_bx, use_container_width=True)

    st.markdown("---")

    # ------------------------------------------------------------------
    # ROW 6 — Tabela-resumo
    # ------------------------------------------------------------------
    st.markdown("#### Tabela-Resumo do Modelo Fleuriet")
    resumo = pd.DataFrame({
        "Indicador": ["Capital de Giro Líquido (CGL)", "NCG (Nec. Cap. Giro)", "Saldo de Tesouraria (ST)"],
        "Fórmula": ["AC − PC", "ACO − PCO", "ACF − PCF"],
        "Contas": [
            "V02 − V10",
            "(V06+V07) − (V09+Obrig.Fisc.)",
            "(V22+V15B) − V13",
        ],
        f"Empresa ({ano})": [_fmt_brl(v_cgl), _fmt_brl(v_ncg), _fmt_brl(v_st)],
        "Mediana Setor": [_fmt_brl(med_cgl), _fmt_brl(med_ncg), _fmt_brl(med_st)],
        "Positivo = ": ["Melhor ✅", "Empresa financia NCG ⚠️", "Melhor ✅"],
    })
    st.dataframe(resumo, use_container_width=True, hide_index=True)

    st.caption(
        "**Premissa N1:** ACF usa `1.01.01` (BP) + `1.01.02` — nunca `6.05.02` (DFC). "
        "PCF = `2.01.04` (Empréstimos CP). | **Fonte:** `layer_03_gold.mart_indicadores_financeiros`"
    )

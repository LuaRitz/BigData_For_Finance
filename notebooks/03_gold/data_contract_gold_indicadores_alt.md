# 🥇 Data Contract | Camada Gold: Indicadores Financeiros 📊
**Squad:** Big Data for Finance 

**Data:** 22 de Maio de 2026 

**Base de Dados:** PostgreSQL (`layer_03_gold`) 

**Tabela Final:** `mart_indicadores_financeiros` 

**Responsável:** Prof. Ivan Mello 

---

## Bloco 1: Notas Gerais Obrigatórias

### N1. Engenharia Reversa e Prefixos de Coluna
Para garantir total rastreabilidade (linhagem) e auditoria, cada coluna do mart na camada Gold possui um prefixo identificando sua origem:
* **`V__`**: Variável de input (mapeamento direto a um `CD_CONTA` da Silver).
* **`AUX__`**: Variável auxiliar (combinação de variáveis `V`, que preparam o terreno mas não possuem interpretação financeira direta).
* **`IND__`**: Indicador financeiro final (fórmula calculada e pronta para análise).

### N2. Divisão Segura (`safe_div`)
Todas as fórmulas de indicadores evitam erros de matemática do Python. A função `safe_div` foi implementada no pipeline para garantir que qualquer divisão por zero (0) ou nulo resulte em `NaN`, evitando a interrupção do processamento (*ZeroDivisionError*) e distorções por valores infinitos.

### N3. Caixa para Indicadores: BP vs DFC
| Indicador | Conta correta | Conta incorreta | Motivo |
|---|---|---|---|
| Liquidez Imediata, ACF Fleuriet | `1.01.01` (BP) | `6.05.02` (DFC) | O ratio de liquidez imediata é um indicador de posição (fotografia), logo deve usar o BP. |
| Dívida Líquida, EV e FCF Yield | `6.05.02` (DFC) | `1.01.01` (BP) | A DFC reflete com mais precisão os equivalentes de caixa de altíssima liquidez (CPC 03), essenciais para o endividamento real. |

### N4. Ausência de Estoques (Regra de Negócio)
Empresas de serviços puros (Educação, Turismo, B3) não reportam a conta de Estoques (`1.01.04`). O pipeline aplica um `COALESCE(estoques, 0)` na extração para essas empresas para evitar nulos em contas estruturais. Porém, para indicadores como "Giro de Estoques" ou "Ciclo Econômico", a tabela deverá exibir "N/A" para não distorcer a análise setorial.

### N5. Granularidade
A tabela `mart_indicadores_financeiros` possui a garantia de **uma linha única** por `CNPJ_CIA` (Empresa) e `DT_REFER` (Período). Os dados são deduplicados na extração preferindo a *FLAG_RECONSTRUCAO = False* (dados originais auditados) frente aos dados reconstruídos.

---

## Bloco 2: Fichas de Variáveis de Input (Origem: BP/DFC/DRE)

### 📊 Variáveis do Balanço Patrimonial (BP)

### V01 | Ativo Total
| Propriedade | Definição |
| :--- | :--- |
| **CD_CONTA** | `1` |
| **DS_CONTA** | ATIVO TOTAL |
| **Tabela Silver** | `n1_dfp_cia_aberta_bp` |
| **ST_CONTA_FIXA** | `S` |
| **Cobertura no setor** | 100% |
| **COALESCE?** | Não. Se nulo, a linha da empresa deve ir para rejeito. |
| **Usado em** | ROA, ROI, PCT/AT, Liquidez Geral, Imobilização do Ativo Total |

### V02 | Ativo Circulante
| Propriedade | Definição |
| :--- | :--- |
| **CD_CONTA** | `1.01` |
| **DS_CONTA** | ATIVO CIRCULANTE |
| **Tabela Silver** | `n1_dfp_cia_aberta_bp` |
| **ST_CONTA_FIXA** | `S` |
| **Cobertura no setor** | 100% |
| **COALESCE?** | Não aplicável. |
| **Usado em** | Liquidez Geral, Liquidez Corrente, Liquidez Seca, CCL, ACF (Fleuriet) |

### V04 | Realizável a Longo Prazo
| Propriedade | Definição |
| :--- | :--- |
| **CD_CONTA** | `1.02.01` |
| **DS_CONTA** | ATIVO REALIZÁVEL A LONGO PRAZO |
| **Tabela Silver** | `n1_dfp_cia_aberta_bp` |
| **ST_CONTA_FIXA** | `S` |
| **COALESCE?** | Sim, `COALESCE(valor, 0)`. |
| **Usado em** | Liquidez Geral |

### V05 | Ativo Não Circulante
| Propriedade | Definição |
| :--- | :--- |
| **CD_CONTA** | `1.02` |
| **DS_CONTA** | ATIVO NÃO CIRCULANTE |
| **Tabela Silver** | `n1_dfp_cia_aberta_bp` |
| **ST_CONTA_FIXA** | `S` |
| **COALESCE?** | Não esperado. |
| **Usado em** | Imobilização do Capital Próprio, Imobilização do Ativo Total |

### V06 | Estoques
| Propriedade | Definição |
| :--- | :--- |
| **CD_CONTA** | `1.01.04` |
| **DS_CONTA** | ESTOQUES |
| **Tabela Silver** | `n1_dfp_cia_aberta_bp` |
| **ST_CONTA_FIXA** | `N` |
| **Cobertura no setor** | ~89.2% (100% em indústrias, ausente em serviços puros) |
| **COALESCE?** | Sim, `COALESCE(valor, 0)` é aplicado pós-extração. |
| **Usado em** | Liquidez Seca, ACO (Fleuriet) |

### V10 | Passivo Circulante
| Propriedade | Definição |
| :--- | :--- |
| **CD_CONTA** | `2.01` |
| **DS_CONTA** | PASSIVO CIRCULANTE |
| **Tabela Silver** | `n1_dfp_cia_aberta_bp` |
| **ST_CONTA_FIXA** | `S` |
| **Cobertura no setor** | 100% |
| **COALESCE?** | Não permitido. |
| **Usado em** | Liquidez (Geral, Corrente, Seca, Imediata), PCT, PCF/PCO (Fleuriet) |

### V11 | Passivo Não Circulante
| Propriedade | Definição |
| :--- | :--- |
| **CD_CONTA** | `2.02` |
| **DS_CONTA** | PASSIVO NÃO CIRCULANTE |
| **Tabela Silver** | `n1_dfp_cia_aberta_bp` |
| **ST_CONTA_FIXA** | `S` |
| **COALESCE?** | Sim, `COALESCE(valor, 0)`. |
| **Usado em** | Liquidez Geral, PCT, Composição de Endividamento |

### V12 | Patrimônio Líquido
| Propriedade | Definição |
| :--- | :--- |
| **CD_CONTA** | `2.03` |
| **DS_CONTA** | PATRIMÔNIO LÍQUIDO |
| **Tabela Silver** | `n1_dfp_cia_aberta_bp` |
| **ST_CONTA_FIXA** | `S` |
| **COALESCE?** | Não permitido. Pode ser negativo (Passivo Descoberto). |
| **Usado em** | PCT/CP, Garantia do CP, Imobilização do Capital Próprio |

### V22 | Caixa e Equivalentes (Balanço)
| Propriedade | Definição |
| :--- | :--- |
| **CD_CONTA** | `1.01.01` |
| **DS_CONTA** | CAIXA E EQUIVALENTES DE CAIXA |
| **Tabela Silver** | `n1_dfp_cia_aberta_bp` |
| **ST_CONTA_FIXA** | `S` |
| **COALESCE?** | Sim, `COALESCE(valor, 0)`. |
| **Usado em** | Liquidez Imediata, Modelo Fleuriet (ACF) |

### 📈 Variáveis da Demonstração do Resultado (DRE) e Fluxo de Caixa (DFC)

### V19 | Receita Líquida de Vendas
| Propriedade | Definição |
| :--- | :--- |
| **CD_CONTA** | `3.01` |
| **DS_CONTA** | RECEITA DE VENDA DE BENS E/OU SERVIÇOS |
| **Tabela Silver** | `n1_dfp_cia_aberta_dre` |
| **ST_CONTA_FIXA** | `S` |
| **COALESCE?** | Mapear para 0 se a empresa não faturou no período. |
| **Usado em** | Margens operacionais, Giros de Ativos |

### V24 | Saldo Final de Caixa e Equivalentes (DFC)
| Propriedade | Definição |
| :--- | :--- |
| **CD_CONTA** | `6.05.02` |
| **DS_CONTA** | SALDO FINAL DE CAIXA E EQUIVALENTES |
| **Tabela Silver** | `n1_dfp_cia_aberta_dfc` |
| **ST_CONTA_FIXA** | `S` |
| **COALESCE?** | Fallback na conta `6.05.01` ou `1.01.01` se houver quebra de preenchimento. |
| **Usado em** | Dívida Líquida, Enterprise Value, FCF Yield |

---

## Bloco 3: Fichas de Indicadores Finais (Output Gold)

Abaixo constam as especificações de cada coluna de indicador calculada no Mart final, formatadas como fichas de dados.

### 🧩 Grupo 1: Liquidez

### IND_liquidez_geral | Liquidez Geral (LG)
| Propriedade | Definição |
| :--- | :--- |
| **Fórmula Gold** | `safe_div((V02__ativo_circ + V04__rlp), (V10__passivo_circ + V11__passivo_ncirc))` |
| **Conceito** | Mede a capacidade de pagamento no curto e longo prazo. Indica quanto a empresa tem para cada R$ 1,00 de dívida total. |
| **Unidade** | R$ (Índice adimensional) |
| **Análise Esperada** | Valores satisfatórios devem ser > `1.0`. |

### IND_liquidez_corrente | Liquidez Corrente (LC)
| Propriedade | Definição |
| :--- | :--- |
| **Fórmula Gold** | `safe_div(V02__ativo_circ, V10__passivo_circ)` |
| **Conceito** | Capacidade de pagamento exclusiva do curto prazo. |
| **Unidade** | R$ (Índice adimensional) |
| **Análise Esperada** | Satisfatório acima de `1.5` na indústria; serviços/varejo aceitam valores próximos a `1.0`. |

### IND_liquidez_seca | Liquidez Seca (LS)
| Propriedade | Definição |
| :--- | :--- |
| **Fórmula Gold** | `safe_div((V02__ativo_circ - V06__estoques_raw), V10__passivo_circ)` |
| **Conceito** | Mede a capacidade de pagamento no curto prazo ignorando os estoques (que têm menor liquidez real). |
| **Unidade** | R$ (Índice adimensional) |
| **Análise Esperada** | Valores superiores a `1.0` representam segurança imediata e independência das vendas. |

### IND_liquidez_imediata | Liquidez Imediata (LI)
| Propriedade | Definição |
| :--- | :--- |
| **Fórmula Gold** | `safe_div(V22__caixa_bp, V10__passivo_circ)` |
| **Conceito** | Revela a parcela de obrigações de curto prazo que pode ser liquidada instantaneamente com as disponibilidades em caixa. |
| **Unidade** | R$ (Índice adimensional) |
| **Análise Esperada** | Costuma ser um índice baixo (`0.1` a `0.3`), já que manter caixa parado reflete ineficiência. |

### 📉 Grupo 2: Estrutura de Capital e Endividamento

### IND_pct_cp | Participação de Capital de Terceiros (Grau de Endividamento)
| Propriedade | Definição |
| :--- | :--- |
| **Fórmula Gold** | `safe_div((V10__passivo_circ + V11__passivo_ncirc), V12__patrimonio_liquido)` |
| **Conceito** | Demonstra a proporção de capital externo que a empresa utiliza em relação ao capital investido pelos sócios. |
| **Unidade** | % (Razão) |
| **Análise Esperada** | Quanto menor, menor o risco de insolvência. |

### IND_pct_at | Endividamento Total
| Propriedade | Definição |
| :--- | :--- |
| **Fórmula Gold** | `safe_div((V10__passivo_circ + V11__passivo_ncirc), V01__ativo_total)` |
| **Conceito** | Indica qual percentual dos ativos da empresa foi financiado por recursos de terceiros. |
| **Unidade** | % |
| **Análise Esperada** | Valores acima de `70%` acendem alertas de alavancagem excessiva. |

### IND_composicao_endividamento | Perfil da Dívida
| Propriedade | Definição |
| :--- | :--- |
| **Fórmula Gold** | `safe_div(V10__passivo_circ, (V10__passivo_circ + V11__passivo_ncirc))` |
| **Conceito** | Mede a pressão de curto prazo da dívida. Percentual das obrigações totais que vence em menos de um ano. |
| **Unidade** | % |
| **Análise Esperada** | Concentrações acima de `60%` no curto prazo indicam risco de liquidez imediato. |

### IND_imobilizacao_cp | Imobilização do Capital Próprio
| Propriedade | Definição |
| :--- | :--- |
| **Fórmula Gold** | `safe_div(V05__ativo_nao_circ, V12__patrimonio_liquido)` |
| **Conceito** | Indica quanto do capital dos sócios está "travado" em ativos imobilizados. |
| **Unidade** | % |
| **Análise Esperada** | Abaixo de `100%` significa que há recurso livre para capital de giro. |

### ⚜️ Grupo 3: Análise Dinâmica de Capital de Giro (Modelo Fleuriet)

* **`AUX_aco`** (Ativo Circulante Operacional) = `V06__estoques_raw + (Contas_a_Receber_CVM)`
* **`AUX_pco`** (Passivo Circulante Operacional) = `(Fornecedores_CVM + Obrigações_Fiscais)`
* **`AUX_acf`** (Ativo Circulante Financeiro) = `V22__caixa_bp + (Aplicações_Financeiras_Curto_Prazo)`
* **`AUX_pcf`** (Passivo Circulante Financeiro) = `(Empréstimos_Curto_Prazo)`

### IND_ncg | Necessidade de Capital de Giro
| Propriedade | Definição |
| :--- | :--- |
| **Fórmula Gold** | `AUX_aco - AUX_pco` |
| **Conceito** | Volume de recursos financeiros que a operação da empresa consome rotineiramente no gap entre pagar e receber. |
| **Unidade** | R$ |

### IND_st | Saldo de Tesouraria
| Propriedade | Definição |
| :--- | :--- |
| **Fórmula Gold** | `AUX_acf - AUX_pcf` |
| **Conceito** | Sobra ou falta de recursos net de curtíssimo prazo geridos pela tesouraria. |
| **Unidade** | R$ |
| **Análise Esperada** | Valor negativo em períodos sucessivos configura o **Efeito Tesoura** (alerta grave). |


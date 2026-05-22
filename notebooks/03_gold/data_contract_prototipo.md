# Dicionário de Premissas | Setor: Metalurgia e Siderurgia 🏭
**Squad:** Heavy Metal 

**Data:** 15 de Maio de 2026 

**Base de Dados:** PostgreSQL (`layer_02_silver`) 

**Empresa Piloto:** ELECTRO AÇO ALTONA S/A (82.643.537/0001-34) 

---

## Bloco 1: Notas Gerais Obrigatórias

### N1. Caixa para indicadores: usar BP ou DFC?
| Indicador | Conta correta | Conta incorreta | Motivo |
|---|---|---|---|
| Liquidez Imediata | `1.01.01` + `1.01.02` (BP) | `6.05.02` (DFC) | O ratio de liquidez é um indicador de posição (fotografia), logo deve usar o BP. |
| Dívida Líquida | `6.05.02` (DFC) | `1.01.01` (BP) | A DFC reflete com mais precisão os equivalentes de caixa de altíssima liquidez, essenciais para o endividamento real da indústria pesada. |

### N2. Estoques ausentes (Alerta Crítico para Indústria)
Ao contrário do setor de serviços, **todas** as empresas operacionais de Metalurgia e Siderurgia **devem** possuir a conta de Estoques (`1.01.04`), composta por matéria-prima (minério de ferro, sucata) e produtos siderúrgicos em elaboração/acabados.
**Regra:** Diferente do Varejo, NÃO faremos `COALESCE(estoques, 0)`. Se a conta de estoques for nula em uma siderúrgica, isso caracteriza um erro de reporte da CVM ou empresa inoperante. O script Python deverá levantar um log de `WARNING` e desconsiderar a empresa do cálculo do respectivo trimestre.

### N3. LPA e a multiplicidade de contas 3.99.x.x
A DRE reporta diversas contas de Lucro por Ação (Básico, Diluído, ON, PN). Para padronização do algoritmo de *valuation* da camada Gold, utilizaremos prioritariamente o **LPA Básico ON** (`3.99.01.01`). 
**Regra de Fallback:** Grandes siderúrgicas (como Gerdau e Usiminas) possuem forte liquidez nas ações PN. Caso a empresa não possua ONs (ou tenham baixíssima liquidez), o algoritmo buscará a `3.99.01.02` (LPA Básico PN).

### N4. O Selo de Confiança ST_CONTA_FIXA
Contas com `ST_CONTA_FIXA = 'S'` são ancoradas pela CVM e seguras para extração direta. Siderúrgicas tendem a seguir estritamente o padrão da CVM, então quase 100% das nossas extrações ocorrerão via `CD_CONTA` fixo, minimizando buscas textuais (`ILIKE`).

---

## Bloco 2: Fichas de Variáveis

### 📊 Variáveis do Balanço Patrimonial (BP)

### V01 | Ativo Total
| Propriedade | Definição |
| :--- | :--- |
| **CD_CONTA** | `1` |
| **DS_CONTA** | ATIVO TOTAL |
| **Tabela Silver** | `n1_dfp_cia_aberta_bp` |
| **ST_CONTA_FIXA** | `S` |
| **Cobertura no setor** | 100% |
| **COALESCE?** | Não. Se nulo, descartar registro. |
| **Empresas sem conta** | Nenhuma |
| **Usado em** | Giro do Ativo, ROA, Endividamento Geral, Capital Investido |

### V02 | Ativo Circulante
| Propriedade | Definição |
| :--- | :--- |
| **CD_CONTA** | `1.01` |
| **DS_CONTA** | ATIVO CIRCULANTE |
| **Tabela Silver** | `n1_dfp_cia_aberta_bp` |
| **ST_CONTA_FIXA** | `S` |
| **Cobertura no setor** | 100% |
| **COALESCE?** | Não. |
| **Empresas sem conta** | Nenhuma |
| **Usado em** | Liquidez Corrente, Liquidez Seca, NCG |

### V06 | Estoques
| Propriedade | Definição |
| :--- | :--- |
| **CD_CONTA** | `1.01.04` |
| **DS_CONTA** | ESTOQUES |
| **Tabela Silver** | `n1_dfp_cia_aberta_bp` |
| **ST_CONTA_FIXA** | `S` |
| **Cobertura no setor** | 100% (Esperado para empresas ativas do setor) |
| **COALESCE?** | **Não.** Ausência indica anomalia severa no balanço industrial. |
| **Empresas sem conta** | [Verificar base por holdings puras classificadas no setor] |
| **Usado em** | Liquidez Seca, Giro de Estoques, PMRE, Ciclo Operacional |

### V10 | Passivo Circulante
| Propriedade | Definição |
| :--- | :--- |
| **CD_CONTA** | `2.01` |
| **DS_CONTA** | PASSIVO CIRCULANTE |
| **Tabela Silver** | `n1_dfp_cia_aberta_bp` |
| **ST_CONTA_FIXA** | `S` |
| **Cobertura no setor** | 100% |
| **COALESCE?** | Não. |
| **Empresas sem conta** | Nenhuma |
| **Usado em** | Liquidez (Corrente, Seca, Imediata), NCG, Dívida Curto Prazo |

---

### 📉 Variáveis da Demonstração de Resultado (DRE)

### V17 | Receita Líquida
| Propriedade | Definição |
| :--- | :--- |
| **CD_CONTA** | `3.01` |
| **DS_CONTA** | RECEITA DE VENDA DE BENS E/OU SERVIÇOS |
| **Tabela Silver** | `n1_dfp_cia_aberta_dre` |
| **ST_CONTA_FIXA** | `S` |
| **Cobertura no setor** | 100% |
| **COALESCE?** | Não. |
| **Empresas sem conta** | Nenhuma |
| **Usado em** | Margem Bruta, Margem EBITDA, Margem Líquida, Giros |

### V21 | Lucro Líquido
| Propriedade | Definição |
| :--- | :--- |
| **CD_CONTA** | `3.11` |
| **DS_CONTA** | LUCRO/PREJUÍZO CONSOLIDADO DO PERÍODO |
| **Tabela Silver** | `n1_dfp_cia_aberta_dre` |
| **ST_CONTA_FIXA** | `S` |
| **Cobertura no setor** | 100% |
| **COALESCE?** | Não. |
| **Empresas sem conta** | Nenhuma |
| **Usado em** | Margem Líquida, ROE, ROA, LPA |

---

### 💸 Variáveis da Demonstração de Fluxos de Caixa (DFC)

### V22 | Depreciação e Amortização
| Propriedade | Definição |
| :--- | :--- |
| **CD_CONTA** | `6.01.01.04` *(Nota: validar na base, siderúrgicas têm altíssima depreciação)* |
| **DS_CONTA** | DEPRECIAÇÃO E AMORTIZAÇÃO |
| **Tabela Silver** | `n1_dfp_cia_aberta_dfc` |
| **ST_CONTA_FIXA** | `S` |
| **Cobertura no setor** | 100% (Altos investimentos em CAPEX garantem D&A relevante) |
| **COALESCE?** | Sim, usar 0 se não reportado, mas sinalizar alerta de integridade. |
| **Empresas sem conta** | Nenhuma esperada |
| **Usado em** | Cálculo do EBITDA (EBIT + D&A) |

### V24 | Saldo Final de Caixa (DFC)
| Propriedade | Definição |
| :--- | :--- |
| **CD_CONTA** | `6.05.02` |
| **DS_CONTA** | SALDO FINAL DE CAIXA E EQUIVALENTES |
| **Tabela Silver** | `n1_dfp_cia_aberta_dfc` |
| **ST_CONTA_FIXA** | `S` |
| **Cobertura no setor** | 100% |
| **COALESCE?** | Não. |
| **Empresas sem conta** | Nenhuma |
| **Usado em** | Cálculo da Dívida Líquida |

---

## Bloco 3: Mapa Rápido (Indicadores x Variáveis)

| Indicador | Fórmula Base | Variáveis Necessárias |
| :--- | :--- | :--- |
| **Liquidez Corrente** | AC / PC | V02, V10 |
| **Liquidez Seca** | (AC - Estoques) / PC | V02, V06, V10 |
| **Margem Líquida** | Lucro Líquido / Receita Líquida | V21, V17 |
| **EBITDA** | EBIT + Depreciação e Amortização | V20, V22 |
| **Dívida Líquida** | Dívida Bruta - Saldo Final de Caixa (DFC) | V12, V13, V24 |# Dicionário de Premissas | Setor: Metalurgia e Siderurgia 🏭
**Squad:** [Nome do seu Squad]
**Data:** 15 de Maio de 2026
**Base de Dados:** PostgreSQL (`layer_02_silver`)
**Empresa Piloto:** Gerdau S.A. (CNPJ: 33.611.500/0001-19)

---

## Bloco 1: Notas Gerais Obrigatórias

### N1. Caixa para indicadores: usar BP ou DFC?
| Indicador | Conta correta | Conta incorreta | Motivo |
|---|---|---|---|
| Liquidez Imediata | `1.01.01` + `1.01.02` (BP) | `6.05.02` (DFC) | O ratio de liquidez é um indicador de posição (fotografia), logo deve usar o BP. |
| Dívida Líquida | `6.05.02` (DFC) | `1.01.01` (BP) | A DFC reflete com mais precisão os equivalentes de caixa de altíssima liquidez, essenciais para o endividamento real da indústria pesada. |

### N2. Estoques ausentes (Alerta Crítico para Indústria)
Ao contrário do setor de serviços, **todas** as empresas operacionais de Metalurgia e Siderurgia **devem** possuir a conta de Estoques (`1.01.04`), composta por matéria-prima (minério de ferro, sucata) e produtos siderúrgicos em elaboração/acabados.
**Regra:** Diferente do Varejo, NÃO faremos `COALESCE(estoques, 0)`. Se a conta de estoques for nula em uma siderúrgica, isso caracteriza um erro de reporte da CVM ou empresa inoperante. O script Python deverá levantar um log de `WARNING` e excluir a empresa do cálculo do respectivo trimestre.

### N3. LPA e a multiplicidade de contas 3.99.x.x
A DRE reporta diversas contas de Lucro por Ação (Básico, Diluído, ON, PN). Para padronização do algoritmo de *valuation* da camada Gold, utilizaremos prioritariamente o **LPA Básico ON** (`3.99.01.01`). 
**Regra de Fallback:** Grandes siderúrgicas (como Gerdau e Usiminas) possuem forte liquidez nas ações PN. Caso a empresa não possua ONs (ou tenham baixíssima liquidez), o algoritmo buscará a `3.99.01.02` (LPA Básico PN).

### N4. O Selo de Confiança ST_CONTA_FIXA
Contas com `ST_CONTA_FIXA = 'S'` são ancoradas pela CVM e seguras para extração direta. Siderúrgicas tendem a seguir estritamente o padrão da CVM, então quase 100% das nossas extrações ocorrerão via `CD_CONTA` fixo, minimizando buscas textuais (`ILIKE`).

---

## Bloco 2: Fichas de Variáveis

### 📊 Variáveis do Balanço Patrimonial (BP)

### V01 | Ativo Total
| Propriedade | Definição |
| :--- | :--- |
| **CD_CONTA** | `1` |
| **DS_CONTA** | ATIVO TOTAL |
| **Tabela Silver** | `n1_dfp_cia_aberta_bp` |
| **ST_CONTA_FIXA** | `S` |
| **Cobertura no setor** | 100% |
| **COALESCE?** | Não. Se nulo, descartar registro. |
| **Empresas sem conta** | Nenhuma |
| **Usado em** | Giro do Ativo, ROA, Endividamento Geral, Capital Investido |

### V02 | Ativo Circulante
| Propriedade | Definição |
| :--- | :--- |
| **CD_CONTA** | `1.01` |
| **DS_CONTA** | ATIVO CIRCULANTE |
| **Tabela Silver** | `n1_dfp_cia_aberta_bp` |
| **ST_CONTA_FIXA** | `S` |
| **Cobertura no setor** | 100% |
| **COALESCE?** | Não. |
| **Empresas sem conta** | Nenhuma |
| **Usado em** | Liquidez Corrente, Liquidez Seca, NCG |

### V06 | Estoques
| Propriedade | Definição |
| :--- | :--- |
| **CD_CONTA** | `1.01.04` |
| **DS_CONTA** | ESTOQUES |
| **Tabela Silver** | `n1_dfp_cia_aberta_bp` |
| **ST_CONTA_FIXA** | `S` |
| **Cobertura no setor** | 100% (Esperado para empresas ativas do setor) |
| **COALESCE?** | **Não.** Ausência indica anomalia severa no balanço industrial. |
| **Empresas sem conta** | [Verificar base por holdings puras classificadas no setor] |
| **Usado em** | Liquidez Seca, Giro de Estoques, PMRE, Ciclo Operacional |

### V10 | Passivo Circulante
| Propriedade | Definição |
| :--- | :--- |
| **CD_CONTA** | `2.01` |
| **DS_CONTA** | PASSIVO CIRCULANTE |
| **Tabela Silver** | `n1_dfp_cia_aberta_bp` |
| **ST_CONTA_FIXA** | `S` |
| **Cobertura no setor** | 100% |
| **COALESCE?** | Não. |
| **Empresas sem conta** | Nenhuma |
| **Usado em** | Liquidez (Corrente, Seca, Imediata), NCG, Dívida Curto Prazo |

---

### 📉 Variáveis da Demonstração de Resultado (DRE)

### V17 | Receita Líquida
| Propriedade | Definição |
| :--- | :--- |
| **CD_CONTA** | `3.01` |
| **DS_CONTA** | RECEITA DE VENDA DE BENS E/OU SERVIÇOS |
| **Tabela Silver** | `n1_dfp_cia_aberta_dre` |
| **ST_CONTA_FIXA** | `S` |
| **Cobertura no setor** | 100% |
| **COALESCE?** | Não. |
| **Empresas sem conta** | Nenhuma |
| **Usado em** | Margem Bruta, Margem EBITDA, Margem Líquida, Giros |

### V21 | Lucro Líquido
| Propriedade | Definição |
| :--- | :--- |
| **CD_CONTA** | `3.11` |
| **DS_CONTA** | LUCRO/PREJUÍZO CONSOLIDADO DO PERÍODO |
| **Tabela Silver** | `n1_dfp_cia_aberta_dre` |
| **ST_CONTA_FIXA** | `S` |
| **Cobertura no setor** | 100% |
| **COALESCE?** | Não. |
| **Empresas sem conta** | Nenhuma |
| **Usado em** | Margem Líquida, ROE, ROA, LPA |

---

### 💸 Variáveis da Demonstração de Fluxos de Caixa (DFC)

### V22 | Depreciação e Amortização
| Propriedade | Definição |
| :--- | :--- |
| **CD_CONTA** | `6.01.01.04` *(Nota: validar na base, siderúrgicas têm altíssima depreciação)* |
| **DS_CONTA** | DEPRECIAÇÃO E AMORTIZAÇÃO |
| **Tabela Silver** | `n1_dfp_cia_aberta_dfc` |
| **ST_CONTA_FIXA** | `S` |
| **Cobertura no setor** | 100% (Altos investimentos em CAPEX garantem D&A relevante) |
| **COALESCE?** | Sim, usar 0 se não reportado, mas sinalizar alerta de integridade. |
| **Empresas sem conta** | Nenhuma esperada |
| **Usado em** | Cálculo do EBITDA (EBIT + D&A) |

### V24 | Saldo Final de Caixa (DFC)
| Propriedade | Definição |
| :--- | :--- |
| **CD_CONTA** | `6.05.02` |
| **DS_CONTA** | SALDO FINAL DE CAIXA E EQUIVALENTES |
| **Tabela Silver** | `n1_dfp_cia_aberta_dfc` |
| **ST_CONTA_FIXA** | `S` |
| **Cobertura no setor** | 100% |
| **COALESCE?** | Não. |
| **Empresas sem conta** | Nenhuma |
| **Usado em** | Cálculo da Dívida Líquida |

---

## Bloco 3: Mapa Rápido (Indicadores x Variáveis)

| Indicador | Fórmula Base | Variáveis Necessárias |
| :--- | :--- | :--- |
| **Liquidez Corrente** | AC / PC | V02, V10 |
| **Liquidez Seca** | (AC - Estoques) / PC | V02, V06, V10 |
| **Margem Líquida** | Lucro Líquido / Receita Líquida | V21, V17 |
| **EBITDA** | EBIT + Depreciação e Amortização | V20, V22 |
| **Dívida Líquida** | Dívida Bruta - Saldo Final de Caixa (DFC) | V12, V13, V24 |
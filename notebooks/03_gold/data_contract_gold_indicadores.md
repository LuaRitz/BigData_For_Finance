# 🥇 Data Contract Definitivo | Camada Gold: Indicadores Financeiros

**Squad:** Big Data for Finance  
**Data da Última Revisão:** 22 de Maio de 2026  
**Versão:** 1.0.0  
**Status:** Homologado / Em Produção  
**Base de Dados:** PostgreSQL  
**Esquema de Destino:** `layer_03_gold`  
**Tabela Alvo:** `mart_indicadores_financeiros`  
**Responsável Técnico/Negócio:** Prof. Ivan Mello  

---

## 📝 Termo de Introdução e Governança

Este contrato de dados (Data Contract) visa estabelecer formalmente as premissas de engenharia, regras de negócio e esquemas estruturais para a geração do Data Mart de Indicadores Financeiros na camada **Gold**. Ele serve como uma ponte de verdade entre o time de Engenharia de Dados e os Analistas/C-Level que consomem o dashboard de BI e modelos analíticos. Qualquer alteração nas fórmulas de cálculo ou nos códigos de conta mapeados deve passar por aprovação deste comitê e gerar um incremento de versão neste documento.

---

## 🧱 Bloco 1: Notas Gerais Obrigatórias e Arquitetura

### N1. Engenharia Reversa e Padronização de Prefixos
Para garantir total rastreabilidade (linhagem de dados), transparência e auditoria das fórmulas contábeis, toda e qualquer coluna gerada na tabela `mart_indicadores_financeiros` deve, obrigatoriamente, seguir as regras de nomenclatura por prefixos tridimensionais abaixo:
* **`V__` (Variável de Input):** Mapeamento direto de um ou mais códigos de conta (`CD_CONTA`) provenientes das tabelas de Balanço Patrimonial (BP), Demonstração do Resultado do Exercício (DRE) ou Demonstração dos Fluxos de Caixa (DFC) da camada Silver.
* **`AUX__` (Variável Auxiliar):** Colunas que consolidam combinações algébricas intermédias de variáveis `V__`. Não possuem interpretação financeira direta isolada, mas servem para simplificar o cálculo de indicadores complexos (ex: Capital Circulante Líquido, Ativo Operacional, etc.).
* **`IND__` (Indicador Financeiro Final):** Produto final com significado econômico-financeiro exato, pronto para consumo em dashboards de BI, relatórios gerenciais e inteligência de mercado.

### N2. Divisão Segura (`safe_div`) contra Quebras de Pipeline
Devido à natureza dos dados reais de empresas (especialmente aquelas em recuperação judicial ou startups em estágio pré-operacional), é comum encontrar contas de Passivo Circulante, Empréstimos ou Estoques zerados. Para evitar erros fatais de interrupção do processamento (*ZeroDivisionError*) ou a inserção de valores infinitos que quebram as agregações do banco, todas as fórmulas deste contrato devem utilizar a lógica da função genérica `safe_div(numerador, denominador)`.
* **Regra de Execução:** Se `denominador == 0` ou `denominador IS NULL`, o retorno do pipeline deve ser estritamente `NaN` (ou `NULL` no banco de dados), garantindo a integridade analítica.

### N3. Caixa para Indicadores: Segregação Estratégica (BP vs DFC)
A origem do Caixa e Equivalentes impacta diretamente os resultados de risco e liquidez. Fica acordado o seguinte mapeamento segregado:
* **Cálculos de Liquidez Imediata e Modelo Fleuriet (ACF):** Devem utilizar a conta de Balanço Patrimonial `1.01.01` (Caixa e Equivalentes de Caixa), visto que são métricas clássicas de posição (fotografia estática do balanço).
* **Cálculos de Dívida Líquida, Enterprise Value (EV) e Free Cash Flow Yield (FCF Yield):** Devem utilizar obrigatoriamente a conta `6.05.02` (Saldo Final de Caixa e Equivalentes) proveniente da DFC. Conforme o pronunciamento técnico **CPC 03**, a DFC abrange com maior precisão os equivalentes de caixa reais (como CDBs e LFTs com liquidez de até 90 dias) e caixas restritos de grupos à venda (**CPC 31**), cruciais para calcular o real endividamento e a capacidade de solvência da indústria.

### N4. Tratamento de Estoques Ausentes (Regra de Negócio Setorial)
Empresas de serviços puros (como o subsetor de Educação, Turismo ou a própria B3) não reportam estoques físicos, fazendo com que a conta `1.01.04` venha ausente na camada Silver.
* **Tratamento no Pipeline:** Aplica-se `COALESCE(v06_estoques, 0)` para que somas e subtrações estruturais não resultem em nulo.
* **Exceção de Indicadores:** Indicadores específicos de eficiência operacional (como "Giro de Estoques" ou "Ciclo Econômico") não devem assumir valor zero para essas empresas; o pipeline deve preencher com a flag textual/valor de escape `"N/A"` para evitar distorções graves nas medianas setoriais.

### N5. Granularidade, Chave Primária e Deduplicação Blindada
A tabela da camada Gold possui granularidade estrita de **uma linha por empresa e período**.
* **Chave Primária Composta:** `CNPJ_CIA` + `DT_REFER`.
* **Regra de Deduplicação:** O pipeline de ingestão limpa os dados aplicando um particionamento (`ROW_NUMBER()`) por `(CNPJ_CIA, DT_REFER, CD_CONTA, DS_CONTA)` ordenado por `VERSAO DESC` e prioritariamente selecionando os registros onde `FLAG_RECONSTRUCAO = False` (dados auditados originais) para mitigar a duplicidade gerada por republicações espontâneas da CVM.

---

## 📥 Bloco 2: Fichas Técnicas das Variáveis de Input (Camada Silver -> Gold)

Estas variáveis representam o mapeamento semântico das contas contábeis CVM da camada Silver para alimentar os motores de cálculo da Gold.

### V01 | Ativo Total (AT)
* **Código da Conta (CD_CONTA):** `1`
* **Descrição CVM:** ATIVO TOTAL
* **Tabela de Origem Silver:** `layer_02_silver.n1_dfp_cia_aberta_bp`
* **Conta Fixa/Padronizada:** Sim (`S`) - Cobertura de 100% nas empresas.
* **Tratamento de Nulos:** Proibido. Se nulo, a linha inteira da empresa deve ir para a tabela de rejeito (Dead Letter Queue).
* **Principais Usos:** ROA, ROI, PCT/AT, Liquidez Geral, Imobilização do Ativo Total.

### V02 | Ativo Circulante (AC)
* **Código da Conta (CD_CONTA):** `1.01`
* **Descrição CVM:** ATIVO CIRCULANTE
* **Tabela de Origem Silver:** `layer_02_silver.n1_dfp_cia_aberta_bp`
* **Conta Fixa/Padronizada:** Sim (`S`)
* **Tratamento de Nulos:** Não aplicável (cobertura total).
* **Principais Usos:** Liquidez Geral, Liquidez Corrente, Liquidez Seca, CCL, ACF (Fleuriet).

### V04 | Realizável a Longo Prazo (RLP)
* **Código da Conta (CD_CONTA):** `1.02.01`
* **Descrição CVM:** ATIVO REALIZÁVEL A LONGO PRAZO
* **Tabela de Origem Silver:** `layer_02_silver.n1_dfp_cia_aberta_bp`
* **Conta Fixa/Padronizada:** Sim (`S`)
* **Tratamento de Nulos:** `COALESCE(valor, 0)`.
* **Principais Usos:** Liquidez Geral.

### V05 | Ativo Não Circulante / Imobilizado + Intangível (ANC)
* **Código da Conta (CD_CONTA):** `1.02`
* **Descrição CVM:** ATIVO NÃO CIRCULANTE
* **Tabela de Origem Silver:** `layer_02_silver.n1_dfp_cia_aberta_bp`
* **Conta Fixa/Padronizada:** Sim (`S`)
* **Tratamento de Nulos:** Não esperado.
* **Principais Usos:** Imobilização do Capital Próprio, Imobilização do Ativo Total.

### V06 | Estoques (Raw)
* **Código da Conta (CD_CONTA):** `1.01.04`
* **Descrição CVM:** ESTOQUES
* **Tabela de Origem Silver:** `layer_02_silver.n1_dfp_cia_aberta_bp`
* **Conta Fixa/Padronizada:** Não (`N`) - Cobertura setorial variável (~89% na base total B3).
* **Tratamento de Nulos:** `COALESCE(valor, 0)` para cálculos de liquidez/estrutura, mas marcado como indício de empresa prestadora de serviços.
* **Principais Usos:** Liquidez Seca, ACO (Fleuriet).

### V10 | Passivo Circulante (PC)
* **Código da Conta (CD_CONTA):** `2.01`
* **Descrição CVM:** PASSIVO CIRCULANTE
* **Tabela de Origem Silver:** `layer_02_silver.n1_dfp_cia_aberta_bp`
* **Conta Fixa/Padronizada:** Sim (`S`)
* **Tratamento de Nulos:** Não permitido.
* **Principais Usos:** Indicadores de Liquidez (Geral, Corrente, Seca, Imediata), Endividamento (PCT, Composição de Endividamento), PCF/PCO (Fleuriet).

### V11 | Passivo Não Circulante / Exigível a Longo Prazo (PNC)
* **Código da Conta (CD_CONTA):** `2.02`
* **Descrição CVM:** PASSIVO NÃO CIRCULANTE
* **Tabela de Origem Silver:** `layer_02_silver.n1_dfp_cia_aberta_bp`
* **Conta Fixa/Padronizada:** Sim (`S`)
* **Tratamento de Nulos:** `COALESCE(valor, 0)`.
* **Principais Usos:** Liquidez Geral, PCT, Composição de Endividamento.

### V12 | Patrimônio Líquido (PL)
* **Código da Conta (CD_CONTA):** `2.03`
* **Descrição CVM:** PATRIMÔNIO LÍQUIDO
* **Tabela de Origem Silver:** `layer_02_silver.n1_dfp_cia_aberta_bp`
* **Conta Fixa/Padronizada:** Sim (`S`)
* **Tratamento de Nulos:** Não permitido. Pode ser negativo (Passivo Descoberto).
* **Principais Usos:** PCT/CP, Garantia do CP, Imobilização do Capital Próprio.

### V19 | Receita Líquida de Vendas
* **Código da Conta (CD_CONTA):** `3.01`
* **Descrição CVM:** RECEITA DE VENDA DE BENS E/OU SERVIÇOS
* **Tabela de Origem Silver:** `layer_02_silver.n1_dfp_cia_aberta_dre`
* **Conta Fixa/Padronizada:** Sim (`S`)
* **Tratamento de Nulos:** Mapear para 0 se a empresa não faturou no período (pré-operacional).
* **Principais Usos:** Margens operacionais, Giros de Ativos.

### V22 | Caixa e Equivalentes (Balanço)
* **Código da Conta (CD_CONTA):** `1.01.01`
* **Descrição CVM:** CAIXA E EQUIVALENTES DE CAIXA
* **Tabela de Origem Silver:** `layer_02_silver.n1_dfp_cia_aberta_bp`
* **Conta Fixa/Padronizada:** Sim (`S`)
* **Tratamento de Nulos:** `COALESCE(valor, 0)`.
* **Principais Usos:** Liquidez Imediata, Modelo Fleuriet (ACF).

### V24 | Saldo Final de Caixa e Equivalentes (DFC)
* **Código da Conta (CD_CONTA):** `6.05.02`
* **Descrição CVM:** SALDO FINAL DE CAIXA E EQUIVALENTES
* **Tabela de Origem Silver:** `layer_02_silver.n1_dfp_cia_aberta_dfc`
* **Conta Fixa/Padronizada:** Sim (`S`)
* **Tratamento de Nulos:** Buscar por fallback na conta `6.05.01` ou `1.01.01` se houver quebra de preenchimento, documentando o alerta de qualidade.
* **Principais Usos:** Cálculo de Dívida Líquida, Enterprise Value, FCF Yield.

---

## 📊 Bloco 3: Fichas Técnicas de Indicadores Finais (Output Gold)

Abaixo constam as especificações de cada coluna de indicador calculada no Mart final.

### 🧩 Grupo 1: Liquidez

#### IND_liquidez_geral
* **Nome de Negócio:** Liquidez Geral (LG)
* **Fórmula de Implementação:** `safe_div((V02__ativo_circ + V04__rlp), (V10__passivo_circ + V11__passivo_ncirc))`
* **Conceito Financeiro:** Mede a segurança financeira de longo prazo da empresa. Indica se os recursos realizáveis a curto e longo prazo cobrem todas as obrigações assumidas.
* **Unidade:** R$ (Índice adimensional)
* **Análise Esperada:** Valores acima de `1.0` indicam uma situação confortável no horizonte total.

#### IND_liquidez_corrente
* **Nome de Negócio:** Liquidez Corrente (LC)
* **Fórmula de Implementação:** `safe_div(V02__ativo_circ, V10__passivo_circ)`
* **Conceito Financeiro:** Capacidade da empresa de honrar seus compromissos financeiros de curto prazo (até 1 ano) usando seus ativos de alta liquidez.
* **Unidade:** R$ (Índice adimensional)
* **Análise Esperada:** Ideal acima de `1.5` para indústrias; setores de serviços/varejo aceitam valores próximos a `1.0` devido ao ciclo operacional acelerado.

#### IND_liquidez_seca
* **Nome de Negócio:** Liquidez Seca (LS)
* **Fórmula de Implementação:** `safe_div((V02__ativo_circ - V06__estoques_raw), V10__passivo_circ)`
* **Conceito Financeiro:** Testa a solvência de curto prazo da companhia em um cenário extremo de estresse, desconsiderando completamente a venda de estoques (o ativo circulante menos líquido).
* **Unidade:** R$ (Índice adimensional)
* **Análise Esperada:** Valores superiores a `1.0` representam segurança imediata e independência da velocidade das vendas.

#### IND_liquidez_imediata
* **Nome de Negócio:** Liquidez Imediata (LI)
* **Fórmula de Implementação:** `safe_div(V22__caixa_bp, V10__passivo_circ)`
* **Conceito Financeiro:** Revela a parcela de obrigações de curto prazo que pode ser liquidada instantaneamente com as disponibilidades em caixa e aplicações financeiras prontas.
* **Unidade:** R$ (Índice adimensional)
* **Análise Esperada:** Geralmente é um índice baixo (`0.1` a `0.3`). Valores excessivamente altos sinalizam ineficiência na alocação de capital (caixa ocioso).

---

### 📉 Grupo 2: Estrutura de Capital e Endividamento

#### IND_pct_cp
* **Nome de Negócio:** Participação de Capital de Terceiros sobre o Capital Próprio (Grau de Endividamento)
* **Fórmula de Implementação:** `safe_div((V10__passivo_circ + V11__passivo_ncirc), V12__patrimonio_liquido)`
* **Conceito Financeiro:** Demonstra a proporção de capital externo que a empresa utiliza em relação ao capital investido pelos sócios/acionistas.
* **Unidade:** % (Percentual ou Razão)
* **Análise Esperada:** Quanto menor, menor o risco de insolvência e menor a dependência de bancos e credores.

#### IND_pct_at
* **Nome de Negócio:** Participação de Capital de Terceiros sobre o Ativo Total (Endividamento Total)
* **Fórmula de Implementação:** `safe_div((V10__passivo_circ + V11__passivo_ncirc), V01__ativo_total)`
* **Conceito Financeiro:** Indica qual percentual dos ativos da empresa foi financiado por recursos de terceiros (capital de dívida).
* **Unidade:** % (Percentual)
* **Análise Esperada:** Valores acima de `70%` acendem alertas de alavancagem excessiva na maioria dos setores industriais.

#### IND_garantia_cp_ct
* **Nome de Negócio:** Garantia do Capital Próprio ao Capital de Terceiros
* **Fórmula de Implementação:** `safe_div(V12__patrimonio_liquido, (V10__passivo_circ + V11__passivo_ncirc))`
* **Conceito Financeiro:** O inverso do grau de endividamento. Mede o tamanho do colchão de segurança fornecido pelos acionistas para cobrir eventuais perdas de credores externos.
* **Unidade:** R$ (Índice)

#### IND_composicao_endividamento
* **Nome de Negócio:** Composição do Endividamento (Perfil da Dívida)
* **Fórmula de Implementação:** `safe_div(V10__passivo_circ, (V10__passivo_circ + V11__passivo_ncirc))`
* **Conceito Financeiro:** Mede a pressão de curto prazo da dívida. Indica qual percentual das obrigações totais vence em menos de um ano.
* **Unidade:** % (Percentual)
* **Análise Esperada:** Concentrações acima de `60%` no curto prazo indicam perfil de endividamento nocivo (risco de liquidez imediato).

#### IND_imobilizacao_cp
* **Nome de Negócio:** Imobilização do Capital Próprio
* **Fórmula de Implementação:** `safe_div(V05__ativo_nao_circ, V12__patrimonio_liquido)`
* **Conceito Financeiro:** Indica quanto do capital dos sócios está "travado" em ativos de longo prazo e imobilizados (máquinas, prédios, marcas).
* **Unidade:** % (Percentual)
* **Análise Esperada:** Valores abaixo de `100%` significam que o PL financia todo o ativo permanente e ainda sobra recurso para o capital de giro.

#### IND_imobilizacao_at
* **Nome de Negócio:** Imobilização do Ativo Total
* **Fórmula de Implementação:** `safe_div(V05__ativo_nao_circ, V01__ativo_total)`
* **Conceito Financeiro:** Mede a rigidez da estrutura de ativos da empresa. Revela qual percentual do patrimônio total é composto por bens de difícil e lenta conversão em caixa.
* **Unidade:** % (Percentual)

---

### ⚜️ Grupo 3: Análise Dinâmica de Capital de Giro (Modelo Fleuriet)

Para a aplicação deste bloco, as contas de curto prazo são reclassificadas em **Operacionais/Cíclicas** (ligadas à atividade-fim) e **Financeiras/Erráticas** (ligadas à tesouraria e empréstimos), gerando as variáveis auxiliares abaixo:

#### ⚙️ Variáveis Auxiliares (Sustentação Fleuriet)
* `AUX_aco` (Ativo Circulante Operacional) = `V06__estoques_raw + (Contas_a_Receber_CVM)`
* `AUX_pco` (Passivo Circulante Operacional) = `(Fornecedores_CVM + Obrigações_Fiscais_Trabalhistas)`
* `AUX_acf` (Ativo Circulante Financeiro) = `V22__caixa_bp + (Aplicações_Financeiras_Curto_Prazo)`
* `AUX_pcf` (Passivo Circulante Financeiro) = `(Empréstimos_e_Financiamentos_Curto_Prazo)`

#### IND_ncg
* **Nome de Negócio:** Necessidade de Capital de Giro (NCG)
* **Fórmula de Implementação:** `AUX_aco - AUX_pco`
* **Conceito Financeiro:** Representa o volume de recursos financeiros que a operação da empresa consome rotineiramente no gap entre pagar fornecedores/produzir e receber dos clientes.
* **Unidade:** R$ (Valor Monetário)
* **Análise Esperada:** Se positiva, indica que a empresa precisa de financiamento para rodar. Se negativa, a operação gera caixa antes mesmo de pagar seus custos diretos (cenário ideal comum em supermercados e e-commerce).

#### IND_st
* **Nome de Negócio:** Saldo de Tesouraria (ST)
* **Fórmula de Implementação:** `AUX_acf - AUX_pcf`
* **Conceito Financeiro:** É a sobra ou falta de recursos net de curtíssimo prazo geridos pela área financeira/tesouraria.
* **Unidade:** R$ (Valor Monetário)
* **Análise Esperada:** **Efeito Tesoura:** Se o Saldo de Tesouraria se mantiver sistematicamente negativo ao longo de múltiplos trimestres concomitante com um aumento da NCG, fica configurado o Efeito Tesoura, sinalizando insolvência iminente por crescimento desordenado.

---

## 🛠️ Bloco 4: Regras de Validação de Dados (Data Quality)

Com o objetivo de impedir a poluição do Data Mart por falhas na extração da CVM ou erros no pipeline Python, a tabela Gold implementará testes de qualidade automatizados pós-escrita:

1. **Garantia de Linhas Únicas:** Um teste de consistência deve verificar se `COUNT(DISTINCT CNPJ_CIA || DT_REFER) == COUNT(*)`. Qualquer desvio anula a carga e emite alerta crítico no Slack/PagerDuty.
2. **Consistência de Sinais Contábeis:** Ativos Totais (`V01`), Circulantes (`V02`) e Passivos (`V10`) devem ser estritamente maiores ou iguais a zero. Valores negativos nesses campos disparam o bloqueio da tabela Gold.
3. **Validação Estatística de Outliers (Z-Score):** Indicadores de liquidez que superem um Z-Score de `+4.0` em relação à mediana histórica do setor econômico da empresa devem ser marcados com uma flag de auditoria interna (`FLAG_OUTLIER = TRUE`) para análise manual do time de Controladoria antes de alimentar o dashboard executivo.

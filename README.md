# Molecular Cell Research - Scientific Systems Exploration Platform (SSEP)

Plataforma de engenharia de conhecimento científico e biofísica computacional dedicada à integração formal de evidências empíricas, rastreabilidade criptográfica de proveniência, representação rigorosa de incertezas, modelagem mecanomolecular e desenho experimental discriminatório.

**Repositório Remoto:** `https://github.com/walbarellos/molecular-cell-research`  
**Metodologia:** Engenharia em Cascata Estrita (Ciclos 00 a 09)  
**Governança:** Epistemic Firewall Transversal (INV-DATA-001) e Rastreabilidade SHA-256  

---

## 1. Visão Geral da Arquitetura (L1 a L7)

![Arquitetura de Camadas SSEP](docs/assets/icons/architecture_layers_l1_l7.svg)

A plataforma estrutura-se em 7 camadas modulares com separação unidirecional de dependências e um pilar transversal de integridade científica:

```
[L7 PRESENTATION]     CLI Tri-modal: Usuário (Operacional) │ Engenheiro (Componentes) │ Cientista (Proveniência)
      │
[L6 APPLICATION]      ExplorationService │ ReproductionPipeline │ FalsificationPipeline │ DiscriminatorEngine
      │
[L5 COMPUTATION]      Kinetics (Michaelis-Menten / Gillespie) │ Model M1 (Quimioestático) │ Model M2 (Bell/Kramers)
      │
[L4 KNOWLEDGE]        Grafo Epistêmico: Biological Entities │ Physical Relations │ Claims │ ConflictRecords
      │
[L3 EVIDENCE]         EvidenceRecords (Medições ± Incertezas) │ ExperimentalConditions │ SourceMetadata (DOI)
      │
[L2 DATA TIERS]       Segregação Estrita: [TIER::RAW] (CSV) │ [TIER::DERIVED] (JSON) │ [TIER::GENERATED] (Simulações)
      │
[L1 INFRASTRUCTURE]   Sistema POSIX │ Checksums Criptográficos SHA-256 │ Semente PRNG Determinística
```

---

## 2. Estrutura Canônica da Documentação (`docs/`)

Toda a documentação do projeto está padronizada e indexada em diretórios numerados:

* **[`docs/00-cascata/`](file:///home/walbarellos/Projects/microbiology-cell/docs/00-cascata/)**:
  * `00.00 - Notas Originais do Usuario.txt`: Requisitos originais do usuário e visão conceitual.
  * `00.01 - Manifesto e Metodologia Cascata.md`: Princípios de integridade epistêmica e filosofia de engenharia.
  * `00.02 - Roadmap dos Ciclos 00 a 09.md`: Histórico de planejamento e entregas dos 10 ciclos cascata.
* **[`docs/01-diagramas/`](file:///home/walbarellos/Projects/microbiology-cell/docs/01-diagramas/)**:
  * `01.01 - Arquitetura de Camadas L1 a L7.md`: Diagrama vetorial e especificações estruturais de L1 a L7.
  * `01.02 - Pipeline de Dados e Epistemic Firewall.md`: Fluxo e barreiras de contenção (`RAW` $\to$ `DERIVED` $\to$ `GENERATED`).
  * `01.03 - Grafo de Entidades e Relacoes.md`: Topologia ontológica do complexo KIF5B, microtúbulo e nucleotídeos.
  * `01.04 - Maquina de Estados Epistemica.md`: Ciclo de vida de conhecimento, falsificação e *Negative Knowledge*.
* **[`docs/02-arquitetura/`](file:///home/walbarellos/Projects/microbiology-cell/docs/02-arquitetura/)**:
  * `02.01 - Especificacao de Arquitetura SSEP v0.1.md`: Requisitos RF/RNF, contratos L1-L7 e os 15 objetos normativos.
* **[`docs/03-dados/`](file:///home/walbarellos/Projects/microbiology-cell/docs/03-dados/)**:
  * `03.01 - Curadoria de Datasets CELL-LAB-001.md`: Curadoria e QC de Dataset A (calibração) e Dataset B (falsificação).
* **[`docs/04-modelos/`](file:///home/walbarellos/Projects/microbiology-cell/docs/04-modelos/)**:
  * `04.01 - Especificacao do Modelo Minimo KIF5B.md`: Modelo cinético analítico, ciclo mecanoquímico e Gillespie.
* **[`docs/05-relatorios/`](file:///home/walbarellos/Projects/microbiology-cell/docs/05-relatorios/)**:
  * `05.01 - Relatorio de Reproducao Dataset A.md`: Benchmark de reprodução sem carga ($R^2 = 0.9955$, $\chi^2_{\text{red}} = 0.778$).
  * `05.02 - Relatorio de Falsificacao Dataset B.md`: Quebra preditiva sob carga ($z = -49.8\sigma$ no stall force).
  * `05.03 - Desenho Experimental Discriminatorio.md`: Proposta ótima de ensaio com $100\%$ de poder de resolução ($> 20\sigma$).
* **[`docs/06-interfaces/`](file:///home/walbarellos/Projects/microbiology-cell/docs/06-interfaces/)**:
  * `06.01 - Guia da Interface e CLI L7.md`: Manual operacional detalhado dos três modos de visualização.

---

## 3. Ativos Visuais e Vetoriais (`docs/assets/icons/`)

* [`architecture_layers_l1_l7.svg`](file:///home/walbarellos/Projects/microbiology-cell/docs/assets/icons/architecture_layers_l1_l7.svg): Arquitetura completa L1-L7 com o pilar transversal de integridade.
* [`epistemic_firewall.svg`](file:///home/walbarellos/Projects/microbiology-cell/docs/assets/icons/epistemic_firewall.svg): Isolamento de dados observados vs. sintéticos.
* [`epistemic_state_transitions.svg`](file:///home/walbarellos/Projects/microbiology-cell/docs/assets/icons/epistemic_state_transitions.svg): Máquina de estados de propagação epistêmica.
* [`kinesin_motor.svg`](file:///home/walbarellos/Projects/microbiology-cell/docs/assets/icons/kinesin_motor.svg): Estrutura biofísica do dímero de Cinesina-1 sobre protofilamento de microtúbulo.
* [`kinesin_mechanochemical_cycle.svg`](file:///home/walbarellos/Projects/microbiology-cell/docs/assets/icons/kinesin_mechanochemical_cycle.svg): Ciclo mecanoquímico de 4 estados e ancoramento do *neck-linker*.
* [`conflict_divergence.svg`](file:///home/walbarellos/Projects/microbiology-cell/docs/assets/icons/conflict_divergence.svg): Curvas de confronto força-velocidade e divergência estatística de $49.8\sigma$.
* [`discriminatory_power.svg`](file:///home/walbarellos/Projects/microbiology-cell/docs/assets/icons/discriminatory_power.svg): Espaço de desenho experimental discriminatório entre modelos concorrentes.

---

## 4. Web Dashboard Interativo L7 (Ciclo 11)

A plataforma conta com uma interface gráfica completa no navegador, desenvolvida com padrões visuais de publicação acadêmica e científica (**estritamente sem emojis**), proporcionando exploração mecanoquímica reativa:

```bash
# Iniciar o painel web interativo (FastAPI na porta 8000)
./cell-ctl ui
# ou: make ui
# ou: python manage.py ui --host 0.0.0.0 --port 8000
```

Acesse no navegador: **`http://localhost:8000`**

### Recursos da Interface Web:
* **01. Mecanoquímica KIF5B (M1 vs M2):** Sliders dinâmicos de $[\text{ATP}]$, $F_{\text{load}}$ e temperatura, animação física do motor caminhando no protofilamento de microtúbulo e gráficos interativos em Canvas ($v(F)$ e $v([\text{ATP}])$) com os dados empíricos de Schnitzer 1997 e Visscher 1999 com barras de erro $\pm\sigma$.
* **02. Competição Motora (Tug-of-War Kinesin vs. Dynein - Ciclo 12):** Simulação de transporte vesicular bidirecional via algoritmo estocástico de Gillespie, plotagem contínua de trajetória $x(t)$, motores ativos $n_+(t), n_-(t)$ e distribuição estacionária da equação mestra de Markov.
* **03. Dinâmica Langevin Estocástica (Ruído Térmico - Ciclo 13):** Integração contínua em microsegundos da equação de Langevin sobreamortecida (Ornstein-Uhlenbeck) sob poço óptico, exibindo ruído térmico browniano e passos discretos de $8.20 \ \text{nm}$.
* **04. Grafo Epistêmico & Conflitos:** Topologia interativa de linhagem formal de conhecimento e auditoria de resoluções.
* **05. Desenho Experimental Discriminatório:** Mapa de calor de poder resolutivo no espaço $[\text{ATP}] \times F_{\text{load}}$.

---

## 5. Central de Administração e Linha de Comando (CLI)

Todos os ensaios podem também ser executados e auditados diretamente via terminal:

### Opção A: Script Executável Unificado (`./cell-ctl`)
```bash
./cell-ctl ui                # Inicia o Web Dashboard Interativo (Porta 8000)
./cell-ctl status            # Resumo global do grafo epistêmico (4 modelos registrados)
./cell-ctl user              # Modo Usuário (regime validado, F = 0 pN)
./cell-ctl user --load 4.0   # Modo Usuário (alerta Epistemic Firewall sob carga)
./cell-ctl tug-of-war        # Simulação estocástica de competição motora (Ciclo 12)
./cell-ctl langevin          # Dinâmica contínua Langevin com ruído térmico (Ciclo 13)
./cell-ctl engineer          # Modo Engenheiro (componentes, entidades e parâmetros)
./cell-ctl scientist         # Modo Científico (proveniência e conflitos formais)
./cell-ctl design            # Desenho Experimental Discriminatório (Ciclo 09)
./cell-ctl evaluate-m2       # Validação multivariada do Modelo M2 (Ciclo 10)
./cell-ctl reproduce         # Executa ciclo de reprodução (Dataset A)
./cell-ctl falsify           # Executa ciclo de falsificação (Dataset B)
./cell-ctl test              # Executa suíte de testes (pytest)
./cell-ctl verify            # Auditoria formal completa de dados, schemas e invariantes
./cell-ctl demo              # Bateria completa pedagógica de demonstração (L1 a L7)
```

### Opção B: Automação via `make`
```bash
make ui                      # Inicia o Web Dashboard L7
make tug-of-war              # Executa ensaio de Tug-of-War (Ciclo 12)
make langevin                # Executa dinâmica Langevin (Ciclo 13)
make status                  # Resumo do grafo epistêmico
make test                    # Executa suíte de testes
make demo                    # Executa bateria pedagógica
```

---

## 6. Como Executar os Testes Automatizados

A suíte de testes automatizados cobre validações de esquemas JSON, integridade referencial ponta a ponta, inviolabilidade de invariantes epistêmicas, controle de qualidade de dados brutos e todos os 4 motores biofísicos computacionais:

```bash
./cell-ctl test
# ou: .venv/bin/pytest -v
```

*Status:* **49 testes automatizados aprovados (100% de sucesso).**


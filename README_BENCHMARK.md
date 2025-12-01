# 📊 Benchmark de Algoritmos de Caminho Mínimo

<p align="center">
  <img src="https://img.shields.io/badge/Algoritmos-3-blue?style=for-the-badge" alt="Algoritmos">
  <img src="https://img.shields.io/badge/Testes-210-green?style=for-the-badge" alt="Testes">
  <img src="https://img.shields.io/badge/Perfis-7-orange?style=for-the-badge" alt="Perfis">
</p>

Este documento descreve a metodologia, processo e resultados do benchmark comparativo entre três algoritmos de caminho mínimo utilizados no Otimizador de Rotas do Campus Unifor.

---

## 📋 Índice

1. [Visão Geral](#-visão-geral)
2. [Algoritmos Comparados](#-algoritmos-comparados)
3. [Metodologia](#-metodologia)
4. [Métricas Analisadas](#-métricas-analisadas)
5. [Resultados](#-resultados)
6. [Insights e Conclusões](#-insights-e-conclusões)
7. [Como Executar](#-como-executar)
8. [Arquivos Gerados](#-arquivos-gerados)

---

## 🎯 Visão Geral

O benchmark foi desenvolvido para avaliar empiricamente o desempenho de três algoritmos de busca de caminho mínimo em um grafo real extraído do OpenStreetMap, representando a rede de caminhos pedestres do Campus da Unifor.

### Objetivos

- **Comparar performance temporal** entre os algoritmos
- **Quantificar eficiência** em termos de nós explorados
- **Avaliar comportamento** sob diferentes perfis de mobilidade
- **Validar a escolha do A*** como algoritmo principal do sistema

---

## 🔬 Algoritmos Comparados

### 1. Dijkstra Unidirecional

```
Complexidade: O((V + E) log V)
Implementação: nx.single_source_dijkstra()
```

- Expande a partir da **origem apenas**
- Explora todos os nós em ordem crescente de distância
- **Baseline** para comparação (algoritmo clássico)

### 2. Dijkstra Bidirecional

```
Complexidade: O((V + E) log V) - mas com constante menor
Implementação: nx.bidirectional_dijkstra()
```

- Expande **simultaneamente** da origem e do destino
- Termina quando as duas buscas se encontram
- Reduz área de busca pela metade (teoricamente)

### 3. A* (A-Star)

```
Complexidade: O(E) no melhor caso, O((V + E) log V) no pior
Implementação: nx.astar_path() com heurística euclidiana
```

- Usa **heurística** para guiar a busca em direção ao destino
- Função de avaliação: `f(n) = g(n) + h(n)`
  - `g(n)`: custo real do início até n
  - `h(n)`: estimativa heurística de n até o destino
- **Heurística utilizada**: Distância euclidiana (admissível)

#### Implementação da Heurística

```python
def heuristica_astar(G, no_atual, no_destino):
    """
    Calcula distância euclidiana entre dois nós.
    Heurística admissível: nunca superestima o custo real.
    """
    lat_atual, lon_atual = G.nodes[no_atual]["y"], G.nodes[no_atual]["x"]
    lat_destino, lon_destino = G.nodes[no_destino]["y"], G.nodes[no_destino]["x"]
    
    # Conversão para metros (1 grau ≈ 111km)
    metros_por_grau_lat = 111000
    metros_por_grau_lon = 111000 * math.cos(math.radians(lat_atual))
    
    delta_lat = (lat_destino - lat_atual) * metros_por_grau_lat
    delta_lon = (lon_destino - lon_atual) * metros_por_grau_lon
    
    return math.sqrt(delta_lat**2 + delta_lon**2)
```

---

## 📐 Metodologia

### Configuração do Experimento

| Parâmetro | Valor |
|-----------|-------|
| **Seed aleatória** | 42 (reprodutibilidade) |
| **Pares origem-destino** | 30 por perfil |
| **Repetições por medição** | 15 |
| **Iterações de warm-up** | 3 (descartadas) |
| **Total de testes** | 210 (30 × 7 perfis) |

### Processo de Benchmark

```
┌─────────────────────────────────────────────────────────────┐
│  1. CARREGAMENTO                                            │
│     └── Grafo OSM do Campus Unifor                          │
│     └── Pontos de Interesse (POIs)                          │
├─────────────────────────────────────────────────────────────┤
│  2. GERAÇÃO DE PARES                                        │
│     └── Seleção aleatória de 30 pares origem-destino        │
│     └── Validação de conectividade                          │
│     └── Categorização por distância (curta/média/longa)     │
├─────────────────────────────────────────────────────────────┤
│  3. ITERAÇÃO POR PERFIL                                     │
│     └── Para cada perfil de mobilidade:                     │
│         └── Ponderar grafo conforme restrições              │
│         └── Executar benchmark em todos os pares            │
├─────────────────────────────────────────────────────────────┤
│  4. MEDIÇÃO POR ALGORITMO                                   │
│     └── 3x warm-up (cache de CPU)                           │
│     └── 15x medições oficiais (time.perf_counter)           │
│     └── Cálculo de média, mediana, desvio padrão            │
│     └── Contagem de nós explorados                          │
├─────────────────────────────────────────────────────────────┤
│  5. EXPORTAÇÃO                                              │
│     └── CSV com todas as métricas                           │
│     └── JSON estruturado                                    │
│     └── Relatório Markdown                                  │
└─────────────────────────────────────────────────────────────┘
```

### Categorização de Distâncias

| Categoria | Distância Euclidiana |
|-----------|---------------------|
| **Curta** | < 200 metros |
| **Média** | 200 - 500 metros |
| **Longa** | > 500 metros |

### Perfis de Mobilidade Testados

| Perfil | Características |
|--------|----------------|
| 🚶 Adulto Sem Dificuldades | Sem restrições |
| ♿ Cadeirante | Evita escadas, requer rampas |
| 👴 Idoso | Evita inclinações acentuadas |
| 🤰 Gestante | Prioriza conforto |
| 👶 Criança/Acompanhante | Adequado para carrinhos |
| 🩼 Mobilidade Temporária | Muletas, bota ortopédica |
| 🏋️ Pessoa com Obesidade | Reduz esforço físico |

---

## 📏 Métricas Analisadas

### 1. Tempo de Execução

- **Tempo médio** (ms): Média aritmética das 15 repetições
- **Tempo mediano** (ms): Valor central das medições
- **Desvio padrão** (ms): Variabilidade das medições

### 2. Nós Explorados

Contagem implementada manualmente para cada algoritmo, simulando a execução e rastreando os nós visitados.

### 3. Speedup

```
Speedup = Tempo_Algoritmo_Base / Tempo_Algoritmo_Comparado
```

- **Speedup > 1**: Algoritmo comparado é mais rápido
- **Speedup = 1**: Desempenho igual
- **Speedup < 1**: Algoritmo comparado é mais lento

### 4. Economia de Nós (%)

```
Economia = 100 × (1 - Nós_Algoritmo_Otimizado / Nós_Algoritmo_Base)
```

---

## 📈 Resultados

### Resumo Geral

| Métrica | Valor |
|---------|-------|
| **Total de testes** | 210 |
| **Perfis testados** | 7 |
| **Taxa de sucesso** | 100% |

### Speedup Médio por Comparação

| Comparação | Speedup Médio |
|------------|---------------|
| **A* vs Dijkstra Unidirecional** | 1.10x |
| **A* vs Dijkstra Bidirecional** | 1.02x |
| **Dijkstra Bi vs Dijkstra Uni** | 1.08x |

### Tempo Médio de Execução por Algoritmo

| Algoritmo | Tempo Médio (ms) |
|-----------|------------------|
| Dijkstra Unidirecional | 5.17 |
| Dijkstra Bidirecional | 4.78 |
| A* | 4.69 |

### 🏆 Economia de Nós Explorados

| Comparação | Economia Média |
|------------|----------------|
| **A* vs Dijkstra Uni** | **66.19%** |
| **A* vs Dijkstra Bi** | **41.13%** |
| **Dijkstra Bi vs Uni** | **38.32%** |

### Análise por Categoria de Distância

#### Distâncias Curtas (< 200m)

| Comparação | Speedup |
|------------|---------|
| A* vs Dijkstra Uni | 1.06x |
| A* vs Dijkstra Bi | 1.01x |
| Dijkstra Bi vs Uni | 1.05x |

#### Distâncias Médias (200-500m)

| Comparação | Speedup |
|------------|---------|
| A* vs Dijkstra Uni | 1.12x |
| A* vs Dijkstra Bi | 1.02x |
| Dijkstra Bi vs Uni | 1.09x |

#### Distâncias Longas (> 500m)

| Comparação | Speedup |
|------------|---------|
| A* vs Dijkstra Uni | **1.13x** |
| A* vs Dijkstra Bi | 1.03x |
| Dijkstra Bi vs Uni | 1.10x |

### Desempenho por Perfil de Mobilidade

| Perfil | A*/Dij-Uni | A*/Dij-Bi | Dij-Bi/Uni |
|--------|------------|-----------|------------|
| Adulto Sem Dificuldades | 1.11x | 1.04x | 1.07x |
| Cadeirante | 1.11x | 1.03x | 1.09x |
| Criança/Acompanhante | **1.12x** | **1.04x** | 1.08x |
| Gestante | 1.10x | 1.01x | 1.09x |
| Idoso | 1.11x | 1.02x | 1.09x |
| Mobilidade Temporária | 1.10x | 1.01x | 1.09x |
| Pessoa com Obesidade | 1.08x | 1.01x | 1.07x |

---

## 💡 Insights e Conclusões

### 1. A* é Consistentemente Superior

O algoritmo A* demonstrou ser o mais eficiente em todas as métricas analisadas:

- **10% mais rápido** que Dijkstra Unidirecional
- **2% mais rápido** que Dijkstra Bidirecional
- **66% menos nós explorados** que Dijkstra Unidirecional

### 2. Heurística Euclidiana é Eficaz

A escolha da distância euclidiana como heurística provou ser adequada para o contexto do campus universitário, onde:

- A rede de caminhos é relativamente densa
- As rotas tendem a seguir direções previsíveis
- A heurística é admissível (nunca superestima)

### 3. Ganho Proporcional à Distância

O benefício do A* aumenta com a distância do percurso:

```
Curta:  1.06x speedup
Média:  1.12x speedup  (+5.7%)
Longa:  1.13x speedup  (+6.6%)
```

Isso ocorre porque a heurística tem mais oportunidades de "podar" caminhos subótimos em buscas mais longas.

### 4. Perfis de Acessibilidade Beneficiam Mais

Perfis que modificam significativamente os pesos do grafo (como Cadeirante e Criança/Acompanhante) apresentaram os melhores speedups, sugerindo que a heurística ajuda especialmente quando há muitas rotas alternativas a serem avaliadas.

### 5. Dijkstra Bidirecional: Alternativa Viável

O Dijkstra Bidirecional oferece um meio-termo interessante:

- **8% mais rápido** que a versão unidirecional
- **38% menos nós** explorados
- Não requer implementação de heurística

### 6. Validação da Escolha de Design

Os resultados validam a decisão de utilizar **A* como algoritmo principal** do sistema de rotas, especialmente considerando que:

- O campus é um ambiente geoespacial bem definido
- A heurística euclidiana é natural para coordenadas GPS
- O ganho de performance é consistente em todos os cenários

---

## 🚀 Como Executar

### Pré-requisitos

```bash
pip install networkx osmnx tqdm pandas matplotlib seaborn
```

### Executar Benchmark

```bash
python benchmark_algoritmos.py
```

### Gerar Visualizações

```bash
python visualizar_benchmark.py
```

### Parâmetros Customizáveis

```python
bench = BenchmarkTresAlgoritmos(G, pois, seed=42)

bench.executar_completo(
    num_testes=30,           # Pares origem-destino
    repeticoes=15,           # Repetições por medição
    perfis_a_testar=None     # None = todos os perfis
)
```

---

## 📁 Arquivos Gerados

### Estrutura de Saída

```
benchmark_results/
└── tres_algoritmos/
    ├── benchmark_tres_algoritmos_YYYYMMDD_HHMMSS.csv
    ├── benchmark_tres_algoritmos_YYYYMMDD_HHMMSS.json
    └── graficos/
        ├── speedup_comparativo_tres.png
        ├── tempos_absolutos.png
        ├── nos_explorados.png
        ├── boxplot_tempos.png
        ├── speedup_por_categoria.png
        ├── economia_nos.png
        └── resumo_tres_algoritmos.md
```

### Descrição dos Arquivos

| Arquivo | Descrição |
|---------|-----------|
| `*.csv` | Dados tabulares para análise externa |
| `*.json` | Dados estruturados com metadados completos |
| `speedup_comparativo_tres.png` | Gráfico de barras comparando speedups |
| `tempos_absolutos.png` | Tempos de execução por perfil |
| `nos_explorados.png` | Comparação de nós visitados |
| `boxplot_tempos.png` | Distribuição estatística dos tempos |
| `speedup_por_categoria.png` | Análise por distância |
| `economia_nos.png` | Percentual de economia de nós |
| `resumo_tres_algoritmos.md` | Relatório completo em Markdown |

---

## 📚 Referências Técnicas

- **NetworkX Documentation**: [networkx.org](https://networkx.org/)
- **OSMnx**: Boeing, G. (2017). OSMnx: New Methods for Acquiring, Constructing, Analyzing, and Visualizing Complex Street Networks.
- **A* Algorithm**: Hart, P. E., Nilsson, N. J., & Raphael, B. (1968). A Formal Basis for the Heuristic Determination of Minimum Cost Paths.

---

<p align="center">
  <i>Benchmark desenvolvido como parte do TCC em Ciência da Computação - Unifor 2025</i>
</p>
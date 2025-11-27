# 🏫 Otimizador de Rotas a Pé - Campus Unifor

Aplicação web para calcular rotas pedestres dentro do Campus da Universidade de Fortaleza (Unifor).

## 📋 Funcionalidades

- ✅ **Sistema completo de perfis de mobilidade**
- ✅ Cálculo de rotas otimizadas por perfil (velocidade, acessibilidade)
- ✅ Ponderação inteligente do grafo considerando:
  - Faixas de pedestres
  - Acessibilidade para cadeiras de rodas
  - Escadas e rampas
  - Inclinações
  - Superfície dos caminhos
- ✅ Visualização interativa no mapa com cores por perfil
- ✅ **Marcadores coloridos por categoria** (Blocos, Estacionamentos, Outros)
- ✅ **Seleção de POIs via dropdown organizado por categoria**
- ✅ **Filtro visual de categorias no mapa**
- ✅ Informações detalhadas: distância, tempo estimado e número de passos
- ✅ Exportação de rotas em formato GPX
- ✅ Interface responsiva e intuitiva
- ✅ Modo debug para desenvolvimento
- ✅ Suporte completo a acentuação (UTF-8)

## 🗂️ Estrutura do Projeto

```
unifor-rotas/
│
├── main.py                    # Arquivo principal da aplicação
├── config.py                  # Configurações e constantes
├── data_loader.py             # Carregamento de dados (grafo e POIs)
├── route_calculator.py        # Lógica de cálculo de rotas
├── graph_weighting.py         # Ponderação do grafo (acessibilidade)
├── mobility_profiles.py       # Perfis de mobilidade
├── ui_components.py           # Componentes de interface (frontend)
├── pontos de interesse.txt    # Arquivo com POIs do campus
├── requirements.txt           # Dependências Python
└── README.md                  # Este arquivo
```

## 🚀 Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/unifor-rotas.git
cd unifor-rotas
```

### 2. Crie um ambiente virtual (opcional, mas recomendado)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Crie o arquivo de POIs

Crie um arquivo chamado `pontos de interesse.txt` (note o espaço no nome) com o seguinte formato:

```
---Blocos---

Bloco A: -3.7710433466067315, -38.48121403014463
Bloco B: -3.7707209350863757, -38.48137566733775

---Outros Lugares---

Ginásio Poliesportivo: -3.7696310501219523, -38.47719764915029
Academia: -3.7699055342732146, -38.476678514470734
Biblioteca: -3.769098, -38.480532

---Estacionamentos---

Estacionamento das Placas Solares: -3.767619568400268, -38.476888140827825
Estacionamento da Reitoria: -3.769280, -38.481543
```

**Formato:**
- Categorias são definidas entre `---Nome da Categoria---`
- Cada POI segue o formato: `Nome: latitude, longitude`
- Linhas vazias são ignoradas
- Use acentuação normalmente (UTF-8)

## ▶️ Como Executar

```bash
streamlit run main.py
```

A aplicação abrirá automaticamente no navegador em `http://localhost:8501`

## 🎯 Como Usar

### Opção 1: Clique no Mapa
1. Clique em dois pontos diferentes no mapa
2. A rota será calculada automaticamente

### Opção 2: Use os Marcadores (POIs)
1. Clique em dois marcadores verdes no mapa
2. A rota entre eles será traçada

### Opção 3: Selecione via Sidebar
1. Abra a sidebar (barra lateral)
2. Selecione "Ponto de Origem" e "Ponto de Destino"
3. Clique em "Traçar Rota entre POIs"

### Limpar Seleção
- Clique no botão "🔁 Limpar seleção" para recomeçar

### Exportar Rota
- Após calcular uma rota, clique em "📥 Exportar Rota (GPX)" para baixar o arquivo

## 📦 Módulos

### `main.py`
Arquivo principal que coordena toda a aplicação. Gerencia o fluxo de execução e integra todos os módulos.

### `config.py`
Contém todas as configurações e constantes:
- Coordenadas do campus
- Centro do mapa e zoom
- Filtros OSM
- Constantes de cálculo (velocidade, tamanho do passo)

### `data_loader.py`
Responsável pelo carregamento de dados:
- `carregar_grafo()`: Carrega a rede de caminhos usando OSMnx
- `carregar_pois()`: Lê os pontos de interesse com suporte a categorias
- `validar_coordenada()`: Verifica se um ponto está dentro do campus

### `route_calculator.py`
Contém a lógica de cálculo de rotas:
- `calcular_rota()`: Calcula o caminho mais curto
- `extrair_geometria_rota()`: Extrai a geometria completa da rota
- `gerar_gpx()`: Gera arquivo GPX para exportação

### `mobility_profiles.py`
Define os perfis de mobilidade disponíveis:
- **Adulto Sem Dificuldades**: Perfil padrão, sem restrições
- **Cadeirante**: Requer acessibilidade total, evita escadas
- **Idoso**: Mobilidade reduzida, evita esforço
- **Gestante**: Conforto e segurança, evita escadas
- **Criança/Acompanhante**: Para carrinhos de bebê
- **Mobilidade Temporariamente Reduzida**: Lesões temporárias

### `graph_weighting.py`
Sistema de ponderação do grafo:
- `identificar_faixas_pedestres()`: Detecta faixas no mapa
- `calcular_peso_aresta()`: Calcula peso baseado no perfil
- `ponderar_grafo()`: Aplica ponderação a todas as arestas
- Considera: wheelchair tags, escadas, inclinações, superfície, largura

### `ui_components.py`
Componentes visuais da interface:
- `renderizar_cabecalho()`: Título e instruções com legenda de cores
- `renderizar_sidebar()`: Painel com seleção de perfil, POIs e filtros
- `renderizar_mapa()`: Mapa interativo com marcadores coloridos por perfil
- `renderizar_informacoes_rota()`: Métricas adaptadas ao perfil

## 🎨 Sistema de Cores por Categoria

- 🔵 **Azul** - Blocos Acadêmicos (ícone: casa)
- 🟢 **Verde** - Outros Lugares (ícone: info)
- 🟠 **Laranja** - Estacionamentos (ícone: carro)
- ⚫ **Cinza** - Outros (ícone: marcador)

## 🛠️ Tecnologias Utilizadas

- **Streamlit**: Framework web Python
- **OSMnx**: Download e análise de dados do OpenStreetMap
- **NetworkX**: Cálculo de rotas em grafos
- **Folium**: Mapas interativos
- **Shapely**: Operações geométricas

## 📊 Informações Técnicas

### Filtro OSM
A aplicação considera os seguintes tipos de vias:
- Footway (calçadas)
- Path (caminhos)
- Pedestrian (áreas pedestres)
- Living street (ruas residenciais de baixa velocidade)
- Residential (ruas residenciais)
- Service (vias de serviço)
- Track (trilhas)
- Steps (escadas)
- Corridor (corredores)

### Cálculos
- **Velocidade de caminhada**: 80 m/min (~4.8 km/h)
- **Tamanho do passo**: 0.75 metros
- **Algoritmo de rota**: Dijkstra (menor distância)

## 🐛 Modo Debug

Para desenvolvedores, ative o "Modo Debug" na sidebar para ver:
- Coordenadas dos cliques
- Número de pontos na rota
- Distância calculada
- Estado da sessão

## 📝 Formato do Arquivo GPX

O arquivo exportado segue o padrão GPX 1.1, compatível com:
- Google Maps
- Strava
- MapMyRun
- Garmin
- Outros apps de GPS

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para:
1. Fazer fork do projeto
2. Criar uma branch para sua feature (`git checkout -b feature/NovaFuncionalidade`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/NovaFuncionalidade`)
5. Abrir um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT.

## 👥 Autores

Desenvolvido para o Campus da Unifor.

## 📞 Suporte

Para reportar bugs ou sugerir melhorias:
- Abra uma issue no GitHub
- Entre em contato com a equipe de desenvolvimento

---

**Nota**: Esta aplicação utiliza dados do OpenStreetMap. As rotas são calculadas com base nos caminhos disponíveis no OSM e podem não refletir 100% a realidade atual do campus.
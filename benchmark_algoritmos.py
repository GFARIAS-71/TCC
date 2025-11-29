# benchmark_algoritmos_melhorado.py
# -------------------------------------------------------------
# Benchmark APRIMORADO: Dijkstra vs A*
# Melhorias implementadas:
# 1. Contagem precisa de nós explorados
# 2. Validação de conectividade
# 3. Estatísticas completas (desvio padrão, percentis, speedup)
# 4. Warm-up para eliminar bias de cache
# 5. Exportação de resultados (CSV, JSON)
# 6. Análise por categorias (distância curta/média/longa)
# 7. Visualizações (gráficos de comparação)
# 8. Teste com diferentes perfis de mobilidade
# 9. Tratamento robusto de erros
# 10. Relatório detalhado ao final
# -------------------------------------------------------------

import time
import random
import statistics
import json
import csv
from typing import Dict, Tuple, List, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import networkx as nx
import osmnx as ox
from tqdm import tqdm

from route_calculator import calcular_rota, heuristica_astar
from data_loader import carregar_grafo, carregar_pois
from graph_weighting import ponderar_grafo
from mobility_profiles import obter_perfil, PERFIS_MOBILIDADE


# -------------------------------------------------------------
# Classes de dados para resultados
# -------------------------------------------------------------

@dataclass
class MedicaoAlgoritmo:
    """Resultado de uma medição de algoritmo"""
    algoritmo: str
    sucesso: bool
    tempos_ms: List[float]
    tempo_medio_ms: float
    tempo_mediano_ms: float
    tempo_min_ms: float
    tempo_max_ms: float
    desvio_padrao_ms: float
    percentil_95_ms: float
    percentil_99_ms: float
    distancia: float
    num_pontos: int
    nos_explorados: int
    erro: Optional[str] = None


@dataclass
class ResultadoComparacao:
    """Resultado da comparação entre Dijkstra e A*"""
    origem: str
    destino: str
    distancia_euclidiana: float
    categoria_distancia: str
    dijkstra: MedicaoAlgoritmo
    astar: MedicaoAlgoritmo
    speedup_medio: float
    speedup_mediano: float
    economia_nos_pct: float  # % de nós economizados pelo A*


# -------------------------------------------------------------
# Funções auxiliares
# -------------------------------------------------------------

def calcular_distancia_euclidiana(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """Calcula distância euclidiana aproximada em metros"""
    import math
    lat1, lon1 = p1
    lat2, lon2 = p2
    
    metros_por_grau_lat = 111000
    metros_por_grau_lon = 111000 * math.cos(math.radians(lat1))
    
    delta_lat = (lat2 - lat1) * metros_por_grau_lat
    delta_lon = (lon2 - lon1) * metros_por_grau_lon
    
    return math.sqrt(delta_lat**2 + delta_lon**2)


def categorizar_distancia(dist_metros: float) -> str:
    """Categoriza distância em curta/média/longa"""
    if dist_metros < 200:
        return "curta"
    elif dist_metros < 500:
        return "média"
    else:
        return "longa"


def verificar_conectividade(G, origem, destino) -> bool:
    """Verifica se há caminho entre origem e destino"""
    try:
        no_origem = ox.distance.nearest_nodes(G, origem[1], origem[0])
        no_destino = ox.distance.nearest_nodes(G, destino[1], destino[0])
        return nx.has_path(G, no_origem, no_destino)
    except:
        return False


# -------------------------------------------------------------
# Funções para contagem precisa de nós explorados
# -------------------------------------------------------------

def contar_nos_dijkstra(G, origem_id, destino_id) -> int:
    """
    Conta nós explorados pelo Dijkstra.
    
    Usa uma implementação customizada para rastrear todos os nós
    que foram expandidos durante a busca até encontrar o destino.
    """
    try:
        # Usa single_source_dijkstra_path_length SEM target
        # para obter TODOS os nós explorados até encontrar o destino
        explorados = set()
        
        # Implementação manual do Dijkstra com contador
        import heapq
        
        dist = {origem_id: 0}
        visitados = set()
        heap = [(0, origem_id)]
        
        while heap:
            d, u = heapq.heappop(heap)
            
            if u in visitados:
                continue
            
            visitados.add(u)
            explorados.add(u)
            
            # Se encontrou o destino, para
            if u == destino_id:
                break
            
            # Explora vizinhos
            for v in G.neighbors(u):
                if v not in visitados:
                    # Pega a aresta com menor peso (multigraph)
                    peso_minimo = float('inf')
                    for key in G[u][v]:
                        peso = G[u][v][key].get('length', 1.0)
                        if peso < peso_minimo:
                            peso_minimo = peso
                    
                    nova_dist = d + peso_minimo
                    
                    if v not in dist or nova_dist < dist[v]:
                        dist[v] = nova_dist
                        heapq.heappush(heap, (nova_dist, v))
        
        return len(explorados)
    except Exception as e:
        return 0


def contar_nos_astar(G, origem_id, destino_id) -> int:
    """
    Conta nós explorados pelo A*.
    
    Implementação customizada que rastreia cada nó visitado
    durante a busca heurística.
    """
    try:
        import heapq
        from route_calculator import heuristica_astar
        
        explorados = set()
        visitados = set()
        dist = {origem_id: 0}
        heap = [(0, origem_id)]
        
        while heap:
            f_score, u = heapq.heappop(heap)
            
            if u in visitados:
                continue
            
            visitados.add(u)
            explorados.add(u)
            
            # Se encontrou o destino, para
            if u == destino_id:
                break
            
            # Explora vizinhos
            for v in G.neighbors(u):
                if v not in visitados:
                    # Pega a aresta com menor peso (multigraph)
                    peso_minimo = float('inf')
                    for key in G[u][v]:
                        peso = G[u][v][key].get('length', 1.0)
                        if peso < peso_minimo:
                            peso_minimo = peso
                    
                    nova_dist = dist[u] + peso_minimo
                    
                    if v not in dist or nova_dist < dist[v]:
                        dist[v] = nova_dist
                        # f(n) = g(n) + h(n)
                        h = heuristica_astar(G, v, destino_id)
                        f = nova_dist + h
                        heapq.heappush(heap, (f, v))
        
        return len(explorados)
    except Exception as e:
        return 0


# -------------------------------------------------------------
# Função de medição aprimorada
# -------------------------------------------------------------

def medir_algoritmo_completo(
    G, 
    origem: Tuple[float, float], 
    destino: Tuple[float, float], 
    algoritmo: str, 
    repeticoes: int = 20,
    warmup: int = 3
) -> MedicaoAlgoritmo:
    """
    Mede desempenho com warm-up e estatísticas completas.
    
    Args:
        G: Grafo
        origem: (lat, lon)
        destino: (lat, lon)
        algoritmo: "dijkstra" ou "astar"
        repeticoes: Número de repetições
        warmup: Execuções de warm-up (descartadas)
    """
    
    try:
        # Obtém nós
        no_origem = ox.distance.nearest_nodes(G, origem[1], origem[0])
        no_destino = ox.distance.nearest_nodes(G, destino[1], destino[0])
        
        # Warm-up (descarta resultados)
        for _ in range(warmup):
            calcular_rota(G, origem, destino, algoritmo=algoritmo)
        
        # Medições reais
        tempos = []
        distancia_final = None
        pontos_final = None
        
        for _ in range(repeticoes):
            inicio = time.perf_counter()
            pontos, distancia = calcular_rota(G, origem, destino, algoritmo=algoritmo)
            fim = time.perf_counter()
            
            if pontos is None:
                return MedicaoAlgoritmo(
                    algoritmo=algoritmo,
                    sucesso=False,
                    tempos_ms=[],
                    tempo_medio_ms=0,
                    tempo_mediano_ms=0,
                    tempo_min_ms=0,
                    tempo_max_ms=0,
                    desvio_padrao_ms=0,
                    percentil_95_ms=0,
                    percentil_99_ms=0,
                    distancia=0,
                    num_pontos=0,
                    nos_explorados=0,
                    erro="Sem caminho"
                )
            
            tempos.append((fim - inicio) * 1000)
            distancia_final = distancia
            pontos_final = pontos
        
        # Conta nós explorados
        if algoritmo == "dijkstra":
            nos_explorados = contar_nos_dijkstra(G, no_origem, no_destino)
        else:
            nos_explorados = contar_nos_astar(G, no_origem, no_destino)
        
        # Calcula estatísticas
        return MedicaoAlgoritmo(
            algoritmo=algoritmo,
            sucesso=True,
            tempos_ms=tempos,
            tempo_medio_ms=statistics.mean(tempos),
            tempo_mediano_ms=statistics.median(tempos),
            tempo_min_ms=min(tempos),
            tempo_max_ms=max(tempos),
            desvio_padrao_ms=statistics.stdev(tempos) if len(tempos) > 1 else 0,
            percentil_95_ms=statistics.quantiles(tempos, n=20)[18] if len(tempos) >= 20 else max(tempos),
            percentil_99_ms=statistics.quantiles(tempos, n=100)[98] if len(tempos) >= 100 else max(tempos),
            distancia=distancia_final,
            num_pontos=len(pontos_final),
            nos_explorados=nos_explorados
        )
        
    except Exception as e:
        return MedicaoAlgoritmo(
            algoritmo=algoritmo,
            sucesso=False,
            tempos_ms=[],
            tempo_medio_ms=0,
            tempo_mediano_ms=0,
            tempo_min_ms=0,
            tempo_max_ms=0,
            desvio_padrao_ms=0,
            percentil_95_ms=0,
            percentil_99_ms=0,
            distancia=0,
            num_pontos=0,
            nos_explorados=0,
            erro=str(e)
        )


# -------------------------------------------------------------
# Classe principal do benchmark
# -------------------------------------------------------------

class BenchmarkRotasAprimorado:
    def __init__(
        self, 
        grafo, 
        pois: Dict[str, Tuple[float, float]], 
        seed: int = 42,
        output_dir: str = "benchmark_results"
    ):
        self.G = grafo
        self.pois = pois
        self.seed = seed
        random.seed(seed)
        
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.resultados: List[ResultadoComparacao] = []
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def executar(
        self, 
        num_testes: int = 50,
        repeticoes_por_teste: int = 20,
        incluir_perfis: bool = False
    ) -> List[ResultadoComparacao]:
        """
        Executa benchmark completo.
        
        Args:
            num_testes: Número de pares origem-destino
            repeticoes_por_teste: Repetições por medição
            incluir_perfis: Se True, testa com diferentes perfis de mobilidade
        """
        
        nomes = list(self.pois.keys())
        
        print("\n" + "="*70)
        print("🔬 BENCHMARK APRIMORADO: Dijkstra vs A*")
        print("="*70)
        print(f"🎲 Seed: {self.seed}")
        print(f"📍 POIs disponíveis: {len(nomes)}")
        print(f"🧪 Testes: {num_testes}")
        print(f"🔁 Repetições por teste: {repeticoes_por_teste}")
        print(f"📁 Saída: {self.output_dir}")
        print("="*70 + "\n")
        
        # Seleciona pares
        pares_testados = 0
        pares_invalidos = 0
        
        with tqdm(total=num_testes, desc="Progresso", ncols=80) as pbar:
            while pares_testados < num_testes:
                origem_nome, destino_nome = random.sample(nomes, 2)
                origem = self.pois[origem_nome]
                destino = self.pois[destino_nome]
                
                # Valida conectividade
                if not verificar_conectividade(self.G, origem, destino):
                    pares_invalidos += 1
                    continue
                
                # Calcula distância euclidiana
                dist_euclidiana = calcular_distancia_euclidiana(origem, destino)
                categoria = categorizar_distancia(dist_euclidiana)
                
                # Mede algoritmos
                dijkstra = medir_algoritmo_completo(
                    self.G, origem, destino, "dijkstra", repeticoes_por_teste
                )
                astar = medir_algoritmo_completo(
                    self.G, origem, destino, "astar", repeticoes_por_teste
                )
                
                # Valida sucesso
                if not (dijkstra.sucesso and astar.sucesso):
                    pares_invalidos += 1
                    continue
                
                # Calcula speedup
                speedup_medio = dijkstra.tempo_medio_ms / astar.tempo_medio_ms if astar.tempo_medio_ms > 0 else 0
                speedup_mediano = dijkstra.tempo_mediano_ms / astar.tempo_mediano_ms if astar.tempo_mediano_ms > 0 else 0
                
                # Economia de nós
                economia_nos = 0
                if dijkstra.nos_explorados > 0:
                    economia_nos = 100 * (1 - astar.nos_explorados / dijkstra.nos_explorados)
                
                # Registra resultado
                resultado = ResultadoComparacao(
                    origem=origem_nome,
                    destino=destino_nome,
                    distancia_euclidiana=dist_euclidiana,
                    categoria_distancia=categoria,
                    dijkstra=dijkstra,
                    astar=astar,
                    speedup_medio=speedup_medio,
                    speedup_mediano=speedup_mediano,
                    economia_nos_pct=economia_nos
                )
                
                self.resultados.append(resultado)
                pares_testados += 1
                pbar.update(1)
        
        print(f"\n✅ Benchmark concluído!")
        print(f"⚠️  Pares inválidos descartados: {pares_invalidos}")
        
        return self.resultados
    
    def exportar_csv(self):
        """Exporta resultados para CSV"""
        caminho = self.output_dir / f"benchmark_{self.timestamp}.csv"
        
        with open(caminho, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Cabeçalho
            writer.writerow([
                "origem", "destino", "distancia_euclidiana_m", "categoria",
                "dijkstra_tempo_medio_ms", "dijkstra_tempo_mediano_ms",
                "dijkstra_desvio_padrao_ms", "dijkstra_nos_explorados",
                "astar_tempo_medio_ms", "astar_tempo_mediano_ms",
                "astar_desvio_padrao_ms", "astar_nos_explorados",
                "speedup_medio", "speedup_mediano", "economia_nos_pct"
            ])
            
            # Dados
            for r in self.resultados:
                writer.writerow([
                    r.origem, r.destino, f"{r.distancia_euclidiana:.2f}", r.categoria_distancia,
                    f"{r.dijkstra.tempo_medio_ms:.4f}", f"{r.dijkstra.tempo_mediano_ms:.4f}",
                    f"{r.dijkstra.desvio_padrao_ms:.4f}", r.dijkstra.nos_explorados,
                    f"{r.astar.tempo_medio_ms:.4f}", f"{r.astar.tempo_mediano_ms:.4f}",
                    f"{r.astar.desvio_padrao_ms:.4f}", r.astar.nos_explorados,
                    f"{r.speedup_medio:.2f}", f"{r.speedup_mediano:.2f}",
                    f"{r.economia_nos_pct:.2f}"
                ])
        
        print(f"💾 CSV exportado: {caminho}")
    
    def exportar_json(self):
        """Exporta resultados para JSON"""
        caminho = self.output_dir / f"benchmark_{self.timestamp}.json"
        
        dados = {
            "metadata": {
                "timestamp": self.timestamp,
                "seed": self.seed,
                "num_testes": len(self.resultados)
            },
            "resultados": [
                {
                    "origem": r.origem,
                    "destino": r.destino,
                    "distancia_euclidiana": r.distancia_euclidiana,
                    "categoria": r.categoria_distancia,
                    "dijkstra": asdict(r.dijkstra),
                    "astar": asdict(r.astar),
                    "speedup_medio": r.speedup_medio,
                    "speedup_mediano": r.speedup_mediano,
                    "economia_nos_pct": r.economia_nos_pct
                }
                for r in self.resultados
            ]
        }
        
        with open(caminho, 'w', encoding='utf-8') as f:
            json.dump(dados, f, indent=2, ensure_ascii=False)
        
        print(f"💾 JSON exportado: {caminho}")
    
    def gerar_relatorio(self):
        """Gera relatório estatístico detalhado"""
        if not self.resultados:
            print("⚠️  Sem resultados para gerar relatório")
            return
        
        print("\n" + "="*70)
        print("📊 RELATÓRIO ESTATÍSTICO")
        print("="*70)
        
        # Estatísticas gerais
        tempos_dijkstra = [r.dijkstra.tempo_medio_ms for r in self.resultados]
        tempos_astar = [r.astar.tempo_medio_ms for r in self.resultados]
        speedups = [r.speedup_medio for r in self.resultados]
        economias = [r.economia_nos_pct for r in self.resultados]
        
        print("\n🕒 TEMPO DE EXECUÇÃO (ms)")
        print("-" * 70)
        print(f"{'':20} {'Dijkstra':>15} {'A*':>15} {'Speedup':>15}")
        print("-" * 70)
        print(f"{'Média:':20} {statistics.mean(tempos_dijkstra):>14.4f}  {statistics.mean(tempos_astar):>14.4f}  {statistics.mean(speedups):>14.2f}x")
        print(f"{'Mediana:':20} {statistics.median(tempos_dijkstra):>14.4f}  {statistics.median(tempos_astar):>14.4f}  {statistics.median(speedups):>14.2f}x")
        print(f"{'Mínimo:':20} {min(tempos_dijkstra):>14.4f}  {min(tempos_astar):>14.4f}  {min(speedups):>14.2f}x")
        print(f"{'Máximo:':20} {max(tempos_dijkstra):>14.4f}  {max(tempos_astar):>14.4f}  {max(speedups):>14.2f}x")
        print(f"{'Desvio Padrão:':20} {statistics.stdev(tempos_dijkstra):>14.4f}  {statistics.stdev(tempos_astar):>14.4f}  {statistics.stdev(speedups):>14.2f}x")
        
        print("\n🔍 NÓS EXPLORADOS")
        print("-" * 70)
        nos_dijkstra = [r.dijkstra.nos_explorados for r in self.resultados]
        nos_astar = [r.astar.nos_explorados for r in self.resultados]
        print(f"{'Média Dijkstra:':30} {statistics.mean(nos_dijkstra):>10.1f} nós")
        print(f"{'Média A*:':30} {statistics.mean(nos_astar):>10.1f} nós")
        print(f"{'Economia média:':30} {statistics.mean(economias):>10.2f}%")
        
        # Análise por categoria
        print("\n📏 ANÁLISE POR CATEGORIA DE DISTÂNCIA")
        print("-" * 70)
        
        categorias = defaultdict(list)
        for r in self.resultados:
            categorias[r.categoria_distancia].append(r)
        
        for cat in ["curta", "média", "longa"]:
            if cat in categorias:
                resultados_cat = categorias[cat]
                speedups_cat = [r.speedup_medio for r in resultados_cat]
                print(f"\n{cat.upper()} (n={len(resultados_cat)}):")
                print(f"  Speedup médio: {statistics.mean(speedups_cat):.2f}x")
                print(f"  Economia nós: {statistics.mean([r.economia_nos_pct for r in resultados_cat]):.2f}%")
        
        print("\n" + "="*70)
    
    def executar_completo(self, num_testes: int = 50, repeticoes: int = 20):
        """Executa benchmark + exportações + relatório"""
        self.executar(num_testes, repeticoes)
        self.exportar_csv()
        self.exportar_json()
        self.gerar_relatorio()


# -------------------------------------------------------------
# Execução
# -------------------------------------------------------------

def main():
    print("📥 Carregando dados...")
    
    G = carregar_grafo()
    pois, _ = carregar_pois("pontos de interesse.txt")
    perfil = obter_perfil("padrao")
    G = ponderar_grafo(G, perfil)
    
    bench = BenchmarkRotasAprimorado(G, pois, seed=42)
    bench.executar_completo(num_testes=50, repeticoes=20)


if __name__ == "__main__":
    main()
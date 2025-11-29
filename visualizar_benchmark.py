# visualizar_benchmark.py
# -------------------------------------------------------------
# Gera gráficos e visualizações a partir dos resultados do benchmark
# -------------------------------------------------------------

import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime

# Configuração de estilo
sns.set_theme(style="whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 10


class VisualizadorBenchmark:
    def __init__(self, arquivo_json: str):
        """
        Args:
            arquivo_json: Caminho para o arquivo JSON do benchmark
        """
        with open(arquivo_json, 'r', encoding='utf-8') as f:
            self.dados = json.load(f)
        
        self.df = self._processar_dados()
        self.output_dir = Path("benchmark_results/graficos")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _processar_dados(self) -> pd.DataFrame:
        """Converte JSON para DataFrame do pandas"""
        registros = []
        
        for r in self.dados['resultados']:
            registros.append({
                'origem': r['origem'],
                'destino': r['destino'],
                'distancia_m': r['distancia_euclidiana'],
                'categoria': r['categoria'],
                'dijkstra_tempo_ms': r['dijkstra']['tempo_medio_ms'],
                'astar_tempo_ms': r['astar']['tempo_medio_ms'],
                'dijkstra_nos': r['dijkstra']['nos_explorados'],
                'astar_nos': r['astar']['nos_explorados'],
                'speedup': r['speedup_medio'],
                'economia_nos_pct': r['economia_nos_pct']
            })
        
        return pd.DataFrame(registros)
    
    def plot_comparacao_tempos(self):
        """Gráfico de barras: tempo médio Dijkstra vs A*"""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        categorias = self.df.groupby('categoria').agg({
            'dijkstra_tempo_ms': 'mean',
            'astar_tempo_ms': 'mean'
        }).reset_index()
        
        x = range(len(categorias))
        width = 0.35
        
        ax.bar([i - width/2 for i in x], categorias['dijkstra_tempo_ms'], 
               width, label='Dijkstra', color='#FF6B6B', alpha=0.8)
        ax.bar([i + width/2 for i in x], categorias['astar_tempo_ms'], 
               width, label='A*', color='#4ECDC4', alpha=0.8)
        
        ax.set_xlabel('Categoria de Distância')
        ax.set_ylabel('Tempo Médio (ms)')
        ax.set_title('Comparação de Tempo de Execução: Dijkstra vs A*')
        ax.set_xticks(x)
        ax.set_xticklabels(categorias['categoria'])
        ax.legend()
        ax.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'comparacao_tempos.png', dpi=300)
        print(f"✅ Gráfico salvo: comparacao_tempos.png")
        plt.close()
    
    def plot_speedup_distribuicao(self):
        """Histograma e boxplot do speedup"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        
        # Histograma
        ax1.hist(self.df['speedup'], bins=20, color='#95E1D3', 
                 edgecolor='black', alpha=0.7)
        ax1.axvline(self.df['speedup'].mean(), color='red', 
                    linestyle='--', linewidth=2, label=f'Média: {self.df["speedup"].mean():.2f}x')
        ax1.axvline(self.df['speedup'].median(), color='blue', 
                    linestyle='--', linewidth=2, label=f'Mediana: {self.df["speedup"].median():.2f}x')
        ax1.set_xlabel('Speedup (x)')
        ax1.set_ylabel('Frequência')
        ax1.set_title('Distribuição do Speedup (A* / Dijkstra)')
        ax1.legend()
        ax1.grid(axis='y', alpha=0.3)
        
        # Boxplot por categoria
        self.df.boxplot(column='speedup', by='categoria', ax=ax2)
        ax2.set_xlabel('Categoria de Distância')
        ax2.set_ylabel('Speedup (x)')
        ax2.set_title('Speedup por Categoria')
        ax2.get_figure().suptitle('')  # Remove título padrão do pandas
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'speedup_distribuicao.png', dpi=300)
        print(f"✅ Gráfico salvo: speedup_distribuicao.png")
        plt.close()
    
    def plot_nos_explorados(self):
        """Scatter plot: nós explorados Dijkstra vs A*"""
        fig, ax = plt.subplots(figsize=(10, 8))
        
        cores_categoria = {
            'curta': '#FF6B6B',
            'média': '#4ECDC4',
            'longa': '#95E1D3'
        }
        
        for cat, cor in cores_categoria.items():
            mask = self.df['categoria'] == cat
            ax.scatter(
                self.df.loc[mask, 'dijkstra_nos'],
                self.df.loc[mask, 'astar_nos'],
                c=cor, label=cat.capitalize(), alpha=0.6, s=100
            )
        
        # Linha y=x (paridade)
        max_nos = max(self.df['dijkstra_nos'].max(), self.df['astar_nos'].max())
        ax.plot([0, max_nos], [0, max_nos], 'k--', alpha=0.3, label='Paridade (y=x)')
        
        ax.set_xlabel('Nós Explorados - Dijkstra')
        ax.set_ylabel('Nós Explorados - A*')
        ax.set_title('Comparação de Nós Explorados')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'nos_explorados.png', dpi=300)
        print(f"✅ Gráfico salvo: nos_explorados.png")
        plt.close()
    
    def plot_economia_nos(self):
        """Gráfico de barras: economia de nós por categoria"""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        economia_media = self.df.groupby('categoria')['economia_nos_pct'].mean().sort_values()
        
        cores = ['#95E1D3' if x > 0 else '#FF6B6B' for x in economia_media]
        
        economia_media.plot(kind='barh', ax=ax, color=cores, alpha=0.8)
        
        ax.set_xlabel('Economia Média de Nós (%)')
        ax.set_ylabel('Categoria')
        ax.set_title('Economia de Nós Explorados pelo A*')
        ax.axvline(0, color='black', linewidth=0.8)
        ax.grid(axis='x', alpha=0.3)
        
        # Adiciona valores nas barras
        for i, v in enumerate(economia_media):
            ax.text(v + 1, i, f'{v:.1f}%', va='center')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'economia_nos.png', dpi=300)
        print(f"✅ Gráfico salvo: economia_nos.png")
        plt.close()
    
    def plot_tempo_vs_distancia(self):
        """Scatter plot: tempo vs distância"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        
        # Dijkstra
        ax1.scatter(self.df['distancia_m'], self.df['dijkstra_tempo_ms'], 
                   c='#FF6B6B', alpha=0.5, s=50)
        ax1.set_xlabel('Distância Euclidiana (m)')
        ax1.set_ylabel('Tempo (ms)')
        ax1.set_title('Dijkstra: Tempo vs Distância')
        ax1.grid(True, alpha=0.3)
        
        # A*
        ax2.scatter(self.df['distancia_m'], self.df['astar_tempo_ms'], 
                   c='#4ECDC4', alpha=0.5, s=50)
        ax2.set_xlabel('Distância Euclidiana (m)')
        ax2.set_ylabel('Tempo (ms)')
        ax2.set_title('A*: Tempo vs Distância')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'tempo_vs_distancia.png', dpi=300)
        print(f"✅ Gráfico salvo: tempo_vs_distancia.png")
        plt.close()
    
    def gerar_tabela_resumo(self):
        """Gera tabela resumo em markdown"""
        resumo = self.df.groupby('categoria').agg({
            'dijkstra_tempo_ms': ['mean', 'std'],
            'astar_tempo_ms': ['mean', 'std'],
            'speedup': ['mean', 'median', 'min', 'max'],
            'economia_nos_pct': 'mean'
        }).round(2)
        
        caminho = self.output_dir / 'resumo.md'
        
        with open(caminho, 'w', encoding='utf-8') as f:
            f.write("# Resumo do Benchmark: Dijkstra vs A*\n\n")
            f.write(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"Total de testes: {len(self.df)}\n\n")
            
            f.write("## Estatísticas por Categoria\n\n")
            f.write(resumo.to_markdown())
            f.write("\n\n")
            
            f.write("## Métricas Gerais\n\n")
            f.write(f"- **Speedup médio geral**: {self.df['speedup'].mean():.2f}x\n")
            f.write(f"- **Speedup mediano**: {self.df['speedup'].median():.2f}x\n")
            f.write(f"- **Economia média de nós**: {self.df['economia_nos_pct'].mean():.2f}%\n")
            f.write(f"- **Melhor speedup**: {self.df['speedup'].max():.2f}x\n")
            f.write(f"- **Pior speedup**: {self.df['speedup'].min():.2f}x\n")
        
        print(f"✅ Resumo salvo: resumo.md")
    
    def gerar_todos_graficos(self):
        """Gera todos os gráficos de uma vez"""
        print("\n📊 Gerando visualizações...")
        print("-" * 50)
        
        self.plot_comparacao_tempos()
        self.plot_speedup_distribuicao()
        self.plot_nos_explorados()
        self.plot_economia_nos()
        self.plot_tempo_vs_distancia()
        self.gerar_tabela_resumo()
        
        print("-" * 50)
        print(f"✅ Todos os gráficos foram salvos em: {self.output_dir}")


# -------------------------------------------------------------
# Execução
# -------------------------------------------------------------

def main():
    import sys
    from glob import glob
    
    # Procura o arquivo JSON mais recente
    arquivos = sorted(glob("benchmark_results/benchmark_*.json"))
    
    if not arquivos:
        print("❌ Nenhum arquivo de benchmark encontrado!")
        print("Execute primeiro: python benchmark_algoritmos_melhorado.py")
        return
    
    arquivo = arquivos[-1] if len(sys.argv) < 2 else sys.argv[1]
    
    print(f"📂 Carregando: {arquivo}")
    
    viz = VisualizadorBenchmark(arquivo)
    viz.gerar_todos_graficos()


if __name__ == "__main__":
    main()
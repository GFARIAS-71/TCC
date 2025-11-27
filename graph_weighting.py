# graph_weighting.py - PONDERAÇÃO DO GRAFO PARA ACESSIBILIDADE

import networkx as nx
import osmnx as ox
from mobility_profiles import MobilityProfile
import streamlit as st


def identificar_faixas_pedestres(G):
    """
    Identifica nós que são faixas de pedestres no grafo.
    
    Faixas são identificadas por:
    - crossing=yes ou crossing=marked ou crossing=zebra
    - highway=crossing
    
    Args:
        G: Grafo NetworkX
        
    Returns:
        Set com IDs dos nós que são faixas
    """
    faixas = set()
    
    for node_id, data in G.nodes(data=True):
        # Verifica tags do OSM
        if data.get('crossing') in ['yes', 'marked', 'zebra', 'traffic_signals']:
            faixas.add(node_id)
        elif data.get('highway') == 'crossing':
            faixas.add(node_id)
    
    return faixas


def calcular_peso_aresta(G, u, v, key, perfil: MobilityProfile, faixas_pedestres: set):
    """
    Calcula o peso de uma aresta baseado no perfil de mobilidade.
    
    Args:
        G: Grafo NetworkX
        u, v: Nós origem e destino da aresta
        key: Chave da aresta (para multigrafos)
        perfil: Perfil de mobilidade do usuário
        faixas_pedestres: Set de nós que são faixas de pedestres
        
    Returns:
        float: Peso ajustado da aresta
    """
    # Pega dados da aresta
    edge_data = G[u][v][key]
    
    # Começa com a distância física (já existe no grafo OSM)
    peso_base = edge_data.get('length', 1.0)
    
    # Fator multiplicador (inicia em 1.0)
    fator_penalizacao = 1.0
    
    # 1. VERIFICA ACESSIBILIDADE PARA CADEIRAS DE RODAS
    wheelchair_tag = edge_data.get('wheelchair', None)
    
    if wheelchair_tag == 'no' and perfil.requer_acessibilidade:
        # Caminho explicitamente NÃO acessível
        fator_penalizacao *= perfil.penalizacao_sem_rampa
    
    elif wheelchair_tag == 'limited':
        # Acessibilidade limitada
        fator_penalizacao *= (perfil.penalizacao_sem_rampa * 0.5)
    
    # 2. VERIFICA PRESENÇA DE ESCADAS
    highway_type = edge_data.get('highway', '')
    
    if highway_type == 'steps':
        # É uma escada
        fator_penalizacao *= perfil.penalizacao_escadas
    
    # 3. VERIFICA INCLINAÇÃO (se disponível)
    incline = edge_data.get('incline', None)
    
    if incline:
        try:
            # Tenta extrair valor numérico da inclinação
            if isinstance(incline, str):
                incline = incline.replace('%', '').strip()
                incline_valor = abs(float(incline))
            else:
                incline_valor = abs(float(incline))
            
            # Se inclinação > 5%, penaliza
            if incline_valor > 5.0:
                fator_penalizacao *= perfil.penalizacao_inclinacao
                
        except (ValueError, TypeError):
            # Se não conseguir converter, ignora
            pass
    
    # 4. VERIFICA PRESENÇA DE RAMPA
    if 'ramp' in highway_type or edge_data.get('ramp') == 'yes':
        # Tem rampa - REDUZ penalização para perfis que precisam
        if perfil.requer_acessibilidade:
            fator_penalizacao *= 0.7  # Incentiva uso de rampas
    
    # 5. VERIFICA CRUZAMENTOS COM FAIXAS DE PEDESTRES
    if perfil.prefere_faixas:
        # Verifica se algum dos nós extremos é uma faixa
        tem_faixa_inicio = u in faixas_pedestres
        tem_faixa_fim = v in faixas_pedestres
        
        if not tem_faixa_inicio and not tem_faixa_fim:
            # Não há faixa próxima - penaliza
            fator_penalizacao *= perfil.penalizacao_sem_faixa
        else:
            # Tem faixa - INCENTIVA
            fator_penalizacao *= 0.8
    
    # 6. VERIFICA TIPO DE SUPERFÍCIE
    surface = edge_data.get('surface', '')
    
    if perfil.requer_acessibilidade:
        # Superfícies irregulares são ruins para mobilidade reduzida
        if surface in ['unpaved', 'gravel', 'dirt', 'grass', 'sand']:
            fator_penalizacao *= 2.0
        elif surface in ['paved', 'asphalt', 'concrete']:
            fator_penalizacao *= 0.9  # Superfície boa
    
    # 7. LARGURA DO CAMINHO
    width = edge_data.get('width', None)
    
    if width and perfil.requer_acessibilidade:
        try:
            if isinstance(width, str):
                width = width.replace('m', '').strip()
                width_valor = float(width)
            else:
                width_valor = float(width)
            
            # Caminhos muito estreitos são ruins para cadeiras
            if width_valor < 1.5:  # Menos de 1.5m
                fator_penalizacao *= 1.5
                
        except (ValueError, TypeError):
            pass
    
    # Peso final = distância * fator de penalização
    peso_final = peso_base * fator_penalizacao
    
    return peso_final


def ponderar_grafo(G, perfil: MobilityProfile):
    """
    Pondera todas as arestas do grafo baseado no perfil de mobilidade.
    
    Args:
        G: Grafo NetworkX (será modificado in-place)
        perfil: Perfil de mobilidade do usuário
        
    Returns:
        G: Grafo ponderado
    """
    # Identifica faixas de pedestres
    faixas_pedestres = identificar_faixas_pedestres(G)
    
    # Contador de modificações
    arestas_penalizadas = 0
    
    # Percorre todas as arestas
    for u, v, key in G.edges(keys=True):
        # Calcula peso customizado
        peso_customizado = calcular_peso_aresta(G, u, v, key, perfil, faixas_pedestres)
        
        # Armazena peso original se ainda não existe
        if 'length_original' not in G[u][v][key]:
            G[u][v][key]['length_original'] = G[u][v][key].get('length', 1.0)
        
        # Atualiza com peso customizado
        G[u][v][key]['length'] = peso_customizado
        
        # Conta se houve penalização significativa
        if peso_customizado > G[u][v][key]['length_original'] * 1.5:
            arestas_penalizadas += 1
    
    # Informações de debug
    if st.session_state.get("debug_mode", False):
        st.info(f"""
        **Ponderação do Grafo:**
        - Perfil: {perfil.nome}
        - Faixas identificadas: {len(faixas_pedestres)}
        - Arestas penalizadas: {arestas_penalizadas}
        """)
    
    return G


def restaurar_pesos_originais(G):
    """
    Restaura os pesos originais das arestas (remove ponderações).
    
    Args:
        G: Grafo NetworkX
        
    Returns:
        G: Grafo com pesos restaurados
    """
    for u, v, key in G.edges(keys=True):
        if 'length_original' in G[u][v][key]:
            G[u][v][key]['length'] = G[u][v][key]['length_original']
    
    return G
# main.py - APLICAÇÃO PRINCIPAL

import streamlit as st
from config import configurar_pagina, inicializar_estado
from data_loader import carregar_grafo, carregar_pois
from ui_components import (
    renderizar_cabecalho,
    renderizar_sidebar,
    renderizar_mapa,
    renderizar_informacoes_rota
)
from route_calculator import calcular_rota_completa

# --- Configuração inicial ---
configurar_pagina()
inicializar_estado()

# --- Carregar dados ---
G = carregar_grafo()
pontos, categorias = carregar_pois("pontos de interesse.txt")

# --- Interface ---
renderizar_cabecalho()

# Sidebar com controles
acao_sidebar = renderizar_sidebar(G, pontos, categorias)

# Processa ações da sidebar (seleção de POIs)
if acao_sidebar:
    st.session_state["clicks"] = acao_sidebar
    st.session_state["rota"] = []
    st.session_state["distancia"] = None
    st.rerun()

# Botão limpar
if st.button("🔁 Limpar seleção", use_container_width=True):
    st.session_state["clicks"].clear()
    st.session_state["rota"].clear()
    st.session_state["distancia"] = None
    st.rerun()

# --- Renderizar mapa ---
map_data = renderizar_mapa(pontos, categorias)

# --- Captura de cliques ---
if map_data:
    clicked = map_data.get("last_clicked") or map_data.get("last_object_clicked")
    
    if clicked and len(st.session_state["clicks"]) < 2:
        nova_coord = (clicked["lat"], clicked["lng"])
        
        # Evita duplicatas
        if not st.session_state["clicks"] or st.session_state["clicks"][-1] != nova_coord:
            st.session_state["clicks"].append(nova_coord)
            st.rerun()

# --- Calcula rota ---
if len(st.session_state["clicks"]) == 2 and not st.session_state["rota"]:
    origem = st.session_state["clicks"][0]
    destino = st.session_state["clicks"][1]
    
    pontos_rota, distancia = calcular_rota_completa(G, origem, destino)
    
    if pontos_rota and distancia:
        st.session_state["rota"] = pontos_rota
        st.session_state["distancia"] = distancia
        st.rerun()

# --- Exibe informações da rota ---
renderizar_informacoes_rota()
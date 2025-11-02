import osmnx as ox
from shapely.geometry import Polygon

# Coordenadas do polígono (em formato (lon, lat))
coords = [
    (-38.481661, -3.771271),
    (-38.482034, -3.768190),
    (-38.480789, -3.768051),
    (-38.480912, -3.766418),
    (-38.477034, -3.766084),
    (-38.476956, -3.766911),
    (-38.476444, -3.766839),
    (-38.475435, -3.766550),
    (-38.473797, -3.766980),
    (-38.473748, -3.768062),
    (-38.473145, -3.768340),
    (-38.474609, -3.770682),
    (-38.481661, -3.771271)  # fecha o polígono
]

poly = Polygon(coords)

# 1. Baixar rede viária de pedestres (ruas internas, calçadas, caminhos)
G = ox.graph_from_polygon(poly, network_type="walk")

# 2. Converter para GeoDataFrames (arestas e nós)
nodes, edges = ox.graph_to_gdfs(G)

# 3. Baixar amenities (POIs)
tags = {
    "amenity": True, 
    "building": True,
    "highway": True,
    "wheelchair": True,
    "elevator": True,
    "incline": True,
    "kerb": True,
    "surface": True,
    "smoothness": True,
    "entrance": True,
}
pois = ox.geometries_from_polygon(poly, tags)

print(nodes.head())
print(edges.head())
print(pois.head())

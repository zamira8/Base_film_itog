import networkx as nx
from .parser import get_films_cached


def build_knowledge_graph() -> nx.Graph:
    """Строит граф связей «фильм—жанр» и «фильм—актёр»."""
    graph = nx.Graph()
    for film in get_films_cached():
        film_id = film["id"]
        graph.add_node(film_id, kind="film", name=film["name"])
        for genre in film.get("genres", []):
            genre_id = f"genre:{genre.casefold()}"
            graph.add_node(genre_id, kind="genre", name=genre)
            graph.add_edge(film_id, genre_id, relation="has_genre")
        for actor in film.get("actors", []):
            actor_id = f"actor:{actor.casefold()}"
            graph.add_node(actor_id, kind="actor", name=actor)
            graph.add_edge(film_id, actor_id, relation="features_actor")
    return graph


def find_related_films(film_id: str) -> list[str]:
    graph = build_knowledge_graph()
    if film_id not in graph:
        return []
    neighbors = set(graph.neighbors(film_id))
    related: set[str] = set()
    for node in neighbors:
        related.update(
            n for n in graph.neighbors(node)
            if graph.nodes[n].get("kind") == "film" and n != film_id
        )
    return sorted(related)

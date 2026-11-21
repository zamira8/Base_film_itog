import re
from difflib import SequenceMatcher
from .parser import get_films_cached
from .graph import find_related_films


def _normal(text: str) -> str:
    return re.sub(r"[^\w\s+-]", " ", text.casefold()).replace("ё", "е").strip()


def semantic_search(query: str, top_k: int = 5) -> list[dict]:
    """Лёгкий семантико-текстовый поиск без обязательной загрузки ML-модели.

    Сопоставляет слова запроса с названием, описанием, жанрами и актёрами,
    а также учитывает связи графа знаний для поиска похожих фильмов.
    """
    q = _normal(query)
    tokens = {w for w in q.split() if len(w) > 2}
    films = get_films_cached()
    scored = []
    for film in films:
        fields = [film["name"], film.get("description", ""), *film.get("genres", []), *film.get("actors", [])]
        text = _normal(" ".join(fields))
        score = sum(2.0 if token in _normal(film["name"]) else 0.8 for token in tokens if token in text)
        # Небольшой бонус за совпадение полного названия.
        if q and q in _normal(film["name"]):
            score += 4
        if score:
            scored.append((score, film))

    # Для запроса «похожие на [название]» поднимаем фильмы с общими жанрами/актёрами.
    for film in films:
        if _normal(film["name"]) in q and film["id"]:
            related_ids = set(film.get("similar", [])) | set(find_related_films(film["id"]))
            for score, candidate in scored:
                if candidate["id"] in related_ids:
                    scored[scored.index((score, candidate))] = (score + 3, candidate)
            for candidate in films:
                if candidate["id"] in related_ids and all(candidate["id"] != f["id"] for _, f in scored):
                    scored.append((3.0, candidate))
            break

    scored.sort(key=lambda pair: (pair[0], pair[1].get("rating", 0)), reverse=True)
    return [film for _, film in scored[:top_k]]

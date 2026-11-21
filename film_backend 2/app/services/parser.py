from functools import lru_cache
from pathlib import Path
import frontmatter

FILMS_DIR = Path(__file__).resolve().parents[2] / "films"


def load_films() -> list[dict]:
    """Загружает карточки фильмов из Markdown-файлов с YAML front matter."""
    films: list[dict] = []
    if not FILMS_DIR.exists():
        return films

    for path in sorted(FILMS_DIR.glob("*.md")):
        post = frontmatter.load(path)
        item = dict(post.metadata)
        item.setdefault("id", path.stem.replace("_", "-"))
        item.setdefault("genres", [])
        item.setdefault("actors", [])
        item.setdefault("similar", [])
        item.setdefault("description", post.content.strip())
        # Нормализуем типы данных, чтобы API всегда возвращал одинаковую структуру.
        item["year"] = int(item.get("year", 0))
        item["duration"] = int(item.get("duration", 0))
        item["rating"] = float(item.get("rating", 0))
        for key in ("genres", "actors", "similar"):
            item[key] = [str(value) for value in (item.get(key) or [])]
        films.append(item)
    return films


@lru_cache(maxsize=1)
def get_films_cached() -> list[dict]:
    return load_films()


def clear_films_cache() -> None:
    get_films_cached.cache_clear()

import os
import re
from .parser import get_films_cached
from .search import semantic_search

GENRE_ALIASES = {
    "комедии": "комедия", "комедию": "комедия", "комедий": "комедия",
    "ужасы": "ужасы", "хоррор": "ужасы", "боевики": "боевик",
    "фантастику": "фантастика", "фантастики": "фантастика",
    "детективы": "детектив", "триллеры": "триллер", "драмы": "драма",
}


def _extract_filters(question: str) -> tuple[float, int, str | None, str | None]:
    q = question.casefold().replace("ё", "е")
    rating_match = re.search(r"(?:от|выше|больше|минимум|рейтингом)\s*(\d(?:[.,]\d)?)", q)
    min_rating = float(rating_match.group(1).replace(",", ".")) if rating_match else 0.0
    year_match = re.search(r"(?:после|с|начиная с)\s*(19\d{2}|20\d{2})", q)
    min_year = int(year_match.group(1)) if year_match else 0

    films = get_films_cached()
    actor = next((a for f in films for a in f.get("actors", []) if a.casefold() in q), None)
    genre = None
    all_genres = {g for f in films for g in f.get("genres", [])}
    for candidate in sorted(all_genres, key=len, reverse=True):
        if candidate.casefold() in q:
            genre = candidate
            break
    if genre is None:
        for alias, normalized in GENRE_ALIASES.items():
            if alias in q and normalized in all_genres:
                genre = normalized
                break
    return min_rating, min_year, actor, genre


def _format_answer(question: str, films: list[dict], actor: str | None, genre: str | None) -> str:
    if not films:
        return ("По заданным критериям фильмы не найдены. Попробуйте снизить минимальный рейтинг, "
                "изменить жанр или указать другого актёра.")
    if actor:
        intro = f"Подборка фильмов с актёром {actor}"
    elif genre:
        intro = f"Подборка в жанре «{genre}»"
    else:
        intro = "Вот фильмы, которые могут вам подойти"
    rows = []
    for i, film in enumerate(films[:5], 1):
        rows.append(
            f"{i}. {film['name']} ({film['year']}) — рейтинг {film['rating']}/10, "
            f"{film['duration']} мин.\n   Жанры: {', '.join(film['genres'])}. "
            f"В ролях: {', '.join(film['actors'])}.\n   {film['description']}"
        )
    return intro + ":\n\n" + "\n\n".join(rows)


def answer_question(question: str) -> dict:
    min_rating, min_year, actor, genre = _extract_filters(question)
    all_films = get_films_cached()
    filtered = [f for f in all_films
                if f.get("rating", 0) >= min_rating
                and f.get("year", 0) >= min_year
                and (not actor or actor in f.get("actors", []))
                and (not genre or genre in f.get("genres", []))]

    if re.search(r"похож|напомин|как\s+в", question.casefold()):
        semantic = semantic_search(question, top_k=10)
        if semantic:
            allowed = {f["id"] for f in filtered} if (min_rating or min_year or actor or genre) else None
            filtered = [f for f in semantic if allowed is None or f["id"] in allowed]
    elif not (actor or genre or min_rating or min_year):
        # Общий запрос на естественном языке: поиск по описанию/названию.
        hits = semantic_search(question, top_k=5)
        if hits:
            filtered = hits

    filtered.sort(key=lambda f: f.get("rating", 0), reverse=True)
    selected = filtered[:5]

    # Опциональный RAG-ответ через OpenAI. При отсутствии ключа сервис полностью работает локально.
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key and selected:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            context = "\n\n".join(
                f"{f['name']} ({f['year']}): {f['description']} Жанры: {', '.join(f['genres'])}. "
                f"Актёры: {', '.join(f['actors'])}. Рейтинг: {f['rating']}/10."
                for f in selected
            )
            response = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[
                    {"role": "system", "content": "Ты помощник по подбору фильмов. Отвечай по-русски и используй только переданные сведения о фильмах. Не выдумывай фильмы и факты."},
                    {"role": "user", "content": f"Запрос: {question}\n\nДанные каталога:\n{context}"},
                ],
                temperature=0.4,
            )
            answer = response.choices[0].message.content or _format_answer(question, selected, actor, genre)
        except Exception:
            answer = _format_answer(question, selected, actor, genre)
    else:
        answer = _format_answer(question, selected, actor, genre)

    return {"answer": answer, "sources": [f["name"] for f in selected], "films": selected}

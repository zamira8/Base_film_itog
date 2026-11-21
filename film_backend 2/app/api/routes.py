from fastapi import APIRouter, HTTPException, Query
from typing import List
from ..schemas import Film, AskRequest, AskResponse
from ..services.parser import get_films_cached
from ..services.rag import answer_question
from ..services.graph import find_related_films

router = APIRouter(prefix="/api", tags=["films"])


def _to_film(item: dict) -> Film:
    return Film(**item)


@router.get("/films", response_model=List[Film])
def list_films(
    genre: str | None = Query(default=None),
    actor: str | None = Query(default=None),
    min_rating: float = Query(default=0, ge=0, le=10),
    year_from: int | None = Query(default=None, ge=1888, le=2100),
):
    films = get_films_cached()
    result = [f for f in films
              if f["rating"] >= min_rating
              and (not genre or genre.casefold() in [g.casefold() for g in f["genres"]])
              and (not actor or actor.casefold() in " ".join(f["actors"]).casefold())
              and (not year_from or f["year"] >= year_from)]
    return [_to_film(f) for f in result]


@router.get("/films/{film_id}", response_model=Film)
def get_film(film_id: str):
    for film in get_films_cached():
        if film["id"] == film_id:
            return _to_film(film)
    raise HTTPException(status_code=404, detail="Film not found")


@router.get("/films/{film_id}/similar", response_model=List[Film])
def get_similar_films(film_id: str):
    films = get_films_cached()
    current = next((f for f in films if f["id"] == film_id), None)
    if current is None:
        raise HTTPException(status_code=404, detail="Film not found")
    ids = list(dict.fromkeys(current.get("similar", []) + find_related_films(film_id)))
    by_id = {f["id"]: f for f in films}
    return [_to_film(by_id[i]) for i in ids if i in by_id]


@router.post("/ask", response_model=AskResponse)
def ask(payload: AskRequest):
    if not payload.query.strip():
        raise HTTPException(status_code=400, detail="Query is empty")
    result = answer_question(payload.query.strip())
    return AskResponse(**result)


# Совместимые адреса на случай, если в старом React-коде ещё остались названия recipes.
@router.get("/recipes", response_model=List[Film], include_in_schema=False)
def list_recipes_compat():
    return [_to_film(f) for f in get_films_cached()]


@router.get("/recipes/{recipe_id}", response_model=Film, include_in_schema=False)
def get_recipe_compat(recipe_id: str):
    return get_film(recipe_id)

from typing import Dict, List, Any, Optional

from app.spotify.parser.base import ParseBase
from app.schemas import Genre, GenreCreate


class ParseGenre(ParseBase[Genre, GenreCreate]):
    def from_dict(self, *, obj_in: Dict[str, Any]) -> Optional[Genre]:
        """
        Parse genre dict to genre object.

        Ex: {id: "pop"}
        """
        if not obj_in.get("id", None):
            return None
        else:
            return Genre(**obj_in)

    def from_genre_list(self, *, obj_in: List[str]) -> List[Genre]:
        """
        Parse list of genres to valid list of genre objects.

        Ex Input: ["pop", "rock", "pop-rock"]
        """
        genres = []
        if not obj_in:
            return genres

        for g in obj_in:
            if not isinstance(g, str):
                continue
            genres.append(Genre(id=g))

        return genres

    def from_artist_about(self, *, obj_in: Dict[str, Any]) -> List[Genre]:
        """
        Parse genres from spotify artist api result.

        Ex: {
           "external_urls": {
                "spotify": "https://open.spotify.com/artist/…"
            },
            "followers": {
                "href": null,
                "total": 5610
            },
            "genres": [
                "meditation",
                "musica de fondo",
                "pianissimo",
                "world meditation"
            ],
            "href": "https://api.spotify.com/v1/artists/…",
            "id": "6Z0Cmu4TIqYn3s5iJyLhP2",
            "images": [{…},…],
            "name": "Marcelo A. Rodríguez",
            "popularity": 43,
            "type": "artist",
            "uri": "spotify:artist:6Z0Cmu4TIqYn3s5iJyLhP2" 
        }
        """
        if not obj_in.get("genres", []):
            return []
        else:
            return self.from_genre_list(obj_in=obj_in["genres"])


genre = ParseGenre(Genre)

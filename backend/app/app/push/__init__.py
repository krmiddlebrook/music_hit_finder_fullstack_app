# Most of these functions could be celery tasks also, but this level of granularity adds too
# much overhead.
from .push_album import album
from .push_track import track
from .push_artist import artist
from .push_genre import genre

from celery import Celery
from celery.schedules import crontab
import pytz
import datetime

from .config import settings


celery_app = Celery(
    "worker",
    broker=settings.BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.spotify"],
)

# celery_app.conf.task_routes = {"app.worker.test_celery": "main-queue"}

# Content types to accept.
celery_app.conf.accept_content = settings.ACCEPT_CONTENT

# Period of time (in secs) that stored task tombstones exist before they are deleted
celery_app.conf.result_expires = datetime.timedelta(hours=4)

# Delegate queue creation to Celery.
celery_app.conf.task_create_missing_queues = True

# Define the name of the default queue.
celery_app.conf.task_default_queue = "main-queue"

# Send task to flower for monitoring.
celery_app.conf.worker_send_task_events = True

# Define date/time settings.
# celery_app.conf.enable_utc = True
celery_app.broker_pool_limit = settings.BROKER_POOL_LIMIT
celery_app.conf.timezone = "America/Los_Angeles"

# Specify which modules to import tasks from.
# celery_app.conf.include = ["app.spotify"]


def now_pst():
    return datetime.datetime.now(pytz.timezone("America/Los_Angeles"))


celery_app.conf.beat_schedule = {
    # Execute daily at midnight PST
    "refresh-materialized-views-three-times-daily": {
        "task": "app.spotify.flow.flow_refresh_materialized_views",
        "schedule": crontab(minute=0, hour="0,8,12,16", nowfun=now_pst),
    },
    "update-artists-at-four-past-the-hour-twice-daily": {
        "task": "app.spotify.flow.flow_update_artists",
        "schedule": crontab(minute=4, hour="0,5", nowfun=now_pst),
        "kwargs": dict(skip=0, limit=10_000),
    },
    "update-artists-with-offset-on-the-hour-twice-daily": {
        "task": "app.spotify.flow.flow_update_artists",
        "schedule": crontab(minute=0, hour="2,6", nowfun=now_pst),
        "kwargs": dict(skip=10_000, limit=5_000),
    },
    "update-tracks-at-twenty-before-the-hour-twice-daily": {
        "task": "app.spotify.flow.flow_update_tracks",
        "schedule": crontab(minute=40, hour="0,5", nowfun=now_pst),
        "kwargs": dict(skip=0, limit=50_000),
    },
    "update-tracks-with-offset-at-twenty-before-the-hour-twice-daily": {
        "task": "app.spotify.flow.flow_update_tracks",
        "schedule": crontab(minute=40, hour="2,6", nowfun=now_pst),
        "kwargs": dict(skip=50_000, limit=50_000),
    },
    "scrape-playlist-tracks-at-one-in-the-morning-every-tuesday": {
        "task": "app.spotify.flow.flow_scrape_playlists_tracks",
        "schedule": crontab(minute=0, hour=1, day_of_week="tuesday", nowfun=now_pst),
        "kwargs": dict(playlist_tracks_limit=300, skip=0, limit=8_000),
    },
    "scrape-album_playcounts-at-ten-past-the-hour-three-times-daily": {
        "task": "app.spotify.flow.flow_scrape_album_playcounts",
        "schedule": crontab(minute=10, hour="0,7,23", nowfun=now_pst),
        "kwargs": dict(verified_artists=True, skip=0, limit=100_000),
    },
    # TODO: schedule for non-rising tracks and longer lag days
    "scrape-spectrograms-every-third-hour-at-twenty-till-the-hour-daily": {
        "task": "app.spotify.flow.flow_scrape_spectrograms",
        "schedule": crontab(minute=40, hour="*/3", nowfun=now_pst),
        "kwargs": dict(rising_tracks_only=True, lag_days=7, skip=0, limit=2_000),
    },
    "track-predictions-every-fourth-hour-daily": {
        "task": "app.spotify.flow.flow_track_predictions",
        "schedule": crontab(minute=30, hour="*/4", nowfun=now_pst),
        "kwargs": dict(rising_tracks_only=True, lag_days=7, skip=0, limit=10_000),
    },
    "track-distances-every-twenty-minutes-between-periods-daily": {
        "task": "app.spotify.flow.flow_track_distances",
        "schedule": crontab(minute="*/20", hour="1,8-11,13,22,23", nowfun=now_pst),
        "kwargs": dict(
            lag_period=7,
            days_since_release=180,
            canidate_hit_limit=2_000,
            skip=0,
            limit=20_000,
        ),
    },
}

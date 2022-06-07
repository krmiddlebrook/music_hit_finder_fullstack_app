from typing import Dict, List, Any
from datetime import date, datetime

from app.core.celery_app import celery_app


def chunkify(input: List[Any], chunk_size: int = 20) -> List[List[Any]]:
    """
    A convenience function to chunk a list

    """
    chunked = []
    for i in range(0, len(input), chunk_size):
        end = i + chunk_size if i + chunk_size < len(input) else len(input)
        chunked.append(list(input[i:end]))
    return chunked


def combine_date(data: Dict[str, Any]) -> date:
    """ Helper method to combine day, month, year keys in a dict into a valid
        Date object.

        Returns:
            A Date object of the form YYYY-MM-DD.
    """
    if data.get("release_date", None) and data.get("release_date_precision", None):
        if data["release_date_precision"] == "day":
            return date.fromisoformat(data["release_date"])
        elif data["release_date_precision"] == "month":
            return date.fromisoformat(f"{data['release_date']}-01")
        else:
            if int(data["release_date"]) == 0:
                data["release_date"] = 1600
            return date.fromisoformat(f"{data['release_date']}-01-01")
    else:
        year = data.get("year", 1600)
        month = data.get("month", 1)
        day = data.get("day", 1)
        cdate = date(year, month, day)
        return cdate


def extract_primary_artist(artists=[]):
    """ Returns the primary artist dict given a list of artist objects. """
    try:
        if isinstance(artists, list):
            artist = artists[0] if len(artists) > 0 else None
            return artist
    except Exception as e:
        print(e)


@celery_app.task(bind=True)
def flow_complete(self, task_name, time):
    total_time = (
        datetime.utcnow() - datetime.strptime(time, "%Y-%m-%dT%H:%M:%S.%f")
    ).total_seconds()
    return {"task_name": task_name, "elapsed_time": total_time}

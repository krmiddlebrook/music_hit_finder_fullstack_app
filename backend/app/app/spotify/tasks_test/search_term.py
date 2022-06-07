from celery.utils.log import get_task_logger

from app.core.config import settings
from app.core.celery_app import celery_app
from app.db.session import session_scope

from app import crud


logger = get_task_logger(__name__)


@celery_app.task(bind=True, queue="low-priority")
def flow_search_terms(self) -> bool:
    """
    Create new search terms.
    """
    with open(settings.SEARCH_TERMS_FILE) as f:
        file_terms = set(f.read().split("\n"))
        if "" in file_terms:
            file_terms.remove("")

    with session_scope() as db:
        db_terms = crud.search_term.get_multi(db, skip=0, limit=None)
        db_terms = set([term.id for term in db_terms])

        # Check if any terms in search terms file are missing in the db
        new_terms = file_terms - db_terms

        # create db objects for search terms
        term_objs = [dict(id=term) for term in new_terms]

        # Push search terms to the search_terms table.
        is_success = crud.search_term.create_multi(db, obj_in=term_objs, logger=logger)
        return is_success


from typing import List, Optional, Dict, Any, Union
from datetime import datetime

from celery import chord, group
from celery.utils.log import get_task_logger
import numpy as np

from app.core.celery_app import celery_app
from app.core.config import settings
from app.db.session import session_scope

from app import crud, schemas, models
from app.spotify import parser
from app.ml import spec_model
from .utils import chunkify


logger = get_task_logger(__name__)


# TODO: finish flow for scrapping artist (cities and links)

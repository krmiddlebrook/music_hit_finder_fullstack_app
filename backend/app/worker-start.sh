#! /usr/bin/env bash
set -e

python /app/app/celeryworker_pre_start.py

celery worker -A app.worker -l info -Q main-queue,spec,short-queue,distance-queue,web-queue -P ${POOL} -c ${CONCURRENCY}
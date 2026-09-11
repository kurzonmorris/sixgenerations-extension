"""Repeating jobs, in this process. No cron, no second container.

A job that throws is logged and the schedule carries on — one broken job must
not silently stop every other one.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from .appLogging import getLogger

log = getLogger("scheduler")


@dataclass(frozen=True)
class Job:
    name: str
    owner: str
    when: str
    run: Callable[[], None]


class Scheduler:
    def __init__(self) -> None:
        self.jobs: list[Job] = []
        self._engine: BackgroundScheduler | None = None

    def add(self, job: Job) -> None:
        self.jobs.append(job)

    def _wrap(self, job: Job) -> Callable[[], None]:
        def guarded() -> None:
            try:
                job.run()
            except Exception as error:
                log.error(f"job {job.name} ({job.owner}) failed: {error}")
        return guarded

    def start(self) -> None:
        if not self.jobs:
            return
        self._engine = BackgroundScheduler(timezone="Europe/London")
        for job in self.jobs:
            trigger = (
                CronTrigger.from_crontab(job.when)
                if " " in job.when
                else IntervalTrigger(minutes=int(job.when))
            )
            self._engine.add_job(self._wrap(job), trigger, id=job.name, name=job.name)
            log.info(f"scheduled {job.name} ({job.when}) for {job.owner}")
        self._engine.start()

    def stop(self) -> None:
        if self._engine:
            self._engine.shutdown(wait=False)
            self._engine = None

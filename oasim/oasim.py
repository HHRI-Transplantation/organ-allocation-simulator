from __future__ import annotations

import contextlib
import functools
import os
import sqlite3
import tempfile
import time
from collections import defaultdict
from collections.abc import Generator
from typing import Any
from typing import Protocol

import polars as pl

from oasim.database import _add_event_data_to_table
from oasim.database import _combine_waitlist_with_donor
from oasim.database import _create_table
from oasim.database import _get_table
from oasim.database import _move_candidate_from_waitlist_to_removals
from oasim.database import _remove_candidate_from_waitlist
from oasim.database import _update_event_data_in_table
from oasim.objects import _Candidate
from oasim.objects import _Donor
from oasim.objects import _Event
from oasim.objects import _Removal


class AllocationProtocol(Protocol):
    '''
        The AllocationProtocol. Defines the signature of the callable
        that must be provided when running a simulation.
    '''

    def __call__(
        self,
        df: pl.DataFrame,
        *args: Any,
        **kwargs: Any,
    ) -> pl.DataFrame:
        ...


@contextlib.contextmanager
def OrganAllocationSimulator(
    candidate_id: str = 'PX_ID',
    donor_id: str = 'DONOR_ID',
) -> Generator[_OrganAllocationSimulator]:
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, 'db.db')
        with contextlib.closing(sqlite3.connect(db_path)) as conn:
            conn.cursor().execute('PRAGMA journal_mode = WAL;')
            sim = _OrganAllocationSimulator(
                candidate_id,
                donor_id,
                db_path,
                conn,
            )
            yield sim


class _OrganAllocationSimulator:

    def __init__(
        self,
        candidate_id: str,
        donor_id: str,
        db_path: str,
        conn: sqlite3.Connection,
    ) -> None:

        self._waitlist_ids: set[int] = set()
        self._transplant_ids: set[int] = set()
        self._transplant_dfs: list[pl.DataFrame] = []
        self._events: list[_Event] = []
        self._waitlist_schema = pl.Schema()
        self._db = db_path
        self._uri = f'sqlite:///{self._db}'
        self._conn = conn
        self.candidate_id = candidate_id
        self.donor_id = donor_id
        self._donor_schema = pl.Schema()
        self._event_times: defaultdict[str, list[float]] = defaultdict(list)
        self._run_flag = False

    def load_candidates(
        self,
        df: pl.DataFrame,
        event_datetime_col: str,
    ) -> None:

        self._validate_candidate_id(df)
        self._waitlist_schema.update(df.schema)
        cands = [
            _Candidate(d[self.candidate_id], d[event_datetime_col], d)
            for d in df.to_dicts()
        ]
        self._events += cands

    def load_removals(
        self,
        df: pl.DataFrame,
        event_datetime_col: str,
    ) -> None:

        self._validate_candidate_id(df)
        rems = [
            _Removal(d[self.candidate_id], d[event_datetime_col], d)
            for d in df.to_dicts()
        ]
        self._events += rems

    def load_donors(
        self,
        df: pl.DataFrame,
        event_datetime_col: str,
    ) -> None:

        self._donor_schema = df.schema
        dons = [
            _Donor(d[self.donor_id], d[event_datetime_col], d)
            for d in df.to_dicts()
        ]
        self._events += dons

    def run(
        self,
        allocate: AllocationProtocol,
        *args: Any,
        **kwargs: Any,
    ) -> None:

        self._prepare_for_simulation_run()
        for e in sorted(self._events):
            start = time.perf_counter()
            self._process_event(
                e,
                allocate,
                *args,
                **kwargs,
            )
            self._event_times[e.__class__.__name__].append(
                time.perf_counter() - start,
            )
        self._finalize_simulation_run()
        return

    @functools.cached_property
    def _transplants(self) -> pl.DataFrame:
        if self._transplant_dfs:
            return pl.concat(
                self._transplant_dfs,
                how='vertical',
            )
        else:
            return pl.DataFrame()

    @property
    def transplants(self) -> pl.DataFrame | None:
        if self._run_flag:
            return self._transplants
        else:
            print('Run simulation to access transplants')
            return None

    @functools.cached_property
    def _waitlist(self) -> pl.DataFrame:
        return _get_table(
            self._conn,
            self._uri,
            self._waitlist_schema,
            'waitlist',
        )

    @property
    def waitlist(self) -> pl.DataFrame | None:
        if self._run_flag:
            return self._waitlist
        else:
            print('Run simulation to access waitlist')
            return None

    @functools.cached_property
    def _removals(self) -> pl.DataFrame:
        return _get_table(
            self._conn,
            self._uri,
            self._waitlist_schema,
            'removals',
        )

    @property
    def removals(self) -> pl.DataFrame | None:
        if self._run_flag:
            return self._removals
        else:
            print('Run simulation to access removals')
            return None

    def _process_event(
        self,
        e: _Event,
        allocate: AllocationProtocol,
        *args: Any,
        **kwargs: Any,
    ) -> None:

        if isinstance(e, _Candidate):
            self._process_candidate_event(e, self._conn)

        elif isinstance(e, _Removal):
            self._process_removal_event(e, self._conn)

        elif isinstance(e, _Donor):
            self._process_donor_event(
                e,
                allocate,
                *args,
                **kwargs,
            )

        else:
            raise TypeError(
                f'e is of type {type(e).__name__}. '
                'Expected _Candidate, _Donor, or _Removal.',
            )

    def _process_candidate_event(
        self,
        cand: _Candidate,
        conn: sqlite3.Connection,
    ) -> None:

        if cand.id in self._transplant_ids:
            return

        elif cand.id in self._waitlist_ids:
            _update_event_data_in_table(
                conn,
                cand,
                'waitlist',
                self.candidate_id,
            )

        else:
            self._waitlist_ids.add(cand.id)
            _add_event_data_to_table(conn, cand, 'waitlist')

    def _process_removal_event(
        self,
        removal: _Removal,
        conn: sqlite3.Connection,
    ) -> None:

        if removal.id in self._transplant_ids:
            return

        _move_candidate_from_waitlist_to_removals(
            conn,
            self.candidate_id,
            removal.id,
        )
        self._waitlist_ids.remove(removal.id)

    def _process_transplants(
        self,
        transplants: pl.DataFrame,
        conn: sqlite3.Connection,
    ) -> None:

        self._transplant_dfs.append(transplants)

        for candidate_id in (
            transplants
            .get_column(self.candidate_id)
            .to_list()
        ):
            self._waitlist_ids.remove(candidate_id)
            self._transplant_ids.add(candidate_id)
            _remove_candidate_from_waitlist(
                conn,
                self.candidate_id,
                candidate_id,
            )

    def _process_donor_event(
        self,
        don: _Donor,
        allocate: AllocationProtocol,
        *args: Any,
        **kwargs: Any,
    ) -> None:

        waitlist = _get_table(
            self._conn,
            self._uri,
            self._waitlist_schema,
            'waitlist',
        )

        df = _combine_waitlist_with_donor(
            waitlist,
            don,
            self._donor_schema,
        )
        self._process_transplants(
            allocate(df),
            self._conn,
        )
        return

    def _validate_candidate_id(
        self,
        df: pl.DataFrame,
    ) -> None:

        if df.schema[self.candidate_id].is_integer():
            return

        raise TypeError(
            f'Column {self.candidate_id} for candidate_id '
            'must be integer type',
        )

    def _prepare_for_simulation_run(self) -> None:

        if self._run_flag:
            print('Simulation can only be run once.')

        elif len(self._events) == 0:
            print('No events have been loaded. Simulation not run.')

        else:
            self._run_flag = True
            _create_table(
                self._conn,
                'waitlist',
                tuple(self._waitlist_schema.keys()),
                primary_key=self.candidate_id,
            )
            _create_table(
                self._conn,
                'removals',
                tuple(self._waitlist_schema.keys()),
                primary_key=self.candidate_id,
            )

    def _finalize_simulation_run(self) -> None:

        if self._run_flag:
            self._conn.commit()

            # Ensures the property is cached so it is accessible
            # after context manager exits and db is gone.
            _ = self.waitlist
            _ = self.removals

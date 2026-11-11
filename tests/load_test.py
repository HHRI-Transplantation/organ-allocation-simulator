from __future__ import annotations

import datetime

import polars as pl
import pytest

from oasim.objects import _Candidate
from oasim.objects import _Donor
from oasim.objects import _Removal


def test_oasim_load_candidates(sim):

    df = pl.DataFrame(
        data={
            'PX_ID': [1, 2],
            'event_datetime': [
                datetime.datetime(2020, 1, 1),
                datetime.datetime(2021, 1, 1),
            ],
        },
        schema={
            'PX_ID': pl.Int32,
            'event_datetime': pl.Datetime,
        },
    )
    expected = [
        _Candidate(
            1,
            datetime.datetime(2020, 1, 1),
            data={
                'PX_ID': 1,
                'event_datetime': datetime.datetime(2020, 1, 1),
            },
        ),
        _Candidate(
            2,
            datetime.datetime(2021, 1, 1),
            data={
                'PX_ID': 2,
                'event_datetime': datetime.datetime(2021, 1, 1),
            },
        ),
    ]

    sim.load_candidates(df, 'event_datetime')
    assert sim._events == expected
    assert sim._waitlist_schema == pl.Schema(
        {'PX_ID': pl.Int32, 'event_datetime': pl.Datetime()},
    )


def test_candidate_id_not_int_load_candidates(sim):

    candidates = pl.DataFrame(
        schema={
            'PX_ID': pl.String,
            'edt': pl.Datetime(),
        },
    )
    with pytest.raises(TypeError) as excinfo:
        sim.load_candidates(candidates, 'edt')

    msg, = excinfo.value.args
    expected = 'Column PX_ID for candidate_id must be integer type'
    assert msg == expected


def test_oasim_load_donors(sim):

    df = pl.DataFrame(
        data={
            'DONOR_ID': [1, 2],
            'event_datetime': [
                datetime.datetime(2020, 1, 1),
                datetime.datetime(2021, 1, 1),
            ],
        },
        schema={
            'DONOR_ID': pl.Int32,
            'event_datetime': pl.Datetime,
        },
    )
    expected = [
        _Donor(
            1,
            datetime.datetime(2020, 1, 1),
            data={
                'DONOR_ID': 1,
                'event_datetime': datetime.datetime(2020, 1, 1),
            },
        ),
        _Donor(
            2,
            datetime.datetime(2021, 1, 1),
            data={
                'DONOR_ID': 2,
                'event_datetime': datetime.datetime(2021, 1, 1),
            },
        ),
    ]

    sim.load_donors(df, 'event_datetime')
    assert sim._events == expected
    assert sim._donor_schema == pl.Schema({
        'DONOR_ID': pl.Int32,
        'event_datetime': pl.Datetime(),
    })


def test_oasim_load_removals(sim):

    df = pl.DataFrame(
        data={
            'PX_ID': [1, 2],
            'event_datetime': [
                datetime.datetime(2020, 1, 1),
                datetime.datetime(2021, 1, 1),
            ],
        },
        schema={
            'PX_ID': pl.Int32,
            'event_datetime': pl.Datetime,
        },
    )
    expected = [
        _Removal(
            1,
            datetime.datetime(2020, 1, 1),
            data={
                'PX_ID': 1,
                'event_datetime': datetime.datetime(2020, 1, 1),
            },
        ),
        _Removal(
            2,
            datetime.datetime(2021, 1, 1),
            data={
                'PX_ID': 2,
                'event_datetime': datetime.datetime(2021, 1, 1),
            },
        ),
    ]

    sim.load_removals(df, 'event_datetime')
    assert sim._events == expected
    assert sim.candidate_id == 'PX_ID'


def test_candidate_id_not_int_load_removals(sim):

    candidates = pl.DataFrame(
        schema={
            'PX_ID': pl.String,
            'edt': pl.Datetime(),
        },
    )
    with pytest.raises(TypeError) as excinfo:
        sim.load_removals(candidates, 'edt')

    msg, = excinfo.value.args
    expected = 'Column PX_ID for candidate_id must be integer type'
    assert msg == expected

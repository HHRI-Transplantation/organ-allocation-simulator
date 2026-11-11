from __future__ import annotations

import datetime

from oasim.objects import _Candidate
from oasim.objects import _Donor
from oasim.objects import _Event
from oasim.objects import _Removal


def test_event_date_converted_to_datetime():

    e = _Event(1, datetime.date(2020, 1, 1))
    assert e.event_datetime == datetime.datetime(2020, 1, 1)


def test_candidate_repr():

    c = _Candidate(1, datetime.datetime(2020, 1, 1))

    expected = (
        '_Candidate('
        'id=1, '
        'event_datetime="2020-01-01 00:00:00"'
        ')'
    )
    assert repr(c) == expected


def test_removal_repr():

    r = _Removal(1, datetime.datetime(2020, 1, 1))

    expected = (
        '_Removal('
        'id=1, '
        'event_datetime="2020-01-01 00:00:00"'
        ')'
    )
    assert repr(r) == expected


def test_donor_repr():

    c = _Donor(1, datetime.datetime(2020, 1, 1))

    expected = (
        '_Donor('
        'id=1, '
        'event_datetime="2020-01-01 00:00:00"'
        ')'
    )
    assert repr(c) == expected


def test_event_equality():

    e1 = _Event(1, datetime.datetime(2020, 1, 1), {'age': 25})
    e2 = _Event(1, datetime.datetime(2020, 1, 1), {'age': 25})
    assert e1 == e2
    assert e1 <= e2
    assert e1 >= e2


def test_sort_events_tiebreaks():
    events = [
        _Donor(1, datetime.datetime(2020, 1, 1)),
        _Removal(1, datetime.datetime(2020, 1, 1)),
        _Candidate(1, datetime.datetime(2020, 1, 1)),
    ]
    expected = [
        _Candidate(1, datetime.datetime(2020, 1, 1)),
        _Donor(1, datetime.datetime(2020, 1, 1)),
        _Removal(1, datetime.datetime(2020, 1, 1)),
    ]
    assert sorted(events) == expected


def test_sort_events():
    events = [
        _Candidate(1, datetime.datetime(2021, 1, 1)),
        _Candidate(1, datetime.datetime(2020, 1, 1)),
        _Candidate(1, datetime.datetime(2022, 1, 1)),
    ]
    expected = [
        _Candidate(1, datetime.datetime(2020, 1, 1)),
        _Candidate(1, datetime.datetime(2021, 1, 1)),
        _Candidate(1, datetime.datetime(2022, 1, 1)),
    ]
    assert sorted(events) == expected

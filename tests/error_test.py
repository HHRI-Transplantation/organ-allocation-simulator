from __future__ import annotations

import datetime

import polars as pl
import pytest

from oasim.objects import _Event


def test_no_waitlist(sim, capsys):
    sim.waitlist
    out, err = capsys.readouterr()
    assert out == 'Run simulation to access waitlist\n'
    assert err == ''


def test_no_removals(sim, capsys):
    sim.removals
    out, err = capsys.readouterr()
    assert out == 'Run simulation to access removals\n'
    assert err == ''


def test_no_transplants(sim, capsys):
    sim.transplants
    out, err = capsys.readouterr()
    assert out == 'Run simulation to access transplants\n'
    assert err == ''


def test_wrong_event(sim):

    e = _Event('', '')
    with pytest.raises(TypeError) as excinfo:
        sim._process_event(e, '', '', '')

    msg, = excinfo.value.args
    expected = (
        'e is of type _Event. Expected _Candidate, '
        '_Donor, or _Removal.'
    )
    assert msg == expected


def test_run_flag(sim, capsys):
    assert sim._run_flag is False
    sim.run('')
    out, err = capsys.readouterr()
    assert out == 'No events have been loaded. Simulation not run.\n'
    assert err == ''
    assert sim._run_flag is False

    candidates = pl.DataFrame(
        data={
            'PX_ID': [1],
            'edt': [
                datetime.datetime(2020, 1, 1),
            ],
        },
        schema={
            'PX_ID': pl.Int32,
            'edt': pl.Datetime,
        },
    )
    sim.load_candidates(candidates, 'edt')
    sim.run(lambda df: pl.DataFrame())
    assert sim._run_flag is True

    sim.run('')
    out, err = capsys.readouterr()
    assert out == 'Simulation can only be run once.\n'
    assert err == ''

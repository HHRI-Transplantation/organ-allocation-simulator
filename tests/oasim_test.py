from __future__ import annotations

import datetime

import polars as pl
from polars.testing import assert_frame_equal

from oasim import OrganAllocationSimulator


def test_candidate_added_to_waitlist(sim):

    candidates = pl.DataFrame(
        data={
            'PX_ID': [1],
            'edt': [datetime.datetime(2020, 1, 1)],
        },
        schema={
            'PX_ID': pl.Int32,
            'edt': pl.Datetime,
        },
    )
    sim.load_candidates(candidates, 'edt')
    sim.run('')
    expected = pl.DataFrame(
        data={
            'PX_ID': [1],
            'edt': [datetime.datetime(2020, 1, 1)],
        },
        schema={
            'PX_ID': pl.Int32,
            'edt': pl.Datetime,
        },
    )
    assert_frame_equal(sim.waitlist, expected)
    assert {1} == sim._waitlist_ids


def test_candidate_already_on_waitlist(sim):

    candidates = pl.DataFrame(
        data={
            'PX_ID': [1],
            'listing_dt': [datetime.datetime(2020, 1, 1)],
        },
        schema={
            'PX_ID': pl.Int32,
            'listing_dt': pl.Datetime,
        },
    )
    sim.load_candidates(candidates, 'listing_dt')
    candidate_updates = pl.DataFrame(
        data={
            'PX_ID': [1],
            'stat_dt': [datetime.datetime(2021, 1, 1)],
        },
        schema={
            'PX_ID': pl.Int32,
            'stat_dt': pl.Datetime,
        },
    )
    sim.load_candidates(candidate_updates, 'stat_dt')
    sim.run('')
    expected = pl.DataFrame(
        data={
            'PX_ID': [1],
            'listing_dt': [datetime.datetime(2020, 1, 1)],
            'stat_dt': [datetime.datetime(2021, 1, 1)],
        },
        schema={
            'PX_ID': pl.Int32,
            'listing_dt': pl.Datetime,
            'stat_dt': pl.Datetime,
        },

    )
    assert_frame_equal(sim.waitlist, expected)


def test_candidate_removed_from_waitlist(sim):

    candidates = pl.DataFrame(
        data={
            'PX_ID': [1, 2],
            'edt': [
                datetime.datetime(2020, 1, 1),
                datetime.datetime(2021, 1, 1),
            ],
        },
        schema={
            'PX_ID': pl.Int32,
            'edt': pl.Datetime,
        },
    )
    sim.load_candidates(candidates, 'edt')
    removals = pl.DataFrame(
        data={
            'PX_ID': [1],
            'rem_dt': [
                datetime.datetime(2022, 1, 1),
            ],
        },
        schema={
            'PX_ID': pl.Int32,
            'rem_dt': pl.Datetime,
        },
    )
    sim.load_removals(removals, 'rem_dt')
    sim.run('')
    expected_waitlist = pl.DataFrame(
        data={
            'PX_ID': [2],
            'edt': [datetime.datetime(2021, 1, 1)],
        },
        schema={
            'PX_ID': pl.Int32,
            'edt': pl.Datetime,
        },
    )
    assert {2} == sim._waitlist_ids
    assert_frame_equal(sim.waitlist, expected_waitlist)
    expected_removals = pl.DataFrame(
        data={
            'PX_ID': [1],
            'edt': [datetime.datetime(2020, 1, 1)],
        },
        schema={
            'PX_ID': pl.Int32,
            'edt': pl.Datetime,
        },
    )
    assert_frame_equal(sim.removals, expected_removals)


def test_candidate_transplanted(sim):

    candidates = pl.DataFrame(
        data={
            'PX_ID': [1],
            'listing_dt': [
                datetime.datetime(2020, 1, 1),
            ],
        },
        schema={
            'PX_ID': pl.Int32,
            'listing_dt': pl.Datetime,
        },
    )
    sim.load_candidates(candidates, 'listing_dt')
    donors = pl.DataFrame(
        data={
            'DONOR_ID': [1],
            'recov_dt': [
                datetime.datetime(2021, 1, 1),
            ],
        },
        schema={
            'DONOR_ID': pl.Int32,
            'recov_dt': pl.Datetime,
        },
    )
    sim.load_donors(donors, 'recov_dt')
    def allocate(df): return df
    sim.run(allocate)
    expected = pl.DataFrame(
        data={
            'PX_ID': [1],
            'listing_dt': [
                datetime.datetime(2020, 1, 1),
            ],
            'DONOR_ID': [1],
            'recov_dt': [
                datetime.datetime(2021, 1, 1),
            ],
        },
        schema={
            'PX_ID': pl.Int32,
            'listing_dt': pl.Datetime,
            'DONOR_ID': pl.Int32,
            'recov_dt': pl.Datetime,
        },
    )
    assert_frame_equal(sim.transplants, expected)
    assert sim._waitlist_ids == set()
    assert sim._transplant_ids == {1}


def test_removal_after_transplant(sim):

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
    removals = pl.DataFrame(
        data={
            'PX_ID': [1],
            'rem_dt': [
                datetime.datetime(2022, 1, 1),
            ],
        },
        schema={
            'PX_ID': pl.Int32,
            'rem_dt': pl.Datetime,
        },
    )
    sim.load_removals(removals, 'rem_dt')
    donors = pl.DataFrame(
        data={
            'DONOR_ID': [1],
            'recovery_dt': [
                datetime.datetime(2021, 1, 1),
            ],
        },
        schema={
            'DONOR_ID': pl.Int32,
            'recovery_dt': pl.Datetime,
        },
    )
    sim.load_donors(donors, 'recovery_dt')
    sim.run(lambda df: df)


def test_candidate_already_transplanted(sim):

    candidates = pl.DataFrame(
        data={
            'PX_ID': [1, 1, 2],
            'edt': [
                datetime.datetime(2020, 1, 1),
                datetime.datetime(2022, 1, 1),
                datetime.datetime(2020, 6, 1),
            ],
        },
        schema={
            'PX_ID': pl.Int32,
            'edt': pl.Datetime,
        },
    )
    donors = pl.DataFrame(
        data={
            'DONOR_ID': [1],
            'edt': [
                datetime.datetime(2021, 1, 1),
            ],
        },
        schema={
            'DONOR_ID': pl.Int32,
            'edt': pl.Datetime,
        },
    )
    sim.load_candidates(candidates, 'edt')
    sim.load_donors(donors, 'edt')
    sim.run(lambda df: df.head(1))
    expected_waitlist = pl.DataFrame(
        data={
            'PX_ID': [2],
            'edt': datetime.datetime(2020, 6, 1),
        },
        schema={
            'PX_ID': pl.Int32,
            'edt': pl.Datetime,
        },
    )
    assert sim._waitlist_ids == {2}
    assert_frame_equal(sim.waitlist, expected_waitlist)


def test_transplants_accessable_after_context():

    candidates = pl.DataFrame(
        data={'PX_ID': [1], 'edt': datetime.datetime(2020, 1, 1)},
    )
    with OrganAllocationSimulator() as sim:
        sim.load_candidates(candidates, 'edt')
        sim.run(lambda df: df.head(1))

    assert isinstance(sim.transplants, pl.DataFrame)


def test_removals_accessable_after_context():

    candidates = pl.DataFrame(
        data={'PX_ID': [1], 'edt': datetime.datetime(2020, 1, 1)},
    )
    with OrganAllocationSimulator() as sim:
        sim.load_candidates(candidates, 'edt')
        sim.run(lambda df: df.head(1))

    assert isinstance(sim.removals, pl.DataFrame)


def test_waitlist_accessable_after_context():

    candidates = pl.DataFrame(
        data={'PX_ID': [1], 'edt': datetime.datetime(2020, 1, 1)},
    )
    with OrganAllocationSimulator() as sim:
        sim.load_candidates(candidates, 'edt')
        sim.run(lambda df: df.head(1))

    assert isinstance(sim.waitlist, pl.DataFrame)


def test_null_values_in_data(sim):

    candidates = pl.DataFrame(
        data={
            'PX_ID': [1, 2],
            'CAN_LISTING_DT': [
                datetime.datetime(2020, 1, 1),
                datetime.datetime(2021, 1, 1),
            ],
            'ctr': ['A', None],
        },
    )
    donors = pl.DataFrame(
        data={
            'DONOR_ID': [1],
            'DON_RECOV_DT': [datetime.datetime(2022, 1, 1)],
        },
    )
    sim.load_candidates(candidates, 'CAN_LISTING_DT')
    sim.load_donors(donors, 'DON_RECOV_DT')
    sim.run(lambda df: df.head(1))

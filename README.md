[![build status](https://github.com/HHRI-Transplantation/organ-allocation-simulator/actions/workflows/main.yml/badge.svg)](https://github.com/HHRI-Transplantation/organ-allocation-simulator/actions/workflows/main.yml)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/HHRI-Transplantation/organ-allocation-simulator/main.svg)](https://results.pre-commit.ci/latest/github/HHRI-Transplantation/organ-allocation-simulator/main)

# oasim

Organ Allocation Simulator?

# Download

In the future I hope to upload this to pypi. For now pip install
directly from git.

```
> pip install git+https://github.com/HHRI-Transplantation/organ-allocation-simulator
```

# Usage
Main use is through the `OrganAllocationSimulator`class[^1],
which is used as a context manager.

[^1]: It's really a context manager wrapping the class `_OrganAllocationSimulator`.

```python
from oasim import OrganAllocationSimulator

with OrganAllocationSimulator() as sim:
    ...
```

The `OrganAllocationSimulator` class supports APIs for loading
candidate and donor data into the instance using data stored as
a polars dataframe. For example, you can load candidate listing data
and status updates using the `load_candidates` API, which requires
a polars dataframe and a indication of which column records the date/time
of the candidate event.

```python
import datetime

import polars as pl

# These would typically be built from SRTR SAFs or
# OPTN STAR files.
cand_listings = pl.DataFrame(
    data={
        'PX_ID': [1, 2],
        'CAN_LISTING_DT': [
            datetime.datetime(2020, 1, 1),
            datetime.datetime(2021, 1, 1),
        ],
    },
    schema={
        'PX_ID': pl.Int64,
        'CAN_LISTING_DT': pl.Datetime,
    },
)
cand_updates = pl.DataFrame(
    data={
        'PX_ID': [1, 1, 2],
        'CANHX_BEGIN_DT_TM': [
            datetime.datetime(2020, 2, 1),
            datetime.datetime(2021, 4, 1),
            datetime.datetime(2021, 6, 1),
        ],
        'CANHX_STAT_CD': [6237, 6238, 6215],
    },
    schema={
        'PX_ID': pl.Int64,
        'CANHX_BEGIN_DT_TM': pl.Datetime,
        'CANHX_STAT_CD': pl.Float64,
    },
)
with OrganAllocationSimulator() as sim:
    sim.load_candidates(cand_listings, 'CAN_LISTING_DT')
    sim.load_candidates(cand_updates, 'CANHX_BEGIN_DT_TM')
```

Candidate removals from the waitlist need to be added using
the `load_removals` API, similarly requiring a polars dataframe
and an indication of which column records the date/time of the
removal event.

```python
...

cand_removals = pl.DataFrame(
    data={
        'PX_ID': [1, 2],
        'CAN_REM_DT': [
            datetime.datetime(2021, 8, 1),
            datetime.datetime(2022, 1, 1),
        ],
        'CAN_REM_CD': [8, 13],
    },
    schema={
        'PX_ID': pl.Int64,
        'CAN_REM_DT': pl.Datetime,
        'CAN_REM_CD': pl.Float64,
    },
)
with OrganAllocationSimulator() as sim:
    sim.load_candidates(cand_listings, 'CAN_LISTING_DT')
    sim.load_candidates(cand_updates, 'CANHX_BEGIN_DT_TM')
    sim.load_removals(cand_removals, 'CAN_REM_DT')
```

Donor events are added to the simulator using the `load_donors`
API, which also requires a dataframe and an indication of which
column indicates the date/time the donor event occurs.

```python
...
donors = pl.DataFrame(
    data={
        'DONOR_ID': [1],
        'DON_RECOV_DT': [datetime.datetime(2021, 2, 1)],
    },
    schema={
        'DONOR_ID': pl.Int64,
        'DON_RECOV_DT': pl.Datetime,
    },
)
with OrganAllocationSimulator() as sim:
    sim.load_candidates(cand_listings, 'CAN_LISTING_DT')
    sim.load_candidates(cand_updates, 'CANHX_BEGIN_DT_TM')
    sim.load_removals(cand_removals, 'CAN_REM_DT')
    sim.load_donors(donors, 'DON_RECOV_DT')
```

Once all the candidate, removal, and donor events have been
added to the simulator, you can run the simulation. This requires
you supply a function which takes at least a polars dataframe as
its input and returns a dataframe as its output. The input
dataframe represents the state of the waitlist at the time a donor
event occurs, and the dataframe returned should be the rows of
the waitlist who were transplanted.

After the simulation is run, you have access to several
attributes:
- transplants: a polars dataframe storing the transplants with information
about the candidate/donor at the time of transplant.
- removals: a polars dataframe storing the non-transplant
removals with information about the candidate at removal
- waitlist: a polars dataframe storing the waitlist after all
events have been processed.

```python
...
def first_come_first_serve(waitlist: pl.DataFrame) -> pl.DataFrame:
    return waitlist.head(1)

with OrganAllocationSimulator() as sim:
    sim.load_candidates(cand_listings, 'CAN_LISTING_DT')
    sim.load_candidates(cand_updates, 'CANHX_BEGIN_DT_TM')
    sim.load_removals(cand_removals, 'CAN_REM_DT')
    sim.load_donors(donors, 'DON_RECOV_DT')
    sim.run(first_come_first_serve)

print(sim.transplants)
'''
┌───────┬─────────────┬─────────────┬─────────────┬──────────┬─────────────┐
│ PX_ID ┆ CAN_LISTING ┆ CANHX_BEGIN ┆ CANHX_STAT_ ┆ DONOR_ID ┆ DON_RECOV_D │
│ ---   ┆ _DT         ┆ _DT_TM      ┆ CD          ┆ ---      ┆ T           │
│ i64   ┆ ---         ┆ ---         ┆ ---         ┆ i64      ┆ ---         │
│       ┆ datetime[μs ┆ datetime[μs ┆ f64         ┆          ┆ datetime[μs │
│       ┆ ]           ┆ ]           ┆             ┆          ┆ ]           │
╞═══════╪═════════════╪═════════════╪═════════════╪══════════╪═════════════╡
│ 1     ┆ 2020-01-01  ┆ 2020-02-01  ┆ 6237.0      ┆ 1        ┆ 2021-02-01  │
│       ┆ 00:00:00    ┆ 00:00:00    ┆             ┆          ┆ 00:00:00    │
└───────┴─────────────┴─────────────┴─────────────┴──────────┴─────────────┘
'''
print(sim.removals)
'''
┌───────┬─────────────────────┬─────────────────────┬───────────────┐
│ PX_ID ┆ CAN_LISTING_DT      ┆ CANHX_BEGIN_DT_TM   ┆ CANHX_STAT_CD │
│ ---   ┆ ---                 ┆ ---                 ┆ ---           │
│ i64   ┆ datetime[μs]        ┆ datetime[μs]        ┆ f64           │
╞═══════╪═════════════════════╪═════════════════════╪═══════════════╡
│ 2     ┆ 2021-01-01 00:00:00 ┆ 2021-06-01 00:00:00 ┆ 6215.0        │
└───────┴─────────────────────┴─────────────────────┴───────────────┘
'''

print(sim.waitlist)
'''
┌───────┬────────────────┬───────────────────┬───────────────┐
│ PX_ID ┆ CAN_LISTING_DT ┆ CANHX_BEGIN_DT_TM ┆ CANHX_STAT_CD │
│ ---   ┆ ---            ┆ ---               ┆ ---           │
│ i64   ┆ datetime[μs]   ┆ datetime[μs]      ┆ f64           │
╞═══════╪════════════════╪═══════════════════╪═══════════════╡
└───────┴────────────────┴───────────────────┴───────────────┘
'''
```

Note that this is a incredibly simplistic version of an allocation
function. A more complete one would include screening candidates
from the waitlist who are incompatible with the donor, sorting
the resulting candidates according to some policy, and then
predicting which candidate (if any) would accept an organ offer.

 ## Advanced Usage

I assume you are using the SRTR SAFs and therefore the candidate
identifier is `PX_ID` and the donor identifier is `DONOR_ID`.
If this is not the case for you, then you can set the candidate and
donor identifiers when you instantiate the class.

```python
with OrganAllocationSimulator(
    candidate_id='CUSTOM_CANDIDATE_ID',
    donor_id='CUSTUM_DONOR_ID',
) as sim:
    ...
```

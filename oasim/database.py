from __future__ import annotations

import sqlite3
from collections.abc import Sequence

import polars as pl

from oasim.objects import _Donor
from oasim.objects import _Event


def _question_marks(n: int) -> str:

    if n <= 0:
        raise ValueError(f'got {n=}, requires n>0')

    return '(' + ','.join(n*['?']) + ')'


def _format_table_columns(
    cols: tuple[str, ...],
    primary_key: str | None = None,
) -> str:
    col = cols[0]
    s = f'[{col}]'
    if col == primary_key:
        s += ' INTEGER PRIMARY KEY'

    for col in cols[1:]:
        s += f', [{col}]'
        if col == primary_key:
            s += ' INTEGER PRIMARY KEY'
    return '(' + s + ')'


def _create_table(
    conn: sqlite3.Connection,
    name: str,
    cols: tuple[str, ...],
    primary_key: str | None = None,
) -> None:

    tbl_cols = _format_table_columns(cols, primary_key)
    cursor = conn.cursor()
    cursor.execute(f'create table {name} {tbl_cols}')


def _add_event_data_to_table(
    conn: sqlite3.Connection,
    event: _Event,
    tbl_name: str,
) -> None:

    cols = tuple(event.data.keys())
    fmt_cols = _format_table_columns(cols)
    event_values = (tuple(event.data.values()),)
    statement = f'''\
INSERT INTO {tbl_name} {fmt_cols}
VALUES {_question_marks(len(cols))}
'''
    cursor = conn.cursor()
    cursor.executemany(
        statement,
        event_values,
    )


def _format_sql_param_set_values(
    cols: Sequence[str],
) -> str:

    return ', '.join([f'[{c}]=?' for c in cols])


def _update_event_data_in_table(
    conn: sqlite3.Connection,
    event: _Event,
    tbl_name: str,
    id_col: str,
) -> None:
    statement = f'''\
UPDATE {tbl_name}

SET {_format_sql_param_set_values(list(event.data))}

WHERE {id_col}={event.id};
'''
    cursor = conn.cursor()
    cursor.execute(
        statement,
        tuple(event.data.values()),
    )


def _remove_candidate_from_waitlist(
    conn: sqlite3.Connection,
    id_col: str,
    id_val: int,
) -> None:
    statement = f'DELETE FROM waitlist WHERE {id_col}={id_val}'
    cursor = conn.cursor()
    cursor.execute(statement)


def _move_candidate_from_waitlist_to_removals(
    conn: sqlite3.Connection,
    id_col: str,
    id_val: int,
) -> None:

    cursor = conn.cursor()
    cursor.execute(
        f'''
INSERT INTO removals

SELECT * FROM WAITLIST

WHERE {id_col}={id_val}
''',
    )
    _remove_candidate_from_waitlist(
        conn,
        id_col,
        id_val,
    )


def _get_table(
    conn: sqlite3.Connection,
    uri: str,
    schema: pl.Schema,
    table: str,
) -> pl.DataFrame:

    try:
        df = _get_table_uri(
            conn,
            uri,
            schema,
            table,
        )
    except RuntimeError:  # NULL value issues
        df = _get_table_conn(
            conn,
            schema,
            table,
        )

    return df


def _get_table_uri(
    conn: sqlite3.Connection,
    uri: str,
    schema: pl.Schema,
    table: str,
) -> pl.DataFrame:
    conn.commit()
    df = pl.read_database_uri(
        f'select * from {table}',
        uri,
        schema_overrides=schema,
    )

    return df


def _split_schema(
    s: pl.Schema,
) -> tuple[pl.Schema, pl.Schema, pl.Schema]:
    '''
        Because schema_overrides doesn't work to convert
        a stringified datetime/date to a date/datetime
        for read_database
    '''

    date_schema = pl.Schema()
    datetime_schema = pl.Schema()
    other_schema = pl.Schema()
    for col, dtype in s.items():
        if dtype == pl.Date:
            date_schema[col] = dtype
        elif dtype == pl.Datetime:
            datetime_schema[col] = dtype
        else:
            other_schema[col] = dtype

    return date_schema, datetime_schema, other_schema


def _get_table_conn(
    conn: sqlite3.Connection,
    schema: pl.Schema,
    table: str,
) -> pl.DataFrame:

    (
        d_schema,
        dt_schema,
        other_schema,
    ) = _split_schema(schema)

    df = pl.read_database(
        f'select * from {table}',
        conn,
        infer_schema_length=1000,
    )

    df = (
        df
        .with_columns(
            pl.col(d_schema.keys()).str.to_date(),
            pl.col(dt_schema.keys()).str.to_datetime(),
        )
        .with_columns(
            [
                pl.col(col).cast(dtype)
                for col, dtype in other_schema.items()
            ],
        )
    )
    return df


def _combine_waitlist_with_donor(
    waitlist: pl.DataFrame,
    donor: _Donor,
    donor_schema: pl.Schema,
) -> pl.DataFrame:

    return (
        waitlist
        .with_columns(
            [
                pl.lit(donor.data[col])
                .cast(dtype)
                .alias(f'{(col in waitlist.columns)*"donor_"}{col}')
                for col, dtype in donor_schema.items()
            ],
        )
    )

from __future__ import annotations

import sqlite3

import polars as pl
import pytest

from oasim.database import _create_table
from oasim.database import _format_sql_param_set_values
from oasim.database import _format_table_columns
from oasim.database import _question_marks
from oasim.database import _split_schema


@pytest.mark.parametrize(
    ('columns', 'expected'),
    (
        (('a',), [('a',)]),
        (('a', 'b'), [('a',), ('b',)]),
        (('b', 'a'), [('b',), ('a',)]),
        (('space col',), [('space col',)]),
    ),
)
def test_create_table(columns, expected):

    conn = sqlite3.connect(':memory:')
    name = 'my_tbl'
    _create_table(conn, name, columns)
    c = conn.cursor()
    c.execute('''
select name

from pragma_table_info('my_tbl')
''')
    rows = c.fetchall()
    conn.close()
    assert rows == expected


@pytest.mark.parametrize(
    ('cols', 'expected'),
    (
        (('a',), '([a])'),
        (('a', 'b'), '([a], [b])'),
        (('b', 'a'), '([b], [a])'),
    ),
)
def test_format_table_columns(cols, expected):
    assert _format_table_columns(cols) == expected


@pytest.mark.parametrize(
    ('cols', 'pk', 'expected'),
    (
        (('a',), 'a', '([a] INTEGER PRIMARY KEY)'),
        (('a', 'b'), 'b', '([a], [b] INTEGER PRIMARY KEY)'),
        (('b', 'a'), 'b', '([b] INTEGER PRIMARY KEY, [a])'),
    ),
)
def test_format_table_columns_with_primary_key(cols, pk, expected):
    assert _format_table_columns(cols, pk) == expected


@pytest.mark.parametrize(
    ('d', 'expected'),
    (
        ({'a': 1}, '[a]=?'),
        ({'a': 1, 'b': 'foo'}, '[a]=?, [b]=?'),
    ),
)
def test_format_sql_param_set_values(d, expected):
    assert _format_sql_param_set_values(d) == expected


@pytest.mark.parametrize(
    ('n', 'expected'),
    (
        (1, '(?)'),
        (2, '(?,?)'),
        (5, '(?,?,?,?,?)'),
    ),
)
def test_question_marks(n, expected):
    assert _question_marks(n) == expected


@pytest.mark.parametrize(
    ('n', 'expected'),
    (
        (0, 'got n=0, requires n>0'),
        (-1, 'got n=-1, requires n>0'),
    ),
)
def test_question_marks_value_error(n, expected):

    with pytest.raises(ValueError) as excinfo:
        _question_marks(n)

    msg, = excinfo.value.args
    assert msg == expected


def test_split_schema():

    schema = pl.Schema({
        'Date': pl.Date(),
        'Datetime': pl.Datetime(),
        'String': pl.String,
        'Enum': pl.Enum(categories=['a']),
        'Categorical': pl.Categorical(),
        'Int64': pl.Int64,
        'Float64': pl.Float64,
    })
    expected = (
        pl.Schema({'Date': pl.Date()}),
        pl.Schema({'Datetime': pl.Datetime()}),
        pl.Schema({
            'String': pl.String,
            'Enum': pl.Enum(categories=['a']),
            'Categorical': pl.Categorical(),
            'Int64': pl.Int64,
            'Float64': pl.Float64,
        }),
    )
    assert _split_schema(schema) == expected

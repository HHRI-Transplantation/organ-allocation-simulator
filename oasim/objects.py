from __future__ import annotations

import datetime
import functools
from typing import Any


EVENT_SORT_RANK = {
    '_Event': 0,
    '_Candidate': 1,
    '_Donor': 2,
    '_Removal': 3,
}


@functools.total_ordering
class _Event():

    def __init__(
        self,
        id: int,
        event_datetime: datetime.date | datetime.datetime,
        data: dict[str, Any] = {},
    ) -> None:

        if isinstance(event_datetime, datetime.date):
            event_datetime = datetime.datetime(
                event_datetime.year,
                event_datetime.month,
                event_datetime.day,
            )

        self.id = id
        self.event_datetime = event_datetime
        self.data = data

    def __repr__(self) -> str:
        return (
            f'{type(self).__name__}('
            f'id={self.id!r}, '
            f'event_datetime="{self.event_datetime}")'
        )

    def __eq__(self, other: object) -> bool:

        if not isinstance(other, _Event):
            raise NotImplementedError

        else:
            return (
                (self.data == other.data) and
                (self.id == other.id) and
                (self.event_datetime == other.event_datetime) and
                (self.__class__.__name__ == other.__class__.__name__)
            )

    def __lt__(self, other: object) -> bool:

        if not isinstance(other, _Event):
            raise NotImplementedError

        else:
            return (
                (
                    self.event_datetime,
                    EVENT_SORT_RANK[self.__class__.__name__],
                ) <
                (
                    other.event_datetime,
                    EVENT_SORT_RANK[other.__class__.__name__],
                )
            )


class _Candidate(_Event):
    '''

        For adding candidates to and/or updating candidates
        on the waitlist.

    '''

    def __init__(
        self,
        id: int,
        event_datetime: datetime.date | datetime.datetime,
        data: dict[str, Any] = {},
    ) -> None:

        super().__init__(id, event_datetime, data)


class _Removal(_Event):
    '''

        For removing candidates from the waitlist.

    '''

    def __init__(
        self,
        id: int,
        event_datetime: datetime.date | datetime.datetime,
        data: dict[str, Any] = {},
    ) -> None:

        super().__init__(id, event_datetime, data)


class _Donor(_Event):

    def __init__(
        self,
        id: int,
        event_datetime: datetime.date | datetime.datetime,
        data: dict[str, Any] = {},
    ) -> None:

        super().__init__(id, event_datetime, data)

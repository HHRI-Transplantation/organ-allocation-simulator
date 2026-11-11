from __future__ import annotations

import pytest

from oasim.oasim import OrganAllocationSimulator


@pytest.fixture
def sim():
    with OrganAllocationSimulator() as s:
        yield s

import pytest
from nightcrawl.runtime import reset_all_stores


@pytest.fixture(autouse=True)
def _reset_stores():
    reset_all_stores()
    yield
    reset_all_stores()

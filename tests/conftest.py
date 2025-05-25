import pytest
from pydantic import BaseModel


class TestContent(BaseModel):
    name: str
    age: int


@pytest.fixture
def test_content():
    return TestContent(name="test", age=20)


@pytest.fixture
def test_content_class():
    return TestContent

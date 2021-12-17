from starlette.testclient import TestClient
from unittest import mock
import time_machine
from datetime import datetime
import pytest

from .main import app, handler

client = TestClient(app)


@pytest.fixture
def marty_mc_fly():
    travel = time_machine.travel('31-12-1955', tick=False)
    travel.start()
    yield
    travel.stop()


@pytest.fixture
def fake_redis():
    with mock.patch.object(handler, 'redis_cur') as fake_cursor:
        yield fake_cursor


def test_create_main(fake_redis, marty_mc_fly):
    fake_redis.get.return_value = 123
    response = client.post("/hand_history", json={'streets': [{'name': 'John'}]})
    assert response.status_code == 200
    assert response.json() == {'id': 123, 'streets': [{'id': 123}]}
    assert fake_redis.set.called
    assert mock.call('HandHistory.123.date', datetime(1955, 12, 31, 0, 0)) in fake_redis.set.call_args_list
    assert mock.call('HandHistory.123.streets.0', 123) in fake_redis.set.call_args_list
    assert mock.call('Street.123.name', 'John') in fake_redis.set.call_args_list


def test_read_main(fake_redis):
    retvals = {
        'HandHistory.123.streets.0': '345',
        'HandHistory.123.streets.1': '567',
        'HandHistory.123.date': '1955-12-31T00:00:00',
        'Street.345.name': 'John',
        'Street.567.name': 'Doe'
    }
    fake_redis.get = lambda x: retvals.get(x)
    response = client.get("/hand_history/123")
    assert response.status_code == 200
    assert response.json() == {'date': '1955-12-31T00:00:00', 'streets': [{'name': 'John'}, {'name': 'Doe'}]}

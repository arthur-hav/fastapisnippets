from starlette.testclient import TestClient
from unittest import mock
import time_machine
from datetime import datetime
import pytest

from .main import app, RedisFlattener

client = TestClient(app)


@pytest.fixture
def marty_mc_fly():
    travel = time_machine.travel('31-12-1955', tick=False)
    travel.start()
    yield
    travel.stop()


@pytest.fixture
def fake_redis():
    with mock.patch.object(RedisFlattener, 'redis_cur') as fake_cursor:
        yield fake_cursor


def test_save_main(fake_redis, marty_mc_fly):
    fake_redis.get.return_value = 123
    response = client.post("/item/", json={'streets': [{'name': 'John'}]})
    assert response.status_code == 200
    assert response.json() == {'id': 123}
    assert fake_redis.set.called
    assert mock.call('HandHistory.objects.123.date', datetime(1955, 12, 31, 0, 0)) in fake_redis.set.call_args_list
    assert mock.call('HandHistory.objects.123.streets.0', 123) in fake_redis.set.call_args_list
    assert mock.call('Street.objects.123.name', 'John') in fake_redis.set.call_args_list


def test_load_main(fake_redis):
    retvals = {
        'HandHistory.objects.123.streets.0': 345,
        'HandHistory.objects.123.date': '1955-12-31T00:00:00',
        'Street.objects.345.name': 'John'
        }

    def lbda(x):
        return retvals.get(x)
    fake_redis.get = lbda

    response = client.get("/item/123")
    assert response.status_code == 200
    assert response.json() == {'date': '1955-12-31T00:00:00', 'streets': [{'name': 'John'}]}
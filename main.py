from __future__ import annotations
from fastapi import FastAPI, Body
from typing import Optional, List, Any, Generator, get_args
from pydantic import BaseModel, Field
from datetime import datetime
import redis
from pydantic.utils import smart_deepcopy

app = FastAPI()


class RedisFlattener:
    redis_cur = redis.Redis()

    def _save_field(self, model_name: str, _id: int, field: str, value: Any):
        if isinstance(value, BaseModel):
            value = self.save(value)
        if isinstance(value, (list, tuple, Generator)):
            for i, item in enumerate(value):
                self._save_field(model_name, _id, f'{field}.{i}', item)
            return
        self.redis_cur.set(f'{model_name}.objects.{_id}.{field}', value)

    def save(self, instance: BaseModel, _id: Optional[int] = None) -> int:
        if _id is None:
            _id = self.new_id(instance.__class__)
        for field in instance.__fields__:
            self._save_field(instance.__class__.__name__, _id, field, getattr(instance, field))
        return _id

    def load(self, _id: int, model: type):
        data = {}
        for field_key, field_value in model.__fields__.items():
            value = self._get_field(model, _id, field_value.name, field_value.type_, field_value.shape)
            if value is not None:
                data[field_value.name] = value
        return model(**data)

    def _get_field(self, model, _id, field_name, field_type, shape):
        if issubclass(field_type, BaseModel):
            if shape == 1:
                _son_id = self.redis_cur.get(f'{model.__name__}.objects.{_id}.{field_name}')
                if _son_id is None:
                    return None
                return self.load(model=field_type, _id=_son_id)
            i = 0
            acc = []
            # Lists of lists currently unsupported
            value = self._get_field(model, _id, f'{field_name}.{i}', field_type, shape=1)
            while value is not None and i < 10:
                acc.append(value)
                i += 1
                value = self._get_field(field_type, _id, f'{field_name}.{i}', field_type, shape=1)
            if acc:
                return acc
        return self.redis_cur.get(f'{model.__name__}.objects.{_id}.{field_name}')

    @staticmethod
    def new_id(cls):
        RedisFlattener.redis_cur.incr(f'{cls.__name__}.id_gen')
        return RedisFlattener.redis_cur.get(f'{cls.__name__}.id_gen')


class Street(BaseModel):
    name: str = 'Preflop'


class HandHistory(BaseModel):
    date: datetime = Field(default_factory=datetime.now)
    streets: List[Street]


@app.post("/item/")
async def create_item(model: HandHistory):
    _id = RedisFlattener().save(model)
    return {'id': _id}


@app.get("/item/{id_test}")
async def read_items(id_test: int):
    return RedisFlattener().load(_id=id_test, model=HandHistory)

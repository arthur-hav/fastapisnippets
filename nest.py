from typing import Optional, Any, Generator
from pydantic import BaseModel
import redis


class RedisModelHandler:
    def __init__(self, *args, **kwargs):
        self.redis_cur = redis.Redis(*args, **kwargs)

    def _save_field(self, model_name: str, _id: int, field: str, value: Any) -> Any:
        retval = None
        if isinstance(value, BaseModel):
            retval = self.save(value)
            value = retval['id']
        if isinstance(value, (list, tuple, Generator)):
            acc = []
            for i, item in enumerate(value):
                acc.append(self._save_field(model_name, _id, f'{field}.{i}', item))
            return acc
        self.redis_cur.set(f'{model_name}.{_id}.{field}', value)
        return retval

    def save(self, instance: BaseModel, _id: Optional[int] = None) -> dict:
        if _id is None:
            _id = self.new_id()
        retval = {'id': _id}
        for field in instance.__fields__:
            save_ids = self._save_field(instance.__class__.__name__, _id, field, getattr(instance, field))
            if save_ids is not None:
                retval[field] = save_ids
        return retval

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
                _son_id = self.redis_cur.get(f'{model.__name__}.{_id}.{field_name}')
                if _son_id is None:
                    return None
                return self.load(model=field_type, _id=_son_id)
            i = 0
            acc = []
            # Lists of lists currently unsupported
            value = self._get_field(model, _id, f'{field_name}.{i}', field_type, shape=1)
            while value is not None:
                acc.append(value)
                i += 1
                value = self._get_field(model, _id, f'{field_name}.{i}', field_type, shape=1)
            if acc:
                return acc
        return self.redis_cur.get(f'{model.__name__}.{_id}.{field_name}')

    def new_id(self):
        self.redis_cur.incr(f'{self.__class__.__name__}.id_gen')
        return self.redis_cur.get(f'{self.__class__.__name__}.id_gen')

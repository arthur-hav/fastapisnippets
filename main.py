from fastapi import FastAPI
from .nest import RedisModelHandler
from datetime import datetime
from typing import List, Optional
from pydantic import Field, BaseModel

app = FastAPI()
handler = RedisModelHandler()


class Street(BaseModel):
    name: str = 'Preflop'


class HandHistory(BaseModel):
    date: datetime = Field(default_factory=datetime.now)
    streets: List[Street]


@app.post("/hand_history")
async def create_hand_history(hand_history: HandHistory):
    return handler.save(hand_history)


@app.post("/hand_history/{id_item}")
async def update_hand_history(hand_history: HandHistory, id_item: int):
    return handler.save(hand_history, _id=id_item)


@app.get("/hand_history/{id_item}")
async def read_hand_history(id_item: int):
    return handler.load(_id=id_item, model=HandHistory)


@app.get("/street/{id_test}")
async def read_street(id_item: int):
    return handler.load(_id=id_item, model=Street)


@app.post("/street")
async def create_street(street: Street):
    return handler.save(street)


@app.post("/street/{id_test}")
async def post_street(street: Street, id_item: Optional[int] = None):
    return handler.save(_id=id_item, instance=street)

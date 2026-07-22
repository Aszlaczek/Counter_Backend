from pydantic import BaseModel
import datetime as dt

class User(BaseModel):
    id: int
    name: str
    surname: str
    username: str | None = name[0] + surname

class Person(BaseModel):
    id: int
    name: str
    surname: str
    date: str | None = dt.datetime.now().strftime("%Y-%m-%d")
    minutes: int | None = 0
    hours: int | None = 0


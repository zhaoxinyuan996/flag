from typing import Optional

from pydantic import BaseModel
from sqlalchemy import text, GenerativeSelect, ChunkedIteratorResult
from sqlalchemy.engine.result import RMKeyView, ResultMetaData
from sqlalchemy.orm import Session
from sqlalchemy.sql import coercions, roles
from sqlalchemy.sql.base import HasCompileState
from sqlalchemy.sql.selectable import TypedReturnsRows, _SelectFromElements, HasHints, HasSuffixes, HasPrefixes
from sqlmodel import Field, SQLModel, create_engine, select


class Hero(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    secret_name: str
    age: Optional[int] = None


# class Hero(BaseModel):
#     id: Optional[int]
#     name: str
#     secret_name: str
#     age: Optional[int] = None


sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=True)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def create_heroes():
    hero_1 = Hero(name="Deadpond", secret_name="Dive Wilson")
    hero_2 = Hero(name="Spider-Boy", secret_name="Pedro Parqueador")
    hero_3 = Hero(name="Rusty-Man", secret_name="Tommy Sharp", age=48)

    with Session(engine) as session:
        session.add(hero_1)
        session.add(hero_2)
        session.add(hero_3)

        session.commit()


class Query(
    GenerativeSelect,
    TypedReturnsRows,
):
    inherit_cache = True
    def __init__(self, ent):
        self._raw_columns = [
            coercions.expect(
                roles.ColumnsClauseRole, ent, apply_propagate_attrs=self
            )
        ]

        GenerativeSelect.__init__(self)

def chunks(size):  # type: ignore
    return iter(range(size))
def select_heroes():
    with Session(engine) as session:
        statement = text('select * from hero')
        statement = select(Hero)
        # statement = Query(Hero)
        result = session.execute(statement)
        print(result.context.compiled.compile_state)
        # ChunkedIteratorResult(
        #     ['hero'],
        #     chunks(1),
        #     True,
        #     results,
        #     False
        # )
        print(result.all())


def main():
    # create_db_and_tables()
    # create_heroes()
    select_heroes()


if __name__ == "__main__":
    main()
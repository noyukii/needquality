from fastapi import Depends, FastAPI, HTTPException

app = FastAPI()


class User:
    def __init__(self, id: str) -> None:
        self.id = id


def get_db():
    return db


def get_current_user(db=Depends(get_db)) -> User:
    return User("u_ada")


class Store:
    def __init__(self) -> None:
        self.items = {
            "i_1": {"id": "i_1", "owner_id": "u_ada"},
            "i_2": {"id": "i_2", "owner_id": "u_other"},
        }

    def get(self, id: str):
        return self.items.get(id)

    def delete_for(self, id: str, owner_id: str) -> None:
        item = self.items.get(id)
        if item is None or item["owner_id"] != owner_id:
            raise KeyError(id)
        del self.items[id]


db = Store()


@app.get("/items/{id}")
def get_item(id: str, user: User = Depends(get_current_user), store=Depends(get_db)):
    item = store.get(id)
    if item is None or item["owner_id"] != user.id:
        raise HTTPException(status_code=404)
    return item

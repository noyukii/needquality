# FastAPI

Read this when the patch touches FastAPI routes, dependencies, or
Pydantic request/response models. [SKILL.md](../SKILL.md) still
applies.

## Routes and dependencies

Copy the sibling route's `Depends(get_current_user)` / `Depends(get_db)`
— a module-global `db` or `current_user` is slop, and a new route
without the auth dependency its siblings carry is a hole. If the tree
has `APIRouter` modules, add the route there — not a new dump in
`main.py`. Match the sibling's response model, status code, and error
shape.

```python
# slop
@app.get("/items/{item_id}")
def get_item(item_id: int):
    return db.query(Item).get(item_id)

# needquality
@router.get("/items/{item_id}", response_model=ItemOut)
def get_item(
    item_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ItemOut:
    item = db.get(Item, item_id)
    if item is None or item.owner_id != user.id:
        raise HTTPException(status_code=404)
    return item
```

## Async and errors

`async def` only when the body awaits — a blocking DB call inside an
async route stalls the event loop; a sync route runs in the
threadpool. Failures are `HTTPException` (or the repo's exception
handlers) — `return {"error": ...}` with a 200 is not an error. Don't
`asyncio.create_task` for request work when the file already uses
`BackgroundTasks`; don't `asyncio.gather` an unbounded user-sized
list.

## Pydantic

Match the file's Pydantic major: v2 (`ConfigDict`, `field_validator`,
`model_dump`) vs v1 (`class Config`, `@validator`, `.dict()`) — do not
mix them in one model. Request bodies parse into models with explicit
fields; `response_model` (or the return annotation) bounds what leaks
out — returning the ORM object raw can expose columns the sibling
routes hide. Ownership and rate limits on uploads and outbound calls:
the `needquality-trust` skill.

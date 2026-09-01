# Django

Read this when the patch touches Django models, views, forms, admin,
or settings. [SKILL.md](../SKILL.md) still applies.

## Queries

A loop that touches `row.relation` is N+1 — `select_related` (FK) /
`prefetch_related` (M2M/reverse), or annotate. Querysets that can grow
take `.order_by(...)[:n]`. `is_authenticated` is not ownership —
filter the queryset by owner:

```python
# slop
post = Post.objects.get(pk=pk)

# needquality
post = get_object_or_404(Post, pk=pk, owner=request.user)
```

Conditional state changes are one query (`.filter(...).update(...)`,
`F()` expressions), not read-modify-save. Uniqueness is a DB
constraint plus the caught `IntegrityError`, not an `exists()` check.
Multi-write operations wrap in `transaction.atomic()`.

## Input and output

Allowlist fields: a `ModelForm` / DRF serializer with explicit
`fields`, never `Model.objects.filter(**request.GET)` or
`__dict__.update(request.POST)`. Templates auto-escape — no `|safe` /
`mark_safe` on user text. CSRF middleware stays on; a new view does
not get `@csrf_exempt` to make a test pass.

## Models and migrations

A model change ships its migration in the same patch. Do not drop or
rename a column the running code still reads — expand-contract. Match
the existing app layout; do not invent a new app for one model. No new
signals for one caller — call the function. `null=True` on a
`CharField` when the codebase uses `blank=True, default=""` is a
convention miss — match the neighbors.

## Settings and jobs

No `DEBUG = True`, `ALLOWED_HOSTS = ['*']`, or hardcoded
`SECRET_KEY` in a committed settings file — environment, like the repo
already does. Slow work goes through the installed task queue
(Celery, django-tasks), not a request-thread loop. Auth, uploads,
webhooks: the `needquality-trust` skill. Raw SQL: the `needquality-sql` skill.

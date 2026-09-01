# ASP.NET Core

Read this when the patch touches ASP.NET Core endpoints, controllers,
middleware, or EF Core. [SKILL.md](../SKILL.md) still applies.

## Endpoints

Match the repo: minimal APIs vs controllers — do not introduce the
other style for one route. A new endpoint copies its sibling's
`[Authorize]` / policy and validation; a logged-in user's route id
still needs an owner check in the query. Bind requests to DTOs, not
EF entities — binding the entity is mass assignment. Failures flow
through the existing exception middleware / `ProblemDetails` — not a
per-action try/catch returning `Ok(new { error })`.

## Dependency injection

Respect lifetimes: a scoped service (like `DbContext`) injected into a
singleton is a captive dependency that breaks under load — take
`IServiceScopeFactory` or restructure. `HttpClient` comes from
`IHttpClientFactory` / typed clients the repo configures. Pass the
request's `CancellationToken` into queries and outbound calls.

## EF Core

A loop touching `entity.Navigation` is N+1 — `Include` / projection /
one `Where(x => ids.Contains(x.Id))`. Read-only queries take
`AsNoTracking` when the repo does. Model changes ship a migration in
the same patch; do not drop a column running code still reads.
Uniqueness is a unique index plus the caught `DbUpdateException`, not
`AnyAsync` then `Add`. Never concatenate user input into
`FromSqlRaw` — `FromSqlInterpolated` or parameters.

```csharp
// slop — race
if (!await db.Users.AnyAsync(u => u.Email == email))
    db.Users.Add(new User { Email = email });

// needquality — unique index owns it
db.Users.Add(new User { Email = email });
try { await db.SaveChangesAsync(ct); }
catch (DbUpdateException e) when (IsUniqueViolation(e))
{ return Conflict(); }
```

## Config

Secrets stay out of committed `appsettings.json` — user-secrets,
environment, or the repo's vault binding. New settings use the options
pattern (`IOptions<T>`) next to existing ones, not ad-hoc
`Configuration["key"]` strings scattered in handlers. Auth, uploads,
webhooks, outbound HTTP: the `needquality-trust` skill.

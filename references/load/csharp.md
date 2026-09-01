# C#

Read this when touching `.cs` / `.csproj` / `.razor`. Core rules in
`SKILL.md` still apply. ASP.NET Core web code:
[aspnet.md](csharp/aspnet.md).

## Format

Match the file: `var` vs explicit types, expression-bodied members,
file-scoped namespaces, records vs classes. Run `dotnet format` only
when the repo configures it. Honor nullable reference types when the
project enables them — do not silence a warning with `!` on wire data.

## Async

`async void` swallows exceptions — only event handlers get it; return
`Task`. `.Result` / `.Wait()` / `GetAwaiter().GetResult()` on a hot
path invites deadlock and hides the async chain — await it.

```csharp
// slop
public void Save(User user)
{
    _repo.SaveAsync(user).Wait();
}

// needquality
public async Task SaveAsync(User user, CancellationToken ct)
{
    await _repo.SaveAsync(user, ct);
}
```

A fired-and-forgotten `Task` whose exception nobody observes is a
swallowed failure. Pass the `CancellationToken` through when the
signature already has one.

## Errors

Empty `catch`, `catch (Exception) { return null; }`, and
log-and-continue swallow bugs. Catch the exception you can handle,
add context, rethrow with `throw;` (not `throw ex;`, which resets the
stack). Do not use exceptions for expected control flow the file
handles with `TryParse` / result types — match the file.

## Structure

No `IUserService` + `UserService` pair with a single implementation
unless the repo's DI convention already does this everywhere — then
match it. No `Helpers.cs` / `Utils.cs` dump for one method. A record
beats a property-bag class for values. `IDisposable` things are
disposed: `using` declaration or DI container ownership, not manual
hope.

## Time, strings, money

Instants are `DateTimeOffset` / `DateTime.UtcNow`, never
`DateTime.Now` for stored or compared times. Wall clock takes an
explicit `TimeZoneInfo`. Money is `decimal`, never `double` /
`float`. Compare user identifiers with an explicit
`StringComparison`; normalize before uniqueness checks. `==` on
strings is ordinal — fine — but `CompareTo` and sorting are
culture-sensitive; say which you mean.

## Shared state and I/O

Check-then-act on a shared dictionary or row is a race —
`ConcurrentDictionary.TryAdd`, a unique constraint, or one conditional
`UPDATE`. One `HttpClient` via `IHttpClientFactory` or a static
instance — never `new HttpClient()` per request (socket exhaustion).
Set a timeout; check `IsSuccessStatusCode` (or `EnsureSuccessStatusCode`)
before treating the body as success. LINQ queries are lazy — a query
enumerated twice runs twice; materialize once with `ToList()` when you
mean once.

Never interpolate user input into SQL — parameters, including
`FromSqlInterpolated` over `FromSqlRaw` string concat. A query per
loop element is N+1. A list query that can grow takes a bound. A
logged-in user's route id still needs an owner check. User input
never reaches `Process.Start` via a shell string — argument list.
HTTP / auth / money: [trust.md](trust.md).

## Leftovers

No `Console.WriteLine` debug in libraries — the configured logger. No
unused usings. Do not add `#pragma warning disable` for a diagnostic
this patch introduced. No secrets in source or committed
`appsettings.json` — user-secrets / environment / vault. Never bypass
certificate validation with a permissive
`ServerCertificateCustomValidationCallback`. Never
`Path.Combine(uploadDir, userFileName)` into a read/write without
validating the resolved path. Don't wrap a boolean; else after
`return` is noise.

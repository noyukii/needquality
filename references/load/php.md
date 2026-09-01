# PHP

Read this when touching `.php` / `composer.json`. Core rules in
`SKILL.md` still apply. Laravel app code: [laravel.md](php/laravel.md).

## Format

Match the file: `declare(strict_types=1)` presence, array syntax,
PSR-12 vs local style. Run the repo's fixer (`php-cs-fixer`, `pint`)
only when configured. Use the autoloader — no `require` of class files
in a Composer project.

## Comparisons and errors

`==` coerces (`0 == "a"`, `"1" == "01"`) — use `===` / `!==` unless
the file deliberately coerces. `@` error suppression hides the
failure; handle or let it throw. Empty `catch` and catch-log-continue
swallow bugs — catch the exception you can handle, add context,
rethrow.

```php
// slop
$data = @json_decode($body, true) ?: [];

// needquality
$data = json_decode($body, true, 512, JSON_THROW_ON_ERROR);
```

Functions that return `false` on failure (`fopen`, `file_get_contents`,
`strtotime`) get their return checked — `false` is not a value to pass
along. Match the file's convention: exceptions or checked returns, not
a mix you introduce.

## Structure

No `helpers.php` / `functions.php` dump for one function in a
namespaced codebase — put it in the class that calls it. Match the
repo's PSR-4 layout. A readonly class / promoted constructor property
beats getter/setter ceremony when the PHP version has it.

## Time, strings, money

`DateTimeImmutable` with an explicit `DateTimeZone`, not `date()` /
`strtotime()` math on the server default zone. Money is integer cents
or `BCMath`/decimal strings — never float; `intval($price * 100)` is
already broken. `strlen` is bytes — `mb_strlen` / `mb_substr` for user
text. Normalize identifiers (`Normalizer::normalize`) before
uniqueness checks.

## Shared state and I/O

Check-then-act (`SELECT` then `INSERT`) is a race — a unique index
plus a caught duplicate-key error, or one conditional `UPDATE`. HTTP
calls (curl, Guzzle) get explicit timeouts; check the status code
before treating the body as success.

Never interpolate user input into SQL — PDO / mysqli prepared
statements with bound parameters, always. Output into HTML goes
through `htmlspecialchars` (or the template engine's default escape) —
echoing request data raw is XSS. A query per loop element is N+1. A
logged-in user's id parameter still needs an owner check.

User input never reaches `include` / `require`, `unlink`, `fopen`,
`file_get_contents` (also SSRF via URL), or a `shell_exec` /
`exec` string — allowlist, resolve, and validate paths; `escapeshellarg`
each argument if a shell call is unavoidable. `unserialize` on
untrusted bytes is object injection — JSON. Passwords are
`password_hash` / `password_verify` — never `md5` / `sha1`, never a
string compare against a stored plain hash. HTTP / auth / money:
[trust.md](trust.md).

## Leftovers

No `var_dump` / `print_r` / `dd` / `die` in production paths. No
`error_reporting(0)` to hide a notice this patch caused. No hardcoded
secrets — environment/config. Don't wrap a boolean (`return $cond;`);
else after `return` is noise. Bind a repeated expression only when one
evaluation preserves mutation, timing, exceptions, and observed state.

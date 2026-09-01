# Ruby

Read this when touching `.rb` / `Gemfile` / `.rake`. Core rules in
`SKILL.md` still apply. Rails app code (models, controllers,
migrations): [rails.md](ruby/rails.md).

## Format

Match the file: quotes, hash syntax, `frozen_string_literal` magic
comment. Run `rubocop` only when the repo configures it, and only on
touched files. Match the file's iteration style (`each` vs `map` vs
comprehension-like chains) — don't rewrite loops you didn't touch.

## Errors

`rescue nil`, bare `rescue` with an empty body, and rescue-and-log
swallow bugs. Rescue the error class you can handle. Never
`rescue Exception` — it catches signals and `SystemExit`; rescue
`StandardError` subclasses.

```ruby
# slop
def parse(body)
  JSON.parse(body) rescue {}
end

# needquality
def parse(body)
  JSON.parse(body)
rescue JSON::ParserError => e
  raise InvalidRequestError, "malformed body: #{e.message}"
end
```

A method that returns `nil` on failure next to callers that never
check is invented success — raise, or return a result the caller
handles. `&.` chains through required data hide the missing value.

## Structure

No `lib/utils.rb` / `ApplicationHelper` dump for one method — put it
in the class that calls it. No `define_method` / `method_missing`
metaprogramming for one case; a plain method is the lazy rung.
Modules are for shared behavior that exists, not behavior that might.

## Time, strings, money

Instants are `Time.now.utc` (Rails: `Time.current` with the app zone).
Do not compare a naive local time to a UTC column. Money is
`BigDecimal("1.50")` or integer cents — never `Float`; never
`BigDecimal(0.1)` from a float literal. Normalize user identifiers
(`unicode_normalize(:nfc)`) before uniqueness checks.

## Shared state and I/O

Check-then-act (`exists?` then `create`) is a race — a unique index
plus rescue of the constraint error, or one conditional `UPDATE`.
`Net::HTTP` and HTTP gems get explicit open/read timeouts; check the
response code before parsing the body as success.

Never interpolate user input into SQL strings — placeholders
(`where("email = ?", email)`) or hash conditions. A query per loop
element is N+1. A query that can grow takes `.limit`. A logged-in
user's params id still needs an owner scope. User input never reaches
backticks / `system` as a shell string — array argv. `Marshal.load` /
`YAML.load` on untrusted bytes is RCE — JSON or `YAML.safe_load`.
`send(params[...])` is a ghost API — never dispatch on user input.
HTTP / auth / money: [trust.md](trust.md).

## Leftovers

No `puts` / `pp` / `binding.pry` / `byebug` in production paths. No
unused requires. Do not add `# rubocop:disable` for an offense this
patch introduced. No hardcoded secrets. Don't wrap a boolean
(`cond`, not `cond ? true : false`); else after `return` is noise.
Bind a repeated expression only when one evaluation preserves
mutation, timing, exceptions, and observed state.

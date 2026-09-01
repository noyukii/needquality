# Spring / Spring Boot

Read this when the patch touches Spring controllers, services,
repositories, or configuration. [java.md](../java.md) still applies.
Do not glob `java/`.

## Wiring

Constructor injection, matching the file — field `@Autowired` on new
code next to constructor-injected siblings is drift. Do not add a new
layer (mapper, facade, second service) for one call; put the method in
the existing service. A bean with one implementation does not need an
interface unless the repo's convention has one everywhere.

## Web boundary

Bind requests to DTOs, not entities — a `@RequestBody User` that is
also the JPA entity is mass assignment (client sets `id`, `role`).
Validate with `@Valid` and constraint annotations like the sibling
endpoints. Failures map through the existing `@ControllerAdvice` /
`ResponseStatusException` — not a per-endpoint try/catch returning
200 with an error map. A new endpoint copies its sibling's security
annotations (`@PreAuthorize`, path scoping); a logged-in user's path
id still needs an owner check.

## Data

`@Transactional` on the service boundary method; a self-invoked
`@Transactional` method (`this.helper()`) does not proxy — the
transaction silently never starts. LAZY relations touched in a loop
are N+1 — fetch join / `@EntityGraph` / one `IN` query. Derived query
methods and `@Query` with named parameters — never concatenated JPQL
or native SQL. Uniqueness is a constraint plus the caught
`DataIntegrityViolationException`, not `existsBy` then `save`.
Schema changes go through the repo's migration tool (Flyway,
Liquibase) — `ddl-auto=update` is not a migration.

```java
// slop — transaction never starts
public void register(User u) { this.saveWithAudit(u); }

@Transactional
public void saveWithAudit(User u) { ... }
```

## Config

No secrets in committed `application.yml` — environment /
`application-local` patterns the repo already uses. New config is
`@ConfigurationProperties` next to the existing ones, not scattered
`@Value` strings. Match the repo's profile convention. Auth, uploads,
webhooks, outbound HTTP: [trust.md](../trust.md).

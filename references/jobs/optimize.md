# Optimize

Read this when they said optimize, faster, or perf. Change the
bottleneck you can name. Not a new architecture.

1. Name the hot path (query, N+1, unbounded map, sync disk, the
   number they quoted). Can't name it → measure, or one question.
   Don't cache speculatively.
2. Smallest change that moves that number: index, JOIN, cap,
   reuse the existing pool. Stdlib first.
3. Keep behavior. Run the path that was slow, or say you didn't.

Don't: Redis "for later", a new queue, rewrite in a faster
language, micro-opts that don't show up in the named metric.

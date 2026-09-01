# Observability

Read this when they said instrument, add metrics, add tracing, or
observability. Add one named signal in the installed stack.

1. Find the existing logger, metric, trace, event name, sampling, and
   redaction convention. Name the operation and failure it measures.
2. Add the signal at that seam. Preserve request correlation and
   cancellation. Do not log tokens, cookies, passwords, full bodies,
   payment data, or raw user text.
3. Exercise success and failure once. Confirm the signal shape if a
   local sink exists; otherwise say delivery was not verified.

Don't: add an APM vendor, dashboard, alert, or `console.log` for one
debugging session unless requested.

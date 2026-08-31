Read this when they said cut a release, bump the version, tag this, or
GitHub release. Release work changes repository history or external
state; perform only the named publication step.

1. Read the version source, package/build metadata, changelog format,
   release script, tag prefix, and publish workflow. Do not infer them.
2. Generate notes from the named range. Update only the requested
   version and release files. Check the build and release artifact.
3. Tag or publish only when the prompt explicitly asks for it. Before
   an external release, show the exact version, range, and target.
4. Verify the tag/artifact/release by reading it back. A local build is
   not a published release.

Don't: publish a package, force-push, invent release notes, or bump
multiple version sources without the repo's convention.

# Dependency upgrade

Read this when they said upgrade deps, bump a dependency, or update
packages. One dependency, or one named group, per slice. "Move the
app to framework vNext" that changes APIs is still this job plus the
language skill for the files you edit.

1. Read the manifest and lockfile first. The installed version, not
   the requested range, is the baseline.
2. Read the release notes between installed and target. List the
   breaking changes, then grep this repo for each affected API.
3. Smallest step that satisfies the ask: patch/minor before major
   unless they named the major.
4. Bump through the repo's package manager. Never hand-edit the
   lockfile. Do not add a second lockfile or switch managers.
5. Fix only breakage the bump caused. APIs from the new version are
   available; APIs from a version you did not install are ghosts.
6. Prove: run the repo's existing build and tests fresh. Close with
   old → new, the breaking changes handled, and the command.

Don't: drive-by bump every outdated package, upgrade the toolchain
"while here", or pin versions the repo left as ranges.

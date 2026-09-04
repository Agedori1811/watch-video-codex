# Release procedure

Releases are built from tags by `.github/workflows/release.yml`. Do not tag until the
pull request CI is green.

## Prepare the release pull request

1. Update `WATCH_VIDEO_VERSION` in `watch-video`.
2. Update both plugin manifest versions.
3. Add the matching heading and release notes to `CHANGELOG.md`.
4. Regenerate the dependency lock when inline requirements changed:
   `uv lock --script watch-video`.
5. Synchronize the release payload copies under `skills/watch-video/`.
6. Run:

```bash
python scripts/check_release.py
python -m unittest discover -s tests -p 'test_*.py' -v
python tests/integration_smoke.py
bash tests/run_all.sh
uv audit --locked --script watch-video
bash scripts/build-skill.sh dist/watch.skill
```

The pull request must document any skipped or target-machine-only checks. Merge through
the normal review flow; do not bypass CI.

## Tag and publish

From the verified commit on `main`, create either a plain `vX.Y.Z` tag or the plugin
form `<name>--vX.Y.Z`, then push that exact tag. Before pushing, verify it locally:

```bash
python scripts/check_release.py --tag vX.Y.Z
git tag -a vX.Y.Z -m "watch-video X.Y.Z"
git push origin vX.Y.Z
```

The release workflow refuses a tag/version mismatch, rebuilds the skill bundle, and
publishes `watch.skill` plus `watch.skill.sha256`. After it finishes:

1. Confirm the workflow is green.
2. Download both release assets and verify the SHA-256 checksum.
3. Install the released bundle in a clean test environment.
4. Run `uv run --locked --script watch-video --diagnose` and one short local-file smoke
   test before announcing the release.

Never publish from an unreviewed branch, overwrite an existing release tag, or describe
hardware/auth paths as verified unless the checks in `VERIFICATION.md` were actually run.

# Provider-neutral protocol distribution

This directory is the temporary canonical source for the federated protocol. It is deliberately
independent from application repositories and contains no runtime state, credentials or network
client.

## Contract

- `VERSION` is the protocol semver.
- `manifest.json` is the signed-off file index for the bundle and its deterministic digest.
- `core/protocol.py` provides local `verify`, `diff`, `install` and `update` operations. Install,
  diff and update require the 40-character `--source-commit` SHA that is recorded in the consumer
  lock.
- `schemas/` contains the public lock, overlay and manifest schemas.
- `templates/` contains the safe consumer lock template; `overlays/` contains the base overlay.
- `tests/` contains parametrized, provider-neutral tests.

The bundle is verified without network access. Consumers must keep a generated
`.protocol-lock.json` beside their installed copy. `install` refuses an occupied target and
`update` refuses undeclared drift; both operations stage a complete tree before replacing the
target, so a failed copy does not leave a partially updated installation. Sensitive paths declared
by the manifest are rejected during verification.

`core/parity.py` and `schemas/semantic-overlay.schema.json` ship the portable overlay/parity
subset (1.1.0). Quality-gates and cycle-review stay out of this bundle.

The source path in a lock is the canonical relative path `federation/protocol`, never an absolute
machine path. Commands, deployment configuration, secrets and application-specific names are not
part of this distribution.

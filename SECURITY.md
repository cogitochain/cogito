# Security policy

## Supported versions

| Version | Supported |
|---|---|
| The `main` branch | yes |
| Anything older | no |

The patch stack is maintained against one Agave tag, `v4.5.0-alpha.4`, and one prototype VM commit, `585f8935f10863b31ce5fc5676aa16879a8eb1ee`. Reports against other upstream versions are welcome but are answered for these two only.

## Reporting a vulnerability

Report privately through GitHub Security Advisories on this repository (Security, then "Report a vulnerability"). Do not open a public issue for a vulnerability.

Include what you ran, what happened, and, when it concerns the running network, the transaction signature. We acknowledge a report within three days and tell you what we will do about it within ten.

## Scope

In scope:

- `chain/patches/`: the six patches to Agave and anything they allow that the unpatched node would refuse.
- `chain/minds/gen_mind.py`: a weights file that makes the generator emit a program that reads or writes outside its input, heap or read-only data, logs something other than the 16 outputs, or accepts an account.
- `chain/minds/weights.py`: a file that passes validation but is not a well-formed mind.
- `chain/minds/reference.py`: any input where the reference computation and a deployed program disagree.
- `chain/minds/vm/`: the harness reporting a match that is not one.

Out of scope:

- The SIMD-0714 prototype VM itself (temporalxyz/sbpf) and Agave upstream: report those to their maintainers. We will still want to hear when our patches make an upstream issue reachable.
- The website, the faucet and the RPC gateway: report them through the same channel, but they are not code in this repository.
- Rate limits, denial of service through volume, and the fact that every validator is operated by us (see Trust assumptions in the README).
- The $COGITO token on Solana mainnet: this repository contains no code that touches it.

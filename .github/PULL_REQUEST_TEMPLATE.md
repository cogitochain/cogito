## What this changes

## How it was checked

- [ ] `python3 -m unittest discover -s tests -v` passes
- [ ] The digit programs still match their recorded SHA-256, or the change explains why they move
- [ ] If the programs change: `chain/minds/vm/check.py` reports `mismatches=0` on an AVX-512 machine
- [ ] If a patch changes: `bash chain/patches/apply.sh <agave checkout>` applies all patches
- [ ] Any figure quoted comes from a measurement with its command and conditions

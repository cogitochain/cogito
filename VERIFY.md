# Verification

## How it was checked

1. The source as the network uses it was built and tested in a temporary tree: both digit programs generated, the unit suites run, the six patches applied to Agave at tag v4.5.0-alpha.4, and both programs run in the prototype VM (JIT and interpreter) on the twelve fixtures and compared with the reference computation.
2. A clean copy of this folder alone was built and tested the same way, with Agave fetched from GitHub and the prototype VM (commit 585f8935f10863b31ce5fc5676aa16879a8eb1ee) fetched from GitHub, built with `cargo build --release`.
3. The digit programs built from this folder are byte-identical to the deployed programs (SHA-256 checked by the unit suite).
4. Every Mermaid block in the README was rendered with mermaid-cli.

Limits: the tests show that the programs compute what the reference says and that the patches apply; they are not an audit. The VM check needs a CPU with AVX-512.

<!-- verify -->
date: 2026-11-18T20:10:48Z
toolchain: Python 3.12.3; numpy 2.5.4; Pillow 13.0.0; git 2.43.0; rustc 1.100.0; cargo 1.100.0
build: python3 chain/minds/gen_mind.py elf-vector chain/minds/digit/weights.bin out/digit-vector.so -> exit=0
build: python3 chain/minds/gen_mind.py elf-scalar chain/minds/digit/weights.bin out/digit-scalar.so -> exit=0
build: cd sbpf && cargo build --release -> exit=0
build: bash chain/minds/vm/build.sh sbpf sbpf -> exit=0
test: python3 -m unittest discover -s tests -v -> passed=35 failed=0
test: bash chain/patches/apply.sh agave -> passed=6 failed=0
test: python3 chain/minds/vm/check.py sbpf out/digit-vector.so out/digit-scalar.so chain/minds/fixtures/inputs.bin --weights chain/minds/digit/weights.bin -> passed=48 failed=0
total: passed=89 failed=0
parity: original_passed=89 github_passed=89
mermaid: rendered=4/4
<!-- /verify -->

## Source history

The commits leading up to the public import reconstruct the supplied source snapshot in dependency order. Their dates illustrate that sequence. The original development timestamps were unavailable. The verification record above retains its recorded run time.

# Contributing

Changes are welcome where they keep three things true: the generator emits the same programs for the same weights, the reference computation stays exactly the arithmetic the programs do, and every figure has a command that reproduces it.

## Toolchain

| Tool | Version | Used for |
|---|---|---|
| Python | 3.12.3 (`.python-version`) | generator, reference, training, tests |
| numpy | 2.5.4 (`requirements.txt`) | reference computation over many inputs, training |
| Pillow | 13.0.0 (`requirements.txt`) | digit preprocessing |
| git | 2.43 or newer | applying the patch stack |
| Rust | the stable toolchain the prototype VM crate selects (rustc 1.100.0 in our runs) | the VM harness |
| CPU | x86-64 with AVX-512 | running vector programs in the prototype VM |

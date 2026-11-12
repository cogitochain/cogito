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

## The commands CI runs

Lint:

```
python3 -m compileall -q chain tests
```

Build the digit mind's two programs:

```
mkdir -p out
python3 chain/minds/gen_mind.py elf-vector chain/minds/digit/weights.bin out/digit-vector.so
python3 chain/minds/gen_mind.py elf-scalar chain/minds/digit/weights.bin out/digit-scalar.so
```

Test the weights format, the reference computation, the program encodings and the scalar program's execution:

```
python3 -m unittest discover -s tests -v
```

Test that the patch stack applies to Agave at the tag:

```
git clone --depth 1 --branch v4.5.0-alpha.4 https://github.com/anza-xyz/agave agave
bash chain/patches/apply.sh agave
```

Run both programs in the prototype VM and compare with the reference (needs AVX-512; `sbpf` is a checkout of the prototype VM at commit `585f8935f10863b31ce5fc5676aa16879a8eb1ee`):

```
cd sbpf && cargo build --release && cd ..
bash chain/minds/vm/build.sh sbpf sbpf
python3 chain/minds/vm/check.py sbpf out/digit-vector.so out/digit-scalar.so chain/minds/fixtures/inputs.bin --weights chain/minds/digit/weights.bin
```

The last command runs `cargo test --release --test mind_vm` in the VM crate and ends with `mind-check ... verdict=PASS`.

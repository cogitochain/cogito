# COGITO: a neural network inside one transaction

COGITO is a Solana-compatible chain we run ourselves. Not Solana mainnet. A fork we run. Its validators carry the vector instructions of the SIMD-0714 draft's prototype, and with them a small neural network runs inside a single transaction. Every figure below is a measurement we recorded with the command that reproduces it, on named hardware; none is copied from elsewhere.

## What runs today

The node is Agave v4.5.0-alpha.4 (upstream commit ccddd3d), built unchanged except for six patch files: the SBPF virtual machine is replaced by the SIMD-0714 prototype (temporalxyz/sbpf, branch rodata-pair, commit 585f893, the sbpf version this Agave release pins), the vector instructions are switched on, the aligned memory mapping they need is forced on, the deploy environment no longer registers the vector syscall twice, two lines follow an API change in the prototype, and the smallest ledger a validator may keep is lowered from 50 million to 100,000 shreds (`0006-ledger-floor.patch`), so each validator's ledger stays inside a fixed disk share. Four validators of this build run as one private network in three emulated locations, two in Frankfurt, one in New York and one in Tokyo, with one-way delays of 40 to 63 ms between them (the distances between those cities), each holding an equal stake. Every validator is ours, all run on one server, and every one runs on a CPU with AVX-512. Transactions reach the network through one RPC gateway with per-address limits.

A mind is an Int8 network with 256 inputs, 128 hidden units and 16 outputs: h = clamp(relu(W1 x) >> 8, 0, 255), y = W2 h. Today's compilers emit neither the new vector instructions nor the prototype's SBPF v3 layout, so each mind is machine code and an ELF file written by a small generator. Every mind exists twice with the same weights: the vector program, and a scalar twin that uses only today's instruction set. A thought is one transaction whose instruction data is the 256 input bytes; the program logs its 16 outputs as one `Program data:` line, and the stock Solana CLI reads that line and the compute units (CU, compute units, Solana's measure of work) with `solana confirm -v <signature> --url <our RPC>`.

The digit mind is this network trained on MNIST, the public handwritten-digit set, scaled to 16 x 16 grayscale, trained on a CPU with the programs' exact integer arithmetic in the forward pass. Its answer is the largest of outputs 0 to 9. The chain's logged outputs equal the outputs computed off chain from the same weights: we check this on a fixed set of twelve inputs for both programs (26 of 26 transactions equal, including the trial pair), and a wrong input length is refused by the program.

## Measured

Host for every row: AMD Ryzen 9 9950X (AVX-512), 28 cores. Chain rows: our network of 4 validators with equal stake in 3 emulated locations (two in Frankfurt, one in New York, one in Tokyo), the build above, the prototype's CU schedule. Wall-time rows: the prototype VM with our network's loader configuration, p50 of 2,000 JIT runs or 50 interpreted runs per sample. Every row is p50 of the record's runs.

| Figure | Value | Conditions |
|---|---|---|
| `mind-digit-vector-program-cu` | 1,700 CU | digit mind, vector program, one MNIST test digit, includes 264 CU for logging 16 outputs |
| `mind-digit-scalar-program-cu` | 349,958 CU | digit mind, scalar twin, same input and weights (206x the vector program) |
| `mind-digit-vector-tx-cu` | 1,700 CU | whole transaction of a vector thought, no ComputeBudget instruction |
| `mind-digit-vector-site-tx-cu` | 1,850 CU | the same thought as the site sends it, with setComputeUnitLimit(10,000) (150 CU) |
| `mind-digit-scalar-tx-cu` | 350,108 CU | whole transaction of the scalar twin, with setComputeUnitLimit (150 CU) |
| `mind-transfer-tx-cu` | 150 CU | comparison: a plain System Program transfer on the same network |
| `mind-digit-vector-jit-us` | 0.822 µs | digit mind, vector program, JIT |
| `mind-digit-scalar-jit-us` | 196.6 µs | digit mind, scalar twin, JIT (239x) |
| `mind-digit-vector-interp-us` | 66.6 µs | digit mind, vector program, interpreter |
| `mind-digit-scalar-interp-us` | 724.1 µs | digit mind, scalar twin, interpreter (about 11x) |
| `mind-digit-accuracy` | 98.01 % correct | MNIST test set, 10,000 digits never used in training, exact integer arithmetic of the programs |
| `mind-largest-vector-hidden` | 19,920 hidden units | widest vector mind 256 -> H -> 16 that deploys and runs in one transaction; bounded by the 10 MiB program account, not by CU (5,418,240 multiply-adds) |
| `mind-largest-vector-program-cu` | 221,032 CU | that mind's thought, with random weights; outputs equal the reference |
| `mind-largest-scalar-hidden` | 512 hidden units | widest scalar twin that runs in one transaction; bounded by the 1,400,000 CU limit (139,264 multiply-adds) |
| `mind-largest-scalar-program-cu` | 1,398,524 CU | that scalar mind's thought |
| `net-slot-pace` | 4.94 slots/s | the network's slot pace through the gateway over 10 s, 10 samples, on the network as it runs (p99 5.08) |
| `net-confirm-fra` | 304.5 ms | a transfer from send to confirmed, client in the Frankfurt location, gateway in Frankfurt (p99 475 ms) |
| `net-confirm-nyc` | 491.5 ms | the same, client in the New York location (p99 601 ms) |
| `net-confirm-tyo` | 645 ms | the same, client in the Tokyo location (p99 802 ms) |
| `net-load-sustained` | 1,200 visitors | simulated visitors through the gateway, each sending one vector thought every 8 s and reading the slot every 2 s; the last level (doubling from 75, 60 s each) with at least 95 % confirmed and p99 at most 5 s. At 2,400 the gateway ran out of memory first; the validators kept confirming |
| `mind-trial-vector-program-cu` | 1,531 CU | the factory trial's program (fixed input, one 5-value log line), reproduced on our network |
| `mind-trial-scalar-program-cu` | 349,771 CU | the trial's scalar program (228x the vector program) |
| `mind-trial-vector-tx-cu` | 1,681 CU | the trial's vector transaction, with setComputeUnitLimit |
| `mind-trial-scalar-tx-cu` | 349,921 CU | the trial's scalar transaction, with setComputeUnitLimit |
| `mind-trial-vector-jit-us` | 0.762 µs | the trial's vector program, JIT |
| `mind-trial-scalar-jit-us` | 200.1 µs | the trial's scalar program, JIT (263x) |
| `mind-trial-vector-interp-us` | 65.2 µs | the trial's vector program, interpreter |
| `mind-trial-scalar-interp-us` | 719.7 µs | the trial's scalar program, interpreter (about 11x) |

The SIMD-0714 document reports, for an Int8 MLP 256→128→16, 490,048 CU scalar against 2,109 CU vector (232x) and 361 µs against 1.17 µs under the JIT (308x), measured on an AMD EPYC 9534. That is another machine and other kernels; it is shown beside ours, not as the same conditions. Our ratios are of the same order: 206x to 228x in CU and 239x to 263x in JIT time.

CU is the prototype's price list, not time. Under the JIT, the digit mind's vector program and its scalar twin both take about 0.57 ns per CU of their own instructions, so on this host the 1-CU price of a vector instruction is consistent with what it costs to run. Under the interpreter it is not: there the gain falls to about 11x.

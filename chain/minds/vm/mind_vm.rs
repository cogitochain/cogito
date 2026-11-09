use solana_sbpf::{
    aligned_memory::AlignedMemory,
    declare_builtin_function, ebpf,
    elf::Executable,
    memory_region::{AccessType, MemoryRegion},
    program::{BuiltinProgram, SBPFVersion},
    verifier::RequisiteVerifier,
    vm::{CallFrame, Config, EbpfVm, ExecutionMode},
};
use std::{cell::RefCell, convert::TryInto, sync::Arc, time::Instant};
use test_utils::{create_memory_mapping, TestContextObject};

thread_local! { static LOGGED: RefCell<Vec<u8>> = RefCell::new(Vec::new()); }

declare_builtin_function!(
    SyscallLog64,
    fn rust(_c: &mut TestContextObject, a: u64, b: u64, c: u64, d: u64, e: u64,) -> Result<u64, Box<dyn std::error::Error>> {
        LOGGED.with(|l| {
            let mut l = l.borrow_mut();
            l.clear();
            for v in [a, b, c, d, e] { l.extend_from_slice(&v.to_le_bytes()); }
        });
        Ok(0)
    }
);

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

declare_builtin_function!(
    SyscallLogData,
    fn rust(c: &mut TestContextObject, addr: u64, len: u64, _a: u64, _b: u64, _d: u64,) -> Result<u64, Box<dyn std::error::Error>> {
        let mut out = Vec::new();
        for i in 0..len {
            let hb = Result::from(c.memory_mapping.map(AccessType::Load, addr + 16 * i, 16))?;
            let s: &[u8] = unsafe { hb.ptr().as_ref_unchecked() };
            let p = u64::from_le_bytes(s[0..8].try_into().unwrap());
            let n = u64::from_le_bytes(s[8..16].try_into().unwrap());
            let fb = Result::from(c.memory_mapping.map(AccessType::Load, p, n))?;
            let f: &[u8] = unsafe { fb.ptr().as_ref_unchecked() };
            out.extend_from_slice(&f[..n as usize]);
        }
        LOGGED.with(|l| *l.borrow_mut() = out);
        Ok(0)
    }
);

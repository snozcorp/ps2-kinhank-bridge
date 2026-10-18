# V11 release

The public ELF has non-runtime debug metadata removed to exclude a local build path. Every PT_LOAD segment, entry point and runtime byte matches the owner's physically tested original. This metadata-only derivative has not been separately run on the console.

Public ELF SHA256: `ee9160badbcb9c479af62208ab097c71f9a20598e97c6be4ecbdc2813a89391a`

Original hardware-tested ELF SHA256: `0af4a5b34230c73bf2f733a1634bf8659cacab1e0a8914e0a5c03d761c6f5079`

The checked-in source builds the original byte-for-byte with the documented toolchain. It remains available in the owner's local workspace; private debug paths are not published. See ../../docs/BUILDING.md and ../../docs/TESTING.md.

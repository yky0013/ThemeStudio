#pragma once

namespace Functions {

// Builds a self-contained security descriptor that grants `access` to the
// "Everyone" group and the "All [Restricted] App Packages" groups, with a
// protected DACL and an Untrusted integrity label, so a shared kernel object is
// reachable from sandboxed and low-integrity target processes. `access` must be
// object-type-specific rights (not GENERIC_*) and must exclude WRITE_DAC and
// WRITE_OWNER, which would let those processes rewrite the object's ACL or take
// ownership across the trust boundary.
BOOL BuildSharedObjectSecurityDescriptor(
    ACCESS_MASK access,
    _Outptr_ PSECURITY_DESCRIPTOR* SecurityDescriptor,
    _Out_opt_ PULONG SecurityDescriptorSize);

struct DaclAce {
    PSID sid;
    ACCESS_MASK access;  // generic or specific rights
    DWORD inheritFlags;  // e.g. CONTAINER_INHERIT_ACE, OBJECT_INHERIT_ACE
};

// Idempotently ensures the file or directory has an explicit allow ACE for each
// entry, added to the existing DACL with inheritance left intact. Makes no
// change when the ACEs are already present. Returns a Win32 error code
// (ERROR_SUCCESS on success or when nothing needed to change).
DWORD EnsureFileDaclContainsAces(PCWSTR path,
                                 const DaclAce* aces,
                                 size_t aceCount);

// Same as above for a registry key (created if missing) in the 64-bit view.
DWORD EnsureRegistryKeyDaclContainsAces(HKEY hKey,
                                        PCWSTR subKey,
                                        const DaclAce* aces,
                                        size_t aceCount);

}  // namespace Functions

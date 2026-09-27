# Installer implementation checkpoints

**Time**: 2026-09-27, 15:00 +08:00
**Source**: https://jrsoftware.org/ishelp/index.php?topic=archidentifiers
**Method**: extract (web__run)
**Confidence**: low
**Insight**: Frameset page returned only the fallback table-of-contents link; it does not establish architecture semantics.

# Relevant extracted content
The page states that the browser does not support frames and links to contents.htm.

---

**Time**: 2026-09-27, 15:02 +08:00
**Source**: https://jrsoftware.org/ishelp/topic_archidentifiers.htm
**Method**: query-search (web__run official Inno documentation)
**Confidence**: high
**Insight**: x64compatible also includes Arm64 Windows emulation; x64os matches true x64 Windows. The installation package currently carries only the x64 offline Runtime, so it will explicitly exclude Arm64.

# Relevant extracted content
Architecture matchers describe x64compatible as native x64 plus capable Arm64 Windows, and x64os as only x64 Windows. The ArchitecturesAllowed page also gives `x64compatible and not arm64` as an explicit x64 package expression.

---

**Time**: 2026-09-27, 15:02 +08:00
**Source**: https://jrsoftware.org/ishelp/topic_setup_architecturesallowed.htm
**Method**: query-search (web__run official Inno documentation)
**Confidence**: high
**Insight**: A Boolean expression can restrict the supported target architectures.

# Relevant extracted content
Example: `ArchitecturesAllowed=x64compatible and not arm64`. Unsupported targets exit with WindowsVersionNotSupported.

---

**Time**: 2026-09-27, 15:02 +08:00
**Source**: https://jrsoftware.org/ishelp/topic_setup_architecturesinstallin64bitmode.htm
**Method**: query-search (web__run official Inno documentation)
**Confidence**: high
**Insight**: The 64-bit installation expression must only match 64-bit systems.

# Relevant extracted content
In 64-bit mode the installer uses the 64-bit registry view and its uninstall registration; a 64-bit payload should enable 64-bit installation mode.

---

Remaining search hits were cross references for IsX64OS, SetupArchitecture, Registry, 64-bit Install Mode, revision history and the table of contents; no additional implementation claim relies on them.

**Time**: 2026-09-27, 15:32 +08:00
**Source**: https://github.com/ant-design/ant-design-icons/blob/master/LICENSE
**Method**: extract (web__run official source repository), compared with installed @ant-design/icons/LICENSE
**Confidence**: high
**Insight**: The shared Ant Design Icons repository provides the MIT notice with Ant UED attribution. The installed sibling package includes the same text; retain that repository notice for icons-svg, whose npm tarball declares MIT but omits a standalone notice file.

# Relevant extracted content
MIT LICENSE; copyright 2018-present Ant UED. The permission and disclaimer text matches the locally installed @ant-design/icons/LICENSE. Both package metadata identify the same ant-design/ant-design-icons repository. is-mobile separately embeds its complete MIT notice in its installed README.md.

---

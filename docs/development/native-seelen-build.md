# 构建原生 Seelen 变体

此页用于 0.5 和 0.6 系列。NoSeelen 不包含此引擎，不需要这些额外工具。

上游固定版本为 Seelen 2.8.6，提交 `079c38584d48ef02e800d6f596bbef97bd00e327`。本地修改仅将开始菜单布局导出改为同一 Windows COM 提供程序，并允许在原始静态文件完全一致且签名有效时复用其签名。原始签名检查没有关闭。详细接口证据和便携工具链来源分别位于 `docs/research/20261020/native-start-layout` 和 `docs/research/20261020/seelen-build`。

构建机器需要 Node.js 24、Python 3.14、Rust `nightly-2026-05-22-x86_64-pc-windows-msvc`（包括 rustfmt）、MSVC 14.44.35207、Windows SDK 10.0.26100.0、Deno 2.9.7、CMake 4.4.4 和 NASM 3.02。Rust/C++ 工具只用于开发，不随应用分发。

可将便携工具解压到本项目 `.tools/seelen-build`，复制 `config/seelen-toolchain.example.json` 为 `.tools/seelen-build/build-env.json`，按实际解压目录修改。`${PROJECT_ROOT}` 会在运行时解析。不要将其他项目的虚拟环境、旧应用或运行目录作为新版本的依赖。便携提取方法、官方下载位置、版本、哈希与 SDK 必要组件清单见调研记录；Windows SDK 必须包含 Desktop/UAP 的 x64 导入库及头文件，不能仅有工具或 CRT。

```text
python tools/studio.py setup
python tools/studio.py prepare-runtimes
```

`prepare-runtimes` 验证官方运行包 SHA-256，提取原始静态资源，再调用当前变体构建。也可分阶段执行：

```text
python tools/build-seelen-native.py bindings
python tools/build-seelen-native.py frontend
python tools/build-seelen-native.py check
python tools/build-seelen-native.py build
python tools/build-seelen-native.py collect
python tools/studio.py build-installer
```

首次生成 Seelen 自有前端依赖前，在其源码目录执行 `npm ci --ignore-scripts --no-audit --no-fund`。`bindings` 用当前源码生成本地库，`frontend` 构建全部 27 个应用入口；二者均成功后再构建最终引擎。`build` 是需要交付 EXE 时的 release 构建；一般源码迭代使用 `check`。

`collect` 生成 `.cache/runtimes/seelen-native/native-build.json`，记录四个重编译文件、锁文件和原生修改的哈希，并更新本项目运行包清单。新安装器会核对这些哈希，不能把官方旧 EXE 当作本次原生替换结果。重编译文件不再具有上游 EXE 的 Authenticode 签名；官方 306 个静态文件及其完整性签名保持原样。

`proof` 阶段读取调用者提供的本机历史布局参考，验证实际 Rust COM 代码。个人开始菜单 JSON 不进入 Git、源码归档或安装包。构建和正常运行均不需要 PowerShell 生成参考文件；该参考仅用于本次旧实现/新实现的等价性验证。

各阶段仅修改子进程环境，没有全局 PATH 或系统工具链安装步骤。完整构建仍需下载锁定的开发依赖；已安装应用无需 Rust、Node.js、Deno、MSVC 或开发用 Python。

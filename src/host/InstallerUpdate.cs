// SPDX-License-Identifier: AGPL-3.0-or-later
using System;
using System.Diagnostics;
using System.IO;

internal static class InstallerUpdate
{
    // The backend has already checked version ordering, byte size and SHA-256.
    // Inno pads version-resource strings; compare the trimmed product/version.
    internal static ProcessStartInfo Prepare(string installer, string version, string applicationDirectory)
    {
        if (Path.GetFileName(installer) != "ThemeStudio-" + version + "-Windows-x64-Setup.exe")
            throw new InvalidDataException("更新安装包文件名与版本不匹配。");
        var info = FileVersionInfo.GetVersionInfo(installer);
        if ((info.ProductName ?? "").Trim() != "桌面主题工作室" || (info.FileVersion ?? "").Trim() != version + ".0" || !(info.FileDescription ?? "").Contains("安装"))
            throw new InvalidDataException("安装包产品信息或版本不匹配，请重新获取 ThemeStudio 安装包。");
        var directory = Path.GetFullPath(applicationDirectory);
        return new ProcessStartInfo(installer, "/DIR=\"" + directory + "\"") {
            UseShellExecute = true, Verb = "runas", WorkingDirectory = Path.GetDirectoryName(installer)
        };
    }
}

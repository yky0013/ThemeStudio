using System;
using System.IO;
using System.Linq;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text;
using System.Diagnostics;

// These declarations mirror the COM metadata embedded in the installed
// Microsoft.Windows.StartLayout.Commands assembly, but this proof does not
// reference that assembly, PowerShell, or System.Management.Automation.
[ComImport]
[Guid("75AB852C-0441-46D4-A205-EF0A33F98255")]
internal class StartLayoutCmdletComClass
{
}

[ComImport]
[Guid("0BAC4102-61E9-48A5-93DD-D295ABA65369")]
[InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
internal interface IStartLayoutCmdlet
{
    void ExportStartLayout([MarshalAs(UnmanagedType.LPWStr)] string pszFilePath);
    void ExportStartLayoutWithDesktopApplicationIDs([MarshalAs(UnmanagedType.LPWStr)] string pszFilePath);
    void ValidateLayoutFile([MarshalAs(UnmanagedType.LPWStr)] string pszFilePath);
    void ExportEdgeAssets([MarshalAs(UnmanagedType.LPWStr)] string pszFilePath);
}

internal static class NativeStartLayoutProof
{
    private static int Main(string[] args)
    {
        if (args.Length != 1)
        {
            Console.Error.WriteLine("usage: native_start_layout_proof.exe <output-json>");
            return 2;
        }

        var output = Path.GetFullPath(args[0]);
        var parent = Path.GetDirectoryName(output);
        if (!string.IsNullOrEmpty(parent)) Directory.CreateDirectory(parent);
        if (File.Exists(output)) File.Delete(output);

        Console.WriteLine("process=" + Process.GetCurrentProcess().MainModule.FileName);
        Console.WriteLine("output=" + output);
        Console.WriteLine("com-class=75AB852C-0441-46D4-A205-EF0A33F98255");
        Console.WriteLine("com-interface=0BAC4102-61E9-48A5-93DD-D295ABA65369");
        Console.WriteLine("native-dll=C:\\Windows\\System32\\StartTileData.dll");

        var loadedAutomation = Process.GetCurrentProcess().Modules
            .Cast<ProcessModule>()
            .Select(x => x.ModuleName)
            .Where(x => x.IndexOf("System.Management.Automation", StringComparison.OrdinalIgnoreCase) >= 0 ||
                        x.IndexOf("powershell", StringComparison.OrdinalIgnoreCase) >= 0)
            .ToArray();
        Console.WriteLine("automation-modules=" + (loadedAutomation.Length == 0 ? "<none>" : string.Join(",", loadedAutomation)));
        if (loadedAutomation.Length != 0) return 3;

        try
        {
            var comObject = (IStartLayoutCmdlet)new StartLayoutCmdletComClass();
            comObject.ExportStartLayout(output);
        }
        catch (COMException ex)
        {
            Console.Error.WriteLine("COM failure type=" + ex.GetType().FullName + " HRESULT=0x" + ex.HResult.ToString("X8"));
            try { Console.Error.WriteLine("message=" + ex.Message); } catch { }
            return 10;
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine("managed failure type=" + ex.GetType().FullName + " HRESULT=0x" + ex.HResult.ToString("X8"));
            try { Console.Error.WriteLine("message=" + ex.Message); } catch { }
            return 12;
        }

        if (!File.Exists(output))
        {
            Console.Error.WriteLine("COM call returned but output file was not created");
            return 11;
        }

        var bytes = File.ReadAllBytes(output);
        var text = Encoding.UTF8.GetString(bytes);
        Console.WriteLine("bytes=" + bytes.Length);
        Console.WriteLine("sha256=" + Sha256(bytes));
        Console.WriteLine("utf8-prefix=" + text.Substring(0, Math.Min(240, text.Length)).Replace("\r", "\\r").Replace("\n", "\\n"));
        Console.WriteLine("pinnedList-token-index=" + text.IndexOf("pinnedList", StringComparison.Ordinal));
        Console.WriteLine("automation-modules-after=" + string.Join(",", Process.GetCurrentProcess().Modules.Cast<ProcessModule>().Select(x => x.ModuleName).Where(x => x.IndexOf("System.Management.Automation", StringComparison.OrdinalIgnoreCase) >= 0 || x.IndexOf("powershell", StringComparison.OrdinalIgnoreCase) >= 0).ToArray()));
        return 0;
    }

    private static string Sha256(byte[] bytes)
    {
        using (var sha = SHA256.Create())
            return BitConverter.ToString(sha.ComputeHash(bytes)).Replace("-", "").ToLowerInvariant();
    }
}

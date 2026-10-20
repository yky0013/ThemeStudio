// SPDX-License-Identifier: AGPL-3.0-or-later
using Microsoft.Win32;
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;
using System.Web.Script.Serialization;
using System.Windows.Forms;

internal static class AsusCursorRecovery
{
    internal static readonly Dictionary<string, string> Files = new Dictionary<string, string> {
        {"Arrow", "Normal Select.ani"}, {"Help", "Help Select.ani"},
        {"AppStarting", "Working In Background.ani"}, {"Wait", "Busy.ani"},
        {"IBeam", "Text Select.ani"}, {"NWPen", "Handwriting.ani"},
        {"No", "Unavailable.ani"}, {"SizeNS", "Vertical Resize.ani"},
        {"SizeWE", "Horizontal Resize.ani"}, {"SizeNWSE", "Diagonal Resize 1.ani"},
        {"SizeNESW", "Diagonal Resize 2.ani"}, {"SizeAll", "Move.ani"},
        {"Hand", "Link Select.ani"}
    };
    internal static readonly string[] Defaults = { "Crosshair", "UpArrow", "Pin", "Person" };
    internal sealed class Value
    {
        public string Name;
        public int Kind;
        public object Data;
    }
    internal sealed class Backup
    {
        public int SchemaVersion = 1;
        public string CreatedUtc = DateTime.UtcNow.ToString("o");
        public List<Value> Values;
    }

    [DllImport("user32.dll", EntryPoint = "SystemParametersInfoW", SetLastError = true)]
    private static extern bool SystemParametersInfo(uint action, uint param, IntPtr value, uint flags);
    [DllImport("user32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern IntPtr LoadCursorFromFile(string filename);
    [DllImport("user32.dll", SetLastError = true)]
    private static extern bool DestroyCursor(IntPtr cursor);

    internal static void Validate(string directory)
    {
        foreach (string name in Files.Values)
        {
            string path = Path.Combine(directory, name);
            if (!File.Exists(path)) throw new FileNotFoundException("缺少原厂指针文件：" + path);
            IntPtr cursor = LoadCursorFromFile(path);
            if (cursor == IntPtr.Zero) throw new Win32Exception(Marshal.GetLastWin32Error(), "指针文件无法加载：" + path);
            DestroyCursor(cursor);
        }
    }

    internal static List<Value> Capture(RegistryKey key)
    {
        var result = new List<Value>();
        foreach (string name in key.GetValueNames())
            result.Add(new Value { Name = name, Kind = (int)key.GetValueKind(name),
                Data = key.GetValue(name, null, RegistryValueOptions.DoNotExpandEnvironmentNames) });
        return result;
    }

    internal static void WriteScheme(RegistryKey key, string directory)
    {
        foreach (var pair in Files)
            key.SetValue(pair.Key, Path.Combine(directory, pair.Value), RegistryValueKind.String);
        foreach (string name in Defaults) key.SetValue(name, "", RegistryValueKind.String);
        key.SetValue("", "ASUS TX (Original)", RegistryValueKind.String);
        key.SetValue("Scheme Source", 1, RegistryValueKind.DWord);
        key.Flush();
    }

    internal static void Restore(RegistryKey key, List<Value> values)
    {
        var names = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        foreach (Value value in values) names.Add(value.Name);
        foreach (string name in key.GetValueNames())
            if (!names.Contains(name)) key.DeleteValue(name, false);
        foreach (Value value in values) key.SetValue(value.Name, value.Data, (RegistryValueKind)value.Kind);
        key.Flush();
    }

    // The callback is injectable only in the compiled unit test, never via user arguments.
    internal static void Apply(RegistryKey key, string directory, string backupPath, Action refresh)
    {
        var values = Capture(key);
        string json = new JavaScriptSerializer().Serialize(new Backup { Values = values });
        Directory.CreateDirectory(Path.GetDirectoryName(backupPath));
        using (var stream = new FileStream(backupPath, FileMode.CreateNew, FileAccess.Write))
        using (var writer = new StreamWriter(stream, new UTF8Encoding(false))) writer.Write(json);
        try
        {
            WriteScheme(key, directory);
            refresh();
        }
        catch
        {
            Restore(key, values);
            try { refresh(); } catch { /* Keep original failure and durable backup. */ }
            throw;
        }
    }

    [STAThread]
    private static int Main(string[] args)
    {
        bool verifyOnly = false, quiet = false;
        string directory = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.Windows), @"Resources\Themes\ASUS");
        string reportPath = null;
        var result = new Dictionary<string, object>();
        try
        {
            for (int i = 0; i < args.Length; i++)
            {
                switch (args[i].ToLowerInvariant())
                {
                    case "--verify-only": case "-verifyonly": verifyOnly = true; break;
                    case "--quiet": quiet = true; break;
                    case "--cursor-directory": case "-cursordirectory":
                        if (++i >= args.Length) throw new ArgumentException("缺少指针目录。");
                        directory = Path.GetFullPath(args[i]); break;
                    case "--json-output":
                        if (++i >= args.Length) throw new ArgumentException("缺少报告路径。");
                        reportPath = Path.GetFullPath(args[i]); break;
                    default: throw new ArgumentException("未知参数：" + args[i]);
                }
            }
            Validate(directory); // All 13 files must load before touching HKCU.
            result["verifiedFiles"] = Files.Count;
            result["settingsChanged"] = false;
            string message = "13 个天选姬原厂指针文件均可加载，尚未更改任何设置。";
            if (!verifyOnly)
            {
                string backups = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                    @"ThemeStudio-CursorRecovery\backups");
                string backup = Path.Combine(backups, "cursor-backup-" + DateTime.UtcNow.ToString("yyyyMMdd-HHmmss-fff") +
                    "-" + Guid.NewGuid().ToString("N") + ".json");
                using (var key = Registry.CurrentUser.OpenSubKey(@"Control Panel\Cursors", true))
                {
                    if (key == null) throw new InvalidOperationException("找不到当前用户的鼠标设置。");
                    Apply(key, directory, backup, delegate {
                        if (!SystemParametersInfo(0x57, 0, IntPtr.Zero, 2))
                            throw new Win32Exception(Marshal.GetLastWin32Error(), "Windows 刷新指针失败，已尝试回滚。");
                    });
                }
                result["settingsChanged"] = true;
                result["backup"] = backup;
                message = "已恢复天选姬原厂指针。\r\n\r\n原设置备份：" + backup;
            }
            result["success"] = true;
            if (reportPath != null) File.WriteAllText(reportPath, new JavaScriptSerializer().Serialize(result), new UTF8Encoding(false));
            if (!quiet) MessageBox.Show(message, "天选姬指针恢复", MessageBoxButtons.OK, MessageBoxIcon.Information);
            return 0;
        }
        catch (Exception error)
        {
            result["success"] = false;
            result["error"] = error.Message;
            if (reportPath != null)
                try { File.WriteAllText(reportPath, new JavaScriptSerializer().Serialize(result), new UTF8Encoding(false)); } catch { }
            if (!quiet) MessageBox.Show(error.Message, "天选姬指针恢复失败", MessageBoxButtons.OK, MessageBoxIcon.Error);
            return 1;
        }
    }
}

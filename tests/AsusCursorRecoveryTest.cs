using Microsoft.Win32;
using System;
using System.IO;
using System.Web.Script.Serialization;

internal static class AsusCursorRecoveryTest
{
    private static void Require(bool ok, string message) { if (!ok) throw new Exception(message); }
    private static int Main()
    {
        string registry = @"Software\ThemeStudio-RecoveryTests\" + Guid.NewGuid().ToString("N");
        string folder = Path.Combine(Path.GetTempPath(), "ThemeStudio-recovery-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(folder);
        try
        {
            using (var key = Registry.CurrentUser.CreateSubKey(registry))
            {
                key.SetValue("", "Original");
                key.SetValue("Arrow", @"%TEMP%\old.ani", RegistryValueKind.ExpandString);
                key.SetValue("Scheme Source", 2, RegistryValueKind.DWord);
                key.SetValue("Extra", new byte[] { 1, 2, 3 }, RegistryValueKind.Binary);
                var before = AsusCursorRecovery.Capture(key);
                string serialized = new JavaScriptSerializer().Serialize(before);
                string backup = Path.Combine(folder, "backup.json");
                int refreshed = 0;
                AsusCursorRecovery.Apply(key, @"C:\光标 目录", backup, delegate { refreshed++; });
                Require(refreshed == 1 && File.Exists(backup), "Durable backup and refresh");
                foreach (var pair in AsusCursorRecovery.Files)
                    Require((string)key.GetValue(pair.Key) == Path.Combine(@"C:\光标 目录", pair.Value), "Mapping " + pair.Key);
                foreach (string role in AsusCursorRecovery.Defaults)
                    Require((string)key.GetValue(role) == "", "OEM absent role " + role);
                Require((string)key.GetValue("") == "ASUS TX (Original)", "Scheme name");
                Require((int)key.GetValue("Scheme Source") == 1, "Scheme source");
                AsusCursorRecovery.Restore(key, before);
                Require(new JavaScriptSerializer().Serialize(AsusCursorRecovery.Capture(key)) == serialized, "Exact typed rollback");
                try { AsusCursorRecovery.Apply(key, "new", backup, delegate { refreshed++; }); throw new Exception("Backup overwritten"); }
                catch (IOException) { }
                Require(new JavaScriptSerializer().Serialize(AsusCursorRecovery.Capture(key)) == serialized, "Backup failure preserves settings");
                int failedRefresh = 0;
                try {
                    AsusCursorRecovery.Apply(key, "new", Path.Combine(folder, "rollback.json"), delegate {
                        failedRefresh++; throw new InvalidOperationException("simulated refresh failure");
                    });
                    throw new Exception("Refresh error swallowed");
                } catch (InvalidOperationException) { }
                Require(failedRefresh == 2, "Refresh retried after rollback");
                Require(new JavaScriptSerializer().Serialize(AsusCursorRecovery.Capture(key)) == serialized, "Failed refresh rolls back");
                try { AsusCursorRecovery.Validate(folder); throw new Exception("Missing files accepted"); }
                catch (FileNotFoundException) { }
            }
            Console.WriteLine("PASS: 13 OEM mappings, 4 defaults, typed backup, duplicate backup rejection, rollback, missing files.");
            return 0;
        }
        finally
        {
            Registry.CurrentUser.DeleteSubKeyTree(registry, false);
            string target = Path.GetFullPath(folder);
            string temporaryRoot = Path.GetFullPath(Path.GetTempPath()).TrimEnd('\\') + "\\";
            if (!target.StartsWith(temporaryRoot, StringComparison.OrdinalIgnoreCase) ||
                !Path.GetFileName(target).StartsWith("ThemeStudio-recovery-", StringComparison.Ordinal))
                throw new Exception("Fixture cleanup escaped the temporary directory.");
            Directory.Delete(target, true);
        }
    }
}

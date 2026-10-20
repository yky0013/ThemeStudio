// SPDX-License-Identifier: AGPL-3.0-or-later
// Fixed-scope native action broker for Windhawk mods.
//
// This helper deliberately accepts only the four actions below. It does not
// accept an executable path, a command line, a script, or a user-supplied
// filesystem target. Windhawk launches it with the `runas` verb when an
// action needs elevation.
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Management;
using System.Security.AccessControl;
using System.Security.Principal;
using System.Text;
using System.Web.Script.Serialization;
using System.Threading;

internal enum NativeActionKind
{
    NetworkEnable,
    NetworkDisable,
    NetworkReset,
    WindowsAppsAccess,
}

internal sealed class NativeActionOptions
{
    internal NativeActionKind Action;
    internal string ActionName;
    internal bool DryRun;
    internal bool Report;
}

internal sealed class AdapterResult
{
    internal string Name;
    internal string InterfaceDescription;
    internal string InterfaceIndex;
    internal bool HardwareInterface;
    internal bool Hidden;
    internal string State;
    internal string Status;
    internal string Method;
    internal bool Invoked;
    internal bool Success;
    internal uint ReturnCode;
    internal string Error;

    internal Dictionary<string, object> ToReport()
    {
        return new Dictionary<string, object>(StringComparer.OrdinalIgnoreCase)
        {
            { "name", Name ?? "" },
            { "interfaceDescription", InterfaceDescription ?? "" },
            { "interfaceIndex", InterfaceIndex ?? "" },
            { "hardwareInterface", HardwareInterface },
            { "hidden", Hidden },
            { "state", State ?? "" },
            { "status", Status ?? "" },
            { "method", Method ?? "" },
            { "invoked", Invoked },
            { "success", Success },
            { "returnCode", ReturnCode },
            { "error", Error ?? "" },
        };
    }
}

internal sealed class NativeActionResult
{
    internal bool Success;
    internal string Action;
    internal bool DryRun;
    internal bool Elevated;
    internal string Message;
    internal string Error;
    internal readonly List<string> Events = new List<string>();
    internal readonly List<AdapterResult> Adapters = new List<AdapterResult>();
    internal readonly List<string> RecoveryErrors = new List<string>();
    internal string WindowsAppsPath;
    internal string CurrentUserSid;
    internal bool TargetExists;
    internal bool AlreadyOwnedByAdministrators;
    internal string SchemaNamespace;
    internal string SchemaClass;
    internal bool SchemaValid;
    internal bool TakeOwnExists;
    internal bool IcaclsExists;

    internal Dictionary<string, object> ToReport()
    {
        var adapterReports = new List<object>();
        foreach (var adapter in Adapters)
            adapterReports.Add(adapter.ToReport());

        var recovery = new List<object>();
        foreach (var item in RecoveryErrors)
            recovery.Add(item);

        return new Dictionary<string, object>(StringComparer.OrdinalIgnoreCase)
        {
            { "ok", Success },
            { "action", Action ?? "" },
            { "dryRun", DryRun },
            { "elevated", Elevated },
            { "message", Message ?? "" },
            { "error", Error ?? "" },
            { "events", Events.ToArray() },
            { "adapters", adapterReports.ToArray() },
            { "recoveryErrors", recovery.ToArray() },
            { "windowsAppsPath", WindowsAppsPath ?? "" },
            { "currentUserSid", CurrentUserSid ?? "" },
            { "targetExists", TargetExists },
            { "alreadyOwnedByAdministrators", AlreadyOwnedByAdministrators },
            { "schemaNamespace", SchemaNamespace ?? "" },
            { "schemaClass", SchemaClass ?? "" },
            { "schemaValid", SchemaValid },
            { "takeownExists", TakeOwnExists },
            { "icaclsExists", IcaclsExists },
        };
    }
}

internal static class Program
{
    private const string StandardCimv2 = @"root\StandardCimv2";
    private const string AdapterQuery =
        "SELECT * FROM MSFT_NetAdapter " +
        "WHERE HardwareInterface = TRUE AND Hidden = FALSE";
    private const int ResetWaitMilliseconds = 2000;
    private const string NetworkActionMutexName =
        @"Local\ThemeStudio.NativeActions.Network";

    private static int Main(string[] args)
    {
        NativeActionResult result;
        NativeActionOptions options = null;
        try
        {
            options = ParseOptions(args);
            result = Execute(options);
        }
        catch (ArgumentException error)
        {
            Console.Error.WriteLine("Invalid arguments: " + error.Message);
            Console.Error.WriteLine(Usage());
            return 2;
        }
        catch (Exception error)
        {
            result = new NativeActionResult
            {
                Success = false,
                Action = "",
                Error = error.GetType().Name + ": " + error.Message,
                Message = "Native action failed.",
            };
        }

        WriteResult(result, options);
        return result.Success ? 0 : 1;
    }

    private static string Usage()
    {
        return "Usage: ThemeStudio.NativeActions.exe " +
               "network-enable|network-disable|network-reset|windowsapps-access " +
               "[--dry-run] [--report]";
    }

    private static NativeActionOptions ParseOptions(string[] args)
    {
        if (args == null || args.Length == 0)
            throw new ArgumentException("Exactly one fixed action is required.");

        string actionName = null;
        bool dryRun = false;
        bool report = false;
        foreach (var raw in args)
        {
            if (String.Equals(raw, "--dry-run", StringComparison.OrdinalIgnoreCase))
            {
                if (dryRun) throw new ArgumentException("--dry-run was specified twice.");
                dryRun = true;
            }
            else if (String.Equals(raw, "--report", StringComparison.OrdinalIgnoreCase))
            {
                if (report) throw new ArgumentException("--report was specified twice.");
                report = true;
            }
            else if (!String.IsNullOrEmpty(raw) && raw[0] != '-')
            {
                if (actionName != null)
                    throw new ArgumentException("Only one fixed action is allowed.");
                actionName = raw;
            }
            else
            {
                throw new ArgumentException("Unsupported option: " + (raw ?? "<null>"));
            }
        }

        NativeActionKind action;
        if (String.Equals(actionName, "network-enable", StringComparison.OrdinalIgnoreCase))
            action = NativeActionKind.NetworkEnable;
        else if (String.Equals(actionName, "network-disable", StringComparison.OrdinalIgnoreCase))
            action = NativeActionKind.NetworkDisable;
        else if (String.Equals(actionName, "network-reset", StringComparison.OrdinalIgnoreCase))
            action = NativeActionKind.NetworkReset;
        else if (String.Equals(actionName, "windowsapps-access", StringComparison.OrdinalIgnoreCase))
            action = NativeActionKind.WindowsAppsAccess;
        else
            throw new ArgumentException("Unsupported action: " + (actionName ?? "<missing>"));

        return new NativeActionOptions
        {
            Action = action,
            ActionName = actionName.ToLowerInvariant(),
            DryRun = dryRun,
            Report = report,
        };
    }

    private static NativeActionResult Execute(NativeActionOptions options)
    {
        var result = new NativeActionResult
        {
            Action = options.ActionName,
            DryRun = options.DryRun,
            Elevated = IsProcessElevated(),
        };

        switch (options.Action)
        {
            case NativeActionKind.NetworkEnable:
                return ExecuteNetworkState(options, result, "Enable");
            case NativeActionKind.NetworkDisable:
                return ExecuteNetworkState(options, result, "Disable");
            case NativeActionKind.NetworkReset:
                return ExecuteNetworkReset(options, result);
            case NativeActionKind.WindowsAppsAccess:
                return ExecuteWindowsAppsAccess(options, result);
            default:
                throw new InvalidOperationException("Unknown fixed action.");
        }
    }

    private static ManagementScope ConnectScope()
    {
        var options = new ConnectionOptions
        {
            EnablePrivileges = true,
            Impersonation = ImpersonationLevel.Impersonate,
            Authentication = AuthenticationLevel.PacketPrivacy,
        };
        var scope = new ManagementScope(@"\\.\" + StandardCimv2, options);
        scope.Connect();
        return scope;
    }

    private static bool TryAcquireNetworkMutex(
        NativeActionResult result, out Mutex mutex)
    {
        mutex = null;
        try
        {
            bool createdNew;
            var candidate = new Mutex(false, NetworkActionMutexName, out createdNew);
            bool acquired = false;
            try
            {
                acquired = candidate.WaitOne(0);
            }
            catch (AbandonedMutexException)
            {
                // Ownership transfers to this process; the previous owner
                // exited without releasing the guard.
                result.Events.Add("recovered abandoned network mutex");
                acquired = true;
            }
            if (!acquired)
            {
                candidate.Dispose();
                result.Error = "Another network action is already running; no changes were made.";
                result.Message = "Busy; no network method was invoked.";
                result.Events.Add("network mutex busy");
                return false;
            }
            mutex = candidate;
            return true;
        }
        catch (Exception error)
        {
            result.Error = "Network action mutex failed: " +
                error.GetType().Name + ": " + error.Message;
            result.Message = "Network action was not invoked.";
            return false;
        }
    }

    private static void ReleaseNetworkMutex(Mutex mutex)
    {
        if (mutex == null) return;
        try
        {
            mutex.ReleaseMutex();
        }
        catch
        {
            // The helper is already finishing; disposal still closes the handle.
        }
        mutex.Dispose();
    }

    private static bool VerifyAdapterSchema(ManagementScope scope, NativeActionResult result)
    {
        result.SchemaNamespace = StandardCimv2;
        result.SchemaClass = "MSFT_NetAdapter";
        using (var adapterClass = new ManagementClass(scope, new ManagementPath("MSFT_NetAdapter"), null))
        {
            // Get() is intentionally read-only. It verifies that the provider
            // exposes the same class and members used by Get-NetAdapter.
            adapterClass.Get();
            bool hardware = adapterClass.Properties["HardwareInterface"] != null;
            bool hidden = adapterClass.Properties["Hidden"] != null;
            bool enable = adapterClass.Methods["Enable"] != null;
            bool disable = adapterClass.Methods["Disable"] != null;
            result.SchemaValid = hardware && hidden && enable && disable;
            result.Events.Add(String.Format(CultureInfo.InvariantCulture,
                "schema properties HardwareInterface={0}, Hidden={1}; methods Enable={2}, Disable={3}",
                hardware, hidden, enable, disable));
            return result.SchemaValid;
        }
    }

    private static List<ManagementObject> QueryAdapters(ManagementScope scope)
    {
        var adapters = new List<ManagementObject>();
        var query = new ObjectQuery(AdapterQuery);
        var enumeration = new EnumerationOptions
        {
            ReturnImmediately = true,
            Rewindable = false,
            EnsureLocatable = false,
        };
        using (var searcher = new ManagementObjectSearcher(scope, query, enumeration))
        using (var found = searcher.Get())
        {
            foreach (ManagementObject adapter in found)
                adapters.Add(adapter);
        }
        return adapters;
    }

    private static AdapterResult DescribeAdapter(ManagementObject adapter)
    {
        return new AdapterResult
        {
            Name = ReadString(adapter, "Name"),
            InterfaceDescription = ReadString(adapter, "InterfaceDescription"),
            InterfaceIndex = ReadString(adapter, "InterfaceIndex"),
            HardwareInterface = ReadBool(adapter, "HardwareInterface"),
            Hidden = ReadBool(adapter, "Hidden"),
            State = ReadString(adapter, "State"),
            Status = ReadString(adapter, "Status"),
        };
    }

    private static string ReadString(ManagementObject adapter, string property)
    {
        try
        {
            object value = adapter[property];
            return value == null ? "" : Convert.ToString(value, CultureInfo.InvariantCulture);
        }
        catch
        {
            return "";
        }
    }

    private static bool ReadBool(ManagementObject adapter, string property)
    {
        try
        {
            object value = adapter[property];
            return value != null && Convert.ToBoolean(value, CultureInfo.InvariantCulture);
        }
        catch
        {
            return false;
        }
    }

    private static NativeActionResult ExecuteNetworkState(
        NativeActionOptions options, NativeActionResult result, string method)
    {
        Mutex networkMutex = null;
        if (!options.DryRun && !TryAcquireNetworkMutex(result, out networkMutex))
            return result;
        if (!options.DryRun && !result.Elevated)
        {
            result.Error = "Network adapter changes require an elevated helper process.";
            result.Message = "Elevation required; no adapter method was invoked.";
            ReleaseNetworkMutex(networkMutex);
            return result;
        }

        try
        {
            var scope = ConnectScope();
                if (!VerifyAdapterSchema(scope, result))
                {
                    result.Error = "MSFT_NetAdapter schema is missing required members.";
                    result.Message = "Read-only provider schema verification failed.";
                    return result;
                }

                var adapters = QueryAdapters(scope);
                result.Events.Add("matched adapters: " + adapters.Count.ToString(CultureInfo.InvariantCulture));
                if (adapters.Count == 0)
                {
                    result.Success = true;
                    result.Message = options.DryRun
                        ? "Dry-run completed; no visible hardware adapters matched."
                        : "No visible hardware adapters matched.";
                    DisposeAdapters(adapters);
                    return result;
                }

                bool allSucceeded = true;
                foreach (var adapter in adapters)
                {
                    var item = DescribeAdapter(adapter);
                    item.Method = method;
                    if (options.DryRun)
                    {
                        item.Success = true;
                        item.Error = "dry-run: method not invoked";
                        result.Adapters.Add(item);
                        continue;
                    }

                    item.Invoked = true;
                    try
                    {
                        object value = adapter.InvokeMethod(method, null);
                        item.ReturnCode = value == null ? 0U : Convert.ToUInt32(value, CultureInfo.InvariantCulture);
                        item.Success = item.ReturnCode == 0U;
                        if (!item.Success)
                        {
                            item.Error = "MSFT_NetAdapter." + method +
                                " returned " + item.ReturnCode.ToString(CultureInfo.InvariantCulture);
                            allSucceeded = false;
                        }
                    }
                    catch (Exception error)
                    {
                        item.Success = false;
                        item.Error = error.GetType().Name + ": " + error.Message;
                        allSucceeded = false;
                    }
                    result.Adapters.Add(item);
                }
                DisposeAdapters(adapters);
                result.Success = allSucceeded;
                result.Message = options.DryRun
                    ? "Dry-run completed; no adapter method was invoked."
                    : (allSucceeded ? method + " completed for all matched adapters."
                                    : method + " failed for one or more matched adapters.");
                if (!allSucceeded)
                    result.Error = "One or more adapter operations failed.";
                return result;
        }
        catch (Exception error)
        {
            result.Error = error.GetType().Name + ": " + error.Message;
            result.Message = "Network adapter operation failed before completion.";
            return result;
        }
        finally
        {
            ReleaseNetworkMutex(networkMutex);
        }
    }

    private static NativeActionResult ExecuteNetworkReset(
        NativeActionOptions options, NativeActionResult result)
    {
        Mutex networkMutex = null;
        if (!options.DryRun && !TryAcquireNetworkMutex(result, out networkMutex))
            return result;
        if (!options.DryRun && !result.Elevated)
        {
            result.Error = "Network reset requires an elevated helper process.";
            result.Message = "Elevation required; no adapter method was invoked.";
            ReleaseNetworkMutex(networkMutex);
            return result;
        }

        List<ManagementObject> adapters = null;
        var disabled = new List<ManagementObject>();
        try
        {
            var scope = ConnectScope();
                if (!VerifyAdapterSchema(scope, result))
                {
                    result.Error = "MSFT_NetAdapter schema is missing required members.";
                    result.Message = "Read-only provider schema verification failed.";
                    return result;
                }

                adapters = QueryAdapters(scope);
                result.Events.Add("matched adapters: " + adapters.Count.ToString(CultureInfo.InvariantCulture));
                if (options.DryRun)
                {
                    foreach (var adapter in adapters)
                    {
                        var item = DescribeAdapter(adapter);
                        item.Method = "Disable -> ipconfig.exe /flushdns -> Enable";
                        item.Success = true;
                        item.Error = "dry-run: adapter methods and ipconfig.exe were not invoked";
                        result.Adapters.Add(item);
                    }
                    result.Events.Add("would wait: " + ResetWaitMilliseconds.ToString(CultureInfo.InvariantCulture) + " ms");
                    result.Events.Add("would run fixed executable: ipconfig.exe /flushdns");
                    result.Success = true;
                    result.Message = "Dry-run completed; reset sequence was not invoked.";
                    return result;
                }

                foreach (var adapter in adapters)
                {
                    var item = DescribeAdapter(adapter);
                    item.Method = "Disable";
                    item.Invoked = true;
                    try
                    {
                        object value = adapter.InvokeMethod("Disable", null);
                        item.ReturnCode = value == null ? 0U : Convert.ToUInt32(value, CultureInfo.InvariantCulture);
                        item.Success = item.ReturnCode == 0U;
                        if (!item.Success)
                        {
                            item.Error = "MSFT_NetAdapter.Disable returned " +
                                item.ReturnCode.ToString(CultureInfo.InvariantCulture);
                            result.Adapters.Add(item);
                            result.Error = "Reset disable phase failed; restoring previously changed adapters.";
                            RestoreAdapters(disabled, result);
                            result.Message = "Network reset failed during disable phase.";
                            return result;
                        }
                        disabled.Add(adapter);
                    }
                    catch (Exception error)
                    {
                        item.Success = false;
                        item.Error = error.GetType().Name + ": " + error.Message;
                        result.Adapters.Add(item);
                        result.Error = "Reset disable phase failed; restoring previously changed adapters.";
                        RestoreAdapters(disabled, result);
                        result.Message = "Network reset failed during disable phase.";
                        return result;
                    }
                    result.Adapters.Add(item);
                }

                Thread.Sleep(ResetWaitMilliseconds);
                result.Events.Add("waited: " + ResetWaitMilliseconds.ToString(CultureInfo.InvariantCulture) + " ms");
                int flushCode;
                string flushError;
                if (!RunFlushDns(out flushCode, out flushError))
                {
                    result.Events.Add("ipconfig.exe /flushdns exit code: " + flushCode.ToString(CultureInfo.InvariantCulture));
                    result.Error = "DNS flush failed; restoring disabled adapters." +
                        (String.IsNullOrEmpty(flushError) ? "" : " " + flushError);
                    RestoreAdapters(disabled, result);
                    result.Message = "Network reset failed during DNS flush.";
                    return result;
                }
                result.Events.Add("ipconfig.exe /flushdns completed");

                bool enableSucceeded = true;
                foreach (var adapter in disabled)
                {
                    AdapterResult item = FindAdapterResult(result, adapter, "Disable");
                    try
                    {
                        object value = adapter.InvokeMethod("Enable", null);
                        uint code = value == null ? 0U : Convert.ToUInt32(value, CultureInfo.InvariantCulture);
                        if (code != 0U)
                        {
                            enableSucceeded = false;
                            result.RecoveryErrors.Add("Enable returned " + code.ToString(CultureInfo.InvariantCulture) +
                                " for " + DescribeAdapter(adapter).Name);
                        }
                        if (item != null)
                        {
                            item.Method = "Disable -> Enable";
                            item.ReturnCode = code;
                            item.Success = code == 0U;
                        }
                    }
                    catch (Exception error)
                    {
                        enableSucceeded = false;
                        result.RecoveryErrors.Add("Enable failed for " + DescribeAdapter(adapter).Name +
                            ": " + error.GetType().Name + ": " + error.Message);
                        if (item != null)
                        {
                            item.Method = "Disable -> Enable";
                            item.Success = false;
                            item.Error = error.GetType().Name + ": " + error.Message;
                        }
                    }
                }

                if (!enableSucceeded)
                {
                    result.Error = "Reset re-enable phase failed; retrying restoration.";
                    RestoreAdapters(disabled, result);
                    result.Message = "Network reset failed while re-enabling adapters.";
                    return result;
                }

                result.Success = true;
                result.Message = "Network reset completed successfully.";
                return result;
        }
        catch (Exception error)
        {
            result.Error = error.GetType().Name + ": " + error.Message;
            result.Message = "Network reset failed; attempting restoration.";
            if (disabled.Count > 0)
                RestoreAdapters(disabled, result);
            return result;
        }
        finally
        {
            DisposeAdapters(adapters);
            ReleaseNetworkMutex(networkMutex);
        }
    }

    private static AdapterResult FindAdapterResult(
        NativeActionResult result, ManagementObject adapter, string method)
    {
        string name = DescribeAdapter(adapter).Name;
        foreach (var item in result.Adapters)
            if (String.Equals(item.Name, name, StringComparison.OrdinalIgnoreCase) &&
                String.Equals(item.Method, method, StringComparison.OrdinalIgnoreCase))
                return item;
        return null;
    }

    private static void RestoreAdapters(List<ManagementObject> adapters, NativeActionResult result)
    {
        for (int i = adapters.Count - 1; i >= 0; i--)
        {
            try
            {
                object value = adapters[i].InvokeMethod("Enable", null);
                uint code = value == null ? 0U : Convert.ToUInt32(value, CultureInfo.InvariantCulture);
                if (code != 0U)
                    result.RecoveryErrors.Add("Recovery Enable returned " + code.ToString(CultureInfo.InvariantCulture) +
                        " for " + DescribeAdapter(adapters[i]).Name);
            }
            catch (Exception error)
            {
                result.RecoveryErrors.Add("Recovery Enable failed for " + DescribeAdapter(adapters[i]).Name +
                    ": " + error.GetType().Name + ": " + error.Message);
            }
        }
    }

    private static bool RunFlushDns(out int exitCode, out string error)
    {
        exitCode = -1;
        error = "";
        string systemRoot = Environment.GetEnvironmentVariable("SystemRoot");
        if (String.IsNullOrEmpty(systemRoot)) systemRoot = Environment.GetFolderPath(Environment.SpecialFolder.Windows);
        string executable = Path.Combine(systemRoot ?? "C:\\Windows", "System32", "ipconfig.exe");
        if (!File.Exists(executable))
        {
            error = "Fixed executable was not found: " + executable;
            return false;
        }

        try
        {
            var start = new ProcessStartInfo
            {
                FileName = executable,
                Arguments = "/flushdns",
                UseShellExecute = false,
                CreateNoWindow = true,
                WindowStyle = ProcessWindowStyle.Hidden,
                WorkingDirectory = Path.GetDirectoryName(executable),
            };
            using (var process = Process.Start(start))
            {
                if (process == null)
                {
                    error = "Process.Start returned null for ipconfig.exe.";
                    return false;
                }
                process.WaitForExit();
                exitCode = process.ExitCode;
            }
            return exitCode == 0;
        }
        catch (Exception exception)
        {
            error = exception.GetType().Name + ": " + exception.Message;
            return false;
        }
    }

    private static NativeActionResult ExecuteWindowsAppsAccess(
        NativeActionOptions options, NativeActionResult result)
    {
        result.WindowsAppsPath = GetWindowsAppsPath();
        result.CurrentUserSid = GetCurrentUserSid();
        result.TargetExists = Directory.Exists(result.WindowsAppsPath);
        string systemRoot = Environment.GetEnvironmentVariable("SystemRoot");
        if (String.IsNullOrEmpty(systemRoot)) systemRoot = Environment.GetFolderPath(Environment.SpecialFolder.Windows);
        string system32 = Path.Combine(systemRoot ?? "C:\\Windows", "System32");
        string takeown = Path.Combine(system32, "takeown.exe");
        string icacls = Path.Combine(system32, "icacls.exe");
        result.TakeOwnExists = File.Exists(takeown);
        result.IcaclsExists = File.Exists(icacls);
        result.AlreadyOwnedByAdministrators = IsOwnedByAdministrators(result.WindowsAppsPath);
        result.Events.Add("fixed target: " + result.WindowsAppsPath);
        result.Events.Add("fixed executables: takeown.exe, icacls.exe");

        if (!result.TargetExists)
        {
            result.Success = options.DryRun;
            result.Error = "ProgramFiles\\WindowsApps was not found.";
            result.Message = options.DryRun
                ? "Dry-run completed; the fixed WindowsApps target was not found."
                : "WindowsApps access action was not invoked.";
            return result;
        }
        if (String.IsNullOrEmpty(result.CurrentUserSid))
        {
            result.Success = options.DryRun;
            result.Error = "The current user's SID could not be resolved.";
            result.Message = options.DryRun
                ? "Dry-run completed; the current user's SID could not be resolved."
                : "WindowsApps access action was not invoked.";
            return result;
        }
        if (!result.TakeOwnExists || !result.IcaclsExists)
        {
            result.Success = options.DryRun;
            result.Error = "Fixed Windows security tools are missing.";
            result.Message = options.DryRun
                ? "Dry-run completed; fixed security tools were not found."
                : "WindowsApps access action was not invoked.";
            return result;
        }
        if (result.AlreadyOwnedByAdministrators)
        {
            result.Success = true;
            result.Message = "WindowsApps is already owned by Administrators.";
            return result;
        }
        if (options.DryRun)
        {
            result.Success = true;
            result.Message = "Dry-run completed; takeown.exe and icacls.exe were not invoked.";
            result.Events.Add("would run takeown.exe /F <fixed-target> /A");
            result.Events.Add("would run icacls.exe <fixed-target> /grant *<current-user-sid>:(R)");
            return result;
        }
        if (!result.Elevated)
        {
            result.Success = false;
            result.Error = "WindowsApps access requires an elevated helper process.";
            result.Message = "Elevation required; security tools were not invoked.";
            return result;
        }

        int takeownExit;
        string takeownError;
        if (!RunFixedTool(takeown, new[] { "/F", result.WindowsAppsPath, "/A" }, out takeownExit, out takeownError))
        {
            result.Error = "takeown.exe failed with exit code " + takeownExit.ToString(CultureInfo.InvariantCulture) +
                (String.IsNullOrEmpty(takeownError) ? "" : ": " + takeownError);
            result.Message = "WindowsApps ownership was not updated.";
            return result;
        }
        result.Events.Add("takeown.exe completed");

        int icaclsExit;
        string icaclsError;
        string grant = "*" + result.CurrentUserSid + ":(R)";
        if (!RunFixedTool(icacls, new[] { result.WindowsAppsPath, "/grant", grant }, out icaclsExit, out icaclsError))
        {
            result.Error = "icacls.exe failed with exit code " + icaclsExit.ToString(CultureInfo.InvariantCulture) +
                (String.IsNullOrEmpty(icaclsError) ? "" : ": " + icaclsError);
            result.Message = "WindowsApps ownership changed, but the current-user read grant failed.";
            return result;
        }
        result.Events.Add("icacls.exe completed");
        result.Success = true;
        result.Message = "WindowsApps ownership and current-user read grant completed.";
        return result;
    }

    private static bool RunFixedTool(string executable, string[] arguments,
        out int exitCode, out string error)
    {
        exitCode = -1;
        error = "";
        try
        {
            var start = new ProcessStartInfo
            {
                FileName = executable,
                Arguments = BuildArguments(arguments),
                UseShellExecute = false,
                CreateNoWindow = true,
                WindowStyle = ProcessWindowStyle.Hidden,
                WorkingDirectory = Path.GetDirectoryName(executable),
            };
            using (var process = Process.Start(start))
            {
                if (process == null)
                {
                    error = "Process.Start returned null.";
                    return false;
                }
                process.WaitForExit();
                exitCode = process.ExitCode;
            }
            return exitCode == 0;
        }
        catch (Exception exception)
        {
            error = exception.GetType().Name + ": " + exception.Message;
            return false;
        }
    }

    private static string BuildArguments(IEnumerable<string> arguments)
    {
        var builder = new StringBuilder();
        foreach (string argument in arguments)
        {
            if (builder.Length > 0) builder.Append(' ');
            builder.Append(QuoteWindowsArgument(argument));
        }
        return builder.ToString();
    }

    private static string QuoteWindowsArgument(string argument)
    {
        if (argument == null) argument = "";
        if (argument.Length > 0 && argument.IndexOfAny(new[] { ' ', '\t', '\r', '\n', '"' }) < 0)
            return argument;

        var builder = new StringBuilder();
        builder.Append('"');
        int backslashes = 0;
        foreach (char character in argument)
        {
            if (character == '\\')
            {
                backslashes++;
                continue;
            }
            if (character == '"')
            {
                builder.Append(new string('\\', backslashes * 2 + 1));
                builder.Append('"');
                backslashes = 0;
                continue;
            }
            if (backslashes > 0)
            {
                builder.Append(new string('\\', backslashes));
                backslashes = 0;
            }
            builder.Append(character);
        }
        if (backslashes > 0)
            builder.Append(new string('\\', backslashes * 2));
        builder.Append('"');
        return builder.ToString();
    }

    private static string GetWindowsAppsPath()
    {
        string programFiles = Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles);
        if (String.IsNullOrEmpty(programFiles))
            programFiles = Environment.GetEnvironmentVariable("ProgramFiles");
        if (String.IsNullOrEmpty(programFiles))
            programFiles = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.Windows), "Program Files");
        return Path.GetFullPath(Path.Combine(programFiles, "WindowsApps"));
    }

    private static string GetCurrentUserSid()
    {
        try
        {
            using (var identity = WindowsIdentity.GetCurrent())
            {
                return identity.User == null ? "" : identity.User.Value;
            }
        }
        catch
        {
            return "";
        }
    }

    private static bool IsOwnedByAdministrators(string path)
    {
        try
        {
            var administrators = new SecurityIdentifier(WellKnownSidType.BuiltinAdministratorsSid, null);
            var security = Directory.GetAccessControl(path, AccessControlSections.Owner);
            var owner = security.GetOwner(typeof(SecurityIdentifier)) as SecurityIdentifier;
            return owner != null && owner.Equals(administrators);
        }
        catch
        {
            return false;
        }
    }

    private static bool IsProcessElevated()
    {
        try
        {
            using (var identity = WindowsIdentity.GetCurrent())
            {
                return identity != null && identity.ImpersonationLevel == TokenImpersonationLevel.None &&
                    new WindowsPrincipal(identity).IsInRole(WindowsBuiltInRole.Administrator);
            }
        }
        catch
        {
            return false;
        }
    }

    private static void DisposeAdapters(List<ManagementObject> adapters)
    {
        if (adapters == null) return;
        foreach (var adapter in adapters)
            if (adapter != null) adapter.Dispose();
    }

    private static void WriteResult(NativeActionResult result, NativeActionOptions options)
    {
        if (options != null && options.Report)
        {
            Console.WriteLine(new JavaScriptSerializer().Serialize(result.ToReport()));
            return;
        }
        if (result.Success)
            Console.WriteLine("OK: " + (result.Message ?? "Native action completed."));
        else
            Console.Error.WriteLine("ERROR: " + (result.Error ?? result.Message ?? "Native action failed."));
    }
}

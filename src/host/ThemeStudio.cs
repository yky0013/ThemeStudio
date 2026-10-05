// SPDX-License-Identifier: AGPL-3.0-or-later
// Theme Studio's desktop container. The UI is compiled from the checked-in
// Seelen/Windhawk sources; Windows changes are handled by the bundled backend.
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using System.Web.Script.Serialization;
using System.Windows.Forms;
using Microsoft.Web.WebView2.Core;
using Microsoft.Web.WebView2.WinForms;
using System.Reflection;

[assembly: AssemblyTitle("Theme Studio")]
[assembly: AssemblyProduct("桌面主题工作室")]
[assembly: AssemblyVersion("0.6.4.0")]
[assembly: AssemblyFileVersion("0.6.4.0")]

internal static class Program
{
    [DllImport("user32.dll")] private static extern bool SetProcessDpiAwarenessContext(IntPtr value);
    [STAThread]
    private static void Main(string[] args)
    {
        try { SetProcessDpiAwarenessContext(new IntPtr(-4)); } catch { }
        Application.EnableVisualStyles();
        Application.SetCompatibleTextRenderingDefault(false);
        string smoke = null;
        string wallpaperData = null;
        string qaScript = null;
        bool stopRuntimes = false;
        for (int i = 0; i < args.Length; i++)
        {
            if (args[i] == "--smoke-dir" && i + 1 < args.Length) smoke = Path.GetFullPath(args[++i]);
            else if (args[i] == "--wallpaper-data" && i + 1 < args.Length) wallpaperData = Path.GetFullPath(args[++i]);
            else if (args[i] == "--qa-script" && i + 1 < args.Length) qaScript = Path.GetFullPath(args[++i]);
            else if (args[i] == "--stop-runtimes") stopRuntimes = true;
        }
        if (wallpaperData != null) { WallpaperRuntime.Run(wallpaperData); return; }
        if (stopRuntimes)
        {
            var data = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "ThemeStudio");
            try
            {
                new NativeWallpaperClient(data).Stop().GetAwaiter().GetResult();
                var executable = Path.Combine(Application.StartupPath, "backend", "ThemeStudio.Backend.exe");
                var child = Process.Start(new ProcessStartInfo(executable, "--data-dir \"" + data + "\" --shutdown") { UseShellExecute = false, CreateNoWindow = true });
                if (!child.WaitForExit(90000) || child.ExitCode != 0) Environment.ExitCode = 1;
            }
            catch { Environment.ExitCode = 1; }
            return;
        }
        using (var applicationMutex = new Mutex(false, "Local\\ThemeStudio.Application"))
            Application.Run(new StudioWindow(smoke, smoke == null ? null : qaScript));
    }
}

internal sealed class StudioWindow : Form
{
    private const string VirtualHost = "app.theme-studio.invalid";
    private readonly string dataDirectory;
    private readonly string smokeDirectory;
    private readonly string scanDirectory;
    private readonly string qaScript;
    private readonly JavaScriptSerializer json = new JavaScriptSerializer { MaxJsonLength = 48 * 1024 * 1024, RecursionLimit = 100 };
    private readonly WebView2 view = new WebView2 { Dock = DockStyle.Fill };
    private readonly SemaphoreSlim bridgeLock = new SemaphoreSlim(1, 1);
    private readonly SemaphoreSlim appearanceLock = new SemaphoreSlim(1, 1);
    private readonly HashSet<string> operations = new HashSet<string> { "state", "icons.import", "icons.assign", "icons.apply", "icons.restore", "cursors.import", "cursors.save", "cursors.apply", "cursors.restore", "cursors.factory", "recipe.export", "runtime.state", "runtime.apply", "runtime.seelen.apply", "runtime.seelen.stop", "runtime.windhawk.apply", "runtime.windhawk.stop" };
    private Process backend;
    private StreamWriter backendInput;
    private int activeRequests;
    private bool closing;
    private bool ready;
    private string backendError = "";
    private System.Windows.Forms.Timer smokeTimeout;
    private readonly NativeWallpaperClient wallpaper;
    private bool suspendPending;
    private bool updateHandoff;
    private bool closeAfterRequests;
    private readonly List<string> smokeOperations = new List<string>();

    internal StudioWindow(string smoke, string script)
    {
        operations.Add("runtime.desktop.apply");
        operations.Add("appearance.state");
        foreach (var op in new[] { "explorer.state", "explorer.apply", "explorer.restore", "pets.state", "pets.launch", "pets.remove" }) operations.Add(op);
        smokeDirectory = smoke;
        qaScript = script;
        dataDirectory = smoke == null ? Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "ThemeStudio") : Path.Combine(smoke, "data");
        scanDirectory = smoke == null ? null : Path.Combine(smoke, "desktop");
#if TUTORIAL_MODE
        dataDirectory = Path.Combine(Application.StartupPath, "demo", "data");
        scanDirectory = Path.Combine(Application.StartupPath, "demo", "desktop");
#endif
        Directory.CreateDirectory(dataDirectory);
        wallpaper = new NativeWallpaperClient(dataDirectory);
        Text = "桌面主题工作室";
        Width = 1360; Height = 920; MinimumSize = new Size(900, 650);
        StartPosition = FormStartPosition.CenterScreen;
        AutoScaleDimensions = new SizeF(96F, 96F);
        AutoScaleMode = AutoScaleMode.Dpi;
        try { Icon = Icon.ExtractAssociatedIcon(Application.ExecutablePath); } catch { }
        Controls.Add(view);
        Shown += Initialize;
        FormClosing += OnClosing;
        FormClosed += OnClosed;
        Resize += UpdateVisibility;
        if (smoke != null)
        {
            ShowInTaskbar = false; Opacity = 0;
            smokeTimeout = new System.Windows.Forms.Timer { Interval = qaScript == null ? 45000 : 120000 };
            smokeTimeout.Tick += delegate { if (!ready || qaScript != null) { Environment.ExitCode = 2; WriteReport(false, "Native UI test timed out", null); Close(); } };
            smokeTimeout.Start();
        }
    }

    private async void UpdateVisibility(object sender, EventArgs args)
    {
        if (view.CoreWebView2 == null || closing) return;
        if (WindowState != FormWindowState.Minimized)
        {
            view.CoreWebView2.Resume(); view.Visible = true; return;
        }
        if (suspendPending || activeRequests > 0) return;
        suspendPending = true;
        try
        {
            view.Visible = false;
            await view.CoreWebView2.TrySuspendAsync();
            if (WindowState != FormWindowState.Minimized) { view.CoreWebView2.Resume(); view.Visible = true; }
        }
        catch { view.Visible = WindowState != FormWindowState.Minimized; }
        finally { suspendPending = false; }
    }

    private bool IsLocal(string address)
    {
        Uri uri;
        return Uri.TryCreate(address, UriKind.Absolute, out uri) && uri.Scheme == "https" && uri.Host == VirtualHost && uri.IsDefaultPort;
    }

    private void OpenExternal(string address)
    {
        Uri uri;
        if (IsLocal(address))
        {
            if (new Uri(address).AbsolutePath == "/help/index.html")
                Process.Start(new ProcessStartInfo(Path.Combine(Application.StartupPath, "wwwroot", "help", "index.html")) { UseShellExecute = true });
            return;
        }
        if (Uri.TryCreate(address, UriKind.Absolute, out uri) && (uri.Scheme == "https" || uri.Scheme == "http"))
            Process.Start(new ProcessStartInfo(address) { UseShellExecute = true });
    }

    private async void Initialize(object sender, EventArgs args)
    {
        try
        {
            var environment = await CoreWebView2Environment.CreateAsync(null, Path.Combine(dataDirectory, "webview"), null);
            await view.EnsureCoreWebView2Async(environment);
            var core = view.CoreWebView2;
            core.Settings.IsWebMessageEnabled = true;
            core.Settings.AreDevToolsEnabled = smokeDirectory != null;
            core.Settings.IsStatusBarEnabled = false;
            core.Settings.AreBrowserAcceleratorKeysEnabled = false;
            core.SetVirtualHostNameToFolderMapping(VirtualHost, Path.Combine(Application.StartupPath, "wwwroot"), CoreWebView2HostResourceAccessKind.Deny);
            core.SetVirtualHostNameToFolderMapping(WallpaperFiles.MediaHost, WallpaperFiles.MediaDirectory(dataDirectory), CoreWebView2HostResourceAccessKind.Allow);
            var packsDirectory = Path.Combine(dataDirectory, "theme-packs", "assets");
            Directory.CreateDirectory(packsDirectory);
            core.SetVirtualHostNameToFolderMapping("packs.theme-studio.invalid", packsDirectory, CoreWebView2HostResourceAccessKind.Allow);
            core.NavigationStarting += delegate(object s, CoreWebView2NavigationStartingEventArgs e)
            {
                if (!IsLocal(e.Uri)) { e.Cancel = true; if (e.IsUserInitiated) OpenExternal(e.Uri); }
            };
            core.NewWindowRequested += delegate(object s, CoreWebView2NewWindowRequestedEventArgs e) { e.Handled = true; if (e.IsUserInitiated) OpenExternal(e.Uri); };
            core.PermissionRequested += delegate(object s, CoreWebView2PermissionRequestedEventArgs e) { e.State = CoreWebView2PermissionState.Deny; };
            core.WebMessageReceived += Receive;
            core.ProcessFailed += delegate(object s, CoreWebView2ProcessFailedEventArgs e) { WriteReport(false, "WebView process failed: " + e.ProcessFailedKind, null); };
            core.Navigate("https://" + VirtualHost + "/index.html");
        }
        catch (Exception error)
        {
            Environment.ExitCode = 1;
            WriteReport(false, error.ToString(), null);
            if (smokeDirectory == null) MessageBox.Show("启动失败：" + error.Message + "\n\n请保留完整程序目录和 Microsoft Edge WebView2 Runtime。", Text, MessageBoxButtons.OK, MessageBoxIcon.Error);
            Close();
        }
    }

    private static string Quote(string value) { return "\"" + value + "\""; }
    private void StartBackend()
    {
        if (backend != null && !backend.HasExited) return;
        var arguments = "--data-dir " + Quote(dataDirectory);
        if (scanDirectory != null) arguments += " --scan-dir " + Quote(scanDirectory);
        var executable = Path.Combine(Application.StartupPath, "backend", "ThemeStudio.Backend.exe");
        var info = new ProcessStartInfo(executable, arguments) {
            WorkingDirectory = Path.GetDirectoryName(executable), UseShellExecute = false, CreateNoWindow = true,
            RedirectStandardInput = true, RedirectStandardOutput = true, RedirectStandardError = true,
            StandardOutputEncoding = Encoding.UTF8, StandardErrorEncoding = Encoding.UTF8
        };
        info.EnvironmentVariables["PYTHONUTF8"] = "1";
        backend = Process.Start(info);
        backendInput = new StreamWriter(backend.StandardInput.BaseStream, new UTF8Encoding(false)) { AutoFlush = true };
        backend.ErrorDataReceived += delegate(object sender, DataReceivedEventArgs e) { if (e.Data != null) backendError = e.Data; };
        backend.BeginErrorReadLine();
    }

    private async Task<string> CallBackend(string request)
    {
        await bridgeLock.WaitAsync();
        try
        {
            StartBackend();
            await backendInput.WriteLineAsync(request);
            await backendInput.FlushAsync();
            while (true)
            {
                var answer = await backend.StandardOutput.ReadLineAsync();
                if (answer == null) throw new IOException("桌面组件已停止。" + backendError);
                var parsed = json.Deserialize<Dictionary<string, object>>(answer);
                if (parsed.ContainsKey("event")) { if (!closing) view.CoreWebView2.PostWebMessageAsJson(answer); continue; }
                return answer;
            }
        }
        finally { bridgeLock.Release(); }
    }

    private async Task<Dictionary<string, object>> BackendAction(string operation, object payload)
    {
        var answer = json.Deserialize<Dictionary<string, object>>(await CallBackend(json.Serialize(new { id = -1, operation = operation, payload = payload })));
        if (answer.ContainsKey("error")) throw new InvalidOperationException(Convert.ToString(answer["error"]));
        return answer["result"] as Dictionary<string, object>;
    }

    private object WithMedia(Dictionary<string, object> status)
    {
        var id = WallpaperFiles.Text(status, "mediaId");
        if (id != null) status["media"] = WallpaperFiles.Media(dataDirectory, id);
        return status;
    }

    private async void Receive(object sender, CoreWebView2WebMessageReceivedEventArgs args)
    {
        if (closing || !IsLocal(args.Source)) return;
        object id = null;
        bool appearanceOwned = false;
        activeRequests++;
        try
        {
            if (args.WebMessageAsJson.Length > 48 * 1024 * 1024) throw new InvalidDataException("文件超过大小限制。");
            var request = json.Deserialize<Dictionary<string, object>>(args.WebMessageAsJson);
            id = request["id"];
            var operation = request["operation"] as string;
            if (smokeDirectory != null) smokeOperations.Add(operation);
            if (updateHandoff) throw new InvalidOperationException("正在启动更新安装程序，请稍候。");
            if (operation == "explorer.apply" || operation == "explorer.restore" || operation == "appearance.apply" || operation == "appearance.restore")
            {
                appearanceOwned = await appearanceLock.WaitAsync(0);
                if (!appearanceOwned) throw new InvalidOperationException("正在应用桌面设置，请等待当前操作完成。");
            }
            if (operation == "appearance.apply" || operation == "appearance.restore")
            {
                var appearancePayload = request.ContainsKey("payload") ? request["payload"] as Dictionary<string, object> : null;
                var appearanceResult = await ExecuteAppearance(operation, appearancePayload);
                if (!closing) view.CoreWebView2.PostWebMessageAsJson(json.Serialize(new { id = id, result = appearanceResult }));
                return;
            }
            if (operation == "pets.import")
            {
                object imported;
                using (var dialog = new OpenFileDialog { Title = "导入已安装或已解压桌宠的主程序", Filter = "桌宠主程序|*.exe", CheckFileExists = true, Multiselect = false })
                    imported = dialog.ShowDialog(this) == DialogResult.OK ? await BackendAction("pets.import", new { path = dialog.FileName }) : null;
                if (!closing) view.CoreWebView2.PostWebMessageAsJson(json.Serialize(new { id = id, result = imported }));
                return;
            }
            if (operation == "updates.install" || operation == "templates.apply" || operation == "templates.restore" || operation == "wallpaper.apply" || operation == "wallpaper.stop" || operation == "wallpaper.pause" || (operation != null && operation.StartsWith("runtime.") && operation != "runtime.state"))
            {
                appearanceOwned = await appearanceLock.WaitAsync(0);
                if (!appearanceOwned) throw new InvalidOperationException("正在应用桌面设置，请等待当前操作完成。");
            }
            if (operation == "app.qa-trace" && smokeDirectory != null && qaScript != null)
            {
                view.CoreWebView2.PostWebMessageAsJson(json.Serialize(new { id = id, result = smokeOperations.ToArray() }));
                return;
            }
            if (operation == "app.qa-suspend" && smokeDirectory != null && qaScript != null)
            {
                view.Visible = false;
                var suspended = await view.CoreWebView2.TrySuspendAsync();
                var observedSuspended = view.CoreWebView2.IsSuspended;
                await Task.Delay(1000);
                view.CoreWebView2.Resume(); view.Visible = true;
                view.CoreWebView2.PostWebMessageAsJson(json.Serialize(new { id = id, result = new { suspended = suspended, observedSuspended = observedSuspended, resumed = !view.CoreWebView2.IsSuspended } }));
                return;
            }
            if (operation == "app.qa-complete" && smokeDirectory != null && qaScript != null)
            {
                File.WriteAllText(Path.Combine(smokeDirectory, "qa-result.json"), json.Serialize(request["payload"]), new UTF8Encoding(false));
                File.WriteAllText(Path.Combine(smokeDirectory, "native-operations.json"), json.Serialize(smokeOperations), new UTF8Encoding(false));
                using (var capture = File.Create(Path.Combine(smokeDirectory, "native-ui.png"))) await view.CoreWebView2.CapturePreviewAsync(CoreWebView2CapturePreviewImageFormat.Png, capture);
                view.CoreWebView2.PostWebMessageAsJson(json.Serialize(new { id = id, result = new { ok = true } }));
                smokeTimeout.Stop(); closeAfterRequests = true; return;
            }
            if (operation != null && operation.StartsWith("templates.", StringComparison.Ordinal))
            {
                var payload = request.ContainsKey("payload") ? request["payload"] as Dictionary<string, object> : null;
                var result = await ExecuteTemplates(operation, payload);
                if (!closing) view.CoreWebView2.PostWebMessageAsJson(json.Serialize(new { id = id, result = result }));
                return;
            }
            if (operation != null && operation.StartsWith("updates.", StringComparison.Ordinal))
            {
                var payload = request.ContainsKey("payload") ? request["payload"] as Dictionary<string, object> : null;
                object result;
                if (operation == "updates.state" || operation == "updates.check") result = await BackendAction(operation, new { });
                else if (operation == "updates.download") result = await BackendAction(operation, new { version = WallpaperFiles.Text(payload, "version") });
                else if (operation == "updates.cancel")
                {
                    var folder = Path.Combine(dataDirectory, "updates"); Directory.CreateDirectory(folder);
                    File.WriteAllText(Path.Combine(folder, "cancel"), "cancel");
                    result = new { ok = true };
                }
                else if (operation == "updates.local")
                {
                    using (var dialog = new OpenFileDialog { Title = "选择更新安装包（同目录需有 .exe.sha256 文件）", Filter = "ThemeStudio 安装包|ThemeStudio-*-Windows-x64-Setup.exe", CheckFileExists = true, Multiselect = false })
                    {
                        result = dialog.ShowDialog(this) == DialogResult.OK ? await BackendAction(operation, new { path = dialog.FileName }) : null;
                    }
                }
                else if (operation == "updates.install")
                {
                    if (activeRequests > 1) throw new InvalidOperationException("其他操作尚未完成，请稍后启动安装。");
                    updateHandoff = true;
                    try
                    {
                        var verified = await BackendAction("updates.verify", new { id = WallpaperFiles.Text(payload, "id") });
                        var installer = WallpaperFiles.Text(verified, "path");
                        var version = WallpaperFiles.Text(verified, "version");
                        var launched = Process.Start(InstallerUpdate.Prepare(installer, version, Application.StartupPath));
                        if (launched == null) throw new IOException("未能启动更新安装程序。");
                        launched.Dispose();
                        result = new { started = true };
                        closeAfterRequests = true;
                    }
                    catch { updateHandoff = false; throw; }
                }
                else throw new InvalidDataException("不支持的更新操作。");
                if (!closing) view.CoreWebView2.PostWebMessageAsJson(json.Serialize(new { id = id, result = result }));
                return;
            }
            if (operation != null && operation.StartsWith("wallpaper.", StringComparison.Ordinal))
            {
                var payload = request.ContainsKey("payload") ? request["payload"] as Dictionary<string, object> : null;
                var result = await ExecuteWallpaper(operation, payload);
                if (!closing) view.CoreWebView2.PostWebMessageAsJson(json.Serialize(new { id = id, result = result }));
                return;
            }
            if (operation == "app.ready")
            {
                var payload = request["payload"] as Dictionary<string, object>;
                if (payload == null || Convert.ToInt32(payload["roles"]) != 17) throw new InvalidDataException("UI readiness data is invalid");
                ready = true;
                WriteReport(true, null, payload);
                view.CoreWebView2.PostWebMessageAsJson(json.Serialize(new { id = id, result = new { ok = true } }));
                if (smokeDirectory != null)
                {
                    if (qaScript == null) { smokeTimeout.Stop(); closeAfterRequests = true; }
                    else await view.CoreWebView2.ExecuteScriptAsync(File.ReadAllText(qaScript, Encoding.UTF8));
                }
                return;
            }
            if (!operations.Contains(operation)) throw new InvalidDataException("不支持的桌面操作。");
            var response = await CallBackend(args.WebMessageAsJson);
            if (!closing) view.CoreWebView2.PostWebMessageAsJson(response);
        }
        catch (Exception error)
        {
            if (!closing) view.CoreWebView2.PostWebMessageAsJson(json.Serialize(new { id = id, error = error.Message }));
            if (smokeDirectory != null)
                File.WriteAllText(Path.Combine(smokeDirectory, "native-action-error.json"), json.Serialize(new { requestId = id, error = error.ToString(), time = DateTimeOffset.Now.ToString("o") }), new UTF8Encoding(false));
        }
        finally
        {
            if (appearanceOwned) appearanceLock.Release();
            activeRequests--;
            if (!closing && activeRequests == 0)
            {
                if (closeAfterRequests) BeginInvoke(new Action(Close));
                else UpdateVisibility(this, EventArgs.Empty);
            }
        }
    }

    private async Task<object> ExecuteTemplates(string operation, Dictionary<string, object> payload)
    {
        object result;
        if (operation == "templates.list") result = await BackendAction(operation, new { });
        else if (operation == "templates.import")
        {
            using (var dialog = new OpenFileDialog { Title = "导入主题数据包", Filter = "ThemeStudio 主题数据包|*.tspack;*.zip", CheckFileExists = true, Multiselect = false })
            {
                result = dialog.ShowDialog(this) == DialogResult.OK ? await BackendAction(operation, new { path = dialog.FileName }) : null;
            }
        }
        else if (operation == "templates.export")
        {
            var templateId = WallpaperFiles.Text(payload, "id");
            await BackendAction("templates.plan", new { id = templateId });
            using (var dialog = new SaveFileDialog { Title = "导出完整主题数据包", Filter = "ThemeStudio 主题数据包|*.tspack", DefaultExt = "tspack", AddExtension = true, FileName = templateId + ".tspack", OverwritePrompt = true })
            {
                if (dialog.ShowDialog(this) != DialogResult.OK) result = null;
                else
                {
                    var exported = await BackendAction(operation, new { id = templateId });
                    var source = WallpaperFiles.Text(exported, "path");
                    var destination = dialog.FileName;
                    await Task.Run(delegate { File.Copy(source, destination, true); });
                    result = new { path = destination };
                }
            }
        }
        else if (operation == "templates.restore")
        {
            var current = await BackendAction("templates.current", new { });
            var active = WallpaperFiles.Running(dataDirectory) ? WallpaperFiles.Read(WallpaperFiles.ConfigPath(dataDirectory)) : null;
            if (active != null && WallpaperFiles.Text(active, "mediaId") != WallpaperFiles.Text(current, "motionMediaId"))
                throw new InvalidOperationException("当前动态壁纸已被其他操作修改，请先停止它再恢复模板。");
            if (active != null) await wallpaper.Stop();
            Dictionary<string, object> restored = null;
            Exception restoreFailure = null;
            try { restored = await BackendAction(operation, new { }); }
            catch (Exception failure) { restoreFailure = failure; }
            if (restoreFailure != null) { if (active != null) await wallpaper.Apply(active); throw restoreFailure; }
            var restoreId = WallpaperFiles.Text(restored, "id");
            if (restoreId != null && System.Text.RegularExpressions.Regex.IsMatch(restoreId, "^[a-f0-9]{32}$"))
            {
                var previous = WallpaperFiles.Read(Path.Combine(dataDirectory, "template-native-history", restoreId + ".json"));
                if (previous != null && previous.ContainsKey("previous")) previous = previous["previous"] as Dictionary<string, object>;
                if (previous != null && WallpaperFiles.Flag(previous, "enabled")) await wallpaper.Apply(previous);
            }
            result = restored;
        }
        else
        {
            var templateId = WallpaperFiles.Text(payload, "id");
            if (templateId == null || !System.Text.RegularExpressions.Regex.IsMatch(templateId, "^[a-z0-9-]{1,64}$")) throw new InvalidDataException("模板编号无效。");
            var plan = await BackendAction("templates.plan", new { id = templateId });
            if (operation == "templates.plan") result = plan;
            else
            {
                var mode = WallpaperFiles.Text(payload, "wallpaperMode") ?? "static";
                if (mode != "static" && mode != "animated") throw new InvalidDataException("壁纸模式无效。");
                var sources = await BackendAction("templates.media", new { id = templateId });
                if (mode == "animated" && WallpaperFiles.Text(sources, "animatedWallpaper") == null) throw new InvalidDataException("这套主题只提供静态壁纸，请选择静态版。");
                var resource = await Task.Run(delegate { return WallpaperFiles.Import(dataDirectory, WallpaperFiles.Text(sources, "wallpaper")); });
                var media = json.Deserialize<Dictionary<string, object>>(json.Serialize(resource));
                var motion = mode == "animated" ? json.Deserialize<Dictionary<string, object>>(json.Serialize(await Task.Run(delegate { return WallpaperFiles.Import(dataDirectory, WallpaperFiles.Text(sources, "animatedWallpaper")); }))) : null;
                if (operation == "templates.preview") result = motion ?? media;
                else if (operation == "templates.apply")
                {
                    var previous = WallpaperFiles.Running(dataDirectory) ? WallpaperFiles.Read(WallpaperFiles.ConfigPath(dataDirectory)) : null;
                    await wallpaper.Stop();
                    payload["mediaId"] = media["id"];
                    payload["wallpaperMode"] = mode;
                    payload["motionMediaId"] = motion == null ? null : motion["id"];
                    Exception templateFailure = null;
                    Dictionary<string, object> applied = null;
                    try
                    {
                        applied = await BackendAction(operation, payload);
                        WallpaperFiles.Write(Path.Combine(dataDirectory, "template-native-history", WallpaperFiles.Text(applied, "id") + ".json"), new { previous = previous, mode = mode });
                        if (motion != null) await wallpaper.Apply(new Dictionary<string, object> {
                            { "mediaId", motion["id"] }, { "settings", new Dictionary<string, object> {
                                { "enabled", false }, { "preset", "elegance" }, { "strength", 1 }, { "perspective", false }, { "tilt", 0 }, { "opposite", true } } }
                        });
                    }
                    catch (Exception failure) { templateFailure = failure; }
                    if (templateFailure != null)
                    {
                        var failures = new List<string> { templateFailure.Message };
                        try { await wallpaper.Stop(); } catch (Exception recovery) { failures.Add(recovery.Message); }
                        if (applied != null) { try { await BackendAction("templates.restore", new { }); } catch (Exception recovery) { failures.Add(recovery.Message); } }
                        if (previous != null) { try { await wallpaper.Apply(previous); } catch (Exception recovery) { failures.Add(recovery.Message); } }
                        throw new InvalidOperationException(String.Join("；", failures.ToArray()));
                    }
                    result = applied;
                }
                else throw new InvalidDataException("不支持的模板操作。");
            }
        }
        return result;
    }

    private async Task<object> ExecuteWallpaper(string operation, Dictionary<string, object> payload)
    {
        object result;
        if (operation == "wallpaper.status")
        {
            var still = await BackendAction("wallpaper.static.status", new { });
            result = WallpaperFiles.Flag(still, "active") && !WallpaperFiles.Running(dataDirectory) ? WithMedia(still) : wallpaper.Status();
        }
        else if (operation == "wallpaper.apply")
        {
            var mediaId = WallpaperFiles.Text(payload, "mediaId");
                    if (mediaId == null && WallpaperFiles.Flag(payload, "useExample"))
                    {
                        var example = WallpaperFiles.Text(payload, "kind") == "video" ? "parallax-motion.mp4" : "parallax-landscape.svg";
                        var imported = json.Deserialize<Dictionary<string, object>>(json.Serialize(await Task.Run(delegate { return WallpaperFiles.Import(dataDirectory, Path.Combine(Application.StartupPath, "wwwroot", "fixtures", example)); })));
                        payload["mediaId"] = imported["id"]; mediaId = Convert.ToString(imported["id"]);
                    }
            WallpaperFiles.Media(dataDirectory, mediaId);
            var settings = WallpaperFiles.Settings(payload["settings"]);
            if (!WallpaperFiles.Flag(settings, "enabled") && WallpaperFiles.CanUseStatic(dataDirectory, mediaId))
            {
                await wallpaper.Stop();
                result = WithMedia(await BackendAction("wallpaper.static.apply", payload));
            }
            else result = await wallpaper.Apply(payload);
        }
        else if (operation == "wallpaper.pause") result = await wallpaper.Pause(WallpaperFiles.Flag(payload, "paused"));
        else if (operation == "wallpaper.stop")
        {
            if (WallpaperFiles.Running(dataDirectory)) result = await wallpaper.Stop();
            else result = WithMedia(await BackendAction("wallpaper.static.restore", new { }));
        }
        else if (operation == "wallpaper.example")
        {
            var name = WallpaperFiles.Text(payload, "kind") == "video" ? "parallax-motion.mp4" : "parallax-landscape.svg";
            result = await Task.Run(delegate { return WallpaperFiles.Import(dataDirectory, Path.Combine(Application.StartupPath, "wwwroot", "fixtures", name)); });
        }
        else if (operation == "wallpaper.pick")
        {
            using (var dialog = new OpenFileDialog { Title = "选择桌面壁纸图片或视频", Filter = "图片和视频|*.png;*.jpg;*.jpeg;*.webp;*.bmp;*.gif;*.svg;*.mp4;*.webm;*.m4v;*.mov;*.mkv;*.avi", CheckFileExists = true, Multiselect = false })
            {
                if (dialog.ShowDialog(this) != DialogResult.OK) result = null;
                else { var selected = dialog.FileName; result = await Task.Run(delegate { return WallpaperFiles.Import(dataDirectory, selected); }); }
            }
        }
        else throw new InvalidDataException("不支持的壁纸操作。");
        return result;
    }

    private Dictionary<string, object> NativeAppearanceSnapshot()
    {
        if (!WallpaperFiles.Running(dataDirectory)) return null;
        var desired = WallpaperFiles.Read(WallpaperFiles.ConfigPath(dataDirectory));
        if (desired == null || !WallpaperFiles.Flag(desired, "enabled")) return null;
        return new Dictionary<string, object> { { "mediaId", desired["mediaId"] },
            { "settings", desired["settings"] }, { "paused", WallpaperFiles.Flag(desired, "paused") } };
    }

    private async Task RestoreNativeAppearance(Dictionary<string, object> result)
    {
        if (!WallpaperFiles.Flag(result, "wallpaperIncluded")) return;
        var target = result.ContainsKey("native") ? result["native"] as Dictionary<string, object> : null;
        if (target != null) await wallpaper.Apply(target);
    }

    private async Task<object> ExecuteAppearance(string operation, Dictionary<string, object> payload)
    {
        if (payload == null) throw new InvalidDataException("外观设置无效。");
        var beforeNative = NativeAppearanceSnapshot();
        Dictionary<string, object> prepared;
        if (operation == "appearance.apply")
            prepared = await BackendAction("appearance.begin", new { operations = payload.ContainsKey("operations") ? payload["operations"] : null, native = beforeNative });
        else
            prepared = await BackendAction("appearance.prepare-restore", new { kind = WallpaperFiles.Text(payload, "kind"), native = beforeNative });
        var transactionId = WallpaperFiles.Text(prepared, "id");
        Exception appearanceFailure = null;
        try
        {
            if (operation == "appearance.apply")
            {
                foreach (var raw in (System.Collections.IEnumerable)payload["operations"])
                {
                    var step = raw as Dictionary<string, object>;
                    var name = WallpaperFiles.Text(step, "operation");
                    var values = step["payload"] as Dictionary<string, object>;
                    object applied;
                    if (name == "templates.apply") applied = await ExecuteTemplates(name, values);
                    else if (name == "wallpaper.apply" || name == "wallpaper.pause" || name == "wallpaper.stop") applied = await ExecuteWallpaper(name, values);
                    else applied = await BackendAction(name, values);
                    var result = applied as Dictionary<string, object>;
                    if (name == "icons.apply" && result != null && result.ContainsKey("entries"))
                    {
                        foreach (var entry in (System.Collections.IEnumerable)result["entries"])
                            if (WallpaperFiles.Text(entry as Dictionary<string, object>, "status") != "applied")
                                throw new InvalidOperationException("部分图标应用失败，正在恢复本次整套修改。");
                    }
                }
                return await BackendAction("appearance.commit", new { id = transactionId, native = NativeAppearanceSnapshot() });
            }
            if (WallpaperFiles.Flag(prepared, "wallpaperIncluded")) await wallpaper.Stop();
            var restored = await BackendAction(WallpaperFiles.Flag(prepared, "recover") ? "appearance.rollback" : "appearance.restore-core", new { id = transactionId });
            await RestoreNativeAppearance(restored);
            if (WallpaperFiles.Flag(prepared, "recover"))
                return await BackendAction("appearance.recovered", new { id = transactionId });
            return await BackendAction("appearance.commit", new { id = transactionId, native = NativeAppearanceSnapshot() });
        }
        catch (Exception failure) { appearanceFailure = failure; }
        var errors = new List<string> { appearanceFailure.Message };
        try
        {
            if (WallpaperFiles.Flag(prepared, "wallpaperIncluded")) await wallpaper.Stop();
            var restored = await BackendAction("appearance.rollback", new { id = transactionId });
            await RestoreNativeAppearance(restored);
            await BackendAction("appearance.recovered", new { id = transactionId });
        }
        catch (Exception recovery) { errors.Add("整套恢复未完成，备份已保留：" + recovery.Message); }
        throw new InvalidOperationException(String.Join("；", errors.ToArray()));
    }

    private void WriteReport(bool success, string error, object payload)
    {
        var destination = smokeDirectory ?? Path.Combine(dataDirectory, "diagnostics");
        Directory.CreateDirectory(destination);
        var report = new { product = "Theme Studio", version = "0.6.4", ready = success, time = DateTimeOffset.Now.ToString("o"), dataDirectory = dataDirectory,
            executable = Application.ExecutablePath, nativeWebView = true, backend = "bundled executable", ui = payload, error = error };
        File.WriteAllText(Path.Combine(destination, "native-runtime.json"), json.Serialize(report), new UTF8Encoding(false));
    }

    private void OnClosing(object sender, FormClosingEventArgs args)
    {
        if (activeRequests > 0) { args.Cancel = true; return; }
        closing = true;
    }
    private void OnClosed(object sender, FormClosedEventArgs args)
    {
        if (smokeTimeout != null) smokeTimeout.Dispose();
        if (backend != null)
        {
            try { backendInput.Close(); backend.WaitForExit(3000); } catch { }
            backend.Dispose();
        }
        view.Dispose();
        bridgeLock.Dispose();
        appearanceLock.Dispose();
    }
}

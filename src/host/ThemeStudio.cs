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
[assembly: AssemblyVersion("0.2.0.0")]
[assembly: AssemblyFileVersion("0.2.0.0")]

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
    private readonly HashSet<string> operations = new HashSet<string> { "state", "icons.import", "icons.assign", "icons.apply", "icons.restore", "cursors.import", "cursors.save", "cursors.apply", "cursors.restore", "recipe.export", "runtime.state", "runtime.apply", "runtime.seelen.apply", "runtime.seelen.stop", "runtime.windhawk.apply", "runtime.windhawk.stop" };
    private Process backend;
    private StreamWriter backendInput;
    private int activeRequests;
    private bool closing;
    private bool ready;
    private string backendError = "";
    private System.Windows.Forms.Timer smokeTimeout;
    private readonly NativeWallpaperClient wallpaper;

    internal StudioWindow(string smoke, string script)
    {
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
        if (smoke != null)
        {
            ShowInTaskbar = false; Opacity = 0;
            smokeTimeout = new System.Windows.Forms.Timer { Interval = qaScript == null ? 45000 : 120000 };
            smokeTimeout.Tick += delegate { if (!ready || qaScript != null) { Environment.ExitCode = 2; WriteReport(false, "Native UI test timed out", null); Close(); } };
            smokeTimeout.Start();
        }
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

    private async void Receive(object sender, CoreWebView2WebMessageReceivedEventArgs args)
    {
        if (closing || !IsLocal(args.Source)) return;
        object id = null;
        activeRequests++;
        try
        {
            if (args.WebMessageAsJson.Length > 48 * 1024 * 1024) throw new InvalidDataException("文件超过大小限制。");
            var request = json.Deserialize<Dictionary<string, object>>(args.WebMessageAsJson);
            id = request["id"];
            var operation = request["operation"] as string;
            if (operation == "app.qa-complete" && smokeDirectory != null && qaScript != null)
            {
                File.WriteAllText(Path.Combine(smokeDirectory, "qa-result.json"), json.Serialize(request["payload"]), new UTF8Encoding(false));
                using (var capture = File.Create(Path.Combine(smokeDirectory, "native-ui.png"))) await view.CoreWebView2.CapturePreviewAsync(CoreWebView2CapturePreviewImageFormat.Png, capture);
                view.CoreWebView2.PostWebMessageAsJson(json.Serialize(new { id = id, result = new { ok = true } }));
                smokeTimeout.Stop(); BeginInvoke(new Action(Close)); return;
            }
            if (operation != null && operation.StartsWith("wallpaper.", StringComparison.Ordinal))
            {
                var payload = request.ContainsKey("payload") ? request["payload"] as Dictionary<string, object> : null;
                object result;
                if (operation == "wallpaper.status") result = wallpaper.Status();
                else if (operation == "wallpaper.apply") result = await wallpaper.Apply(payload);
                else if (operation == "wallpaper.pause") result = await wallpaper.Pause(WallpaperFiles.Flag(payload, "paused"));
                else if (operation == "wallpaper.stop") result = await wallpaper.Stop();
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
                    if (qaScript == null) { smokeTimeout.Stop(); BeginInvoke(new Action(Close)); }
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
            if (smokeDirectory != null) WriteReport(false, error.ToString(), null);
        }
        finally { activeRequests--; }
    }

    private void WriteReport(bool success, string error, object payload)
    {
        var destination = smokeDirectory ?? Path.Combine(dataDirectory, "diagnostics");
        Directory.CreateDirectory(destination);
        var report = new { product = "Theme Studio", version = "0.2.0", ready = success, time = DateTimeOffset.Now.ToString("o"), dataDirectory = dataDirectory,
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
    }
}

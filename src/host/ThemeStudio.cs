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
[assembly: AssemblyVersion("0.1.1.0")]
[assembly: AssemblyFileVersion("0.1.1.0")]

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
        for (int i = 0; i < args.Length; i++)
            if (args[i] == "--smoke-dir" && i + 1 < args.Length) smoke = Path.GetFullPath(args[++i]);
        Application.Run(new StudioWindow(smoke));
    }
}

internal sealed class StudioWindow : Form
{
    private const string VirtualHost = "app.theme-studio.invalid";
    private readonly string dataDirectory;
    private readonly string smokeDirectory;
    private readonly string scanDirectory;
    private readonly JavaScriptSerializer json = new JavaScriptSerializer { MaxJsonLength = 48 * 1024 * 1024, RecursionLimit = 100 };
    private readonly WebView2 view = new WebView2 { Dock = DockStyle.Fill };
    private readonly SemaphoreSlim bridgeLock = new SemaphoreSlim(1, 1);
    private readonly HashSet<string> operations = new HashSet<string> { "state", "icons.import", "icons.apply", "icons.restore", "cursors.import", "cursors.save", "cursors.apply", "cursors.restore", "recipe.export" };
    private Process backend;
    private StreamWriter backendInput;
    private int activeRequests;
    private bool closing;
    private bool ready;
    private string backendError = "";
    private System.Windows.Forms.Timer smokeTimeout;

    internal StudioWindow(string smoke)
    {
        smokeDirectory = smoke;
        dataDirectory = smoke == null ? Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "ThemeStudio") : Path.Combine(smoke, "data");
        scanDirectory = smoke == null ? null : Path.Combine(smoke, "desktop");
#if TUTORIAL_MODE
        dataDirectory = Path.Combine(Application.StartupPath, "demo", "data");
        scanDirectory = Path.Combine(Application.StartupPath, "demo", "desktop");
#endif
        Directory.CreateDirectory(dataDirectory);
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
            smokeTimeout = new System.Windows.Forms.Timer { Interval = 45000 };
            smokeTimeout.Tick += delegate { if (!ready) { Environment.ExitCode = 2; WriteReport(false, "Native UI readiness timed out", null); Close(); } };
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
            var answer = await backend.StandardOutput.ReadLineAsync();
            if (answer == null) throw new IOException("桌面组件已停止。" + backendError);
            return answer;
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
            if (operation == "app.ready")
            {
                var payload = request["payload"] as Dictionary<string, object>;
                if (payload == null || Convert.ToInt32(payload["roles"]) != 17) throw new InvalidDataException("UI readiness data is invalid");
                ready = true;
                WriteReport(true, null, payload);
                view.CoreWebView2.PostWebMessageAsJson(json.Serialize(new { id = id, result = new { ok = true } }));
                if (smokeDirectory != null) { smokeTimeout.Stop(); BeginInvoke(new Action(Close)); }
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
        var report = new { product = "Theme Studio", version = "0.1.1", ready = success, time = DateTimeOffset.Now.ToString("o"), dataDirectory = dataDirectory,
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

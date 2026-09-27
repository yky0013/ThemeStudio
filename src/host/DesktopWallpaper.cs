// SPDX-License-Identifier: AGPL-3.0-or-later
// WorkerW detection and parenting ported from Seelen-UI@faaf244,
// src/background/widgets/wallpaper_manager/mod.rs. Media and motion remain in
// Seelen's existing components and the attributed Windhawk motion source.
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using System.Web.Script.Serialization;
using System.Windows.Forms;
using Microsoft.Web.WebView2.Core;
using Microsoft.Web.WebView2.WinForms;

internal static class WallpaperFiles
{
    internal const string AppHost = "app.theme-studio.invalid";
    internal const string MediaHost = "media.theme-studio.invalid";
    internal static readonly JavaScriptSerializer Json = new JavaScriptSerializer { MaxJsonLength = 1024 * 1024 };
    internal static string ConfigPath(string data) { return Path.Combine(data, "wallpaper", "desired.json"); }
    internal static string StatusPath(string data) { return Path.Combine(data, "wallpaper", "observed.json"); }
    internal static string MediaDirectory(string data) { return Path.Combine(data, "wallpapers"); }
    internal static string MutexName(string data)
    {
        using (var hash = SHA256.Create()) return "Local\\ThemeStudioWallpaper-" + BitConverter.ToString(hash.ComputeHash(Encoding.UTF8.GetBytes(Path.GetFullPath(data).ToUpperInvariant()))).Replace("-", "");
    }
    internal static bool Running(string data)
    {
        Mutex mutex;
        if (!Mutex.TryOpenExisting(MutexName(data), out mutex)) return false;
        mutex.Dispose(); return true;
    }
    internal static Dictionary<string, object> Read(string path)
    {
        try { return Json.Deserialize<Dictionary<string, object>>(File.ReadAllText(path, Encoding.UTF8)); }
        catch (IOException) { return null; }
        catch (ArgumentException) { return null; }
    }
    internal static void Write(string path, object value)
    {
        Directory.CreateDirectory(Path.GetDirectoryName(path));
        var temporary = path + "." + Guid.NewGuid().ToString("N") + ".tmp";
        File.WriteAllText(temporary, Json.Serialize(value), new UTF8Encoding(false));
        if (File.Exists(path)) File.Replace(temporary, path, null); else File.Move(temporary, path);
    }
    internal static string Text(Dictionary<string, object> value, string key)
    {
        object item; return value != null && value.TryGetValue(key, out item) ? item as string : null;
    }
    internal static bool Flag(Dictionary<string, object> value, string key)
    {
        object item; return value != null && value.TryGetValue(key, out item) && item is bool && (bool)item;
    }
    internal static object Media(string data, string id)
    {
        if (id == null || !Regex.IsMatch(id, "^[a-f0-9]{64}\\.(png|jpg|jpeg|webp|bmp|gif|svg|mp4|webm|m4v|mov|mkv|avi)$")) throw new InvalidDataException("壁纸资源无效，请重新选择文件。");
        var file = Path.Combine(MediaDirectory(data), id);
        if (!File.Exists(file)) throw new FileNotFoundException("壁纸素材已不存在，请重新导入。");
        var metadata = Read(file + ".json");
        return new { id = id, name = Text(metadata, "name") ?? id, kind = Text(metadata, "kind") ?? "image", url = "https://" + MediaHost + "/" + id };
    }
    internal static object Import(string data, string source)
    {
        var extension = Path.GetExtension(source).ToLowerInvariant();
        if (!Regex.IsMatch(extension, "^\\.(png|jpg|jpeg|webp|bmp|gif|svg|mp4|webm|m4v|mov|mkv|avi)$")) throw new InvalidDataException("请选择常见图片或视频文件。");
        var info = new FileInfo(source);
        if (info.Length == 0 || info.Length > 4L * 1024 * 1024 * 1024) throw new InvalidDataException("壁纸文件不能为空，也不能超过 4 GB。");
        string digest;
        using (var hash = SHA256.Create()) using (var stream = File.OpenRead(source)) digest = BitConverter.ToString(hash.ComputeHash(stream)).Replace("-", "").ToLowerInvariant();
        Directory.CreateDirectory(MediaDirectory(data));
        var id = digest + extension;
        var target = Path.Combine(MediaDirectory(data), id);
        if (!File.Exists(target))
        {
            var temporary = target + "." + Guid.NewGuid().ToString("N") + ".tmp";
            try
            {
                File.Copy(source, temporary);
                using (var hash = SHA256.Create()) using (var stream = File.OpenRead(temporary))
                    if (BitConverter.ToString(hash.ComputeHash(stream)).Replace("-", "").ToLowerInvariant() != digest) throw new IOException("复制时素材已变化，请重新选择。");
                File.Move(temporary, target);
            }
            finally { if (File.Exists(temporary)) File.Delete(temporary); }
        }
        var kind = Regex.IsMatch(extension, "^\\.(mp4|webm|m4v|mov|mkv|avi)$") ? "video" : "image";
        Write(target + ".json", new { name = Path.GetFileName(source), kind = kind });
        return Media(data, id);
    }
    internal static Dictionary<string, object> Settings(object value)
    {
        var input = value as Dictionary<string, object>;
        if (input == null) throw new InvalidDataException("视差设置无效。");
        var preset = Text(input, "preset");
        if (preset != "elegance" && preset != "silk" && preset != "depth" && preset != "cinema") throw new InvalidDataException("视差预设无效。");
        foreach (var key in new[] { "enabled", "perspective", "opposite" }) if (!input.ContainsKey(key) || !(input[key] is bool)) throw new InvalidDataException("视差开关无效。");
        double strength = Convert.ToDouble(input["strength"]), tilt = Convert.ToDouble(input["tilt"]);
        if (Double.IsNaN(strength) || Double.IsInfinity(strength) || strength < 0 || strength > 2 || Double.IsNaN(tilt) || Double.IsInfinity(tilt) || tilt < 0 || tilt > 8) throw new InvalidDataException("视差参数超出范围。");
        return new Dictionary<string, object> { { "enabled", input["enabled"] }, { "preset", preset }, { "strength", strength }, { "perspective", input["perspective"] }, { "tilt", tilt }, { "opposite", input["opposite"] } };
    }
}

internal sealed class NativeWallpaperClient
{
    private readonly string data;
    internal NativeWallpaperClient(string directory) { data = directory; Directory.CreateDirectory(WallpaperFiles.MediaDirectory(data)); }
    internal object Status()
    {
        var observed = WallpaperFiles.Read(WallpaperFiles.StatusPath(data)) ?? new Dictionary<string, object>();
        var desired = WallpaperFiles.Read(WallpaperFiles.ConfigPath(data));
        observed["active"] = WallpaperFiles.Running(data) && WallpaperFiles.Flag(observed, "active");
        var id = WallpaperFiles.Text(desired, "mediaId");
        if (id != null) { try { observed["media"] = WallpaperFiles.Media(data, id); } catch (IOException) { } }
        if (desired != null && desired.ContainsKey("settings")) observed["settings"] = desired["settings"];
        return observed;
    }
    internal async Task<object> Apply(Dictionary<string, object> payload)
    {
        var id = WallpaperFiles.Text(payload, "mediaId");
        WallpaperFiles.Media(data, id);
        var settings = WallpaperFiles.Settings(payload["settings"]);
        var request = Guid.NewGuid().ToString("N");
        WallpaperFiles.Write(WallpaperFiles.ConfigPath(data), new { requestId = request, enabled = true, mediaId = id, settings = settings, paused = WallpaperFiles.Flag(payload, "paused") });
        if (!WallpaperFiles.Running(data)) Process.Start(new ProcessStartInfo(Application.ExecutablePath, "--wallpaper-data \"" + data + "\"") { UseShellExecute = false, CreateNoWindow = true, WorkingDirectory = Application.StartupPath });
        return await Wait(request, true);
    }
    internal async Task<object> Pause(bool paused)
    {
        var desired = WallpaperFiles.Read(WallpaperFiles.ConfigPath(data));
        if (desired == null || !WallpaperFiles.Running(data)) throw new InvalidOperationException("桌面壁纸尚未启动。");
        return await Apply(new Dictionary<string, object> { { "mediaId", desired["mediaId"] }, { "settings", desired["settings"] }, { "paused", paused } });
    }
    internal async Task<object> Stop()
    {
        var desired = WallpaperFiles.Read(WallpaperFiles.ConfigPath(data)) ?? new Dictionary<string, object>();
        var request = Guid.NewGuid().ToString("N"); desired["requestId"] = request; desired["enabled"] = false;
        WallpaperFiles.Write(WallpaperFiles.ConfigPath(data), desired);
        if (!WallpaperFiles.Running(data)) { WallpaperFiles.Write(WallpaperFiles.StatusPath(data), new { active = false, requestId = request, restored = true }); return Status(); }
        return await Wait(request, false);
    }
    private async Task<object> Wait(string request, bool expectedActive)
    {
        for (int i = 0; i < 320; i++)
        {
            await Task.Delay(150);
            var observed = WallpaperFiles.Read(WallpaperFiles.StatusPath(data));
            if (WallpaperFiles.Text(observed, "requestId") != request) continue;
            var error = WallpaperFiles.Text(observed, "error");
            if (!String.IsNullOrEmpty(error)) throw new InvalidOperationException("桌面壁纸应用失败：" + error);
            if (WallpaperFiles.Flag(observed, "active") == expectedActive) return Status();
        }
        throw new TimeoutException("桌面播放层没有完成启动，请查看状态后重试。");
    }
}

internal static class DesktopParent
{
    private delegate bool EnumWindowCallback(IntPtr hwnd, IntPtr parameter);
    [StructLayout(LayoutKind.Sequential)] internal struct Point { public int X, Y; }
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] private static extern IntPtr FindWindow(string name, string title);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] private static extern IntPtr FindWindowEx(IntPtr parent, IntPtr after, string name, string title);
    [DllImport("user32.dll")] private static extern bool EnumWindows(EnumWindowCallback callback, IntPtr parameter);
    [DllImport("user32.dll")] private static extern bool PostMessage(IntPtr hwnd, uint message, IntPtr wParam, IntPtr lParam);
    [DllImport("user32.dll", SetLastError = true)] private static extern IntPtr SetParent(IntPtr hwnd, IntPtr parent);
    [DllImport("user32.dll")] internal static extern IntPtr GetParent(IntPtr hwnd);
    [DllImport("user32.dll")] internal static extern bool IsWindow(IntPtr hwnd);
    [DllImport("user32.dll")] internal static extern bool GetCursorPos(out Point point);
    [DllImport("user32.dll", EntryPoint = "GetWindowLongPtrW")] private static extern IntPtr GetStyle(IntPtr hwnd, int index);
    [DllImport("user32.dll", EntryPoint = "SetWindowLongPtrW")] private static extern IntPtr SetStyle(IntPtr hwnd, int index, IntPtr value);
    [DllImport("user32.dll")] private static extern int MapWindowPoints(IntPtr from, IntPtr to, ref Point point, uint count);
    [DllImport("user32.dll")] private static extern bool SetWindowPos(IntPtr hwnd, IntPtr after, int x, int y, int width, int height, uint flags);
    internal static IntPtr Find()
    {
        IntPtr result = IntPtr.Zero;
        EnumWindows(delegate(IntPtr current, IntPtr unused) { if (FindWindowEx(current, IntPtr.Zero, "SHELLDLL_DefView", null) != IntPtr.Zero) { var next = FindWindowEx(IntPtr.Zero, current, "WorkerW", null); if (next != IntPtr.Zero) result = next; } return true; }, IntPtr.Zero);
        if (result == IntPtr.Zero)
        {
            var progman = FindWindow("Progman", null);
            if (progman != IntPtr.Zero && FindWindowEx(progman, IntPtr.Zero, "SHELLDLL_DefView", null) != IntPtr.Zero) result = FindWindowEx(progman, IntPtr.Zero, "WorkerW", null);
        }
        return result;
    }
    internal static IntPtr Attach(IntPtr window, Rectangle bounds)
    {
        var parent = Find();
        if (parent == IntPtr.Zero)
        {
            var progman = FindWindow("Progman", null);
            if (progman == IntPtr.Zero) throw new InvalidOperationException("Windows 桌面管理器不可用。");
            PostMessage(progman, 0x052C, new IntPtr(0xD), new IntPtr(1));
            for (int i = 0; i < 10 && parent == IntPtr.Zero; i++) { Thread.Sleep(100); parent = Find(); }
        }
        if (parent == IntPtr.Zero) throw new InvalidOperationException("没有找到 Windows 桌面背景层。");
        long style = GetStyle(window, -16).ToInt64();
        SetStyle(window, -16, new IntPtr((style | 0x40000000L) & ~0x80000000L & ~0x04000000L));
        long exStyle = GetStyle(window, -20).ToInt64();
        SetStyle(window, -20, new IntPtr((exStyle & ~0x00040000L & ~0x00000100L & ~0x00000010L) | 0x08000020L));
        SetParent(window, parent);
        if (GetParent(window) != parent) throw new InvalidOperationException("无法把播放窗口接入 Windows 桌面。");
        var position = new Point { X = bounds.X, Y = bounds.Y }; MapWindowPoints(IntPtr.Zero, parent, ref position, 1);
        SetWindowPos(window, new IntPtr(1), position.X, position.Y, bounds.Width, bounds.Height, 0x0010);
        return parent;
    }
}

internal sealed class WallpaperWindow : Form
{
    private readonly string data;
    private readonly Rectangle screen;
    private readonly WebView2 view = new WebView2 { Dock = DockStyle.Fill };
    private readonly TaskCompletionSource<bool> frameReady = new TaskCompletionSource<bool>();
    private TaskCompletionSource<bool> applied;
    private string pendingRequest;
    internal IntPtr DesktopHandle;
    internal bool Playing;
    internal WallpaperWindow(string directory, Rectangle bounds)
    {
        data = directory; screen = bounds; Text = "Theme Studio Desktop Background";
        FormBorderStyle = FormBorderStyle.None; ShowInTaskbar = false; StartPosition = FormStartPosition.Manual; Bounds = bounds; BackColor = Color.Black;
        Controls.Add(view);
        DesktopHandle = DesktopParent.Attach(Handle, screen);
        Shown += Initialize;
        FormClosed += delegate { view.Dispose(); };
    }
    protected override bool ShowWithoutActivation { get { return true; } }
    private async void Initialize(object sender, EventArgs args)
    {
        try
        {
            var environment = await CoreWebView2Environment.CreateAsync(null, Path.Combine(data, "wallpaper-webview"), null);
            await view.EnsureCoreWebView2Async(environment);
            var core = view.CoreWebView2;
            core.Settings.IsStatusBarEnabled = false; core.Settings.AreDevToolsEnabled = false; core.Settings.AreDefaultContextMenusEnabled = false;
            core.SetVirtualHostNameToFolderMapping(WallpaperFiles.AppHost, Path.Combine(Application.StartupPath, "wwwroot"), CoreWebView2HostResourceAccessKind.Deny);
            core.SetVirtualHostNameToFolderMapping(WallpaperFiles.MediaHost, WallpaperFiles.MediaDirectory(data), CoreWebView2HostResourceAccessKind.Allow);
            core.NavigationStarting += delegate(object s, CoreWebView2NavigationStartingEventArgs e) { Uri address; if (!Uri.TryCreate(e.Uri, UriKind.Absolute, out address) || address.Scheme != "https" || address.Host != WallpaperFiles.AppHost || address.AbsolutePath != "/wallpaper.html") e.Cancel = true; };
            core.NewWindowRequested += delegate(object s, CoreWebView2NewWindowRequestedEventArgs e) { e.Handled = true; };
            core.PermissionRequested += delegate(object s, CoreWebView2PermissionRequestedEventArgs e) { e.State = CoreWebView2PermissionState.Deny; };
            core.WebMessageReceived += delegate(object s, CoreWebView2WebMessageReceivedEventArgs e)
            {
                Uri address;
                if (e.WebMessageAsJson.Length > 65536 || !Uri.TryCreate(e.Source, UriKind.Absolute, out address) || address.Host != WallpaperFiles.AppHost || address.AbsolutePath != "/wallpaper.html") return;
                var message = WallpaperFiles.Json.Deserialize<Dictionary<string, object>>(e.WebMessageAsJson);
                var operation = WallpaperFiles.Text(message, "operation");
                if (operation == "wallpaper.ready") frameReady.TrySetResult(true);
                else if (WallpaperFiles.Text(message, "requestId") == pendingRequest && applied != null)
                {
                    if (operation == "wallpaper.applied") { Playing = WallpaperFiles.Flag(message, "playing"); applied.TrySetResult(true); }
                    else if (operation == "wallpaper.error") applied.TrySetException(new InvalidOperationException(WallpaperFiles.Text(message, "error")));
                }
            };
            core.Navigate("https://" + WallpaperFiles.AppHost + "/wallpaper.html");
        }
        catch (Exception error) { frameReady.TrySetException(error); }
    }
    internal async Task Apply(Dictionary<string, object> request)
    {
        if (await Task.WhenAny(frameReady.Task, Task.Delay(20000)) != frameReady.Task) throw new TimeoutException("桌面媒体页面加载超时。");
        await frameReady.Task;
        pendingRequest = WallpaperFiles.Text(request, "requestId"); applied = new TaskCompletionSource<bool>();
        view.CoreWebView2.PostWebMessageAsJson(WallpaperFiles.Json.Serialize(new { operation = "apply", requestId = pendingRequest, media = WallpaperFiles.Media(data, WallpaperFiles.Text(request, "mediaId")), settings = WallpaperFiles.Settings(request["settings"]), paused = WallpaperFiles.Flag(request, "paused") }));
        if (await Task.WhenAny(applied.Task, Task.Delay(22000)) != applied.Task) throw new TimeoutException("桌面素材解码超时。");
        await applied.Task;
        if (DesktopParent.GetParent(Handle) != DesktopHandle) DesktopHandle = DesktopParent.Attach(Handle, screen);
    }
    internal void Pointer(DesktopParent.Point cursor)
    {
        if (view.CoreWebView2 != null) view.CoreWebView2.PostWebMessageAsJson(WallpaperFiles.Json.Serialize(new { operation = "pointer", x = cursor.X, y = cursor.Y, bounds = new { left = screen.Left, top = screen.Top, right = screen.Right, bottom = screen.Bottom } }));
    }
    internal object Evidence() { return new { window = Handle.ToInt64(), parent = DesktopParent.GetParent(Handle).ToInt64(), attached = DesktopParent.GetParent(Handle) == DesktopHandle && DesktopParent.IsWindow(DesktopHandle), screen = new { left = screen.Left, top = screen.Top, width = screen.Width, height = screen.Height }, playing = Playing }; }
}

internal sealed class WallpaperRuntime : ApplicationContext
{
    private readonly string data;
    private readonly List<WallpaperWindow> windows = new List<WallpaperWindow>();
    private readonly System.Windows.Forms.Timer timer = new System.Windows.Forms.Timer { Interval = 50 };
    private string requestId;
    private bool busy;
    private int ticks;
    private string screenLayout;
    private WallpaperRuntime(string directory) { data = directory; timer.Tick += Tick; timer.Start(); }
    internal static void Run(string directory)
    {
        bool created;
        using (var mutex = new Mutex(true, WallpaperFiles.MutexName(directory), out created))
        {
            if (!created) return;
            try { Application.Run(new WallpaperRuntime(directory)); }
            finally { mutex.ReleaseMutex(); }
        }
    }
    private async void Tick(object sender, EventArgs args)
    {
        if (busy) return;
        if (++ticks % 5 != 0)
        {
            DesktopParent.Point cursor;
            if (DesktopParent.GetCursorPos(out cursor)) foreach (var window in windows) if (!window.IsDisposed) window.Pointer(cursor);
            return;
        }
        var desired = WallpaperFiles.Read(WallpaperFiles.ConfigPath(data));
        var incoming = WallpaperFiles.Text(desired, "requestId");
        if (incoming == null) return;
        var layout = String.Join("|", Array.ConvertAll(Screen.AllScreens, delegate(Screen screen) { return screen.DeviceName + ":" + screen.Bounds; }));
        bool invalidParent = windows.Exists(delegate(WallpaperWindow window) { return window.IsDisposed || !window.IsHandleCreated || !DesktopParent.IsWindow(window.DesktopHandle) || DesktopParent.GetParent(window.Handle) != window.DesktopHandle; }) || (windows.Count > 0 && screenLayout != layout);
        if (requestId == incoming && !invalidParent) return;
        busy = true;
        try
        {
            if (!WallpaperFiles.Flag(desired, "enabled"))
            {
                CloseWindows(); WallpaperFiles.Write(WallpaperFiles.StatusPath(data), new { active = false, requestId = incoming, restored = true, time = DateTimeOffset.Now.ToString("o") }); ExitThread(); return;
            }
            if (invalidParent) CloseWindows();
            if (windows.Count == 0) { screenLayout = layout; foreach (var screen in Screen.AllScreens) { var window = new WallpaperWindow(data, screen.Bounds); windows.Add(window); window.Show(); } }
            var tasks = new List<Task>(); foreach (var window in windows) tasks.Add(window.Apply(desired));
            await Task.WhenAll(tasks);
            requestId = incoming;
            var evidence = new List<object>(); foreach (var window in windows) evidence.Add(window.Evidence());
            WallpaperFiles.Write(WallpaperFiles.StatusPath(data), new { active = true, requestId = incoming, media = WallpaperFiles.Media(data, WallpaperFiles.Text(desired, "mediaId")), paused = WallpaperFiles.Flag(desired, "paused"), windows = evidence, pid = Process.GetCurrentProcess().Id, time = DateTimeOffset.Now.ToString("o") });
        }
        catch (Exception error)
        {
            requestId = incoming; CloseWindows(); WallpaperFiles.Write(WallpaperFiles.StatusPath(data), new { active = false, requestId = incoming, error = error.Message, time = DateTimeOffset.Now.ToString("o") });
        }
        finally { busy = false; }
    }
    private void CloseWindows() { foreach (var window in windows) { if (!window.IsDisposed) { window.Close(); window.Dispose(); } } windows.Clear(); }
    protected override void ExitThreadCore() { timer.Stop(); timer.Dispose(); CloseWindows(); base.ExitThreadCore(); }
}

using System;
using System.IO;
using System.Linq;
using System.Reflection;

internal static class ManagedComProbe
{
    private static void Main(string[] args)
    {
        var asmPath = @"C:\Windows\Microsoft.NET\assembly\GAC_MSIL\Microsoft.Windows.StartLayout.Commands\v4.0_10.0.0.0__31bf3856ad364e35\Microsoft.Windows.StartLayout.Commands.dll";
        var output = args.Length == 0 ? Path.Combine(Path.GetTempPath(), "native-start-layout-managed-probe.json") : Path.GetFullPath(args[0]);
        var asm = Assembly.LoadFrom(asmPath);
        var cls = asm.GetType("Microsoft.Windows.StartLayout.Commands.CLSID_StartLayoutCmdlet", true);
        var iface = asm.GetType("Microsoft.Windows.StartLayout.Commands.IStartLayoutCmdlet", true);
        Console.WriteLine("class=" + cls.FullName + " guid=" + cls.GUID + " import=" + cls.IsImport);
        Console.WriteLine("interface=" + iface.FullName + " guid=" + iface.GUID + " import=" + iface.IsImport);
        foreach (var method in iface.GetMethods()) Console.WriteLine("method=" + method.Name + " token=0x" + method.MetadataToken.ToString("X8") + " return=" + method.ReturnType.FullName + " params=" + string.Join(",", method.GetParameters().Select(x => x.ParameterType.FullName + " " + x.Name)));
        try
        {
            var instance = Activator.CreateInstance(cls);
            Console.WriteLine("instance=" + instance.GetType().FullName);
            var export = iface.GetMethod("ExportStartLayout");
            export.Invoke(instance, new object[] { output });
            Console.WriteLine("ok=" + File.Exists(output) + " output=" + output);
        }
        catch (TargetInvocationException ex)
        {
            var inner = ex.InnerException;
            Console.WriteLine("target-inner-type=" + (inner == null ? "<null>" : inner.GetType().FullName));
            var com = inner as System.Runtime.InteropServices.COMException;
            if (com != null)
                Console.WriteLine("target-inner-hresult=0x" + com.HResult.ToString("X8"));
            try { Console.WriteLine("target-inner-message=" + (inner == null ? "<null>" : inner.Message)); } catch { }
        }
        catch (Exception ex)
        {
            Console.WriteLine("error-type=" + ex.GetType().FullName + " hresult=0x" + ex.HResult.ToString("X8"));
            try { Console.WriteLine("error-message=" + ex.Message); } catch { }
        }
    }
}

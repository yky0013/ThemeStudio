using System;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Runtime.InteropServices;

internal static class InspectStartLayout
{
    private static void Main(string[] args)
    {
        var path = args.Length == 0
            ? @"C:\Windows\Microsoft.NET\assembly\GAC_MSIL\Microsoft.Windows.StartLayout.Commands\v4.0_10.0.0.0__31bf3856ad364e35\Microsoft.Windows.StartLayout.Commands.dll"
            : Path.GetFullPath(args[0]);
        var asm = Assembly.LoadFrom(path);
        Console.WriteLine("assembly=" + asm.FullName);
        Console.WriteLine("location=" + asm.Location);
        Console.WriteLine("references=" + string.Join(";", asm.GetReferencedAssemblies().Select(x => x.FullName)));
        foreach (var type in asm.GetTypes().OrderBy(x => x.FullName))
        {
            Console.WriteLine("TYPE " + type.FullName + " visibility=" + type.IsPublic + " base=" + type.BaseType);
            Console.WriteLine("  GUID=" + type.GUID + " isComImport=" + type.IsImport + " isInterface=" + type.IsInterface + " isClass=" + type.IsClass);
            foreach (var attr in type.GetCustomAttributesData())
                Console.WriteLine("  ATTR " + attr.AttributeType.FullName + " " + string.Join(", ", attr.ConstructorArguments.Select(x => x.Value == null ? "null" : x.Value.ToString())));
            foreach (var method in type.GetMethods(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly).OrderBy(x => x.Name))
            {
                var p = string.Join(", ", method.GetParameters().Select(x => x.ParameterType.FullName + " " + x.Name));
                Console.WriteLine("  METHOD " + method.Attributes + " " + method.ReturnType.FullName + " " + method.Name + "(" + p + ")");
                var pinvoke = method.GetCustomAttribute<DllImportAttribute>();
                if (pinvoke != null) Console.WriteLine("    DLLIMPORT " + pinvoke.Value + " entry=" + pinvoke.EntryPoint + " calling=" + pinvoke.CallingConvention);
                foreach (var attr in method.GetCustomAttributesData())
                    Console.WriteLine("    ATTR " + attr.AttributeType.FullName + " " + string.Join(", ", attr.ConstructorArguments.Select(x => x.Value == null ? "null" : x.Value.ToString())));
                var body = method.GetMethodBody();
                if (body != null)
                    Console.WriteLine("    IL " + BitConverter.ToString(body.GetILAsByteArray() ?? new byte[0]));
            }
            foreach (var field in type.GetFields(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly).OrderBy(x => x.Name))
                Console.WriteLine("  FIELD " + field.Attributes + " " + field.FieldType.FullName + " " + field.Name);
        }
    }
}

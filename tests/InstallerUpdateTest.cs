using System;
using System.IO;

internal static class InstallerUpdateTest
{
    private static void Main(string[] args)
    {
        var command = InstallerUpdate.Prepare(args[0], args[1], @"E:\主题 工作室\ThemeStudio");
        if (command.Arguments != "/DIR=\"E:\\主题 工作室\\ThemeStudio\"" || command.Verb != "runas" || !command.UseShellExecute)
            throw new Exception("Invalid installer handoff for Unicode path with spaces");
        bool refused = false;
        try { InstallerUpdate.Prepare(args[0], "99.0.0", @"E:\ThemeStudio"); }
        catch (InvalidDataException) { refused = true; }
        if (!refused) throw new Exception("Mismatched version was accepted");
        Console.WriteLine("Installer metadata and quoted Unicode handoff passed. No installer was launched.");
    }
}

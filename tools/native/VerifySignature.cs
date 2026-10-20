// SPDX-License-Identifier: AGPL-3.0-or-later
// Authenticode verification without a shell or PowerShell host.
using System;
using System.Runtime.InteropServices;
using System.Security.Cryptography.X509Certificates;
using System.Web.Script.Serialization;

internal static class VerifySignature
{
    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    private struct FileInfo
    {
        public uint Size;
        [MarshalAs(UnmanagedType.LPWStr)] public string Path;
        public IntPtr File;
        public IntPtr KnownSubject;
    }

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    private struct TrustData
    {
        public uint Size;
        public IntPtr PolicyCallback, SIPClient;
        public uint UIChoice, RevocationChecks, UnionChoice;
        public IntPtr File;
        public uint StateAction;
        public IntPtr StateData;
        public IntPtr URLReference;
        public uint ProviderFlags, UIContext;
    }

    [DllImport("wintrust.dll", ExactSpelling = true, PreserveSig = true)]
    private static extern int WinVerifyTrust(IntPtr window, ref Guid action, ref TrustData data);

    private static int Main(string[] args)
    {
        if (args.Length < 1 || args.Length > 2) return 2;
        IntPtr filePointer = IntPtr.Zero;
        var data = new TrustData();
        Guid action = new Guid("00AAC56B-CD44-11d0-8CC2-00C04FC295EE");
        try
        {
            string path = System.IO.Path.GetFullPath(args[0]);
            var file = new FileInfo { Size = (uint)Marshal.SizeOf(typeof(FileInfo)), Path = path };
            filePointer = Marshal.AllocHGlobal(Marshal.SizeOf(typeof(FileInfo)));
            Marshal.StructureToPtr(file, filePointer, false);
            data.Size = (uint)Marshal.SizeOf(typeof(TrustData));
            data.UIChoice = 2; // WTD_UI_NONE
            data.RevocationChecks = 1; // WTD_REVOKE_WHOLECHAIN
            data.UnionChoice = 1; // WTD_CHOICE_FILE
            data.File = filePointer;
            data.StateAction = 1; // WTD_STATEACTION_VERIFY
            int status = WinVerifyTrust(new IntPtr(-1), ref action, ref data);
            string subject = "";
            if (status == 0)
                using (var certificate = new X509Certificate2(X509Certificate.CreateFromSignedFile(path)))
                    subject = certificate.Subject;
            bool expectedPublisher = args.Length < 2 ||
                subject.IndexOf("O=" + args[1] + ",", StringComparison.OrdinalIgnoreCase) >= 0;
            bool valid = status == 0 && expectedPublisher;
            Console.WriteLine(new JavaScriptSerializer().Serialize(new {
                valid, trustStatus = status, subject, expectedPublisher
            }));
            return valid ? 0 : 1;
        }
        catch (Exception error)
        {
            Console.Error.WriteLine(error.Message);
            return 1;
        }
        finally
        {
            if (data.StateData != IntPtr.Zero)
            {
                data.StateAction = 2; // WTD_STATEACTION_CLOSE
                WinVerifyTrust(new IntPtr(-1), ref action, ref data);
            }
            if (filePointer != IntPtr.Zero)
            {
                Marshal.DestroyStructure(filePointer, typeof(FileInfo));
                Marshal.FreeHGlobal(filePointer);
            }
        }
    }
}

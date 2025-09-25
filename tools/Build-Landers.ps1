Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Process terminated. Process terminated. The type initializer for 'Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry' threw an exception.
   at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)
   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)
   at System.Environment.FailFast(System.String, System.Exception)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)
   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])
System.TypeInitializationException: The type initializer for 'Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry' threw an exception.
 ---> System.TypeInitializationException: The type initializer for 'Microsoft.ApplicationInsights.Extensibility.TelemetryConfiguration' threw an exception.
 ---> System.TypeInitializationException: The type initializer for 'System.Diagnostics.Activity' threw an exception.
 ---> System.TypeInitializationException: The type initializer for 'System.Diagnostics.DiagnosticSourceEventSource' threw an exception.
 ---> System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at System.Globalization.TextInfo.ChangeCaseCommon[TConversion](String source)
   at System.Diagnostics.Tracing.EventSource.GetGuid(Type eventSourceType)
   at System.Diagnostics.Tracing.EventSource..ctor(EventSourceSettings settings, String[] traits)
   at System.Diagnostics.DiagnosticSourceEventSource..cctor()
   --- End of inner exception stack trace ---
   at System.Diagnostics.ActivitySource..ctor(String name, String version, IEnumerable`1 tags)
   at System.Diagnostics.Activity..cctor()
   --- End of inner exception stack trace ---
   at System.Diagnostics.Activity.get_ForceDefaultIdFormat()
   at Microsoft.ApplicationInsights.Extensibility.TelemetryConfiguration.<>c.<.cctor>b__13_0()
   at Microsoft.ApplicationInsights.ActivityExtensions.TryRun(Action action)
   at Microsoft.ApplicationInsights.Extensibility.TelemetryConfiguration..cctor()
   --- End of inner exception stack trace ---
   at Microsoft.ApplicationInsights.Extensibility.TelemetryConfiguration.CreateDefault()
   at Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry..cctor()
   --- End of inner exception stack trace ---
   at Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry.SendPSCoreStartupTelemetry(String mode, Double parametersUsed)
   at Microsoft.PowerShell.ConsoleHost.Start(String bannerText, String helpText, Boolean issProvidedExternally)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
Unhandled exception. System.Management.Automation.PSInvalidOperationException: PowerShell has stopped working because of a security issue: Cannot read the configuration file: C:\Program Files\PowerShell\7\powershell.config.json
 ---> System.TypeInitializationException: The type initializer for 'Newtonsoft.Json.Utilities.ConvertUtils' threw an exception.
 ---> System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at System.Collections.Generic.Dictionary`2.TryInsert(TKey key, TValue value, InsertionBehavior behavior)
   at System.Collections.Generic.Dictionary`2.Add(TKey key, TValue value)
   at Newtonsoft.Json.Utilities.ConvertUtils..cctor()
   --- End of inner exception stack trace ---
   at Newtonsoft.Json.Utilities.ConvertUtils.GetTypeCode(Type t, Boolean& isEnum)
   at Newtonsoft.Json.Serialization.DefaultContractResolver.IsJsonPrimitiveType(Type t)
   at Newtonsoft.Json.Serialization.DefaultContractResolver.CreateContract(Type objectType)
   at System.Collections.Concurrent.ConcurrentDictionary`2.GetOrAdd(TKey key, Func`2 valueFactory)
   at Newtonsoft.Json.Serialization.JsonSerializerInternalReader.Deserialize(JsonReader reader, Type objectType, Boolean checkAdditionalContent)
   at Newtonsoft.Json.JsonSerializer.DeserializeInternal(JsonReader reader, Type objectType)
   at Newtonsoft.Json.JsonSerializer.Deserialize[T](JsonReader reader)
   at System.Management.Automation.Configuration.PowerShellConfig.ReadValueFromFile[T](ConfigScope scope, String key, T defaultValue)
   --- End of inner exception stack trace ---
   at System.Management.Automation.Configuration.PowerShellConfig.ReadValueFromFile[T](ConfigScope scope, String key, T defaultValue)
   at System.Management.Automation.Configuration.PowerShellConfig.GetPowerShellPolicies(ConfigScope scope)
   at System.Collections.Concurrent.ConcurrentDictionary`2.GetOrAdd(TKey key, Func`2 valueFactory)
   at System.Management.Automation.Utils.GetPolicySettingFromConfigFile[T](ConfigScope[] preferenceOrder)
   at System.Management.Automation.Utils.GetPolicySetting[T](ConfigScope[] preferenceOrder)
   at Microsoft.PowerShell.CommandLineParameterParser.GetConfigurationNameFromGroupPolicy()
   at Microsoft.PowerShell.ConsoleHost.ParseCommandLine(String[] args)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)
   at Microsoft.PowerShell.ManagedPSEntry.Main(String[] args)
Process terminated. ←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
Exception of type 'System.OutOfMemoryException' was thrown.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Process terminated. Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
The type initializer for 'Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry' threw an exception.
   at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
ObjectNotFound: The process cannot access the file 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by another process.
     | Stream was not readable.
ObjectNotFound: The process cannot access the file 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by another process.
System.TypeInitializationException: The type initializer for 'System.Management.Automation.Configuration.PowerShellConfig' threw an exception.
 ---> System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at System.Management.Automation.Configuration.PowerShellConfig..ctor()
   at System.Management.Automation.Configuration.PowerShellConfig..cctor()
   --- End of inner exception stack trace ---
   at System.Management.Automation.Utils.GetPolicySettingFromConfigFile[T](ConfigScope[] preferenceOrder)
   at System.Management.Automation.Utils.GetPolicySetting[T](ConfigScope[] preferenceOrder)
   at Microsoft.PowerShell.CommandLineParameterParser.GetConfigurationNameFromGroupPolicy()
   at Microsoft.PowerShell.ConsoleHost.ParseCommandLine(String[] args)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)
   at Microsoft.PowerShell.ManagedPSEntry.Main(String[] args)ObjectNotFound: The process cannot access the file 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
ObjectNotFound: The process cannot access the file 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by another process.

←[31;1mObjectNotFound: ←[31;1mThe process cannot access the file 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by another process.←[0m
←[31;1mObjectNotFound: ←[31;1mThe process cannot access the file 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by another process.←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1mObjectNotFound: ←[31;1mThe process cannot access the file 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by another process.←[0m
←[31;1mObjectNotFound: ←[31;1mThe process cannot access the file 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by another process.←[0m
←[31;1mObjectNotFound: ←[31;1mThe process cannot access the file 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by another process.←[0m
←[31;1mObjectNotFound: ←[31;1mThe process cannot access the file 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by another process.←[0m
←[31;1mObjectNotFound: ←[31;1mThe process cannot access the file 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by another process.←[0m
←[31;1mObjectNotFound: ←[31;1mThe process cannot access the file 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by another process.←[0m
←[31;1mObjectNotFound: ←[31;1mThe process cannot access the file 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by another process.←[0m
←[31;1mObjectNotFound: ←[31;1mThe process cannot access the file 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by another process.←[0m
←[31;1mObjectNotFound: ←[31;1mThe process cannot access the file 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by another process.←[0m
←[31;1mObjectNotFound: ←[31;1mThe process cannot access the file 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by another process.←[0m
←[31;1mObjectNotFound: ←[31;1mThe process cannot access the file 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by another process.←[0m
←[31;1mObjectNotFound: ←[31;1mThe process cannot access the file 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by another process.←[0m
←[31;1mObjectNotFound: ←[31;1mThe process cannot access the file 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by another process.←[0m
Exception of type 'System.OutOfMemoryException' was thrown.←[31;1mObjectNotFound: ←[31;1mThe process cannot access the file 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by another process.←[0m
ObjectNotFound: The process cannot access the file 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by another process.

   at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.

←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
   at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
Line |
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | The process cannot access the file
     | Stream was not readable.
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
     | another process.
   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)
   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mStream was not readable.←[0m

Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | Stream was not readable.
ObjectNotFound: The process cannot access the file 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by another process.
   at System.Environment.FailFast(System.String, System.Exception)
←[31;1mObjectNotFound: ←[31;1mThe process cannot access the file 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by another process.←[0m
ObjectNotFound: The process cannot access the file 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by another process.
ObjectNotFound: The process cannot access the file 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by another process.
ObjectNotFound: The process cannot access the file 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by another process.
ObjectNotFound: The process cannot access the file 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by another process.
ObjectNotFound: The process cannot access the file 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by another process.
ObjectNotFound: The process cannot access the file 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by another process.
←[31;1mObjectNotFound: ←[31;1mThe process cannot access the file 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by another process.←[0m
←[31;1mObjectNotFound: ←[31;1mThe process cannot access the file 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by another process.←[0m
The shell cannot be started. A failure occurred during initialization:
The type initializer for 'System.Management.Automation.Language.Compiler' threw an exception.
   at System.Environment.FailFast(System.String, System.Exception)←[31;1mObjectNotFound: ←[31;1mThe process cannot access the file 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by another process.←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.

ObjectNotFound: The process cannot access the file 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by another process.
ObjectNotFound: The process cannot access the file 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by another process.
ObjectNotFound: The process cannot access the file 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by another process.
ObjectNotFound: The process cannot access the file 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by another process.
   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
ObjectNotFound: The process cannot access the file 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by another process.
ObjectNotFound: The process cannot access the file 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by another process.
ObjectNotFound: The process cannot access the file 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by another process.

ObjectNotFound: The process cannot access the file 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by another process.
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)
   at System.Environment.FailFast(System.String, System.Exception)ObjectNotFound: The process cannot access the file 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by another process.

←[31;1mObjectNotFound: ←[31;1mThe process cannot access the file 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by another process.←[0m
   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)
System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry.SendPSCoreStartupTelemetry(String mode, Double parametersUsed)
   at Microsoft.PowerShell.ConsoleHost.Start(String bannerText, String helpText, Boolean issProvidedExternally)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])
   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])
System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at System.IO.TextWriter..cctor()
   at System.IO.TextWriter..ctor(IFormatProvider formatProvider)
   at Microsoft.PowerShell.ConsoleHost..ctor()
   at Microsoft.PowerShell.ConsoleHost.Start(String bannerText, String helpText, Boolean issProvidedExternally)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)System.TypeInitializationException: The type initializer for 'Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry' threw an exception.
 ---> System.TypeInitializationException: The type initializer for 'Microsoft.ApplicationInsights.Extensibility.TelemetryConfiguration' threw an exception.
 ---> System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at Microsoft.ApplicationInsights.Extensibility.TelemetryConfiguration.<>c.<.cctor>b__13_0()
   at Microsoft.ApplicationInsights.ActivityExtensions.TryRun(Action action)
   at Microsoft.ApplicationInsights.Extensibility.TelemetryConfiguration..cctor()
   --- End of inner exception stack trace ---
   at Microsoft.ApplicationInsights.Extensibility.TelemetryConfiguration.CreateDefault()
   at Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry..cctor()
   --- End of inner exception stack trace ---
   at Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry.SendPSCoreStartupTelemetry(String mode, Double parametersUsed)
   at Microsoft.PowerShell.ConsoleHost.Start(String bannerText, String helpText, Boolean issProvidedExternally)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1mNew-Item: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:2←[0m
Fatal error. Process terminated.
An error occurred while creating the pipeline.
Failed to load System.Private.CoreLib.dll (error code 0x8007000E)
Failed to load System.Private.CoreLib.dll (error code 0x8007000E)
Path: C:\Program Files\PowerShell\7\System.Private.CoreLib.dll
An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.Path: C:\Program Files\PowerShell\7\System.Private.CoreLib.dll
Error message: Out Of Memory
Error message: Out Of Memory

Exception of type 'System.OutOfMemoryException' was thrown.
Out of memory.
Failed to create CoreCLR, HRESULT: 0x8007000E
Failed to create CoreCLR, HRESULT: 0x8007000E
   at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)
   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)
   at System.Environment.FailFast(System.String, System.Exception)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)
   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])
System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at System.Management.Automation.Host.PSHostUserInterface.get_TranscriptionData()
   at System.Management.Automation.Host.PSHostUserInterface.CheckSystemTranscript()
   at Microsoft.PowerShell.ConsoleHostUserInterface..ctor(ConsoleHost parent)
   at Microsoft.PowerShell.ConsoleHost..ctor()
   at Microsoft.PowerShell.ConsoleHost.Start(String bannerText, String helpText, Boolean issProvidedExternally)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)Failed to create RW mapping for RX memory. This can be caused by insufficient memory or hitting the limit of memory mappings on Linux (vm.map_max_count).
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1mformat-default: ←[31;1mException of type 'System.OutOfMemoryException' was thrown.←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Process terminated. Exception of type 'System.OutOfMemoryException' was thrown.
   at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)
   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)
   at System.Environment.FailFast(System.String, System.Exception)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)
   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])
System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at System.Management.Automation.Host.PSHostUserInterface.get_TranscriptionData()
   at System.Management.Automation.Host.PSHostUserInterface.CheckSystemTranscript()
   at Microsoft.PowerShell.ConsoleHostUserInterface..ctor(ConsoleHost parent)
   at Microsoft.PowerShell.ConsoleHost..ctor()
   at Microsoft.PowerShell.ConsoleHost.Start(String bannerText, String helpText, Boolean issProvidedExternally)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)An error occurred while creating the pipeline.
An error occurred while creating the pipeline.
An error occurred while creating the pipeline.

An error occurred while creating the pipeline.
An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
Process terminated. Exception of type 'System.OutOfMemoryException' was thrown.
   at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)
   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)
   at System.Environment.FailFast(System.String, System.Exception)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)
   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])
System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry..cctor()
   at Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry.SendPSCoreStartupTelemetry(String mode, Double parametersUsed)
   at Microsoft.PowerShell.ConsoleHost.Start(String bannerText, String helpText, Boolean issProvidedExternally)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)
An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.
Process terminated. Exception of type 'System.OutOfMemoryException' was thrown.
   at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)
   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)
   at System.Environment.FailFast(System.String, System.Exception)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)
   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])
System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at System.Management.Automation.Internal.ObjectStream.get_ObjectWriter()
   at System.Management.Automation.Runspaces.LocalPipeline.InitStreams()
   at System.Management.Automation.Runspaces.LocalRunspace.CoreCreatePipeline(String command, Boolean addToHistory, Boolean isNested)
   at Microsoft.PowerShell.ConsoleHost.DoRunspaceInitialization(RunspaceCreationEventArgs args)
   at Microsoft.PowerShell.ConsoleHost.CreateRunspace(RunspaceCreationEventArgs runspaceCreationArgs)
   at Microsoft.PowerShell.ConsoleHost.DoRunspaceLoop(String initialCommand, Boolean skipProfiles, Collection`1 initialCommandArgs, Boolean staMode, String configurationName, String configurationFilePath)
   at Microsoft.PowerShell.ConsoleHost.Run(CommandLineParameterParser cpp, Boolean isPrestartWarned)
   at Microsoft.PowerShell.ConsoleHost.Start(String bannerText, String helpText, Boolean issProvidedExternally)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)
An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   2 | ←[0m ←[36;1mNew-Item←[0m -ItemType Directory -Path .\tools -Force | Out-Null←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe 'New-Item' command was found in the module 'Microsoft.PowerShell.Management', but the module could not be←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1mloaded due to the following error: [Exception of type 'System.OutOfMemoryException' was thrown.] For more←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1minformation, run 'Import-Module Microsoft.PowerShell.Management'.←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Process terminated. Process terminated.




















Fatal error.

Fatal error. Fatal error. Fatal error. Fatal error.

Fatal error. Fatal error. Fatal error. Stack overflow.
An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.Process terminated. An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.Fatal error. Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.The type initializer for 'Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry' threw an exception.
An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.Line |









An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …

Process terminated.



Internal CLR error. (0x80131506)


Internal CLR error. (0x80131506)Internal CLR error. (0x80131506)Process terminated.      |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Internal CLR error. (0x80131506)Internal CLR error. (0x80131506)


Internal CLR error. (0x80131506)
     | The process cannot access the file
Out of memory.
Out of memory.
Out of memory.
Out of memory.

     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
Out of memory.

Out of memory.
Out of memory.
     | another process.
An error occurred while creating the pipeline.
Out of memory.
Out of memory.
Out of memory.
An error occurred while creating the pipeline.
Out of memory.
Out of memory.
Out of memory.
Out of memory.
An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.Out of memory.
Exception of type 'System.OutOfMemoryException' was thrown.The type initializer for 'Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry' threw an exception.
Out of memory.
Out of memory.

Exception of type 'System.OutOfMemoryException' was thrown.

out-lineoutput: Exception of type 'System.OutOfMemoryException' was thrown.
An error occurred while creating the pipeline.

The type initializer for 'Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry' threw an exception.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3


   at System.Reflection.RuntimeAssembly.GetTypeCoreIgnoreCase(System.Runtime.CompilerServices.QCallAssembly, System.String, System.ReadOnlySpan`1<System.String>, Int32, System.Runtime.CompilerServices.ObjectHandleOnStack)
Out of memory.
   at System.Reflection.RuntimeAssembly.GetTypeCore(System.String, System.ReadOnlySpan`1<System.String>, Boolean, Boolean)
   at System.Reflection.TypeNameResolver.GetType(System.String, System.ReadOnlySpan`1<System.String>, System.Reflection.Metadata.TypeName)
Out of memory.
   at System.Reflection.TypeNameResolver.GetSimpleType(System.Reflection.Metadata.TypeName)

   at System.Reflection.RuntimeAssembly.GetTypeCoreIgnoreCase(System.Runtime.CompilerServices.QCallAssembly, System.String, System.ReadOnlySpan`1<System.String>, Int32, System.Runtime.CompilerServices.ObjectHandleOnStack)
   at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)Out of memory.
Out of memory.

   at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)Line |
Out of memory.
   at System.Reflection.TypeNameResolver.GetType(System.String, Boolean, Boolean, System.Reflection.Assembly)An error occurred while creating the pipeline.
An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
   at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.An error occurred while creating the pipeline.
An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.Exception of type 'System.OutOfMemoryException' was thrown.

     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
   at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)


   at System.Reflection.RuntimeAssembly.GetTypeCore(System.String, System.ReadOnlySpan`1<System.String>, Boolean, Boolean)

     | The process cannot access the file
   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)


   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)
Out of memory.
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
   at System.Management.Automation.Language.TypeResolver.LookForTypeInSingleAssembly(System.Reflection.Assembly, System.String)
   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)   at System.Reflection.TypeNameResolver.GetType(System.String, System.ReadOnlySpan`1<System.String>, System.Reflection.Metadata.TypeName)     | another process.


   at System.Reflection.TypeNameResolver.GetSimpleType(System.Reflection.Metadata.TypeName)
Unhandled exception.   at System.Reflection.TypeNameResolver.GetType(System.String, Boolean, Boolean, System.Reflection.Assembly)

Out of memory.

Out of memory.
Out of memory.
   at System.Environment.FailFast(System.String, System.Exception)   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)
   at System.Management.Automation.Language.TypeResolver.LookForTypeInSingleAssembly(System.Reflection.Assembly, System.String)   at System.Environment.FailFast(System.String, System.Exception)   at System.Environment.FailFast(System.String, System.Exception)


   at System.Management.Automation.Language.TypeResolver.LookForTypeInAssemblies(System.Management.Automation.Language.TypeName, System.Collections.Generic.IEnumerable`1<System.Reflection.Assembly>, System.Collections.Generic.HashSet`1<System.Reflection.Assembly>, System.Management.Automation.Language.TypeResolutionState, Boolean, System.Exception ByRef)

System.Runtime.InteropServices.SEHException (0x80004005): External component has thrown an exception.
   at System.Management.Automation.Runspaces.LocalPipeline.InvokeThreadProc()
   at System.Management.Automation.Runspaces.PipelineThread.WorkerProc()
   at System.Threading.ExecutionContext.RunInternal(ExecutionContext executionContext, ContextCallback callback, Object state)
--- End of stack trace from previous location ---
   at System.Threading.ExecutionContext.RunInternal(ExecutionContext executionContext, ContextCallback callback, Object state)   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)

   at System.Management.Automation.Language.TypeResolver.LookForTypeInAssemblies(System.Management.Automation.Language.TypeName, System.Collections.Generic.IEnumerable`1<System.Reflection.Assembly>, System.Collections.Generic.HashSet`1<System.Reflection.Assembly>, System.Management.Automation.Language.TypeResolutionState, Boolean, System.Exception ByRef)   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)   at System.Environment.FailFast(System.String, System.Exception)   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])
   at System.Management.Automation.Language.TypeResolver.ResolveTypeNameWorker(System.Management.Automation.Language.TypeName, System.Management.Automation.SessionStateScope, System.Collections.Generic.IEnumerable`1<System.Reflection.Assembly>, System.Collections.Generic.HashSet`1<System.Reflection.Assembly>, System.Management.Automation.Language.TypeResolutionState, Boolean, Boolean, System.Exception ByRef)




System.TypeInitializationException: The type initializer for 'Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry' threw an exception.
 ---> System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at System.Uri.ParseSchemeCheckImplicitFile(String uriString, ParsingError& err, Flags& flags, UriParser& syntax)
   at System.Uri.ParseScheme(String uriString, Flags& flags, UriParser& syntax)
   at System.Uri.CreateThis(String uri, Boolean dontEscape, UriKind uriKind, UriCreationOptions& creationOptions)
   at System.Uri.CreateUri(Uri baseUri, String relativeUri, Boolean dontEscape)
   at Microsoft.ApplicationInsights.Extensibility.Implementation.Endpoints.EndpointContainer.get_FormattedIngestionEndpoint()
   at Microsoft.ApplicationInsights.Extensibility.TelemetrySink..ctor(TelemetryConfiguration telemetryConfiguration, ITelemetryChannel telemetryChannel)
   at Microsoft.ApplicationInsights.Extensibility.TelemetryConfiguration..ctor(String instrumentationKey, ITelemetryChannel channel)
   at Microsoft.ApplicationInsights.Extensibility.TelemetryConfiguration.CreateDefault()
   at Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry..cctor()
   --- End of inner exception stack trace ---
   at Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry.SendPSCoreStartupTelemetry(String mode, Double parametersUsed)
   at Microsoft.PowerShell.ConsoleHost.Start(String bannerText, String helpText, Boolean issProvidedExternally)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])
   at System.Management.Automation.Language.TypeResolver.ResolveTypeNameWorker(System.Management.Automation.Language.TypeName, System.Management.Automation.SessionStateScope, System.Collections.Generic.IEnumerable`1<System.Reflection.Assembly>, System.Collections.Generic.HashSet`1<System.Reflection.Assembly>, System.Management.Automation.Language.TypeResolutionState, Boolean, Boolean, System.Exception ByRef)

   at System.Management.Automation.Language.TypeResolver.CallResolveTypeNameWorkerHelper(System.Management.Automation.Language.TypeName, System.Management.Automation.ExecutionContext, System.Collections.Generic.IEnumerable`1<System.Reflection.Assembly>, Boolean, System.Management.Automation.Language.TypeResolutionState, System.Exception ByRef)
System.TypeInitializationException: The type initializer for 'Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry' threw an exception.
 ---> System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at Microsoft.ApplicationInsights.Extensibility.TelemetryConfiguration..ctor(String instrumentationKey, ITelemetryChannel channel)
   at Microsoft.ApplicationInsights.Extensibility.TelemetryConfiguration.CreateDefault()
   at Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry..cctor()
   --- End of inner exception stack trace ---
   at Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry.SendPSCoreStartupTelemetry(String mode, Double parametersUsed)
   at Microsoft.PowerShell.ConsoleHost.Start(String bannerText, String helpText, Boolean issProvidedExternally)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)   at System.Management.Automation.Language.TypeResolver.CallResolveTypeNameWorkerHelper(System.Management.Automation.Language.TypeName, System.Management.Automation.ExecutionContext, System.Collections.Generic.IEnumerable`1<System.Reflection.Assembly>, Boolean, System.Management.Automation.Language.TypeResolutionState, System.Exception ByRef)System.TypeInitializationException: The type initializer for 'Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry' threw an exception.
 ---> System.TypeInitializationException: The type initializer for 'System.DomainNameHelper' threw an exception.
 ---> System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at System.SpanHelpers.Fill[T](T& refData, UIntPtr numElements, T value)
   at System.Buffers.ProbabilisticMapState..ctor(ReadOnlySpan`1 values, Int32 maxInclusive)
   at System.Buffers.ProbabilisticWithAsciiCharSearchValues`1..ctor(ReadOnlySpan`1 values, Int32 maxInclusive)
   at System.Buffers.SearchValues.Create(ReadOnlySpan`1 values)
   at System.DomainNameHelper..cctor()
   --- End of inner exception stack trace ---
   at System.DomainNameHelper.IsValid(ReadOnlySpan`1 hostname, Boolean iri, Boolean notImplicitFile, Int32& length)
   at System.Uri.CheckAuthorityHelper(Char* pString, Int32 idx, Int32 length, ParsingError& err, Flags& flags, UriParser syntax, String& newHost)
   at System.Uri.PrivateParseMinimal()
   at System.Uri.InitializeUri(ParsingError err, UriKind uriKind, UriFormatException& e)
   at System.Uri.CreateThis(String uri, Boolean dontEscape, UriKind uriKind, UriCreationOptions& creationOptions)
   at System.Uri..ctor(String uriString)
   at Microsoft.ApplicationInsights.Extensibility.Implementation.Endpoints.EndpointProvider.GetEndpoint(EndpointName endpointName)
   at Microsoft.ApplicationInsights.Extensibility.Implementation.Endpoints.EndpointContainer..ctor(IEndpointProvider endpointProvider)
   at Microsoft.ApplicationInsights.Extensibility.TelemetryConfiguration..ctor(String instrumentationKey, ITelemetryChannel channel)
   at Microsoft.ApplicationInsights.Extensibility.TelemetryConfiguration.CreateDefault()
   at Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry..cctor()
   --- End of inner exception stack trace ---
   at Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry.SendPSCoreStartupTelemetry(String mode, Double parametersUsed)
   at Microsoft.PowerShell.ConsoleHost.Start(String bannerText, String helpText, Boolean issProvidedExternally)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)   at System.Management.Automation.Language.TypeResolver.ResolveTypeNameWithContext(System.Management.Automation.Language.TypeName, System.Exception ByRef, System.Reflection.Assembly[], System.Management.Automation.Language.TypeResolutionState)


   at System.Management.Automation.Language.SymbolResolver.VisitTypeName(System.Management.Automation.Language.TypeName, Int32, Boolean)
   at System.Management.Automation.Language.TypeResolver.ResolveTypeNameWithContext(System.Management.Automation.Language.TypeName, System.Exception ByRef, System.Reflection.Assembly[], System.Management.Automation.Language.TypeResolutionState)
   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])
   at System.Management.Automation.Language.SymbolResolver.VisitTypeExpression(System.Management.Automation.Language.TypeExpressionAst)
   at System.Management.Automation.Language.SymbolResolver.VisitTypeName(System.Management.Automation.Language.TypeName, Int32, Boolean)System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at System.Management.Automation.Runspaces.LocalRunspace.StopOrDisconnectAllJobs()
   at System.Management.Automation.Runspaces.LocalRunspace.DoCloseHelper()
   at System.Management.Automation.Runspaces.RunspaceBase.CoreClose(Boolean syncCall)
   at System.Management.Automation.Runspaces.LocalRunspace.Close()
   at Microsoft.PowerShell.ConsoleHost.DoRunspaceLoop(String initialCommand, Boolean skipProfiles, Collection`1 initialCommandArgs, Boolean staMode, String configurationName, String configurationFilePath)
   at Microsoft.PowerShell.ConsoleHost.Run(CommandLineParameterParser cpp, Boolean isPrestartWarned)
   at Microsoft.PowerShell.ConsoleHost.Start(String bannerText, String helpText, Boolean issProvidedExternally)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)
   at System.Management.Automation.Language.TypeExpressionAst.InternalVisit(System.Management.Automation.Language.AstVisitor)
   at System.Management.Automation.Language.SymbolResolver.VisitTypeExpression(System.Management.Automation.Language.TypeExpressionAst)
   at System.Management.Automation.Language.InvokeMemberExpressionAst.InternalVisitChildren(System.Management.Automation.Language.AstVisitor)
   at System.Management.Automation.Language.TypeExpressionAst.InternalVisit(System.Management.Automation.Language.AstVisitor)
   at System.Management.Automation.Language.InvokeMemberExpressionAst.InternalVisit(System.Management.Automation.Languag







Stack overflow.

Stack overflow.

Fatal error. Stack overflow.
Stack overflow.
Stack overflow.
Fatal error.    at System.Management.Automation.Language.MemberExpressionAst.InternalVisit(System.Management.Automation.Language.AstVisitor)
An error occurred while creating the pipeline.
   at System.Management.Automation.Language.CommandExpressionAst.InternalVisit(System.Management.Automation.Language.AstVisitor)
   at System.Management.Automation.Language.CommandExpressionAst.InternalVisit(System.Management.Automation.Language.AstVisitor)Internal CLR error. (0x80131506)Exception of type 'System.OutOfMemoryException' was thrown.
Exception of type 'System.OutOfMemoryException' was thrown.
Internal CLR error. (0x80131506)An error occurred while creating the pipeline.

   at System.Management.Automation.Language.AssignmentStatementAst.InternalVisit(System.Management.Automation.Language.AstVisitor)

Exception of type 'System.OutOfMemoryException' was thrown.
Exception of type 'System.OutOfMemoryException' was thrown.


An error occurred while creating the pipeline.
An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
   at System.Management.Automation.Language.AssignmentStatementAst.InternalVisit(System.Management.Automation.Language.AstVisitor)   at System.Management.Automation.Language.StatementBlockAst.InternalVisit(System.Management.Automation.Language.AstVisitor, System.Collections.ObjectModel.ReadOnlyCollection`1<System.Management.Automation.Language.TrapStatementAst>, System.Collections.ObjectModel.ReadOnlyCollection`1<System.Management.Automation.Language.StatementAst>, System.Management.Automation.Language.AstVisitAction)
An error occurred while creating the pipeline.
An error occurred while creating the pipeline.
An error occurred while creating the pipeline.

   at System.Net.Http.HttpConnectionSettings.CloneAndNormalize()

   at System.Management.Automation.Language.StatementBlockAst.InternalVisit(System.Management.Automation.Language.AstVisitor, System.Collections.ObjectModel.ReadOnlyCollection`1<System.Management.Automation.Language.TrapStatementAst>, System.Collections.ObjectModel.ReadOnlyCollection`1<System.Management.Automation.Language.StatementAst>, System.Management.Automation.Language.AstVisitAction)

   at System.Management.Automation.Language.StatementBlockAst.InternalVisit(System.Management.Automation.Language.AstVisitor)
   at System.Net.Http.SocketsHttpHandler.SetupHandlerChain()   at System.Management.Automation.Language.IfStatementAst.InternalVisit(System.Management.Automation.Language.AstVisitor)

   at System.Management.Automation.Language.StatementBlockAst.InternalVisit(System.Management.Automation.Language.AstVisitor, System.Collections.ObjectModel.ReadOnlyCollection`1<System.Management.Automation.Language.TrapStatementAst>, System.Collections.ObjectModel.ReadOnlyCollection`1<System.Management.Automation.Language.StatementAst>, System.Management.Automation.Language.AstVisitAction)
   at System.Management.Automation.Language.NamedBlockAst.InternalVisit(System.Management.Automation.Language.AstVisitor)
   at System.Net.Http.SocketsHttpHandler.SendAsync(System.Net.Http.HttpRequestMessage, System.Threading.CancellationToken)
   at System.Management.Automation.Language.StatementBlockAst.InternalVisit(System.Management.Automation.Language.AstVisitor)
   at Microsoft.ApplicationInsights.Channel.RedirectHttpHandler+<SendAsync>d__4.MoveNext()
   at System.Management.Automation.Language.ScriptBlockAst.InternalVisit(System.Management.Automation.Language.AstVisitor)
   at System.Management.Automation.Language.IfStatementAst.InternalVisit(System.Management.Automation.Language.AstVisitor)
   at System.Runtime.CompilerServices.AsyncMethodBuilderCore.Start[[Microsoft.ApplicationInsights.Channel.RedirectHttpHandler+<SendAsync>d__4, Microsoft.ApplicationInsights, Version=2.22.0.997, Culture=neutral, PublicKeyToken=31bf3856ad364e35]](<SendAsync>d__4 ByRef)
   at System.Management.Automation.Language.Ast.Visit(System.Management.Automation.Language.AstVisitor)   at System.Management.Automation.Language.StatementBlockAst.InternalVisit(System.Management.Automation.Language.AstVisitor, System.Collections.ObjectModel.ReadOnlyCollection`1<System.Management.Automation.Language.TrapStatementAst>, System.Collections.ObjectModel.ReadOnlyCollection`1<System.Management.Automation.Language.StatementAst>, System.Management.Automation.Language.AstVisitAction)
   at System.Runtime.CompilerServices.AsyncTaskMethodBuilder`1[[System.__Canon, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e]].Start[[Microsoft.ApplicationInsights.Channel.RedirectHttpHandler+<SendAsync>d__4, Microsoft.ApplicationInsights, Version=2.22.0.997, Culture=neutral, PublicKeyToken=31bf3856ad364e35]](<SendAsync>d__4 ByRef)
   at System.Management.Automation.Language.SymbolResolver.ResolveSymbols(System.Management.Automation.Language.Parser, System.Management.Automation.Language.ScriptBlockAst)
   at Microsoft.ApplicationInsights.Channel.RedirectHttpHandler.SendAsync(System.Net.Http.HttpRequestMessage, System.Threading.CancellationToken)   at System.Management.Automation.Language.ScriptBlockAst.PerformPostParseChecks(System.Management.Automation.Language.Parser)

   at System.Management.Automation.Language.Parser.ParseTask(System.String, System.String, System.Collections.Generic.List`1<System.Management.Automation.Language.Token>, Boolean, System.Management.Automation.Language.ParseMode)

   at System.Net.Http.HttpClient+<<SendAsync>g__Core|83_0>d.MoveNext()   at System.Management.Automation.Language.NamedBlockAst.InternalVisit(System.Management.Automation.Language.AstVisitor)

   at System.Management.Automation.Language.ScriptBlockAst.InternalVisit(System.Management.Automation.Language.AstVisitor)
   at System.Management.Automation.Language.Parser.Parse(System.String, System.String, System.Collections.Generic.List`1<System.Management.Automation.Language.Token>, System.Management.Automation.Language.ParseError[] ByRef, System.Management.Automation.Language.ParseMode)
   at System.Runtime.CompilerServices.AsyncMethodBuilderCore.Start[[System.Net.Http.HttpClient+<<SendAsync>g__Core|83_0>d, System.Net.Http, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a]](<<SendAsync>g__Core|83_0>d ByRef)   at System.Management.Automation.Language.FunctionDefinitionAst.InternalVisit(System.Management.Automation.Language.AstVisitor)

   at System.Management.Automation.Language.StatementBlockAst.InternalVisit(System.Management.Automation.Language.AstVisitor, System.Collections.ObjectModel.ReadOnlyCollection`1<System.Management.Automation.Language.TrapStatementAst>, System.Collections.ObjectModel.ReadOnlyCollection`1<System.Management.Automation.Language.StatementAst>, System.Management.Automation.Language.AstVisitAction)   at System.Management.Automation.CompiledScriptBlockData.DelayParseScriptText()
   at System.Runtime.CompilerServices.AsyncTaskMethodBuilder`1[[System.__Canon, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e]].Start[[System.Net.Http.HttpClient+<<SendAsync>g__Core|83_0>d, System.Net.Http, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a]](<<SendAsync>g__Core|83_0>d ByRef)
   at System.Management.Automation.ScriptBlock.get_HasBeginBlock()

   at System.Management.Automation.ScriptBlock.GetCodeToInvoke(Boolean ByRef, System.Management.Automation.ScriptBlockClauseToInvoke)
   at System.Management.Automation.Language.NamedBlockAst.InternalVisit(System.Management.Automation.Language.AstVisitor)
   at System.Net.Http.HttpClient.<SendAsync>g__Core|83_0(System.Net.Http.HttpRequestMessage, System.Net.Http.HttpCompletionOption, System.Threading.CancellationTokenSource, Boolean, System.Threading.CancellationTokenSource, System.Threading.CancellationToken)   at System.Management.Automation.Language.ScriptBlockAst.InternalVisit(System.Management.Automation.Language.AstVisitor)

   at System.Management.Automation.Language.Ast.Visit(System.Management.Automation.Language.AstVisitor)
   at System.Management.Automation.ScriptBlock.InvokeWithPipeImpl(System.Management.Automation.ScriptBlockClauseToInvoke, Boolean, System.Collections.Generic.Dictionary`2<System.String,System.Management.Automation.ScriptBlock>, System.Collections.Generic.List`1<System.Management.Automation.PSVariable>, ErrorHandlingBehavior, System.Object, System.Object, System.Object, System.Management.Automation.Internal.Pipe, System.Management.Automation.InvocationInfo, System.Object[])
   at System.Net.Http.HttpClient.SendAsync(System.Net.Http.HttpRequestMessage, System.Net.Http.HttpCompletionOption, System.Threading.CancellationToken)   at System.Management.Automation.ScriptBlock.InvokeWithPipe(Boolean, ErrorHandlingBehavior, System.Object, System.Object, System.Object, System.Management.Automation.Internal.Pipe, System.Management.Automation.InvocationInfo, Boolean, System.Collections.Generic.List`1<System.Management.Automation.PSVariable>, System.Collections.Generic.Dictionary`2<System.String,System.Management.Automation.ScriptBlock>, System.Object[])

   at System.Management.Automation.Language.SymbolResolver.ResolveSymbols(System.Management.Automation.Language.Parser, System.Management.Automation.Language.ScriptBlockAst)   at System.Management.Automation.ScriptBlock.DoInvokeReturnAsIs(Boolean, ErrorHandlingBehavior, System.Object, System.Object, System.Object, System.Object[])

   at Microsoft.ApplicationInsights.Channel.Transmission+<SendAsync>d__53.MoveNext()   at System.Management.Automation.Language.ScriptBlockAst.PerformPostParseChecks(System.Management.Automation.Language.Parser)
   at Microsoft.PowerShell.Commands.PSPropertyExpression.GetValue(System.Management.Automation.PSObject, Boolean)

   at Microsoft.PowerShell.Commands.PSPropertyExpression.GetValues(System.Management.Automation.PSObject, Boolean, Boolean)
   at System.Management.Automation.Language.Parser.ParseTask(System.String, System.String, System.Collections.Generic.List`1<System.Management.Automation.Language.Token>, Boolean, System.Management.Automation.Language.ParseMode)
   at System.Runtime.CompilerServices.AsyncMethodBuilderCore.Start[[Microsoft.ApplicationInsights.Channel.Transmission+<SendAsync>d__53, Microsoft.ApplicationInsights, Version=2.22.0.997, Culture=neutral, PublicKeyToken=31bf3856ad364e35]](<SendAsync>d__53 ByRef)   at System.Management.Automation.Language.Parser.Parse(System.String, System.String, System.Collections.Generic.List`1<System.Management.Automation.Language.Token>, System.Management.Automation.Language.ParseError[] ByRef, System.Management.Automation.Language.ParseMode)
   at Microsoft.PowerShell.Commands.Internal.Format.ComplexControlGenerator.ExecuteFormatTokenList(Microsoft.PowerShell.Commands.Internal.Format.TraversalInfo, System.Management.Automation.PSObject, System.Collections.Generic.List`1<Microsoft.PowerShell.Commands.Internal.Format.FormatToken>, System.Collections.Generic.List`1<Microsoft.PowerShell.Commands.Internal.Format.FormatValue>)

   at Microsoft.PowerShell.Commands.Internal.Format.ComplexControlGenerator.ExecuteFormatControl(Microsoft.PowerShell.Commands.Internal.Format.TraversalInfo, Microsoft.PowerShell.Commands.Internal.Format.ControlBase, System.Management.Automation.PSObject, System.Collections.Generic.List`1<Microsoft.PowerShell.Commands.Internal.Format.FormatValue>)   at System.Management.Automation.CompiledScriptBlockData.DelayParseScriptText()

   at System.Runtime.CompilerServices.AsyncTaskMethodBuilder`1[[System.__Canon, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e]].Start[[Microsoft.ApplicationInsights.Channel.Transmission+<SendAsync>d__53, Microsoft.ApplicationInsights, Version=2.22.0.997, Culture=neutral, PublicKeyToken=31bf3856ad364e35]](<SendAsync>d__53 ByRef)

   at System.Management.Automation.ScriptBlock.get_HasBeginBlock()
   at Microsoft.ApplicationInsights.Channel.Transmission.SendAsync()   at System.Management.Automation.ScriptBlock.GetCodeToInvoke(Boolean ByRef, System.Management.Automation.ScriptBlockClauseToInvoke)

   at System.Management.Automation.ScriptBlock.InvokeWithPipeImpl(System.Management.Automation.ScriptBlockClauseToInvoke, Boolean, System.Collections.Generic.Dictionary`2<System.String,System.Management.Automation.ScriptBlock>, System.Collections.Generic.List`1<System.Management.Automation.PSVariable>, ErrorHandlingBehavior, System.Object, System.Object, System.Object, System.Management.Automation.Internal.Pipe, System.Management.Automation.InvocationInfo, System.Object[])
   at Microsoft.PowerShell.Commands.Internal.Format.ComplexControlGenerator.GenerateFormatEntries(Int32, Microsoft.PowerShell.Commands.Internal.Format.ControlBase, System.Management.Automation.PSObject, System.Collections.Generic.List`1<Microsoft.PowerShell.Commands.Internal.Format.FormatValue>)
   at Microsoft.ApplicationInsights.Channel.InMemoryTransmitter.DequeueAndSend(System.TimeSpan)   at Microsoft.PowerShell.Commands.Internal.Format.ComplexViewGenerator.GenerateComplexViewEntryFromDataBaseInfo(System.Management.Automation.PSObject, Int32)

   at Microsoft.PowerShell.Commands.Internal.Format.ComplexViewGenerator.GeneratePayload(System.Management.Automation.PSObject, Int32)
Out of memory.
   at System.Management.Automation.ScriptBlock.InvokeWithPipe(Boolean, ErrorHandlingBehavior, System.Object, System.Object, System.Object, System.Management.Automation.Internal.Pipe, System.Management.Automation.InvocationInfo, Boolean, System.Collections.Generic.List`1<System.Management.Automation.PSVariable>, System.Collections.Generic.Dictionary`2<System.String,System.Management.Automation.ScriptBlock>, System.Object[])
   at Microsoft.PowerShell.Commands.Internal.Format.OutOfBandFormatViewManager.GenerateOutOfBandData(Microsoft.PowerShell.Commands.Internal.Format.TerminatingErrorContext, Microsoft.PowerShell.Commands.Internal.Format.PSPropertyExpressionFactory, Microsoft.PowerShell.Commands.Internal.Format.TypeInfoDataBase, System.Management.Automation.PSObject, Int32, Boolean, System.Collections.Generic.List`1<System.Management.Automation.ErrorRecord> ByRef)
   at Microsoft.ApplicationInsights.Channel.InMemoryTransmitter.Runner()   at Microsoft.PowerShell.Commands.Internal.Format.InnerFormatShapeCommand.ProcessOutOfBandObjectOutsideDocumentSequence(System.Management.Automation.PSObject)
   at System.Management.Automation.ScriptBlock.DoInvokeReturnAsIs(Boolean, ErrorHandlingBehavior, System.Object, System.Object, System.Object, System.Object[])
Unhandled exception.
   at Microsoft.PowerShell.Commands.Internal.Format.InnerFormatShapeCommand.ProcessObject(System.Management.Automation.PSObject)
    at System.Management.Automation.CommandProcessor.ProcessRecord()
   at System.Threading.ExecutionContext.RunInternal(System.Threading.ExecutionContext, System.Threading.ContextCallback, System.Object)   at Microsoft.PowerShell.Commands.PSPropertyExpression.GetValue(System.Management.Automation.PSObject, Boolean)   at System.Management.Automation.CommandProcessorBase.DoExecute()


   at System.Management.Automation.Internal.PipelineProcessor.Step(System.Object)
   at System.Threading.Tasks.Task.ExecuteWithThreadLocal(System.Threading.Tasks.Task ByRef, System.Threading.Thread)   at Microsoft.PowerShell.Commands.Internal.Format.OutCommandInner.ProcessRecord()

   at System.Management.Automation.CommandProcessor.ProcessRecord()
   at Microsoft.PowerShell.Commands.PSPropertyExpression.GetValues(System.Management.Automation.PSObject, Boolean, Boolean)
   at System.Management.Automation.CommandProcessorBase.DoExecute()
   at Microsoft.PowerShell.Commands.Internal.Format.ComplexControlGenerator.ExecuteFormatTokenList(Microsoft.PowerShell.Commands.Internal.Format.TraversalInfo, System.Management.Automation.PSObject, System.Collections.Generic.List`1<Microsoft.PowerShell.Commands.Internal.Format.FormatToken>, System.Collections.Generic.List`1<Microsoft.PowerShell.Commands.Internal.Format.FormatValue>)
   at System.Management.Automation.Internal.PipelineProcessor.Step(System.Object)
   at Microsoft.PowerShell.Commands.Internal.Format.ComplexControlGenerator.ExecuteFormatControl(Microsoft.PowerShell.Commands.Internal.Format.TraversalInfo, Microsoft.PowerShell.Commands.Internal.Format.ControlBase, System.Management.Automation.PSObject, System.Collections.Generic.List`1<Microsoft.PowerShell.Commands.Internal.Format.FormatValue>)
   at Microsoft.PowerShell.Commands.Internal.Format.OutputManagerInner.ProcessRecord()
   at Microsoft.PowerShell.Commands.Internal.Format.ComplexControlGenerator.GenerateFormatEntries(Int32, Microsoft.PowerShell.Commands.Internal.Format.ControlBase, System.Management.Automation.PSObject, System.Collections.Generic.List`1<Microsoft.PowerShell.Commands.Internal.Format.FormatValue>)
   at Microsoft.PowerShell.Commands.OutDefaultCommand.ProcessRecord()
   at Microsoft.PowerShell.Commands.Internal.Format.ComplexViewGenerator.GenerateComplexViewEntryFromDataBaseInfo(System.Management.Automation.PSObject, Int32)
   at System.Management.Automation.CommandProcessor.ProcessRecord()
   at Microsoft.PowerShell.Commands.Internal.Format.ComplexViewGenerator.GeneratePayload(System.Management.Automation.PSObject, Int32)
   at System.Management.Automation.CommandProcessorBase.DoExecute()
   at Microsoft.PowerShell.Commands.Internal.Format.OutOfBandFormatViewManager.GenerateOutOfBandData(Microsoft.PowerShell.Commands.Internal.Format.TerminatingErrorContext, Microsoft.PowerShell.Commands.Internal.Format.PSPropertyExpressionFactory, Microsoft.PowerShell.Commands.Internal.Format.TypeInfoDataBase, System.Management.Automation.PSObject, Int32, Boolean, System.Collections.Generic.List`1<System.Management.Automation.ErrorRecord> ByRef)
   at System.Management.Automation.ExceptionHandlingOps.ReportErrorRecord(System.Management.Automation.Language.IScriptExtent, System.Management.Automation.RuntimeException, System.Management.Automation.ExecutionContext)
   at Microsoft.PowerShell.Commands.Internal.Format.InnerFormatShapeCommand.ProcessOutOfBandObjectOutsideDocumentSequence(System.Management.Automation.PSObject)
   at System.Management.Automation.ExceptionHandlingOps.CheckActionPreference(System.Management.Automation.Language.FunctionContext, System.Exception)
   at Microsoft.PowerShell.Commands.Internal.Format.InnerFormatShapeCommand.ProcessObject(System.Management.Automation.PSObject)
   at System.Management.Automation.Interpreter.ActionCallInstruction`2[[System.__Canon, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e],[System.__Canon, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e]].Run(System.Management.Automation.Interpreter.InterpretedFrame)
   at System.Management.Automation.CommandProcessor.ProcessRecord()
   at System.Management.Automation.Interpreter.EnterTryCatchFinallyInstruction.Run(System.Management.Automation.Interpreter.InterpretedFrame)
   at System.Management.Automation.CommandProcessorBase.DoExecute()
   at System.Management.Automation.Interpreter.EnterTryCatchFinallyInstruction.Run(System.Management.Automation.Interpreter.InterpretedFrame)
   at System.Management.Automation.Internal.PipelineProcessor.Step(System.Object)
   at System.Management.Automation.Interpreter.Interpreter.Run(System.Management.Automation.Interpreter.InterpretedFrame)
   at Microsoft.PowerShell.Commands.Internal.Format.OutCommandInner.ProcessRecord()
   at System.Management.Automation.Interpreter.LightLambda.RunVoid1[[System.__Canon, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e]](System.__Canon)
   at System.Management.Automation.CommandProcessor.ProcessRecord()
   at System.Management.Automation.DlrScriptCommandProcessor.RunClause(System.Action`1<System.Management.Automation.Language.FunctionContext>, System.Object, System.Object)
   at System.Management.Automation.CommandProcessorBase.DoExecute()
   at System.Management.Automation.DlrScriptCommandProcessor.Complete()
   at System.Management.Automation.Internal.PipelineProcessor.Step(System.Object)
   at System.Management.Automation.CommandProcessorBase.DoComplete()
   at Microsoft.PowerShell.Commands.Internal.Format.OutputManagerInner.ProcessRecord()
   at System.Management.Automation.Internal.PipelineProcessor.DoCompleteCore(System.Management.Automation.CommandProcessorBase)
   at Microsoft.PowerShell.Commands.OutDefaultCommand.ProcessRecord()
   at System.Management.Automation.Internal.PipelineProcessor.SynchronousExecuteEnumerate(System.Object)
   at System.Management.Automation.CommandProcessor.ProcessRecord()
   at System.Management.Automation.Runspaces.LocalPipeline.InvokeHelper()
   at System.Management.Automation.CommandProcessorBase.DoExecute()
   at System.Management.Automation.Runspaces.LocalPipeline.InvokeThreadProc()
   at System.Management.Automation.ExceptionHandlingOps.ReportErrorRecord(System.Management.Automation.Language.IScriptExtent, System.Management.Automation.RuntimeException, System.Management.Automation.ExecutionContext)
   at System.Management.Automation.Runspaces.PipelineThread.WorkerProc()
   at System.Management.Automation.ExceptionHandlingOps.CheckActionPreference(System.Management.Automation.Language.FunctionContext, System.Exception)
   at System.Threading.ExecutionContext.RunInternal(System.Threading.ExecutionContext, System.Threading.ContextCallback, System.Object)
   at System.Management.Automation.Interpreter.ActionCallInstruction`2[[System.__Canon, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e],[System.__Canon, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e]].Run(System.Management.Automation.Interpreter.InterpretedFrame)
   at System.Management.Automation.Interpreter.EnterTryCatchFinallyInstruction.Run(System.Management.Automation.Interpreter.InterpretedFrame)
   at System.Management.Automation.Interpreter.EnterTryCatchFinallyInstruction.Run(System.Management.Automation.Interpreter.InterpretedFrame)
   at System.Management.Automation.Interpreter.Interpreter.Run(System.Management.Automation.Interpreter.InterpretedFrame)
   at System.Management.Automation.Interpreter.LightLambda.RunVoid1[[System.__Canon, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e]](System.__Canon)
   at System.Management.Automation.DlrScriptCommandProcessor.RunClause(System.Action`1<System.Management.Automation.Language.FunctionContext>, System.Object, System.Object)
   at System.Management.Automation.DlrScriptCommandProcessor.Complete()
   at System.Management.Automation.CommandProcessorBase.DoComplete()
   at System.Management.Automation.Internal.PipelineProcessor.DoCompleteCore(System.Management.Automation.CommandProcessorBase)
   at System.Management.Automation.Internal.PipelineProcessor.SynchronousExecuteEnumerate(System.Object)
   at System.Management.Automation.Runspaces.LocalPipeline.InvokeHelper()
   at System.Management.Automation.Runspaces.LocalPipeline.InvokeThreadProc()
   at System.Management.Automation.Runspaces.PipelineThread.WorkerProc()
   at System.Threading.ExecutionContext.RunInternal(System.Threading.ExecutionContext, System.Threading.ContextCallback, System.Object)
System.Runtime.InteropServices.SEHException (0x80004005): External component has thrown an exception.
   at System.Buffers.SharedArrayPool`1.Rent(Int32 minimumLength)
   at System.Net.Http.HttpConnectionPool.ScavengeHttp11ConnectionStack(HttpConnectionPool pool, ConcurrentStack`1 connections, List`1& toDispose, Int64 nowTicks, TimeSpan pooledConnectionLifetime, TimeSpan pooledConnectionIdleTimeout)
   at System.Net.Http.HttpConnectionPool.CleanCacheAndDisposeIfUnused()
   at System.Net.Http.HttpConnectionPoolManager.RemoveStalePools()
   at System.Net.Http.HttpConnectionPoolManager.<>c.<.ctor>b__11_0(Object s)
   at System.Threading.TimerQueueTimer.Fire(Boolean isThreadPool)
   at System.Threading.TimerQueue.FireNextTimers()
   at System.Threading.ThreadPoolWorkQueue.Dispatch()
   at System.Threading.PortableThreadPool.WorkerThread.WorkerThreadStart()

Internal CLR error. (0x80131506)


ResourceUnavailable: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:6
An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.Line |
An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.   6 |  pwsh .\tools\Build-Landers.ps1 -All -Root .\docs -GTM GTM-K58Z4XD -Fo …




     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Out of memory.




Out of memory.

Out of memory.
     | Program 'pwsh.exe' failed to run: Exception of type 'System.OutOfMemoryException' was thrown.At
Out of memory.
Out of memory.
     | D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:6 char:1 + pwsh
Out of memory.
     | .\tools\Build-Landers.ps1 -All -Root .\docs -GTM GTM-K58Z4XD -Fo … +
Out of memory.
Out of memory.
     | ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~.
Out of memory.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.
An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.
Fatal error. Stack overflow.
   at System.SR.Format(System.String, System.Object)
   at System.Net.Sockets.Socket+AwaitableSocketAsyncEventArgs.CreateException(System.Net.Sockets.SocketError, Boolean)
   at System.Net.Sockets.Socket+AwaitableSocketAsyncEventArgs.ThrowException(System.Net.Sockets.SocketError, System.Threading.CancellationToken)
   at System.Net.Sockets.Socket+AwaitableSocketAsyncEventArgs.System.Threading.Tasks.Sources.IValueTaskSource<System.Int32>.GetResult(Int16)
   at System.Net.Security.SslStream+<EnsureFullTlsFrameAsync>d__168`1[[System.Net.Security.AsyncReadWriteAdapter, System.Net.Security, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a]].MoveNext()
   at System.Runtime.CompilerServices.PoolingAsyncValueTaskMethodBuilder`1+StateMachineBox`1[[System.Int32, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e],[System.Net.Security.SslStream+<EnsureFullTlsFrameAsync>d__168`1[[System.Net.Security.AsyncReadWriteAdapter, System.Net.Security, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a]], System.Net.Security, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a]].ExecutionContextCallback(System.Object)
   at System.Threading.ExecutionContext.RunInternal(System.Threading.ExecutionContext, System.Threading.ContextCallback, System.Object)
   at System.Runtime.CompilerServices.PoolingAsyncValueTaskMethodBuilder`1+StateMachineBox`1[[System.Int32, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e],[System.Net.Security.SslStream+<EnsureFullTlsFrameAsync>d__168`1[[System.Net.Security.AsyncReadWriteAdapter, System.Net.Security, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a]], System.Net.Security, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a]].MoveNext()
   at System.Net.Sockets.SocketAsyncEventArgs+<>c.<.cctor>b__174_0(UInt32, UInt32, System.Threading.NativeOverlapped*)

   at System.Threading.PortableThreadPool+IOCompletionPoller+Callback.Invoke(Event)
   at System.Threading.ThreadPoolTypedWorkItemQueue`2[[System.Threading.PortableThreadPool+IOCompletionPoller+Event, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e],[System.Threading.PortableThreadPool+IOCompletionPoller+Callback, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e]].System.Threading.IThreadPoolWorkItem.Execute()An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
   at System.Threading.ThreadPoolWorkQueue.Dispatch()
Out of memory.

Stack overflow.
An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
   at System.Threading.PortableThreadPool+WorkerThread.WorkerThreadStart()Out of memory.

   at System.Threading.Tasks.Task.HandleException(System.Exception)
   at System.Threading.Tasks.Task.ExecuteWithThreadLocal(System.Threading.Tasks.Task ByRef, System.Threading.Thread)
   at Microsoft.ApplicationInsights.Metrics.DefaultAggregationPeriodCycle.FetchAndTrackMetrics()
   at Interop+Kernel32.Sleep(UInt32)
   at Microsoft.ApplicationInsights.Metrics.DefaultAggregationPeriodCycle.Run()
   at System.Threading.LowLevelLifoSemaphore.Wait(Int32, Boolean)
   at System.Threading.ExecutionContext.RunInternal(System.Threading.ExecutionContext, System.Threading.ContextCallback, System.Object)
   at System.Threading.PortableThreadPool+WorkerThread.WorkerThreadStart()
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.
Process terminated. Exception of type 'System.OutOfMemoryException' was thrown.
   at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)
   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)
   at System.Environment.FailFast(System.String, System.Exception)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)
   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])
System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at System.Management.Automation.Internal.ObjectStream.get_ObjectWriter()
   at System.Management.Automation.Runspaces.LocalPipeline.InitStreams()
   at System.Management.Automation.Runspaces.LocalRunspace.CoreCreatePipeline(String command, Boolean addToHistory, Boolean isNested)
   at Microsoft.PowerShell.ConsoleHost.DoRunspaceInitialization(RunspaceCreationEventArgs args)
   at Microsoft.PowerShell.ConsoleHost.CreateRunspace(RunspaceCreationEventArgs runspaceCreationArgs)
   at Microsoft.PowerShell.ConsoleHost.DoRunspaceLoop(String initialCommand, Boolean skipProfiles, Collection`1 initialCommandArgs, Boolean staMode, String configurationName, String configurationFilePath)
   at Microsoft.PowerShell.ConsoleHost.Run(CommandLineParameterParser cpp, Boolean isPrestartWarned)
   at Microsoft.PowerShell.ConsoleHost.Start(String bannerText, String helpText, Boolean issProvidedExternally)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)
An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.

Stack overflow.
Process terminated. An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Exception of type 'System.OutOfMemoryException' was thrown.
   at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)
   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)
   at System.Environment.FailFast(System.String, System.Exception)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)
   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])
System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at System.Management.Automation.Runspaces.PipelineBase.Initialize(Runspace runspace, String command, Boolean addToHistory, Boolean isNested)
   at System.Management.Automation.Runspaces.PipelineBase..ctor(Runspace runspace, String command, Boolean addToHistory, Boolean isNested)
   at System.Management.Automation.Runspaces.LocalRunspace.CoreCreatePipeline(String command, Boolean addToHistory, Boolean isNested)
   at Microsoft.PowerShell.ConsoleHost.DoRunspaceInitialization(RunspaceCreationEventArgs args)
   at Microsoft.PowerShell.ConsoleHost.CreateRunspace(RunspaceCreationEventArgs runspaceCreationArgs)
   at Microsoft.PowerShell.ConsoleHost.DoRunspaceLoop(String initialCommand, Boolean skipProfiles, Collection`1 initialCommandArgs, Boolean staMode, String configurationName, String configurationFilePath)
   at Microsoft.PowerShell.ConsoleHost.Run(CommandLineParameterParser cpp, Boolean isPrestartWarned)
   at Microsoft.PowerShell.ConsoleHost.Start(String bannerText, String helpText, Boolean issProvidedExternally)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)An error occurred while creating the pipeline.
Out of memory.
   at Interop+Kernel32.Sleep(UInt32)
   at System.Threading.LowLevelSpinWaiter.Wait(Int32, Int32, Boolean)
   at System.Threading.LowLevelLifoSemaphore.Wait(Int32, Boolean)
   at System.Threading.PortableThreadPool+WorkerThread.WorkerThreadStart()
Exception of type 'System.OutOfMemoryException' was thrown.

   at Microsoft.ApplicationInsights.Extensibility.Implementation.JsonSerializationWriter.WriteProperty(System.String, System.Collections.Generic.IDictionary`2<System.String,Double>)
   at Microsoft.ApplicationInsights.Extensibility.Implementation.External.EventData.Serialize(Microsoft.ApplicationInsights.Extensibility.ISerializationWriter)
   at Microsoft.ApplicationInsights.Extensibility.Implementation.JsonSerializer.SerializeHelper(Microsoft.ApplicationInsights.Channel.ITelemetry, Microsoft.ApplicationInsights.Extensibility.Implementation.JsonSerializationWriter, System.String, System.String)
   at Microsoft.ApplicationInsights.Extensibility.Implementation.JsonSerializer.SerializeTelemetryItem(Microsoft.ApplicationInsights.Channel.ITelemetry, Microsoft.ApplicationInsights.Extensibility.Implementation.JsonSerializationWriter)
   at Microsoft.ApplicationInsights.Extensibility.Implementation.JsonSerializer.SerializeToStream(System.Collections.Generic.IEnumerable`1<Microsoft.ApplicationInsights.Channel.ITelemetry>, System.IO.TextWriter)
   at Microsoft.ApplicationInsights.Extensibility.Implementation.JsonSerializer.Serialize(System.Collections.Generic.IEnumerable`1<Microsoft.ApplicationInsights.Channel.ITelemetry>, Boolean)

   at Microsoft.ApplicationInsights.Channel.InMemoryTransmitter.Send(System.Collections.Generic.IEnumerable`1<Microsoft.ApplicationInsights.Channel.ITelemetry>, System.TimeSpan)

Process terminated. Exception of type 'System.OutOfMemoryException' was thrown.
   at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)
   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)
   at System.Environment.FailFast(System.String, System.Exception)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)
   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])
System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at System.Text.BaseCodePageEncoding..ctor(Int32 codepage, Int32 dataCodePage)
   at System.Text.CodePagesEncodingProvider.GetEncoding(Int32 codepage)
   at System.Text.CodePagesEncodingProvider.GetEncoding(Int32 codepage)
   at System.Text.EncodingProvider.GetEncodingFromProvider(Int32 codepage)
   at System.Text.Encoding.GetEncoding(Int32 codepage)
   at System.Text.EncodingHelper.GetSupportedConsoleEncoding(Int32 codepage)
   at System.Console.get_OutputEncoding()
   at System.ConsolePal.OpenStandardError()
   at System.Console.<get_Error>g__EnsureInitialized|28_0()
   at Microsoft.PowerShell.ConsoleHost.ReportExceptionFallback(Exception e, String header)
   at Microsoft.PowerShell.ConsoleHost.ReportException(Exception e, Executor exec)
   at Microsoft.PowerShell.ConsoleHost.DoRunspaceInitialization(RunspaceCreationEventArgs args)
   at Microsoft.PowerShell.ConsoleHost.CreateRunspace(RunspaceCreationEventArgs runspaceCreationArgs)
   at Microsoft.PowerShell.ConsoleHost.DoRunspaceLoop(String initialCommand, Boolean skipProfiles, Collection`1 initialCommandArgs, Boolean staMode, String configurationName, String configurationFilePath)
   at Microsoft.PowerShell.ConsoleHost.Run(CommandLineParameterParser cpp, Boolean isPrestartWarned)
   at Microsoft.PowerShell.ConsoleHost.Start(String bannerText, String helpText, Boolean issProvidedExternally)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)

Process terminated. Exception of type 'System.OutOfMemoryException' was thrown.
   at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)
Exception of type 'System.OutOfMemoryException' was thrown.   at System.Collections.Generic.List`1[[System.__Canon, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e]]..cctor()
   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)

   at System.Environment.FailFast(System.String, System.Exception)
   at System.Collections.Generic.List`1[[System.__Canon, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e]]..ctor()
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)
   at System.Net.Http.HttpConnectionPool.ScavengeHttp11ConnectionStack(System.Net.Http.HttpConnectionPool, System.Collections.Concurrent.ConcurrentStack`1<System.Net.Http.HttpConnection>, System.Collections.Generic.List`1<System.Net.Http.HttpConnectionBase> ByRef, Int64, System.TimeSpan, System.TimeSpan)
   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])
   at System.Net.Http.HttpConnectionPool.CleanCacheAndDisposeIfUnused()
System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at System.Array.Empty[T]()
   at System.Collections.Generic.Stack`1..ctor()
   at System.Management.Automation.Runspaces.PipelineStopper..ctor(LocalPipeline localPipeline)
   at System.Management.Automation.Runspaces.LocalRunspace.CoreCreatePipeline(String command, Boolean addToHistory, Boolean isNested)
   at Microsoft.PowerShell.ConsoleHost.DoRunspaceInitialization(RunspaceCreationEventArgs args)
   at Microsoft.PowerShell.ConsoleHost.CreateRunspace(RunspaceCreationEventArgs runspaceCreationArgs)
   at Microsoft.PowerShell.ConsoleHost.DoRunspaceLoop(String initialCommand, Boolean skipProfiles, Collection`1 initialCommandArgs, Boolean staMode, String configurationName, String configurationFilePath)
   at Microsoft.PowerShell.ConsoleHost.Run(CommandLineParameterParser cpp, Boolean isPrestartWarned)
   at Microsoft.PowerShell.ConsoleHost.Start(String bannerText, String helpText, Boolean issProvidedExternally)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)   at System.Net.Http.HttpConnectionPoolManager.RemoveStalePools()
   at System.Net.Http.HttpConnectionPoolManager+<>c.<.ctor>b__11_0(System.Object)
   at System.Threading.TimerQueueTimer.Fire(Boolean)
   at System.Threading.TimerQueue.FireNextTimers()
   at System.Threading.ThreadPoolWorkQueue.Dispatch()
   at System.Threading.PortableThreadPool+WorkerThread.WorkerThreadStart()
   at Microsoft.ApplicationInsights.Channel.InMemoryTransmitter.DequeueAndSend(System.TimeSpan)
   at Microsoft.ApplicationInsights.Channel.InMemoryTransmitter.Runner()
   at System.Threading.ExecutionContext.RunInternal(System.Threading.ExecutionContext, System.Threading.ContextCallback, System.Object)
   at System.Threading.Tasks.Task.ExecuteWithThreadLocal(System.Threading.Tasks.Task ByRef, System.Threading.Thread)
Process terminated. Exception of type 'System.OutOfMemoryException' was thrown.
   at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)
   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)
   at System.Environment.FailFast(System.String, System.Exception)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)
   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])
System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at Microsoft.PowerShell.ConsoleHost.ReportExceptionFallback(Exception e, String header)
   at Microsoft.PowerShell.ConsoleHost.ReportException(Exception e, Executor exec)
   at Microsoft.PowerShell.ConsoleHost.DoRunspaceInitialization(RunspaceCreationEventArgs args)
   at Microsoft.PowerShell.ConsoleHost.CreateRunspace(RunspaceCreationEventArgs runspaceCreationArgs)
   at Microsoft.PowerShell.ConsoleHost.DoRunspaceLoop(String initialCommand, Boolean skipProfiles, Collection`1 initialCommandArgs, Boolean staMode, String configurationName, String configurationFilePath)
   at Microsoft.PowerShell.ConsoleHost.Run(CommandLineParameterParser cpp, Boolean isPrestartWarned)
   at Microsoft.PowerShell.ConsoleHost.Start(String bannerText, String helpText, Boolean issProvidedExternally)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)   at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)   at System.Collections.Generic.List`1[[System.__Canon, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e]].System.Collections.Generic.IEnumerable<T>.GetEnumerator()   at System.Threading.Tasks.ContinueWithTaskContinuation.Run(System.Threading.Tasks.Task, Boolean)Process terminated. Exception of type 'System.OutOfMemoryException' was thrown.
   at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)
   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)
   at System.Environment.FailFast(System.String, System.Exception)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)
   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])
System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at Microsoft.PowerShell.ConsoleHost.ReportExceptionFallback(Exception e, String header)
   at Microsoft.PowerShell.ConsoleHost.ReportException(Exception e, Executor exec)
   at Microsoft.PowerShell.ConsoleHost.DoRunspaceInitialization(RunspaceCreationEventArgs args)
   at Microsoft.PowerShell.ConsoleHost.CreateRunspace(RunspaceCreationEventArgs runspaceCreationArgs)
   at Microsoft.PowerShell.ConsoleHost.DoRunspaceLoop(String initialCommand, Boolean skipProfiles, Collection`1 initialCommandArgs, Boolean staMode, String configurationName, String configurationFilePath)
   at Microsoft.PowerShell.ConsoleHost.Run(CommandLineParameterParser cpp, Boolean isPrestartWarned)
   at Microsoft.PowerShell.ConsoleHost.Start(String bannerText, String helpText, Boolean issProvidedExternally)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m

Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.

   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)   at Microsoft.ApplicationInsights.Metrics.MetricManager.TrackMetricAggregates(Microsoft.ApplicationInsights.Metrics.Extensibility.AggregationPeriodSummary, Boolean)   at System.Threading.Tasks.Task.RunContinuations(System.Object)
   at System.Threading.Tasks.Task.TrySetResult()
   at System.Threading.Tasks.Task+DelayPromise.CompleteTimedOut()
   at System.Threading.TimerQueueTimer.Fire(Boolean)
   at System.Threading.TimerQueue.FireNextTimers()
   at System.Threading.ThreadPoolWorkQueue.Dispatch()
   at System.Threading.PortableThreadPool+WorkerThread.WorkerThreadStart()
Could not load type 'System.Dynamic.UnaryOperationBinder' from assembly 'System.Linq.Expressions, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a'.

←[31;1mParentContainsErrorRecordException: ←[31;1mAn error occurred while creating the pipeline.←[0m
The process cannot access the file 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by another process.
An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.   at System.Environment.FailFast(System.String, System.Exception)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)
   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])
System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at System.Management.Automation.Runspaces.PipelineStopper..ctor(LocalPipeline localPipeline)
   at System.Management.Automation.Runspaces.LocalRunspace.CoreCreatePipeline(String command, Boolean addToHistory, Boolean isNested)
   at Microsoft.PowerShell.ConsoleHost.DoRunspaceInitialization(RunspaceCreationEventArgs args)
   at Microsoft.PowerShell.ConsoleHost.CreateRunspace(RunspaceCreationEventArgs runspaceCreationArgs)
   at Microsoft.PowerShell.ConsoleHost.DoRunspaceLoop(String initialCommand, Boolean skipProfiles, Collection`1 initialCommandArgs, Boolean staMode, String configurationName, String configurationFilePath)
   at Microsoft.PowerShell.ConsoleHost.Run(CommandLineParameterParser cpp, Boolean isPrestartWarned)
   at Microsoft.PowerShell.ConsoleHost.Start(String bannerText, String helpText, Boolean issProvidedExternally)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.

←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
format-default: Exception of type 'System.OutOfMemoryException' was thrown.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
     | another process.
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
   at System.Threading.ExecutionContext.RunFromThreadPoolDispatchLoop(System.Threading.Thread, System.Threading.ExecutionContext, System.Threading.ContextCallback, System.Object)
     | another process.
   at System.Threading.Tasks.Task.ExecuteWithThreadLocal(System.Threading.Tasks.Task ByRef, System.Threading.Thread)
Exception of type 'System.OutOfMemoryException' was thrown.
   at System.Threading.ThreadPoolWorkQueue.Dispatch()

   at System.Threading.PortableThreadPool+WorkerThread.WorkerThreadStart()
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
format-default: Exception of type 'System.OutOfMemoryException' was thrown.
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
format-default: Exception of type 'System.OutOfMemoryException' was thrown.
format-default: Exception of type 'System.OutOfMemoryException' was thrown.
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1mNew-Item: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:2←[0m
←[31;1mParentContainsErrorRecordException: ←[31;1mAn error occurred while creating the pipeline.←[0m
format-default: Exception of type 'System.OutOfMemoryException' was thrown.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
←[31;1mParentContainsErrorRecordException: ←[31;1mAn error occurred while creating the pipeline.←[0m
←[31;1mformat-default: ←[31;1mException of type 'System.OutOfMemoryException' was thrown.←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1mParentContainsErrorRecordException: ←[31;1mAn error occurred while creating the pipeline.←[0m
←[31;1mformat-default: ←[31;1mException of type 'System.OutOfMemoryException' was thrown.←[0m
←[31;1mParentContainsErrorRecordException: ←[31;1mAn error occurred while creating the pipeline.←[0m
←[31;1mformat-default: ←[31;1mException of type 'System.OutOfMemoryException' was thrown.←[0m
←[31;1mSecurityError: ←[31;1mAuthorizationManager check failed.←[0m
←[31;1mSecurityError: ←[31;1mAuthorizationManager check failed.←[0m
The type initializer for 'System.Management.Automation.Internal.ValueStringDecorated' threw an exception.

←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m   2 | ←[0m ←[36;1mNew-Item←[0m -ItemType Directory -Path .\tools -Force | Out-Null←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe 'New-Item' command was found in the module 'Microsoft.PowerShell.Management', but the module could not be←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1mloaded due to the following error: [Exception of type 'System.OutOfMemoryException' was thrown.] For more←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1minformation, run 'Import-Module Microsoft.PowerShell.Management'.←[0m
←[31;1mformat-default: ←[31;1mException of type 'System.OutOfMemoryException' was thrown.←[0m
←[31;1mformat-default: ←[31;1mException of type 'System.OutOfMemoryException' was thrown.←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1mformat-default: ←[31;1mException of type 'System.OutOfMemoryException' was thrown.←[0m
←[31;1m←[0m←[36;1mLine |←[0m

←[31;1mParentContainsErrorRecordException: ←[31;1mAn error occurred while creating the pipeline.←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
Out of memory.
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1m←[0m←[36;1mLine |←[0m


Out of memory.
Out of memory.
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
Out of memory.
←[31;1mParentContainsErrorRecordException: ←[31;1mAn error occurred while creating the pipeline.←[0m
←[31;1mParentContainsErrorRecordException: ←[31;1mAn error occurred while creating the pipeline.←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
     | another process.
Fatal error. Out of memory.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.
Process terminated. Exception of type 'System.OutOfMemoryException' was thrown.
   at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)
   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)
   at System.Environment.FailFast(System.String, System.Exception)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)
   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])
System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at System.Management.Automation.Runspaces.LocalRunspace.DoCloseHelper()
   at System.Management.Automation.Runspaces.RunspaceBase.CoreClose(Boolean syncCall)
   at System.Management.Automation.Runspaces.LocalRunspace.Close()
   at Microsoft.PowerShell.ConsoleHost.DoRunspaceLoop(String initialCommand, Boolean skipProfiles, Collection`1 initialCommandArgs, Boolean staMode, String configurationName, String configurationFilePath)
   at Microsoft.PowerShell.ConsoleHost.Run(CommandLineParameterParser cpp, Boolean isPrestartWarned)
   at Microsoft.PowerShell.ConsoleHost.Start(String bannerText, String helpText, Boolean issProvidedExternally)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)Out of memory.
Failed to create RW mapping for RX memory. This can be caused by insufficient memory or hitting the limit of memory mappings on Linux (vm.map_max_count).Unhandled exception.
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
An error occurred while creating the pipeline.
←[31;1m←[0m←[36;1mLine |←[0m
   at System.Management.Automation.Language.Ast.SetParents[[System.__Canon, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e],[System.__Canon, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e]](System.Collections.ObjectModel.ReadOnlyCollection`1<System.Tuple`2<System.__Canon,System.__Canon>>)←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m

←[31;1mNew-Item: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:2←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
An error occurred while creating the pipeline.
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
   at System.Management.Automation.Language.Parser.HashExpressionRule(System.Management.Automation.Language.Token, Boolean)
Line |
   at System.Management.Automation.Language.Parser.PrimaryExpressionRule(Boolean)
←[31;1m←[0m←[36;1m←[36;1m   2 | ←[0m ←[36;1mNew-Item←[0m -ItemType Directory -Path .\tools -Force | Out-Null←[0m
   at System.Management.Automation.Language.Parser.UnaryExpressionRule(Boolean)
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~←[0m
   at System.Management.Automation.Language.Parser.ArrayLiteralRule(Boolean)←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe 'New-Item' command was found in the module 'Microsoft.PowerShell.Management', but the module could not be←[0m

   at System.Management.Automation.Language.Parser.BinaryExpressionRule(Boolean)←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1mloaded due to the following error: [Exception of type 'System.OutOfMemoryException' was thrown.] For more←[0m

   at System.Management.Automation.Language.Parser.ExpressionRule(Boolean)←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1minformation, run 'Import-Module Microsoft.PowerShell.Management'.←[0m

   at System.Management.Automation.Language.Parser.PipelineChainRule()
   at System.Management.Automation.Language.Parser.StatementRule()
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1'←[0m
   at System.Management.Automation.Language.Parser.StatementListRule(System.Collections.Generic.List`1<System.Management.Automation.Language.StatementAst>, System.Collections.Generic.List`1<System.Management.Automation.Language.TrapStatementAst>)
   at System.Management.Automation.Language.Parser.ScriptBlockBodyRule(System.Management.Automation.Language.Token, System.Collections.Generic.List`1<System.Management.Automation.Language.UsingStatementAst>, System.Management.Automation.Language.ParamBlockAst, Boolean, System.Management.Automation.Language.StatementAst)
   at System.Management.Automation.Language.Parser.ScriptBlockRule(System.Management.Automation.Language.Token, Boolean, System.Management.Automation.Language.StatementAst)
   at System.Management.Automation.Language.Parser.ParseTask(System.String, System.String, System.Collections.Generic.List`1<System.Management.Automation.Language.Token>, Boolean, System.Management.Automation.Language.ParseMode)
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1mbecause it is being used by another process.←[0m
   at System.Management.Automation.Language.Parser.Parse(System.String, System.String, System.Collections.Generic.List`1<System.Management.Automation.Language.Token>, System.Management.Automation.Language.ParseError[] ByRef, System.Management.Automation.Language.ParseMode)
   at System.Management.Automation.ScriptBlock.Create(System.Management.Automation.Language.Parser, System.String, System.String)
   at System.Management.Automation.ExternalScriptInfo.ParseScriptContents(System.Management.Automation.Language.Parser, System.String, System.String, System.Nullable`1<System.Management.Automation.PSLanguageMode>)
   at System.Management.Automation.ExternalScriptInfo.get_ScriptBlock()
   at Microsoft.PowerShell.Commands.ModuleCmdletBase.LoadModuleManifestData(System.Management.Automation.ExternalScriptInfo, System.String[], ManifestProcessingFlags, Boolean ByRef)
   at Microsoft.PowerShell.Commands.ModuleCmdletBase.LoadModuleManifestData(System.Management.Automation.ExternalScriptInfo, ManifestProcessingFlags, System.Collections.Hashtable ByRef, System.Collections.Hashtable ByRef, Boolean ByRef)
   at Microsoft.PowerShell.Commands.ModuleCmdletBase.LoadModule(System.Management.Automation.PSModuleInfo, System.String, System.String, System.String, System.Management.Automation.SessionState, System.Object, ImportModuleOptions ByRef, ManifestProcessingFlags, Boolean ByRef, Boolean ByRef)
   at Microsoft.PowerShell.Commands.ImportModuleCommand.ImportModule_LocallyViaName(ImportModuleOptions, System.String)
   at Microsoft.PowerShell.Commands.ImportModuleCommand.ImportModule_LocallyViaName_WithTelemetry(ImportModuleOptions, System.String)
   at Microsoft.PowerShell.Commands.ImportModuleCommand.ProcessRecord()
   at System.Management.Automation.CommandProcessor.ProcessRecord()
   at System.Management.Automation.CommandProcessorBase.DoExecute()
   at System.Management.Automation.Internal.PipelineProcessor.SynchronousExecuteEnumerate(System.Object)
   at System.Management.Automation.Runspaces.LocalPipeline.InvokeHelper()
   at System.Management.Automation.Runspaces.LocalPipeline.InvokeThreadProc()
   at System.Management.Automation.Runspaces.LocalPipeline.StartPipelineExecution()
   at System.Management.Automation.Runspaces.PipelineBase.CoreInvoke(System.Collections.IEnumerable, Boolean)
   at System.Management.Automation.Runspaces.PipelineBase.Invoke(System.Collections.IEnumerable)
   at System.Management.Automation.PowerShell+Worker.ConstructPipelineAndDoWork(System.Management.Automation.Runspaces.Runspace, Boolean)
   at System.Management.Automation.PowerShell.CoreInvokeHelper[[System.__Canon, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e],[System.__Canon, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e]](System.Management.Automation.PSDataCollection`1<System.__Canon>, System.Management.Automation.PSDataCollection`1<System.__Canon>, System.Management.Automation.PSInvocationSettings)
   at System.Management.Automation.PowerShell.CoreInvoke[[System.__Canon, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e],[System.__Canon, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e]](System.Management.Automation.PSDataCollection`1<System.__Canon>, System.Management.Automation.PSDataCollection`1<System.__Canon>, System.Management.Automation.PSInvocationSettings)
   at System.Management.Automation.PowerShell.Invoke[[System.__Canon, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e]]()
   at System.Management.Automation.CommandDiscovery.AutoloadSpecifiedModule(System.String, System.Management.Automation.ExecutionContext, System.Management.Automation.SessionStateEntryVisibility, System.Exception ByRef)
   at System.Management.Automation.CommandDiscovery.TryModuleAutoDiscovery(System.String, System.Management.Automation.ExecutionContext, System.String, System.Management.Automation.CommandOrigin, System.Management.Automation.SearchResolutionOptions, System.Management.Automation.CommandTypes, System.Exception ByRef)
   at System.Management.Automation.CommandDiscovery.LookupCommandInfo(System.String, System.Management.Automation.CommandTypes, System.Management.Automation.SearchResolutionOptions, System.Management.Automation.CommandOrigin, System.Management.Automation.ExecutionContext)
   at System.Management.Automation.CommandDiscovery.LookupCommandProcessor(System.String, System.Management.Automation.CommandOrigin, System.Nullable`1<Boolean>)
   at System.Management.Automation.ExecutionContext.CreateCommand(System.String, Boolean)
   at System.Management.Automation.PipelineOps.AddCommand(System.Management.Automation.Internal.PipelineProcessor, System.Management.Automation.CommandParameterInternal[], System.Management.Automation.Language.CommandBaseAst, System.Management.Automation.CommandRedirection[], System.Management.Automation.ExecutionContext)
   at System.Management.Automation.PipelineOps.InvokePipeline(System.Object, Boolean, System.Management.Automation.CommandParameterInternal[][], System.Management.Automation.Language.CommandBaseAst[], System.Management.Automation.CommandRedirection[][], System.Management.Automation.Language.FunctionContext)
   at System.Management.Automation.Interpreter.ActionCallInstruction`6[[System.__Canon, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e],[System.Boolean, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e],[System.__Canon, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e],[System.__Canon, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e],[System.__Canon, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e],[System.__Canon, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e]].Run(System.Management.Automation.Interpreter.InterpretedFrame)
   at System.Management.Automation.Interpreter.EnterTryCatchFinallyInstruction.Run(System.Management.Automation.Interpreter.InterpretedFrame)
   at System.Management.Automation.Interpreter.EnterTryCatchFinallyInstruction.Run(System.Management.Automation.Interpreter.InterpretedFrame)
   at System.Management.Automation.Interpreter.Interpreter.Run(System.Management.Automation.Interpreter.InterpretedFrame)
   at System.Management.Automation.Interpreter.LightLambda.RunVoid1[[System.__Canon, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e]](System.__Canon)
   at System.Management.Automation.DlrScriptCommandProcessor.RunClause(System.Action`1<System.Management.Automation.Language.FunctionContext>, System.Object, System.Object)
   at System.Management.Automation.DlrScriptCommandProcessor.Complete()
   at System.Management.Automation.CommandProcessorBase.DoComplete()
   at System.Management.Automation.Internal.PipelineProcessor.DoCompleteCore(System.Management.Automation.CommandProcessorBase)
   at System.Management.Automation.Internal.PipelineProcessor.SynchronousExecuteEnumerate(System.Object)
   at System.Management.Automation.Runspaces.LocalPipeline.InvokeHelper()
   at System.Management.Automation.Runspaces.LocalPipeline.InvokeThreadProc()
   at System.Management.Automation.Runspaces.PipelineThread.WorkerProc()
   at System.Threading.ExecutionContext.RunInternal(System.Threading.ExecutionContext, System.Threading.ContextCallback, System.Object)
Process terminated.
Build-Landers.ps1: Exception of type 'System.OutOfMemoryException' was thrown.
Process terminated. Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3

The following error occurred while loading the extended type data file: Error in TypeData "System.Management.Automation.Job": A previous error caused all serialization settings to be ignored.
ParentContainsErrorRecordException: An error occurred while creating the pipeline.
←[31;1m←[0m←[36;1mLine |←[0m
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
Process terminated. Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
System.Management.Automation.PSInvalidOperationException: PowerShell has stopped working because of a security issue: Cannot read the configuration file: C:\Program Files\PowerShell\7\powershell.config.json
 ---> System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at System.Signature.GetSignature(Void* pCorSig, Int32 cCorSig, RuntimeFieldHandleInternal fieldHandle, IRuntimeMethodInfo methodHandle, RuntimeType declaringType)
   at System.Reflection.RuntimeMethodInfo.<get_Signature>g__LazyCreateSignature|25_0()
   at System.Reflection.RuntimeMethodInfo.FetchNonReturnParameters()
   at System.Reflection.RuntimeMethodInfo.GetParameters()
   at Newtonsoft.Json.Serialization.DefaultContractResolver.GetCallbackMethodsForType(Type type, List`1& onSerializing, List`1& onSerialized, List`1& onDeserializing, List`1& onDeserialized, List`1& onError)
   at Newtonsoft.Json.Serialization.DefaultContractResolver.ResolveCallbackMethods(JsonContract contract, Type t)
   at Newtonsoft.Json.Serialization.DefaultContractResolver.InitializeContract(JsonContract contract)
   at Newtonsoft.Json.Serialization.DefaultContractResolver.CreateLinqContract(Type objectType)
   at System.Collections.Concurrent.ConcurrentDictionary`2.GetOrAdd(TKey key, Func`2 valueFactory)
   at Newtonsoft.Json.Serialization.JsonSerializerInternalReader.Deserialize(JsonReader reader, Type objectType, Boolean checkAdditionalContent)
   at Newtonsoft.Json.JsonSerializer.DeserializeInternal(JsonReader reader, Type objectType)
   at Newtonsoft.Json.JsonSerializer.Deserialize[T](JsonReader reader)
   at System.Management.Automation.Configuration.PowerShellConfig.ReadValueFromFile[T](ConfigScope scope, String key, T defaultValue)
   --- End of inner exception stack trace ---
   at System.Management.Automation.Configuration.PowerShellConfig.ReadValueFromFile[T](ConfigScope scope, String key, T defaultValue)
   at System.Management.Automation.Configuration.PowerShellConfig.GetPowerShellPolicies(ConfigScope scope)
   at System.Collections.Concurrent.ConcurrentDictionary`2.GetOrAdd(TKey key, Func`2 valueFactory)
   at System.Management.Automation.Utils.GetPolicySettingFromConfigFile[T](ConfigScope[] preferenceOrder)
   at System.Management.Automation.Utils.GetPolicySetting[T](ConfigScope[] preferenceOrder)
   at Microsoft.PowerShell.CommandLineParameterParser.GetConfigurationNameFromGroupPolicy()
   at Microsoft.PowerShell.ConsoleHost.ParseCommandLine(String[] args)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)
   at Microsoft.PowerShell.ManagedPSEntry.Main(String[] args)Exception of type 'System.OutOfMemoryException' was thrown.Exception of type 'System.OutOfMemoryException' was thrown.Process terminated. Exception of type 'System.OutOfMemoryException' was thrown.
   at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)
   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)
   at System.Environment.FailFast(System.String, System.Exception)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)
   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])
System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at Microsoft.PowerShell.ConsoleHost.Start(String bannerText, String helpText, Boolean issProvidedExternally)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)Process terminated. Exception of type 'System.OutOfMemoryException' was thrown.
   at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)
   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)
   at System.Environment.FailFast(System.String, System.Exception)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)
   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])
System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at Microsoft.PowerShell.ConsoleHost.Start(String bannerText, String helpText, Boolean issProvidedExternally)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)
ParentContainsErrorRecordException: An error occurred while creating the pipeline.
The following error occurred while loading the extended type data file: Error in TypeData "System.Management.Automation.Job": Cannot convert note "SerializationMethod":"Cannot convert value "SpecificProperties" to type "System.Management.Automation.SerializationMethod". Error: "Exception of type 'System.OutOfMemoryException' was thrown."".
Exception of type 'System.OutOfMemoryException' was thrown.←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1mParentContainsErrorRecordException: ←[31;1mAn error occurred while creating the pipeline.←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
     | another process.
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | The process cannot access the file
Get-Clipboard: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
   3 |  … \tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clipboard) # <- o …
     | another process.
     |                                                    ~~~~~~~~~~~~~
     | Exception of type 'System.OutOfMemoryException' was thrown.
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
←[31;1mParentContainsErrorRecordException: ←[31;1mAn error occurred while creating the pipeline.←[0m

←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1mParentContainsErrorRecordException: ←[31;1mAn error occurred while creating the pipeline.←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
out-lineoutput: Exception of type 'System.OutOfMemoryException' was thrown.
ParentContainsErrorRecordException: An error occurred while creating the pipeline.
←[31;1m←[0m←[36;1mLine |←[0m
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
←[31;1mNew-Item: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:2←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   2 | ←[0m ←[36;1mNew-Item←[0m -ItemType Directory -Path .\tools -Force | Out-Null←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe 'New-Item' command was found in the module 'Microsoft.PowerShell.Management', but the module could not be←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1mloaded due to the following error: [Exception of type 'System.OutOfMemoryException' was thrown.] For more←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1minformation, run 'Import-Module Microsoft.PowerShell.Management'.←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
Line |
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
     | another process.
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
Line |
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     | The process cannot access the file
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | The process cannot access the file
     | another process.
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
ParentContainsErrorRecordException: An error occurred while creating the pipeline.
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
Line |
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Line |
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | The process cannot access the file
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     | The process cannot access the file
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
     | another process.
     | The process cannot access the file
     | another process.
     | another process.
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Line |
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
←[31;1mBuild-Landers.ps1: ←[31;1mException of type 'System.OutOfMemoryException' was thrown.←[0m
←[31;1mNew-Item: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:2←[0m
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
     |                                                  ~~~~

     | Cannot process argument transformation on parameter 'Encoding'. The type initializer for
     | 'System.Management.Automation.EncodingConversion' threw an exception.
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
Line |
Line |
Line |
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
   2 |  New-Item -ItemType Directory -Path .\tools -Force | Out-Null
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     | another process.
Line |
     |  ~~~~~~~~
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.     | The 'New-Item' command was found in the module 'Microsoft.PowerShell.Management', but the module could not be
     | The process cannot access the file
     | loaded due to the following error: [Exception of type 'System.OutOfMemoryException' was thrown.] For more
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | information, run 'Import-Module Microsoft.PowerShell.Management'.
     | another process.
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
ParentContainsErrorRecordException: An error occurred while creating the pipeline.
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
ParentContainsErrorRecordException: An error occurred while creating the pipeline.
The type initializer for 'System.Management.Automation.Internal.ValueStringDecorated' threw an exception.

Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |

   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
ParentContainsErrorRecordException: An error occurred while creating the pipeline.
ParentContainsErrorRecordException: An error occurred while creating the pipeline.
ParentContainsErrorRecordException: An error occurred while creating the pipeline.
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1mParentContainsErrorRecordException: ←[31;1mAn error occurred while creating the pipeline.←[0m
←[31;1mParentContainsErrorRecordException: ←[31;1mAn error occurred while creating the pipeline.←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
Line |
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Line |
     | The process cannot access the file
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | another process.
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
New-Item: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:2
Line |
   2 |  New-Item -ItemType Directory -Path .\tools -Force | Out-Null
     |  ~~~~~~~~
     | The 'New-Item' command was found in the module 'Microsoft.PowerShell.Management', but the module could not be
     | loaded due to the following error: [Exception of type 'System.OutOfMemoryException' was thrown.] For more
     | information, run 'Import-Module Microsoft.PowerShell.Management'.
ParentContainsErrorRecordException: An error occurred while creating the pipeline.
ParentContainsErrorRecordException: An error occurred while creating the pipeline.
out-lineoutput: Exception of type 'System.OutOfMemoryException' was thrown.
   at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)ParentContainsErrorRecordException: An error occurred while creating the pipeline.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.

Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.

ParentContainsErrorRecordException: An error occurred while creating the pipeline.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
   at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)←[31;1mSecurityError: ←[31;1mAuthorizationManager check failed.←[0m
←[31;1mNew-Item: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:2←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m


Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
     | another process.
Out of memory.
   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Processing -File 'C:\Program Files\PowerShell\7\pwsh.exe' failed because the file does not have a '.ps1' extension. Specify a valid PowerShell script file name, and then try again.
Line |
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
←[31;1m←[0m←[36;1mLine |←[0m

Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
Line |
     | another process.
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)   2 |  New-Item -ItemType Directory -Path .\tools -Force | Out-Null
Line |
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …

Line |
   at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)     |  ~~~~~~~~
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
Out of memory.
     | The term 'New-Item' is not recognized as a name of a cmdlet, function, script file, or executable program. Check
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
   at System.Environment.FailFast(System.String, System.Exception)←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1mthe spelling of the name, or if a path was included, verify that the path is correct and try again.←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m

     | The process cannot access the file
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
   at System.Environment.FailFast(System.String, System.Exception)
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
     | another process.
The shell cannot be started. A failure occurred during initialization:
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
The type initializer for 'System.Management.Automation.Language.Compiler' threw an exception.
Line |
Line |
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])
System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at System.Management.Automation.Runspaces.Runspace.get_RunspaceList()
   at System.Management.Automation.Runspaces.LocalRunspace.DoCloseHelper()
   at System.Management.Automation.Runspaces.RunspaceBase.CoreClose(Boolean syncCall)
   at System.Management.Automation.Runspaces.LocalRunspace.Close()
   at Microsoft.PowerShell.ConsoleHost.DoRunspaceLoop(String initialCommand, Boolean skipProfiles, Collection`1 initialCommandArgs, Boolean staMode, String configurationName, String configurationFilePath)
   at Microsoft.PowerShell.ConsoleHost.Run(CommandLineParameterParser cpp, Boolean isPrestartWarned)
   at Microsoft.PowerShell.ConsoleHost.Start(String bannerText, String helpText, Boolean issProvidedExternally)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m

     | The process cannot access the file
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
   at System.Environment.FailFast(System.String, System.Exception)←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m

     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at System.HexConverter.TryDecodeFromUtf16_Vector128(ReadOnlySpan`1 chars, Span`1 bytes, Int32& charsProcessed)
   at System.Reflection.AssemblyNameParser.TryParsePKT(String attributeValue, Boolean isToken, Byte[]& result)
   at System.Reflection.AssemblyNameParser.TryParse(AssemblyNameParts& result)
   at System.Reflection.AssemblyNameParser.Parse(ReadOnlySpan`1 name)
   at System.Reflection.AssemblyName..ctor(String assemblyName)
   at System.Management.Automation.Runspaces.PSSnapInHelpers.LoadPSSnapInAssembly(PSSnapInInfo psSnapInInfo)
   at System.Management.Automation.Runspaces.InitialSessionState.ImportPSSnapIn(PSSnapInInfo psSnapInInfo, PSSnapInException& warning)
   at System.Management.Automation.Runspaces.InitialSessionState.CreateDefault2()
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
     | another process.
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.

Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
Line |
Line |
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
     | another process.
     | another process.
     | another process.
   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Line |
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
Line |
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     | another process.
Line |
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     | The process cannot access the file
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | The process cannot access the file
     | another process.
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at System.Management.Automation.Runspaces.InitialSessionState..cctor()
   at System.Management.Automation.Runspaces.InitialSessionState.CreateDefault2()
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.


An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.



An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.

Out of memory.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Fatal error. Internal CLR error. (0x80131506)
Stack overflow.
GC heap initialization failed with error 0x8007000E


Process terminated. Fatal error. Fatal error. Internal CLR error. (0x80131506)
Process terminated. Exception of type 'System.OutOfMemoryException' was thrown.
Exception of type 'System.OutOfMemoryException' was thrown.
   at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)
   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)
   at System.Environment.FailFast(System.String, System.Exception)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)
   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])
System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at System.Management.Automation.Runspaces.Command..ctor(String command, Boolean isScript, Boolean useLocalScope)
   at Microsoft.PowerShell.ConsoleHost.DoRunspaceInitialization(RunspaceCreationEventArgs args)
   at Microsoft.PowerShell.ConsoleHost.CreateRunspace(RunspaceCreationEventArgs runspaceCreationArgs)
   at Microsoft.PowerShell.ConsoleHost.DoRunspaceLoop(String initialCommand, Boolean skipProfiles, Collection`1 initialCommandArgs, Boolean staMode, String configurationName, String configurationFilePath)
   at Microsoft.PowerShell.ConsoleHost.Run(CommandLineParameterParser cpp, Boolean isPrestartWarned)
   at Microsoft.PowerShell.ConsoleHost.Start(String bannerText, String helpText, Boolean issProvidedExternally)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)   at System.Net.Security.SslSessionsCache+SslCredKey.Equals(SslCredKey)
   at System.Collections.Generic.GenericEqualityComparer`1[[System.Net.Security.SslSessionsCache+SslCredKey, System.Net.Security, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a]].Equals(SslCredKey, SslCredKey)
   at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)
   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)
   at System.Environment.FailFast(System.String, System.Exception)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)
   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])
System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry..cctor()
   at Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry.SendPSCoreStartupTelemetry(String mode, Double parametersUsed)
   at Microsoft.PowerShell.ConsoleHost.Start(String bannerText, String helpText, Boolean issProvidedExternally)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)Fatal error.
Out of memory.
Out of memory.
out-lineoutput: Exception of type 'System.OutOfMemoryException' was thrown.
Failed to load System.Private.CoreLib.dll (error code 0x8007000E)
Out of memory.
Internal CLR error. (0x80131506)An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Path: C:\Program Files\PowerShell\7\System.Private.CoreLib.dll   at System.Collections.Concurrent.ConcurrentDictionary`2[[System.Net.Security.SslSessionsCache+SslCredKey, System.Net.Security, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a],[System.__Canon, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e]].TryGetValue(SslCredKey, System.__Canon ByRef)Failed to create CoreCLR, HRESULT: 0x8007000E

   at System.Net.Security.SslSessionsCache.TryCachedCredential(Byte[], System.Security.Authentication.SslProtocols, Boolean, System.Net.Security.EncryptionPolicy, Boolean, Boolean, Boolean)
   at System.Net.Security.SslStream.AcquireClientCredentials(Byte[] ByRef, Boolean)
   at System.Net.Security.SslStream.GenerateToken(System.ReadOnlySpan`1<Byte>, Int32 ByRef)
   at System.Net.Security.SslStream.NextMessage(System.ReadOnlySpan`1<Byte>, Int32 ByRef)
   at System.Net.Security.SslStream+<ForceAuthenticationAsync>d__157`1[[System.Net.Security.AsyncReadWriteAdapter, System.Net.Security, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a]].MoveNext()
   at System.Runtime.CompilerServices.AsyncMethodBuilderCore.Start[[System.Net.Security.SslStream+<ForceAuthenticationAsync>d__157`1[[System.Net.Security.AsyncReadWriteAdapter, System.Net.Security, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a]], System.Net.Security, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a]](<ForceAuthenticationAsync>d__157`1<System.Net.Security.AsyncReadWriteAdapter> ByRef)
   at System.Runtime.CompilerServices.AsyncTaskMethodBuilder.Start[[System.Net.Security.SslStream+<ForceAuthenticationAsync>d__157`1[[System.Net.Security.AsyncReadWriteAdapter, System.Net.Security, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a]], System.Net.Security, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a]](<ForceAuthenticationAsync>d__157`1<System.Net.Security.AsyncReadWriteAdapter> ByRef)
   at System.Net.Security.SslStream.ForceAuthenticationAsync[[System.Net.Security.AsyncReadWriteAdapter, System.Net.Security, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a]](Boolean, Byte[], System.Threading.CancellationToken)
   at System.Net.Http.ConnectHelper+<EstablishSslConnectionAsync>d__2.MoveNext()
   at System.Runtime.CompilerServices.AsyncMethodBuilderCore.Start[[System.Net.Http.ConnectHelper+<EstablishSslConnectionAsync>d__2, System.Net.Http, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a]](<EstablishSslConnectionAsync>d__2 ByRef)
   at System.Runtime.CompilerServices.AsyncValueTaskMethodBuilder`1[[System.__Canon, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e]].Start[[System.Net.Http.ConnectHelper+<EstablishSslConnectionAsync>d__2, System.Net.Http, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a]](<EstablishSslConnectionAsync>d__2 ByRef)

   at System.Net.Http.ConnectHelper.EstablishSslConnectionAsync(System.Net.Security.SslClientAuthenticationOptions, System.Net.Http.HttpRequestMessage, Boolean, System.IO.Stream, System.Threading.CancellationToken)
   at System.Net.Http.HttpConnectionPool+<ConnectAsync>d__51.MoveNext()An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Error message: Out Of Memory   at System.Runtime.CompilerServices.AsyncTaskMethodBuilder`1+AsyncStateMachineBox`1[[System.ValueTuple`4[[System.__Canon, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e],[System.__Canon, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e],[System.__Canon, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e],[System.__Canon, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e]], System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e],[System.Net.Http.HttpConnectionPool+<ConnectAsync>d__51, System.Net.Http, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a]].ExecutionContextCallback(System.Object)


   at System.Threading.ExecutionContext.RunInternal(System.Threading.ExecutionContext, System.Threading.ContextCallback, System.Object)

   at System.Runtime.CompilerServices.AsyncTaskMethodBuilder`1+AsyncStateMachineBox`1[[System.ValueTuple`4[[System.__Canon, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e],[System.__Canon, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e],[System.__Canon, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e],[System.__Canon, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e]], System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e],[System.Net.Http.HttpConnectionPool+<ConnectAsync>d__51, System.Net.Http, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a]].MoveNext(System.Threading.Thread)
Out of memory.

Out of memory.
   at System.Runtime.CompilerServices.AsyncTaskMethodBuilder`1+AsyncStateMachineBox`1[[System.ValueTuple`4[[System.__Canon, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e],[System.__Canon, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e],[System.__Canon, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e],[System.__Canon, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e]], System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e],[System.Net.Http.HttpConnectionPool+<ConnectAsync>d__51, System.Net.Http, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a]].MoveNext()
   at System.Threading.Tasks.AwaitTaskContinuation.RunOrScheduleAction(System.Runtime.CompilerServices.IAsyncStateMachineBox, Boolean)
   at System.Threading.Tasks.Task.RunContinuations(System.Object)
   at System.Threading.Tasks.Task`1[[System.__Canon, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e]].TrySetResult(System.__Canon)
   at System.Runtime.CompilerServices.AsyncTaskMethodBuilder`1[[System.__Canon, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e]].SetExistingTaskResult(System.Threading.Tasks.Task`1<System.__Canon>, System.__Canon)
   at System.Net.Http.HttpConnectionPool+<ConnectToTcpHostAsync>d__52.MoveNext()
   at System.Runtime.CompilerServices.AsyncTaskMethodBuilder`1+AsyncStateMachineBox`1[[System.__Canon, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e],[System.Net.Http.HttpConnectionPool+<ConnectToTcpHostAsync>d__52, System.Net.Http, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a]].ExecutionContextCallback(System.Object)
   at System.Threading.ExecutionContext.RunInternal(System.Threading.ExecutionContext, System.Threading.ContextCallback, System.Object)
   at System.Runtime.CompilerServices.AsyncTaskMethodBuilder`1+AsyncStateMachineBox`1[[System.__Canon, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e],[System.Net.Http.HttpConnectionPool+<ConnectToTcpHostAsync>d__52, System.Net.Http, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a]].MoveNext(System.Threading.Thread)
   at System.Runtime.CompilerServices.AsyncTaskMethodBuilder`1+AsyncStateMachineBox`1[[System.__Canon, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e],[System.Net.Http.HttpConnectionPool+<ConnectToTcpHostAsync>d__52, System.Net.Http, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a]].MoveNext()
   at System.Threading.Tasks.AwaitTaskContinuation.RunOrScheduleAction(System.Runtime.CompilerServices.IAsyncStateMachineBox, Boolean)
   at System.Threading.Tasks.Task.RunContinuations(System.Object)
   at System.Threading.Tasks.Task`1[[System.Threading.Tasks.VoidTaskResult, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e]].TrySetResult(System.Threading.Tasks.VoidTaskResult)
   at System.Runtime.CompilerServices.AsyncTaskMethodBuilder`1[[System.Threading.Tasks.VoidTaskResult, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e]].SetExistingTaskResult(System.Threading.Tasks.Task`1<System.Threading.Tasks.VoidTaskResult>, System.Threading.Tasks.VoidTaskResult)
   at System.Runtime.CompilerServices.AsyncValueTaskMethodBuilder.SetResult()
   at System.Net.Sockets.Socket+<<ConnectAsync>g__WaitForConnectWithCancellation|285_0>d.MoveNext()
   at System.Runtime.CompilerServices.AsyncTaskMethodBuilder`1+AsyncStateMachineBox`1[[System.Threading.Tasks.VoidTaskResult, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e],[System.Net.Sockets.Socket+<<ConnectAsync>g__WaitForConnectWithCancellation|285_0>d, System.Net.Sockets, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a]].ExecutionContextCallback(System.Object)
   at System.Threading.ExecutionContext.RunInternal(System.Threading.ExecutionContext, System.Threading.ContextCallback, System.Object)
   at System.Runtime.CompilerServices.AsyncTaskMethodBuilder`1+AsyncStateMachineBox`1[[System.Threading.Tasks.VoidTaskResult, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e],[System.Net.Sockets.Socket+<<ConnectAsync>g__WaitForConnectWithCancellation|285_0>d, System.Net.Sockets, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a]].MoveNext(System.Threading.Thread)
   at System.Runtime.CompilerServices.AsyncTaskMethodBuilder`1+AsyncStateMachineBox`1[[System.Threading.Tasks.VoidTaskResult, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e],[System.Net.Sockets.Socket+<<ConnectAsync>g__WaitForConnectWithCancellation|285_0>d, System.Net.Sockets, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a]].MoveNext()
   at System.Net.Sockets.SocketAsyncEventArgs+<<DnsConnectAsync>g__Core|113_0>d.MoveNext()
   at System.Runtime.CompilerServices.AsyncTaskMethodBuilder`1+AsyncStateMachineBox`1[[System.Threading.Tasks.VoidTaskResult, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e],[System.Net.Sockets.SocketAsyncEventArgs+<<DnsConnectAsync>g__Core|113_0>d, System.Net.Sockets, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a]].ExecutionContextCallback(System.Object)
   at System.Threading.ExecutionContext.RunInternal(System.Threading.ExecutionContext, System.Threading.ContextCallback, System.Object)
   at System.Runtime.CompilerServices.AsyncTaskMethodBuilder`1+AsyncStateMachineBox`1[[System.Threading.Tasks.VoidTaskResult, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e],[System.Net.Sockets.SocketAsyncEventArgs+<<DnsConnectAsync>g__Core|113_0>d, System.Net.Sockets, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a]].MoveNext(System.Threading.Thread)
   at System.Runtime.CompilerServices.AsyncTaskMethodBuilder`1+AsyncStateMachineBox`1[[System.Threading.Tasks.VoidTaskResult, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e],[System.Net.Sockets.SocketAsyncEventArgs+<<DnsConnectAsync>g__Core|113_0>d, System.Net.Sockets, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a]].MoveNext()
   at System.Threading.ExecutionContext.RunInternal(System.Threading.ExecutionContext, System.Threading.ContextCallback, System.Object)
   at System.Net.Sockets.SocketAsyncEventArgs+<>c.<.cctor>b__174_0(UInt32, UInt32, System.Threading.NativeOverlapped*)
   at System.Threading.PortableThreadPool+IOCompletionPoller+Callback.Invoke(Event)
   at System.Threading.ThreadPoolTypedWorkItemQueue`2[[System.Threading.PortableThreadPool+IOCompletionPoller+Event, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e],[System.Threading.PortableThreadPool+IOCompletionPoller+Callback, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e]].System.Threading.IThreadPoolWorkItem.Execute()
   at System.Threading.ThreadPoolWorkQueue.Dispatch()
   at System.Threading.PortableThreadPool+WorkerThread.WorkerThreadStart()
Failed to create CoreCLR, HRESULT: 0x8007000E
Out of memory.
Fatal error. Internal CLR error. (0x80131506)
Unhandled exception. Process terminated. Stack overflow.
Fatal error. Fatal error. Out of memory.
Process terminated. Process terminated. Process terminated. Out of memory.
Process terminated. OperationStopped: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:6
Process terminated. Line |
   6 |  pwsh .\tools\Build-Landers.ps1 -All -Root .\docs -GTM GTM-K58Z4XD -Fo …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | Exception of type 'System.OutOfMemoryException' was thrown.
Fatal error. Internal CLR error. (0x80131506)
Process terminated. Exception of type 'System.OutOfMemoryException' was thrown.
   at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)
   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)
   at System.Environment.FailFast(System.String, System.Exception)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)
   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])
System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at System.SpanHelpers.NonPackedIndexOfValueType[TValue,TNegator](TValue& searchSpace, TValue value, Int32 length)
   at System.Enum.IsDefinedPrimitive[TStorage](RuntimeType enumType, TStorage value)
   at System.RuntimeType.IsEnumDefined(Object value)
   at Microsoft.Win32.RegistryKey.GetValueKind(String name)
   at System.Management.Automation.Platform.get_IsIoT()
   at System.Management.Automation.Platform.get_IsWindowsDesktop()
   at Microsoft.PowerShell.TaskbarJumpList.CreateRunAsAdministratorJumpList()
   at Microsoft.PowerShell.ConsoleHost.Start(String bannerText, String helpText, Boolean issProvidedExternally)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)Process terminated. The type initializer for 'System.Management.Automation.PSVersionInfo' threw an exception.
   at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)
   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)
   at System.Environment.FailFast(System.String, System.Exception)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)
   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])
System.TypeInitializationException: The type initializer for 'System.Management.Automation.PSVersionInfo' threw an exception.
 ---> System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at System.Version.ParseVersion(ReadOnlySpan`1 input, Boolean throwOnFailure)
   at System.Version.Parse(String input)
   at System.Version..ctor(String version)
   at System.Management.Automation.PSVersionInfo..cctor()
   --- End of inner exception stack trace ---
   at System.Management.Automation.PSSnapInReader.ReadRegistryInfo(Version& assemblyVersion, String& publicKeyToken, String& culture, String& applicationBase, Version& psVersion)
   at System.Management.Automation.PSSnapInReader.ReadCoreEngineSnapIn()
   at System.Management.Automation.Runspaces.InitialSessionState.CreateDefault2()
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)Process terminated. Internal CLR error. (0x80131506)
Exception of type 'System.OutOfMemoryException' was thrown.
Out of memory.
Process terminated. Stack overflow.
Process terminated. Process terminated. Process terminated.






GC: PER_HEAP_ISOLATED data members initialization failedProcess terminated. Exception of type 'System.OutOfMemoryException' was thrown.Process terminated. Exception of type 'System.OutOfMemoryException' was thrown.
   at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)
   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)
   at System.Environment.FailFast(System.String, System.Exception)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)
   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])
System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry.SendPSCoreStartupTelemetry(String mode, Double parametersUsed)
   at Microsoft.PowerShell.ConsoleHost.Start(String bannerText, String helpText, Boolean issProvidedExternally)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)   at System.Management.Automation.Runspaces.LocalPipeline.InvokeThreadProc()
   at System.Management.Automation.Runspaces.PipelineThread.WorkerProc()
   at System.Threading.ExecutionContext.RunInternal(System.Threading.ExecutionContext, System.Threading.ContextCallback, System.Object)
The type initializer for 'System.Management.Automation.Internal.ValueStringDecorated' threw an exception.

Process terminated. Exception of type 'System.OutOfMemoryException' was thrown.
   at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)
   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)
   at System.Environment.FailFast(System.String, System.Exception)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)
   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])
System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at System.Threading.Thread.StartCore()
   at Microsoft.PowerShell.TaskbarJumpList.CreateRunAsAdministratorJumpList()
   at Microsoft.PowerShell.ConsoleHost.Start(String bannerText, String helpText, Boolean issProvidedExternally)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)The type initializer for 'Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry' threw an exception.
   at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)
   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)
   at System.Environment.FailFast(System.String, System.Exception)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)
   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])
System.TypeInitializationException: The type initializer for 'Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry' threw an exception.
 ---> System.TypeInitializationException: The type initializer for 'Microsoft.ApplicationInsights.Extensibility.TelemetryConfiguration' threw an exception.
 ---> System.TypeInitializationException: The type initializer for 'System.Diagnostics.Activity' threw an exception.
 ---> System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at System.Diagnostics.ActivitySource..ctor(String name, String version, IEnumerable`1 tags)
   at System.Diagnostics.Activity..cctor()
   --- End of inner exception stack trace ---
   at System.Diagnostics.Activity.get_ForceDefaultIdFormat()
   at Microsoft.ApplicationInsights.Extensibility.TelemetryConfiguration.<>c.<.cctor>b__13_0()
   at Microsoft.ApplicationInsights.ActivityExtensions.TryRun(Action action)
   at Microsoft.ApplicationInsights.Extensibility.TelemetryConfiguration..cctor()
   --- End of inner exception stack trace ---
   at Microsoft.ApplicationInsights.Extensibility.TelemetryConfiguration.CreateDefault()
   at Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry..cctor()
   --- End of inner exception stack trace ---
   at Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry.SendPSCoreStartupTelemetry(String mode, Double parametersUsed)
   at Microsoft.PowerShell.ConsoleHost.Start(String bannerText, String helpText, Boolean issProvidedExternally)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)Exception of type 'System.OutOfMemoryException' was thrown.
Fatal error.
System.Management.Automation.PSInvalidOperationException: PowerShell has stopped working because of a security issue: Cannot read the configuration file: C:\Program Files\PowerShell\7\powershell.config.json
 ---> System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at Newtonsoft.Json.Utilities.ReflectionUtils.GetAttributes(Object attributeProvider, Type attributeType, Boolean inherit)
   at Newtonsoft.Json.Serialization.JsonTypeReflector.GetAssociateMetadataTypeFromAttribute(Type type)
   at System.Collections.Concurrent.ConcurrentDictionary`2.GetOrAdd(TKey key, Func`2 valueFactory)
   at Newtonsoft.Json.Serialization.JsonTypeReflector.GetAttribute[T](Type type)
   at Newtonsoft.Json.Serialization.JsonTypeReflector.GetAttribute[T](Object provider)
   at System.Collections.Concurrent.ConcurrentDictionary`2.GetOrAdd(TKey key, Func`2 valueFactory)
   at Newtonsoft.Json.Serialization.DefaultContractResolver.CreateContract(Type objectType)
   at System.Collections.Concurrent.ConcurrentDictionary`2.GetOrAdd(TKey key, Func`2 valueFactory)
   at Newtonsoft.Json.Serialization.JsonSerializerInternalReader.Deserialize(JsonReader reader, Type objectType, Boolean checkAdditionalContent)
   at Newtonsoft.Json.JsonSerializer.DeserializeInternal(JsonReader reader, Type objectType)
   at Newtonsoft.Json.JsonSerializer.Deserialize[T](JsonReader reader)
   at System.Management.Automation.Configuration.PowerShellConfig.ReadValueFromFile[T](ConfigScope scope, String key, T defaultValue)
   --- End of inner exception stack trace ---
   at System.Management.Automation.Configuration.PowerShellConfig.ReadValueFromFile[T](ConfigScope scope, String key, T defaultValue)
   at System.Management.Automation.Configuration.PowerShellConfig.GetPowerShellPolicies(ConfigScope scope)
   at System.Collections.Concurrent.ConcurrentDictionary`2.GetOrAdd(TKey key, Func`2 valueFactory)
   at System.Management.Automation.Utils.GetPolicySettingFromConfigFile[T](ConfigScope[] preferenceOrder)
   at System.Management.Automation.Utils.GetPolicySetting[T](ConfigScope[] preferenceOrder)
   at Microsoft.PowerShell.CommandLineParameterParser.GetConfigurationNameFromGroupPolicy()
   at Microsoft.PowerShell.ConsoleHost.ParseCommandLine(String[] args)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)
   at Microsoft.PowerShell.ManagedPSEntry.Main(String[] args)Process terminated. Fatal error. Exception of type 'System.OutOfMemoryException' was thrown.
   at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)
Exception of type 'System.OutOfMemoryException' was thrown.
Exception of type 'System.OutOfMemoryException' was thrown.

   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)
Exception of type 'System.OutOfMemoryException' was thrown.
   at System.Environment.FailFast(System.String, System.Exception)
   at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)
   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)
   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])
   at System.Environment.FailFast(System.String, System.Exception)
System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry.SendPSCoreStartupTelemetry(String mode, Double parametersUsed)
   at Microsoft.PowerShell.ConsoleHost.Start(String bannerText, String helpText, Boolean issProvidedExternally)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)
   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])
System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at System.Management.Automation.Host.PSHostUserInterface.get_TranscriptionData()
   at System.Management.Automation.Host.PSHostUserInterface.CheckSystemTranscript()
   at Microsoft.PowerShell.ConsoleHostUserInterface..ctor(ConsoleHost parent)
   at Microsoft.PowerShell.ConsoleHost..ctor()
   at Microsoft.PowerShell.ConsoleHost.Start(String bannerText, String helpText, Boolean issProvidedExternally)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)The shell cannot be started. A failure occurred during initialization:
Exception of type 'System.OutOfMemoryException' was thrown.

   at System.SpanHelpers.NonPackedIndexOfValueType[[System.Int32, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e],[System.SpanHelpers+DontNegate`1[[System.Int32, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e]], System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e]](Int32 ByRef, Int32, Int32)
   at System.Enum.IsDefinedPrimitive[[System.UInt32, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e]](System.RuntimeType, UInt32)
   at System.RuntimeType.IsEnumDefined(System.Object)
   at Microsoft.Win32.RegistryKey.GetValueKind(System.String)
   at System.Management.Automation.Platform.get_IsIoT()
   at System.Management.Automation.Platform.get_IsWindowsDesktop()
   at Microsoft.PowerShell.TaskbarJumpList.CreateRunAsAdministratorJumpList()
   at Microsoft.PowerShell.ConsoleHost.Start(System.String, System.String, Boolean)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)
   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])
Out of memory.
Exception of type 'System.OutOfMemoryException' was thrown.New-Item: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:2
Line |
   2 |  New-Item -ItemType Directory -Path .\tools -Force | Out-Null
     |  ~~~~~~~~
     | The 'New-Item' command was found in the module 'Microsoft.PowerShell.Management', but the module could not be
     | loaded due to the following error: [Exception of type 'System.OutOfMemoryException' was thrown.] For more
     | information, run 'Import-Module Microsoft.PowerShell.Management'.

Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
format-default: Exception of type 'System.OutOfMemoryException' was thrown.
Line |
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
New-Item: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:2
Line |
   2 |  New-Item -ItemType Directory -Path .\tools -Force | Out-Null
     |  ~~~~~~~~
     | The 'New-Item' command was found in the module 'Microsoft.PowerShell.Management', but the module could not be
     | loaded due to the following error: [Exception of type 'System.OutOfMemoryException' was thrown.] For more
     | information, run 'Import-Module Microsoft.PowerShell.Management'.
←[31;1mOutOfMemoryException: ←[31;1mException of type 'System.OutOfMemoryException' was thrown.←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1mSecurityError: ←[31;1mAuthorizationManager check failed.←[0m
←[31;1mParentContainsErrorRecordException: ←[31;1mAn error occurred while creating the pipeline.←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
     | The process cannot access the file
Line |
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     | another process.
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Exception of type 'System.OutOfMemoryException' was thrown.Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3

Line |
ParentContainsErrorRecordException: An error occurred while creating the pipeline.
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
SecurityError: AuthorizationManager check failed.
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Exception of type 'System.OutOfMemoryException' was thrown.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
Line |
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
     | another process.
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
Line |
Line |
Line |
Line |
Exception of type 'System.OutOfMemoryException' was thrown.
Exception of type 'System.OutOfMemoryException' was thrown.Exception of type 'System.OutOfMemoryException' was thrown.Exception of type 'System.OutOfMemoryException' was thrown.
Exception of type 'System.OutOfMemoryException' was thrown.   at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)
   at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)The type initializer for 'Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry' threw an exception.Failed to create RW mapping for RX memory. This can be caused by insufficient memory or hitting the limit of memory mappings on Linux (vm.map_max_count).

Exception of type 'System.OutOfMemoryException' was thrown.

   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
     | another process.
     | another process.
     | another process.
An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
     | another process.
New-Item: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:2
Line |
←[31;1m←[0m←[36;1m←[36;1m   2 | ←[0m New-Item -ItemType ←[36;1mDirectory←[0m -Path .\tools -Force | Out-Null←[0m
     |                     ~~~~~~~~~
     | Cannot bind parameter 'ItemType' to the target. Exception setting "ItemType": "Exception of type
     | 'System.OutOfMemoryException' was thrown."
OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
ParentContainsErrorRecordException: An error occurred while creating the pipeline.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3




GC heap initialization failed with error 0x80004005   at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)   at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)
   at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)

   at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)
   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)

   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)
   at System.Environment.FailFast(System.String, System.Exception)
   at System.Environment.FailFast(System.String, System.Exception)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)
   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])
   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])
System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at System.Management.Automation.Runspaces.PSSnapInHelpers.InitializeCoreCmdletsAndProviders(PSSnapInInfo psSnapInInfo, Dictionary`2& cmdlets, Dictionary`2& providers, String helpFile)
   at System.Management.Automation.Runspaces.PSSnapInHelpers.AnalyzePSSnapInAssembly(Assembly assembly, String name, PSSnapInInfo psSnapInInfo, PSModuleInfo moduleInfo, Dictionary`2& cmdlets, Dictionary`2& aliases, Dictionary`2& providers, String& helpFile)
   at System.Management.Automation.Runspaces.InitialSessionState.ImportPSSnapIn(PSSnapInInfo psSnapInInfo, PSSnapInException& warning)
   at System.Management.Automation.Runspaces.InitialSessionState.CreateDefault2()
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)
System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at Microsoft.PowerShell.ConsoleHost.DoCreateRunspace(RunspaceCreationEventArgs args)
   at Microsoft.PowerShell.ConsoleHost.CreateRunspace(RunspaceCreationEventArgs runspaceCreationArgs)
   at Microsoft.PowerShell.ConsoleHost.DoRunspaceLoop(String initialCommand, Boolean skipProfiles, Collection`1 initialCommandArgs, Boolean staMode, String configurationName, String configurationFilePath)
   at Microsoft.PowerShell.ConsoleHost.Run(CommandLineParameterParser cpp, Boolean isPrestartWarned)
   at Microsoft.PowerShell.ConsoleHost.Start(String bannerText, String helpText, Boolean issProvidedExternally)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)   at System.Environment.FailFast(System.String, System.Exception)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)
   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])
System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry.SendPSCoreStartupTelemetry(String mode, Double parametersUsed)
   at Microsoft.PowerShell.ConsoleHost.Start(String bannerText, String helpText, Boolean issProvidedExternally)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)Line |
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | The process cannot access the file
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
Line |
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | The process cannot access the file
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
     | another process.
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
     | another process.
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Line |
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
SecurityError: AuthorizationManager check failed.
An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.ParentContainsErrorRecordException: An error occurred while creating the pipeline.
←[31;1mSecurityError: ←[31;1mAuthorizationManager check failed.←[0m
ParentContainsErrorRecordException: An error occurred while creating the pipeline.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.ParentContainsErrorRecordException: An error occurred while creating the pipeline.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
ParentContainsErrorRecordException: An error occurred while creating the pipeline.
ParentContainsErrorRecordException: An error occurred while creating the pipeline.
ParentContainsErrorRecordException: An error occurred while creating the pipeline.
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
ParentContainsErrorRecordException: An error occurred while creating the pipeline.
The process cannot access the file 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by another process.
   at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
     | another process.
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
Line |
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
     | another process.
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.

Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
←[31;1mParentContainsErrorRecordException: ←[31;1mAn error occurred while creating the pipeline.←[0m





Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
Out of memory.
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |

Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.

Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3

Out of memory.
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Out of memory.
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
   at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)
   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)
   at System.Environment.FailFast(System.String, System.Exception)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)
   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])
System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry..cctor()
   at Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry.SendPSCoreStartupTelemetry(String mode, Double parametersUsed)
   at Microsoft.PowerShell.ConsoleHost.Start(String bannerText, String helpText, Boolean issProvidedExternally)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)Out of memory.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m

Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
     | The process cannot access the file
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | another process.
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Processing -File 'C:\Program Files\PowerShell\7\pwsh.exe' failed because the file does not have a '.ps1' extension. Specify a valid PowerShell script file name, and then try again.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.

←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
   at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)Out of memory.
Out of memory.
Out of memory.
Out of memory.
   at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)Failed to create CoreCLR, HRESULT: 0x80004005   at System.Environment.FailFast(System.String, System.Exception)Out of memory.
   at System.Environment.FailFast(System.String, System.Exception)←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.

←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
     | another process.
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.

←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Out of memory.
Process terminated. The type initializer for 'Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry' threw an exception.
   at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)
   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)
   at System.Environment.FailFast(System.String, System.Exception)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)
   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])
System.TypeInitializationException: The type initializer for 'Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry' threw an exception.
 ---> System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at Microsoft.ApplicationInsights.Extensibility.TelemetryConfiguration.CreateDefault()
   at Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry..cctor()
   --- End of inner exception stack trace ---
   at Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry.SendPSCoreStartupTelemetry(String mode, Double parametersUsed)
   at Microsoft.PowerShell.ConsoleHost.Start(String bannerText, String helpText, Boolean issProvidedExternally)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)OperationStopped: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:6
Line |
   6 |  pwsh .\tools\Build-Landers.ps1 -All -Root .\docs -GTM GTM-K58Z4XD -Fo …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | Exception of type 'System.OutOfMemoryException' was thrown.

Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
Line |
Line |
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     | The process cannot access the file
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | The process cannot access the file
     | The process cannot access the file
     | another process.
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Out of memory.
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1mLine |←[0m
Line |
Line |

Line |
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
Process terminated. The type initializer for 'Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry' threw an exception.
   at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)
   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)
   at System.Environment.FailFast(System.String, System.Exception)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)
   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])
System.TypeInitializationException: The type initializer for 'Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry' threw an exception.
 ---> System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at Microsoft.ApplicationInsights.Extensibility.TelemetryConfiguration..ctor(String instrumentationKey, ITelemetryChannel channel)
   at Microsoft.ApplicationInsights.Extensibility.TelemetryConfiguration.CreateDefault()
   at Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry..cctor()
   --- End of inner exception stack trace ---
   at Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry.SendPSCoreStartupTelemetry(String mode, Double parametersUsed)
   at Microsoft.PowerShell.ConsoleHost.Start(String bannerText, String helpText, Boolean issProvidedExternally)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Out of memory.
     | another process.
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …

←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m

Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
   at System.Environment.FailFast(System.String, System.Exception)     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file

←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by

   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)     | another process.
     | another process.
     | another process.

     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | another process.
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)
     | The process cannot access the file
     | The process cannot access the file
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
   at System.Environment.FailFast(System.String, System.Exception)
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)
     | another process.
     | another process.
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)
   at System.Environment.FailFast(System.String, System.Exception)   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])   at System.Environment.FailFast(System.String, System.Exception)   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])


   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)
System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at System.Management.Automation.Internal.ObjectStream.get_ObjectWriter()
   at System.Management.Automation.Runspaces.LocalPipeline.InitStreams()
   at System.Management.Automation.Runspaces.LocalRunspace.CoreCreatePipeline(String command, Boolean addToHistory, Boolean isNested)
   at Microsoft.PowerShell.ConsoleHost.DoRunspaceInitialization(RunspaceCreationEventArgs args)
   at Microsoft.PowerShell.ConsoleHost.CreateRunspace(RunspaceCreationEventArgs runspaceCreationArgs)
   at Microsoft.PowerShell.ConsoleHost.DoRunspaceLoop(String initialCommand, Boolean skipProfiles, Collection`1 initialCommandArgs, Boolean staMode, String configurationName, String configurationFilePath)
   at Microsoft.PowerShell.ConsoleHost.Run(CommandLineParameterParser cpp, Boolean isPrestartWarned)
   at Microsoft.PowerShell.ConsoleHost.Start(String bannerText, String helpText, Boolean issProvidedExternally)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])
System.TypeInitializationException: The type initializer for 'Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry' threw an exception.
 ---> System.TypeInitializationException: The type initializer for 'System.DomainNameHelper' threw an exception.
 ---> System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at System.SpanHelpers.Fill[T](T& refData, UIntPtr numElements, T value)
   at System.Buffers.ProbabilisticMapState..ctor(ReadOnlySpan`1 values, Int32 maxInclusive)
   at System.Buffers.ProbabilisticWithAsciiCharSearchValues`1..ctor(ReadOnlySpan`1 values, Int32 maxInclusive)
   at System.Buffers.SearchValues.Create(ReadOnlySpan`1 values)
   at System.DomainNameHelper..cctor()
   --- End of inner exception stack trace ---
   at System.DomainNameHelper.IsValid(ReadOnlySpan`1 hostname, Boolean iri, Boolean notImplicitFile, Int32& length)
   at System.Uri.CheckAuthorityHelper(Char* pString, Int32 idx, Int32 length, ParsingError& err, Flags& flags, UriParser syntax, String& newHost)
   at System.Uri.PrivateParseMinimal()
   at System.Uri.InitializeUri(ParsingError err, UriKind uriKind, UriFormatException& e)
   at System.Uri.CreateThis(String uri, Boolean dontEscape, UriKind uriKind, UriCreationOptions& creationOptions)
   at System.Uri..ctor(String uriString)
   at Microsoft.ApplicationInsights.Extensibility.Implementation.Endpoints.EndpointProvider.GetEndpoint(EndpointName endpointName)
   at Microsoft.ApplicationInsights.Extensibility.Implementation.Endpoints.EndpointContainer..ctor(IEndpointProvider endpointProvider)
   at Microsoft.ApplicationInsights.Extensibility.TelemetryConfiguration..ctor(String instrumentationKey, ITelemetryChannel channel)
   at Microsoft.ApplicationInsights.Extensibility.TelemetryConfiguration.CreateDefault()
   at Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry..cctor()
   --- End of inner exception stack trace ---
   at Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry.SendPSCoreStartupTelemetry(String mode, Double parametersUsed)
   at Microsoft.PowerShell.ConsoleHost.Start(String bannerText, String helpText, Boolean issProvidedExternally)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)

System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at System.Management.Automation.Security.NativeMethods.SaferComputeTokenFromLevel(IntPtr LevelHandle, IntPtr InAccessToken, IntPtr& OutAccessToken, UInt32 dwFlags, IntPtr lpReserved)
   at System.Management.Automation.Internal.SecuritySupport.GetSaferPolicy(String path, SafeHandle handle)
   at System.Management.Automation.Security.SystemPolicy.TestSaferPolicy(String testPathScript, String testPathModule)
   at System.Management.Automation.Security.SystemPolicy.GetAppLockerPolicy(String path, SafeHandle handle)
   at System.Management.Automation.Security.SystemPolicy.GetLockdownPolicy(String path, SafeHandle handle, Nullable`1 canExecuteResult)
   at System.Management.Automation.Security.SystemPolicy.GetLockdownPolicy(String path, SafeHandle handle)
   at System.Management.Automation.Security.SystemPolicy.GetSystemLockdownPolicy()
   at System.Management.Automation.Runspaces.InitialSessionState..cctor()
   at System.Management.Automation.Runspaces.InitialSessionState.CreateDefault2()
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
Line |
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     | The process cannot access the file
Line |
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     | The process cannot access the file
     | another process.
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | The process cannot access the file
     | another process.
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at System.Management.Automation.Runspaces.Runspace.get_RunspaceList()
   at System.Management.Automation.Runspaces.LocalRunspace.DoCloseHelper()
   at System.Management.Automation.Runspaces.RunspaceBase.CoreClose(Boolean syncCall)
   at System.Management.Automation.Runspaces.LocalRunspace.Dispose(Boolean disposing)
   at System.Management.Automation.Runspaces.Runspace.Dispose()
   at Microsoft.PowerShell.ConsoleHost.Dispose(Boolean isDisposingNotFinalizing)
   at Microsoft.PowerShell.ConsoleHost.Start(String bannerText, String helpText, Boolean issProvidedExternally)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file 'C:\tools\Build-Landers.ps1' because it is being used by another process.
System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at Microsoft.PowerShell.ConsoleHost.Start(String bannerText, String helpText, Boolean issProvidedExternally)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])
System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at System.Text.EncodingHelper.GetSupportedConsoleEncoding(Int32 codepage)
   at System.Console.get_OutputEncoding()
   at System.ConsolePal.OpenStandardError()
   at System.Console.<get_Error>g__EnsureInitialized|28_0()
   at Microsoft.PowerShell.ConsoleHost.ReportExceptionFallback(Exception e, String header)
   at Microsoft.PowerShell.ConsoleHost.CreateRunspace(RunspaceCreationEventArgs runspaceCreationArgs)
   at Microsoft.PowerShell.ConsoleHost.DoRunspaceLoop(String initialCommand, Boolean skipProfiles, Collection`1 initialCommandArgs, Boolean staMode, String configurationName, String configurationFilePath)
   at Microsoft.PowerShell.ConsoleHost.Run(CommandLineParameterParser cpp, Boolean isPrestartWarned)
   at Microsoft.PowerShell.ConsoleHost.Start(String bannerText, String helpText, Boolean issProvidedExternally)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Process terminated.
Process terminated. Exception of type 'System.OutOfMemoryException' was thrown.←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
Line |
Line |
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
     | another process.
     | another process.
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m

←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1mLine |←[0m
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
     | another process.
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     | The process cannot access the file
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | another process.
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
     | another process.
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
Exception of type 'System.OutOfMemoryException' was thrown.
   at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)
An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.
   at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
     | another process.
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
     | another process.
   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m

←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)
   at System.Environment.FailFast(System.String, System.Exception)Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
Line |
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     | The process cannot access the file
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | The process cannot access the file
     | another process.
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.

   at System.Environment.FailFast(System.String, System.Exception)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)
   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])
   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at System.Reflection.AssemblyNameParser.TryParsePKT(String attributeValue, Boolean isToken, Byte[]& result)
   at System.Reflection.AssemblyNameParser.TryParse(AssemblyNameParts& result)
   at System.Reflection.AssemblyNameParser.Parse(ReadOnlySpan`1 name)
   at System.Reflection.AssemblyName..ctor(String assemblyName)
   at System.Management.Automation.Runspaces.PSSnapInHelpers.LoadPSSnapInAssembly(PSSnapInInfo psSnapInInfo)
   at System.Management.Automation.Runspaces.InitialSessionState.ImportPSSnapIn(PSSnapInInfo psSnapInInfo, PSSnapInException& warning)
   at System.Management.Automation.Runspaces.InitialSessionState.CreateDefault2()
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Line |
     | The process cannot access the file
     | The process cannot access the file
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | another process.
     | another process.
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
     | another process.
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at System.Management.Automation.Internal.ObjectStream.get_ObjectWriter()
   at System.Management.Automation.Runspaces.LocalPipeline.InitStreams()
   at System.Management.Automation.Runspaces.LocalRunspace.CoreCreatePipeline(String command, Boolean addToHistory, Boolean isNested)
   at Microsoft.PowerShell.ConsoleHost.DoRunspaceInitialization(RunspaceCreationEventArgs args)
   at Microsoft.PowerShell.ConsoleHost.CreateRunspace(RunspaceCreationEventArgs runspaceCreationArgs)
   at Microsoft.PowerShell.ConsoleHost.DoRunspaceLoop(String initialCommand, Boolean skipProfiles, Collection`1 initialCommandArgs, Boolean staMode, String configurationName, String configurationFilePath)
   at Microsoft.PowerShell.ConsoleHost.Run(CommandLineParameterParser cpp, Boolean isPrestartWarned)
   at Microsoft.PowerShell.ConsoleHost.Start(String bannerText, String helpText, Boolean issProvidedExternally)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
Line |
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     | The process cannot access the file
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | The process cannot access the file
     | another process.
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
Line |
Line |
Line |
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
     | another process.
     | another process.
     | another process.
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
Line |
Line |
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | The process cannot access the file
     | another process.
     | another process.
     | another process.
     | another process.
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
New-Item: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:2
Line |
   2 |  New-Item -ItemType Directory -Path .\tools -Force | Out-Null
     |  ~~~~~~~~
     | The 'New-Item' command was found in the module 'Microsoft.PowerShell.Management', but the module could not be
     | loaded due to the following error: [Exception of type 'System.OutOfMemoryException' was thrown.] For more
     | information, run 'Import-Module Microsoft.PowerShell.Management'.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
Line |
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     | The process cannot access the file
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
New-Item: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:2
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
New-Item: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:2
Get-Clipboard: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Build-Landers.ps1: Exception of type 'System.OutOfMemoryException' was thrown.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
New-Item: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:2
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
Line |
Line |
Line |
Line |
Line |
Line |
Line |
Line |
Line |
Line |
Line |
Line |
Line |
Line |
Line |
Line |
Line |
Line |
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  … \tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clipboard) # <- o …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   2 |  New-Item -ItemType Directory -Path .\tools -Force | Out-Null
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   2 |  New-Item -ItemType Directory -Path .\tools -Force | Out-Null
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   2 |  New-Item -ItemType Directory -Path .\tools -Force | Out-Null
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |                                                    ~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | Exception of type 'System.OutOfMemoryException' was thrown.
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | The 'New-Item' command was found in the module 'Microsoft.PowerShell.Management', but the module could not be
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | The 'New-Item' command was found in the module 'Microsoft.PowerShell.Management', but the module could not be
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | The process cannot access the file
     | The 'New-Item' command was found in the module 'Microsoft.PowerShell.Management', but the module could not be
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | loaded due to the following error: [Exception of type 'System.OutOfMemoryException' was thrown.] For more
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | loaded due to the following error: [Exception of type 'System.OutOfMemoryException' was thrown.] For more
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
     | another process.
     | another process.
     | another process.
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | loaded due to the following error: [Exception of type 'System.OutOfMemoryException' was thrown.] For more
     | another process.
     | another process.
     | another process.
     | another process.
     | another process.
     | another process.
     | information, run 'Import-Module Microsoft.PowerShell.Management'.
     | another process.
     | another process.
     | information, run 'Import-Module Microsoft.PowerShell.Management'.
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
     | another process.
     | another process.
     | another process.
     | information, run 'Import-Module Microsoft.PowerShell.Management'.
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
New-Item: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:2
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Line |
     | Exception of type 'System.OutOfMemoryException' was thrown.
   2 |  New-Item -ItemType Directory -Path .\tools -Force | Out-Null
     |  ~~~~~~~~
     | The 'New-Item' command was found in the module 'Microsoft.PowerShell.Management', but the module could not be
     | loaded due to the following error: [Exception of type 'System.OutOfMemoryException' was thrown.] For more
     | information, run 'Import-Module Microsoft.PowerShell.Management'.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
New-Item: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:2
Line |
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   2 |  New-Item -ItemType Directory -Path .\tools -Force | Out-Null
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~
     | The process cannot access the file
     | The 'New-Item' command was found in the module 'Microsoft.PowerShell.Management', but the module could not be
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | loaded due to the following error: [Exception of type 'System.OutOfMemoryException' was thrown.] For more
     | another process.
     | information, run 'Import-Module Microsoft.PowerShell.Management'.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
     | The process cannot access the file
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
Line |
     | another process.
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
Line |
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     | The process cannot access the file
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | The process cannot access the file
     | another process.
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
ParentContainsErrorRecordException: An error occurred while creating the pipeline.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
     | another process.
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
Line |
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
     | another process.
     | another process.
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1mLine |←[0m
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
     | another process.
     | another process.
Line |
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Line |
     | The process cannot access the file
     | The process cannot access the file
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | another process.
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
Line |
Line |
Line |
Line |
Line |
Line |
Line |
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
     | another process.
     | another process.
     | another process.
     | another process.
     | another process.
     | another process.
     | another process.
     | another process.
     | The process cannot access the file
     | The process cannot access the file
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
     | The process cannot access the file
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     | another process.
Line |
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
Line |
     | another process.
Line |
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
Line |
Line |
Line |
Line |
Line |
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
Line |
Line |
Line |
Line |
Line |
Line |
Line |
Line |
Line |
Line |
Line |
Line |
Line |
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
     | another process.
     | another process.
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
     | another process.
     | another process.
     | another process.
     | another process.
     | another process.
     | another process.
     | another process.
     | another process.
     | another process.
     | another process.
     | another process.
     | another process.
     | another process.
Line |
     | another process.
     | another process.
     | another process.
     | another process.
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
Line |
Line |
Line |
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
     | another process.
     | another process.
     | another process.
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
←[31;1m←[0m←[36;1mLine |←[0m
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
     | another process.
Line |
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
     | another process.
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
Line |
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
     | another process.
Line |
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
Line |
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     | The process cannot access the file
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | The process cannot access the file
     | another process.
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
     | another process.
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
←[31;1m←[0m←[36;1mLine |←[0m
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
     | The process cannot access the file
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
     | another process.
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
Line |
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Line |
Line |
Line |
Line |
Line |
     | The process cannot access the file
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | The process cannot access the file
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
Line |
Line |
Line |
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Line |
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
     | The process cannot access the file
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Line |
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Line |
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
Line |
Line |
Line |
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
     | The process cannot access the file
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     | another process.
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     | The process cannot access the file
Line |
Line |
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
Line |
Line |
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
     | The process cannot access the file
     | another process.
     | The process cannot access the file
     | another process.
     | another process.
     | another process.
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
Line |
Line |
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
Line |
     | another process.
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Line |
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     | The process cannot access the file
     | The process cannot access the file
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     | another process.
     | The process cannot access the file
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | another process.
     | another process.
     | another process.
     | another process.
Line |
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     | The process cannot access the file
     | another process.
     | another process.
     | The process cannot access the file
     | The process cannot access the file
     | another process.
     | another process.
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
Line |
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     | The process cannot access the file
     | another process.
     | another process.
     | another process.
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | The process cannot access the file
     | another process.
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
     | The process cannot access the file
Line |
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     | another process.
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
     | another process.
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
     | another process.
     | another process.
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
Line |
     | another process.
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
     | The process cannot access the file
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Line |
     | another process.
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
     | another process.
     | another process.
     | another process.
     | another process.
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
Line |
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
Line |
Line |
Line |
Line |
Line |
Line |
Line |
Line |
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Line |
Line |
Line |
Line |
Line |
Line |
Line |
Line |
Line |
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
Line |
Line |
Line |
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     | The process cannot access the file
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
     | The process cannot access the file
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | another process.
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
     | another process.
     | another process.
     | another process.
     | another process.
     | another process.
     | another process.
     | another process.
     | another process.
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
     | another process.
     | another process.
     | another process.
     | another process.
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Line |
Line |
     | another process.
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
Line |
Line |
Line |
Line |
Line |
Line |
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
     | another process.
     | another process.
     | another process.
     | another process.
     | another process.
     | another process.
     | another process.
     | another process.
     | another process.
Process terminated. Exception of type 'System.OutOfMemoryException' was thrown.
   at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)
   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)
   at System.Environment.FailFast(System.String, System.Exception)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)
   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])
System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry.SendPSCoreStartupTelemetry(String mode, Double parametersUsed)
   at Microsoft.PowerShell.ConsoleHost.Start(String bannerText, String helpText, Boolean issProvidedExternally)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)Process terminated. Exception of type 'System.OutOfMemoryException' was thrown.
   at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)
   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)
   at System.Environment.FailFast(System.String, System.Exception)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)
   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])
System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at System.Management.Automation.Host.TranscriptionData..ctor()
   at System.Management.Automation.Host.PSHostUserInterface.get_TranscriptionData()
   at System.Management.Automation.Host.PSHostUserInterface.CheckSystemTranscript()
   at Microsoft.PowerShell.ConsoleHostUserInterface..ctor(ConsoleHost parent)
   at Microsoft.PowerShell.ConsoleHost..ctor()
   at Microsoft.PowerShell.ConsoleHost.Start(String bannerText, String helpText, Boolean issProvidedExternally)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.
Fatal error. Internal CLR error. (0x80131506)
   at System.Net.Security.SslStream+<ReceiveHandshakeFrameAsync>d__158`1[[System.Net.Security.AsyncReadWriteAdapter, System.Net.Security, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a]].MoveNext()
   at System.Runtime.CompilerServices.AsyncTaskMethodBuilder`1+AsyncStateMachineBox`1[[System.Int32, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e],[System.Net.Security.SslStream+<ReceiveHandshakeFrameAsync>d__158`1[[System.Net.Security.AsyncReadWriteAdapter, System.Net.Security, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a]], System.Net.Security, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a]].ExecutionContextCallback(System.Object)
   at System.Threading.ExecutionContext.RunInternal(System.Threading.ExecutionContext, System.Threading.ContextCallback, System.Object)
   at System.Runtime.CompilerServices.AsyncTaskMethodBuilder`1+AsyncStateMachineBox`1[[System.Int32, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e],[System.Net.Security.SslStream+<ReceiveHandshakeFrameAsync>d__158`1[[System.Net.Security.AsyncReadWriteAdapter, System.Net.Security, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a]], System.Net.Security, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a]].MoveNext(System.Threading.Thread)
   at System.Runtime.CompilerServices.AsyncTaskMethodBuilder`1+AsyncStateMachineBox`1[[System.Int32, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e],[System.Net.Security.SslStream+<ReceiveHandshakeFrameAsync>d__158`1[[System.Net.Security.AsyncReadWriteAdapter, System.Net.Security, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a]], System.Net.Security, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a]].MoveNext()
   at System.Net.Security.SslStream+<EnsureFullTlsFrameAsync>d__168`1[[System.Net.Security.AsyncReadWriteAdapter, System.Net.Security, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a]].MoveNext()
   at System.Runtime.CompilerServices.PoolingAsyncValueTaskMethodBuilder`1+StateMachineBox`1[[System.Int32, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e],[System.Net.Security.SslStream+<EnsureFullTlsFrameAsync>d__168`1[[System.Net.Security.AsyncReadWriteAdapter, System.Net.Security, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a]], System.Net.Security, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a]].ExecutionContextCallback(System.Object)
←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
   at System.Threading.ExecutionContext.RunInternal(System.Threading.ExecutionContext, System.Threading.ContextCallback, System.Object)
←[31;1m←[0m←[36;1mLine |←[0m
   at System.Runtime.CompilerServices.PoolingAsyncValueTaskMethodBuilder`1+StateMachineBox`1[[System.Int32, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e],[System.Net.Security.SslStream+<EnsureFullTlsFrameAsync>d__168`1[[System.Net.Security.AsyncReadWriteAdapter, System.Net.Security, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a]], System.Net.Security, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a]].MoveNext()←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m

←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
   at System.Net.Sockets.SocketAsyncEventArgs+<>c.<.cctor>b__174_0(UInt32, UInt32, System.Threading.NativeOverlapped*)
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
   at System.Threading.PortableThreadPool+IOCompletionPoller+Callback.Invoke(Event)
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
   at System.Threading.ThreadPoolTypedWorkItemQueue`2[[System.Threading.PortableThreadPool+IOCompletionPoller+Event, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e],[System.Threading.PortableThreadPool+IOCompletionPoller+Callback, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e]].System.Threading.IThreadPoolWorkItem.Execute()←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m

   at System.Threading.ThreadPoolWorkQueue.Dispatch()
   at System.Threading.PortableThreadPool+WorkerThread.WorkerThreadStart()
OperationStopped: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:6
Line |
   6 |  pwsh .\tools\Build-Landers.ps1 -All -Root .\docs -GTM GTM-K58Z4XD -Fo …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | Exception of type 'System.OutOfMemoryException' was thrown.

Process terminated. Process terminated. Process terminated. Process terminated. Process terminated. Process terminated. Process terminated. Process terminated. ←[31;1mSet-Content: ←[0mD:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3←[0m
The type initializer for 'Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry' threw an exception.The type initializer for 'Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry' threw an exception.
←[31;1m←[0m←[36;1mLine |←[0m

Exception of type 'System.OutOfMemoryException' was thrown.
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
   at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)
   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)
   at System.Environment.FailFast(System.String, System.Exception)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)
   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])
System.TypeInitializationException: The type initializer for 'Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry' threw an exception.
 ---> System.TypeInitializationException: The type initializer for 'Microsoft.ApplicationInsights.Extensibility.TelemetryConfiguration' threw an exception.
 ---> System.TypeInitializationException: The type initializer for 'System.Diagnostics.Activity' threw an exception.
 ---> System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at System.Diagnostics.ActivitySource..cctor()
   at System.Diagnostics.ActivitySource..ctor(String name, String version, IEnumerable`1 tags)
   at System.Diagnostics.Activity..cctor()
   --- End of inner exception stack trace ---
   at System.Diagnostics.Activity.get_ForceDefaultIdFormat()
   at Microsoft.ApplicationInsights.Extensibility.TelemetryConfiguration.<>c.<.cctor>b__13_0()
   at Microsoft.ApplicationInsights.ActivityExtensions.TryRun(Action action)
   at Microsoft.ApplicationInsights.Extensibility.TelemetryConfiguration..cctor()
   --- End of inner exception stack trace ---
   at Microsoft.ApplicationInsights.Extensibility.TelemetryConfiguration.CreateDefault()
   at Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry..cctor()
   --- End of inner exception stack trace ---
   at Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry.SendPSCoreStartupTelemetry(String mode, Double parametersUsed)
   at Microsoft.PowerShell.ConsoleHost.Start(String bannerText, String helpText, Boolean issProvidedExternally)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
Line |
Line |
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
Line |
Line |
Line |
Line |
Line |
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Process terminated. Process terminated.
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
     | another process.
Process terminated. Out of memory.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Exception of type 'System.OutOfMemoryException' was thrown.
Process terminated. Line |
   at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
Could not load file or assembly 'Microsoft.ApplicationInsights, Version=2.22.0.997, Culture=neutral, PublicKeyToken=31bf3856ad364e35'. The system cannot find the file specified.
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Process terminated.
Stack overflow.
     | The process cannot access the file
Exception of type 'System.OutOfMemoryException' was thrown.
   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by

Line |
Line |
   at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)     | another process.

Out of memory.
Process terminated. Process terminated.    at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)
Exception of type 'System.OutOfMemoryException' was thrown.
   at System.Environment.FailFast(System.String, System.Exception)
   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)
   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)
   at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)
   at System.Environment.FailFast(System.String, System.Exception)
   at System.Environment.FailFast(System.String, System.Exception)
   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)
   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry.SendPSCoreStartupTelemetry(String mode, Double parametersUsed)
   at Microsoft.PowerShell.ConsoleHost.Start(String bannerText, String helpText, Boolean issProvidedExternally)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)   at System.Environment.FailFast(System.String, System.Exception)

   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])
   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])
System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at Microsoft.PowerShell.ConsoleHost.Start(String bannerText, String helpText, Boolean issProvidedExternally)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)System.IO.FileNotFoundException: Could not load file or assembly 'Microsoft.ApplicationInsights, Version=2.22.0.997, Culture=neutral, PublicKeyToken=31bf3856ad364e35'. The system cannot find the file specified.
File name: 'Microsoft.ApplicationInsights, Version=2.22.0.997, Culture=neutral, PublicKeyToken=31bf3856ad364e35'
   at Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry..cctor()
   at Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry.SendPSCoreStartupTelemetry(String mode, Double parametersUsed)
   at Microsoft.PowerShell.ConsoleHost.Start(String bannerText, String helpText, Boolean issProvidedExternally)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)
   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])
System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry.SendPSCoreStartupTelemetry(String mode, Double parametersUsed)
   at Microsoft.PowerShell.ConsoleHost.Start(String bannerText, String helpText, Boolean issProvidedExternally)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1mLine |←[0m
←[31;1m←[0m←[36;1m←[36;1m   3 | ←[0m ←[36;1mSet-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip←[0m …←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m     | ←[31;1m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m     | ←[31;1mThe process cannot access the file←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1m'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by←[0m
←[31;1m←[0m←[36;1m←[36;1m←[0m←[36;1m←[0m←[36;1m←[31;1m←[31;1m←[36;1m←[31;1m←[36;1m←[31;1m←[36;1m     | ←[31;1manother process.←[0m
   at System.Management.Automation.Runspaces.LocalPipeline.InvokeThreadProc()   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …

     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   at System.Management.Automation.Runspaces.PipelineThread.WorkerProc()     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
   at System.Threading.ExecutionContext.RunInternal(System.Threading.ExecutionContext, System.Threading.ContextCallback, System.Object)     | The process cannot access the file

     | The process cannot access the file 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1'
     | The process cannot access the file

Process terminated. The type initializer for 'Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry' threw an exception.
   at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)
   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)
   at System.Environment.FailFast(System.String, System.Exception)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)
   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])
System.TypeInitializationException: The type initializer for 'Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry' threw an exception.
 ---> System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at Microsoft.ApplicationInsights.Channel.InMemoryTransmitter..ctor(TelemetryBuffer buffer)
   at Microsoft.ApplicationInsights.Channel.InMemoryChannel..ctor()
   at Microsoft.ApplicationInsights.Extensibility.TelemetrySink..ctor(TelemetryConfiguration telemetryConfiguration, ITelemetryChannel telemetryChannel)
   at Microsoft.ApplicationInsights.Extensibility.TelemetryConfiguration..ctor(String instrumentationKey, ITelemetryChannel channel)
   at Microsoft.ApplicationInsights.Extensibility.TelemetryConfiguration.CreateDefault()
   at Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry..cctor()
   --- End of inner exception stack trace ---
   at Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry.SendPSCoreStartupTelemetry(String mode, Double parametersUsed)
   at Microsoft.PowerShell.ConsoleHost.Start(String bannerText, String helpText, Boolean issProvidedExternally)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)Out of memory.
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | because it is being used by another process.
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
   at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)
     | another process.
     | another process.
     | another process.
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
     | another process.
     | another process.
Process terminated.

Line |
The type initializer for 'Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry' threw an exception.The type initializer for 'Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry' threw an exception.Exception of type 'System.OutOfMemoryException' was thrown.Exception of type 'System.OutOfMemoryException' was thrown.   at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)Exception of type 'System.OutOfMemoryException' was thrown.
Exception of type 'System.OutOfMemoryException' was thrown.Exception of type 'System.OutOfMemoryException' was thrown.   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)
An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3








   at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)Out of memory.
   at System.Environment.FailFast(System.String, System.Exception)
Line |
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …

   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])
   at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)   at System.Environment.FailFast(System.String, System.Exception)
System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry..cctor()
   at Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry.SendPSCoreStartupTelemetry(String mode, Double parametersUsed)
   at Microsoft.PowerShell.ConsoleHost.Start(String bannerText, String helpText, Boolean issProvidedExternally)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)     | The process cannot access the file



     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
   at System.Environment.FailFast(System.String, System.Exception)   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)Out of memory.
     | another process.
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)


   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)
   at System.Environment.FailFast(System.String, System.Exception)
   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)

System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at System.Collections.Generic.Dictionary`2.get_Count()
   at System.Management.Automation.Runspaces.PSSnapInHelpers.AnalyzePSSnapInAssembly(Assembly assembly, String name, PSSnapInInfo psSnapInInfo, PSModuleInfo moduleInfo, Dictionary`2& cmdlets, Dictionary`2& aliases, Dictionary`2& providers, String& helpFile)
   at System.Management.Automation.Runspaces.InitialSessionState.ImportPSSnapIn(PSSnapInInfo psSnapInInfo, PSSnapInException& warning)
   at System.Management.Automation.Runspaces.InitialSessionState.CreateDefault2()
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)System.TypeInitializationException: The type initializer for 'Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry' threw an exception.
 ---> System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at Microsoft.ApplicationInsights.Extensibility.TelemetryConfiguration..ctor(String instrumentationKey, ITelemetryChannel channel)
   at Microsoft.ApplicationInsights.Extensibility.TelemetryConfiguration.CreateDefault()
   at Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry..cctor()
   --- End of inner exception stack trace ---
   at Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry.SendPSCoreStartupTelemetry(String mode, Double parametersUsed)
   at Microsoft.PowerShell.ConsoleHost.Start(String bannerText, String helpText, Boolean issProvidedExternally)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])
System.TypeInitializationException: The type initializer for 'Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry' threw an exception.
 ---> System.TypeInitializationException: The type initializer for 'System.DomainNameHelper' threw an exception.
 ---> System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at System.Buffers.SearchValues.TryGetSingleRange[T](ReadOnlySpan`1 values, T& minInclusive, T& maxInclusive)
   at System.Buffers.SearchValues.Create(ReadOnlySpan`1 values)
   at System.DomainNameHelper..cctor()
   --- End of inner exception stack trace ---
   at System.DomainNameHelper.IsValid(ReadOnlySpan`1 hostname, Boolean iri, Boolean notImplicitFile, Int32& length)
   at System.Uri.CheckAuthorityHelper(Char* pString, Int32 idx, Int32 length, ParsingError& err, Flags& flags, UriParser syntax, String& newHost)
   at System.Uri.PrivateParseMinimal()
   at System.Uri.InitializeUri(ParsingError err, UriKind uriKind, UriFormatException& e)
   at System.Uri.CreateThis(String uri, Boolean dontEscape, UriKind uriKind, UriCreationOptions& creationOptions)
   at System.Uri..ctor(String uriString)
   at Microsoft.ApplicationInsights.Extensibility.Implementation.Endpoints.EndpointProvider.GetEndpoint(EndpointName endpointName)
   at Microsoft.ApplicationInsights.Extensibility.Implementation.Endpoints.EndpointContainer..ctor(IEndpointProvider endpointProvider)
   at Microsoft.ApplicationInsights.Extensibility.TelemetryConfiguration..ctor(String instrumentationKey, ITelemetryChannel channel)
   at Microsoft.ApplicationInsights.Extensibility.TelemetryConfiguration.CreateDefault()
   at Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry..cctor()
   --- End of inner exception stack trace ---
   at Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry.SendPSCoreStartupTelemetry(String mode, Double parametersUsed)
   at Microsoft.PowerShell.ConsoleHost.Start(String bannerText, String helpText, Boolean issProvidedExternally)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)   at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)
   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)
   at System.Environment.FailFast(System.String, System.Exception)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)
   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])
System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at Microsoft.PowerShell.ConsoleHost.BindBreakHandler()
   at Microsoft.PowerShell.ConsoleHost.Start(String bannerText, String helpText, Boolean issProvidedExternally)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Line |
Line |
Line |
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Line |
Line |
     | The process cannot access the file
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     | The process cannot access the file
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | another process.
     | The process cannot access the file
     | The process cannot access the file
     | The process cannot access the file
     | another process.
     | The process cannot access the file
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
     | another process.
     | another process.
     | another process.
     | another process.
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
   at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)
   at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)
   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)
   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)
   at System.Environment.FailFast(System.String, System.Exception)
   at System.Environment.FailFast(System.String, System.Exception)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)
   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])
   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])
System.TypeInitializationException: The type initializer for 'Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry' threw an exception.
 ---> System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at System.Buffers.ProbabilisticWithAsciiCharSearchValues`1.IndexOfAny(ReadOnlySpan`1 span)
   at System.DomainNameHelper.IsValid(ReadOnlySpan`1 hostname, Boolean iri, Boolean notImplicitFile, Int32& length)
   at System.Uri.CheckAuthorityHelper(Char* pString, Int32 idx, Int32 length, ParsingError& err, Flags& flags, UriParser syntax, String& newHost)
   at System.Uri.PrivateParseMinimal()
   at System.Uri.InitializeUri(ParsingError err, UriKind uriKind, UriFormatException& e)
   at System.Uri.CreateThis(String uri, Boolean dontEscape, UriKind uriKind, UriCreationOptions& creationOptions)
   at System.Uri..ctor(String uriString)
   at Microsoft.ApplicationInsights.Extensibility.Implementation.Endpoints.EndpointProvider.GetEndpoint(EndpointName endpointName)
   at Microsoft.ApplicationInsights.Extensibility.Implementation.Endpoints.EndpointContainer..ctor(IEndpointProvider endpointProvider)
   at Microsoft.ApplicationInsights.Extensibility.TelemetryConfiguration..ctor(String instrumentationKey, ITelemetryChannel channel)
   at Microsoft.ApplicationInsights.Extensibility.TelemetryConfiguration.CreateDefault()
   at Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry..cctor()
   --- End of inner exception stack trace ---
   at Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry.SendPSCoreStartupTelemetry(String mode, Double parametersUsed)
   at Microsoft.PowerShell.ConsoleHost.Start(String bannerText, String helpText, Boolean issProvidedExternally)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at System.Management.Automation.Runspaces.PSSnapInHelpers.InitializeCoreCmdletsAndProviders(PSSnapInInfo psSnapInInfo, Dictionary`2& cmdlets, Dictionary`2& providers, String helpFile)
   at System.Management.Automation.Runspaces.PSSnapInHelpers.AnalyzePSSnapInAssembly(Assembly assembly, String name, PSSnapInInfo psSnapInInfo, PSModuleInfo moduleInfo, Dictionary`2& cmdlets, Dictionary`2& aliases, Dictionary`2& providers, String& helpFile)
   at System.Management.Automation.Runspaces.InitialSessionState.ImportPSSnapIn(PSSnapInInfo psSnapInInfo, PSSnapInException& warning)
   at System.Management.Automation.Runspaces.InitialSessionState.CreateDefault2()
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)   at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)
   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)
   at System.Environment.FailFast(System.String, System.Exception)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)
   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])
System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at System.SpanHelpers.NonPackedIndexOfValueType[TValue,TNegator](TValue& searchSpace, TValue value, Int32 length)
   at System.Enum.IsDefinedPrimitive[TStorage](RuntimeType enumType, TStorage value)
   at System.RuntimeType.IsEnumDefined(Object value)
   at Microsoft.Win32.RegistryKey.GetValueKind(String name)
   at System.Management.Automation.Platform.get_IsIoT()
   at System.Management.Automation.Platform.get_IsWindowsDesktop()
   at Microsoft.PowerShell.TaskbarJumpList.CreateRunAsAdministratorJumpList()
   at Microsoft.PowerShell.ConsoleHost.Start(String bannerText, String helpText, Boolean issProvidedExternally)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)format-default: Exception of type 'System.OutOfMemoryException' was thrown.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |

   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by

Out of memory.

     | another process.
An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.



An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.
An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
   at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)
   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)
   at System.Environment.FailFast(System.String, System.Exception)
Stack overflow.
Stack overflow.
An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.Stack overflow.
Stack overflow.

Stack overflow.
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)


Out of memory.
   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])
System.OutOfMemoryException: Exception of type 'System.OutOfMemoryException' was thrown.
   at Microsoft.PowerShell.ConsoleHostUserInterface..ctor(ConsoleHost parent)
   at Microsoft.PowerShell.ConsoleHost..ctor()
   at Microsoft.PowerShell.ConsoleHost.Start(String bannerText, String helpText, Boolean issProvidedExternally)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)Stack overflow.
An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.   at System.Collections.Generic.List`1[[System.__Canon, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e]].System.Collections.Generic.IEnumerable<T>.GetEnumerator()
   at Microsoft.ApplicationInsights.Metrics.MetricManager.TrackMetricAggregates(Microsoft.ApplicationInsights.Metrics.Extensibility.AggregationPeriodSummary, Boolean)

   at System.Threading.ExecutionContext.RunFromThreadPoolDispatchLoop(System.Threading.Thread, System.Threading.ExecutionContext, System.Threading.ContextCallback, System.Object)Out of memory.
   at System.Threading.Tasks.Task.ExecuteWithThreadLocal(System.Threading.Tasks.Task ByRef, System.Threading.Thread)
   at System.Threading.ThreadPoolWorkQueue.Dispatch()
   at System.Threading.PortableThreadPool+WorkerThread.WorkerThreadStart()
Stack overflow.

Stack overflow.
An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.Stack overflow.


An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.Out of memory.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.Out of memory.
OperationStopped: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:6

Line |
Out of memory.
   6 |  pwsh .\tools\Build-Landers.ps1 -All -Root .\docs -GTM GTM-K58Z4XD -Fo …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | Exception of type 'System.OutOfMemoryException' was thrown.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.
Fatal error.
   at Microsoft.ApplicationInsights.Extensibility.Implementation.Tracing.SelfDiagnostics.SelfDiagnosticsConfigRefresher.Worker(System.Threading.CancellationToken)   at System.Threading.Tasks.Task`1[[System.__Canon, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e]].InnerInvoke()
   at System.Threading.ExecutionContext.RunFromThreadPoolDispatchLoop(System.Threading.Thread, System.Threading.ExecutionContext, System.Threading.ContextCallback, System.Object)   at System.Threading.Tasks.Task.ExecuteWithThreadLocal(System.Threading.Tasks.Task ByRef, System.Threading.Thread)   at System.Threading.ThreadPoolWorkQueue.Dispatch()   at System.Threading.PortableThreadPool+WorkerThread.WorkerThreadStart()

Stack overflow.
Stack overflow.
Stack overflow.
   at System.Runtime.ExceptionServices.ExceptionDispatchInfo.Throw()
   at System.Net.Sockets.NetworkStream.Dispose(Boolean)
   at System.Threading.Tasks.Sources.ManualResetValueTaskSourceCore`1[[System.Int32, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e]].ThrowForFailedGetResult()
An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.   at System.IO.Stream.Close()

   at System.Threading.Tasks.Sources.ManualResetValueTaskSourceCore`1[[System.Int32, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e]].GetResult(Int16)

   at System.Net.Security.AuthenticatedStream.Dispose(Boolean)
   at System.Threading.Thread.StartCore()
OperationStopped: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:6
Stack overflow.
   at System.Runtime.CompilerServices.PoolingAsyncValueTaskMethodBuilder`1+StateMachineBox`1[[System.Int32, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e],[System.Net.Security.SslStream+<EnsureFullTlsFrameAsync>d__168`1[[System.Net.Security.AsyncReadWriteAdapter, System.Net.Security, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a]], System.Net.Security, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a]].System.Threading.Tasks.Sources.IValueTaskSource<TResult>.GetResult(Int16)   at System.Net.Security.SslStream.Dispose(Boolean)An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.Out of memory.
   at System.Threading.PortableThreadPool+WorkerThread.MaybeAddWorkingWorker(System.Threading.PortableThreadPool)Line |
Fatal error.


Internal CLR error. (0x80131506)   6 |  pwsh .\tools\Build-Landers.ps1 -All -Root .\docs -GTM GTM-K58Z4XD -Fo …
OperationStopped: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:6


   at System.Runtime.EH.DispatchEx(System.Runtime.StackFrameIterator ByRef, ExInfo ByRef)   at System.IO.Stream.Close()Line |
   at System.Threading.ThreadPool.RequestWorkerThread()
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
   at System.Management.Automation.NativeCommandProcessor.NewParameterBinderController(System.Management.Automation.Internal.InternalCommand)
Out of memory.

   6 |  pwsh .\tools\Build-Landers.ps1 -All -Root .\docs -GTM GTM-K58Z4XD -Fo …
   at System.Net.Security.SslStream+<ReadAsyncInternal>d__170`1[[System.Net.Security.AsyncReadWriteAdapter, System.Net.Security, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a]].MoveNext()     | Exception of type 'System.OutOfMemoryException' was thrown.

   at System.Threading.ThreadPoolWorkQueue.Dispatch()   at System.Management.Automation.NativeCommandProcessor.get_NativeParameterBinderController()     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

   at System.Collections.Generic.List`1[[System.__Canon, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e]].ForEach(System.Action`1<System.__Canon>)
   at System.Runtime.EH.RhRethrow(ExInfo ByRef, ExInfo ByRef)     | Exception of type 'System.OutOfMemoryException' was thrown.

   at System.Management.Automation.NativeCommandProcessor.Prepare(System.Collections.IDictionary)
   at System.Runtime.CompilerServices.PoolingAsyncValueTaskMethodBuilder`1+StateMachineBox`1[[System.Int32, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e],[System.Net.Security.SslStream+<ReadAsyncInternal>d__170`1[[System.Net.Security.AsyncReadWriteAdapter, System.Net.Security, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a]], System.Net.Security, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a]].ExecutionContextCallback(System.Object)   at System.Threading.PortableThreadPool+WorkerThread.WorkerThreadStart()
   at System.Management.Automation.CommandProcessorBase.DoPrepare(System.Collections.IDictionary)   at System.Net.Security.SslStream+<ReadAsyncInternal>d__170`1[[System.Net.Security.AsyncReadWriteAdapter, System.Net.Security, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a]].MoveNext()   at System.Threading.ExecutionContext.RunFromThreadPoolDispatchLoop(System.Threading.Thread, System.Threading.ExecutionContext, System.Threading.ContextCallback, System.Object)   at System.Threading.ExecutionContext.RunInternal(System.Threading.ExecutionContext, System.Threading.ContextCallback, System.Object)   at System.Management.Automation.Internal.PipelineProcessor.Start(Boolean)   at System.Runtime.CompilerServices.PoolingAsyncValueTaskMethodBuilder`1+StateMachineBox`1[[System.Int32, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e],[System.Net.Security.SslStream+<ReadAsyncInternal>d__170`1[[System.Net.Security.AsyncReadWriteAdapter, System.Net.Security, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a]], System.Net.Security, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a]].ExecutionContextCallback(System.Object)

   at System.Management.Automation.Internal.PipelineProcessor.SynchronousExecuteEnumerate(System.Object)   at System.Runtime.CompilerServices.PoolingAsyncValueTaskMethodBuilder`1+StateMachineBox`1[[System.Int32, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e],[System.Net.Security.SslStream+<ReadAsyncInternal>d__170`1[[System.Net.Security.AsyncReadWriteAdapter, System.Net.Security, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a]], System.Net.Security, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a]].MoveNext()   at System.Threading.Tasks.Task.ExecuteWithThreadLocal(System.Threading.Tasks.Task ByRef, System.Threading.Thread)   at System.Threading.ExecutionContext.RunInternal(System.Threading.ExecutionContext, System.Threading.ContextCallback, System.Object)   at System.Management.Automation.PipelineOps.InvokePipeline(System.Object, Boolean, System.Management.Automation.CommandParameterInternal[][], System.Management.Automation.Language.CommandBaseAst[], System.Management.Automation.CommandRedirection[][], System.Management.Automation.Language.FunctionContext)



   at System.Management.Automation.Interpreter.ActionCallInstruction`6[[System.__Canon, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e],[System.Boolean, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e],[System.__Canon, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e],[System.__Canon, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e],[System.__Canon, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e],[System.__Canon, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e]].Run(System.Management.Automation.Interpreter.InterpretedFrame)
   at System.Runtime.CompilerServices.PoolingAsyncValueTaskMethodBuilder`1+StateMachineBox`1[[System.Int32, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e],[System.Net.Security.SslStream+<ReadAsyncInternal>d__170`1[[System.Net.Security.AsyncReadWriteAdapter, System.Net.Security, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a]], System.Net.Security, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a]].MoveNext()   at System.Threading.ThreadPoolWorkQueue.Dispatch()   at System.Net.Security.SslStream+<EnsureFullTlsFrameAsync>d__168`1[[System.Net.Security.AsyncReadWriteAdapter, System.Net.Security, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a]].MoveNext()


   at System.Management.Automation.Interpreter.EnterTryCatchFinallyInstruction.Run(System.Management.Automation.Interpreter.InterpretedFrame)   at System.Net.Security.SslStream+<EnsureFullTlsFrameAsync>d__168`1[[System.Net.Security.AsyncReadWriteAdapter, System.Net.Security, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a]].MoveNext()   at System.Management.Automation.Interpreter.EnterTryCatchFinallyInstruction.Run(System.Management.Automation.Interpreter.InterpretedFrame)ResourceUnavailable: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:9
   at System.Runtime.CompilerServices.PoolingAsyncValueTaskMethodBuilder`1+StateMachineBox`1[[System.Int32, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e],[System.Net.Security.SslStream+<EnsureFullTlsFrameAsync>d__168`1[[System.Net.Security.AsyncReadWriteAdapter, System.Net.Security, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a]], System.Net.Security, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a]].ExecutionContextCallback(System.Object)   at System.Runtime.CompilerServices.PoolingAsyncValueTaskMethodBuilder`1+StateMachineBox`1[[System.Int32, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e],[System.Net.Security.SslStream+<EnsureFullTlsFrameAsync>d__168`1[[System.Net.Security.AsyncReadWriteAdapter, System.Net.Security, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a]], System.Net.Security, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a]].ExecutionContextCallback(System.Object)   at System.Threading.PortableThreadPool+WorkerThread.WorkerThreadStart()Line |
   at System.Management.Automation.Interpreter.Interpreter.Run(System.Management.Automation.Interpreter.InterpretedFrame)

   9 |  pwsh .\tools\Build-Landers.ps1 -All -Root .\docs -GTM GTM-K58Z4XD -Dr …


   at System.Management.Automation.Interpreter.LightLambda.RunVoid1[[System.__Canon, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e]](System.__Canon)
   at System.Threading.ExecutionContext.RunInternal(System.Threading.ExecutionContext, System.Threading.ContextCallback, System.Object)     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

   at System.Management.Automation.DlrScriptCommandProcessor.RunClause(System.Action`1<System.Management.Automation.Language.FunctionContext>, System.Object, System.Object)
   at System.Runtime.CompilerServices.PoolingAsyncValueTaskMethodBuilder`1+StateMachineBox`1[[System.Int32, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e],[System.Net.Security.SslStream+<EnsureFullTlsFrameAsync>d__168`1[[System.Net.Security.AsyncReadWriteAdapter, System.Net.Security, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a]], System.Net.Security, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a]].MoveNext()   at System.Threading.ExecutionContext.RunInternal(System.Threading.ExecutionContext, System.Threading.ContextCallback, System.Object)     | Program 'pwsh.exe' failed to run: Exception of type 'System.OutOfMemoryException' was thrown.At
   at System.Management.Automation.DlrScriptCommandProcessor.Complete()


     | D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:9 char:1 + pwsh
   at System.Management.Automation.CommandProcessorBase.DoComplete()
   at System.Runtime.CompilerServices.PoolingAsyncValueTaskMethodBuilder`1+StateMachineBox`1[[System.Int32, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e],[System.Net.Security.SslStream+<EnsureFullTlsFrameAsync>d__168`1[[System.Net.Security.AsyncReadWriteAdapter, System.Net.Security, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a]], System.Net.Security, Version=9.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a]].MoveNext()   at System.Net.Sockets.SocketAsyncEventArgs+<>c.<.cctor>b__174_0(UInt32, UInt32, System.Threading.NativeOverlapped*)     | .\tools\Build-Landers.ps1 -All -Root .\docs -GTM GTM-K58Z4XD -Dr … +
   at System.Management.Automation.Internal.PipelineProcessor.DoCompleteCore(System.Management.Automation.CommandProcessorBase)


     | ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~.
   at System.Management.Automation.Internal.PipelineProcessor.SynchronousExecuteEnumerate(System.Object)
   at System.Threading.PortableThreadPool+IOCompletionPoller+Callback.Invoke(Event)   at System.Net.Sockets.SocketAsyncEventArgs+<>c.<.cctor>b__174_0(UInt32, UInt32, System.Threading.NativeOverlapped*)   at System.Management.Automation.Runspaces.LocalPipeline.InvokeHelper()


   at System.Management.Automation.Runspaces.LocalPipeline.InvokeThreadProc()
   at System.Threading.PortableThreadPool+IOCompletionPoller+Callback.Invoke(Event)   at System.Threading.ThreadPoolTypedWorkItemQueue`2[[System.Threading.PortableThreadPool+IOCompletionPoller+Event, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e],[System.Threading.PortableThreadPool+IOCompletionPoller+Callback, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e]].System.Threading.IThreadPoolWorkItem.Execute()   at System.Management.Automation.Runspaces.PipelineThread.WorkerProc()


   at System.Threading.ExecutionContext.RunInternal(System.Threading.ExecutionContext, System.Threading.ContextCallback, System.Object)
   at System.Threading.ThreadPoolTypedWorkItemQueue`2[[System.Threading.PortableThreadPool+IOCompletionPoller+Event, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e],[System.Threading.PortableThreadPool+IOCompletionPoller+Callback, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e]].System.Threading.IThreadPoolWorkItem.Execute()   at System.Threading.ThreadPoolWorkQueue.Dispatch()

   at System.Threading.PortableThreadPool+WorkerThread.WorkerThreadStart()
   at System.Threading.ThreadPoolWorkQueue.Dispatch()
   at System.Threading.PortableThreadPool+WorkerThread.WorkerThreadStart()Stack overflow.

Fatal error. An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.
Fatal error. Stack overflow.
Stack overflow.

Fatal error.    at System.Net.Http.HttpConnectionPool.CleanCacheAndDisposeIfUnused()
   at System.Threading.Thread.StartCore()
Stack overflow.
Stack overflow.
Stack overflow.
An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
   at System.Net.Http.HttpConnectionPoolManager.RemoveStalePools()
   at System.Threading.PortableThreadPool+WorkerThread.MaybeAddWorkingWorker(System.Threading.PortableThreadPool)

Fatal error. Out of memory.
   at System.Runtime.CompilerServices.AsyncTaskMethodBuilder`1[[System.Threading.Tasks.VoidTaskResult, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e]].GetStateMachineBox[[Microsoft.ApplicationInsights.Extensibility.Implementation.Tracing.SelfDiagnostics.SelfDiagnosticsConfigRefresher+<Worker>d__12, Microsoft.ApplicationInsights, Version=2.22.0.997, Culture=neutral, PublicKeyToken=31bf3856ad364e35]](<Worker>d__12 ByRef, System.Threading.Tasks.Task`1<System.Threading.Tasks.VoidTaskResult> ByRef)An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.Stack overflow.
Stack overflow.
Stack overflow.
Stack overflow.
Stack overflow.
   at System.Threading.Lock.TryEnterSlow(Int32, ThreadId)
Fatal error.
   at System.Net.Http.HttpConnectionPoolManager+<>c.<.ctor>b__11_0(System.Object)Fatal error. Out of memory.
   at System.Threading.ThreadPool.RequestWorkerThread()Fatal error. Fatal error. Internal CLR error. (0x80131506)
Out of memory.
   at System.Runtime.EH.DispatchEx(System.Runtime.StackFrameIterator ByRef, ExInfo ByRef)


Internal CLR error. (0x80131506)
   at System.Runtime.CompilerServices.AsyncTaskMethodBuilder`1[[System.Threading.Tasks.VoidTaskResult, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e]].AwaitUnsafeOnCompleted[[System.Runtime.CompilerServices.ConfiguredTaskAwaitable+ConfiguredTaskAwaiter, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e],[Microsoft.ApplicationInsights.Extensibility.Implementation.Tracing.SelfDiagnostics.SelfDiagnosticsConfigRefresher+<Worker>d__12, Microsoft.ApplicationInsights, Version=2.22.0.997, Culture=neutral, PublicKeyToken=31bf3856ad364e35]](ConfiguredTaskAwaiter ByRef, <Worker>d__12 ByRef, System.Threading.Tasks.Task`1<System.Threading.Tasks.VoidTaskResult> ByRef)
An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.   at System.Threading.TimerQueueTimer.Fire(Boolean)



   at System.Runtime.CompilerServices.AsyncTaskMethodBuilder.AwaitUnsafeOnCompleted[[System.Runtime.CompilerServices.ConfiguredTaskAwaitable+ConfiguredTaskAwaiter, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e],[Microsoft.ApplicationInsights.Extensibility.Implementation.Tracing.SelfDiagnostics.SelfDiagnosticsConfigRefresher+<Worker>d__12, Microsoft.ApplicationInsights, Version=2.22.0.997, Culture=neutral, PublicKeyToken=31bf3856ad364e35]](ConfiguredTaskAwaiter ByRef, <Worker>d__12 ByRef)An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.

   at System.Threading.TimerQueue.FireNextTimers()An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
   at System.Runtime.EH.RhThrowEx(System.Object, ExInfo ByRef)
Out of memory.

   at Microsoft.ApplicationInsights.Extensibility.Implementation.Tracing.SelfDiagnostics.SelfDiagnosticsConfigRefresher+<Worker>d__12.MoveNext()
An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
   at System.Net.Http.HttpClient.SendAsync(System.Net.Http.HttpRequestMessage, System.Net.Http.HttpCompletionOption, System.Threading.CancellationToken)
   at System.Threading.Thread.StartCore()
   at System.Threading.ThreadPoolWorkQueue.Dispatch()

Out of memory.
   at System.Runtime.CompilerServices.AsyncMethodBuilderCore.Start[[Microsoft.ApplicationInsights.Extensibility.Implementation.Tracing.SelfDiagnostics.SelfDiagnosticsConfigRefresher+<Worker>d__12, Microsoft.ApplicationInsights, Version=2.22.0.997, Culture=neutral, PublicKeyToken=31bf3856ad364e35]](<Worker>d__12 ByRef)
   at Microsoft.ApplicationInsights.Channel.Transmission+<SendAsync>d__53.MoveNext()
   at System.Threading.PortableThreadPool+WorkerThread.MaybeAddWorkingWorker(System.Threading.PortableThreadPool)
Out of memory.

   at System.Threading.PortableThreadPool+WorkerThread.WorkerThreadStart()
   at System.Runtime.CompilerServices.AsyncTaskMethodBuilder.Start[[Microsoft.ApplicationInsights.Extensibility.Implementation.Tracing.SelfDiagnostics.SelfDiagnosticsConfigRefresher+<Worker>d__12, Microsoft.ApplicationInsights, Version=2.22.0.997, Culture=neutral, PublicKeyToken=31bf3856ad364e35]](<Worker>d__12 ByRef)
   at System.Runtime.CompilerServices.AsyncMethodBuilderCore.Start[[Microsoft.ApplicationInsights.Channel.Transmission+<SendAsync>d__53, Microsoft.ApplicationInsights, Version=2.22.0.997, Culture=neutral, PublicKeyToken=31bf3856ad364e35]](<SendAsync>d__53 ByRef)An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
   at System.Threading.ThreadPool.RequestWorkerThread()
Out of memory.

   at Microsoft.ApplicationInsights.Extensibility.Implementation.Tracing.SelfDiagnostics.SelfDiagnosticsConfigRefresher.Worker(System.Threading.CancellationToken)   at System.Threading.ThreadPoolWorkQueue.Dispatch()   at System.Runtime.CompilerServices.AsyncTaskMethodBuilder`1[[System.__Canon, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e]].Start[[Microsoft.ApplicationInsights.Channel.Transmission+<SendAsync>d__53, Microsoft.ApplicationInsights, Version=2.22.0.997, Culture=neutral, PublicKeyToken=31bf3856ad364e35]](<SendAsync>d__53 ByRef)
Process terminated. Stack overflow.
Out of memory.
   at System.Threading.ThreadPoolWorkQueue.Dispatch()


Stack overflow.
   at System.Threading.Lock.EnterAndGetCurrentThreadId()Could not load file or assembly 'C:\Program Files\PowerShell\7\Microsoft.ApplicationInsights.dll'. The paging file is too small for this operation to complete. (0x800705AF)
   at System.Threading.Tasks.Task`1[[System.__Canon, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e]].InnerInvoke()
   at System.Threading.PortableThreadPool+WorkerThread.WorkerThreadStart()   at Microsoft.ApplicationInsights.Channel.Transmission.SendAsync()

   at System.Environment.FailFast(System.Runtime.CompilerServices.StackCrawlMarkHandle, System.String, System.Runtime.CompilerServices.ObjectHandleOnStack, System.String)   at Interop+Kernel32.Sleep(UInt32)
   at System.Threading.ExecutionContext.RunFromThreadPoolDispatchLoop(System.Threading.Thread, System.Threading.ExecutionContext, System.Threading.ContextCallback, System.Object)
   at System.Threading.TimerQueue.TimerThread()   at System.Threading.PortableThreadPool+WorkerThread.WorkerThreadStart()

   at System.Threading.LowLevelSpinWaiter.Wait(Int32, Int32, Boolean)
   at Microsoft.ApplicationInsights.Channel.InMemoryTransmitter.DequeueAndSend(System.TimeSpan)
Stack overflow.

   at System.Threading.Tasks.Task.ExecuteWithThreadLocal(System.Threading.Tasks.Task ByRef, System.Threading.Thread)
   at System.Environment.FailFast(System.Threading.StackCrawlMark ByRef, System.String, System.Exception, System.String)   at Microsoft.ApplicationInsights.Channel.InMemoryTransmitter.Runner()Fatal error.    at System.Threading.LowLevelLifoSemaphore.Wait(Int32, Boolean)
   at System.Threading.ThreadPoolWorkQueue.Dispatch()

Failed to create RW mapping for RX memory. This can be caused by insufficient memory or hitting the limit of memory mappings on Linux (vm.map_max_count).
   at System.Environment.FailFast(System.String, System.Exception)   at System.Threading.ExecutionContext.RunInternal(System.Threading.ExecutionContext, System.Threading.ContextCallback, System.Object)
   at System.Threading.PortableThreadPool+WorkerThread.WorkerThreadStart()
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(System.String[], Int32)


   at System.Threading.PortableThreadPool+WorkerThread.WorkerThreadStart()
   at Microsoft.PowerShell.ManagedPSEntry.Main(System.String[])
   at System.Threading.Tasks.Task.ExecuteWithThreadLocal(System.Threading.Tasks.Task ByRef, System.Threading.Thread)
System.IO.FileLoadException: Could not load file or assembly 'C:\Program Files\PowerShell\7\Microsoft.ApplicationInsights.dll'. The paging file is too small for this operation to complete. (0x800705AF)
File name: 'C:\Program Files\PowerShell\7\Microsoft.ApplicationInsights.dll'
   at Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry..cctor()
   at Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry.SendPSCoreStartupTelemetry(String mode, Double parametersUsed)
   at Microsoft.PowerShell.ConsoleHost.Start(String bannerText, String helpText, Boolean issProvidedExternally)
   at Microsoft.PowerShell.UnmanagedPSEntry.Start(String[] args, Int32 argc)
An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.
OperationStopped: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:6
Line |
   6 |  pwsh .\tools\Build-Landers.ps1 -All -Root .\docs -GTM GTM-K58Z4XD -Fo …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | Exception of type 'System.OutOfMemoryException' was thrown.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.
Fatal error. The type initializer for 'System.Management.Automation.Language.PSPipeWriterBinder' threw an exception.
Process terminated. Stack overflow.
ParentContainsErrorRecordException: An error occurred while creating the pipeline.
Stack overflow.

The type initializer for 'Microsoft.PowerShell.Telemetry.ApplicationInsightsTelemetry' threw an exception.


Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.

Line |
An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.Out of memory.
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …

Out of memory.
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.
Stack overflow.

The type initializer for 'System.Management.Automation.Internal.ValueStringDecorated' threw an exception.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
Line |
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     | The process cannot access the file
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
Line |
     | The process cannot access the file
     | another process.
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | another process.
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
     | another process.


An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.
An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.
The shell cannot be started. A failure occurred during initialization:
Exception of type 'System.OutOfMemoryException' was thrown.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.


An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.
An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.
Fatal error.
An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.
Fatal error.
An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.
   at Interop+Kernel32.SetLastError(Int32)

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.


An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.
An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.


An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.
An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.
OperationStopped: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:6
Line |
   6 |  pwsh .\tools\Build-Landers.ps1 -All -Root .\docs -GTM GTM-K58Z4XD -Fo …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | Exception of type 'System.OutOfMemoryException' was thrown.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.

Fatal error.
An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.

Out of memory.
Out of memory.
Stack overflow.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.


An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.
Stack overflow.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.


An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.
An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.
   at System.IO.FileSystem.FillAttributeInfo(System.String, WIN32_FILE_ATTRIBUTE_DATA ByRef, Boolean)
An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.
Stack overflow.


An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.
Stack overflow.
Stack overflow.
Fatal error.
An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.
Stack overflow.
   at System.IO.FileSystem.FileExists(System.String)
An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.


An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.
Stack overflow.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.
   at System.IO.File.Exists(System.String)

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.
Stack overflow.
Stack overflow.
   at Microsoft.ApplicationInsights.Extensibility.Implementation.Tracing.SelfDiagnostics.SelfDiagnosticsConfigParser.TryGetConfiguration(System.String ByRef, Int32 ByRef, System.Diagnostics.Tracing.EventLevel ByRef)


An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.

Out of memory.
Out of memory.
   at Microsoft.ApplicationInsights.Extensibility.Implementation.Tracing.SelfDiagnostics.SelfDiagnosticsConfigRefresher.UpdateMemoryMappedFileFromConfiguration()

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.
Stack overflow.
Stack overflow.
   at Microsoft.ApplicationInsights.Extensibility.Implementation.Tracing.SelfDiagnostics.SelfDiagnosticsConfigRefresher+<Worker>d__12.MoveNext()
An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.

Out of memory.
An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.


An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.
   at System.Runtime.CompilerServices.AsyncTaskMethodBuilder`1+AsyncStateMachineBox`1[[System.Threading.Tasks.VoidTaskResult, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e],[Microsoft.ApplicationInsights.Extensibility.Implementation.Tracing.SelfDiagnostics.SelfDiagnosticsConfigRefresher+<Worker>d__12, Microsoft.ApplicationInsights, Version=2.22.0.997, Culture=neutral, PublicKeyToken=31bf3856ad364e35]].ExecutionContextCallback(System.Object)
   at System.Threading.ExecutionContext.RunInternal(System.Threading.ExecutionContext, System.Threading.ContextCallback, System.Object)
An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.

   at System.Runtime.CompilerServices.AsyncTaskMethodBuilder`1+AsyncStateMachineBox`1[[System.Threading.Tasks.VoidTaskResult, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e],[Microsoft.ApplicationInsights.Extensibility.Implementation.Tracing.SelfDiagnostics.SelfDiagnosticsConfigRefresher+<Worker>d__12, Microsoft.ApplicationInsights, Version=2.22.0.997, Culture=neutral, PublicKeyToken=31bf3856ad364e35]].MoveNext(System.Threading.Thread)

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.
   at System.Runtime.CompilerServices.AsyncTaskMethodBuilder`1+AsyncStateMachineBox`1[[System.Threading.Tasks.VoidTaskResult, System.Private.CoreLib, Version=9.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e],[Microsoft.ApplicationInsights.Extensibility.Implementation.Tracing.SelfDiagnostics.SelfDiagnosticsConfigRefresher+<Worker>d__12, Microsoft.ApplicationInsights, Version=2.22.0.997, Culture=neutral, PublicKeyToken=31bf3856ad364e35]].MoveNext()

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.
   at System.Threading.Tasks.AwaitTaskContinuation.RunOrScheduleAction(System.Runtime.CompilerServices.IAsyncStateMachineBox, Boolean)

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.
   at System.Threading.Tasks.Task.RunContinuations(System.Object)
   at System.Threading.Tasks.Task.TrySetResult()
   at System.Threading.Tasks.Task+DelayPromise.CompleteTimedOut()
   at System.Threading.TimerQueueTimer.Fire(Boolean)
   at System.Threading.TimerQueue.FireNextTimers()

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.
   at System.Threading.ThreadPoolWorkQueue.Dispatch()
   at System.Threading.PortableThreadPool+WorkerThread.WorkerThreadStart()
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.
     | The process cannot access the file
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
Line |
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
     | another process.
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
Line |
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     | The process cannot access the file
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
     | The process cannot access the file
     | another process.
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.
Stack overflow.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.


An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.

Out of memory.


An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.

Out of memory.
Out of memory.


An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.
An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.
Stack overflow.
   at System.Threading.LowLevelLock..cctor()
   at System.Threading.LowLevelLock.WaitAndAcquire()
   at System.Threading.PortableThreadPool+WaitThread.ProcessRemovals()
   at System.Threading.PortableThreadPool+WaitThread.WaitThreadStart()
Stack overflow.
Stack overflow.
Stack overflow.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.


An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.
Stack overflow.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.
Stack overflow.
Stack overflow.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.

Out of memory.
An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.
Stack overflow.
Stack overflow.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.



An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.
Stack overflow.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.
OperationStopped: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:6
Line |
   6 |  pwsh .\tools\Build-Landers.ps1 -All -Root .\docs -GTM GTM-K58Z4XD -Fo …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | Exception of type 'System.OutOfMemoryException' was thrown.
Out of memory.
Set-Content: D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1:3
Line |
   3 |  Set-Content .\tools\Build-Landers.ps1 -Encoding UTF8 -Value (Get-Clip …
     |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | The process cannot access the file
     | 'D:\Users\ten77\Documents\GitHub\910cpr-class-landers\tools\Build-Landers.ps1' because it is being used by
     | another process.

An error has occurred that was not properly handled. Additional information is shown below. The PowerShell process will exit.
Out of memory.


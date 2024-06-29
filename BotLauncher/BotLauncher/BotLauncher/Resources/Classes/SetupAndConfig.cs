using System.Configuration;
using System.Diagnostics;
using System.IO;
using System.Windows;

namespace BotLauncher.Resources.Classes
{
     public static class ConfigOperations
     {
          /// <summary>
          /// Set the path of the bot script to a provided path
          /// </summary>
          /// <param name="bot_path">Exact path to the bot python script</param>
          public static void SetBotPath(string bot_path)
          {
               Configuration cfg = ConfigurationManager.OpenExeConfiguration(ConfigurationUserLevel.None);
               cfg.AppSettings.Settings["BotPath"].Value = bot_path;
               cfg.Save(ConfigurationSaveMode.Modified);
               ConfigurationManager.RefreshSection("appSettings");
          }


          /// <summary>
          /// Check if the path of the bot script in the config file exists on the machine
          /// </summary>
          /// <returns>True if the file exists at the currently set path; False if the file doesn't exist at the path</returns>
          public static bool VerifyBotFileExists()
          {
               Configuration cfg = ConfigurationManager.OpenExeConfiguration(ConfigurationUserLevel.None);
               return File.Exists(cfg.AppSettings.Settings["BotPath"].Value);
          }

          /// <summary>
          /// Retrieve the bot path from the app.config file
          /// </summary>
          /// <returns>The bot path that is stored inside the app.config file</returns>
          public static string GetBotPath() 
          {
               Configuration cfg = ConfigurationManager.OpenExeConfiguration(ConfigurationUserLevel.None);
               return cfg.AppSettings.Settings["BotPath"].Value;
          }

          /// <summary>
          /// Check if the bot path exists in the app.config file.
          /// </summary>
          /// <returns>True if a path exists in the app.config; false if there is no path for the bot script in the app.config file.</returns>
          public static bool CheckConfigBotPath()
          {
               Configuration cfg = ConfigurationManager.OpenExeConfiguration(ConfigurationUserLevel.None);
               return cfg.AppSettings.Settings["BotPath"].Value != null;
          }
          

     }


     public static class StartupOperations
     {
          public static bool IsPythonInstalled()
          {
               try
               {
                    ProcessStartInfo si = new()
                    {
                         FileName = "py",
                         Arguments = "--version",
                         RedirectStandardOutput = true,
                         RedirectStandardError = true,
                         UseShellExecute = false,
                         CreateNoWindow = true
                    };

                    using (Process process = new() { StartInfo = si })
                    {
                         process.Start();
                         process.WaitForExit();
                         return process.ExitCode == 0;
                    }
               }
               catch { return false; }
          }

          public static string? GetDefaultPythonPath()
          {
               try
               {
                    ProcessStartInfo si = new()
                    {
                         FileName = "py",
                         Arguments = "-c \"import sys; print(sys.executable)\"",
                         RedirectStandardOutput = true,
                         RedirectStandardError = true,
                         UseShellExecute = false,
                         CreateNoWindow = true
                    };

                    using (Process process = new() { StartInfo = si })
                    {
                         process.Start();
                         string output = process.StandardOutput.ReadToEnd();
                         process.WaitForExit();
                         return output.Trim();
                    }
               }
               catch (Exception ex)
               {
                    MessageBox.Show(
                         $"Failed to retrieve default python path:\n\n{ex.Message}",
                         "Python Error",
                         MessageBoxButton.OK,
                         MessageBoxImage.Error
                    );
                    return null;
               }
          }


          public static void StartupChecklist()
          {
               //this is the default path when downloading the application from the repo
               string DEFAULT_BOT_PATH = $@"{Environment.CurrentDirectory}\Scripts\monkamind.py";

               //check if python is installed
               if (!IsPythonInstalled())
               {
                    MessageBox.Show(
                         "Failed to find a python installtion on the computer, please verify python is installed.",
                         "Python Error",
                         MessageBoxButton.OK,
                         MessageBoxImage.Error
                    );
                    throw new PythonNotInstalled();
               }

               //check if python.exe path can be found
               string? python_path = GetDefaultPythonPath();
               if(python_path == null)
               {
                    MessageBox.Show(
                         "Failed to find the python.exe path for the default python installtion. You may add a custom path to a python.exe through the toolbar.",
                         "Python Error",
                         MessageBoxButton.OK,
                         MessageBoxImage.Error
                    );
                    throw new PythonPathNotResolvable();
               }

               //set the python path if it can be found
               MainWindow.SetDEFAULT_PYTHON_PATH_Variable(python_path);

               //if there is no path to a script for the bot in the app.config file, set it as the default bot script path
               if (!ConfigOperations.CheckConfigBotPath()) { ConfigOperations.SetBotPath(DEFAULT_BOT_PATH); }

               //verify the file set in the bot path section of the app.config actually exists
               if (!ConfigOperations.VerifyBotFileExists())
               {
                    MessageBox.Show(
                         "Bot script file doesn't exist at the currently set configuration path",
                         "Filepath Error",
                         MessageBoxButton.OK,
                         MessageBoxImage.Error
                    );
                    throw new BotScriptDoesnotExist();
               }

               //if both script doesn't exist, return false and notify user to update the path of the bot script

          }
     }
}

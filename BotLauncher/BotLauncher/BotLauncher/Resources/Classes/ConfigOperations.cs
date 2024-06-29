using System.Configuration;
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
          /// Check if the bot path value in the BotPath key inside the app.config file exists or not.
          /// </summary>
          /// <returns>
          /// Boolean value if there is a path in the app.config file as well as if the path does exist in the config
          /// does the path point to a valid/existing file on the local machine
          /// </returns>
          public static bool VerifyBotPath()
          {
               Configuration cfg = ConfigurationManager.OpenExeConfiguration(ConfigurationUserLevel.None);
               //check if the path in the app.config exists
               bool path_exists = cfg.AppSettings.Settings["BotPath"].Value != null ? true : false;
               bool file_exists = false;
               if (path_exists) { file_exists = File.Exists(cfg.AppSettings.Settings["BotPath"].Value) ? true : false; }

               return path_exists && file_exists;
          }

          public static string GetBotPath() 
          {
               Configuration cfg = ConfigurationManager.OpenExeConfiguration(ConfigurationUserLevel.None);
               return cfg.AppSettings.Settings["BotPath"].Value;
          }

     }
}

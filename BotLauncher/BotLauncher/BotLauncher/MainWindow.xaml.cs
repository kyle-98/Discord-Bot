using BotLauncher.Resources.Classes;
using Microsoft.Win32;
using System.Configuration;
using System.IO;
using System.Windows;

namespace BotLauncher
{
     /// <summary>
     /// Interaction logic for MainWindow.xaml
     /// </summary>
     public partial class MainWindow : Window
     {
          /// <summary>
          /// Flag to set the running state of the bot
          /// </summary>
          bool bot_running = false;

          /// <summary>
          /// The default path of the python bot script when downloaded from repo
          /// </summary>
          string DEFAULT_BOT_PATH = $@"{Environment.CurrentDirectory}\Scripts\monkamind.py"; //please let me remember to rename the bot in the repo
          public static string? DEFAULT_PYTHON_PATH;

          public MainWindow()
          {
               InitializeComponent();

               //Run startup checks to verify all things are installed properly
              
          }

          /// <summary>
          /// Allow other classes to edit the <see cref="DEFAULT_PYTHON_PATH"/> variable
          /// </summary>
          /// <param name="value">The value that will be assigned to <see cref="DEFAULT_PYTHON_PATH"/></param>
          public static void SetDEFAULT_PYTHON_PATH_Variable(string? value) => DEFAULT_PYTHON_PATH = value;

          /// <summary>
          /// Check if the bot filepath that is currently saved in the app.config file exists and is valid
          /// </summary>
          /// <param name="bot_path">Exact filepath of the bot</param>
          private void CheckBotFileExist(string bot_path)
          {
               if (!File.Exists(bot_path))
               {
                    MessageBoxResult result = MessageBox.Show(
                         "Bot script not found at selected path. Do you want to cancel the path setting operation and revert to the previous path?\n\nNote: if you select No you will need to set a valid path later for the application to work.",
                         "Path Set Error",
                         MessageBoxButton.YesNo,
                         MessageBoxImage.Error
                    );
                    if (result == MessageBoxResult.No)
                    {
                         StartBotButton.IsEnabled = false;
                         StopBotButton.IsEnabled = false;
                         return;
                    }
                    else { return; }
               }
               else
               {
                    ConfigOperations.SetBotPath(bot_path);
                    StartBotButton.IsEnabled = true;
               }
          }
          
          /// <summary>
          /// Click event from the File => Set Bot Path header. This method calls a prompt to prompt the user to select the file location
          /// of the ptyhon bot script if the user wants to save it to a custom location outside of the install directory
          /// </summary>
          /// <param name="sender">Object that was interacted with for the click event to take place</param>
          /// <param name="e">Event arguments being passed with the click event</param>
          private void SetBotPath_Header_Click(object sender, RoutedEventArgs e)
          {
               OpenFileDialog ofd = new()
               {
                    Title = "Select the python bot script",
                    Filter = "Python Scripts (*.py)|*.py"
               };

               if (ofd.ShowDialog() == true) { CheckBotFileExist(ofd.FileName); }
          }

          private void StartBotButton_Click(object sender, RoutedEventArgs e)
          {
               //attempt to launch python with bot
          }

          private void StopBotButton_Click(object sender, RoutedEventArgs e)
          {

          }

          
     }
}
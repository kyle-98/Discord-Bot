namespace BotLauncher.Resources.Classes
{
     public class PythonNotInstalled : Exception
     {
          public PythonNotInstalled() : base("Python installation not found.") { }
          public PythonNotInstalled(string message) : base(message) { }
          public PythonNotInstalled(string message, Exception inner_exception) : base(message, inner_exception) { }
     }

     public class PythonPathNotResolvable : Exception
     {
          public PythonPathNotResolvable() : base("Default python.exe path not resolvable. Use the toolbar to set a custom path.") { }
          public PythonPathNotResolvable(string message) : base(message) { }
          public PythonPathNotResolvable(string message, Exception inner_exception) : base(message, inner_exception) { }
     }

     public class BotScriptDoesnotExist : Exception
     {
          public BotScriptDoesnotExist() : base("Bot script doesn't exist in bot path location inside the app.config file. Set a custom path to the bot script through the toolbar.") { }
          public BotScriptDoesnotExist(string message) : base(message) { }
          public BotScriptDoesnotExist(string message, Exception inner_exception) : base(message, inner_exception) { }
     }

}

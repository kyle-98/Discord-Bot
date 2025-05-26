from discord.ext.commands import CheckFailure

class NotAdmin(CheckFailure):
    """
    Custom exception class used to prevent users without administrator permissions from access administrator only commands

    Parameters:
        CheckFailure (discord.ext.commands.CheckFailure): The failed administrator permission check
    """
    pass
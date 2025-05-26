import os

# Initialize all cog modules
def get_cog_modules():
    return[
        f'cogs.{file[:-3]}'
        for file in os.listdir(os.path.dirname(__file__))
        if file.endswith('.py') and file != '__init__.py'
    ]

from . recipe import Recipe

class InterfaceEthernet(Recipe):
    def __init__(self, session, command_file):
        super().__init__(session, command_file)

    # Define any custom processing of parameters here

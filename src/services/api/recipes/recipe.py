
class Recipe(object):
    def __init__(self, session, command_file):
        self._session = session
        self._cmd_file = command_file

    def configure(self):
        session = self._session
        cmd_file = self._cmd_file
        try:
            commands = []
            with open(cmd_file) as f:
                lines = f.readlines()
            for line in lines:
                commands.append(line.split())
            for cmd in commands:
                if cmd[0] == 'set':
                    session.set(cmd[1:])
                elif cmd[0] == 'delete':
                    session.delete(cmd[1:])
                else:
                    raise ValueError('Operation must be "set" or "delete"')
            session.commit()
        except Exception as error:
            raise error



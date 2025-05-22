
class AlreadyExistsError(RuntimeError):
    '''Item already exists in database'''
    def __str__(self):
        s = self.__doc__
        if self.args:
            s = '{0}: {1}'.format(s, self.args[0])
        s = '{0}.'.format(s)
        return s

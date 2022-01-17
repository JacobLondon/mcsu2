
class Module:
    def __init__(self):
        pass
    def init(self):
        pass
    def update(self):
        return True
    def cleanup(self):
        pass

    def run(self):
        self.init()
        rv = True
        while rv:
            rv = self.update()
        self.cleanup()

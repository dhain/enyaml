class ExprSyntaxError(SyntaxError):
    def __init__(self, msg, offset=None, text=None):
        SyntaxError.__init__(self, msg, (
            '<expression>', 1, None if offset is None else offset + 1, text
        ))

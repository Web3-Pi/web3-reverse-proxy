import sys
from io import StringIO


class StdOutCaptureStreamTee(StringIO):

    def __init__(self):
        super().__init__()

        self.orig_stdout = sys.stdout
        self.buf = StringIO()
        self.last_line = ""

    # FIXME: a hack tailored to this project only
    def write(self, __s: str) -> int:
        if "\r" in __s and "\n" not in __s:
            self.last_line = __s
        else:
            self.buf.write(__s)

        return self.orig_stdout.write(__s)

    def getvalue(self) -> str:
        return self.buf.getvalue() + self.last_line

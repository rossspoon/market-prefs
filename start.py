import re
import sys
from otree.main import execute_from_command_line

if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw?|\.exe)?$', '', sys.argv[0])
    print(sys.argv)
    sys.exit(execute_from_command_line())

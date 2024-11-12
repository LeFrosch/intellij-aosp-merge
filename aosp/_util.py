import sys


def log(message: str):
    print('-> ' + message)


def log_error(message: str):
    print('-> ERROR: ' + message, file=sys.stderr)
    sys.exit(1)


def ask(question: str) -> bool:
    while True:
        answer = input('-> %s [y/n]' % question)

        if (answer in ['y', 'Y']):
            return True
        if (answer in ['n', 'N']):
            return False


def filter_none(generator):
    return (x for x in generator if x is not None)

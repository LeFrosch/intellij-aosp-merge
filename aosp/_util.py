import sys

from simple_term_menu import TerminalMenu


def log(message: str):
    print('>> ' + message)


def log_error(message: str):
    print('!! ' + message)
    sys.exit(1)


def exit(message: str):
    log(message)
    sys.exit(1)


def ask(question: str) -> bool:
    while True:
        answer = input('?? %s [y/n]' % question)

        if (answer in ['y', 'Y']):
            return True
        if (answer in ['n', 'N']):
            return False


def choose(title: str, options: list[str]) -> str:
    menu = TerminalMenu(options, title='?? ' + title)
    index = menu.show()

    return options[index][1]


def wait(message: str):
    input(':: %s' % message)


def filter_none(generator):
    return (x for x in generator if x is not None)


def first(generator):
    return next(iter(generator), None)

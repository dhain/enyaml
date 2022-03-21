import nox


@nox.session
def lint(session):
    session.install('flake8')
    session.run('flake8', 'src')


@nox.session
def tests(session):
    session.install('.[test]')
    session.run('pytest')


@nox.session
def doctests(session):
    session.install('.[doc]')
    with session.chdir('docs'):
        session.run('make', 'doctest', external=True)

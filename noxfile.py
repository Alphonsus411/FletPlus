import nox


nox.options.sessions = [
    "pytest",
    "ruff",
    "black",
    "mypy",
    "bandit",
    "pip-audit",
    "safety",
]


def _install_deps(session: nox.Session) -> None:
    session.install("-r", "requirements-dev.txt")


@nox.session
def pytest(session: nox.Session) -> None:
    _install_deps(session)
    session.run("python", "-m", "pytest")


@nox.session
def ruff(session: nox.Session) -> None:
    _install_deps(session)
    session.run("python", "-m", "ruff", "check", ".")


@nox.session
def black(session: nox.Session) -> None:
    _install_deps(session)
    session.run("python", "-m", "black", "--check", ".")


@nox.session
def mypy(session: nox.Session) -> None:
    _install_deps(session)
    session.run("python", "-m", "mypy", "fletplus")


@nox.session
def bandit(session: nox.Session) -> None:
    _install_deps(session)
    session.run("python", "-m", "bandit", "-r", "fletplus")


@nox.session(name="pip-audit")
def pip_audit(session: nox.Session) -> None:
    _install_deps(session)
    session.run("python", "-m", "pip_audit")


@nox.session(name="safety")
def safety_check(session: nox.Session) -> None:
    _install_deps(session)
    session.run("python", "-m", "safety", "check")


@nox.session(name="qa")
def qa(session: nox.Session) -> None:
    _install_deps(session)
    session.run("python", "-m", "pytest")
    session.run("python", "-m", "ruff", "check", ".")
    session.run("python", "-m", "black", "--check", ".")
    session.run("python", "-m", "mypy", "fletplus")
    session.run("python", "-m", "bandit", "-r", "fletplus")
    session.run("python", "-m", "pip_audit")
    session.run("python", "-m", "safety", "check")

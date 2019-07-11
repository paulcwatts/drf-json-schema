"""Test scenarios for drf-json-schema."""

import os
import subprocess

import nox
from nox.sessions import Session


# pipenv and tox don't interact very well, they seem to be highly
# dependent on what python/python environment you run nox in.
# So instead of dealing with that, we just convert the lockfile to
# a requirements file and install like that.
def install_pipenv_requirements(session: Session) -> None:
    """Generate a requirements file from pipfile.lock and install those."""
    OUTFILE = os.path.join(".nox", "reqs.txt")

    session.install("pipenv")
    reqs = subprocess.check_output(["pipenv", "lock", "--dev", "-r"])

    with open(OUTFILE, "wb+") as f:
        f.write(reqs)

    session.install("-r", OUTFILE)


if os.environ.get("CI"):
    # On Travis, we allow Travis to set the Python version
    nox_session = nox.session
else:
    nox_session = nox.session(python=["3.6", "3.7"])


@nox_session
@nox.parametrize("django", ["2.0", "2.1", "2.2"])
@nox.parametrize("drf", ["3.8", "3.9"])
def test(session: Session, django: str, drf: str) -> None:
    """Run unit tests."""
    install_pipenv_requirements(session)
    session.install(f"django=={django}")
    session.install(f"djangorestframework=={drf}")
    session.run(
        "py.test",
        "--flake8",
        "--cov=rest_framework_json_schema",
        "--cov-append",
        "rest_framework_json_schema/",
        "tests/",
        env={"PYTHONPATH": "."},
    )


@nox.session
def black(session: Session) -> None:
    """Check black."""
    session.install("black==19.3b0")
    session.run("black", "--check", ".")


@nox.session
def mypy(session: Session) -> None:
    """Check mypy."""
    session.install("mypy")
    session.run("mypy", ".")


@nox.session
def pydocstyle(session: Session) -> None:
    """Check docstrings."""
    session.install("pydocstyle")
    session.run("pydocstyle")

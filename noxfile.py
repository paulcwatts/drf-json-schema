import os
import subprocess

import nox


# pipenv and tox don't interact very well, they seem to be highly
# dependent on what python/python environment you run nox in.
# So instead of dealing with that, we just convert the lockfile to
# a requirements file and install like that.
def install_pipenv_requirements(session):
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
def test(session, django, drf):
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
def black(session):
    session.install("black==19.3b0")
    session.run("black", "--check", ".")

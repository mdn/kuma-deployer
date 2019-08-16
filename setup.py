from os import path

from setuptools import find_packages, setup

_here = path.dirname(__file__)


dev_requirements = ["black==19.3b0", "flake8==3.7.8"]  # "flake8-import-order==0.18.1"

setup(
    name="kuma-deployer",
    version="0.0.1",
    author="Peter Bengtsson",
    author_email="mail@peterbe.com",
    url="https://github.com/mdn/kuma-deployer",
    description="https://kuma.readthedocs.io/en/latest/deploy.html as a script",
    long_description=open(path.join(_here, "README.md")).read(),
    long_description_content_type="text/markdown",
    license="MPL 2.0",
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: Implementation :: CPython",
        "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
    ],
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=["GitPython", "click", "PyGithub", "python-decouple", "requests"],
    extras_require={"dev": dev_requirements},
    entry_points="""
        [console_scripts]
        kuma-deployer=deployer.main:cli
    """,
    setup_requires=[],
    tests_require=["pytest"],
    keywords="git github submodule",
)

from setuptools import find_packages, setup

setup(
    name="swcol",
    version="0.0.10",
    description="Switch: Electricity Planning Model applied to Colombia",
    package_dir={"":"app"},
    packages=find_packages(where="app"),
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/Greater-Gold/switch-colombia",
    author="Juan José Dorado",
    author_email="juanjosedoradom@gmail.com",
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "numpy",
        "pandas",
        "matplotlib",
        "kaleido"
    ],
    python_requires='>=3.9',
)
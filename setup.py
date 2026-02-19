from setuptools import setup, find_packages

setup(
    name="hydra-cred-tester",
    version="0.1.0",
    description="Expandable credential testing tool with plugin architecture",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=["requests>=2.28.0"],
    entry_points={"console_scripts": ["hydra=hydra:main"]},
)

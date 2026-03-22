from setuptools import setup, find_packages

setup(
    name="iacguard",
    version="0.1.0",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=["colorama"],
    entry_points={"console_scripts": ["iacguard=iacguard.cli:main"]},
    author="IACGuard",
    description="Terraform pre-apply risk and blast radius analyzer",
)

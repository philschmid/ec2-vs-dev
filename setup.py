from __future__ import absolute_import
import os
from datetime import date
from setuptools import find_packages, setup

# We don't declare our dependency on transformers here because we build with
# different packages for different variants

VERSION = "1.0.2"

install_requires = [
    "boto3",
    "sshconf",
]

extras = {}

extras["quality"] = [
    "black==21.4b0",
    "isort>=5.5.4",
    "flake8>=3.8.3",
]

setup(
    name="ec2ssh",
    version=VERSION,
    author="Philipp",
    description="A CLI to start or stop ec2 instances and update the ssh config",
    url="https://github.com/aws/sagemaker-huggingface-inference-toolkit",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=install_requires,
    extras_require=extras,
    entry_points={"console_scripts": "ec2ssh=ec2ssh.main:main"},
    python_requires=">=3.6.0",
    license="Apache License 2.0",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
)

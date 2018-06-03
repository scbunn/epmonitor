"""
Synthetic endpoint monitoring

"""
from setuptools import setup

setup(
    name="SyntheticMonitor",
    version="0.1.0",
    url="https://github.com/scbunn/epmonitor",
    author="Stephen Bunn",
    author_email="scbunn@sbunn.org",
    description="Synthetic endpoint monitoring",
    long_description=__doc__,
    packages=['webapp'],
    include_package_data=True,
    setup_requires=[
        'pytest-runner',
    ],
    install_requires=[
        'flask',
        'python-dotenv',
        'flask-sqlalchemy',
        'SQLAlchemy-Utils',
        'flask-migrate',
        'psycopg2-binary',
        'python-slugify',
        'requests',
        'sqlalchemy-json',
        'flask-wtf',
        'flask-moment',
        'numpy',
        'psutil'
    ],
    tests_require=[
        'pytest',
        'pytest-cov',
        'pytest-spec',
        'flake8',
    ],
)

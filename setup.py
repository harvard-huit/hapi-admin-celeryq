from setuptools import setup, find_packages

setup(name='adexk8s-migration-celeryq',
      version='0.0',
      packages= find_packages(),
      install_requires=[
          'google-api-python-client==2.88.0',
      ],
)
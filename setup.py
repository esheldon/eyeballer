import os
from distutils.core import setup

scripts=['make-se-eyeball.py']
scripts=[os.path.join('bin',s) for s in scripts]

setup(name="eyeballer", 
      version="0.1.0",
      description="Python code to make cutouts for eyeballing",
      license = "GPL",
      author="Erin Scott Sheldon",
      author_email="erin.sheldon@gmail.com",
      packages=['eyeballer'],
      scripts=scripts)


import os
import glob
from distutils.core import setup

scripts=['make-se-eyeball.py','make-se-eyeball-full.py']
scripts=[os.path.join('bin',s) for s in scripts]

config_files=glob.glob('config/*.yaml')

data_files=[]
for f in config_files:
    d=os.path.dirname(f)
    n=os.path.basename(f)
    d=os.path.join('share',d)

    data_files.append( (d,[f]) )


setup(name="eyeballer", 
      version="0.1.0",
      description="Python code to make cutouts for eyeballing",
      license = "GPL",
      author="Erin Scott Sheldon",
      author_email="erin.sheldon@gmail.com",
      packages=['eyeballer'],
      data_files=data_files,
      scripts=scripts)


import os
import glob
from distutils.core import setup

scripts=['make-se-eyeball.py',
         'make-se-eyeball-full.py',
         'make-scripts.py',
         'make-db.py']
scripts=[os.path.join('bin',s) for s in scripts]

config_files=glob.glob('config/*.yaml')

data_files=[]
for f in config_files:
    n=os.path.basename(f)
    d=os.path.join('share','eyeball-config')

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


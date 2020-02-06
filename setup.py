import sys
import subprocess

from distutils.core import setup, Command

setup(name='nixops-vbox',
      version='@version@',
      description='NixOps backend for VirtualBox',
      url='https://github.com/AmineChikhaoui/nixops-vbox',
      maintainer='Amine Chikhaoui',
      maintainer_email='amine.chikhaoui91@gmail.com',
      packages=['nixopsvbox', 'nixopsvbox.backends', 'nixopsvbox.resources'],
      entry_points={'nixops': ['vbox = nixopsvbox.plugin']},
      py_modules=['plugin']
)

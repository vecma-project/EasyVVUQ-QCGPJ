#!/usr/bin/env python
from livereload import Server, shell
server = Server()
server.watch('*.rst', shell('make html', cwd='.'))
server.watch('tutorials/*.rst', shell('make html', cwd='.'))
server.watch('tutorials/cooling_cup/guide/*.rst', shell('make html', cwd='.'))
server.serve(root='_build/html')
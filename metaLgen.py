from metaL import *

p = Project(
    title='generative metaprogramming interpreter',
    about='''
* homoiconic language targets automated code synthesis
* compiles to high-level languages
* easy integration with any existing infrastructure
''') \
    | metaL()

p.sync()

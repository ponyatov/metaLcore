#!/usr/bin/env python3

## @file
## @brief generative metaprogramming interpreter

import os, sys, re, time
import datetime as dt

## @defgroup core

## @brief   Object HyperGraph node = Marvin Minsky's Frame
## @details base program=data structure the same as lists in Lisp
## @ingroup core
class Object:
    def __init__(self, V):
        ## type/class tag /required for PLY/
        self.type = self.tag()
        ## scalar: object name, string/number value
        self.value = V
        ## associative array = map = env/namespace = attributes
        self.slot = {}
        ## ordered container = vector = stack = AST sub-edges
        self.nest = []
        ## unical global id
        self.gid = id(self)

    ## Python types wrapper
    def box(self, that):
        if isinstance(that, Object): return that
        if isinstance(that, str): return S(that)
        raise TypeError(['box', type(that), that])

    ## @name text dump & serialization

    ## pytest callback
    def test(self):
        return self.dump(test=True)

    ## `print` callback
    def __repr__(self):
        return self.dump(test=False)

    ## full text tree dump
    def dump(self, cycle=[], depth=0, prefix='', test=False):
        # head
        def pad(depth): return '\n' + '\t' * depth
        ret = pad(depth) + self.head(prefix, test)
        # cycles block
        if not depth: cycle = [] # init
        if self in cycle: return ret + ' _/'
        else: cycle.append(self)
        # slot{}s
        for i in self.keys():
            ret += self[i].dump(cycle, depth + 1, f'{i} = ', test)
        # nest[]ed
        for j, k in enumerate(self):
            ret += k.dump(cycle, depth + 1, f'{j}: ', test)
        # subtree
        return ret

    ## short `<T:V>` header
    def head(self, prefix='', test=False):
        gid = '' if test else f' @{self.gid:x}'
        return f'{prefix}<{self.tag()}:{self.val()}>{gid}'

    def tag(self):
        return self.__class__.__name__.lower()

    def val(self):
        return f'{self.value}'

    def __format__(self, spec=''):
        if not spec: return f'{self.value}'
        if spec == 'l': return f'{self.value.lower()}'
        raise TypeError(['__format__', spec])

    ## @name operator

    ## get slot names in order
    def keys(self):
        return sorted(self.slot.keys())

    ## iterate over subtree
    def __iter__(self):
        return iter(self.nest)

    ## `A[key]` get from slot
    def __getitem__(self, key):
        if isinstance(key, str): return self.slot[key]
        if isinstance(key, int): return self.nest[key]
        raise TypeError(['__getitem__', type(key), key])

    ## `A[key] = B` set slot
    def __setitem__(self, key, that):
        that = self.box(that)
        if isinstance(key, str): self.slot[key] = that; return self
        raise TypeError(['__setitem__', type(key), key])

    ## `A << B ~> A[B.type] = B`
    def __lshift__(self, that):
        that = self.box(that)
        return self.__setitem__(that.tag(), that)

    ## `A >> B ~> A[B.value] = B`
    def __rshift__(self, that):
        that = self.box(that)
        return self.__setitem__(that.val(), that)

    ## `A // B ~> A.push(B)` push as stack
    def __floordiv__(self, that):
        that = self.box(that)
        self.nest.append(that); return self

    ## insert at index
    def ins(self, idx, that):
        assert isinstance(idx, int)
        that = self.box(that)
        self.nest.insert(idx, that); return self

    ## remove given object
    def remove(self, that):
        assert isinstance(that, Object)
        ret = []
        for i in self:
            if i != that: ret.append(i)
        self.nest = ret; return self

    ## insert `that` before `where`
    def before(self, where, that):
        assert isinstance(where, Object)
        that = self.box(that)
        ret = []
        for i in self:
            if i == where: ret.append(that)
            ret.append(i)
        self.nest = ret; return self

    ## insert `that` after `where`
    def after(self, where, that):
        assert isinstance(where, Object)
        that = self.box(that)
        ret = []
        for i in self:
            ret.append(i)
            if i == where: ret.append(that)
        self.nest = ret; return self

    ## @name stack ops

    ## `( ... -- )` clean stack
    def dropall(self):
        self.nest = []; return self

    ## `( n1 n2 -- n1 )` drop
    def drop(self, idx=-1, num=1):
        for i in range(num): self.nest.pop(idx)
        return self

    ## @name functional evaluation

    def eval(self, env):
        raise NotImplementedError(['eval', self, env])

    def apply(self, that, env):
        assert isinstance(that, Object)
        raise NotImplementedError(['apply', self, that, env])

## @defgroup primitive Primitive
## @ingroup core

## @ingroup primitive
class Primitive(Object):
    ## most primitives evaluates into itself
    def eval(self, env):
        return self

## strings can be nested: source code tree
class S(Primitive):
    def __init__(self, V=None, end=None, pfx=None, sfx=None):
        super().__init__(V)
        self.end = end; self.pfx = pfx; self.sfx = sfx

    def gen(self, to, depth=0, inline=False):
        if inline: return f'{self.value}'
        ret = ''
        if self.pfx is not None:
            if self.pfx: ret += f'{to.tab*depth}{self.pfx}\n'
            else: ret += '\n'
        if self.value is not None:
            ret += f'{to.tab*depth}{self.value}\n'
        for i in self:
            ret += i.gen(to, depth + 1)
        if self.end is not None:
            ret += f'{to.tab*depth}{self.end}\n'
        if self.sfx is not None:
            if self.sfx: ret += f'{to.tab*depth}{self.sfx}\n'
            else: ret += '\n'
        return ret

## code section
class Sec(S):
    def gen(self, to, depth=0):
        ret = ''
        if self.nest:
            if self.pfx is not None:
                if self.pfx: ret += f'{to.tab*depth}{self.pfx}\n'
                else: ret += '\n'
            if self.value is not None:
                ret += f'{to.tab*depth}{to.comment} \\ {self.value}\n'
            for i in self:
                ret += i.gen(to, depth + 0)
            if self.value is not None:
                ret += f'{to.tab*depth}{to.comment} / {self.value}\n'
            if self.sfx is not None:
                if self.sfx: ret += f'{to.tab*depth}{self.sfx}\n'
                else: ret += '\n'
        return ret


## @defgroup container Container
## @ingroup core

## @ingroup container
class Container(Object):
    def __init__(self, V=''): super().__init__(V)

## @ingroup container
class Vector(Container): pass

## @ingroup container
class Map(Container): pass

## @ingroup container
class Stack(Container): pass

## @ingroup container
class Queue(Container): pass

## @defgroup io IO
## @ingroup core

## @ingroup io
class IO(Object):
    def __init__(self, V):
        super().__init__(V)
        self.path = V

## @ingroup io
class Dir(IO):
    def sync(self):
        try: os.mkdir(self.path)
        except FileExistsError: pass
        for i in self: i.sync()

    def __floordiv__(self, that):
        assert isinstance(that, IO)
        that.path = f'{self.path}/{that.path}'
        return super().__floordiv__(that)

## @defgroup file File
## @ingroup io

## @ingroup file
class File(IO):
    def __init__(self, V, ext='', tab=' ' * 4, comment='#'):
        super().__init__(V + ext)
        self.tab = tab; self.comment = comment
        self.top = Sec(); self.bot = Sec()

    def sync(self):
        with open(self.path, 'w') as F:
            F.write(self.top.gen(self))
            for i in self: F.write(i.gen(self))
            F.write(self.bot.gen(self))

## @ingroup file
class giti(File):
    def __init__(self, V='', ext='.gitignore'):
        super().__init__(V, ext)
        self.bot // '!.gitignore'

## @defgroup active Active
## @ingroup core

## EDS: Executable Data Structure (c)
## @ingroup active
class Active(Object):
    pass

## Function
## @ingroup active
class Fn(Active):
    def __init__(self, V, args=[], ret=None, pfx=None, sfx=None):
        super().__init__(V)
        self.args = args
        self.ret = ret
        self.pfx = pfx; self.sfx = sfx

    def gen(self, to, depth=0):
        args = ', '.join(self.args)
        rets = ' ' if self.ret is None else f' -> {self.ret} '
        #
        if isinstance(to, rsFile):
            ret = S(f'fn {self}({args}){rets}{{', f'}}',
                    pfx=self.pfx, sfx=self.sfx)
        elif isinstance(to, pyFile):
            ret = S(f'def {self}({args}):',
                    pfx=self.pfx, sfx=self.sfx)
        else:
            raise TypeError(['gen', type(to)])
        #
        for i in self: ret // i
        #
        return ret.gen(to, depth)

## Method
## @ingroup active
class Meth(Fn):
    def __init__(self, V, args=[], ret=None, pfx=None, sfx=None):
        args = ['self'] + args
        super().__init__(V, args, ret, pfx, sfx)


## @defgroup net Net
## @ingroup io

class Net(IO): pass

class Web(Net):
    def bootstrap_head(self, p):
        return (HEAD()
                // (TITLE() // f'{p}')
                // META(charset='utf-8')
                // META(name="viewport", content="width=device-width, initial-scale=1")
                // LINK(rel="stylesheet", href="https://cdnjs.cloudflare.com/ajax/libs/bootswatch/5.1.0/darkly/bootstrap.min.css")
                // LINK(rel="stylesheet", href="/static/css.css")
                // SCRIPT(src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js")
                )

    def bootstrap_script(self, p):
        return (Sec()
                // SCRIPT(src="https://cdnjs.cloudflare.com/ajax/libs/twitter-bootstrap/5.1.0/js/bootstrap.min.js")
                )

    def static(self, p):
        p.static = Dir('static')
        p.d // p.static; p.static // giti()
        #
        p.css = File('css', '.css'); p.static // p.css
        p.css \
            // '#localtime { position: absolute; top: .5em; right: .5em; }' \
            // '#logo      { max-height: 64px; }'


## @defgroup meta Meta
## @ingroup core

## metaprogramming components
## @ingroup meta
class Meta(Object): pass

class Class(Meta):
    def __init__(self, C, sup=[], pfx=None):
        if isinstance(C, Object):
            super().__init__(C.__name__)
        elif isinstance(C, str):
            super().__init__(C)
        else:
            raise TypeError(['Class', type(C), C])
        #
        self.sup = sup
        self.pfx = pfx

    def gen(self, to, depth=0):
        if self.sup:
            sups = '(%s)' % \
                ', '.join(
                    map(lambda i: f'{i.value}',
                        self.sup))
        else: sups = ''
        pas = '' if self.nest else ' pass'
        ret = S(f'class {self.value}{sups}:{pas}', pfx=self.pfx)
        for i in self: ret // i
        return ret.gen(to, depth)

## @ingroup meta
class Module(Meta): pass

## @defgroup mods Mod
## @brief functional Project modificators
## @ingroup meta

## Project functional modificator
## @ingroup mods
class Mod(Module):
    def __init__(self):
        super().__init__(self.tag())

    def pipe(self, p):
        self.inher(p)
        self.dirs(p)
        self.giti(p)
        self.package(p)
        self.apt(p)
        self.mk(p)
        self.readme(p)
        self.src(p)
        self.test(p)
        self.tasks(p)
        self.settings(p)
        self.extensions(p)
        self.meta(p)
        self.reqs(p)
        self.doxy(p)
        return p // self

    def sync(self, p): pass
    # print(self.head(), p.head())

    def inher(self, p): pass
    def apt(self, p): pass
    def dirs(self, p): pass
    def giti(self, p): pass
    def package(self, p): pass
    def mk(self, p): pass
    def readme(self, p): pass
    def src(self, p): pass
    def test(self, p): pass
    def tasks(self, p): pass
    def settings(self, p): pass
    def extensions(self, p): pass
    def reqs(self, p): pass
    def doxy(self, p): pass
    def meta(self, p): p.meta.p // self

## @ingroup file
class jsonFile(File):
    def __init__(self, V='', ext='.json', tab=' ' * 4, comment='//'):
        super().__init__(V, ext, tab, comment)

## @ingroup file
class mkFile(File):
    def __init__(self, V='Makefile', ext='', tab='\t', comment='#'):
        super().__init__(V, ext, tab, comment)

## @ingroup file
class pyFile(File):
    def __init__(self, V, ext='.py', tab=' ' * 4, comment='#'):
        super().__init__(V, ext, tab, comment)

## software project
class Project(Module):
    def __init__(self, V=None, title=None, about=None):
        if not V: V = os.getcwd().split('/')[-1]
        super().__init__(V)
        #
        self.TITLE = title if title else f'{self}'
        self.ABOUT = about if about else ''
        self.AUTHOR = 'Dmitry Ponyatov'
        self.EMAIL = 'dponyatov@gmail.com'
        self.YEAR = 2020
        self.LICENSE = 'All rights reserved'
        self.GITHUB = 'https://github.com/ponyatov'
        #
        self.HOST = '127.0.0.1'
        self.PORT = self.port()
        #
        self.dirs()
        self.apt()
        self.vscode()
        self.mk()
        self.readme()
        self.meta()
        self.doxy()
        self.license()

    def port(self):
        return 12345

    def license(self):
        self.LICENSE = 'MIT'
        self.lic = File('LICENSE', ''); self.d // self.lic
        self.lic // f'''MIT License

Copyright (c) {self.AUTHOR} <{self.EMAIL}> {self.YEAR} All rights reserved

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.'''

    def apt(self):
        self.dev = File('apt', '.dev'); self.d // self.dev
        self.dev // 'code meld doxygen'
        self.apt = File('apt', '.txt'); self.d // self.apt
        self.apt \
            // 'git make curl' \
            // 'python3 python3-venv python3-pip'

    def meta(self):
        self.meta = pyFile(f'{self}.metaL')
        self.d // (self.meta // '## @file' //
                   f'## @brief meta: {self.TITLE}' // '')
        self.meta.p = Vector('mod')# // self

    def sync_meta(self):
        p = \
            'p = Project(\n' +\
            f"    title='''{self.TITLE}''',\n" +\
            f"    about='''{self.ABOUT}''')"
        mods = " \\\n    | ".join(
            [p] +
            list(map(lambda i: f'{i.__class__.__name__}()',
                     self.meta.p.nest)))
        self.meta \
            // 'from metaL import *' \
            // (Sec(pfx='')
                // f'{mods}'
                // f'\np.sync()')

    def doxy(self):
        self.doxy = File('doxy', '.gen'); self.d // self.doxy
        self.doxy.input = S(
            f'{"INPUT":<22} = README.md src doc')
        self.doxy \
            // (Sec()
                // f'{"PROJECT_NAME":<22} = "{self}"'
                // f'{"PROJECT_BRIEF":<22} = "{self.TITLE}"'
                // f'{"PROJECT_LOGO":<22} = doc/logo.png'
                // f'{"OUTPUT_DIRECTORY":<22} ='
                // f'{"WARN_IF_UNDOCUMENTED":<22} = NO'
                // self.doxy.input
                // f'{"RECURSIVE":<22} = YES'
                // f'{"USE_MDFILE_AS_MAINPAGE":<22} = README.md'
                // f'{"HTML_OUTPUT":<22} = docs'
                // f'{"GENERATE_LATEX":<22} = NO'
                )

    def readme(self):
        self.readme = File('README', '.md'); self.d // self.readme
        self.readme.bot // HR(
        ) // f'powered with [metaL]({self.GITHUB}/metaLgen)'
        self.readme \
            // f'#  ![logo](doc/logo.png) `{self}`' \
            // f'## {self.TITLE}' \
            // f'\n(c) {self.AUTHOR} <<{self.EMAIL}>> {self.YEAR} {self.LICENSE}' \
            // f'\ngithub: {self.GITHUB}/{self}/' \
            // f'\n{self.ABOUT}'

    def __or__(self, that):
        assert isinstance(that, Mod)
        return that.pipe(self)

    def mk(self):
        self.mk = mkFile(); self.d // self.mk
        self.mk.var = (Sec('var')
                       // f'{"MODULE":<7} = $(notdir $(CURDIR))'
                       // f'{"OS":<7} = $(shell uname -s)'
                       // f'{"NOW":<7} = $(shell date +%d%m%y)'
                       // f'{"REL":<7} = $(shell git rev-parse --short=4 HEAD)'
                       // f'{"BRANCH":<7} = $(shell git rev-parse --abbrev-ref HEAD)'
                       // f'{"CORES":<7} = $(shell grep processor /proc/cpuinfo| wc -l)'
                       )
        self.mk // self.mk.var
        #
        self.mk.ver = (Sec('ver', pfx=''))
        self.mk // self.mk.ver
        #
        self.mk.dir = \
            (Sec('dir', pfx='')
             // f'{"CWD":<7} = $(CURDIR)'
             // f'{"BIN":<7} = $(CWD)/bin'
             // f'{"DOC":<7} = $(CWD)/doc'
             // f'{"LIB":<7} = $(CWD)/lib'
             // f'{"SRC":<7} = $(CWD)/src'
             // f'{"TMP":<7} = $(CWD)/tmp')
        self.mk // self.mk.dir
        #
        self.mk.tool = (Sec('tool', pfx='')
                        // f'{"CURL":<7} = curl -L -o')
        self.mk.tool.py = (Sec()
                           // f'{"PY":<7} = $(shell which python3)'
                           // f'{"PIP":<7} = $(shell which pip3)'
                           // f'{"PEP":<7} = $(shell which autopep8)'
                           // f'{"PYT":<7} = $(shell which pytest)')
        self.mk // (self.mk.tool // self.mk.tool.py)
        #
        self.mk.src = (Sec('src', pfx='')
                       // f'{"Y":<3} += $(MODULE).metaL.py metaL.py'
                       // f'{"S":<3} += $(Y)')
        self.mk // self.mk.src
        # // 'R += $(shell find src -type f -regex ".+.rs$$")'
        self.mk.cfg = (Sec('cfg', pfx='')); self.mk // self.mk.cfg
        self.mk.package = (Sec('package', pfx='')); self.mk // self.mk.package
        #
        self.mk.format = S('format: tmp/format_py', pfx='')
        self.mk.format.py = (S('tmp/format_py: $(Y)')
                             // f'$(PEP) {Python.PEP8} --in-place $?'
                             // 'touch $@')
        #
        self.mk.meta = \
            (S('meta: $(PY) $(MODULE).metaL.py', pfx='\n.PHONY: meta')
             // '$^'
             // '$(MAKE) format')
        #
        self.mk.all = (S('all:', pfx='\n.PHONY: all'))
        self.mk.test = (S('test:', pfx='\n.PHONY: test'))
        self.mk.all_ = \
            (Sec('all', pfx='')
                // self.mk.all
                // self.mk.meta
                // self.mk.test
                // self.mk.format // self.mk.format.py
             )
        self.mk // self.mk.all_
        #
        self.mk.rule = Sec('rule', pfx=''); self.mk // self.mk.rule
        #
        self.mk.doc_ = Sec('doc', pfx=''); self.mk // self.mk.doc_
        self.mk.doxy = \
            (S('doxy:', pfx='\n.PHONY: doxy')
             // 'rm -rf docs ; doxygen doxy.gen 1>/dev/null')
        self.mk.doc_ // self.mk.doxy
        self.mk.doc = (S('doc:', pfx='\n.PHONY: doc')
                       ); self.mk.doc_ // self.mk.doc
        #
        self.mk.install_ = Sec('install', pfx='')
        self.mk.install = \
            (S('install: $(OS)_install doc', pfx='.PHONY: install update')
             // '$(MAKE) update')
        self.mk.install_ // self.mk.install
        #
        self.mk.update = (S('update: $(OS)_update'))
        self.mk.install_ // self.mk.update
        #
        self.mk.update.py = (Sec()
                             // '$(PIP) install --user -U pip pytest autopep8')
        self.mk.update // self.mk.update.py
        #
        self.mk.linux = \
            (S('ifneq (,$(shell which apt))', 'endif')
             // 'sudo apt update'
             // 'sudo apt install -u `cat apt.txt apt.dev`')
        self.mk.msys = (Sec(pfx='')
                        // '.PHONY: Msys_install Msys_update'
                        // (S('Msys_install:')
                            // 'pacman -S git make python3 python3-pip')
                        // 'Msys_update:'
                        )
        self.mk.install_ \
            // (S('Linux_install Linux_update:',
                  pfx='\n.PHONY: Linux_install Linux_update')) \
            // self.mk.linux // self.mk.msys
        self.mk // self.mk.install_
        #
        self.mk.merge_ = Sec('merge', pfx=''); self.mk // self.mk.merge_
        self.mk.merge = \
            (Sec()
             // 'SHADOW ?= shadow'
                // 'MERGE   = Makefile README.md .gitignore apt.dev apt.txt doxy.gen $(S)'
                // 'MERGE  += .vscode bin doc lib src tmp')
        self.mk.merge_ \
            // self.mk.merge \
            // (S('shadow:', pfx='\n.PHONY: shadow')
                // 'git push -v'
                // 'git checkout $(SHADOW)'
                // 'git pull -v'
                ) \
            // (S('dev:', pfx='\n.PHONY: dev')
                // 'git push -v'
                // 'git checkout $@'
                // 'git pull -v'
                // 'git checkout shadow -- $(MERGE)'
                // '$(MAKE) doxy ; git add -f docs'
                ) \
            // (S('release:', pfx='\n.PHONY: release')
                // 'git tag $(NOW)-$(REL)'
                // 'git push -v --tags'
                // '$(MAKE) shadow'
                )
        self.mk.zip = \
            (S('zip:', pfx='\n.PHONY: zip\nZIP = $(TMP)/$(MODULE)_$(BRANCH)_$(NOW)_$(REL).src.zip')
             // 'git archive --format zip --output $(ZIP) HEAD'
             // '$(MAKE) doxy ; zip -r $(ZIP) docs')
        self.mk.merge_ // self.mk.zip

    def vscode(self):
        self.vscode = Dir('.vscode'); self.d // self.vscode
        self.settings()
        self.tasks()
        self.extensions()

    def vsTask(self, group, target, make='make', param=''):
        return (S('{', '},')
                // f'"label":          "{group}: {target}",'
                // f'"type":           "shell",'
                // f'"command":        "{make} {target}{param}",'
                // f'"problemMatcher": []'
                )

    def tasks(self):
        self.tasks = jsonFile('tasks'); self.vscode // self.tasks
        self.tasks.task = (S('"tasks": [', ']')
                           // self.vsTask('project', 'install')
                           // self.vsTask('project', 'update')
                           // self.vsTask('git', 'shadow')
                           // self.vsTask('git', 'dev')
                           // self.vsTask('metaL', 'meta')
                           )

        self.tasks // (S('{', '}')
                       // '"version": "2.0.0",'
                       // self.tasks.task
                       )

    def extensions(self):
        self.extensions = jsonFile('extensions')
        self.vscode // self.extensions
        self.ext = (S('"recommendations": [', ']')
                    // '"ryuta46.multi-command",'
                    // '"stkb.rewrap",'
                    // '"tabnine.tabnine-vscode",'
                    // '// "auchenberg.vscode-browser-preview",'
                    // '// "ms-azuretools.vscode-docker",'
                    // '"tht13.python",' // '// "ms-python.python",'
                    )
        self.extensions // (S('{', '}') // self.ext)

    def multiCommand(self, key, command):
        return (S('{', '},')
                // f'"command": "multiCommand.{key}",'
                // (S('"sequence": [', ']')
                    // '"workbench.action.files.saveAll",'
                    // (S('{"command": "workbench.action.terminal.sendSequence",')
                        // f'"args": {{"text": "\\u000D clear ; {command} \\u000D"}}}}'
                        )
                    )
                )

    def settings(self):
        self.settings = jsonFile('settings'); self.vscode // self.settings
        #
        self.multi = (S('"multiCommand.commands": [', '],'))
        self.multi // self.multiCommand('f11', 'make meta')
        self.multi // self.multiCommand('f12', 'make all')
        #
        self.files = (Sec()
                      // f'"**/{self}/**":true, "**/docs/**":true,'
                      // '"**/__pycache__/**":true,'
                      )
        self.exclude = S('"files.exclude": {', '},') // self.files
        self.watcher = (S('"files.watcherExclude": {', '},') // self.files)
        self.assoc = (S('"files.associations": {', '},'))
        self.files = (Sec('files', pfx='')
                      // self.exclude // self.watcher // self.assoc)
        #
        self.terminal = (Sec('terminal', pfx='')
                         // r'"terminal.integrated.shell.windows": "D:\\msys2\\usr\\bin\\bash.exe",'
                         // '"terminal.integrated.shellArgs.windows": ["--login", "-i"],'
                         // '"terminal.integrated.env.windows":'
                         // (S('{', '},')
                             // '"MSYSTEM": "MINGW64",'
                             // '"CHERE_INVOKING":"1",'
                             // '// "PATH" : "/mingw64/bin:/usr/local/bin:/usr/bin:/bin:/c/Windows/System32:/c/Windows:/c/Windows/System32/Wbem"')
                         )
        #
        self.editor = (Sec('editor', pfx='')
                       // '"editor.tabSize": 4,'
                       // '"editor.rulers": [80],'
                       // '"workbench.tree.indent": 32,')
        #
        self.settings // (S('{', '}') // self.multi //
                          self.files // self.terminal // self.editor)

    def giti(self):
        self.giti = giti(); self.d // self.giti
        self.giti.py = (Sec(sfx='')
                        // '__pycache__/')
        self.giti \
            // '*~' // '*.swp' // '*.log' // '' \
            // '/docs/' // f'/{self}/' // '' \
            // self.giti.py

    def dirs(self):
        self.d = Dir(f'{self}'); self.giti()
        #
        self.bin = Dir('bin'); self.d // self.bin
        self.bin.giti = giti(); self.bin // (self.bin.giti // '*')
        #
        self.doc = Dir('doc'); self.d // self.doc
        self.doc.giti = giti(); self.doc // (self.doc.giti // '*.pdf')
        #
        self.lib = Dir('lib'); self.d // self.lib
        self.lib.giti = giti(); self.lib // self.lib.giti
        #
        self.src = Dir('src'); self.d // self.src
        self.src.giti = giti(); self.src // self.src.giti
        #
        self.tmp = Dir('tmp'); self.d // self.tmp
        self.tmp.giti = giti(); self.tmp // (self.tmp.giti // '*')

    def sync(self):
        self.sync_meta()
        self.d.sync()
        for i in self: i.sync(self)

## @ingroup file
class tomlFile(File):
    def __init__(self, V, ext='.toml', tab=' ' * 4, comment='#'):
        super().__init__(V, ext, tab, comment)

## @ingroup file
class rsFile(File):
    def __init__(self, V, ext='.rs', tab=' ' * 4, comment='//'):
        super().__init__(V, ext, tab, comment)

## @ingroup mods
class Rust(Mod):

    def apt(self, p):
        p.dev // 'build-essential'

    def giti(self, p):
        p.giti // (Sec(sfx='') // 'target/' // 'Cargo.lock')

    def package(self, p):
        p.toml = tomlFile('Cargo'); p.d // p.toml
        p.toml // (Sec(pfx='[package]')
                   // f'{"name":<22} = "{p:l}"'
                   // f'{"version":<22} = "0.0.1"'
                   // f'{"edition":<22} = "2018"'
                   // ''
                   // f'{"authors":<22} = ["{p.AUTHOR} <{p.EMAIL}>"]'
                   // f'{"description":<22} = "{p.TITLE}"')
        #
        p.toml.deps = (Sec(pfx='\n[dependencies]')
                       // f'{"tracing":<22} = "0.1"'
                       // f'{"tracing-subscriber":<22} = "0.2"'
                       #    // f'{"chrono":<22} = "0.4"'
                       )
        p.toml.web = (Sec('web'))
        p.toml // (p.toml.deps // p.toml.web)
        #
        p.toml.build = (Sec(pfx='\n[build-dependencies]'))
        p.toml // p.toml.build
        #
        p.toml.dev = (Sec(pfx='\n[dev-dependencies]'))
        p.toml // p.toml.dev
        #
        p.toml.unix = (Sec(pfx="\n[target.'cfg(unix)'.dependencies]")
                       // f'{"libc":<22} = "0.2"'
                       // f'{"nix":<22} = "0.22"'
                       )
        p.toml // p.toml.unix
        #
        p.toml.win = (Sec(pfx="\n[target.'cfg(windows)'.dependencies]")
                      // f'{"windows":<22} = "0.19"'
                      )
        p.toml // p.toml.win
        #
        # p.toml.bin = (Sec(pfx='\n[[bin]]')
        #               // f'{"name":<22} = "{p}"'
        #               // f'{"path":<22} = "src/main.rs"')
        # p.toml // p.toml.bin

    def settings(self, p):
        p.exclude.rust = \
            (Sec()
             // '"**/target/**":true, "**/Cargo.lock":true,')
        p.exclude // p.exclude.rust; p.watcher // p.exclude.rust

    def tasks(self, p):
        p.tasks.task \
            // p.vsTask('cargo', 'update', make='cargo') \
            // p.vsTask('cargo', 'watch')

    def extensions(self, p):
        p.ext // '"rust-lang.rust",' // '"bungcip.better-toml",'

    def mk(self, p):
        p.mk.dir \
            // f'{"CAR":<7} = $(HOME)/.cargo/bin'
        p.mk.tool \
            // (Sec()
                // f'{"RUSTUP":<7} = $(CAR)/rustup'
                // f'{"CARGO":<7} = $(CAR)/cargo'
                // f'{"RUSTC":<7} = $(CAR)/rucstc'
                )
        p.mk.src \
            // f'{"R":<3} += $(shell find src -type f -regex ".+.rs$$")' \
            // f'{"S":<3} += $(R) Cargo.toml'
        #
        p.mk.all.value += ' $(R)'
        p.mk.all // '$(CARGO) test && $(CARGO) fmt && $(CARGO) run'
        #
        p.mk.test.value += ' $(R)'
        p.mk.test // '$(CARGO) test'
        #
        p.mk.watch = \
            (S('watch:', pfx='')
             // '$(CARGO) watch -w Cargo.toml -w src -x test -x fmt -x run')
        p.mk.all_ // p.mk.watch
        #
        # p.mk.doc_.before(p.mk.doxy,
        #                  'RR = $(shell echo $(R) | sed "s/src\///g")')
        # p.mk.doxy.ins(0,
        #               '$(foreach i,$(RR),cargo readme -i src/$(i) > doc/$(i).md;)')
        p.mk.doxy \
            // 'rm -rf target/doc ; $(CARGO) doc --no-deps && cp -r target/doc docs/rust'
        #
        p.mk.install.value += ' $(RUSTUP)'
        p.mk.update \
            // '$(RUSTUP) update && $(CARGO) update'
        p.mk.install_ \
            // (S('$(RUSTUP):', pfx='')
                // 'curl --proto \'=https\' --tlsv1.2 -sSf https://sh.rustup.rs | sh')

    def readme(self, p):
        p.readme.ins(4,
                     f'\n# <a href="rust/{p}/index.html">rustdoc</a>')

    def src(self, p):
        self.main(p)
        self.test(p)

    def main(self, p):
        p.main = rsFile('main'); p.src // p.main
        #
        p.main.top // f'//! # {p.TITLE}' // '' \
            // '// #![allow(dead_code)]' \
            // '// #![allow(non_camel_case_types)]'
        #
        p.main.config = Sec('config', pfx='', sfx=''); p.main // p.main.config
        p.main.mod = Sec('mod', pfx='') // 'mod test;'; p.main // p.main.mod
        #
        p.main.extern = Sec('extern', pfx=''); p.main // p.main.extern
        p.main.extern // 'extern crate tracing;'
        #
        p.main.use = Sec('use', pfx=''); p.main // p.main.use
        p.main.use // 'use tracing::{info, instrument};'
        #
        p.main.main = Fn('main',
                         pfx='\n#[instrument]\n/// program entry point')
        p.main // p.main.main
        #
        p.main.args = \
            (Sec('args')
             // 'let argv: Vec<String> = std::env::args().collect();'
             // 'let argc = argv.len();'
             // 'let program = std::path::Path::new(&argv[0]);'
             // 'let module = program.file_stem().unwrap();'
             // 'info!("start {:?} as #{:?} {:?}", module, argc, argv);')
        p.main.main.atexit = (Sec('atexit') // 'info!("stop");')
        p.main.main \
            // 'tracing_subscriber::fmt().compact().init();' \
            // p.main.args \
            // p.main.main.atexit
        #
        p.main.web = Sec('web', pfx=''); p.main // p.main.web

    def test(self, p):
        p.test = rsFile('test'); p.src \
            // (p.test // f'//! # `{p}` tests' // '')
        p.test // '#![cfg(test)]' // '' \
            // '#[allow(unused_imports)]' // 'use crate::*;' // ''
        p.test // (Fn('any',
                      pfx='#[test]\n/// dummy test /always ok/')
                   // 'assert_eq!(1, 1);')

## extend Python project with venv (local interpreter & libs)
## @ingroup mods
class VEnv(Mod):

    def package(self, p):
        p.reqs = File('requirements', '.txt'); p.d // p.reqs

    def giti(self, p):
        p.giti // (Sec(sfx='')
                   // '/lib64' // '/include/' // '/share/'
                   // 'pyvenv.cfg' // '*.pyc')

    def mk(self, p):
        p.mk.tool // (Sec(pfx='')
                      // f'{"PY":<7} = $(BIN)/python3'
                      // f'{"PIP":<7} = $(BIN)/pip3'
                      // f'{"PYT":<7} = $(BIN)/pytest'
                      // f'{"PEP":<7} = $(BIN)/autopep8')
        p.mk.update.py.dropall() \
            // '$(PIP) install -U pytest autopep8' \
            // '$(PIP) install -U -r requirements.txt'
        p.mk.install.value += ' $(PIP)'
        p.mk.install_ \
            // (S('$(PY) $(PIP) $(PYT) $(PEP):', pfx='')
                // 'python3 -m venv .'
                // '$(MAKE) update')

    def settings(self, p):
        p.settings[0].ins(0, (Sec('py', sfx='')
                              // '"python.pythonPath"              : "./bin/python3",'
                              // '"python.formatting.provider"     : "autopep8",'
                              // '"python.formatting.autopep8Path" : "./bin/autopep8",'
                              // f'"python.formatting.autopep8Args" : ["{Python.PEP8}"],'
                              ))
        #
        p.exclude.py = (Sec()
                        // '"**/lib/python**":true, "**/lib64/**":true,'
                        // '"**/include/**":true, "**/share/**":true,'
                        // '"**/pyvenv.cfg":true,')
        p.exclude // p.exclude.py; p.watcher // p.exclude.py

## @ingroup mods
class Python(Mod):
    PEP8 = '--ignore=E26,E302,E305,E401,E402,E701,E702'

    def pipe(self, p):
        p = super().pipe(p)
        self.reqs(p)
        return p

    def mk(self, p):
        p.mk.src.ins(1, (Sec()
                         // f'{"Y":<3} += $(MODULE).py test_$(MODULE).py'
                         // f'{"P":<3} += config.py'
                         ))
        #
        p.mk.all.value += ' $(PY) $(MODULE).py'
        p.mk.all // '$(MAKE) test format' // '$^ $@'
        #
        p.mk.test.value += ' $(PYT) test_$(MODULE).py'
        p.mk.test // '$^'
        #
        p.mk.update // '$(PIP) install --user -U -r requirements.txt'
        p.mk.merge // 'MERGE  += requirements.txt'

    def config(self, p):
        p.config = (pyFile('config') // 'import os' // ''); p.d // p.config
        p.config \
            // (S(f"SECRET_KEY = {os.urandom(0x22)}",
                  pfx='# SECURITY WARNING: keep the secret key used in production secret!'))
        p.config // f"""
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True"""
        #
        p.config // (Sec(pfx='')
                     // f"HOST = os.getenv('HOST', '{p.HOST}')"
                     // f"PORT = os.getenv('PORT', {p.PORT})")

    def src(self, p):
        p.py = pyFile(f'{p}'); p.d // p.py
        brf = f'## @brief {p.TITLE}'
        p.py // '## @file' // brf // f'## @defgroup {p}' // brf // '## @{'
        p.py.bot // '\n## @}'
        #
        self.config(p)
        p.py.imp = (Sec(pfx='') // 'import config' // 'import os, sys')
        p.py // p.py.imp
        #
        p.py.init = Sec(pfx=''); p.py // p.py.init
        p.py.init // (S("if __name__ == '__main__':") // 'pass')

    def test(self, p):
        p.test = pyFile(f'test_{p}'); p.d // p.test
        p.test // (Sec() // f'from {p} import *' // 'import pytest')
        p.test // (S('def test_any(): assert True', pfx=''))

    def reqs(self, p):
        p.reqs = File('requirements', '.txt'); p.d // p.reqs

    def doxy(self, p):
        p.doxy.input.value += f' {p}.py test_{p}.py'


## Django project
## @ingroup mods
class Django(Mod):

    def inher(self, p):
        if not hasattr(p, 'py'):
            p = p | Python()

    maketasks = {'runserver': '', 'makemigrations': '', 'migrate': '',
                 'dumpdata': ' --indent 2 > tmp/$@.json',
                 'loaddata': ' fixture/user.json'}

    def mk(self, p):
        p.mk.src.drop(idx=-2)
        p.mk.src.ins(1, (Sec()
                         // f'{"Y":<3} += manage.py'
                         // f'{"P":<3} += config.py'
                         // f'{"Y":<3} += $(shell find project -type f -regex ".+.py$$")'
                         // f'{"Y":<3} += $(shell find app     -type f -regex ".+.py$$")'
                         ))
        p.mk.src[-1].value = f'{"S":<3} += $(shell echo $(Y) | grep -v "migrations/0")'
        #
        p.mk.all.value = 'all:'
        p.mk.all.dropall()
        #
        for i in self.maketasks:
            p.mk.all_ // (S(f'{i}: $(PY) manage.py', pfx='')
                          // f'$^ $@{self.maketasks[i]}')
        #
        p.mk.install // '$(MAKE) migrate loaddata'

    def apt(self, p):
        p.dev // 'sqlitebrowser'
        p.apt // 'sqlite3'

    def dirs(self, p):
        p.fixture = Dir('fixture'); p.d // p.fixture

    def fixture(self, p):
        p.fixture.user = jsonFile('user'); p.fixture // p.fixture.user
        isonow = dt.datetime.now().isoformat()
        p.fixture.user \
            // (S('[', ']')
                // (S('{', '}')
                    // '"model": "app.customuser",'
                    // '"pk": 1,'
                    // (S('"fields": {', '}')
                        // '"password": "pbkdf2_sha256$260000$zmTo77UpOSFFM0VsnFo6Wr$SQYvj/o9IijWywXDasN9qfVRAaiZRAR4+q+x+/UbcJk=",'
                        // f'"last_login": "{isonow}Z",'
                        // '"is_superuser": true,'
                        // '"username": "dponyatov",'
                        // '"first_name": "Dmitry",'
                        // '"second_name": "A",'
                        // '"last_name": "Ponyatov",'
                        // '"email": "dponyatov@gmail.com",'
                        // f'"phone": "+79171010818",'
                        // f'"telegram": "@dponyatov",'
                        // f'"vk": "https://vk.com/id266201297",'
                        // '"is_staff": true,'
                        // '"is_active": true,'
                        // f'"date_joined": "{isonow}Z",'
                        // '"groups": [],'
                        // '"user_permissions": []'
                        )))

    def tasks(self, p):
        for i in self.maketasks:
            p.tasks.task // p.vsTask('django', i)

    def reqs(self, p):
        assert p.py
        p.reqs // 'Django' // 'django-grappelli'

    def src(self, p):
        p.d.remove(p.py)
        p.d.remove(p.test)
        self.manage(p)
        self.project(p)
        self.app(p)
        self.settings(p)
        self.urls(p)
        self.fixture(p)

    def admin_model(self, model, fields=[]):
        return (Sec()
                // (S(f'class {model}Admin(admin.ModelAdmin):', pfx='')
                    // f"model = {model}"
                    // (S(f"list_display = fields({model},")
                        // f"{fields})"))
                // S(f"admin.site.register({model}, {model}Admin)", pfx='')
                )

    def admin(self, p):
        p.admin = pyFile('admin'); p.app // p.admin
        #
        p.admin // (Sec()
                    // 'from django.contrib import admin'
                    // 'from .models import *')
        #
        p.admin // (Sec(pfx='')
                    // f"admin.site.site_header = '{p.TITLE}'"
                    // f"admin.site.site_title = 'site_title'"
                    // f"admin.site.index_title = 'admin'"
                    )
        #
        p.admin // (S('def fields(model, whats=[]):', pfx='')
                    // 'assert isinstance(whats, list)'
                    // (S('return whats + [', ']')
                        // "field.name"
                        // "for field in model._meta.fields"
                        // "if field.name not in ['id', 'password'] + whats"
                        ))
        #
        p.admin // self.admin_model('CustomUser',
                                    ['username', 'last_name', 'first_name', 'second_name', 'email'])
        p.admin // self.admin_model('Address')
        #
        p.t = Dir('templates'); p.app // p.t
        p.t.admin = Dir('admin'); p.t // p.t.admin
        p.admin.base = htmlFile('base'); p.t.admin // p.admin.base
        p.admin.base // """
{# https://stackoverflow.com/questions/67135053/can-someone-explain-to-my-why-my-django-admin-theme-is-dark #}
{% extends 'admin/base.html' %}

{% block extrahead %}{{ block.super }}
<style>

    h1 { color: #0af; }
    caption { background: #023 !important; }
    :root {
    }
</style>
{% endblock %}
"""

    def app(self, p):
        p.app = Dir('app'); p.d // p.app; p.app // pyFile('__init__')
        self.models(p)
        self.admin(p)
        self.apps(p)
        self.views(p)
        self.migrations(p)

    def migrations(self, p):
        p.migrations = Dir('migrations'); p.app // p.migrations
        p.migrations // pyFile('__init__')
        p.migrations // (giti() // '????_*.py')

    def apps(self, p):
        p.apps = pyFile('apps'); p.app // p.apps
        p.apps // """from django.apps import AppConfig

class AppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'
    verbose_name = 'Сайт'"""

    def views(self, p):
        p.views = pyFile('views'); p.app // p.views
        p.views // 'from django.shortcuts import render'

    def models(self, p):
        p.models = pyFile('models'); p.app // p.models
        p.models \
            // 'from django.db import models' // ''
        p.models \
            // 'from django.db import models' \
            // 'from django.contrib.auth.models import AbstractUser'
        p.models \
            // (S('class CustomUser(AbstractUser):', pfx='')
                // "second_name = models.CharField(verbose_name='Отчество',"
                // "                               max_length=33,"
                // "                               null=True, blank = True)"
                )

    def manage(self, p):
        p.manage = pyFile('manage'); p.d // p.manage
        p.manage \
            // '#!/usr/bin/env python3' // '' // 'import os, sys'
        p.manage \
            // (S('def main():', pfx='')
                // "os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')"
                // 'from django.core.management import execute_from_command_line'
                // 'execute_from_command_line(sys.argv)'
                )
        p.manage \
            // (S("if __name__ == '__main__':", pfx='') // 'main()')

    def project(self, p):
        p.project = Dir('project'); p.d // p.project
        p.project // pyFile('__init__')

    def settings(self, p):
        p.settings = pyFile('settings'); p.project // p.settings
        p.settings \
            // (Sec()
                // 'import config' // ''
                // 'SECRET_KEY = config.SECRET_KEY'
                // 'DEBUG = config.DEBUG'

                )
        p.settings \
            // """
from pathlib import Path"""
        p.settings \
            // """
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent"""
        p.settings \
            // """
ALLOWED_HOSTS = []"""
        p.settings \
            // """
# Application definition"""
        p.settings \
            // """
INSTALLED_APPS = [
    'grappelli',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'app',
]"""
        p.settings \
            // """
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]"""
        p.settings \
            // """
ROOT_URLCONF = 'project.urls'"""
        p.settings \
            // """
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # https://stackoverflow.com/questions/67135053/can-someone-explain-to-my-why-my-django-admin-theme-is-dark
        'DIRS': [BASE_DIR / 'app' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]"""
        p.settings \
            // """
# WSGI_APPLICATION = 'project.wsgi.application'"""
        p.settings \
            // """
# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases"""
        p.settings \
            // """
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'tmp' / 'db.sqlite3',
    }
}"""
        p.settings \
            // """
# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators"""
        p.settings \
            // """
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]"""
        p.settings \
            // """
# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/"""
        p.settings \
            // """
LANGUAGE_CODE = 'ru-RU'
TIME_ZONE = 'Europe/Samara'
USE_I18N = True
USE_L10N = True
USE_TZ = True"""
        p.settings \
            // """
# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = '/static/'"""
        p.settings \
            // """
# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'app.CustomUser'"""

    def urls(self, p):
        p.urls = pyFile('urls'); p.project // p.urls
        p.urls \
            // 'from django.contrib import admin' \
            // 'from django.urls import path' \
            // 'from django.conf.urls import include' \
            // 'from django.views.generic.base import RedirectView'
        p.urls \
            // (S('urlpatterns = [', ']', pfx='')
                // "path('grappelli/', include('grappelli.urls')), # grappelli URLS"
                // "path('admin/', admin.site.urls),"
                // "path('', RedirectView.as_view(url='/admin/'))"
                )

## @defgroup circular circular
## @brief `metaL` circular implementation

## @ingroup circular
class metaL(Python):
    def mk(self, p):
        super().mk(p)
        p.mk.meta[0].value += ' meta'

    def giti(self, p):
        p.lib.giti.ins(0, 'python*/')

    def src(self, p):
        p.m = pyFile('metaL'); p.d // p.m

    def imports(self, p):
        p.m.top // '#!/usr/bin/env python3'
        p.m // (Sec(pfx='')
                // '## @file'
                // f'## @brief {p.TITLE}')

    def core(self, p):
        self.meta(p)
        self.io(p)
        self.net(p)
        self.web(p)

    def meta(self, p):
        p.m.meta = Class('Meta', [p.m.object])
        p.m // p.m.meta

    def io(self, p):
        p.m.io = Class('IO', [p.m.object])
        p.m // p.m.io

    def net(self, p):
        p.m.net = Class('Net', [p.m.io])
        p.m // p.m.net

    def web(self, p):
        p.m.web = Class('Web', [p.m.net])
        p.m // p.m.web

## @defgroup html

## @ingroup html
class htmlFile(File):
    def __init__(self, V, ext='.html'):
        super().__init__(V, ext)

class teraFile(File):
    def __init__(self, V, ext='.html.tera'):
        super().__init__(V, ext)

## block
## @ingroup html
class HTML(S):
    def __init__(self, **kw):
        super().__init__(self.tag())
        for i in kw:
            j = 'class' if i == 'clazz' else i
            self[j] = kw[i]

    def gen_head(self,):
        ret = ''
        if self.keys():
            args = ' ' + ' '.join(map(lambda i:
                                      f'{i}="{self[i]}"', self.keys()))
        else: args = ''
        return (ret, args)

    def gen(self, to, depth=0, inline=False):
        ret, args = self.gen_head()
        ret += f'{to.tab*depth}<{self.value}{args}>\n'
        for i in self: ret += i.gen(to, depth + 1)
        ret += f'{to.tab*depth}</{self.value}>\n'
        return ret

## inline
## @ingroup html
class HTMLI(HTML):
    def gen(self, to, depth=0, inline=False):
        ret, args = self.gen_head()
        ret += f'{to.tab*depth}<{self.value}{args}>'
        for i in self: ret += i.gen(to, depth + 1, inline=True)
        ret += f'</{self.value}>\n'
        return ret

class HTMLS(HTML):
    def gen(self, to, depth=0, inline=False):
        ret, args = self.gen_head()
        ret += f'{to.tab*depth}<{self.value}{args}>\n'
        # for i in self: ret += i.gen(to, depth + 1, inline=True)
        # ret += f'</{self.value}>\n'
        return ret

class HEAD(HTML): pass
class BODY(HTML): pass
class DIV(HTML): pass
class NAV(DIV): pass

class SPAN(HTMLI): pass
class TITLE(HTMLI): pass
class SCRIPT(HTMLI): pass

class META(HTMLS): pass
class LINK(HTMLS): pass
class IMG(HTMLS): pass
class HR(HTMLS): pass


## Rust WASM target
## @ingroup mods
class WASM(Mod):

    def giti(self, p):
        p.giti // '/dist/' // ''

    def apt(self, p):
        p.dev // 'npm'

    def package(self, p):
        p.toml.wasm = Sec(
            pfx='\n[target.\'cfg(target_arch = "wasm32")\'.dependencies]')
        p.toml // p.toml.wasm
        p.toml.deps.dropall() // p.toml.web
        p.toml.wasm \
            // f'{"wasm-bindgen":<22} = "0.2"' \
            // f'{"# js-sys":<22} = "0.3"' \
            // f'{"# web-sys":<22} = "0.3"'
        # p.toml.build \
        #     // f'{"wasm-pack":<22} = "0.10"' \
        #     // f'{"cargo-web":<22} = "0.6.26"'
        # p.toml \
        #     // (Sec(pfx='\n[lib]')
        #         // 'path = "src/wasm.rs"'
        #         // 'crate-type = ["cdylib"]')

    def src(self, p):
        p.wasm = rsFile('lib'); p.src // p.wasm
        p.main.mod.ins(0, 'mod lib;')
        p.wasm \
            // 'extern crate wasm_bindgen;' // '' \
            // 'use wasm_bindgen::prelude::*;'
        p.wasm \
            // (S('extern "C" {', '}',
                  pfx='\n#[wasm_bindgen]')
                // 'pub fn alert(s: &str);')
        p.wasm \
            // (S('pub fn greet(name: &str) {', '}',
                  pfx='\n#[wasm_bindgen]')
                // 'alert(&format!("Hello, {}!", name));')

    def mk(self, p):
        p.mk.rust.dropall() // 'trunk serve'
        p.mk.install \
            // '$(RUSTUP) toolchain install nightly' \
            // '$(RUSTUP) target add wasm32-unknown-unknown --toolchain nightly' \
            // '$(CARGO) install cargo-web wasm-pack'

## Yew framework application
## @ingroup mods
class Yew(WASM):
    def mk(self, p):
        super().mk(p)
        p.mk.meta[0].value += ' yew'

    def package(self, p):
        super().package(p)
        p.toml.web \
            // f'{"yew":<22} = "0.18"'

    def src(self, p):
        super().src(p)
        # p.src.remove(p.wasm)
        self.index(p)
        self.main(p)

    def main(self, p):
        p.main.extern.dropall()
        p.main.use.dropall()
        #
        p.yew = (Sec('yew', pfx='') // 'use yew::prelude::*;')
        p.main.before(p.main.main, p.yew)
        #
        p.yew.msg = S('enum Msg {', '}', pfx='')
        p.yew // (p.yew.msg // 'Inc,' // 'Dec,')
        #
        p.yew.model = S('struct Model {', '}', pfx='')
        p.yew // (p.yew.model // 'value: isize,')
        #
        p.yew.component = S('impl Component for Model {', '}', pfx='')
        #
        p.yew.create = \
            (Fn('create',
                ['_props: Self::Properties', 'link: ComponentLink<Self>'],
                'Self', pfx='')
                // (S('Self {', '}')))
        #
        p.yew.update = \
            (Fn('update',
                ['&mut self', 'msg: Self::Message'],
                'ShouldRender', pfx='')
                // (S('match msg {', '}')))
        #
        p.yew.change = \
            (Fn('change',
                ['&mut self', '_props: Self::Properties'],
                'ShouldRender', pfx='')
                // 'false')
        #
        p.yew.view = \
            (Fn('view', ['&self'], 'Html', pfx='')
             // (S('html! {', '}') // DIV()))
        #
        p.yew \
            // (p.yew.component
                // 'type Message = Msg;'
                // 'type Properties = ();'
                // p.yew.create
                // p.yew.update
                // p.yew.change
                // p.yew.view
                )
        #
        p.main.main.pfx = ''
        p.main.main.dropall() // 'yew::start_app::<Model>();'

    def index(self, p):
        p.html = htmlFile('index'); p.d // p.html
        p.html \
            // '<!DOCTYPE html>' \
            // (HTML()
                // Web.bootstrap_head(self, p)
                // (BODY() // DIV(clazz='container'))
                // Web.bootstrap_script(self, p)
                )

    def dirs(self, p):
        Web.static(self, p)

    # def mk(self, p):
    #     p.mk.install // '$(CARGO) install cargo-web'

## @ingroup mods
## Actix Web framework
class Actix(Mod):
    def mk(self, p):
        p.mk.meta[0].value += ' actix'

    def package(self, p):
        p.toml.web \
            // f'{"actix-web":<22} = "3.3"'

    def src(self, p):
        p.main.extern.ins(0, 'extern crate actix_web;')
        p.main.use.ins(0,
                       (S('use actix_web::{get, post, web, App, HttpResponse, HttpServer, Responder};',
                          pfx='#[allow(unused_imports)]')))
        #
        p.main.web \
            // (S('async fn hello() -> impl Responder {', '}',
                  pfx='#[get("/")]')
                // 'HttpResponse::Ok().body("Hello world!")')
        p.main.web \
            // (S('async fn echo(req_body: String) -> impl Responder {', '}',
                  pfx='\n#[post("/echo")]')
                // 'HttpResponse::Ok().body(req_body)')

## @ingroup mods
## `Rocket.rs` web framework
class Rocket(Mod):

    def mk(self, p):
        p.mk.meta[0].value += ' web'

    def dirs(self, p):
        Web.static(self, p)
        self.templates(p)

    def extensions(self, p):
        p.ext // '"karunamurti.tera",'

    def templates(self, p):
        p.templates = Dir('templates')
        p.d // p.templates; p.templates // giti()
        #
        p.index = teraFile('index'); p.templates // p.index
        p.index \
            // '{% extends "all" %}' \
            // '{% block body %}' \
            // 'Hello World' \
            // '{% endblock %}'
        #
        p.all = teraFile('all'); p.templates // p.all
        #
        p.all.head = Web.bootstrap_head(self, p)
        #
        p.all \
            // '<!DOCTYPE html>' \
            // (HTML(lang='ru')
                // p.all.head
                // (BODY()
                    // (NAV()
                        // (IMG(id="logo", clazz="nav-icon", src="/static/logo.png"))
                        // (SPAN(id='localtime') // '{{localtime}}'))
                    // (DIV(clazz='container')
                        // '{% block body %}{% endblock %}')
                    )
                )

    def package(self, p):
        p.toml.web \
            // (Sec()
                // 'serde = "1.0"'
                // 'serde_derive = "1.0"'
                // 'rocket = { version = "0.4" }'
                // 'rocket_contrib = { version = "0.4", features = ["tera_templates"] }')
        p.toml \
            // (Sec(pfx='\n[development]')
                // 'template_dir = "templates/"'
                )

    def src(self, p):
        p.main.ins(0, (Sec('rocket', sfx='')
                       // '#![feature(proc_macro_hygiene, decl_macro)]'
                       // '#[macro_use]' // 'extern crate rocket;'
                       // 'extern crate rocket_contrib;'
                       // '#[macro_use]'
                       // 'extern crate serde_derive;'
                       // 'use rocket_contrib::templates::Template;'
                       ))
        #
        p.main.main.ins(-1,
                        (S('rocket::ignite()')
                         // '.mount("/", routes![favicon, logo, static_file, index])'
                         // '.attach(Template::fairing())'
                         // '.launch();'
                         ))
        #
        p.main.static = Sec('static', pfx=''); p.main.web // p.main.static
        p.main.static \
            // 'use rocket::response::NamedFile;' \
            // 'use std::path::{Path, PathBuf};' \
            // (Fn('favicon', [], 'Option<NamedFile>',
                   pfx='\n#[get("/favicon.ico")]')
                // 'NamedFile::open(Path::new("doc/").join("logo.png")).ok()') \
            // (Fn('logo', [], 'Option<NamedFile>',
                   pfx='\n#[get("/static/logo.png")]')
                // 'favicon()') \
            // (Fn('static_file',
                   ['file: PathBuf'],
                   'Option<NamedFile>',
                   pfx='\n#[get("/static/<file..>")]')
                // 'NamedFile::open(Path::new("static/").join(file)).ok()')
        #
        p.main.web \
            // (S('struct WebState {', '}', pfx='\n#[derive(Serialize)]')
                // 'localtime: String,'
                // 'title: &\'static str,'
                )
        #
        p.main.web \
            // (Fn('index', ret='Template', pfx='\n#[get("/")]')
                // (S('let context = WebState {', '};')
                    // 'title: "index",'
                    // 'localtime: chrono::Utc::now().format("%Y-%m-%d %H:%M:%S").to_string(),'
                    )
                // 'Template::render("index", &context)')

## Rust gaming
## @ingroup mods
class Game(Mod):

    def apt(self, p):
        p.dev // 'libsdl2-dev libsdl2-ttf-dev libsdl2-image-dev'
        p.apt // 'libsdl2-2.0-0 libsdl2-ttf-2.0-0 libsdl2-image-2.0-0'

    def package(self, p):
        p.toml.deps // (Sec(pfx='')
                        // 'sdl2 = { version = "0.34", features = ["image"] }'
                        // '# features = ["ttf","gfx","mixer"]')

    def test(self, p):
        p.test \
            // (S('fn sdl_context() {', '}', pfx='\n#[test]')
                // 'let scr = Screen::new(String::from(""));'
                // 'assert_eq!(scr.argv, "");'
                // 'assert_eq!(scr.w, W);'
                // 'assert_eq!(scr.h, H);'
                )

    def src(self, p):
        p.main.extern.ins(0, 'extern crate sdl2;')
        p.main.main.ins(-1, 'game_loop(argv[0].clone());')
        #
        p.main.game = (Sec('game', pfx='')); p.main // p.main.game
        p.main.config // (Sec('game')
                          // '/// default screen window width, pixels'
                          // 'pub const W: u16 = 640;'
                          // '/// default screen window height, pixels'
                          // 'pub const H: u16 = 480;')
        #
        p.main.game \
            // (S('pub struct Screen {', '}',
                  pfx='\n#[allow(dead_code)]\n/// SDL screen state')
                // '/// window title: program name from `argv[0]`'
                // 'pub argv: String,'
                // '/// current width, pixels'
                // 'pub w: u16,'
                // '/// current height, pixels'
                // 'pub h: u16,'
                // '/// SDL context'
                // 'pub sdl: sdl2::Sdl,'
                // '/// video subsystem context'
                // 'pub video: sdl2::VideoSubsystem,'
                // '/// SDL window state'
                // 'pub window: sdl2::video::Window,'
                // '/// window icon'
                // 'pub icon: sdl2::surface::Surface<\'static>,'
                // '/// GUI events queue'
                // 'pub events: sdl2::EventPump,'
                // '// pub canvas: sdl2::render::WindowCanvas,'
                )
        #
        p.main.game \
            // (S('impl Screen {', '}', pfx='')
                // (Fn('new', ['argv: String'], 'Self', pfx='#[instrument]')
                    // 'let context = sdl2::init().unwrap();'
                    // 'let video = context.video().unwrap();'
                    // (S('let window = video')
                        // '.window(argv.as_str(), W as u32, H as u32)'
                        // '.build()' // '.unwrap();'
                        )
                    // 'let icon = sdl2::image::LoadSurface::from_file("doc/logo.png").unwrap();'
                    // '// let canvas = window.into_canvas().build().unwrap();'
                    // 'let event_pump = context.event_pump().unwrap();'
                    // (S('Screen {', '}')
                        // 'argv: argv,' // 'w: W,' // 'h: H,'
                        // 'sdl: context,' // 'video: video,'
                        // 'window: window,' // 'icon: icon,'
                        // 'events: event_pump,'
                        )))
        #
        p.main.gameloop = \
            (Fn('game_loop', ['argv: String'],
                pfx='\n#[instrument]\n/// SDL/GUI event loop', sfx='')
             // 'let mut game = Screen::new(argv);'
             // ((S('\'event: loop {', '}')
                  // (S('for event in game.events.poll_iter() {', '}')

                      // 'info!("{:?}", event);'
                      // (S('match event {', '}')
                          // 'sdl2::event::Event::Quit { .. }'
                          // (S('| sdl2::event::Event::KeyDown {')
                              // 'keycode: Some(sdl2::keyboard::Keycode::Escape),' // '..')
                          // '} => break \'event,' // '_ => (),')
                      )))
             )
        p.main.game // p.main.gameloop
        # p.main.mod.ins(0, 'mod game;')
        # p.main.extern.ins(0, 'extern crate sdl2;')

## tiny Forth-like interpreter
## @ingroup mods
class Forth(Mod):
    def src(self, p):
        p.forth = Sec('forth', pfx=''); p.main // p.forth
        #
        p.main.config.forth = \
            (Sec('forth', pfx='')
             // '/// memory size, bytes'
             // '#[allow(non_upper_case_globals)]'
             // 'pub const Msz: usize = 0x10000;'
             // '/// return stack size, cells'
             // '#[allow(non_upper_case_globals)]'
             // 'pub const Rsz: usize = 0x100;'
             // '/// data stack size, cells'
             // '#[allow(non_upper_case_globals)]'
             // 'pub const Dsz: usize = 0x10;'
             )
        p.main.config // p.main.config.forth
        #
        p.forth.struct = \
            (S('pub struct Forth {', '}',
               pfx='\n/// FVM: Forth Virtual Machine state\n#[allow(dead_code)]')
             // '/// main memory size, bytes' // 'pub msz: usize,'
             // '/// main memory' // 'm: Vec<u8>,'
             // '/// instruction pointer' // 'pub ip: usize,'
             // '/// compilation pointer' // 'pub cp: usize,'
             // ''
             // '/// return stack size, cells' // 'pub rsz: usize,'
             // '/// return stack' // 'r: Vec<usize>,'
             // '/// return stack pointer' // 'pub rp: usize,'
             // ''
             // '/// data stack size, cells' // 'pub dsz: usize,'
             // '/// data stack' // 'd: Vec<isize>,'
             // '/// data stack pointer' // 'pub dp: usize,'
             )
        p.forth // p.forth.struct
        #
        p.forth.impl = \
            (S('impl Forth {', '}', pfx='')
             // (Fn('default', [], 'Self')
                 // 'Forth::new(Msz, Rsz, Dsz)')
             // (Fn('new', ['ms: usize', 'rs: usize', 'ds: usize'], 'Self'))
             ); p.forth // p.forth.impl
        #
        self.initf(p)

    def initf(self, p):
        p.lib.init = File('init', '.f', comment='\\'); p.lib // p.lib.init
        p.lib.init \
            // '\\ system init' \
            // '\\ this is single line comment in FORTH language prefixed with \\' \
            // '' // '\\ numbers' \
            // '-01 +02.30 +5e-5 0xDeadBeef 0b1101' \
            // '? \\ print data stack' \
            // '. \\ clean data stack' \
            // '? \\ must be empty'

    def mk(self, p):
        p.mk.meta[0].value += ' forth'

## SCADA/IoT platform
## @ingroup mods
class SCADA(Actix):
    def mk(self, p):
        p.mk.meta[0].value += ' scada'

    def apt(self, p):
        super().apt(p)
        p.dev // 'sqlitebrowser'
        p.apt // 'sqlite3'

## @ingroup mods
class Java(Mod):
    def extensions(self, p):
        p.ext // '"redhat.java",'

    def dirs(self, p):
        p.lib.giti.ins(0, '*.jar')

    def mk(self, p):
        p.mk.dir \
            // f'{"CP":<7} = bin' \
            // f'{"PKDIR":<7} = src/$(shell echo $(PACKAGE) | sed "s/\./\//g" )'
        #
        p.mk.jar = \
            (Sec('jar', pfx='')
             // 'GJF_VER        = 1.7'
             // 'GJF_JAR        = google-java-format-$(GJF_VER).jar'
             // 'GJF            = lib/$(GJF_JAR)'
             // ''
             // 'JUNIT_VER      = 4.13.2'
             // 'JUNIT_JAR      = junit-$(JUNIT_VER).jar'
             // 'JUNIT          = lib/$(JUNIT_JAR)'
             // 'CP            += $(JUNIT)'
             // ''
             // 'HAMCREST_VER   = 2.2'
             // 'HAMCREST_JAR   = hamcrest-$(HAMCREST_VER).jar'
             // 'HAMCREST       = lib/$(HAMCREST_JAR)'
             // 'CP            += $(HAMCREST)'
             )
        p.mk.before(p.mk.tool, p.mk.jar)
        #
        p.mk.tool \
            // f'{"JAVA":<7} = $(JAVA_HOME)/bin/java' \
            // f'{"JAVAC":<7} = $(JAVA_HOME)/bin/javac'
        p.mk.src \
            // f'J += $(shell find $(PKDIR) -type f -regex ".+.java$$")' \
            // f'S += $(J)'
        p.mk.cfg \
            // f'{"CLASS":<7} = $(shell echo $(J) | sed "s|\.java|.class|g" | sed "s|src/|bin/|g")' \
            // f'{"JPATH":<7} = -cp $(shell echo $(CP) | sed "s/ /:/g")' \
            // f'{"JFLAGS":<7} = -d $(BIN) $(JPATH)'
        p.mk.all.value += ' test format'
        p.mk.format.value += ' tmp/format_java'
        p.mk.all_.after(p.mk.format,
                        (S('tmp/format_java: $(J)')
                         // '$(JAVA) $(JPATH) -jar $(GJF) --replace $^'
                         // 'touch $@'))
        p.mk.test.value += ' $(CLASS)'
        p.mk.test \
            // (S('$(JAVA) $(JPATH) \\')
                // 'org.junit.runner.JUnitCore $(TESTS)')
        #
        p.mk.rule \
            // (S('$(CLASS): $(J)')
                // '$(JAVAC) $(JFLAGS) $^'
                // '$(MAKE) format')
        #
        p.mk.install.ins(0, '$(MAKE) gjf junit')
        p.mk.install_ \
            // (S('$(GJF):', pfx='\ngjf: $(GJF)')
                // '$(CURL) $@ https://github.com/google/google-java-format/releases/download/google-java-format-$(GJF_VER)/google-java-format-$(GJF_VER)-all-deps.jar')
        p.mk.install_ \
            // (S('$(JUNIT):', pfx='junit: $(JUNIT) $(HAMCREST)')
                // '$(CURL) $@ https://search.maven.org/remotecontent?filepath=junit/junit/$(JUNIT_VER)/$(JUNIT_JAR)')
        p.mk.install_ \
            // (S('$(HAMCREST):', pfx='hamcrest: $(HAMCREST)')
                // '$(CURL) $@ https://search.maven.org/remotecontent?filepath=org/hamcrest/hamcrest/$(HAMCREST_VER)/$(HAMCREST_JAR)')
        #
        p.mk.zip.drop() // 'zip $(ZIP) lib/*.jar'

    def apt(self, p):
        p.dev // 'default-jdk-headless'
        # //'libantlr-dev'

class netCracker(Mod):
    def dirs(self, p):
        com = Dir('com')
        nc = Dir('nc')
        edu = Dir('edu')
        ta = Dir('ta')
        ponyatov = Dir('ponyatov')
        pr1 = Dir('pr1')
        p.src // com; com // nc; nc // edu; edu // ta; ta // ponyatov; ponyatov // pr1

    def mk(self, p):
        p.mk.all_.before(p.mk.test,
                         (Sec(pfx='')
                          // 'TESTS += $(PACKAGE).test.MyTest'
                          // 'TESTS += $(PACKAGE).test.TaskTest'))

## object (hyper)graph functional core
## @ingroup mods
class Fun(Mod):
    def src(self, p):
        self.imports(p)
        self.core(p)

    def imports(self, p):
        p.py // (Sec(pfx='')
                 // 'import os, sys, re, time'
                 // 'import datetime as dt')

    def core(self, p):
        self.object(p)
        self.primitive(p)
        self.container(p)
        self.active(p)

    def primitive(self, p):
        p.py.prims = Sec('primitive', pfx='')
        p.py.prim = Class('Primitive', [p.py.object])
        p.py // (p.py.prims // p.py.prim)
        #
        p.py.prim \
            // (Meth('eval', ['env'],
                     pfx='## most primitives evaluates into itself')
                // 'return self')
        #
        p.py.prims \
            // (Class('S', [p.py.prim],
                      pfx='\n## strings can be nested: source code tree')
                // (Meth('__init__', ['V=None', 'end=None', 'pfx=None', 'sfx=None'])
                    // 'super().__init__(V)'
                    // 'self.end = end; self.pfx = pfx; self.sfx = sfx'
                    )
                )

    def container(self, p):
        p.py.conts = Sec('container', pfx='')
        p.py.cont = Class('Container', [p.py.object])
        p.py // (p.py.conts // p.py.cont)
        #
        p.py.map = Class('Map', [p.py.cont]); p.py.conts // p.py.map
        #
        p.py.stack = Class('Stack', [p.py.cont]); p.py.conts // p.py.stack
        #
        p.py.vector = Class('Vector', [p.py.cont]); p.py.conts // p.py.vector
        #
        p.py.queue = Class('Queue', [p.py.cont]); p.py.conts // p.py.queue

    def active(self, p):
        p.py.actives = Sec('active', pfx='')
        p.py.active = Class('Active', [p.py.object])
        p.py // (p.py.actives // p.py.active)

    def object_init(self):
        return (Meth('__init__', ['V'], pfx=None, sfx='')
                // (S("self.type = self.__class__.__name__.lower()",
                      pfx='## type/class tag (required for PLY)'))
                // (S("self.value = V",
                      pfx='## scalar: object name, string/number value'))
                // (S("self.slot = {}",
                      pfx='## associative array = map = env/namespace = attributes'))
                // (S("self.nest = []",
                      pfx='## ordered container = vector = stack = AST sub-edges'))
                // (S("self.gid = id(self)",
                      pfx='## unical global id')))

    def box(self):
        return (Meth('box', ['that'], pfx='## Python types wrapper')
                // "if isinstance(that, Object): return that"
                // "if isinstance(that, str): return S(that)"
                // "raise TypeError(['box', type(that), that])")

    def dumps(self):
        return (Sec()
                // (Meth('test', [], pfx='## pytest callback', sfx='')
                    // 'return self.dump(test=True)')
                // (Meth('__repr__', [], pfx='## `print` callback', sfx='')
                    // 'return self.dump(test=False)')
                // self.dump()
                // self.head()
                // (Meth('tag', [], sfx='')
                    // 'return self.type')
                // (Meth('val', [], sfx='')
                    // "return f'{self.value}'")
                // self.format()
                )

    def format(self):
        return (Meth('__format__', ["spec=''"])
                // "if not spec: return f'{self.value}'"
                // "elif spec == 'l': return f'{self.value.lower()}'"
                // "else: raise TypeError(['__format__', spec])")

    def head(self):
        return (Meth('head', ["prefix=''", 'test=False'],
                     pfx='## short `<T:V>` header', sfx='')
                // "gid = '' if test else f' @{self.gid:x}'"
                // "return f'{prefix}<{self.tag()}:{self.val()}>{gid}'")

    def dump(self):
        return (Meth('dump', ['cycle=[]', 'depth=0', "prefix=''", 'test=False'],
                     pfx='## full text tree dump', sfx='')
                // '# head'
                // "def pad(depth): return '\\n' + '\\t' * depth"
                // "ret = pad(depth) + self.head(prefix, test)"
                // '# cycle break'
                // "if not depth: cycle = [] # init"
                // "if self in cycle: return ret + ' _/'"
                // "else: cycle.append(self)"
                // (S('for i in self.keys():', pfx='# slot{}s')
                    // "ret += self[i].dump(cycle, depth + 1, f'{i} = ', test)")
                // (S('for j, k in enumerate(self):', pfx='# nest[]ed')
                    // "ret += k.dump(cycle, depth + 1, f'{j}: ', test)")
                // '# subtree'
                // 'return ret')

    def object(self, p):
        p.py.object = Class('Object', pfx='\n## object (hyper)graph node')
        p.py // p.py.object
        #
        p.py.object \
            // (Sec()
                // self.object_init()
                // self.box()
                )
        #
        p.py.object \
            // (Sec()
                // S('## @name text dump & serialization', pfx='', sfx='')
                // self.dumps()
                )
        #
        p.py.object \
            // (Sec()
                // S('## @name operator', pfx='', sfx='')
                // self.operator()
                )

    def operator(self):
        return (Sec()
                // (Meth('keys', [], pfx='## get slot names in order', sfx='')
                    // 'return sorted(self.slot.keys())')
                // (Meth('__iter__', [], pfx='## iterate over subtree', sfx='')
                    // 'return iter(self.nest)')
                // self.getitem()
                // self.setitem()
                // self.lshift()
                // self.rshift()
                // self.floordiv()
                // self.ins()
                // self.remove()
                )

    def getitem(self):
        return (Meth('__getitem__', ['key'],
                     pfx='## `A[key]` get from slot', sfx='')
                // "if isinstance(key, str): return self.slot[key]"
                // "if isinstance(key, int): return self.nest[key]"
                // "raise TypeError(['__getitem__', type(key), key])")

    def setitem(self):
        return (Meth('__setitem__', ['key', 'that'],
                     pfx='## `A[key] = B` set slot', sfx='')
                // "that = self.box(that)"
                // "if isinstance(key, str): self.slot[key] = that; return self"
                // "raise TypeError(['__setitem__', type(key), key])")

    def lshift(self):
        return (Meth('__lshift__', ['that'],
                     pfx='## `A << B ~> A[B.type] = B`', sfx='')
                // "that = self.box(that)"
                // "return self.__setitem__(that.tag(), that)")

    def rshift(self):
        return (Meth('__rshift__', ['that'],
                     pfx='## `A >> B ~> A[B.value] = B`', sfx='')
                // "that = self.box(that)"
                // "return self.__setitem__(that.val(), that)")

    def floordiv(self):
        return (Meth('__floordiv__', ['that'],
                     pfx='## `A // B ~> A.push(B)` push as stack', sfx='')
                // "that = self.box(that)"
                // "self.nest.append(that); return self")

    def ins(self):
        return (Meth('ins', ['idx', 'that'],
                     pfx='## insert at index', sfx='')
                // "assert isinstance(idx, int)"
                // "that = self.box(that)"
                // "self.nest.insert(idx, that); return self"
                )

    def remove(self):
        return (Meth('remove', ['that'],
                     pfx='## remove given object', sfx='')
                // "assert isinstance(that, Object)"
                // "ret = []"
                // (S("for i in self.nest:")
                    // "if i != that: ret.append(i)")
                // "self.nest = ret; return self"
                )

## Flask project
## @ingroup
class Flask(Mod):
    def reqs(self, p):
        p.reqs // 'Flask' // 'Flask-SocketIO'

    def dirs(self, p):
        p.static = Dir('static'); p.d // p.static
        #
        p.templates = Dir('templates'); p.d // p.templates
        p.all = htmlFile('all'); p.templates // p.all
        p.index = htmlFile('index'); p.templates // p.index
        p.index // "{% extends 'all.html' %}"

    def src(self, p):
        p.py.imp // 'import flask'
        p.py.init[0].drop() \
            // "app = flask.Flask(__name__)" \
            // "app.run(debug=True, host=HOST, port=PORT)"


## Smalltalkish projects
## @ingroup mods
class ST(Mod):
    def readme(mk, p):
        super().readme(p)
        if not p.ABOUT:
            p.ABOUT += '''
* http://som-st.github.io/
  * https://github.com/Hirevo/som-rs
  * https://github.com/softdevteam/yksom/
'''

    def mk(self, p):
        super().mk(p)
        p.mk.doc.value += ' doc/moser.pdf doc/Bluebook.pdf doc/ALittleSmalltalk.pdf doc/PERQ.pdf'
        p.mk.doc_ \
            // (S('doc/moser.pdf:')
                // '$(CURL) $@ https://www.heinzi.at/texte/smalltalk.pdf')
        p.mk.doc_ \
            // (S('doc/Bluebook.pdf:')
                // '$(CURL) $@ http://stephane.ducasse.free.fr/FreeBooks/BlueBook/Bluebook.pdf')
        p.mk.doc_ \
            // (S('doc/ALittleSmalltalk.pdf:')
                // '$(CURL) $@ http://rmod-files.lille.inria.fr/FreeBooks/LittleSmalltalk/ALittleSmalltalk.pdf')
        p.mk.doc_ \
            // (S('doc/PERQ.pdf:')
                // '$(CURL)	$@ http://www.wolczko.com/msc.pdf')
## LaTeX documenting project
## @ingroup mods
class TeX(Mod):

    def apt(self, p):
        p.dev // 'texlive-latex-extra texlive-lang-cyrillic ghostscript'

    def mk(self, p):
        p.mk.var // f'{"MONTH":<7} = $(shell LANG=C date +%b%y)'
        p.mk.tool // f'{"LATEX":<7} = pdflatex -halt-on-error --output-dir=$(TMP)'
        p.mk.src \
            // f'{"TEX":<3}  = doc/$(MONTH).tex doc/header.tex doc/about.tex doc/bib.tex' \
            // f'{"TEX":<3} += doc/linux/$(MONTH).tex doc/meh/$(MONTH).tex' \
            // f'{"S":<3} += $(TEX)'
        p.mk.all_.before(p.mk.all, 'PDF = $(MODULE)_$(MONTH)_$(NOW).pdf')
        p.mk.all.value += ' pdf'
        p.mk.all_.after(p.mk.all,
                        (Sec()
                         // (S('tmp/$(PDF): tmp/$(MONTH).pdf', pfx='\npdf: tmp/$(PDF)')
                             // (S('gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dPDFSETTINGS=/screen \\')
                                 // '-dNOPAUSE -dQUIET -dBATCH \\'
                                 // '-sOutputFile=$@ $<'
                                 )
                             // 'ls -la tmp/*.pdf'
                             )
                            // (S('tmp/$(MONTH).pdf: $(TEX) $(IMG)')
                                // 'cd doc ; $(LATEX) $(MONTH) && $(LATEX) $(MONTH)')
                         ))

    def extensions(self, p):
        p.ext // '"james-yu.latex-workshop",'

    def settings(self, p):
        p.settings[0] \
            // (Sec('latex', pfx='')
                // '"latex-workshop.latex.external.build.command": "make",'
                // '"latex-workshop.latex.outDir": "./tmp",'
                // '"latex-workshop.view.pdf.viewer": "tab",'
                // '"latex-workshop.view.pdf.zoom": "page-fit",'
                )

## Rust Interpreter Toolkit
## @ingroup mods
class RIT(Mod):

    def src(self, p):
        super().src(p)
        self.asm(p)
        self.bytecode(p)
        self.vm(p)
        self.types(p)

    def asm(self, p):
        p.asm = rsFile('asm'); p.src // p.asm
        p.main.mod // 'mod asm;'

    def bytecode(self, p):
        p.bytecode = rsFile('bytecode'); p.src // p.bytecode
        p.main.mod.ins(0, 'mod bytecode;')

    def vm(self, p):
        p.vm = rsFile('vm'); p.src // p.vm
        p.main.mod // 'mod vm;'

    def types(self, p):
        p.types = rsFile('types'); p.src // p.types
        p.main.mod // 'mod types;'

## embedded Buildroot
class Buildroot(Mod):

    def apt(self, p):
        p.dev // 'rsync'

    def giti(self, p):
        p.giti // '/buildroot-*/' // ''

    def settings(self, p):
        p.exclude // '"buildroot-*/*":true,'
        p.watcher // '"buildroot-*/**":true,'

    def mk(self, p):
        p.mk.ver // f'{"BUILDROOT_VER":<13} = 2021.05.2'
        p.mk.dir // f'{"GZ":<7} = $(HOME)/gz'
        #
        p.mk.cfg // (Sec()
                     // f'{"BUILDROOT":<13} = buildroot-$(BUILDROOT_VER)'
                     // f'{"BUILDROOT_GZ":<13} = $(BUILDROOT).tar.gz'
                     // f'{"BUILDROOT_URL":<13} = https://github.com/buildroot/buildroot/archive/refs/tags/$(BUILDROOT_VER).tar.gz'
                     )
        #
        p.mk.rule \
            // (S('%/README: $(GZ)/%.tar.gz')
                // 'tar zx < $< && touch $@'
                )
        #
        p.mk.gz = (Sec()
                   // S('gz: $(GZ)/$(BUILDROOT_GZ)', pfx='\n.PHONY: gz')
                   // (S('$(GZ)/$(BUILDROOT_GZ):')
                       // '$(CURL) $@ $(BUILDROOT_URL)'))
        p.mk.install_ // p.mk.gz
        #
        p.mk.buildroot = \
            (S('buildroot: $(BUILDROOT)/README',
               pfx='\n.PHONY: buildroot')
             // 'cd $(BUILDROOT) ; rm .config ; make allnoconfig ;\\'
             // 'cat ../all/br >> .config ;\\'
             // 'cat ../arch/$(APP) >> .config ;\\'
             // 'cat ../cpu/$(APP) >> .config ;\\'
             // 'cat ../hw/$(APP) >> .config ;\\'
             // 'cat ../app/$(APP) >> .config ;\\'
             // 'echo "BR2_DL_DIR=\\"$(GZ)\\"" >> .config ;\\'
             // 'make menuconfig && make'
             )
        p.mk.install_ // p.mk.buildroot

    def src(self, p):
        p.app = Dir('app'); p.d // p.app
        p.hw = Dir('hw'); p.d // p.hw
        self.qemu(p)
        p.cpu = Dir('cpu'); p.d // p.cpu
        self.i486(p)
        p.arch = Dir('arch'); p.d // p.arch
        self.i386(p)
        self.all(p)

    def all(self, p):
        p.all = Dir('all'); p.d // p.all
        p.all.br = File('br'); p.all // p.all.br
        p.all.kr = File('kr'); p.all // p.all.kr

    def qemu(self, p):
        p.qemu386_mk = mkFile('qemu386', '.mk') // 'CPU = i486'
        p.qemu386_br = File('qemu386', '.br')
        p.hw // p.qemu386_mk // p.qemu386_br

    def i486(self, p):
        p.i486_mk = mkFile('i486', '.mk') // 'ARCH = i386'
        p.i486_br = File('i486', '.br') // 'BR2_x86_i486=y'
        p.cpu // p.i486_mk // p.i486_br

    def i386(self, p):
        p.i386_mk = mkFile('i386', '.mk')
        p.i386_br = File('i386', '.br') // 'BR2_i386=y'
        p.arch // p.i386_mk // p.i386_br

## Linux kernel hacks
## @ingroup mods
class Kernel(Buildroot):

    def apt(self, p):
        super().apt(p)
        p.dev // 'qemu-system-i386'

    def src(self, p):
        super().src(p)
        p.driver_br = File('driver', '.br'); p.app // p.driver_br

    def mk(self, p):
        super().mk(p)
        p.mk.var \
            // f'{"APP":<7} = driver' \
            // f'{"HW":<7} = qemu386' \
            // 'include hw/$(HW).mk' \
            // 'include cpu/$(CPU).mk' \
            // 'include arch/$(ARCH).mk'
        p.mk.linux // 'sudo apt install -u linux-headers-`uname -r`'

## empty project initialization
## @ingroup mods
class Ini(Mod):
    def sync(self, p):
        super().sync(p)
        for i in [
            'ln -fs ~/metaL.py metaL.py',
            f'mv {p}/* ./ ; mv {p}/.* ./ ',
            'git init',
            'git checkout --orphan shadow',
        ]: os.system(i)
        # 'git add Makefile README.md',
        # 'git commit -a -m "."',
        # 'git push -v -u bb shadow',

    def meta(self, p): pass

if __name__ == '__main__':
    # if sys.argv[1] == 'meta':
    #      | metaL()
    # elif sys.argv[1] == 'rs':
    #     p = Project() | Rust()
    # else:
    #     raise SyntaxError(['init', sys.argv])
    # #
    p = Project()
    for mod in sys.argv[1:]:
        p = p | {
            'ini': Ini(),
            'rs': Rust(),
            'rit': RIT(),
            'py': Python(),
            'fun': Fun(),
            'dj': Django(),
            'flask': Flask(),
            'java': Java(),
            'nec': netCracker(),
            'web': Rocket(),
            'game': Game(),
            'scada': SCADA(),
            'yew': Yew(),
            'tex': TeX(),
            'kernel': Kernel(),
            'st': ST(),
        }[mod]
    #
    p.sync()

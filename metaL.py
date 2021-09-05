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
        if not depth: cyce = [] # init
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
    def drop(self, num=1):
        for i in range(num): self.nest.pop(-1)
        return self

    ## @name functional evaluation

    def eval(self, env):
        raise NotImplementedError(['eval', self, env])

    def apply(self, that, env):
        assert isinstance(that, Object)
        raise NotImplementedError(['apply', self, that, env])

## @defgroup primitive
## @ingroup core

## @ingroup primitive
class Primitive(Object):
    def __init__(self, V=None):
        super().__init__(V)
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


## @defgroup Container
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

## @defgroup io
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

## @defgroup file
## @ingroup io

## @ingroup file
class File(IO):
    def __init__(self, V, ext, tab=' ' * 4, comment='#'):
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

## @defgroup active
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


## @defgroup net
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


## @defgroup meta
## @ingroup core

## @ingroup meta
class Meta(Object): pass

class Class(Meta):
    def __init__(self, C, sup=[]):
        if isinstance(C, Object):
            super().__init__(C.__name__)
        elif isinstance(C, str):
            super().__init__(C)
        else:
            raise TypeError(['Class', type(C), C])
        #
        self.sup = sup

    def gen(self, to, depth=0):
        if self.sup:
            sups = '(%s)' % \
                ', '.join(
                    map(lambda i: f'{i.value}',
                        self.sup))
        else: sups = ''
        pas = '' if self.nest else ' pass'
        ret = S(f'class {self.value}{sups}:{pas}', pfx='')
        for i in self: ret // i
        return ret.gen(to, depth)

## @ingroup meta
class Module(Meta): pass

## @defgroup mods
## @brief functional Project modificators
## @ingroup meta

## Project functional modificator
## @ingroup mods
class Mod(Module):
    def __init__(self):
        super().__init__(self.tag())

    def pipe(self, p):
        self.dirs(p)
        self.giti(p)
        self.package(p)
        self.apt(p)
        self.mk(p)
        self.src(p)
        self.tasks(p)
        self.settings(p)
        self.extensions(p)
        self.meta(p)
        self.reqs(p)
        return p // self

    def sync(self, p):
        print(self.head(), p.head())

    def apt(self, p): pass
    def dirs(self, p): pass
    def giti(self, p): pass
    def package(self, p): pass
    def mk(self, p): pass
    def src(self, p): pass
    def tasks(self, p): pass
    def settings(self, p): pass
    def extensions(self, p): pass
    def reqs(self, p): pass
    def meta(self, p): p.meta.p // self

## @ingroup file
class jsonFile(File):
    def __init__(self, V='', ext='.json', tab=' ' * 4, comment='//'):
        super().__init__(V, ext, tab, comment)

## @ingroup file
class Makefile(File):
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
        self.dirs()
        self.apt()
        self.vscode()
        self.mk()
        self.readme()
        self.meta()
        self.doxy()

    def apt(self):
        self.dev = File('apt', '.dev'); self.d // self.dev
        self.dev // 'code meld doxygen'
        self.apt = File('apt', '.txt'); self.d // self.apt
        self.apt \
            // 'git make curl' \
            // 'python3 python3-venv'

    def meta(self):
        self.meta = pyFile(f'{self}.metaL'); self.d // self.meta
        self.meta.p = Vector('mod')# // self

    def sync_meta(self):
        p = \
            'p = Project(\n' +\
            f"    title='{self.TITLE}',\n" +\
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
        self.doxy \
            // (Sec()
                // f'{"PROJECT_NAME":<22} = "{self}"'
                // f'{"PROJECT_BRIEF":<22} = "{self.TITLE}"'
                // f'{"PROJECT_LOGO":<22} = doc/logo.png'
                // f'{"OUTPUT_DIRECTORY":<22} ='
                // f'{"WARN_IF_UNDOCUMENTED":<22} = NO'
                // f'{"INPUT":<22} = README.md src metaL.py {self}.py'
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
            // f'# ![logo](doc/logo.png) `{self}`' \
            // f'## {self.TITLE}' \
            // f'\n(c) {self.AUTHOR} <<{self.EMAIL}>> {self.YEAR} {self.LICENSE}' \
            // f'\ngithub: {self.GITHUB}/{self}/' \
            // f'\n{self.ABOUT}'

    def __or__(self, that):
        assert isinstance(that, Mod)
        return that.pipe(self)

    def mk(self):
        self.mk = Makefile(); self.d // self.mk
        self.mk // (Sec('var')
                    // f'{"MODULE":<7} = $(notdir $(CURDIR))'
                    // f'{"OS":<7} = $(shell uname -s)'
                    // f'{"NOW":<7} = $(shell date +%d%m%y)'
                    // f'{"REL":<7} = $(shell git rev-parse --short=4 HEAD)'
                    // f'{"BRANCH":<7} = $(shell git rev-parse --abbrev-ref HEAD)'
                    // f'{"CORES":<7} = $(shell grep processor /proc/cpuinfo| wc -l)'
                    )
        self.mk.dir = \
            (Sec('dir', pfx='')
             // f'{"CWD":<7} = $(CURDIR)'
             // f'{"BIN":<7} = $(CWD)/bin'
             // f'{"DOC":<7} = $(CWD)/doc'
             // f'{"LIB":<7} = $(CWD)/lib'
             // f'{"SRC":<7} = $(CWD)/src'
             // f'{"TMP":<7} = $(CWD)/tmp'
             // f'{"PYPATH":<7} = $(HOME)/.local/bin')
        self.mk // self.mk.dir
        #
        self.mk.tool = (Sec('tool', pfx='')
                        // f'{"CURL":<7} = curl -L -o')
        self.mk.tool.py = (Sec()
                           // f'{"PY":<7} = $(shell which python3)'
                           // f'{"PIP":<7} = $(shell which pip3)'
                           // f'{"PEP":<7} = $(PYPATH)/autopep8'
                           // f'{"PYT":<7} = $(PYPATH)/pytest')
        self.mk // (self.mk.tool // self.mk.tool.py)
        #
        self.mk.src = (Sec('src', pfx='')
                       // 'Y += $(MODULE).py $(MODULE).metaL.py metaL.py'
                       // 'S += $(Y)')
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
            (S('meta: $(PY) $(MODULE).metaL.py', pfx='')
             // '$^'
             // '$(MAKE) format')
        #
        self.mk.all = (S('all:', pfx=''))
        self.mk.test = (S('test:', pfx=''))
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
            (S('doxy:')
             // 'rm -rf docs ; doxygen doxy.gen 1>/dev/null')
        self.mk.doc_ // self.mk.doxy
        self.mk.doc = (S('doc:')); self.mk.doc_ // self.mk.doc
        #
        self.mk.install_ = Sec('install', pfx='')
        self.mk.install = (S('install: $(OS)_install doc') // '$(MAKE) update')
        self.mk.install_ // self.mk.install
        #
        self.mk.update = (S('update: $(OS)_update'))
        self.mk.install_ // self.mk.update
        #
        self.mk.update.py = (Sec()
                             // '$(PIP) install --user -U pytest autopep8')
        self.mk.update // self.mk.update.py
        #
        self.mk.install_ \
            // (S('Linux_install Linux_update:',
                  pfx='', sfx='endif')
                // S('sudo apt update', pfx='\nifneq (,$(shell which apt))')
                // 'sudo apt install -u `cat apt.txt apt.dev`')
        self.mk // self.mk.install_
        #
        self.mk.merge_ = Sec('merge', pfx=''); self.mk // self.mk.merge_
        self.mk.merge = \
            (Sec()
                // 'MERGE  = Makefile README.md .gitignore apt.dev apt.txt $(S)'
                // 'MERGE += .vscode bin doc lib src tmp')
        self.mk.merge_ \
            // self.mk.merge \
            // (S('ponymuck:', pfx='\n.PHONY: ponymuck')
                // 'git push -v'
                // 'git checkout $@'
                // 'git pull -v'
                ) \
            // (S('dev:', pfx='\n.PHONY: dev')
                // 'git push -v'
                // 'git checkout $@'
                // 'git pull -v'
                // 'git checkout ponymuck -- $(MERGE)'
                ) \
            // (S('release:', pfx='\n.PHONY: release')
                // 'git tag $(NOW)-$(REL)'
                // 'git push -v --tags'
                // '$(MAKE) ponymuck'
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

    def vsTask(self, group, target):
        return (S('{', '},')
                // f'"label":          "{group}: {target}",'
                // f'"type":           "shell",'
                // f'"command":        "make {target}",'
                // f'"problemMatcher": []'
                )

    def tasks(self):
        self.tasks = jsonFile('tasks'); self.vscode // self.tasks
        self.tasks.task = (S('"tasks": [', ']')
                           // self.vsTask('project', 'install')
                           // self.vsTask('project', 'update')
                           // self.vsTask('git', 'ponymuck')
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
        self.exclude = (S('"files.exclude": {', '},')
                        // f'"**/{self}/**":true, "**/docs/**":true,'
                        // '"**/__pycache__/**":true,'
                        )
        self.watcher = (S('"files.watcherExclude": {', '},'))
        self.assoc = (S('"files.associations": {', '},'))
        self.files = (Sec('files', pfx='')
                      // self.exclude // self.watcher // self.assoc)
        #
        self.editor = (Sec('editor', pfx='')
                       // '"editor.tabSize": 4,'
                       // '"editor.rulers": [80],'
                       // '"workbench.tree.indent": 32,')
        #
        self.settings // (S('{', '}') // self.multi //
                          self.files // self.editor)

    def giti(self):
        self.giti = giti(); self.d // self.giti
        self.giti.py = (Sec(sfx='')
                        // '/__pycache__/')
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
                       // f'{"chrono":<22} = "0.4"'
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
                       )
        p.toml // p.toml.unix
        #
        p.toml.win = (Sec(pfx="\n[target.'cfg(windows)'.dependencies]")
                      // f'{"windows":<22} = "0.19"'
                      )
        p.toml // p.toml.win

    def settings(self, p):
        p.exclude.rust = \
            (Sec()
             // '"**/target/**":true, "**/Cargo.lock":true')
        p.exclude // p.exclude.rust; p.watcher // p.exclude.rust

    def extensions(self, p):
        p.ext // '"rust-lang.rust",' // '"bungcip.better-toml",'

    def mk(self, p):
        p.mk.dir \
            // f'{"CAR":<7} = $(HOME)/.cargo/bin'
        p.mk.tool \
            // (Sec()
                // f'{"RUSTUP":<7} = $(CAR)/rustup'
                // f'{"CARGO":<7} = $(CAR)/cargo'
                // f'{"CWATCH":<7} = $(CAR)/cargo-watch'
                // f'{"RUSTC":<7} = $(CAR)/rucstc'
                )
        #
        p.mk.rust = \
            (S('rust:', pfx='')
             // '$(CWATCH) -w Cargo.toml -w src -x test -x fmt -x run')
        p.mk.all // p.mk.rust
        #
        p.mk.meta[0].value += ' rs'
        p.mk.install.value += ' $(RUSTUP)'
        p.mk.update \
            // '$(RUSTUP) update && $(CARGO) update'
        p.mk.install_ \
            // (S('$(RUSTUP):', pfx='')
                // 'curl --proto \'=https\' --tlsv1.2 -sSf https://sh.rustup.rs | sh')

    def src(self, p):
        self.main(p)
        self.test(p)

    def main(self, p):
        p.main = rsFile('main'); p.src // p.main
        p.main.config = Sec('config', sfx=''); p.main // p.main.config
        p.main.mod = Sec('mod') // 'mod test;'; p.main // p.main.mod
        #
        p.main.extern = Sec('extern', pfx=''); p.main // p.main.extern
        p.main.extern // 'extern crate tracing;'
        #
        p.main.use = Sec('use', pfx=''); p.main // p.main.use
        p.main.use // 'use tracing::{info, instrument};'
        #
        p.main.main = Fn('main', pfx='\n#[instrument]'); p.main // p.main.main
        #
        p.main.args = \
            (Sec('args')
             // 'let argv: Vec<String> = std::env::args().collect();'
             // 'let argc = argv.len();'
             // 'info!("start #{:?} {:?}", argc, argv);')
        p.main.main.atexit = (Sec('atexit') // 'info!("stop");')
        p.main.main \
            // 'tracing_subscriber::fmt().compact().init();' \
            // p.main.args \
            // p.main.main.atexit
        #
        p.main.web = Sec('web', pfx=''); p.main // p.main.web

    def test(self, p):
        p.test = rsFile('test'); p.src // p.test
        p.test // '#[cfg(test)]'
        p.test // (Fn('any', pfx='#[test]') // 'assert_eq!(1, 1);')

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

    def mk(self, p):
        p.mk.update // '$(PIP) install --user -U -r requirements.txt'
        p.mk.merge // 'MERGE += requirements.txt'

    def src(self, p):
        p.py = pyFile(f'{p}'); p.d // p.py
        self.reqs(p)

    def reqs(self, p):
        p.reqs = File('requirements', '.txt'); p.d // p.reqs

## Django project
## @ingroup mods
class Django(Mod):
    def reqs(self, p):
        assert p.py
        p.reqs // 'Django'

## @defgroup circular
## @brief `metaL` circulat implementation

## @ingroup circular
class metaL(Python):
    def mk(self, p):
        super().mk(p)
        p.mk.meta[0].value += ' meta'

    def giti(self, p):
        p.lib.giti.ins(0, 'python*/')

    def src(self, p):
        p.m = pyFile('metaL'); p.d // p.m
        self.imports(p)
        self.core(p)

    def imports(self, p):
        p.m.top // '#!/usr/bin/env python3'
        p.m // (Sec(pfx='')
                // '## @file'
                // f'## @brief {p.TITLE}')
        p.m // (Sec(pfx='')
                // 'import os, sys, re, time'
                // 'import datetime as dt')

    def core(self, p):
        self.object(p)
        self.primitive(p)
        self.container(p)
        self.active(p)
        self.meta(p)
        self.io(p)
        self.net(p)
        self.web(p)

    def object_init(self):
        return (Meth('__init__', ['V'], pfx=None, sfx='')
                // (S("self.type = self.tag()",
                      pfx='## type/class tag /required for PLY/'))
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

    def format(self):
        return (Meth('__format__', ["spec=''"])
                // "if not spec: return f'{self.value}'"
                // "if spec == 'l': return f'{self.value.lower()}'"
                // "raise TypeError(['__format__', spec])")

    def head(self):
        return (Meth('head', ["prefix=''", 'test=False'],
                     pfx='## short `<T:V>` header', sfx='')
                // "gid = '' if test else f' @{self.gid:x}'"
                // "return f'{prefix}<{self.tag()}:{self.val()}>{gid}'")

    def dump(self):
        return Meth('dump', ['cycle=[]', 'depth=0', "prefix=''", 'test=False'],
                    pfx='## full text tree dump', sfx='')

    def object(self, p):
        p.m.object = Class('Object')
        p.m // p.m.object
        p.m.object \
            // (Sec()
                // self.object_init()
                // self.box()
                )
        p.m.object \
            // (Sec() // S('## @name text dump & serialization', pfx='', sfx='')
                // (Meth('test', [], pfx='## pytest callback', sfx='')
                    // 'return self.dump(test=True)')
                // (Meth('__repr__', [], pfx='## `print` callback', sfx='')
                    // 'return self.dump(test=False)')
                // self.dump()
                // self.head()
                // (Meth('tag', [], sfx='')
                    // 'return self.__class__.__name__.lower()')
                // (Meth('val', [], sfx='')
                    // "return f'{self.value}'")
                // self.format()
                )
        p.m.object \
            // (Sec() // S('## @name operator', pfx='', sfx='')
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
        p.m.object \
            // (Sec()
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

    def primitive(self, p):
        p.m.prim = Class('Primitive', [p.m.object])
        p.m // p.m.prim

    def container(self, p):
        p.m.cont = Class('Container', [p.m.object])
        p.m // p.m.cont

    def active(self, p):
        p.m.active = Class('Active', [p.m.object])
        p.m // p.m.active

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

    def mk(self, p):
        p.mk.meta[0].value += ' game'

    def package(self, p):
        p.toml.deps \
            // 'sdl2 = { version = "0.34", features = ["image"] }' \
            // '# features = ["ttf","gfx","mixer"]'

    def src(self, p):
        p.main.extern.ins(0, 'extern crate sdl2;')
        p.main.main.ins(-1, 'game_loop(argv[0].clone());')
        #
        p.main.game = (Sec('game', pfx='')); p.main // p.main.game
        p.main.config // (Sec('game', pfx='')
                          // '// default screen window width'
                          // 'pub const W: u16 = 640;'
                          // '// default screen window height'
                          // 'pub const H: u16 = 480;'
                          )
        #
        p.main.game \
            // (S('pub struct Game {', '}', pfx='\n#[allow(dead_code)]')
                // 'pub argv: String,'
                // 'pub w: u16,'
                // 'pub h: u16,'
                // 'pub sdl: sdl2::Sdl,'
                // 'pub video: sdl2::VideoSubsystem,'
                // 'pub window: sdl2::video::Window,'
                // 'pub icon: sdl2::surface::Surface<\'static>,'
                // 'pub events: sdl2::EventPump,'
                // '// pub canvas: sdl2::render::WindowCanvas,'
                )
        #
        p.main.game \
            // (S('impl Game {', '}', pfx='')
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
                // (S('Game {', '}')
                    // 'argv: argv,' // 'w: W,' // 'h: H,'
                    // 'sdl: context,' // 'video: video,'
                    // 'window: window,' // 'icon: icon,'
                    // 'events: event_pump,'
                    )))
        #
        p.main.gameloop = \
            (Fn('game_loop', ['argv: String'], pfx='', sfx='')
             // 'let mut game = Game::new(argv);'
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

## @ingrou
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

## empty project initialization
## @ingroup mods
class Ini(Mod):
    def sync(self, p):
        super().sync(p)
        # os.system('ln -fs ~/metaL.py metaL.py')
        # os.system('git checkout -b ponymuck')
        # os.system('git push -v -u bb ponymuck')
        # os.system(f'mv {p}/* ./ ; mv {p}/.* ./ ')

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
            'py': Python(),
            'java': Java(),
            'nec': netCracker(),
            'web': Rocket(),
            'game': Game(),
            'scada': SCADA(),
            'yew': Yew(),
        }[mod]
    #
    p.sync()

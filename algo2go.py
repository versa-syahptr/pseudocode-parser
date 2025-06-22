#!/usr/bin/env python3

# algo2go.py
# Copyright (C) 2022 Versa Syahputra
# core repo : https://github.com/versa-syahptr/pseudocode-parser
# web IDE   : https://versa.my.id/algo2go/

import os
import re
import subprocess
import sys
from io import StringIO
from textwrap import dedent
from typing import Union, TextIO

TEMPLATE = """\
package main
import "fmt"

"""

grammar = {
    " mod ": "%",
    '<-': '=',
    " then": ' {',
    "else if": "} else if",
    "else\n": "} else {\n",
    "endif": '}',
    " and ": "&&",
    " or ": "||",
    " not ": "!"
}
type_map = {
    "integer": "int",
    "real": "float64",
    "char": "byte",
    "character": "byte",
    "boolean": "bool"
}
block_regex = {
    # --------------- pseudocode ----------------- : ---------------------- golang ----------------------
    # for  var  <- start to   end     actions      :   for  var  = start;  var  <=  end ;  var++ {actions}
    r"for (\w+) <- (\w+) to ([^\n]+) do(.*?)endfor": r"for \g<1> = \g<2>; \g<1> <= \g<3>; \g<1>++{\g<4>}",  # for loop
    #      condition  actions              :    conditions {actions}
    r"while ([^\n]+) do(.*?)\n\s*?endwhile": r"for \g<1> {\g<2>\n}",  # while loop
    #      actions   stop_condition :                                       !stop_condition {actions}
    r"repeat(.*?)until ([^\n]+)": r"for _iterator := true; _iterator; _iterator = !(\g<2>) {\g<1>}"  # repeat until
}

global_chars = []

# hide traceback in production
if "dev" not in os.environ:
    print("prod")
    sys.tracebacklimit = 0


class FormattingError(SyntaxError):
    def __init__(self, msg, raw_code=""):
        code = '\n'.join(["{:2d}\t{}".format(i+1, l).expandtabs(2) for i, l in enumerate(raw_code.splitlines())])
        msg = f"An error occured when formating golang code:\n{msg}\nThis is the raw code generated:\n{code}"
        super().__init__(msg)

def split_param(s: str): return s.split(',')


def join_param(_i): return ','.join(_i)


def error(*a): print(*a, file=sys.stderr)


def split_subprograms(code: str) -> list:
    """
    split subprograms in raw code
    :param code: raw pseudocode
    :return: list of Algorithm instance
    """
    p = re.compile(r"((?<=endprogram)|(?<=endfunction)|(?<=endprocedure))\s*\n*?(?=program|procedure|function)")
    blok = list(filter(bool, p.split(code)))
    return blok


def get_type(t, replace_all=False):
    if replace_all:
        for pseudotype, gotype in type_map.items():
            t = t.replace(pseudotype, gotype)
        return t
    return type_map.get(t, t)


def parse_array(pcd):
    if "array" not in pcd:
        # array not found here, just return it
        return pcd
    #               array --[start.. ------------- end ------------]  of  tipe
    p = re.search(r"array\s\[(\d+)..((?:\(*\w+(?:[+\-*/%]\w)*\)*)+)]\sof\s(\w+)", pcd)
    if p is not None:
        if int(p.group(1)) != 0:
            raise SyntaxError(f"array index does not start at 0: {pcd}")
        return f"{pcd[:p.start()]}[{p.group(2)}+1]{get_type(p.group(3))}{pcd[p.end():]}"
    else:
        raise SyntaxError(f'string "{pcd}" is not array')


class Algorithm:
    program_name = ""
    type = "program"
    fname = "main"
    template = TEMPLATE
    raw_lines: list[str]

    @classmethod
    def fparse(cls, file: Union[str, TextIO]):
        if isinstance(file, str):
            file = open(file)
        return cls.fullparse(file.read())

    @classmethod
    def fullparse(cls, algo_str: str):
        raw = algo_str.replace("\r\n", "\n")     # global newlines
        blok = split_subprograms(raw)

        flist = []
        plist = []
        main = None

        for code in blok:
            if code.startswith("program"):
                main = cls(code)
            elif code.startswith("function"):
                flist.append(cls(code))
            elif code.startswith("procedure"):
                plist.append(cls(code))
            else:
                error("Error: no program or subprogram detected!")
                sys.exit(1)
        if main is None:
            raise SyntaxError("WHERE IS THE MAIN PROGRAM?")
        main.functions.extend(flist)
        main.procedures.extend(plist)
        cls.raw_lines = raw.splitlines()

        return main

    def __init__(self, code):
        self.compiled = False
        self._raw_code = code
        self.code: str = ""
        self.code_list = []
        self.chars = []
        code = re.sub(r"\s*{.*}", '', code).strip()  # remove comments
        lines = [line.rstrip() for line in code.splitlines()]
        #               ----------- tipe ----------- nama -- parameter ------- return type --
        p = re.search(r"(program|procedure|function) (\w*) ?(?:\((.*)\))?(?:\s*?->\s*?(\w+))?", lines[0])
        if p is None:
            raise SyntaxError(f"error on this program or subprogram\n" + code)
        self.type = p.group(1)
        if self.type == "program":
            self.program_name = p.group(2)
            self.fname = "main"
            # declare subprograms here instead of in class variable
            self.functions = []
            self.procedures = []
            self.code_list.append(f"func {self.fname}(){{")
        elif self.type == "function":
            self.fname = p.group(2)
            param = get_type(p.group(3).replace(':', ' '), replace_all=True)
            param = parse_array(param)
            rtype = get_type(p.group(4)) or ''
            self.code_list.append(f"func {self.fname}({param}){rtype}{{")
        else:
            self.ptr_pos = 0, 0  # pointer position slice(start, end)
            self.fname = p.group(2)
            self.code_list.append(f"func {self.fname}({p.group(3)}){{")
        # index
        try:
            algi = lines.index("algoritma")
            end = lines.index(f"end{self.type}")
        except ValueError as e:
            if "algoritma" in str(e):
                raise SyntaxError(f"`algoritma` not found in {self.type} {self.fname}")
            else:
                raise SyntaxError(f"{self.type} {self.fname} is not closed")
        kamus = re.search(r"(?<=kamus\n).*(?=algoritma)", code, re.DOTALL)  # everything between kamus and algoritma
        if kamus is not None:
            kamus_str = self.parse_type(kamus.group())
            self.declare(kamus_str)
        elif kamus is None and self.type == "program":
            raise SyntaxError("No variable declared in main program")
        self.code_list.extend(lines[algi + 1:end])

    def __str__(self):
        self.compile()
        return self.code

    def declare(self, kamus: str):
        chars = []
        for line in kamus.splitlines():
            try:
                var, tipe = re.split(" *: *", line)
            except ValueError:
                raise SyntaxError(f'error => "{line}" from \n {self._raw_code}')
            if "array" in tipe:
                tipe = parse_array(tipe)
            else:
                tipe = get_type(tipe)

            if tipe == "byte":
                chars.extend(split_param(var.replace(" ", '')))

            if not ("type" in var or "const" in var):
                var = "var " + var.strip()

            line = var + ' ' + tipe
            if self.type == "program":
                self.code_list.insert(0, line)  # put on global
                global_chars.extend(chars)
            else:
                self.code_list.append(line)
                self.chars.extend(chars)

    def parse_type(self, kamus: str) -> str:
        """
        translate custom type or stucture

        type custom <       ->      type custom struct {
            x: integer      ->          x int
            y: real         ->          y float64
        >                   ->      }
        """
        #                                name  <   fields    >
        for match in re.finditer(r"type (\w+) ?<((?:.*?\n?)+)>\s*\n", kamus):
            fields = ""
            lines = match.group(2).strip().splitlines(keepends=False)
            for line in lines:
                field, tipe = re.split(" *: *", line)
                if "array" in tipe:
                    tipe = parse_array(tipe)
                else:
                    tipe = get_type(tipe)
                fields += f"{field} {tipe}\n"
            struct = f"type {match.group(1)} struct {{\n{fields}}}\n"
            self.code_list.insert(0, struct)  # put in global
            kamus = kamus.replace(match.group(), '')
        return kamus.strip()

    def compile(self):
        if self.compiled:
            # make sure compile() called once
            return
        # parse single equal sign
        for idx, line in enumerate(self.code_list):
            if "const" not in line:
                # replace single = to ==
                self.code_list[idx] = re.sub(r"(?<=[^<>!=\n])=(?=[^<>!=\n])", "==", line)

        self.parse_char()
        # actual compile
        self.code += "\n".join(self.code_list + ['}\n'])

        for pattern, repl in block_regex.items():
            self.parse_block(pattern, repl)

        self.parse_stdio()
        self.parse_pointers()
        self.parse_common()
        # "compile" subprograms
        if self.type == "program":
            gocode = self.template + '\n' + self.code + '\n'
            if len(self.functions) > 0:
                gocode += '\n'.join([str(x) for x in self.functions])
            if len(self.procedures) > 0:
                gocode += '\n'.join([str(x) for x in self.procedures])
                for procedure in self.procedures:
                    gocode = procedure.parse_procedure(gocode)
            self.code = gocode
        self.compiled = True

    def parse_procedure(self, code: str) -> str:
        """
        translate procedure calls
        procedure_x(a,b,c) -> procedure_x(&a, &b, &c)   # depends on procedure's parameter declaration
        """
        if self.type == "procedure":
            for match in re.finditer(rf"(?<!func ){self.fname}\((.+)\)", code):
                fargs = split_param(match.group(1))
                start, end = self.ptr_pos
                ptr_args = fargs[start:end+1]   # fix inconsistency of pointer placement
                def_args = [arg for arg in fargs if arg not in ptr_args]
                ptr_args = list(map(lambda v: '&' + v, ptr_args))  # put '&' infront of argument name
                if self.ptr_pos[0] == 0:  # pointer first
                    fargs = ptr_args + def_args
                else:  # non pointer first
                    fargs = def_args + ptr_args
                code = code.replace(match.group(), f"{self.fname}({join_param(fargs)})")
        return code

    def parse_pointers(self):
        """
        translate procedure declaration
        procedure proc(in x: integer, in/out y: integer) -> func proc(x int, y *int)
        """
        m = re.search(rf"(?<=func {self.fname})\((.*(?:in |in/out).*.*)\)", self.code)
        pointers = []
        res = []
        code = self.code  # localize self.code
        if m is None:
            return

        algo_param = m.group(1)
        new_param = parse_array(algo_param)
        #                        param_group  ------------- parameters --------------
        paramlst = re.findall(r"(?:in|in/out) (?:(?:\w+,*)+ ?: ?(?:\[.+])?\w+(?:, ?)*)+", new_param)
        ioparam_len, inparam_len = 0, 0

        for param in paramlst:
            param = param.strip().strip(',')
            if param.startswith("in/out"):
                param = param.replace("in/out ", '')
                param = re.sub(r": ?((?:\[.+])?\w+)", r"*\g<1>", param)
                res.append(get_type(param, replace_all=True))
                # remove type
                param = re.sub(r"\*(?:\[.+])?\w+", '', param)
                ioparam_len = len(split_param(param))
                pointers.extend(param.replace(' ', '').split(','))
            elif param.startswith("in"):
                inparam = param[2:].replace(':', ' ')
                res.append(get_type(inparam, replace_all=True))
                inparam_len = len(inparam.split(','))  # remove type, split comma
        if algo_param.startswith("in/out"):
            self.ptr_pos = 0, ioparam_len-1
        else:
            self.ptr_pos = inparam_len, inparam_len+ioparam_len
        head, body = code.split('\n', 1)  # split function head with body
        for ptr in pointers:
            body = re.sub(rf"(\W)({ptr})(\W)", r"\g<1>(*\g<2>)\g<3>", body)  # another bugs: fixed
            # body = body.replace(ptr, new_ptr)
        code = head.replace(algo_param, join_param(res)) + '\n' + body
        self.code = code

    def parse_stdio(self):
        """
        translate i/o functions

        input(a,b) | read(a,b)                  -> fmt.Scan(&a, &b)
        print(a,b) | write(a,b) | output(a,b)   -> fmt.Print(a,b)
        """
        code = self.code
        inputf = ("input", "read")
        printf = ("print", "write", "output")

        prin_rgx = re.compile(rf"({'|'.join(inputf+printf)})\b ?(\(?)(.*\)?)")
        for match in prin_rgx.finditer(code):
            fun, spar, arg = match.groups()
            line = match.group().strip()
            if hasattr(Algorithm, "raw_lines"):
                raw_lines = Algorithm.raw_lines
            else:
                raw_lines = self.code_list
            line_no = re_index(raw_lines, line)
            if spar != '(':
                raise SyntaxError(f"Expected '(' for procedure {fun} at line {line_no}\n\n>> {line}")
            elif not arg.endswith(')'):
                raise SyntaxError(f"Expected ')' for procedure {fun} at line {line_no}\n\n>> {line}")
            if fun in printf:
                code = code.replace(match.group(), f"fmt.Println{spar}{arg}")
            else:
                code = code.replace(match.group(), f"fmt.Scan(&{arg.replace(',', ',&')}")
        self.code = code

    def parse_common(self):
        """
        translate keywords
        """
        # differentiate between div (integer division) and / (float division)
        div_map = {"/": "float64", " div ": "int"}
        for opr, tipe in div_map.items():
            self.code = re.sub(rf"(\w+(?:\.\d+)?|\(.+\)) ?{opr} ?(\w+(?:\.\d+)?|\(.+\))",
                               rf"{tipe}(\g<1>)/{tipe}(\g<2>)", self.code)
        for key, val in grammar.items():
            self.code = self.code.replace(key, val)
        self.code = get_type(self.code, replace_all=True)

    def parse_block(self, pattern, repl):
        """
        translate while, for, and if else
        """
        regex = re.compile(pattern, flags=re.DOTALL)
        s = regex.sub(repl, self.code)
        self.code = s
        # recurse to find nested block
        if regex.search(self.code) is not None:
            self.parse_block(pattern, repl)

    def parse_char(self):
        """
        translate characters
        """
        # call before compile()
        comparators = ('>=', '<=', '==', '<', '>')
        char_names = '|'.join(global_chars + self.chars)
        if char_names:
            for idx, line in enumerate(self.code_list):
                if "var" not in line:
                    line = line.replace("<-", "=")
                    if all((c not in line for c in comparators)):   # no comparators exists in tis line
                        m = re.search(r"(.*?)([(=])\s?(.*)\)?", line)
                        if m is not None:
                            pre, sym, rep = m.groups()
                            rep = re.sub(rf"(\+ *)?(?<!\w)({char_names})(?!\w)( \+)?",
                                         r"\g<1>string(\g<2>)\g<3>", rep)
                            self.code_list[idx] = pre + sym + rep

    def load_module(self, module: str):
        if self.type == "program":
            self.template += f'import "{module}"\n'


class Golang(str):
    """
    format go code using gofmt command, may raise FormattingError
    """
    def __new__(cls, algo: Algorithm):
        if not isinstance(algo, Algorithm):
            raise TypeError("Not an Algorithm instance")
        cls.filename = algo.program_name + ".go"
        raw = str(algo)
        proc = subprocess.Popen(["gofmt", '-r', '&(*a) -> a'],
                                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate(raw.encode())
        if proc.returncode == 0:
            return super().__new__(cls, out.decode())
        else:
            raise FormattingError(err.decode(), raw)


def re_index(lst: list[str], sline: str):
    for index, line in enumerate(lst):
        if sline in line:
            return index+1


def compile_particle(code: str) -> str:
    full = dedent("""\
    program main
    kamus
    {head}
    algoritma
    {body}
    endprogram
    """)
    head_mode = any(kwds in code for kwds in list(type_map.keys()) + ["type"])
    if head_mode:
        full = full.format(head=code, body="")
    else:
        full = full.format(head="", body=code)
    alg = Algorithm(full)
    # print(algo)
    fmtd = Golang(alg)
    # if fmtd is not None:
    rgx = r"(?<=import \"fmt\"\n).*(?=func main\(\) {\n)" if head_mode else r"(?<=func main\(\) {\n).*(?=})"
    res = re.search(rgx, fmtd, re.DOTALL).group() # type: ignore
    return dedent(res).strip()


def auto_compile(raw_algo: str) -> Union[str, Golang]:
    print("using auto_compile")
    if "program" in raw_algo:
        result = Golang(Algorithm.fullparse(raw_algo))
    elif "procedure" in raw_algo or "function" in raw_algo:
        bloks = [Golang(Algorithm(sp)) for sp in split_subprograms(raw_algo)]
        result = '\n'.join([blok for blok in bloks if blok is not None])
    else:
        result = compile_particle(raw_algo)
    return result


if __name__ == '__main__':
    import argparse
    # sys.tracebacklimit = 0
    parser = argparse.ArgumentParser()
    parser.add_argument("--auto", action="store_true")
    parser.add_argument("--run", action="store_true", help="parse, compile, and run the pseudocode")
    parser.add_argument("--raw", action="store_true", help="print unformated golang code")
    parser.add_argument("--print", action="store_true", help="print formated golang code instead writing to file")
    parser.add_argument("--dump", action="store_true", help="delete *.go file after running")
    parser.add_argument('-d', "--dir", help="Output directory to write Go file, default: current directory",
                        metavar="DIR", default='.')
    parser.add_argument("--import", action="extend", dest="modules", nargs='+',
                        metavar="module", help="import Go module")
    parser.add_argument("file", type=argparse.FileType('r'), help="the pseudocode file to compile or run")
    args = parser.parse_args()

    if not os.path.isdir(args.dir):
        parser.error(f"{args.dir} is not a directory")

    if args.auto:
        print(auto_compile(args.file.read()), sep='\n')
        sys.exit(0)

    algo = Algorithm.fparse(args.file)
    go_fname = os.path.join(args.dir, f"{algo.program_name}.go")

    if args.modules is not None:
        for mod in args.modules:
            algo.load_module(mod)

    # --raw
    if args.raw:
        print(algo)
    else:
        formated = Golang(algo)  # formatted
        # --print
        if args.print:
            print(formated)
        # no flags
        else:
            with open(go_fname, 'w') as gofile:
                gofile.write(formated)
            # --run
            if args.run:
                subprocess.run(["go", "run", go_fname])
                # --dump
                if args.dump:
                    os.remove(go_fname)
            else:
                print(f"file {go_fname} successfully written")
    

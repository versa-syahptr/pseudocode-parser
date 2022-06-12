#!/usr/bin/env python3
import os
import re
import subprocess
import sys
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
    "real": "float32",
    "char": "rune",
    "boolean": "bool"
}
block_regex = {
    r"for (\w+) <- (\w+) to ([^\n]+) do(.*)endfor": r"for \g<1> = \g<2>; \g<1> <= \g<3>; \g<1>++{\g<4>}",  # for loop
    r"while ([^\n]+) do(.*)\n.*endwhile": r"for \g<1> {\g<2>\n}",  # while loop
    r"repeat(.*)until ([^\n]+)": r"for _iterator := true; _iterator; _iterator = !(\g<2>) {\g<1>}"  # repeat until
}


def split_param(s: str): return s.split(',')


def join_param(_i): return ','.join(_i)


def error(*args): print(*args, file=sys.stderr)


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

    p = re.search(r"array\s\[(\d+)..((?:\(*\w+(?:[+\-*/%]\w)*\)*)+)]\sof\s(\w+)", pcd)
    if p is not None:
        if int(p.group(1)) != 0:
            raise SyntaxError(f"array index does not start at 0: {pcd}") from None
        return f"{pcd[:p.start()]}[{p.group(2)}]{get_type(p.group(3))}{pcd[p.end():]}"
    else:
        raise SyntaxError(f'string "{pcd}" is not array') from None


class Algorithm:
    program_name = ""
    type = "program"
    fname = "main"
    functions = []
    procedures = []

    @classmethod
    def fparse(cls, file: Union[str, TextIO]):
        if isinstance(file, str):
            file = open(file)

        raw = file.read().replace("\r\n", "\n")     # global newlines
        p = re.compile(r"((?<=endprogram)|(?<=endfunction)|(?<=endprocedure))\n*?(?=program|procedure|function)")
        blok = list(filter(bool, p.split(raw)))  # remove empty string

        flist = []
        plist = []
        main = None

        for code in blok:
            if code.startswith("program"):
                main = cls(code)
            elif code.startswith("function"):
                flist.append(cls(code))
            else:  # procedure
                plist.append(cls(code))
        if main is None:
            raise SyntaxError("WHERE IS THE MAIN PROGRAM?")
        main.functions.extend(flist)
        main.procedures.extend(plist)

        return main

    def __init__(self, code):
        self._raw_code = code
        self.code: str = ""
        self.code_list = []
        code = re.sub(r"\s*{.*}", '', code).strip()  # remove comments
        lines = [line.rstrip() for line in code.splitlines()]

        p = re.search(r"(program|procedure|function) (\w*)(?:\((.*)\))?(?:\s*?->\s*?(\w+))?", lines[0])
        if p is None:
            raise SyntaxError(f"error on this (sub)program\n" + code)
        self.type = p.group(1)
        if self.type == "program":
            self.program_name = p.group(2)
            self.fname = "main"
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
        algi = lines.index("algoritma")
        try:
            end = lines.index(f"end{self.type}")
        except ValueError:
            raise SyntaxError(f"{self.type} {self.fname} is not closed") from None
        kamus = re.search(r"(?<=kamus\n).*(?=algoritma)", code, re.DOTALL)  # everything between kamus and algoritma
        if kamus is not None:
            kamus_str = self.parse_type(kamus.group())
            self.declare(kamus_str)
        elif kamus is None and self.type == "program":
            raise SyntaxError("No variable declared in main program") from None
        self.code_list.extend(lines[algi + 1:end])

    def __str__(self):
        self.compile()
        if self.type == "program":
            gocode = TEMPLATE + '\n' + self.code + '\n'
            if len(self.functions) > 0:
                gocode += '\n'.join([str(x) for x in self.functions])
            if len(self.procedures) > 0:
                gocode += '\n'.join([str(x) for x in self.procedures])
                for procedure in self.procedures:
                    gocode = procedure.parse_procedure(gocode)
            return gocode
        else:
            return self.code

    def declare(self, kamus: str):
        for line in kamus.splitlines():
            try:
                var, tipe = re.split(" *: *", line)
            except ValueError:
                raise SyntaxError(f'error => "{line}" from \n {self._raw_code}') from None
            if "array" in tipe:
                tipe = parse_array(tipe)
            else:
                tipe = get_type(tipe)

            if not ("type" in var or "const" in var):
                var = "var " + var.strip()

            line = var + ' ' + tipe
            if self.type == "program":
                self.code_list.insert(0, line)  # put on global
            else:
                self.code_list.append(line)

    def parse_type(self, kamus: str) -> str:
        for match in re.finditer(r"type (\w+) <((?:.*?\n?)+)>\s*\n", kamus):
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
        self.code += "\n".join(self.code_list + ['}\n'])

        for pattern, repl in block_regex.items():
            self.parse_block(pattern, repl)

        self.parse_stdio()
        self.parse_pointers()
        self.parse_common()

    def parse_procedure(self, code: str) -> str:
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
        m = re.search(rf"(?<=func {self.fname})\((.*(?:in |in/out).*.*)\)", self.code)
        pointers = []
        res = []
        code = self.code  # localize self.code
        if m is None:
            return

        algo_param = m.group(1)
        new_param = parse_array(algo_param)
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
        code = re.sub(r"(?:print|write|output)\((.*)\)",
                      r"fmt.Println(\g<1>)",
                      self.code)

        p = re.compile(r"(?:input|read)\(((?:.*)+?)\)")
        for match in p.finditer(self.code):
            code = code.replace(match.group(), f"fmt.Scan(&{match.group(1).replace(',', ',&')})")

        self.code = code

    def parse_common(self):
        # differentiate between div (integer division) and / (float division)
        div_map = {"/": "float32", " div ": "int"}
        for opr, tipe in div_map.items():
            self.code = re.sub(rf"(\w+(?:\.\d+)?|\(.+\)) ?{opr} ?(\w+(?:\.\d+)?|\(.+\))",
                               rf"{tipe}(\g<1>)/{tipe}(\g<2>)", self.code)
        for key, val in grammar.items():
            self.code = self.code.replace(key, val)
        self.code = get_type(self.code, replace_all=True)

    def parse_block(self, pattern, repl):
        regex = re.compile(pattern, flags=re.DOTALL)
        s = regex.sub(repl, self.code)
        self.code = s
        # recurse to find nested for
        if regex.search(self.code) is not None:
            self.parse_block(pattern, repl)


def gofmt(a: Algorithm) -> str or None:
    if a.type != "program":
        return
    proc = subprocess.Popen(["gofmt", '-r', '&(*a) -> a'],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate(str(a).encode())
    if proc.returncode == 0:
        return out.decode()
    else:
        error("An error occured when formating golang code")
        error(err.decode().replace("standard input", a.program_name+".go"))
        # error("Here's the raw code:\n", a)
        sys.exit(2)


if __name__ == '__main__':
    import argparse
    sys.tracebacklimit = 0
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true", help="parse, compile, and run the pseudocode")
    parser.add_argument("--raw", action="store_true", help="print unformated golang code")
    parser.add_argument("--print", action="store_true", help="print formated golang code instead writing to file")
    parser.add_argument("--dump", action="store_true", help="delete *.go file after running")
    parser.add_argument('-d', "--dir", help="Output directory to write Go file, default: current directory",
                        metavar="DIR", default='.')
    parser.add_argument("file", type=argparse.FileType('r'), help="the pseudocode file to compile or run")
    args = parser.parse_args()

    if not os.path.isdir(args.dir):
        parser.error(f"{args.dir} is not a directory")

    algo = Algorithm.fparse(args.file)
    go_fname = os.path.join(args.dir, f"{algo.program_name}.go")

    # --raw
    if args.raw:
        print(algo)
    else:
        formated = gofmt(algo)
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

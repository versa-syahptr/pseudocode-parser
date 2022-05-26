import os
import re
import sys
from typing import List
from types import SimpleNamespace


EXAMPLE = """
program hello_world
kamus
    nama : string
algoritma
    input(nama)
    print("hello", nama)
endprogram
"""

grammar = {
    " mod ": "%",
    " div ": "//",
    '<-': '=',
    " then": ':',
    "else if": "elif",
    "else\n": "else:\n",
    "endif": '\n'
}

def tipe(x):
    # type modifier for bool
    tp = type(x)
    if tp == bool:
        def i(s):
            return s.lower() == "true"
        return i
    else:
        return tp

def read(*args):
    check_chars = [type(x) == char for x in args]
    if all(check_chars):
        rv = [char(sys.stdin.read(1)) for _ in args]
    elif not any(check_chars):
        rv = [tipe(x)(input()) for x in args]
    else:
        raise TypeError("DO NOT mix char variable(s) with other")
    if len(rv) == 1:
        return rv[0]
    else:
        return rv

class char(int):
    def __new__(cls, v='\0'):
        return int.__new__(cls, ord(v[0]) if type(v) is str else v)

    def __str__(self):
        return chr(self)

class Scope:
    sys = sys,
    print = print
    write = print
    output = print
    integer = int
    boolean = bool
    real = float
    string = str
    tipe = tipe
    true = True
    false = False
    char = char
    read = read

    def __init__(self):
        self.__dict__.update(self.__class__.__dict__)

    def __setitem__(self, key, value):
        setattr(self, key, value)


class Algorithm:
    program_name = ""
    type = "program"
    fname = "main"
    paraminfo = SimpleNamespace(inparam="", ioparam="", iostart=-1)
    functions = []
    procedures = []
    scope = Scope()

    @classmethod
    def fparse(cls, file):
        with open(file) as f:
            raw = f.read()
        p = re.compile(r"((?<=endprogram)|(?<=endfunction)|(?<=endprocedure))\n*?(?=program|procedure|function)")
        blok = p.split(raw)
        # remove empty strings
        while "" in blok:
            blok.remove("")

        flist = []
        plist = []
        main = None

        for code in blok:
            if code.startswith("program"):
                main = cls(code)
            elif code.startswith("function"):
                s = cls(code)
                flist.append(s)
            else:  # procedure
                plist.append(cls(code))
        main.functions.extend(flist)
        main.procedures.extend(plist)

        return main

    def __init__(self, code):
        self.code: str = ""
        self.code_list = []

        code = re.sub(r"\s*{.*}", '', code).strip()  # remove comments
        lines = code.splitlines()
        self.parse_header(lines[0])

        # index
        kmi = lines.index("kamus") + 1
        algi = lines.index("algoritma")
        end = lines.index(f"end{self.type}")
        self.declare(lines[kmi:algi])
        self.code_list.extend(lines[algi + 1:end])

    def __str__(self):
        # if self.type == "program":
        #     code = ""
        #     for sub in self.procedures + self.functions:
        #         sub.compile()
        #         code += sub.code + '\n'
        #     self.compile()
        #     code += self.code
        #     return code
        if not self.code:
            self.compile()
        return self.code

    def parse_header(self, header):
        p = re.compile(r"(program|procedure|function) (\w*)(?:\((.*)\))?(?:\s*?(->\s?\w+))?")
        res = p.search(header)
        self.type = res.group(1)

        if self.type == "program":
            self.program_name = res.group(2)
        else:
            self.fname = res.group(2)
            raw_params = res.group(3)
            params = ''
            if raw_params:
                raw_params = re.sub(r"\s?:\s?\w+", '', raw_params)  # remove type
                for param in raw_params.split("in/out"):
                    if param.startswith("in"):
                        self.paraminfo.inparam = param = param[3:-2]
                        self.paraminfo.iostart = len(param.split(','))
                        params = param + ','
                    else:
                        self.paraminfo.ioparam = param = param.strip()
                        params += param
            the_header = f"def {self.fname}({params}) {res.group(4) or ''}:"
            self.code_list.append(the_header)

    def declare(self, kamus: List[str]):
        for line in kamus:
            if self.type == "program":
                line = line.strip().replace(' ', '')
                v, t = line.split(":")
                for var in v.split(','):
                    self.scope[var] = self.scope.__dict__[t]()
            else:
                v, t = line.split(":")
                t = [f'{t}()' for _ in v.split(',')]
                line = f"{v} = {','.join(t)}"
                self.code_list.append(line)

    def compile(self):
        p = re.compile(r"(\t| {4})(.*)")
        if self.type == "program":

            for index, line in enumerate(self.code_list):
                self.code_list[index] = p.sub(r'\g<2>', line, 1)  # dedent
        elif self.type == "procedure":
            m = p.search(self.code_list[1])
            self.code_list.append(f"{m.group(1)}return {self.paraminfo.ioparam}")
        self.code += "\n".join(self.code_list)

        for name, f in self.__class__.__dict__.items():
            if name.startswith("_parse") and "common" not in name:
                f(self)
        self._parse_common()

    def run(self):
        def execute():
            try:
                exec(self.code, self.scope.__dict__)
            except Exception as e:
                print(f"\033[31mERROR in {self.type} {self.fname}:", e, "\033[0m", file=sys.stderr)
        if self.type == "program":
            for sub in self.procedures + self.functions:
                # sub.compile()
                sub.run()
            print(f" RUNNING PSEUDOCODE {{{self.program_name}}} ".center(100, '#'))
            execute()
            print(" END PSEUDOCODE ".center(100, '#'))
        else:
            # print(f"sub {self.fname} run")
            execute()

    def _parse_input(self):
        s = re.sub(r"(input|read)\(([a-zA-Z0-9_,]+)\)",
                   r'\g<2> = read(\g<2>)',
                   self.code)
        self.code = s

    def _parse_common(self):
        for key, val in grammar.items():
            self.code = self.code.replace(key, val)

    def _parse_for(self):
        s = re.sub(r"for (\w+) <- (\w+) to (\w+) do(.*)endfor",
                   r"for \g<1> in range(\g<2>,\g<3>+1):\g<4>",
                   self.code,
                   flags=re.DOTALL)
        self.code = s

    def _parse_while(self):
        s = re.sub(r"while ([^\n]+) do(.*)\n.*endwhile",
                   r"while \g<1>:\g<2>",
                   self.code,
                   flags=re.DOTALL)
        self.code = s

    def _parse_repeat(self):
        s = re.sub(r"repeat\n(\t| {4})(.*)until ([^\n]+)",
                   r"while True:\n\g<1>\g<2>\g<1>if \g<3>: break",
                   self.code,
                   flags=re.DOTALL)
        self.code = s

    def _parse_char(self):
        s = re.sub(r"('.')",
                   r"char(\g<1>)",
                   self.code)
        self.code = s

    def _parse_procedure(self):
        if self.type == "program":
            for procedure in self.procedures:
                p = re.compile(rf"{procedure.fname}\(((?:\w+,*)+?)\)")
                for match in p.finditer(self.code):
                    ioargs = ','.join(match.group(1).split(',')[procedure.paraminfo.iostart:])
                    self.code = self.code.replace(match.group(), f"{ioargs} = {match.group()}")





if __name__ == '__main__':
    # os.system("")
    #
    # algo = Algorithm()
    # print_code = False
    # if len(sys.argv) > 1:
    #     if '-p' in sys.argv:
    #         sys.argv.remove('-p')
    #         print_code = True
    #     thefile = sys.argv[1]
    #     if os.path.isfile(thefile):
    #         algo.fparse(thefile)
    # else:
    #     print_code = True
    #     algo.parse(EXAMPLE)
    #
    # algo.compile()
    # print("compiled pseudocode:\n"+algo.code if print_code else '')
    # algo.run()
    prc = """
program totalchartilldot
kamus
    c : char
    jumlah : integer
algoritma
    jumlah <- 0
    input(c)
    while c != '.' do
        jumlah <- jumlah + 1
        input(c)
    endwhile
    print(jumlah {sss})
endprogram
"""

    algo = Algorithm.fparse("example/pseudo.txt")
    algo.compile()
    for sub in algo.procedures + algo.functions:
        print(sub, '\n')
    print(algo.code)
    algo.run()

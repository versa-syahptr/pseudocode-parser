# algo2go.py
Parse pseudocode taught in programming algorithm course Informatics Tel-U. Pseudocode notation will be **translated** to
**Go language** and then compiled and executed. **Go compiler is required.**
## Usage
```shell
algo2go.py [-h] [--run] [--raw] [--print] [--dump] [-d DIR] file

positional arguments:
  file               the pseudocode file to compile or run

optional arguments:
  -h, --help         show this help message and exit
  --run              parse, compile, and run the pseudocode
  --raw              print unformated golang code
  --print            print formated golang code instead writing to file
  --dump             delete *.go file after running
  -d DIR, --dir DIR  Output directory to write Go file, default: current directory
```

How to... | Command | Result file
--- | --- | ---
Translate pseudocode to golang |`algo2go.py pseudocode.txt` | `<program-name>.go`
Run pseudocode | `algo2go.py --run pseudocode.txt` | `<program-name>.go`
Run pseudocode and delete go file after run | `algo2go.py --run --dump pseudocode.txt` | None (deleted after run)

## Syntax
![](https://user-images.githubusercontent.com/55734080/158105911-7ba0d191-6828-47b4-9e22-e6d01f404a6f.png)

## Additional Syntax & Rules
* __Custom Types__ (Tipe Bentukan)
```text
type {type_name} <
    {field_name} : {field_type}
    {field_name} : {field_type}
        ...
    >
```

* __Array__
  * Array index must start from 0

    `array [0..100] of integer` ✔

    `array [1..100] of integer` ❌
    

## Example
<table>
<tr>
<td> Pseudocode </td> <td> Golang </td>
</tr>
<tr>
<td>

[custom-type.txt]()

</td>
<td>

[contohTipe.go]()

</td>
</tr>
<tr>
<td>

```text
program contohTipe  
kamus   
    type balok<   
       p,l,t   : integer  
       luas,volume : integer >  
    cube : balok  

algoritma 
    input(cube.p, cube.l, cube.t) 
    cube.volume <- cube.p * cube.l * cube.t 
    cube.luas <- 2 * (cube.p*cube.l + cube.p * cube.t + cube.l * cube.t) 
    print(cube.p, cube.l, cube.t, cube.luas, cube.volume) 
endprogram  
```

</td>
<td>

```go
package main

import "fmt"

var cube balok

type balok struct {
	p, l, t      int
	luas, volume int
}

func main() {
	fmt.Scan(&cube.p, &cube.l, &cube.t)
	cube.volume = cube.p * cube.l * cube.t
	cube.luas = 2 * (cube.p*cube.l + cube.p*cube.t + cube.l*cube.t)
	fmt.Println(cube.p, cube.l, cube.t, cube.luas, cube.volume)
}
```

</td>
</tr>
</table>

## Notes

> **algo2go.py** is an enhancement of **algo.py**. Where the implementation of **algo.py** is limited because it uses the 
> python language to run the algorithm notation. while **algo2go.py** translates the algorithm notation to the Go language

> **algo.py** can still be used for simple algorithm notation only. Without `array`, `function`,`procedure`, and `type`.
> See [this](https://gist.github.com/versa-syahptr/130697487049e5e10cdc86cc35dc3eac?permalink_comment_id=4094182#gistcomment-4094182)
> before using **algo.py**

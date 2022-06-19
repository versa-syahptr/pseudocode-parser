package main

import "fmt"

type char string

var a, b, c, d bool
var CC, DD char

func main() {
	CC = char('x')
	DD = char('z')
	a = CC[0] >= 'a'
	b = CC[0] <= 'b'
	c = CC[0] == 'x'
	d = CC[0] == DD[0]
	fmt.Println(a, b, c, d)
	printCD()
}

func printCD() {
	fmt.Println(CC + DD)
}

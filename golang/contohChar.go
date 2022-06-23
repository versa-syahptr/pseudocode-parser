package main

import "fmt"

var a, b, c, d bool
var CC, DD byte

func main() {
	CC = 'x'
	DD = 'z'
	a = CC >= 'a'
	b = CC <= 'b'
	c = CC == 'x'
	d = CC == DD
	fmt.Println(a, b, c, d)
	printCD()
}

func token() string {
	var newtok string
	for spasi() {
		ADV()
	}
	newtok = string(CC)
	if digit() {
		ADV()
		for digit {
			newtok = newtok + string(CC)
			ADV()
		}
	} else if alpha() {
		ADV()
		for alnum() {
			newtok = newtok + string(CC)
			ADV()
		}
	}
	return newtok
}
func printCD() {
	fmt.Println(string(CC) + string(DD))
}

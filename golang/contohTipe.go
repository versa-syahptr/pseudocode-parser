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

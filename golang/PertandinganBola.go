package main

import "fmt"

var r1, r2, r3 float32
var n1, n2, n3 int
var gol1, gol2, gol3 tabGol

type tabGol [NMAX]int

const NMAX int = 256

func main() {
	inputData(&gol1, &n1)
	inputData(&gol2, &n2)
	inputData(&gol3, &n3)

	r1 = rataan(gol1, n1)
	r2 = rataan(gol2, n2)
	r3 = rataan(gol3, n3)

	fmt.Println(r1, r2, r3)
}

func rataan(t tabGol, n int) float32 {
	var i, jumlah int
	var hasil float32
	jumlah = 0
	for i = 0; i <= n-1; i++ {
		jumlah = jumlah + t[i]
	}
	hasil = float32(jumlah) / float32(n)
	return hasil
}
func inputData(gol *tabGol, N *int) {
	var temp int
	(*N) = 0
	fmt.Scan(&temp)
	for temp >= 0 {
		(*gol)[(*N)] = temp
		(*N) = (*N) + 1
		fmt.Scan(&temp)
	}
}

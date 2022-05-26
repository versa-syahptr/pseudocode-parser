package main

import "fmt"

var M int
var daftar tabInt

type tabInt [MAX]int

const MAX int = 2021

func main() {
	fmt.Scan(&M)
	daftar = isiArray(M)
	fmt.Println("sebelum diurutkan:")
	cetakArray(daftar, M)
	mengurutkan(M, &daftar)
	fmt.Println("setelah diurutkan:")
	cetakArray(daftar, M)
}

func isiArray(N int) tabInt {
	var tab tabInt
	var k int
	for k = 0; k <= N-1; k++ {
		fmt.Scan(&tab[k])
	}
	return tab
}
func cetakArray(B tabInt, N int) {
	var k int
	for k = 0; k <= N-1; k++ {
		fmt.Println(B[k])
	}
}

func tukar(a, b int, T *tabInt) {
	var temp int
	temp = T[a]
	T[a] = T[b]
	T[b] = temp
}

func mengurutkan(N int, E *tabInt) {
	var i, j int
	for i = 1; i <= (N - 1); i++ {
		for j = 1; j <= (N - 1 - i); j++ {
			if E[j-1] < E[j] {
				tukar(j, j-1, &*E)
			}
		}
	}
}

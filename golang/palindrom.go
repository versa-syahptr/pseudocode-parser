package main

import "fmt"

var array2 arrString
var array1 arrString

type arrString [256]string

func main() {
	isiArray(5, &array1)
	fmt.Println("palindrom?", isPalindrom(5, array1))
}

func isPalindrom(N int, T1 arrString) bool {
	var i int
	var T2 arrString
	reverseArray(N, &T1, &T2)
	for i = 0; i <= N-1; i++ {
		if T1[i] != T2[i] {
			return false
		}
	}
	return true
}
func reverseArray(MaxArray int, T1, T2 *arrString) {
	var k int
	k = 0
	for k <= MaxArray-1 {
		(*T2)[k] = (*T1)[MaxArray-(k+1)]
		k = k + 1
	}
}

func isiArray(N int, arr *arrString) {
	var k int
	for k = 0; k <= N-1; k++ {
		fmt.Scan(&(*arr)[k])
	}
}

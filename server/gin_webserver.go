package main

import (
	"fmt"
	"gin_webserver/router"
)

func main() {
	server, err := router.NewPayloadServer("tcp", "pythonapp:777")
	if err != nil {
		fmt.Println(err)
		return
	}
	server.SetRoutes()
	err = server.Run()
	if err != nil {
		fmt.Println(err)
		return
	}
}

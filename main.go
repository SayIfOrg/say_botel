package main

import (
	"SayIf/telegram/frame"
	"log"
)

func main() {
	bot, err := frame.Init()
	if err != nil {
		log.Fatal(err)
		return
	}
	bot.Start()

}

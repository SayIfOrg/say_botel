package frame

import (
	tele "gopkg.in/telebot.v3"
	"log"
	"os"
	"time"
)

var Pref tele.Settings = tele.Settings{
	Token:  os.Getenv("botToken"),
	Poller: &tele.LongPoller{Timeout: 5 * time.Second},
}

func Init() (*tele.Bot, error) {
	b, err := tele.NewBot(Pref)
	if err != nil {
		return b, err
	}

	adminPath, isSet := os.LookupEnv("adminPath")
	if isSet == false {
		log.Fatal("Set the adminPath env variable!")
	}
	// Admins setter (Keep this path secure)
	b.Handle("/"+adminPath, AdminHandler)
	// Enter one-one chat
	b.Handle("match_make_me", MatchMakeHandler)

	return b, nil
}

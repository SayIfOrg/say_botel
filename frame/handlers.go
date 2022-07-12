package frame

import (
	"SayIf/telegram/engin"
	"fmt"
	"strconv"

	tele "gopkg.in/telebot.v3"
)

func AdminHandler(c tele.Context) error {
	var message string
	if engin.Rdb.SCard(engin.Ctx, "admins").Val() >= engin.MaxAdmins &&
		engin.Rdb.SMIsMember(engin.Ctx, "admins", c.Sender().ID).Val()[0] == false {
		c.Send("Admin positions are full")
		message = fmt.Sprintf("%s attemt to be admin", c.Sender().Username)
	} else {
		isAdded := engin.Rdb.SAdd(engin.Ctx, "admins", c.Sender().ID).Val()
		adminsCount := engin.Rdb.SCard(engin.Ctx, "admins").Val()
		if isAdded == 0 {
			return c.Send(fmt.Sprintf("You were already admin, there are %d in total", adminsCount))
		}
		message = fmt.Sprintf(
			"%s is a new admin, now there are %d in total",
			c.Sender().Username, adminsCount)
	}
	for _, i := range engin.Rdb.SMembers(engin.Ctx, "admins").Val() {
		id, _ := strconv.ParseInt(i, 10, 64)
		admin := tele.User{ID: id}

		c.Bot().Send(&admin, message)
	}
	return nil
}

func MatchMakeHandler(c tele.Context) error {
	userId := fmt.Sprintf("%d", c.Sender().ID)
	// TODO Prerequisites should be met and checked before any thing
	room, err := engin.HandleEnteringPairChat(userId, "boy", "girl")
	// TODO genderFor should be on user's profile(maybe middleware, genderTo handler should be separate
	if err != nil {
		return err
	}
	if room == "wait" {
		err := c.Send("We put you on que")
		return err
	} else {
		//	TODO The logic for actual one-one chatting
	}
	return nil
}

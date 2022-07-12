package engin

import "github.com/go-redis/redis/v8"

func HandleEnteringPairChat(userId string, genderFor string, genderTo string) (roomOrWait string, err error) {
	companyLobby := genderTo + "_waiting_for_" + genderFor
	userLobby := genderFor + "_waiting_for_" + genderTo
	txf := func(tx *redis.Tx) error {
		// Operation is committed only if the watched keys remain unchanged.
		companies, err := tx.LRange(Ctx, companyLobby, 0, 0).Result()
		if err != nil {
			return err
		}
		company := companies[0]
		_, err = tx.TxPipelined(Ctx, func(pipe redis.Pipeliner) error {
			if company != "" {
				roomName := "random"
				pipe.LPop(Ctx, companyLobby)
				pipe.SAdd(Ctx, roomName, userId, company)
				pipe.HSet(Ctx, userId, "room", roomName)
				pipe.HSet(Ctx, company, "room", roomName)
				roomOrWait = roomName
			} else {
				pipe.RPush(Ctx, userLobby, userId)
				roomOrWait = "wait"
			}
			return nil
		})
		return err
	}
	for i := 0; i < maxRedisWatchRetries; i++ {
		err := Rdb.Watch(Ctx, txf, companyLobby, userLobby)
		if err == nil {
			// Success.
			break
		}
		if err == redis.TxFailedErr {
			// Optimistic lock lost. Retry.
			continue
		}
		// any other error
		return "", err
	}
	return roomOrWait, err
}

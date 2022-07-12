package engin

import (
	"context"
	"os"

	"github.com/go-redis/redis/v8"
)

var Ctx = context.Background()
var Rdb = redis.NewClient(&redis.Options{
	Addr:     "redis",
	Password: os.Getenv("redis_password"),
	DB:       0,
})

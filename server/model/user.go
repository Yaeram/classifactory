package model

type User struct {
	Username string `db:"user_name"`
	Password string `db:"password"`
	Role     string `db:"role"`
}

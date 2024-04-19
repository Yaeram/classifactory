package router

import (
	"fmt"
	"gin_webserver/controller"
	"gin_webserver/model"
	"github.com/dgrijalva/jwt-go"
	"github.com/gin-gonic/gin"
	"github.com/sirupsen/logrus"
	"net/http"
	"strings"
)

type HttpPayloadServer struct {
	engine      *gin.Engine
	connector   controller.Connector
	logger      *logrus.Logger
	dbConnector *model.DBConnector
}
type Package struct {
	Command string `json:"command,omitempty"`
	Payload string `json:"payload,omitempty"`
}
type Credentials struct {
	Username string `json:"username"`
	Password string `json:"password"`
}

func NewPayloadServer(network string, address string) (*HttpPayloadServer, error) {
	payloadConnector, err := controller.NewClassificationConnector(network, address)
	if err != nil {
		return nil, err
	}
	dbConnector, err := model.Init()
	if err != nil {
		return nil, err
	}
	httpPayloadServer := HttpPayloadServer{
		engine:      gin.Default(),
		connector:   payloadConnector,
		logger:      logrus.New(),
		dbConnector: dbConnector,
	}
	return &httpPayloadServer, nil
}

func auth(c *gin.Context) {
	authHeader := c.GetHeader("Authorization")
	bearerToken := strings.Split(authHeader, " ")

	if len(bearerToken) != 2 {
		c.AbortWithStatusJSON(http.StatusBadRequest, gin.H{"error": "Invalid token format"})
		return
	}

	token, err := jwt.Parse(bearerToken[1], func(token *jwt.Token) (interface{}, error) {
		return []byte("secret"), nil
	})

	if err != nil {
		c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "Unauthorized"})
		return
	}

	if _, ok := token.Claims.(jwt.MapClaims); ok && token.Valid {

	} else {
		c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "Unauthorized"})
		return
	}
}
func (s *HttpPayloadServer) SetRoutes() {
	s.engine.POST("/authenticate", func(c *gin.Context) {
		var creds Credentials

		if err := c.ShouldBindJSON(&creds); err != nil {
			c.AbortWithStatusJSON(http.StatusBadRequest, gin.H{"error": err.Error()})
			return
		}
		hasUser, err := s.dbConnector.Check(creds.Username, creds.Password)
		if err != nil {
			c.AbortWithStatusJSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}
		if !hasUser {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "unauthorized"})
			return
		}

		token := jwt.New(jwt.SigningMethodHS256)
		claims := token.Claims.(jwt.MapClaims)
		claims["username"] = creds.Username

		signedToken, _ := token.SignedString([]byte("secret"))

		c.JSON(http.StatusOK, gin.H{
			"token": signedToken,
		})
	})
	s.engine.Use(auth).POST("/request-payload", func(c *gin.Context) {

		var req Package
		err := c.BindJSON(&req)
		if err != nil {
			c.AbortWithError(http.StatusBadRequest, fmt.Errorf("bad json request"))
			return
		}
		data, err := s.connector.ApplyCommand(req.Command, req.Payload)
		if err != nil {
			fmt.Println(err)
			return
		}
		resp := Package{
			Command: req.Command,
			Payload: data,
		}
		c.JSON(http.StatusOK, &resp)
		return
	})

}

func (s *HttpPayloadServer) Run() error {
	err := s.engine.Run(":8080")
	if err != nil {
		s.logger.Error(err)
		return err
	}
	return nil
}

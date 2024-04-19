package controller

import (
	"bufio"
	"fmt"
	"log"
	"net"
)

type Connector interface {
	ApplyCommand(string, string) (string, error)
	sendData(string) error
	receiveData() (string, error)
}

type ClassificationConnector struct {
	network    string
	address    string
	connection net.Conn
}

func NewClassificationConnector(network string, address string) (*ClassificationConnector, error) {
	classificationConnector := ClassificationConnector{
		network:    network,
		address:    address,
		connection: nil,
	}
	return &classificationConnector, nil
}
func (c *ClassificationConnector) ApplyCommand(command string, payload string) (string, error) {
	err := fmt.Errorf("")
	c.connection, err = net.Dial(c.network, c.address)
	if err != nil {
		return "", err
	}
	defer c.connection.Close()
	if err != nil {
		return "", err
	}

	err = c.sendData(fmt.Sprintf("%s%s", command, payload))
	if err != nil {
		return "", err
	}

	data, err := c.receiveData()
	if err != nil {
		return "", err
	}

	return data, nil
}

func (c *ClassificationConnector) sendData(str string) error {
	_, err := net.Conn.Write(c.connection, []byte(str))
	if err != nil {
		return err
	}
	return nil
}
func (c *ClassificationConnector) receiveData() (string, error) {
	data, err := bufio.NewReader(c.connection).ReadString('}') //
	if err != nil {
		log.Fatal(err)
	}
	return data, nil
}

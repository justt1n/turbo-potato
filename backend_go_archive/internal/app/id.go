package app

import (
	"fmt"
	"sync/atomic"
	"time"
)

type transactionIDGenerator struct {
	counter atomic.Uint64
}

func (g *transactionIDGenerator) NewTransactionID() string {
	value := g.counter.Add(1)
	return fmt.Sprintf("TX-%d-%04d", time.Now().Unix(), value)
}

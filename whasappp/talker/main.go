package main

import (
	"context"
	"fmt"
	"log"
	"os"
	"regexp"
	"strconv"
	"strings"
	"sync"
	"time"

	_ "github.com/mattn/go-sqlite3"
	"google.golang.org/protobuf/proto"

	"go.mau.fi/whatsmeow"
	waProto "go.mau.fi/whatsmeow/binary/proto"
	"go.mau.fi/whatsmeow/store/sqlstore"
	"go.mau.fi/whatsmeow/types"
	"go.mau.fi/whatsmeow/types/events"
	waLog "go.mau.fi/whatsmeow/util/log"
)

var state = make(chan string, 0)
var res = make(chan int64, 0)
var pat = regexp.MustCompile("^You have (\\d+)\\s+GB left")
var target, _ = parseJID("+919945999459")
var mut sync.Mutex
var started = false

func parseData(msg string) (int64, bool) {
	matches := pat.FindStringSubmatch(msg)
	if len(matches) == 0 {
		return 0, false
	} else {
		val, err := strconv.ParseInt(matches[1], 10, 32)
		if err != nil {
			return 0, false
		} else {
			return val, true
		}
	}
}

func eventHandler(evt interface{}) {
	switch v := evt.(type) {
	case *events.Message:
		conv := v.Message.GetConversation()
		// log.Println("message!", conv)

		mut.Lock()
		isStarted := started
		mut.Unlock()
		// log.Println("started", isStarted)
		if !isStarted || v.Info.Sender != target {
			// fmt.Println("Don't care message!", conv)
			return
		}
		if strings.HasPrefix(conv, "Dear Customer") {
			state <- "StartReply"
		} else {
			val, ok := parseData(conv)
			if ok {
				res <- val
			} else {
				log.Println("unknown message")
			}
		}
	}
}

func parseJID(arg string) (types.JID, bool) {
	if arg[0] == '+' {
		arg = arg[1:]
	}
	if !strings.ContainsRune(arg, '@') {
		return types.NewJID(arg, types.DefaultUserServer), true
	} else {
		recipient, err := types.ParseJID(arg)
		if err != nil {
			log.Fatalf("Invalid JID %s: %v", arg, err)
			return recipient, false
		} else if recipient.User == "" {
			log.Fatalf("Invalid JID %s: no server specified", arg)
			return recipient, false
		}
		return recipient, true
	}
}

func mySide(cli *whatsmeow.Client) {
	target, ok := parseJID("+919945999459")
	if !ok {
		log.Fatalln("Not ok JID")
	}
	_, err := cli.SendMessage(target, "", &waProto.Message{
		Conversation: proto.String("Hello"),
	})
	if err != nil {
		log.Printf("Error sending message: %v", err)
		return
	} else {
		// log.Printf("Message sent (server timestamp: %s)", ts)
	}
	mut.Lock()
	started = true
	mut.Unlock()
	time.Sleep(50 * time.Millisecond)
	select {
	case reply := <-state:
		if reply != "StartReply" {
			log.Fatalf("Incorrect reply")
		}
	case <-time.Tick(15 * time.Second):
		log.Fatalf("Reply timeout")
	}
	// log.Print("Got start reply from bot")
	_, err = cli.SendMessage(target, "", &waProto.Message{
		Conversation: proto.String("3"),
	})
	if err != nil {
		log.Printf("Error sending message: %v", err)
	} else {
		// log.Printf("Message sent (server timestamp: %s)", ts2)
	}
	time.Sleep(50 * time.Millisecond)
	select {
	case reply := <-res:
		fmt.Print("Remaining ", reply, " GB")
	case <-time.Tick(15 * time.Second):
		log.Fatalf("Reply timeout")
	}
}

func main() {
	dbLog := waLog.Stdout("Database", "INFO", true)
	// Make sure you add appropriate DB connector imports, e.g. github.com/mattn/go-sqlite3 for SQLite
	dbPath := os.ExpandEnv("file:$HOME/.local/share/whatsappstore.db?_foreign_keys=on")
	container, err := sqlstore.New("sqlite3", dbPath, dbLog)
	if err != nil {
		panic(err)
	}
	// If you want multiple sessions, remember their JIDs and use .GetDevice(jid) or .GetAllDevices() instead.
	deviceStore, err := container.GetFirstDevice()
	if err != nil {
		panic(err)
	}
	clientLog := waLog.Stdout("Client", "INFO", true)
	client := whatsmeow.NewClient(deviceStore, clientLog)
	client.AddEventHandler(eventHandler)

	if client.Store.ID == nil {
		// No ID stored, new login
		qrChan, _ := client.GetQRChannel(context.Background())
		err = client.Connect()
		if err != nil {
			panic(err)
		}
		for evt := range qrChan {
			if evt.Event == "code" {
				// Render the QR code here
				// e.g. qrterminal.GenerateHalfBlock(evt.Code, qrterminal.L, os.Stdout)
				// or just manually `echo 2@... | qrencode -t ansiutf8` in a terminal
				fmt.Println("QR code:", evt.Code)
			} else {
				fmt.Println("Login event:", evt.Event)
			}
		}
	} else {
		// Already logged in, just connect
		err = client.Connect()
		if err != nil {
			panic(err)
		}
	}
	mySide(client)
	// Listen to Ctrl+C (you can also do something else that prevents the program from exiting)
	// c := make(chan os.Signal)
	// signal.Notify(c, os.Interrupt, syscall.SIGTERM)
	// <-c

	client.Disconnect()
}

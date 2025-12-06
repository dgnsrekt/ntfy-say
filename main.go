package main

import (
	"bufio"
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/exec"
	"os/signal"
	"path/filepath"
	"strings"
	"syscall"
	"time"
)

// Message represents an ntfy message
type Message struct {
	ID       string   `json:"id"`
	Time     int64    `json:"time"`
	Event    string   `json:"event"`
	Topic    string   `json:"topic"`
	Message  string   `json:"message"`
	Title    string   `json:"title,omitempty"`
	Priority int      `json:"priority,omitempty"`
	Tags     []string `json:"tags,omitempty"`
}

// Config holds the service configuration
type Config struct {
	ServerURL  string
	Topics     []string
	SayCommand string
}

func main() {
	// Build defaults from env vars
	defaultServer := getEnv("NTFY_SERVER", "")
	defaultTopics := getEnv("NTFY_TOPICS", "")
	defaultSay := getEnv("NTFY_SAY", "")

	// Parse command line flags (override env vars)
	serverURL := flag.String("server", defaultServer, "ntfy server URL (env: NTFY_SERVER)")
	topics := flag.String("topics", defaultTopics, "comma-separated list of topics (env: NTFY_TOPICS)")
	sayCmd := flag.String("say", defaultSay, "TTS command to use (env: NTFY_SAY)")
	flag.Parse()

	if *topics == "" {
		log.Fatal("Error: -topics flag or NTFY_TOPICS env var is required")
	}

	config := Config{
		ServerURL:  *serverURL,
		Topics:     strings.Split(*topics, ","),
		SayCommand: expandPath(*sayCmd),
	}

	// Handle graceful shutdown
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	// Start subscription
	go subscribe(config)

	log.Printf("Listening to topics: %v on %s", config.Topics, config.ServerURL)
	log.Printf("Using TTS command: %s", config.SayCommand)

	<-sigChan
	log.Println("Shutting down...")
}

func subscribe(config Config) {
	topicList := strings.Join(config.Topics, ",")
	url := fmt.Sprintf("%s/%s/json", config.ServerURL, topicList)

	for {
		if err := connectAndListen(url, config); err != nil {
			log.Printf("Connection error: %v", err)
		}
		log.Println("Reconnecting in 5 seconds...")
		time.Sleep(5 * time.Second)
	}
}

func connectAndListen(url string, config Config) error {
	log.Printf("Connecting to %s", url)

	resp, err := http.Get(url)
	if err != nil {
		return fmt.Errorf("failed to connect: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("unexpected status code: %d", resp.StatusCode)
	}

	log.Println("Connected successfully")

	scanner := bufio.NewScanner(resp.Body)
	for scanner.Scan() {
		var msg Message
		if err := json.Unmarshal(scanner.Bytes(), &msg); err != nil {
			log.Printf("Failed to parse message: %v", err)
			continue
		}

		// Only process actual messages, skip keepalive and open events
		if msg.Event == "message" {
			handleMessage(msg, config)
		}
	}

	if err := scanner.Err(); err != nil {
		return fmt.Errorf("scanner error: %w", err)
	}

	return nil
}

func handleMessage(msg Message, config Config) {
	log.Printf("Received [%s]: %s", msg.Topic, msg.Message)

	// Build the text to speak
	var text string
	if msg.Title != "" {
		text = fmt.Sprintf("%s. %s", msg.Title, msg.Message)
	} else {
		text = msg.Message
	}

	// Execute TTS command
	if err := speak(config.SayCommand, text); err != nil {
		log.Printf("TTS error: %v", err)
	}
}

func speak(sayCmd, text string) error {
	cmd := exec.Command(sayCmd, text)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	return cmd.Run()
}

func getEnv(key, fallback string) string {
	if value, ok := os.LookupEnv(key); ok {
		return value
	}
	return fallback
}

func expandPath(path string) string {
	if strings.HasPrefix(path, "~/") {
		home, err := os.UserHomeDir()
		if err != nil {
			return path
		}
		return filepath.Join(home, path[2:])
	}
	return path
}

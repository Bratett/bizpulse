package middleware

import (
	"fmt"
	"net/http"
	"sync"
	"time"
)

type rateLimiter struct {
	mu       sync.Mutex
	attempts map[string][]time.Time
	limit    int
	window   time.Duration
}

func newRateLimiter(limit int, window time.Duration) *rateLimiter {
	rl := &rateLimiter{
		attempts: make(map[string][]time.Time),
		limit:    limit,
		window:   window,
	}
	go rl.cleanup()
	return rl
}

func (rl *rateLimiter) allow(key string) bool {
	rl.mu.Lock()
	defer rl.mu.Unlock()

	now := time.Now()
	cutoff := now.Add(-rl.window)

	// Remove expired entries
	valid := make([]time.Time, 0)
	for _, t := range rl.attempts[key] {
		if t.After(cutoff) {
			valid = append(valid, t)
		}
	}

	if len(valid) >= rl.limit {
		rl.attempts[key] = valid
		return false
	}

	rl.attempts[key] = append(valid, now)
	return true
}

func (rl *rateLimiter) cleanup() {
	for {
		time.Sleep(5 * time.Minute)
		rl.mu.Lock()
		cutoff := time.Now().Add(-rl.window)
		for key, times := range rl.attempts {
			valid := make([]time.Time, 0)
			for _, t := range times {
				if t.After(cutoff) {
					valid = append(valid, t)
				}
			}
			if len(valid) == 0 {
				delete(rl.attempts, key)
			} else {
				rl.attempts[key] = valid
			}
		}
		rl.mu.Unlock()
	}
}

// RateLimit returns middleware that limits requests per IP.
// 5 attempts per 15 minutes for auth endpoints.
func RateLimit(limit int, window time.Duration) func(http.HandlerFunc) http.HandlerFunc {
	rl := newRateLimiter(limit, window)

	return func(next http.HandlerFunc) http.HandlerFunc {
		return func(w http.ResponseWriter, r *http.Request) {
			ip := r.Header.Get("X-Forwarded-For")
			if ip == "" {
				ip = r.RemoteAddr
			}

			if !rl.allow(ip) {
				w.Header().Set("Content-Type", "application/json")
				w.Header().Set("Retry-After", fmt.Sprintf("%d", int(window.Seconds())))
				w.WriteHeader(http.StatusTooManyRequests)
				fmt.Fprintf(w, `{"error":{"code":"RATE_LIMITED","message":"Too many attempts. Try again later."}}`)
				return
			}

			next(w, r)
		}
	}
}

package middleware

import (
	"net/http"
	"net/http/httptest"
	"strconv"
	"testing"
	"time"
)

func TestRateLimiter_Allow(t *testing.T) {
	t.Run("first request is allowed", func(t *testing.T) {
		rl := &rateLimiter{
			attempts: make(map[string][]time.Time),
			limit:    5,
			window:   15 * time.Minute,
		}

		if !rl.allow("192.168.1.1") {
			t.Error("first request should be allowed")
		}
	})

	t.Run("requests within limit are allowed", func(t *testing.T) {
		rl := &rateLimiter{
			attempts: make(map[string][]time.Time),
			limit:    5,
			window:   15 * time.Minute,
		}

		for i := 0; i < 5; i++ {
			if !rl.allow("192.168.1.1") {
				t.Errorf("request %d should be allowed", i+1)
			}
		}
	})

	t.Run("request exceeding limit is blocked", func(t *testing.T) {
		rl := &rateLimiter{
			attempts: make(map[string][]time.Time),
			limit:    5,
			window:   15 * time.Minute,
		}

		for i := 0; i < 5; i++ {
			rl.allow("192.168.1.1")
		}

		if rl.allow("192.168.1.1") {
			t.Error("6th request should be blocked")
		}
	})

	t.Run("different keys are independent", func(t *testing.T) {
		rl := &rateLimiter{
			attempts: make(map[string][]time.Time),
			limit:    2,
			window:   15 * time.Minute,
		}

		// Fill up IP1
		rl.allow("ip1")
		rl.allow("ip1")
		if rl.allow("ip1") {
			t.Error("ip1 3rd request should be blocked")
		}

		// IP2 should still be allowed
		if !rl.allow("ip2") {
			t.Error("ip2 should be allowed independently")
		}
	})

	t.Run("expired entries are cleaned during allow", func(t *testing.T) {
		rl := &rateLimiter{
			attempts: make(map[string][]time.Time),
			limit:    2,
			window:   100 * time.Millisecond,
		}

		rl.allow("key1")
		rl.allow("key1")

		// Should be blocked
		if rl.allow("key1") {
			t.Error("should be blocked at limit")
		}

		// Wait for window to expire
		time.Sleep(150 * time.Millisecond)

		// Should be allowed again after window expires
		if !rl.allow("key1") {
			t.Error("should be allowed after window expires")
		}
	})
}

func TestRateLimit_Middleware(t *testing.T) {
	dummyHandler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("OK"))
	})

	t.Run("requests within limit get 200", func(t *testing.T) {
		limiter := RateLimit(5, 15*time.Minute)
		handler := limiter(dummyHandler)

		for i := 0; i < 5; i++ {
			req := httptest.NewRequest(http.MethodPost, "/api/auth/login", nil)
			req.RemoteAddr = "10.0.0.1:12345"
			rr := httptest.NewRecorder()

			handler.ServeHTTP(rr, req)

			if rr.Code != http.StatusOK {
				t.Errorf("request %d: status = %d, want %d", i+1, rr.Code, http.StatusOK)
			}
		}
	})

	t.Run("6th request gets 429", func(t *testing.T) {
		limiter := RateLimit(5, 15*time.Minute)
		handler := limiter(dummyHandler)

		for i := 0; i < 5; i++ {
			req := httptest.NewRequest(http.MethodPost, "/api/auth/login", nil)
			req.RemoteAddr = "10.0.0.2:12345"
			rr := httptest.NewRecorder()
			handler.ServeHTTP(rr, req)
		}

		// 6th request
		req := httptest.NewRequest(http.MethodPost, "/api/auth/login", nil)
		req.RemoteAddr = "10.0.0.2:12345"
		rr := httptest.NewRecorder()

		handler.ServeHTTP(rr, req)

		if rr.Code != http.StatusTooManyRequests {
			t.Errorf("status = %d, want %d", rr.Code, http.StatusTooManyRequests)
		}
	})

	t.Run("429 response includes Retry-After header", func(t *testing.T) {
		window := 15 * time.Minute
		limiter := RateLimit(1, window)
		handler := limiter(dummyHandler)

		// First request passes
		req := httptest.NewRequest(http.MethodPost, "/api/auth/login", nil)
		req.RemoteAddr = "10.0.0.3:12345"
		rr := httptest.NewRecorder()
		handler.ServeHTTP(rr, req)

		// Second request blocked
		req = httptest.NewRequest(http.MethodPost, "/api/auth/login", nil)
		req.RemoteAddr = "10.0.0.3:12345"
		rr = httptest.NewRecorder()
		handler.ServeHTTP(rr, req)

		retryAfter := rr.Header().Get("Retry-After")
		if retryAfter == "" {
			t.Error("expected Retry-After header on 429 response")
		}

		retrySeconds, err := strconv.Atoi(retryAfter)
		if err != nil {
			t.Errorf("Retry-After should be an integer, got %q", retryAfter)
		}
		expectedSeconds := int(window.Seconds())
		if retrySeconds != expectedSeconds {
			t.Errorf("Retry-After = %d, want %d", retrySeconds, expectedSeconds)
		}
	})

	t.Run("429 response has JSON error body", func(t *testing.T) {
		limiter := RateLimit(1, 1*time.Minute)
		handler := limiter(dummyHandler)

		// Exhaust limit
		req := httptest.NewRequest(http.MethodPost, "/", nil)
		req.RemoteAddr = "10.0.0.4:12345"
		rr := httptest.NewRecorder()
		handler.ServeHTTP(rr, req)

		// Blocked request
		req = httptest.NewRequest(http.MethodPost, "/", nil)
		req.RemoteAddr = "10.0.0.4:12345"
		rr = httptest.NewRecorder()
		handler.ServeHTTP(rr, req)

		contentType := rr.Header().Get("Content-Type")
		if contentType != "application/json" {
			t.Errorf("Content-Type = %q, want %q", contentType, "application/json")
		}

		body := rr.Body.String()
		if body == "" {
			t.Error("expected non-empty body on 429 response")
		}
	})

	t.Run("uses X-Forwarded-For when present", func(t *testing.T) {
		limiter := RateLimit(1, 15*time.Minute)
		handler := limiter(dummyHandler)

		// First request from forwarded IP
		req := httptest.NewRequest(http.MethodPost, "/", nil)
		req.Header.Set("X-Forwarded-For", "203.0.113.1")
		req.RemoteAddr = "10.0.0.5:12345"
		rr := httptest.NewRecorder()
		handler.ServeHTTP(rr, req)

		if rr.Code != http.StatusOK {
			t.Errorf("first request: status = %d, want %d", rr.Code, http.StatusOK)
		}

		// Second request from same forwarded IP should be blocked
		req = httptest.NewRequest(http.MethodPost, "/", nil)
		req.Header.Set("X-Forwarded-For", "203.0.113.1")
		req.RemoteAddr = "10.0.0.6:54321" // different RemoteAddr
		rr = httptest.NewRecorder()
		handler.ServeHTTP(rr, req)

		if rr.Code != http.StatusTooManyRequests {
			t.Errorf("second request from same X-Forwarded-For: status = %d, want %d", rr.Code, http.StatusTooManyRequests)
		}
	})

	t.Run("allowed again after window expires", func(t *testing.T) {
		limiter := RateLimit(1, 100*time.Millisecond)
		handler := limiter(dummyHandler)

		// Exhaust limit
		req := httptest.NewRequest(http.MethodPost, "/", nil)
		req.RemoteAddr = "10.0.0.7:12345"
		rr := httptest.NewRecorder()
		handler.ServeHTTP(rr, req)

		// Should be blocked
		req = httptest.NewRequest(http.MethodPost, "/", nil)
		req.RemoteAddr = "10.0.0.7:12345"
		rr = httptest.NewRecorder()
		handler.ServeHTTP(rr, req)

		if rr.Code != http.StatusTooManyRequests {
			t.Errorf("blocked request: status = %d, want %d", rr.Code, http.StatusTooManyRequests)
		}

		// Wait for window to expire
		time.Sleep(150 * time.Millisecond)

		// Should be allowed again
		req = httptest.NewRequest(http.MethodPost, "/", nil)
		req.RemoteAddr = "10.0.0.7:12345"
		rr = httptest.NewRecorder()
		handler.ServeHTTP(rr, req)

		if rr.Code != http.StatusOK {
			t.Errorf("after window: status = %d, want %d", rr.Code, http.StatusOK)
		}
	})
}

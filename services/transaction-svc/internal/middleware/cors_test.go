package middleware

import (
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestCORS_AllowedOrigin(t *testing.T) {
	handler := CORS("http://localhost:3000")(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	}))

	req := httptest.NewRequest(http.MethodGet, "/api/test", nil)
	req.Header.Set("Origin", "http://localhost:3000")
	rr := httptest.NewRecorder()

	handler.ServeHTTP(rr, req)

	if rr.Code != http.StatusOK {
		t.Errorf("status = %d, want %d", rr.Code, http.StatusOK)
	}

	acao := rr.Header().Get("Access-Control-Allow-Origin")
	if acao != "http://localhost:3000" {
		t.Errorf("Access-Control-Allow-Origin = %q, want %q", acao, "http://localhost:3000")
	}

	acac := rr.Header().Get("Access-Control-Allow-Credentials")
	if acac != "true" {
		t.Errorf("Access-Control-Allow-Credentials = %q, want %q", acac, "true")
	}
}

func TestCORS_DisallowedOrigin(t *testing.T) {
	handler := CORS("http://localhost:3000")(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	}))

	req := httptest.NewRequest(http.MethodGet, "/api/test", nil)
	req.Header.Set("Origin", "http://evil.example.com")
	rr := httptest.NewRecorder()

	handler.ServeHTTP(rr, req)

	if rr.Code != http.StatusOK {
		t.Errorf("status = %d, want %d", rr.Code, http.StatusOK)
	}

	acao := rr.Header().Get("Access-Control-Allow-Origin")
	if acao != "" {
		t.Errorf("Access-Control-Allow-Origin should not be set for disallowed origin, got %q", acao)
	}

	acac := rr.Header().Get("Access-Control-Allow-Credentials")
	if acac != "" {
		t.Errorf("Access-Control-Allow-Credentials should not be set for disallowed origin, got %q", acac)
	}
}

func TestCORS_OptionsRequest(t *testing.T) {
	handlerCalled := false
	handler := CORS("http://localhost:3000")(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		handlerCalled = true
		w.WriteHeader(http.StatusOK)
	}))

	req := httptest.NewRequest(http.MethodOptions, "/api/test", nil)
	req.Header.Set("Origin", "http://localhost:3000")
	rr := httptest.NewRecorder()

	handler.ServeHTTP(rr, req)

	if rr.Code != http.StatusNoContent {
		t.Errorf("status = %d, want %d", rr.Code, http.StatusNoContent)
	}

	if handlerCalled {
		t.Error("next handler should not be called for OPTIONS request")
	}

	acao := rr.Header().Get("Access-Control-Allow-Origin")
	if acao != "http://localhost:3000" {
		t.Errorf("Access-Control-Allow-Origin = %q, want %q", acao, "http://localhost:3000")
	}

	acam := rr.Header().Get("Access-Control-Allow-Methods")
	if acam == "" {
		t.Error("Access-Control-Allow-Methods should be set on OPTIONS response")
	}

	acah := rr.Header().Get("Access-Control-Allow-Headers")
	if acah == "" {
		t.Error("Access-Control-Allow-Headers should be set on OPTIONS response")
	}
}

func TestCORS_MultipleAllowedOrigins(t *testing.T) {
	handler := CORS("http://localhost:3000,https://app.bizpulse.com,https://staging.bizpulse.com")(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	}))

	tests := []struct {
		name           string
		origin         string
		expectAllowed  bool
		expectedOrigin string
	}{
		{"first origin", "http://localhost:3000", true, "http://localhost:3000"},
		{"second origin", "https://app.bizpulse.com", true, "https://app.bizpulse.com"},
		{"third origin", "https://staging.bizpulse.com", true, "https://staging.bizpulse.com"},
		{"unknown origin", "https://evil.example.com", false, ""},
		{"empty origin", "", false, ""},
		{"partial match", "http://localhost", false, ""},
		{"port mismatch", "http://localhost:8080", false, ""},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			req := httptest.NewRequest(http.MethodGet, "/api/test", nil)
			if tt.origin != "" {
				req.Header.Set("Origin", tt.origin)
			}
			rr := httptest.NewRecorder()

			handler.ServeHTTP(rr, req)

			acao := rr.Header().Get("Access-Control-Allow-Origin")
			if tt.expectAllowed {
				if acao != tt.expectedOrigin {
					t.Errorf("Access-Control-Allow-Origin = %q, want %q", acao, tt.expectedOrigin)
				}
			} else {
				if acao != "" {
					t.Errorf("Access-Control-Allow-Origin should not be set, got %q", acao)
				}
			}
		})
	}
}

func TestCORS_OptionsWithDisallowedOrigin(t *testing.T) {
	handler := CORS("http://localhost:3000")(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		t.Error("next handler should not be called for OPTIONS")
	}))

	req := httptest.NewRequest(http.MethodOptions, "/api/test", nil)
	req.Header.Set("Origin", "http://evil.example.com")
	rr := httptest.NewRecorder()

	handler.ServeHTTP(rr, req)

	// OPTIONS still returns 204 regardless of origin
	if rr.Code != http.StatusNoContent {
		t.Errorf("status = %d, want %d", rr.Code, http.StatusNoContent)
	}

	// But no CORS origin header
	acao := rr.Header().Get("Access-Control-Allow-Origin")
	if acao != "" {
		t.Errorf("Access-Control-Allow-Origin should not be set for disallowed origin, got %q", acao)
	}
}

func TestCORS_AllowMethodsAndHeaders(t *testing.T) {
	handler := CORS("http://localhost:3000")(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	}))

	req := httptest.NewRequest(http.MethodGet, "/api/test", nil)
	req.Header.Set("Origin", "http://localhost:3000")
	rr := httptest.NewRecorder()

	handler.ServeHTTP(rr, req)

	methods := rr.Header().Get("Access-Control-Allow-Methods")
	if methods == "" {
		t.Error("Access-Control-Allow-Methods should always be set")
	}

	headers := rr.Header().Get("Access-Control-Allow-Headers")
	if headers == "" {
		t.Error("Access-Control-Allow-Headers should always be set")
	}
}

func TestCORS_NoOriginHeader(t *testing.T) {
	handler := CORS("http://localhost:3000")(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	}))

	req := httptest.NewRequest(http.MethodGet, "/api/test", nil)
	// No Origin header
	rr := httptest.NewRecorder()

	handler.ServeHTTP(rr, req)

	if rr.Code != http.StatusOK {
		t.Errorf("status = %d, want %d", rr.Code, http.StatusOK)
	}

	acao := rr.Header().Get("Access-Control-Allow-Origin")
	if acao != "" {
		t.Errorf("Access-Control-Allow-Origin should not be set without Origin header, got %q", acao)
	}
}

func TestCORS_OriginsWithWhitespace(t *testing.T) {
	// Origins string with spaces around commas
	handler := CORS(" http://localhost:3000 , https://app.bizpulse.com ")(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	}))

	tests := []struct {
		name          string
		origin        string
		expectAllowed bool
	}{
		{"first origin trimmed", "http://localhost:3000", true},
		{"second origin trimmed", "https://app.bizpulse.com", true},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			req := httptest.NewRequest(http.MethodGet, "/api/test", nil)
			req.Header.Set("Origin", tt.origin)
			rr := httptest.NewRecorder()

			handler.ServeHTTP(rr, req)

			acao := rr.Header().Get("Access-Control-Allow-Origin")
			if tt.expectAllowed && acao != tt.origin {
				t.Errorf("Access-Control-Allow-Origin = %q, want %q", acao, tt.origin)
			}
		})
	}
}

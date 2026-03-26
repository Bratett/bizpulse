package keycloak

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strings"
	"sync"
	"time"
)

// Client communicates with the Keycloak Admin REST API and token endpoints.
type Client struct {
	adminURL     string
	realm        string
	clientID     string
	clientSecret string
	httpClient   *http.Client

	mu         sync.Mutex
	adminToken string
	tokenExp   time.Time
}

// TokenResponse represents the OAuth2 token endpoint response.
type TokenResponse struct {
	AccessToken  string `json:"access_token"`
	RefreshToken string `json:"refresh_token,omitempty"`
	TokenType    string `json:"token_type"`
	ExpiresIn    int    `json:"expires_in"`
}

// keycloakError is the structure Keycloak returns on errors.
type keycloakError struct {
	ErrorCode   string `json:"error"`
	Description string `json:"error_description,omitempty"`
	Message     string `json:"errorMessage,omitempty"`
}

func (e *keycloakError) String() string {
	if e.Description != "" {
		return e.Description
	}
	if e.Message != "" {
		return e.Message
	}
	return e.ErrorCode
}

// NewClient creates a Keycloak client with the given service account credentials.
func NewClient(adminURL, realm, clientID, clientSecret string) *Client {
	return &Client{
		adminURL:     strings.TrimRight(adminURL, "/"),
		realm:        realm,
		clientID:     clientID,
		clientSecret: clientSecret,
		httpClient: &http.Client{
			Timeout: 15 * time.Second,
		},
	}
}

// GetAdminToken obtains (or reuses a cached) service-account access token
// from the master realm token endpoint.
func (c *Client) GetAdminToken() (string, error) {
	c.mu.Lock()
	defer c.mu.Unlock()

	// Reuse if still valid with a 30-second safety margin
	if c.adminToken != "" && time.Now().Before(c.tokenExp.Add(-30*time.Second)) {
		return c.adminToken, nil
	}

	data := url.Values{
		"grant_type":    {"client_credentials"},
		"client_id":     {c.clientID},
		"client_secret": {c.clientSecret},
	}

	tokenURL := fmt.Sprintf("%s/realms/master/protocol/openid-connect/token", c.adminURL)
	resp, err := c.httpClient.PostForm(tokenURL, data)
	if err != nil {
		return "", fmt.Errorf("keycloak admin token request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("keycloak admin token: status %d", resp.StatusCode)
	}

	var tok TokenResponse
	if err := json.NewDecoder(resp.Body).Decode(&tok); err != nil {
		return "", fmt.Errorf("keycloak admin token decode: %w", err)
	}

	c.adminToken = tok.AccessToken
	c.tokenExp = time.Now().Add(time.Duration(tok.ExpiresIn) * time.Second)
	return c.adminToken, nil
}

// CreateUser creates a user in the Keycloak realm.
// Returns the Keycloak user ID on success.
func (c *Client) CreateUser(email, password, firstName, lastName string) (string, error) {
	token, err := c.GetAdminToken()
	if err != nil {
		return "", fmt.Errorf("get admin token: %w", err)
	}

	body := map[string]any{
		"username":  email,
		"email":     email,
		"firstName": firstName,
		"lastName":  lastName,
		"enabled":   true,
		"credentials": []map[string]any{
			{
				"type":      "password",
				"value":     password,
				"temporary": false,
			},
		},
	}

	payload, err := json.Marshal(body)
	if err != nil {
		return "", fmt.Errorf("marshal create user: %w", err)
	}

	usersURL := fmt.Sprintf("%s/admin/realms/%s/users", c.adminURL, c.realm)
	req, err := http.NewRequest(http.MethodPost, usersURL, bytes.NewReader(payload))
	if err != nil {
		return "", fmt.Errorf("build create user request: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+token)

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return "", fmt.Errorf("keycloak create user: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusConflict {
		return "", fmt.Errorf("user already exists in Keycloak")
	}

	if resp.StatusCode != http.StatusCreated {
		respBody, _ := io.ReadAll(resp.Body)
		var kcErr keycloakError
		if json.Unmarshal(respBody, &kcErr) == nil && kcErr.String() != "" {
			return "", fmt.Errorf("keycloak create user (%d): %s", resp.StatusCode, kcErr.String())
		}
		return "", fmt.Errorf("keycloak create user: status %d", resp.StatusCode)
	}

	// Extract Keycloak user ID from Location header
	location := resp.Header.Get("Location")
	if location == "" {
		return "", fmt.Errorf("keycloak create user: no Location header")
	}
	parts := strings.Split(location, "/")
	keycloakUserID := parts[len(parts)-1]

	return keycloakUserID, nil
}

// SetUserAttribute sets a custom attribute on a Keycloak user.
func (c *Client) SetUserAttribute(keycloakUserID, key, value string) error {
	token, err := c.GetAdminToken()
	if err != nil {
		return fmt.Errorf("get admin token: %w", err)
	}

	// First, GET the current user representation
	userURL := fmt.Sprintf("%s/admin/realms/%s/users/%s", c.adminURL, c.realm, keycloakUserID)
	getReq, err := http.NewRequest(http.MethodGet, userURL, nil)
	if err != nil {
		return fmt.Errorf("build get user request: %w", err)
	}
	getReq.Header.Set("Authorization", "Bearer "+token)

	getResp, err := c.httpClient.Do(getReq)
	if err != nil {
		return fmt.Errorf("keycloak get user: %w", err)
	}
	defer getResp.Body.Close()

	if getResp.StatusCode != http.StatusOK {
		return fmt.Errorf("keycloak get user: status %d", getResp.StatusCode)
	}

	var userRep map[string]any
	if err := json.NewDecoder(getResp.Body).Decode(&userRep); err != nil {
		return fmt.Errorf("decode user rep: %w", err)
	}

	// Merge the new attribute into the existing attributes map
	attrs, _ := userRep["attributes"].(map[string]any)
	if attrs == nil {
		attrs = make(map[string]any)
	}
	attrs[key] = []string{value}
	userRep["attributes"] = attrs

	payload, err := json.Marshal(userRep)
	if err != nil {
		return fmt.Errorf("marshal user update: %w", err)
	}

	putReq, err := http.NewRequest(http.MethodPut, userURL, bytes.NewReader(payload))
	if err != nil {
		return fmt.Errorf("build put user request: %w", err)
	}
	putReq.Header.Set("Content-Type", "application/json")
	putReq.Header.Set("Authorization", "Bearer "+token)

	putResp, err := c.httpClient.Do(putReq)
	if err != nil {
		return fmt.Errorf("keycloak update user: %w", err)
	}
	defer putResp.Body.Close()

	if putResp.StatusCode != http.StatusNoContent {
		return fmt.Errorf("keycloak update user: status %d", putResp.StatusCode)
	}

	return nil
}

// GetToken performs a Resource Owner Password Credentials grant
// against the realm's token endpoint.
func (c *Client) GetToken(email, password string) (*TokenResponse, error) {
	data := url.Values{
		"grant_type":    {"password"},
		"client_id":     {c.clientID},
		"client_secret": {c.clientSecret},
		"username":      {email},
		"password":      {password},
		"scope":         {"openid"},
	}

	tokenURL := fmt.Sprintf("%s/realms/%s/protocol/openid-connect/token", c.adminURL, c.realm)
	resp, err := c.httpClient.PostForm(tokenURL, data)
	if err != nil {
		return nil, fmt.Errorf("keycloak token request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		respBody, _ := io.ReadAll(resp.Body)
		var kcErr keycloakError
		if json.Unmarshal(respBody, &kcErr) == nil && kcErr.String() != "" {
			return nil, fmt.Errorf("keycloak token (%d): %s", resp.StatusCode, kcErr.String())
		}
		return nil, fmt.Errorf("keycloak token: status %d", resp.StatusCode)
	}

	var tok TokenResponse
	if err := json.NewDecoder(resp.Body).Decode(&tok); err != nil {
		return nil, fmt.Errorf("decode token response: %w", err)
	}

	return &tok, nil
}

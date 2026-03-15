package sheets

import (
	"bytes"
	"context"
	"crypto"
	"crypto/rand"
	"crypto/rsa"
	"crypto/sha256"
	"crypto/x509"
	"encoding/base64"
	"encoding/json"
	"encoding/pem"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strings"
	"sync"
	"time"

	"github.com/admin/turbo-potato/backend/internal/config"
)

const spreadsheetsScope = "https://www.googleapis.com/auth/spreadsheets"

type ValuesAPI interface {
	Append(ctx context.Context, spreadsheetID, readRange string, values [][]interface{}) error
	Get(ctx context.Context, spreadsheetID, readRange string) ([][]interface{}, error)
	Update(ctx context.Context, spreadsheetID, readRange string, values [][]interface{}) error
}

type SpreadsheetAdminAPI interface {
	GetSheetTitles(ctx context.Context, spreadsheetID string) ([]string, error)
	AddSheets(ctx context.Context, spreadsheetID string, titles []string) error
}

type GoogleValuesClient struct {
	httpClient *http.Client
	auth       *serviceAccountAuthorizer
}

type serviceAccountCredentials struct {
	ClientEmail string `json:"client_email"`
	PrivateKey  string `json:"private_key"`
	TokenURI    string `json:"token_uri"`
}

type serviceAccountAuthorizer struct {
	httpClient *http.Client
	creds      serviceAccountCredentials

	mu          sync.Mutex
	accessToken string
	expiresAt   time.Time
}

func NewGoogleValuesClient(_ context.Context, cfg config.Config) (*GoogleValuesClient, error) {
	if !cfg.UseGoogleSheets() {
		return nil, fmt.Errorf("google sheets is not configured")
	}

	var creds serviceAccountCredentials
	if err := json.Unmarshal([]byte(cfg.Sheets.ServiceAccountJSON), &creds); err != nil {
		return nil, fmt.Errorf("parse service account json: %w", err)
	}

	if creds.ClientEmail == "" || creds.PrivateKey == "" || creds.TokenURI == "" {
		return nil, fmt.Errorf("service account json is missing required fields")
	}

	httpClient := &http.Client{Timeout: 15 * time.Second}

	return &GoogleValuesClient{
		httpClient: httpClient,
		auth: &serviceAccountAuthorizer{
			httpClient: httpClient,
			creds:      creds,
		},
	}, nil
}

func (c *GoogleValuesClient) Append(ctx context.Context, spreadsheetID, readRange string, values [][]interface{}) error {
	payload := map[string][][]interface{}{
		"values": values,
	}

	body, err := json.Marshal(payload)
	if err != nil {
		return fmt.Errorf("marshal append payload: %w", err)
	}

	endpoint := fmt.Sprintf(
		"https://sheets.googleapis.com/v4/spreadsheets/%s/values/%s:append?valueInputOption=RAW",
		url.PathEscape(spreadsheetID),
		url.PathEscape(readRange),
	)

	request, err := http.NewRequestWithContext(ctx, http.MethodPost, endpoint, bytes.NewReader(body))
	if err != nil {
		return fmt.Errorf("build append request: %w", err)
	}
	request.Header.Set("Content-Type", "application/json")

	if err := c.authorize(ctx, request); err != nil {
		return err
	}

	response, err := c.httpClient.Do(request)
	if err != nil {
		return fmt.Errorf("append values: %w", err)
	}
	defer response.Body.Close()

	if response.StatusCode >= 300 {
		return fmt.Errorf("append values: google sheets returned %s", response.Status)
	}

	return nil
}

func (c *GoogleValuesClient) Get(ctx context.Context, spreadsheetID, readRange string) ([][]interface{}, error) {
	endpoint := fmt.Sprintf(
		"https://sheets.googleapis.com/v4/spreadsheets/%s/values/%s",
		url.PathEscape(spreadsheetID),
		url.PathEscape(readRange),
	)

	request, err := http.NewRequestWithContext(ctx, http.MethodGet, endpoint, nil)
	if err != nil {
		return nil, fmt.Errorf("build get request: %w", err)
	}

	if err := c.authorize(ctx, request); err != nil {
		return nil, err
	}

	response, err := c.httpClient.Do(request)
	if err != nil {
		return nil, fmt.Errorf("get values: %w", err)
	}
	defer response.Body.Close()

	if response.StatusCode >= 300 {
		return nil, fmt.Errorf("get values: google sheets returned %s", response.Status)
	}

	var payload struct {
		Values [][]interface{} `json:"values"`
	}

	if err := json.NewDecoder(response.Body).Decode(&payload); err != nil {
		return nil, fmt.Errorf("decode get values payload: %w", err)
	}

	return payload.Values, nil
}

func (c *GoogleValuesClient) Update(ctx context.Context, spreadsheetID, readRange string, values [][]interface{}) error {
	payload := map[string][][]interface{}{
		"values": values,
	}

	body, err := json.Marshal(payload)
	if err != nil {
		return fmt.Errorf("marshal update payload: %w", err)
	}

	endpoint := fmt.Sprintf(
		"https://sheets.googleapis.com/v4/spreadsheets/%s/values/%s?valueInputOption=RAW",
		url.PathEscape(spreadsheetID),
		url.PathEscape(readRange),
	)

	request, err := http.NewRequestWithContext(ctx, http.MethodPut, endpoint, bytes.NewReader(body))
	if err != nil {
		return fmt.Errorf("build update request: %w", err)
	}
	request.Header.Set("Content-Type", "application/json")

	if err := c.authorize(ctx, request); err != nil {
		return err
	}

	response, err := c.httpClient.Do(request)
	if err != nil {
		return fmt.Errorf("update values: %w", err)
	}
	defer response.Body.Close()

	if response.StatusCode >= 300 {
		return fmt.Errorf("update values: google sheets returned %s", response.Status)
	}

	return nil
}

func (c *GoogleValuesClient) GetSheetTitles(ctx context.Context, spreadsheetID string) ([]string, error) {
	endpoint := fmt.Sprintf(
		"https://sheets.googleapis.com/v4/spreadsheets/%s?fields=sheets.properties.title",
		url.PathEscape(spreadsheetID),
	)

	request, err := http.NewRequestWithContext(ctx, http.MethodGet, endpoint, nil)
	if err != nil {
		return nil, fmt.Errorf("build get spreadsheet request: %w", err)
	}

	if err := c.authorize(ctx, request); err != nil {
		return nil, err
	}

	response, err := c.httpClient.Do(request)
	if err != nil {
		return nil, fmt.Errorf("get spreadsheet: %w", err)
	}
	defer response.Body.Close()

	if response.StatusCode >= 300 {
		return nil, fmt.Errorf("get spreadsheet: google sheets returned %s", response.Status)
	}

	var payload struct {
		Sheets []struct {
			Properties struct {
				Title string `json:"title"`
			} `json:"properties"`
		} `json:"sheets"`
	}

	if err := json.NewDecoder(response.Body).Decode(&payload); err != nil {
		return nil, fmt.Errorf("decode spreadsheet payload: %w", err)
	}

	titles := make([]string, 0, len(payload.Sheets))
	for _, sheet := range payload.Sheets {
		titles = append(titles, sheet.Properties.Title)
	}

	return titles, nil
}

func (c *GoogleValuesClient) AddSheets(ctx context.Context, spreadsheetID string, titles []string) error {
	if len(titles) == 0 {
		return nil
	}

	requests := make([]map[string]map[string]map[string]string, 0, len(titles))
	for _, title := range titles {
		requests = append(requests, map[string]map[string]map[string]string{
			"addSheet": {
				"properties": {
					"title": title,
				},
			},
		})
	}

	body, err := json.Marshal(map[string]any{
		"requests": requests,
	})
	if err != nil {
		return fmt.Errorf("marshal add sheets payload: %w", err)
	}

	endpoint := fmt.Sprintf(
		"https://sheets.googleapis.com/v4/spreadsheets/%s:batchUpdate",
		url.PathEscape(spreadsheetID),
	)

	request, err := http.NewRequestWithContext(ctx, http.MethodPost, endpoint, bytes.NewReader(body))
	if err != nil {
		return fmt.Errorf("build add sheets request: %w", err)
	}
	request.Header.Set("Content-Type", "application/json")

	if err := c.authorize(ctx, request); err != nil {
		return err
	}

	response, err := c.httpClient.Do(request)
	if err != nil {
		return fmt.Errorf("add sheets: %w", err)
	}
	defer response.Body.Close()

	if response.StatusCode >= 300 {
		return fmt.Errorf("add sheets: google sheets returned %s", response.Status)
	}

	return nil
}

func (c *GoogleValuesClient) authorize(ctx context.Context, request *http.Request) error {
	token, err := c.auth.Token(ctx)
	if err != nil {
		return fmt.Errorf("authorize request: %w", err)
	}

	request.Header.Set("Authorization", "Bearer "+token)
	return nil
}

func (a *serviceAccountAuthorizer) Token(ctx context.Context) (string, error) {
	a.mu.Lock()
	defer a.mu.Unlock()

	if a.accessToken != "" && time.Until(a.expiresAt) > time.Minute {
		return a.accessToken, nil
	}

	assertion, err := a.buildAssertion()
	if err != nil {
		return "", err
	}

	form := url.Values{}
	form.Set("grant_type", "urn:ietf:params:oauth:grant-type:jwt-bearer")
	form.Set("assertion", assertion)

	request, err := http.NewRequestWithContext(ctx, http.MethodPost, a.creds.TokenURI, strings.NewReader(form.Encode()))
	if err != nil {
		return "", fmt.Errorf("build token request: %w", err)
	}
	request.Header.Set("Content-Type", "application/x-www-form-urlencoded")

	response, err := a.httpClient.Do(request)
	if err != nil {
		return "", fmt.Errorf("request access token: %w", err)
	}
	defer response.Body.Close()

	if response.StatusCode >= 300 {
		body, _ := io.ReadAll(response.Body)
		return "", fmt.Errorf("request access token: %s: %s", response.Status, strings.TrimSpace(string(body)))
	}

	var payload struct {
		AccessToken string `json:"access_token"`
		ExpiresIn   int64  `json:"expires_in"`
	}

	if err := json.NewDecoder(response.Body).Decode(&payload); err != nil {
		return "", fmt.Errorf("decode token response: %w", err)
	}

	a.accessToken = payload.AccessToken
	a.expiresAt = time.Now().Add(time.Duration(payload.ExpiresIn) * time.Second)

	return a.accessToken, nil
}

func (a *serviceAccountAuthorizer) buildAssertion() (string, error) {
	headerJSON, err := json.Marshal(map[string]string{
		"alg": "RS256",
		"typ": "JWT",
	})
	if err != nil {
		return "", fmt.Errorf("marshal jwt header: %w", err)
	}

	now := time.Now().UTC()
	claimsJSON, err := json.Marshal(map[string]interface{}{
		"iss":   a.creds.ClientEmail,
		"scope": spreadsheetsScope,
		"aud":   a.creds.TokenURI,
		"iat":   now.Unix(),
		"exp":   now.Add(time.Hour).Unix(),
	})
	if err != nil {
		return "", fmt.Errorf("marshal jwt claims: %w", err)
	}

	unsignedToken := base64.RawURLEncoding.EncodeToString(headerJSON) + "." +
		base64.RawURLEncoding.EncodeToString(claimsJSON)

	privateKey, err := parsePrivateKey(a.creds.PrivateKey)
	if err != nil {
		return "", err
	}

	hash := sha256.Sum256([]byte(unsignedToken))
	signature, err := rsa.SignPKCS1v15(rand.Reader, privateKey, crypto.SHA256, hash[:])
	if err != nil {
		return "", fmt.Errorf("sign jwt assertion: %w", err)
	}

	return unsignedToken + "." + base64.RawURLEncoding.EncodeToString(signature), nil
}

func parsePrivateKey(privateKeyPEM string) (*rsa.PrivateKey, error) {
	block, _ := pem.Decode([]byte(privateKeyPEM))
	if block == nil {
		return nil, fmt.Errorf("decode private key pem: no block found")
	}

	if parsed, err := x509.ParsePKCS8PrivateKey(block.Bytes); err == nil {
		rsaKey, ok := parsed.(*rsa.PrivateKey)
		if !ok {
			return nil, fmt.Errorf("parse private key pem: expected RSA private key")
		}
		return rsaKey, nil
	}

	parsed, err := x509.ParsePKCS1PrivateKey(block.Bytes)
	if err != nil {
		return nil, fmt.Errorf("parse private key pem: %w", err)
	}

	return parsed, nil
}

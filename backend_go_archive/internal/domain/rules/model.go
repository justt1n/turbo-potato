package rules

type FixedCostRule struct {
	Name           string `json:"name"`
	ExpectedAmount int64  `json:"expectedAmount"`
	WindowStartDay int    `json:"windowStartDay"`
	WindowEndDay   int    `json:"windowEndDay"`
	LinkedJarCode  string `json:"linkedJarCode"`
	IsActive       bool   `json:"isActive"`
}

type CreateFixedCostRuleInput struct {
	Name           string `json:"name"`
	ExpectedAmount int64  `json:"expectedAmount"`
	WindowStartDay int    `json:"windowStartDay"`
	WindowEndDay   int    `json:"windowEndDay"`
	LinkedJarCode  string `json:"linkedJarCode"`
	IsActive       bool   `json:"isActive"`
}

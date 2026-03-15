package metrics

type Summary struct {
	STS              MetricValue      `json:"sts"`
	Anomaly          MetricValue      `json:"anomaly"`
	GoalPace         MetricValue      `json:"goalPace"`
	OperatingPosture OperatingPosture `json:"operatingPosture"`
	Baselines        []BaselineSeries `json:"baselines"`
}

type MetricValue struct {
	Label    string `json:"label"`
	Value    string `json:"value"`
	Caption  string `json:"caption"`
	Progress int    `json:"progress"`
	Status   string `json:"status"`
}

type OperatingPosture struct {
	Status string        `json:"status"`
	Items  []SummaryItem `json:"items"`
}

type SummaryItem struct {
	Label string `json:"label"`
	Value string `json:"value"`
}

type BaselineSeries struct {
	Label       string `json:"label"`
	Description string `json:"description"`
	Values      []int  `json:"values"`
	Current     string `json:"current"`
	Delta       string `json:"delta"`
	ColorToken  string `json:"colorToken"`
}

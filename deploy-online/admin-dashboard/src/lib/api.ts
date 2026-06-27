const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  (typeof window !== "undefined" && window.location.hostname === "localhost"
    ? "http://localhost:8080"
    : "https://suraksha-setu-production.up.railway.app");

export async function getAccountSummary() {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/account/summary`,
    {
      cache: "no-store",
    }
  );

  if (!response.ok) {
    throw new Error("Failed to fetch account summary");
  }

  return response.json();
}

export async function getHourlyRiskTrends(
  windowStart: string,
  windowEnd: string
) {
  const params = new URLSearchParams({
    windowStart,
    windowEnd,
  });

  const response = await fetch(
    `${API_BASE_URL}/api/v1/analytics/risk-events/trends/hourly?${params}`,
    {
      cache: "no-store",
    }
  );

  if (!response.ok) {
    throw new Error("Failed to fetch hourly trends");
  }

  return response.json();
}

export async function getHighRiskEvents(
  windowStart: string,
  windowEnd: string,
  minimumRiskScore = 80
) {
  const params = new URLSearchParams({
    windowStart,
    windowEnd,
    minimumRiskScore: minimumRiskScore.toString(),
  });

  const response = await fetch(
    `${API_BASE_URL}/api/v1/analytics/risk-events/high-risk?${params}`,
    {
      cache: "no-store",
    }
  );

  if (!response.ok) {
    throw new Error("Failed to fetch high risk events");
  }

  return response.json();
}

export async function getRiskEvents(
  windowStart: string,
  windowEnd: string
) {
  const params = new URLSearchParams({
    windowStart,
    windowEnd,
  });

  const response = await fetch(
    `${API_BASE_URL}/api/v1/analytics/risk-events?${params}`,
    {
      cache: "no-store",
    }
  );

  if (!response.ok) {
    throw new Error("Failed to fetch risk events");
  }

  return response.json();
}
const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";

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

export async function getRiskDistribution() {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/account/risk-distribution`,
    { cache: "no-store" }
  );

  if (!response.ok) {
    throw new Error("Failed to fetch risk distribution");
  }

  return response.json();
}

export async function getMonthlyStats() {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/account/monthly-stats`,
    { cache: "no-store" }
  );

  if (!response.ok) {
    throw new Error("Failed to fetch monthly stats");
  }

  return response.json();
}

export async function getTransactions() {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/transactions`,
    { cache: "no-store" }
  );

  if (!response.ok) {
    throw new Error("Failed to fetch transactions");
  }

  return response.json();
}
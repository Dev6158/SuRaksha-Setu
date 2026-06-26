const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";

  function authHeaders() {
  const token = localStorage.getItem("token");

  return {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
  };
}

export async function login(
  username: string,
  password: string
) {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/auth/login`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        username,
        password,
      }),
    }
  );

  if (!response.ok) {
    throw new Error("Login failed");
  }

  const data = await response.json();

  localStorage.setItem(
    "token",
    data.accessToken
  );
  localStorage.setItem(
  "user",
  JSON.stringify(data.user)
  );


  return data;
}

export async function getAccountSummary() {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/account/summary`,
    {
      headers: authHeaders(),
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
    { 
      headers: authHeaders(),
      cache: "no-store",
    }
  );

  if (!response.ok) {
    throw new Error("Failed to fetch risk distribution");
  }

  return response.json();
}

export async function getMonthlyStats() {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/account/monthly-stats`,
    { 
      headers: authHeaders(),
      cache: "no-store", 
    }
  );

  if (!response.ok) {
    throw new Error("Failed to fetch monthly stats");
  }

  return response.json();
}

export async function getTransactions() {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/transactions`,
    { 
      headers: authHeaders(),
      cache: "no-store",
    }
  );

  if (!response.ok) {
    throw new Error("Failed to fetch transactions");
  }

  return response.json();
}
let inMemoryToken: string | null = null;

export function setToken(token: string | null) {
    inMemoryToken = token;
}

const BASE_URL = '/api';

export async function apiClient(endpoint: string, options: RequestInit = {}) {
    const token = inMemoryToken;

    const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        ...(options.headers as Record<string, string>),
    };

    if (import.meta.env.DEV) {
        headers['ngrok-skip-browser-warning'] = 'true';
    }

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${BASE_URL}${endpoint}`, {
        ...options,
        headers: headers
    });

    if (!response.ok) {
        if (response.status === 401) {
            setToken(null);
            window.location.reload();
        }
        throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return await response.json();
}
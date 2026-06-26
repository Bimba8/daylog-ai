const BASE_URL = '/api';

export async function apiClient(endpoint: string, options: RequestInit = {}) {
    // 1. Пытаемся достать токен из хранилища браузера
    const token = localStorage.getItem('access_token');

    // 2. Собираем заголовки. 
    // Record<string, string> - это подсказка для TypeScript, что ключи и значения тут будут строками
    const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        'ngrok-skip-browser-warning': 'true',
        // Если при вызове функции передали еще какие-то свои заголовки, мы их подмешиваем сюда
        ...(options.headers as Record<string, string>),
    };

    // 3. Если токен физически существует, добавляем его в объект заголовков
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    // 4. Делаем сам сетевой запрос
    const response = await fetch(`${BASE_URL}${endpoint}`, {
        ...options,      // Подкидываем метод (GET/POST), тело запроса (body) и т.д.
        headers: headers // И наши заботливо собранные заголовки
    });

    // 5. Если бэкенд ответил ошибкой (например, 401 Unauthorized или 500)
    if (!response.ok) {
        throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    // 6. Если всё супер — распаковываем JSON
    return await response.json();
}
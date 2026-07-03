#!/bin/bash
set -e

# Подключаемся к базе от имени главного юзера и выполняем SQL
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- 1. Создаем пользователя (пароль подтянется из .env)
    CREATE USER metabase_ro WITH PASSWORD '${METABASE_RO_PASSWORD}';
    
    -- 2. Разрешаем ему подключаться к БД
    GRANT CONNECT ON DATABASE ${POSTGRES_DB} TO metabase_ro;
    
    -- 3. Пускаем его в основную схему public
    GRANT USAGE ON SCHEMA public TO metabase_ro;
    
    -- 4. Даем права на чтение ВСЕХ ТЕКУЩИХ таблиц
    GRANT SELECT ON ALL TABLES IN SCHEMA public TO metabase_ro;
    
    -- 5. Магия: даем права на чтение ВСЕХ БУДУЩИХ таблиц (которые мы создадим потом)
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO metabase_ro;
EOSQL
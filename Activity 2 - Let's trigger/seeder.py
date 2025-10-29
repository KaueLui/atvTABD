"""Script para aplicar o esquema do banco e popular dados iniciais."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Iterable

import psycopg
from faker import Faker
from psycopg import sql
from psycopg.rows import dict_row

BASE_DIR = Path(__file__).parent
SCHEMA_PATH = BASE_DIR / "schema.sql"
ENV_PATH = BASE_DIR / ".env"

faker = Faker("pt_BR")
DEFAULT_NUM_COLECIONADORES = 5
DEFAULT_NOVAS_CARTAS = 1
DEFAULT_COLECAO_MIN = 1
DEFAULT_COLECAO_MAX = 3


def load_env(path: Path = ENV_PATH) -> None:
    """Carrega variáveis do arquivo .env para o ambiente atual."""
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def configure_faker() -> None:
    """Configura a semente do Faker, caso informada via variável de ambiente."""
    seed = os.getenv("FAKER_SEED")
    if seed is None:
        return

    try:
        faker.seed_instance(int(seed))
    except ValueError:
        raise ValueError("A variável FAKER_SEED deve ser um inteiro válido.")


def get_env_int(var_name: str, default: int, min_value: int | None = None) -> int:
    raw = os.getenv(var_name)
    if raw is None:
        return default

    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"A variável {var_name} deve ser um inteiro válido.") from exc

    if min_value is not None and value < min_value:
        raise ValueError(
            f"A variável {var_name} deve ser maior ou igual a {min_value}."
        )

    return value


def get_conn_kwargs(dbname: str | None = None) -> Dict[str, str]:
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": os.getenv("DB_PORT", "5432"),
        "dbname": dbname or os.getenv("DB_NAME", "postgres"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", "postgres"),
    }


def ensure_database(conn_kwargs: Dict[str, str]) -> None:
    """Cria o banco de dados solicitado, caso ainda não exista."""
    target_db = conn_kwargs["dbname"]
    admin_db = os.getenv("DB_ADMIN_NAME", "postgres")

    admin_kwargs = get_conn_kwargs(admin_db)

    with psycopg.connect(**admin_kwargs, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (target_db,))
            exists = cur.fetchone() is not None
            if exists:
                return

            cur.execute(sql.SQL("CREATE DATABASE {}" ).format(sql.Identifier(target_db)))


def schema_already_applied(connection: psycopg.Connection) -> bool:
    with connection.cursor() as cur:
        cur.execute(
            "SELECT to_regclass('public.colecionadores') IS NOT NULL AS existe"
        )
        row = cur.fetchone()
        return bool(row and row.get("existe"))


def apply_schema(connection: psycopg.Connection, schema_sql: str) -> None:
    """Executa o arquivo de esquema completo apenas quando necessário."""
    if schema_already_applied(connection):
        return

    connection.execute(schema_sql)
    connection.commit()


def seed_colecionadores(cursor: psycopg.Cursor, quantidade_novos: int) -> Dict[str, str]:
    cursor.execute("SELECT nickname, id FROM colecionadores")
    ids: Dict[str, str] = {row["nickname"]: row["id"] for row in cursor.fetchall()}

    inseridos = 0
    while inseridos < quantidade_novos:
        nickname = faker.unique.user_name()
        nome = faker.name()

        cursor.execute(
            """
            INSERT INTO colecionadores (nome, nickname)
            VALUES (%s, %s)
            ON CONFLICT (nickname) DO NOTHING
            RETURNING id
            """,
            (nome, nickname),
        )

        row = cursor.fetchone()
        if row is None:
            cursor.execute(
                "SELECT id FROM colecionadores WHERE nickname = %s",
                (nickname,),
            )
            existing = cursor.fetchone()
            if existing:
                ids[nickname] = existing["id"]
            continue

        ids[nickname] = row["id"]
        inseridos += 1

    faker.unique.clear()
    return ids


def seed_cartas(cursor: psycopg.Cursor, novas_cartas: int) -> Dict[str, str]:
    cursor.execute("SELECT nome, id FROM cartas")
    ids: Dict[str, str] = {row["nome"]: row["id"] for row in cursor.fetchall()}

    cartas_iniciais = [
        {"nome": "Pikachu V", "tipo": "Elétrico", "raridade": "Ultra Rara", "preco_medio": 120.00},
        {"nome": "Charizard GX", "tipo": "Fogo", "raridade": "Secreta", "preco_medio": 350.00},
        {"nome": "Blastoise EX", "tipo": "Água", "raridade": "Rara", "preco_medio": 200.00},
        {"nome": "Gengar VMAX", "tipo": "Fantasma", "raridade": "Ultra Rara", "preco_medio": 280.00},
    ]

    for carta in cartas_iniciais:
        if carta["nome"] in ids:
            continue

        cursor.execute(
            """
            INSERT INTO cartas (nome, tipo, raridade, preco_medio)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """,
            (carta["nome"], carta["tipo"], carta["raridade"], carta["preco_medio"]),
        )
        row = cursor.fetchone()
        if row is None or row.get("id") is None:
            raise RuntimeError("Falha ao inserir carta; nenhuma linha retornada pelo banco.")
        ids[carta["nome"]] = row["id"]

    raridades = ["Comum", "Incomum", "Rara", "Ultra Rara", "Secreta"]
    tipos = ["Fogo", "Água", "Elétrico", "Grama", "Psíquico", "Fantasma", "Dragão"]

    criadas = 0
    tentativas = 0
    limite_tentativas = max(novas_cartas * 10, 10)

    while criadas < novas_cartas:
        tentativas += 1
        if tentativas > limite_tentativas:
            raise RuntimeError(
                "Não foi possível gerar cartas únicas suficientes. Considere diminuir NUM_NOVAS_CARTAS."
            )

        nome = f"{faker.word().title()} {faker.random_element(elements=['GX', 'V', 'EX', 'VMAX'])}"
        if nome in ids:
            continue

        carta = {
            "nome": nome,
            "tipo": faker.random_element(elements=tipos),
            "raridade": faker.random_element(elements=raridades),
            "preco_medio": round(
                faker.pyfloat(
                    left_digits=3,
                    right_digits=2,
                    positive=True,
                    min_value=50,
                    max_value=500,
                ),
                2,
            ),
        }

        cursor.execute(
            """
            INSERT INTO cartas (nome, tipo, raridade, preco_medio)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """,
            (carta["nome"], carta["tipo"], carta["raridade"], carta["preco_medio"]),
        )
        row = cursor.fetchone()
        if row is None or row.get("id") is None:
            raise RuntimeError("Falha ao inserir carta gerada; nenhuma linha retornada pelo banco.")

        ids[carta["nome"]] = row["id"]
        criadas += 1
        tentativas = 0

    return ids


def seed_colecao(
    cursor: psycopg.Cursor,
    colecionador_ids: Dict[str, str],
    carta_ids: Dict[str, str],
    min_registros_por_colecionador: int = 1,
    max_registros_por_colecionador: int = 3,
) -> None:
    carta_nomes = list(carta_ids.keys())

    if not carta_nomes:
        raise RuntimeError("Nenhuma carta disponível para semear a coleção.")

    for nickname, colecionador_id in colecionador_ids.items():
        registros = faker.random_int(
            min=min_registros_por_colecionador, max=max_registros_por_colecionador
        )

        for _ in range(registros):
            carta_nome = faker.random_element(elements=carta_nomes)
            carta_id = carta_ids[carta_nome]
            quantidade = faker.random_int(min=1, max=4)
            preco_pago = round(
                faker.pyfloat(
                    left_digits=3,
                    right_digits=2,
                    positive=True,
                    min_value=30,
                    max_value=400,
                ),
                2,
            )

            cursor.execute(
                """
                INSERT INTO colecao_cartas (colecionador_id, carta_id, quantidade, preco_pago)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    colecionador_id,
                    carta_id,
                    quantidade,
                    preco_pago,
                ),
            )


def fetch_all(cursor: psycopg.Cursor, query: str) -> Iterable[Dict[str, object]]:
    cursor.execute(query)
    return cursor.fetchall()


def main() -> None:
    load_env()
    configure_faker()

    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    conn_kwargs = get_conn_kwargs()
    quantidade_colecionadores = get_env_int(
        "NUM_COLECIONADORES", DEFAULT_NUM_COLECIONADORES, min_value=0
    )
    novas_cartas = get_env_int(
        "NUM_NOVAS_CARTAS", DEFAULT_NOVAS_CARTAS, min_value=0
    )
    colecao_min = get_env_int(
        "COLECAO_MIN", DEFAULT_COLECAO_MIN, min_value=0
    )
    colecao_max = get_env_int(
        "COLECAO_MAX", DEFAULT_COLECAO_MAX, min_value=1
    )

    if colecao_max < colecao_min:
        raise ValueError("COLECAO_MAX deve ser maior ou igual a COLECAO_MIN.")

    ensure_database(conn_kwargs)

    conn = psycopg.connect(**conn_kwargs, autocommit=False, row_factory=dict_row)

    try:
        apply_schema(conn, schema_sql)

        with conn.cursor() as cur:
            colecionadores = seed_colecionadores(cur, quantidade_colecionadores)
            cartas = seed_cartas(cur, novas_cartas)
            seed_colecao(cur, colecionadores, cartas, colecao_min, colecao_max)
            conn.commit()

        with conn.cursor() as cur:
            colecionadores_info = fetch_all(
                cur,
                """
                SELECT nome, nickname, total_cartas, valor_total
                FROM colecionadores
                ORDER BY nome
                """,
            )
            auditoria = fetch_all(
                cur,
                """
                SELECT mensagem, registrado_em
                FROM colecao_audit
                ORDER BY registrado_em
                """,
            )

        print("Colecionadores com totais atualizados:")
        for colecionador in colecionadores_info:
            print(
                " - {nome} (@{nickname}): {total_cartas} cartas | valor_total = {valor_total}".format(
                    **colecionador
                )
            )

        print("\nRegistros de auditoria gerados pelas triggers:")
        for log in auditoria:
            print(
                f" - {log['mensagem']} (registrado em {log['registrado_em']:%Y-%m-%d %H:%M:%S})"
            )

    finally:
        conn.close()


if __name__ == "__main__":
    main()

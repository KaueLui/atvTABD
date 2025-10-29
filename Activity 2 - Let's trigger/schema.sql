BEGIN;

-- Cria a extensão necessária para gerar UUIDs, caso ainda não exista
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Remove tabelas antigas para permitir recriações idempotentes
DROP TABLE IF EXISTS colecao_audit CASCADE;
DROP TABLE IF EXISTS colecao_cartas CASCADE;
DROP TABLE IF EXISTS cartas CASCADE;
DROP TABLE IF EXISTS colecionadores CASCADE;

-- Tabela com os colecionadores de cartas Pokémon
CREATE TABLE colecionadores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nome TEXT NOT NULL,
    nickname TEXT UNIQUE NOT NULL,
    total_cartas INTEGER NOT NULL DEFAULT 0,
    valor_total NUMERIC(12,2) NOT NULL DEFAULT 0,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Tabela com informações das cartas Pokémon registradas
CREATE TABLE cartas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nome TEXT NOT NULL,
    tipo TEXT NOT NULL,
    raridade TEXT NOT NULL,
    preco_medio NUMERIC(10,2) NOT NULL CHECK (preco_medio >= 0),
    criado_em TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Tabela de vínculo entre o colecionador e as cartas que ele possui
CREATE TABLE colecao_cartas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    colecionador_id UUID NOT NULL REFERENCES colecionadores(id) ON DELETE CASCADE,
    carta_id UUID NOT NULL REFERENCES cartas(id) ON DELETE CASCADE,
    quantidade INTEGER NOT NULL CHECK (quantidade > 0),
    preco_pago NUMERIC(10,2) NOT NULL CHECK (preco_pago >= 0),
    adquirido_em DATE NOT NULL DEFAULT CURRENT_DATE,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Tabela de auditoria para registrar inserções na coleção de cartas
CREATE TABLE colecao_audit (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    colecao_carta_id UUID NOT NULL REFERENCES colecao_cartas(id) ON DELETE CASCADE,
    colecionador_id UUID NOT NULL,
    carta_id UUID NOT NULL,
    quantidade INTEGER NOT NULL,
    preco_pago NUMERIC(10,2) NOT NULL,
    mensagem TEXT NOT NULL,
    registrado_em TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Função utilizada pelo trigger para atualizar os totais do colecionador
CREATE OR REPLACE FUNCTION atualizar_totais_colecionador() RETURNS TRIGGER AS $$
BEGIN
    -- Atualiza a contagem de cartas e o valor total investido pelo colecionador
    UPDATE colecionadores
    SET total_cartas = total_cartas + NEW.quantidade,
        valor_total = valor_total + (NEW.quantidade * NEW.preco_pago)
    WHERE id = NEW.colecionador_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Função utilizada pelo trigger de auditoria da coleção
CREATE OR REPLACE FUNCTION auditar_insercao_colecao() RETURNS TRIGGER AS $$
DECLARE
    nome_carta TEXT;
BEGIN
    SELECT nome INTO nome_carta FROM cartas WHERE id = NEW.carta_id;

    -- Registra a inserção da carta para facilitar auditorias futuras
    INSERT INTO colecao_audit (
        colecao_carta_id,
        colecionador_id,
        carta_id,
        quantidade,
        preco_pago,
        mensagem
    )
    VALUES (
        NEW.id,
        NEW.colecionador_id,
        NEW.carta_id,
        NEW.quantidade,
        NEW.preco_pago,
        FORMAT(
            'Colecionador %s adicionou %s unidade(s) da carta %s ao preço de %s',
            NEW.colecionador_id,
            NEW.quantidade,
            COALESCE(nome_carta, 'desconhecida'),
            NEW.preco_pago
        )
    );

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Atualiza agregados do colecionador após inserir cartas na coleção
CREATE TRIGGER trg_colecao_atualiza_totais
AFTER INSERT ON colecao_cartas
FOR EACH ROW
EXECUTE FUNCTION atualizar_totais_colecionador();

-- Trigger: Gera registro de auditoria sempre que novas cartas entram na coleção
CREATE TRIGGER trg_colecao_auditoria
AFTER INSERT ON colecao_cartas
FOR EACH ROW
EXECUTE FUNCTION auditar_insercao_colecao();

COMMIT;

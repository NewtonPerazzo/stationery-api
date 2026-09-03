# Stationery API

Backend do desafio técnico da papelaria, construído com Django e Django REST Framework.

## Versões utilizadas

- Python 3.12.13
- pip 26.2.1
- Django 5.2.17 (LTS)
- Django REST Framework 3.16.1
- django-cors-headers 4.9.0
- django-environ 0.12.1
- psycopg 3.3.5
- PostgreSQL (servidor local ou remoto)

As versões diretas da aplicação estão fixadas em `requirements.txt`. Dependências transitivas são resolvidas pelo `pip`.

## Executando localmente

No PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py runserver
```

A API será executada em `http://localhost:8000` e o Django Admin em `http://localhost:8000/admin/`.

Antes de executar as migrations, crie um banco PostgreSQL chamado `stationery`. A configuração padrão de desenvolvimento espera o usuário `postgres`, senha `postgres`, host `localhost` e porta `5432`. Caso sua instalação use outros valores, altere `DATABASE_URL` no arquivo `.env`:

```dotenv
DATABASE_URL=postgresql://usuario:senha@localhost:5432/stationery
```

## Configuração

As configurações locais ficam no arquivo `.env`, que não deve ser versionado. Use `.env.example` como referência.

## Organização planejada

O projeto seguirá uma organização pragmática em aplicações de domínio (`people`, `products` e `sales`). O ORM e os recursos nativos do Django serão usados para CRUDs simples; services concentrarão regras de negócio e repositories/query services serão utilizados apenas em consultas mais complexas, como o relatório de comissões.

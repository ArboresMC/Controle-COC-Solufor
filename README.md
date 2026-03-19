# Portal FSC — versão pronta para publicação

Este pacote já está ajustado para:
- rodar localmente;
- subir em hospedagem com PostgreSQL;
- publicar com Render;
- servir arquivos estáticos com WhiteNoise;
- usar Gunicorn em produção.

## 1. Rodar localmente

### Windows
1. Instale Python 3.11
2. Extraia a pasta
3. Abra o terminal dentro da pasta do projeto
4. Rode:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Depois abra:

```text
http://127.0.0.1:8000/login/
```

## 2. Publicar no Render

### Arquivos já incluídos
- `render.yaml`
- `Procfile`
- `build.sh`
- `.env.example`
- `runtime.txt`

### Passo a passo
1. Crie conta no Render
2. Envie este projeto para um repositório GitHub
3. No Render, escolha criar a partir do repositório
4. O arquivo `render.yaml` já cria:
   - 1 web service
   - 1 banco PostgreSQL
5. Depois do deploy, abra o shell do serviço e rode:

```bash
python manage.py createsuperuser
python manage.py seed_demo
```

6. Entre no sistema pelo domínio gerado pelo Render

## 3. Variáveis importantes

As principais variáveis já previstas são:
- `SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS`
- `CSRF_TRUSTED_ORIGINS`
- `DATABASE_URL`
- `SESSION_COOKIE_SECURE`
- `CSRF_COOKIE_SECURE`

Use o arquivo `.env.example` como modelo.

## 4. Login inicial

Se usar `seed_demo`:
- gestor / `12345678`
- participante / `12345678`
- auditor / `12345678`

Troque essas senhas assim que publicar.

## 5. Painel administrativo

Depois de publicar, o admin fica em:

```text
/admin/
```

## 6. O que esta versão já resolve para produção inicial

- banco PostgreSQL por `DATABASE_URL`
- arquivos estáticos em produção
- comando de build
- processo web com Gunicorn
- segurança básica por variáveis

## 7. O que ainda é recomendado fazer antes de uso real com participantes externos

- trocar senhas padrão
- configurar domínio próprio
- configurar e-mail para recuperação de senha
- rotina de backup do banco
- revisão das permissões por perfil
- termos de uso e política interna
- HTTPS ativo no domínio final

## 8. Comandos úteis

### Criar admin
```bash
python manage.py createsuperuser
```

### Rodar migrations
```bash
python manage.py migrate
```

### Popular dados de demonstração
```bash
python manage.py seed_demo
```

### Coletar estáticos
```bash
python manage.py collectstatic --noinput
```


## Atualização — conversões e rastreabilidade

Esta versão adiciona:
- escolha de unidade no lançamento de entradas e saídas;
- conversão para unidade base por produto;
- regras de rendimento entre produtos;
- tela de transformações (consumo de um produto e geração de outro);
- validação de saldo para impedir saídas e transformações acima do disponível;
- fornecedor automático "Não informado" nas entradas;
- exportação Excel com quantidades informadas e convertidas.

### Cadastros novos para usar corretamente
1. Cadastre o produto com a unidade base de controle.
2. Cadastre as conversões de unidade em `Catálogo > Conversões`.
3. Cadastre os rendimentos em `Catálogo > Rendimentos`.
4. Faça entradas, depois transformações, e só então as saídas do produto transformado.


## DOMÍNIO PRÓPRIO

Para usar um domínio próprio (ex.: portal.solufor.com.br):
1. Adicione o domínio no painel da Render em Custom Domains.
2. Crie o registro DNS solicitado pelo painel da Render.
3. Atualize as variáveis de ambiente `CUSTOM_DOMAIN`, `APP_BASE_URL`, `ALLOWED_HOSTS` e `CSRF_TRUSTED_ORIGINS`.
4. Faça um novo deploy.

Exemplo:
- CUSTOM_DOMAIN=portal.solufor.com.br
- APP_BASE_URL=https://portal.solufor.com.br
- ALLOWED_HOSTS=portal.solufor.com.br,portal-fsc.onrender.com,.onrender.com,127.0.0.1,localhost
- CSRF_TRUSTED_ORIGINS=https://portal.solufor.com.br,https://portal-fsc.onrender.com

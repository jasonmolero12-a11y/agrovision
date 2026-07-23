# AgroVision

Sistema web de gestão e consultoria agrícola desenvolvido com Django.

## Funcionalidades

- gestão de agricultores, clientes, consultores, técnicos e analistas;
- propriedades, talhões, culturas, produção e colheitas;
- consultoria agrícola inteligente e recomendações;
- meteorologia, alertas, visitas técnicas, pragas e doenças;
- mercado agrícola para clientes compradores;
- chatbot orientado pelo perfil do utilizador;
- integrações com Gemini, Open-Meteo, NASA POWER, SoilGrids,
  Copernicus Sentinel-2 e FAOSTAT;
- painel administrativo com controlo de utilizadores, permissões e APIs.

## Instalação local

1. Instale Python 3.12 e MySQL 8.
2. Crie e ative um ambiente virtual:

   ```powershell
   py -3.12 -m venv .venv
   .venv\Scripts\activate
   ```

3. Instale as dependências:

   ```powershell
   python -m pip install -r requirements.txt
   ```

4. Copie `.env.example` para `.env` e preencha as configurações locais.
5. Crie o banco MySQL indicado no `.env`.
6. Execute:

   ```powershell
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py runserver
   ```

7. Abra `http://127.0.0.1:8000/`.

## Testes

```powershell
python manage.py test --noinput
```

## Segurança

O ficheiro `.env`, credenciais, ambientes virtuais, banco local e uploads não
são enviados ao GitHub. Configure os segredos diretamente na plataforma de
hospedagem.


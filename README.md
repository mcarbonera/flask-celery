# Nome Projeto

## Descrição

## Instruções para rodar

- docker compose up
- Adminer em http://localhost:8080/
- Para acessar, utilizar os seguintes dados:

```
Servidor: postgres (o acesso é feito pelo docker, por isso não é localhost)
Usuário: user
Senha: pass
Base de Dados: chinook (base de dados criada na inicialização do container)
```

- O banco Postgres é automaticamente inicializado com os scripts da pasta /sql

## Demonstração

- (OPCIONAL) Duplicar base de dados (para aumentar o workload)

```
GET http://localhost:5000/duplicate_database
```

- Verificar status da task Celery:

```
GET http://localhost:5000/get_task_result?result_id=8e4c6bc7-e8b0-49d1-8ab7-3b8ffb362a9d
```

- Get Album. A primeira requisição tenta encontrar no cache e, se não encontra, busca no banco e atualiza o cache. Rodar duas vezes com o banco limpo para notar a diferença. (Para limpar o volume, utilizar o comando "docker compose down -v")

```
GET http://localhost:5000/album?album_id=193
```

- Update Album. Essa task está rodando para o banco todo, a fim de verificar o comportamento das tasks sob muita carga de trabalho. Contudo, em uma aplicação "normal", apenas atualizaria um registro por vez.

```
http://localhost:5000/update-album
```

- A estratégia de atualização adotada é o write-back. Dessa forma, atualiza o cache (redis) de maneira síncrona e agenda a task para atualização na base de dados persistente (postgres). Essa estratégia é rápida para grandes volumes de dados, contudo, ocorre a questão da consistência eventual, de forma que a base de dados persistente pode não conter o registro mais atualizado. Com o tempo, as modificações são propagadas.

## Descrição de arquitetura

- Redis para cache e resultados das tasks executadas pelo Celery.
- Postgres para armazenamento persistente.
- RabbitMQ para agendamento de tasks de duplicação de dados e atualização.
- adminer: apenas para visualização do banco Postgres (http://localhost:8080/).
- redis-commander: apenas para visualização do banco Redis (http://localhost:8082/).
- api-producer: API em Flask.
- db-duplication-worker: Task Celery responsável pela tarefa de duplicação da base de dados Postgres.
- db-write-back-worker: Task Celery responsável pela tarefa de write-back na base Postgres.
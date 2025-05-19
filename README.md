# Flask com tasks Celery

## Descrição

Foi utilizada uma base de dados pública (Chinook) com uma API Flask para demonstrar a estratégia "write-back" para atualização de dados em um sistema que utiliza cache.

Nesta estratégia, na atualização dos dados, primeiramente é atualizado o cache de maneira síncrona. A escrita em base de dados persistente, por ser geralmente lenta, é feita de maneira assíncrona.

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

## Instrução sobre como configurar o Gitlab CI para um repositório Github

- Dado que o repositório já existe no Github, acessar o Gitlab, clicar em "Novo Projeto", e clicar em "Executar CI/CD para repositório externo".

- Informar o token do github para que o gitlab consiga acessar o repositório.
- Selecionar o projeto para importar.
- Com o comando abaixo, rodar o Gitlab Runner, para executar a pipeline utilizando um container.

```
docker compose -f ./gitlab-ci/docker-compose.cicd.yml up
```

- Inicialmente, dará um erro por falta de configuração:

```
ERROR: Failed to load config stat /etc/gitlab-runner/config.toml: no such file or directory
```

- Na página do Gitlab, acessar: Projeto Gitlab -> Settings -> CI/CD -> Runner (Executores em português)

- Ao abrir a aba Executores, clicar em Novo executor de projeto. Criar um executor. Utilizei tempo limite máximo de 1800 segundos.

- É necessário utilizar uma tag. Configurando sem tag, o gitlab utiliza uma máquina própria para o executar o job. Utilizei a tag "local".

- Algumas informações vão surgir (url e token). Serão utilizadas nos próximos passos.

- No terminal, registrar o runner (nome do container é gitlab-ci-gitlab-runner-1, verificar com "docker ps -a"):

```
docker exec -it gitlab-ci-gitlab-runner-1 gitlab-runner register
```

- Serão solicitadas algumas informações: gitlab instance url, token, runner name, executor.

- Para url e token, utilizar as informações da página do gitlab.

- Para o nome do runner, utilizei "Severino".

- Para o campo executor, utilizei "docker", para rodar o job em um container separado do gitlab-runner. Contudo, para essa abordagem funcionar, é necessário subir container docker a partir de outro container docker e isso para ser feito precisa de acesso ao docker socket, que não tem suporte no Windows. Para fazer semelhante no Windows, precisa chamar o docker via TCP, abordagem "nativa" demais, e ainda é considerado algo inseguro, mas fazer o que.

- Para o campo default Docker Image, utilizei a imagem sonarsource/sonar-scanner-cli:latest (Tem que ser a imagem que roda o Job, não do gitlab-runner).

- A partir desse ponto, perceba que os logs de erro param de aparecer. Para verificar o funcionamento do gitlab runner por linha de comando:

```
docker exec -it gitlab-ci-gitlab-runner-1 gitlab-runner verify
```

- O resultado esperado no log é: "Verifying runner... is valid".

- Para habilitar a funcionalidade do docker de comunicação via TCP, necessária para subir o job a partir do gitlab-runner, acessar o Docker Desktop, e clicar em "Expose daemon on tcp://localhost:2375 without TLS".

- Se for necessário refazer a configuração, por algum motivo, utilizar o seguinte comando (tira o registro do gitlab runner, a fim de registrar novamente com outra configuração. Pode-se também editar o arquivo /data/gitlab-runner/config/config.toml):

```
docker exec -it gitlab-ci-gitlab-runner-1 gitlab-runner unregister --all-runners
```
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

## Instrução sobre como configurar o Gitlab CI

- Em repositório gitlab, ou em repositório github, mas usando a versão paga do gitlab, para permitir espelhar automaticamente.

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

- Para o campo default Docker Image, utilizei a imagem python:3.11.4-slim (Tem que ser a imagem que roda o Job, não do gitlab-runner).

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

- No arquivo config.toml, alterei a configuração para "concurrent = 3", a fim de permitir executar as tasks de modo paralelo.

- Foi necessário configurar duas variáveis de projeto no Gitlab (em Configurações -> CI/CD -> Variáveis), CI_DOCKERHUB_USER e CI_DOCKERHUB_PASSWORD, que contém o usuário e senha do Docker Hub, necessárias para publicação das imagens.

## Etapa de CD

- Para configurar uma base de dados postgres já inicializada no Kubernetes, foi necessário criar um arquivo dockerfile, para gerar a imagem postgres com os dados já carregados em docker-entrypoint-initdb.db. No docker compose, isto foi feito montando um volume.

- Para construir a imagem do banco postgres, utilizei o seguinte comando:

```
docker build -t mcarbonera/postgres:latest -f k8s-deploy/Dockerfile-postgres .
```

- O arquivo de configuração Kubernetes é flask-celery-app.yaml

- Para rodar, usar o comando:

```
kubectl apply -f k8s-deploy/flask-celery-app.yaml
```

- Para excluir:

```
kubectl delete -f k8s-deploy/flask-celery-app.yaml
```

## Para acionar a etapa de CD pelo gitlab-ci:

- No projeto, acessar Operação -> Clusters do Kubernetes.

- Clicar em "Conectar um cluster", adicionar o nome do agente (utilizei agente-severino-007) e clicar em "Criar e Registrar".

- Na próxima tela, vai aparecer alguns comandos "helm". Rodar na linha de comando para conectar o agente ao cluster Kubernetes. Os comandos são semelhantes a estes:

```
helm repo add gitlab https://charts.gitlab.io
helm repo update
helm upgrade --install <<nome-do-agente>> gitlab/gitlab-agent \
  --namespace <<nome-do-namespace>> \
  --create-namespace \
  --set config.token=<<token>> \
  --set config.kasAddress=wss://kas.gitlab.com
```

- No projeto, criar o arquivo .gitlab/agents/agente-severino-007/config.yaml.

- O conteúdo do arquivo deve ser conforme abaixo, com o id sendo "REPOSITORIO"/"NOME_DO_PROJETO":

```
ci_access:
  projects:
    - id: mcarbonera/flask-celery
```

- Para excluir o agente do Kubernetes, utilizar o seguinte comando:

```
helm uninstall --namespace=gitlab-agent-agente-severino-007 agente-severino-007
```

## Descrição da configuração do Kubernetes (flask-celery-app.yaml):

### RabbitMQ

- Deployment
- Service

### Redis

- Deployment
- Service

### Postgres

- PersistentVolumeClaim (para armazenar os dados)
- Deployment
- Service

### API Producer

- Deployment
- Service

### Task - Duplication Worker

- Deployment (Neste caso não foi necessário um service, pois as tasks não precisam expor suas portas externamente).

### Task Write-back Worker

- Deployment